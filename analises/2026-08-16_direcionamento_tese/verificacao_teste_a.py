"""
Verificacao ADVERSARIAL e INDEPENDENTE do Teste A (equivalencia clima x vetor).

Le SOMENTE os CSVs de previsoes ja salvos pelo Teste A (nao le nem importa o
script teste_a_equivalencia_clima_vetor.py). Reimplementa do zero: MAE pareado,
DM-HLN (4 celulas a mao), TOST (3 margens) e bootstrap em blocos (semente
diferente, para checar estabilidade do IC). So leitura de arquivos do projeto;
nada e alterado.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

PASTA = Path(
    "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/"
    "Meu Drive/Mestrado/Pesquisa/Meu_Projeto/analises/2026-08-16_direcionamento_tese"
)

HORIZONTES = (1, 4, 8, 12)
NIVEL_SIGNIFICANCIA = 0.05
MARGENS_FRACAO = (0.05, 0.10, 0.15)

# ---------------------------------------------------------------------------
# 1) Recarrega os CSVs de previsoes e recalcula MAE pareado (intersecao de data)
# ---------------------------------------------------------------------------

def carregar_previsoes(nome_conjunto: str, horizonte: int) -> pd.DataFrame:
    caminho = PASTA / f"previsoes_{nome_conjunto}_h{horizonte}.csv"
    return pd.read_csv(caminho, parse_dates=["data"])


def parear_clima_vetor(nome_clima: str, nome_vetor: str, horizonte: int) -> pd.DataFrame:
    clima = carregar_previsoes(nome_clima, horizonte)
    vetor = carregar_previsoes(nome_vetor, horizonte)
    pareado = clima.merge(vetor, on=["data", "h"], suffixes=("_clima", "_vetor"))
    # checagem de integridade: o valor 'real' tem que bater dos dois lados
    discrepancias_real = (pareado["real_clima"] - pareado["real_vetor"]).abs()
    n_discrepante = int((discrepancias_real > 1e-9).sum())
    pareado = pareado.sort_values("data").reset_index(drop=True)
    return pareado, n_discrepante


# ---------------------------------------------------------------------------
# 2) DM-HLN reimplementado do zero (formula padrao Harvey-Leybourne-Newbold 1997)
# ---------------------------------------------------------------------------

def variancia_longo_prazo_newey_west_truncada(diferenca: np.ndarray, horizonte: int) -> float:
    n = len(diferenca)
    media = diferenca.mean()
    d = diferenca - media
    gama0 = float((d ** 2).sum() / n)
    soma = 0.0
    for k in range(1, horizonte):
        gama_k = float((d[k:] * d[:-k]).sum() / n)
        soma += 2 * gama_k
    var_lp = gama0 + soma
    if var_lp <= 0:
        var_lp = gama0
    return var_lp


def dm_hln(diferenca: np.ndarray, horizonte: int) -> tuple[float, float]:
    n = len(diferenca)
    media = diferenca.mean()
    var_lp = variancia_longo_prazo_newey_west_truncada(diferenca, horizonte)
    dm = media / np.sqrt(var_lp / n)
    correcao = np.sqrt((n + 1 - 2 * horizonte + horizonte * (horizonte - 1) / n) / n)
    dm_hln_stat = dm * correcao
    p = 2 * (1 - stats.t.cdf(abs(dm_hln_stat), df=n - 1))
    return float(dm_hln_stat), float(p)


# ---------------------------------------------------------------------------
# 3) TOST reimplementado do zero (two one-sided tests sobre a media pareada)
# ---------------------------------------------------------------------------

def tost(diferenca: np.ndarray, horizonte: int, margem: float) -> tuple[float, float, float]:
    n = len(diferenca)
    media = diferenca.mean()
    var_lp = variancia_longo_prazo_newey_west_truncada(diferenca, horizonte)
    erro_padrao = np.sqrt(var_lp / n)
    gl = n - 1
    t_inf = (media - (-margem)) / erro_padrao
    t_sup = (media - margem) / erro_padrao
    p_inf = 1 - stats.t.cdf(t_inf, df=gl)
    p_sup = stats.t.cdf(t_sup, df=gl)
    p_tost = max(p_inf, p_sup)
    return p_inf, p_sup, p_tost


# ---------------------------------------------------------------------------
# 4) Bootstrap em blocos com SEMENTE DIFERENTE da original (20260816 -> 777001)
# ---------------------------------------------------------------------------

def bootstrap_blocos(diferenca: np.ndarray, tamanho_bloco: int, n_reamostras: int, semente: int):
    rng = np.random.default_rng(semente)
    n = len(diferenca)
    n_blocos = int(np.ceil(n / tamanho_bloco))
    pos_max = n - tamanho_bloco + 1
    medias = np.empty(n_reamostras)
    for i in range(n_reamostras):
        posicoes = rng.integers(0, pos_max, size=n_blocos)
        blocos = [diferenca[p:p + tamanho_bloco] for p in posicoes]
        serie = np.concatenate(blocos)[:n]
        medias[i] = serie.mean()
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


# ---------------------------------------------------------------------------
# 5) Checagem de vazamento / rastreabilidade nos CSVs
# ---------------------------------------------------------------------------

def checar_rastreabilidade() -> dict:
    """Confere se origem e alvo estao gravados nos CSVs, e se a semantica da
    coluna 'data' e consistente com origem <= alvo - h (sem vazamento), usando
    tabela_final.csv (projeto) so como referencia externa read-only."""
    caminho_tabela = Path(
        "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/"
        "Meu Drive/Mestrado/Pesquisa/Meu_Projeto/modelagem_aedes/dados/entradas/"
        "tabela_modelagem/tabela_final.csv"
    )
    tabela = pd.read_csv(caminho_tabela, parse_dates=["data_inicio_semana_epidemi"])
    tabela = tabela.sort_values("data_inicio_semana_epidemi").reset_index(drop=True)
    mapa_casos = dict(zip(tabela["data_inicio_semana_epidemi"], tabela["casos_confirmados"]))

    exemplo = carregar_previsoes("SO_CLIMA_PURO", 12)
    colunas = list(exemplo.columns)
    tem_duas_datas = ("data" in colunas) and any(
        c for c in colunas if c != "data" and "data" in c.lower()
    )

    # testa a hipotese "data == origem" contra 5 linhas amostradas
    linhas_testadas = 0
    linhas_consistentes_origem = 0
    persist = carregar_previsoes("persistencia", 12) if (PASTA / "previsoes_persistencia_h12.csv").exists() else None
    if persist is None:
        persist = pd.read_csv(PASTA / "previsoes_persistencia_h12.csv", parse_dates=["data"])
    amostra = persist.sample(n=min(8, len(persist)), random_state=42)
    for _, linha in amostra.iterrows():
        data_origem = linha["data"]
        casos_na_origem = mapa_casos.get(data_origem, np.nan)
        data_alvo = data_origem + pd.Timedelta(weeks=12)
        casos_no_alvo = mapa_casos.get(data_alvo, np.nan)
        linhas_testadas += 1
        pred_bate_origem = np.isclose(linha["pred"], casos_na_origem, equal_nan=True)
        real_bate_alvo = np.isclose(linha["real"], casos_no_alvo, equal_nan=True)
        if pred_bate_origem and real_bate_alvo:
            linhas_consistentes_origem += 1

    return {
        "colunas_previsoes": colunas,
        "tem_coluna_data_origem_e_data_alvo_separadas": bool(tem_duas_datas),
        "linhas_testadas_semantica_data": linhas_testadas,
        "linhas_consistentes_com_data_igual_origem": linhas_consistentes_origem,
    }


# ---------------------------------------------------------------------------
# Orquestracao
# ---------------------------------------------------------------------------

def main():
    linhas_saida = []
    celulas_dm_a_mao = [("puro", 1), ("com_ar", 1), ("puro", 12), ("com_ar", 12)]

    for versao, nome_clima, nome_vetor in (
        ("puro", "SO_CLIMA_PURO", "SO_VETOR_PURO"),
        ("com_ar", "SO_CLIMA_AR", "SO_VETOR_AR"),
    ):
        for h in HORIZONTES:
            pareado, n_discrepante = parear_clima_vetor(nome_clima, nome_vetor, h)
            n = len(pareado)
            erro_clima = (pareado["real_clima"] - pareado["pred_clima"]).abs().to_numpy()
            erro_vetor = (pareado["real_clima"] - pareado["pred_vetor"]).abs().to_numpy()
            diferenca = erro_vetor - erro_clima

            mae_clima = float(erro_clima.mean())
            mae_vetor = float(erro_vetor.mean())
            delta = mae_vetor - mae_clima

            fazer_dm_a_mao = (versao, h) in celulas_dm_a_mao
            if fazer_dm_a_mao:
                dm_stat, dm_p = dm_hln(diferenca, h)
            else:
                dm_stat, dm_p = np.nan, np.nan

            ic_inf, ic_sup = bootstrap_blocos(diferenca, 8, 2000, semente=777001)

            linha = {
                "versao": versao,
                "h": h,
                "n_pareado_verificacao": n,
                "n_discrepancias_real_clima_vs_vetor": n_discrepante,
                "MAE_clima_verificacao": round(mae_clima, 4),
                "MAE_vetor_verificacao": round(mae_vetor, 4),
                "delta_MAE_verificacao": round(delta, 4),
                "DM_HLN_estat_a_mao": round(dm_stat, 6) if fazer_dm_a_mao else "",
                "DM_HLN_p_a_mao": round(dm_p, 6) if fazer_dm_a_mao else "",
                "IC95_boot_semente_diferente_inf": round(ic_inf, 4),
                "IC95_boot_semente_diferente_sup": round(ic_sup, 4),
            }

            for fracao in MARGENS_FRACAO:
                margem = fracao * mae_clima
                p_inf, p_sup, p_tost = tost(diferenca, h, margem)
                rotulo = f"{int(fracao*100)}pct"
                linha[f"TOST_{rotulo}_p_inf"] = round(p_inf, 6)
                linha[f"TOST_{rotulo}_p_sup"] = round(p_sup, 6)
                linha[f"TOST_{rotulo}_p_tost"] = round(p_tost, 6)
                linha[f"TOST_{rotulo}_equivalente"] = bool(p_tost < NIVEL_SIGNIFICANCIA)

            linhas_saida.append(linha)

    tabela_saida = pd.DataFrame(linhas_saida)
    tabela_saida.to_csv(PASTA / "verificacao_teste_a_resultados.csv", index=False)

    rastreabilidade = checar_rastreabilidade()
    pd.DataFrame([rastreabilidade]).to_csv(PASTA / "verificacao_teste_a_rastreabilidade.csv", index=False)

    print(tabela_saida.to_string())
    print()
    print("RASTREABILIDADE:", rastreabilidade)


if __name__ == "__main__":
    main()
