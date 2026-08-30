"""

Teste A (qual alvo?) e Teste B (features de transmissao do InfoDengue).

Pre-declarado em PRE_DECLARACAO.md antes de rodar. Roda os dois em sequencia.

Uso:  python testar_alvo_e_features.py

"""

import sys
import time
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from acesso import fontes
from config import settings
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from dominio.features import construir_alvo_horizonte

PASTA_SAIDAS = PASTA_ANALISE / "saidas"
HORIZONTES = (1, 4, 8, 12)
PASSO_TESTE = 1
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")

# Configuracao de referencia definida pelo grid de 30/08.
PARAMETROS_REFERENCIA = {
    "max_iter": 250, "learning_rate": 0.05, "max_leaf_nodes": 15,
    "min_samples_leaf": 5, "random_state": 42,
    "loss": "quantile", "quantile": 0.80,
}

# Colunas do InfoDengue nunca usadas pelo projeto. Todas contemporaneas:
# o valor de t esta disponivel em t, entao usa-las para prever t+h nao vaza.
FEATURES_TRANSMISSAO = ["Rt", "p_rt1", "notif_accum_year", "receptivo", "transmissao"]

# O pico e definido pelo percentil 85 de CADA alvo, e nao por um numero fixo:
# os tres alvos tem escalas diferentes e um corte fixo compararia coisas
# distintas (100 casos e pico para confirmados e rotina para notificados).
PERCENTIL_PICO = 85


def carregar_base_com_infodengue() -> pd.DataFrame:
    """

    Junta a tabela_final com todas as colunas do InfoDengue.

    Atencao: carregar_tabela_final() JA renomeia 'casos_confirmados' para
    'casos' na leitura. Aqui o nome original e restaurado, porque este script
    trabalha com tres alvos concorrentes e precisa que cada um tenha nome
    proprio - 'casos' fica reservado para o alvo escolhido em cada rodada.

    """
    tabela = fontes.carregar_tabela_final().rename(columns={"casos": "casos_confirmados"})
    info = pd.read_csv(settings.CAMINHO_INFODENGUE, parse_dates=["data_iniSE"])

    colunas_info = ["data_iniSE", "casos", "casos_est"] + FEATURES_TRANSMISSAO
    info = info[colunas_info].rename(columns={
        "data_iniSE": "data", "casos": "casos_notificados", "casos_est": "casos_nowcast",
    })
    return tabela.merge(info, on="data", how="left").sort_values("data").reset_index(drop=True)


def preparar(base: pd.DataFrame, coluna_alvo: str) -> tuple[pd.DataFrame, list[str], list[str]]:
    """

    Monta a tabela para um alvo, removendo os OUTROS alvos.

    Deixar as tres series de casos juntas seria vazamento grosseiro: uma e
    quase funcao da outra na mesma semana.

    """
    dados = base.copy()
    dados["casos"] = dados[coluna_alvo]

    # As TRES colunas de alvo saem da tabela depois que a escolhida vira 'casos'.
    # Deixar qualquer uma delas seria vazamento grosseiro: as tres medem o mesmo
    # evento na mesma semana, entao uma preveria a outra perfeitamente.
    colunas_de_alvo = ["casos_confirmados", "casos_notificados", "casos_nowcast"]
    dados = dados.drop(columns=[c for c in colunas_de_alvo if c in dados.columns])

    dados = surto.aplicar_corte_maturidade(dados, CIDADE_REGRESSAO.semanas_corte_maturidade)
    dados = features.construir_features_temporais(dados)

    colunas_ignorar = tuple(CIDADE_REGRESSAO.colunas_ignorar) + tuple(FEATURES_TRANSMISSAO)
    nucleo, clima, vetor = selecao_features.separar_grupos_de_features(
        dados, colunas_ignorar, CIDADE_REGRESSAO.padroes_vetor, CIDADE_REGRESSAO.padroes_clima
    )
    ranking = selecao_features.selecionar_clima_por_ganho(
        dados, nucleo, clima, "casos", CIDADE_REGRESSAO.horizontes_selecao_clima,
        CIDADE_REGRESSAO.modelo_selecao_clima, CIDADE_REGRESSAO.fracao_treino_selecao,
    )
    referencia = nucleo + ranking.head(6).index.tolist() + vetor
    return dados, referencia, referencia + FEATURES_TRANSMISSAO


def rodar(dados: pd.DataFrame, colunas: list[str], horizonte: int) -> pd.DataFrame:
    """Walk-forward da configuracao de referencia."""
    preparados = construir_alvo_horizonte(dados, "casos", horizonte)
    usadas = colunas + ["alvo_sin", "alvo_cos"]
    validos = (preparados.dropna(subset=usadas + ["y_h"])
               .sort_values("data").reset_index(drop=True))

    linhas = []
    for corte in range(CIDADE_REGRESSAO.minimo_semanas_treino, len(validos), PASSO_TESTE):
        treino = validos.iloc[:corte]
        teste = validos.iloc[corte:corte + 1]
        modelo = HistGradientBoostingRegressor(**PARAMETROS_REFERENCIA)
        modelo.fit(treino[usadas], treino["y_h"])
        previsao = float(modelo.predict(teste[usadas])[0])
        linhas.append({
            "h": horizonte,
            "data_alvo": teste["data"].to_numpy()[0] + np.timedelta64(horizonte * 7, "D"),
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": max(previsao, 0.0),
        })
    return pd.DataFrame(linhas)


def resumir(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Resume por variante, horizonte e periodo, com pico relativo a cada alvo."""
    p = previsoes.copy()
    p["periodo"] = np.where(pd.to_datetime(p["data_alvo"]) <= FIM_DA_CALIBRACAO,
                            "calibracao", "avaliacao")
    p["erro"] = p["pred"] - p["real"]

    linhas = []
    for (variante, horizonte, periodo), g in p.groupby(["variante", "h", "periodo"]):
        reais = g["real"].to_numpy()
        sq_tot = float(((reais - reais.mean()) ** 2).sum())
        limiar = np.percentile(reais, PERCENTIL_PICO)
        picos = g.loc[g["real"] >= limiar]
        linhas.append({
            "variante": variante, "h": horizonte, "periodo": periodo, "n": len(g),
            "MAE": g["erro"].abs().mean(),
            "R2": 1 - float((g["erro"].to_numpy() ** 2).sum()) / sq_tot if sq_tot > 0 else np.nan,
            "captura_pico": picos["pred"].mean() / picos["real"].mean() if len(picos) else np.nan,
            "pico_real_medio": picos["real"].mean() if len(picos) else np.nan,
        })
    return pd.DataFrame(linhas)


def main() -> None:
    inicio_geral = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)
    base = carregar_base_com_infodengue()

    print("#" * 90, flush=True)
    print("# TESTE A — qual alvo? confirmados x notificados x nowcasting", flush=True)
    print("#" * 90, flush=True)

    todas = []
    conjuntos_por_alvo = {}
    for coluna_alvo, rotulo in (("casos_confirmados", "A1_confirmados"),
                                ("casos_notificados", "A2_notificados"),
                                ("casos_nowcast", "A3_nowcast")):
        dados, referencia, com_transmissao = preparar(base, coluna_alvo)
        conjuntos_por_alvo[coluna_alvo] = (dados, referencia, com_transmissao)
        print(f"\n--- {rotulo} ({len(referencia)} colunas) ---", flush=True)
        for h in HORIZONTES:
            t0 = time.time()
            previsoes = rodar(dados, referencia, h)
            previsoes["variante"] = rotulo
            todas.append(previsoes)
            print(f"  h={h:2d}: {len(previsoes)} semanas ({(time.time()-t0)/60:.1f} min)", flush=True)

    print("\n" + "#" * 90, flush=True)
    print("# TESTE B — features de transmissao (Rt, p_rt1, notif_accum_year, receptivo, transmissao)",
          flush=True)
    print("#" * 90, flush=True)

    dados, referencia, com_transmissao = conjuntos_por_alvo["casos_confirmados"]
    print(f"\n--- B_com_transmissao ({len(com_transmissao)} colunas) ---", flush=True)
    for h in HORIZONTES:
        t0 = time.time()
        previsoes = rodar(dados, com_transmissao, h)
        previsoes["variante"] = "B_confirmados_+_transmissao"
        todas.append(previsoes)
        print(f"  h={h:2d}: {len(previsoes)} semanas ({(time.time()-t0)/60:.1f} min)", flush=True)

    previsoes_finais = pd.concat(todas, ignore_index=True)
    previsoes_finais.to_csv(PASTA_SAIDAS / "alvo_features_previsoes.csv", index=False)
    resumo = resumir(previsoes_finais)
    resumo.to_csv(PASTA_SAIDAS / "alvo_features_resumo.csv", index=False)

    aval = resumo[resumo["periodo"] == "avaliacao"]
    print("\n" + "=" * 100, flush=True)
    print("CAPTURA DO PICO na AVALIACAO (previsto/real; 1,0 = perfeito) — metrica principal do Teste A",
          flush=True)
    print("=" * 100, flush=True)
    print(aval.pivot_table(index="h", columns="variante", values="captura_pico").round(3).to_string(),
          flush=True)

    print("\n=== R2 na AVALIACAO ===", flush=True)
    print(aval.pivot_table(index="h", columns="variante", values="R2").round(3).to_string(), flush=True)

    print("\n=== MAE na AVALIACAO (so comparavel DENTRO do mesmo alvo) ===", flush=True)
    print(aval.pivot_table(index="h", columns="variante", values="MAE").round(1).to_string(), flush=True)

    print("\n=== escala de cada alvo (media do pico) ===", flush=True)
    print(aval.pivot_table(index="h", columns="variante", values="pico_real_medio").round(0).to_string(),
          flush=True)

    print(f"\ntempo total: {(time.time()-inicio_geral)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
