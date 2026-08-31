"""

Teste focado no horizonte longo: o vetor ajuda em h=8 e h=12?

Pre-declarado em PRE_DECLARACAO.md antes de rodar. EXPLORATORIO, nao
confirmatorio - a hipotese nasceu destes mesmos dados.

Diferencas para os testes anteriores:
  - foca so nos horizontes onde o padrao aparece (8 e 12), em vez de diluir
    o sinal em 60 comparacoes;
  - corrige por Holm sobre 6 comparacoes, nao 60;
  - repete com 5 SEMENTES, para separar efeito real de sorte de inicializacao -
    nenhum teste anterior do projeto fez isso;
  - IC do delta-MAE por bootstrap EM BLOCOS, que respeita a autocorrelacao da
    serie (um bootstrap simples trataria semanas vizinhas como independentes e
    daria intervalo estreito demais).

Uso:  python testar_h12_focado.py

"""

import sys
import time
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor

from acesso import fontes
from avaliacao import diebold_mariano
from avaliacao.correcao_multipla import corrigir_holm
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from dominio.features import construir_alvo_horizonte

PASTA_SAIDAS = PASTA_ANALISE / "saidas"
CAMINHO_CHECKPOINT = PASTA_SAIDAS / "h12_previsoes_parciais.csv"

HORIZONTES = (8, 12)
PASSO_TESTE = 1
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")
SEMENTES = (42, 101, 202, 303, 404)
ALFA = 0.05

TAMANHO_BLOCO_BOOTSTRAP = 8
NUMERO_REAMOSTRAS = 2000
SEMENTE_BOOTSTRAP = 20260830

QUANTIL_REFERENCIA = 0.80

ALGORITMOS = {
    "hist_gradient_boosting": {
        "classe": HistGradientBoostingRegressor,
        "base": {"max_iter": 250, "learning_rate": 0.05, "max_leaf_nodes": 15,
                 "min_samples_leaf": 5},
        "perda": {"loss": "quantile", "quantile": QUANTIL_REFERENCIA},
    },
    "gradient_boosting": {
        "classe": GradientBoostingRegressor,
        "base": {"n_estimators": 250, "learning_rate": 0.05, "max_depth": 3,
                 "min_samples_leaf": 5},
        "perda": {"loss": "quantile", "alpha": QUANTIL_REFERENCIA},
    },
    "lightgbm": {
        "classe": LGBMRegressor,
        "base": {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 31,
                 "min_child_samples": 20, "verbose": -1, "n_jobs": -1},
        "perda": {"objective": "quantile", "alpha": QUANTIL_REFERENCIA},
    },
}


def montar_dados_e_conjuntos() -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Reproduz o preparo do cenario 1 e devolve a tabela e os dois conjuntos."""
    config = CIDADE_REGRESSAO

    tabela = fontes.carregar_tabela_final()
    tabela = surto.aplicar_corte_maturidade(tabela, config.semanas_corte_maturidade)
    tabela = features.construir_features_temporais(tabela)

    nucleo, clima, vetor = selecao_features.separar_grupos_de_features(
        tabela, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )
    ranking = selecao_features.selecionar_clima_por_ganho(
        tabela, nucleo, clima, config.coluna_alvo, config.horizontes_selecao_clima,
        config.modelo_selecao_clima, config.fracao_treino_selecao,
    )
    enxuto = ranking.head(6).index.tolist()
    return tabela, {"M0_sem_vetor": nucleo + enxuto, "M1_com_vetor": nucleo + enxuto + vetor}


def rodar_celula(
    tabela: pd.DataFrame,
    colunas: list[str],
    nome_algoritmo: str,
    horizonte: int,
    semente: int,
) -> pd.DataFrame:
    """Walk-forward de uma celula (algoritmo x conjunto x horizonte x semente)."""
    config = CIDADE_REGRESSAO
    ficha = ALGORITMOS[nome_algoritmo]

    parametros = dict(ficha["base"])
    parametros.update(ficha["perda"])
    parametros["random_state"] = semente

    dados = construir_alvo_horizonte(tabela, config.coluna_alvo, horizonte)
    usadas = colunas + ["alvo_sin", "alvo_cos"]
    validos = (dados.dropna(subset=usadas + ["y_h"])
               .sort_values("data").reset_index(drop=True))

    linhas = []
    for corte in range(config.minimo_semanas_treino, len(validos), PASSO_TESTE):
        treino = validos.iloc[:corte]
        teste = validos.iloc[corte:corte + 1]
        modelo = ficha["classe"](**parametros)
        modelo.fit(treino[usadas], treino["y_h"])
        previsao = float(modelo.predict(teste[usadas])[0])
        linhas.append({
            "h": horizonte,
            "data_alvo": teste["data"].to_numpy()[0] + np.timedelta64(horizonte * 7, "D"),
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": max(previsao, 0.0),
        })
    return pd.DataFrame(linhas)


def bootstrap_em_blocos(
    diferenca_de_erros: np.ndarray,
    gerador: np.random.Generator,
) -> tuple[float, float]:
    """

    IC 95% da media da diferenca de erros, por bootstrap em blocos.

    Reamostra blocos contiguos de TAMANHO_BLOCO_BOOTSTRAP semanas em vez de
    semanas isoladas: semanas vizinhas sao correlacionadas, e reamostrar uma a
    uma trataria cada semana como informacao independente, produzindo intervalo
    estreito demais.

    """
    numero_de_pontos = len(diferenca_de_erros)
    if numero_de_pontos < TAMANHO_BLOCO_BOOTSTRAP * 2:
        return float("nan"), float("nan")

    blocos_por_amostra = int(np.ceil(numero_de_pontos / TAMANHO_BLOCO_BOOTSTRAP))
    ultimo_inicio = numero_de_pontos - TAMANHO_BLOCO_BOOTSTRAP

    medias = []
    for _ in range(NUMERO_REAMOSTRAS):
        inicios = gerador.integers(0, ultimo_inicio + 1, size=blocos_por_amostra)
        pedacos = []
        for inicio in inicios:
            pedacos.append(diferenca_de_erros[inicio:inicio + TAMANHO_BLOCO_BOOTSTRAP])
        amostra = np.concatenate(pedacos)[:numero_de_pontos]
        medias.append(amostra.mean())

    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def main() -> None:
    inicio_geral = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)
    if CAMINHO_CHECKPOINT.exists():
        CAMINHO_CHECKPOINT.unlink()

    tabela, conjuntos = montar_dados_e_conjuntos()
    print(f"M0={len(conjuntos['M0_sem_vetor'])} colunas | "
          f"M1={len(conjuntos['M1_com_vetor'])} colunas", flush=True)
    total = len(ALGORITMOS) * len(conjuntos) * len(HORIZONTES) * len(SEMENTES)
    print(f"celulas: {total}\n", flush=True)

    contador = 0
    todas = []
    for nome_algoritmo in ALGORITMOS:
        for semente in SEMENTES:
            for rotulo_conjunto, colunas in conjuntos.items():
                for horizonte in HORIZONTES:
                    contador += 1
                    t0 = time.time()
                    previsoes = rodar_celula(
                        tabela, colunas, nome_algoritmo, horizonte, semente
                    )
                    previsoes["algoritmo"] = nome_algoritmo
                    previsoes["conjunto"] = rotulo_conjunto
                    previsoes["semente"] = semente
                    todas.append(previsoes)

                    cabecalho = not CAMINHO_CHECKPOINT.exists()
                    previsoes.to_csv(CAMINHO_CHECKPOINT, mode="a",
                                     header=cabecalho, index=False)
                    print(f"[{contador:2d}/{total}] {nome_algoritmo} | semente {semente} | "
                          f"{rotulo_conjunto} | h={horizonte}: "
                          f"{len(previsoes)} semanas ({(time.time()-t0)/60:.1f} min)", flush=True)

    p = pd.concat(todas, ignore_index=True)
    aval = p[pd.to_datetime(p["data_alvo"]) > FIM_DA_CALIBRACAO]
    gerador = np.random.default_rng(SEMENTE_BOOTSTRAP)

    linhas = []
    for (nome_algoritmo, horizonte, semente), g in aval.groupby(["algoritmo", "h", "semente"]):
        m0 = g[g["conjunto"] == "M0_sem_vetor"][["data_alvo", "real", "pred"]]
        m1 = g[g["conjunto"] == "M1_com_vetor"][["data_alvo", "real", "pred"]]
        par = m0.merge(m1, on=["data_alvo", "real"], suffixes=("_m0", "_m1"))

        erro_m0 = (par["pred_m0"] - par["real"]).to_numpy()
        erro_m1 = (par["pred_m1"] - par["real"]).to_numpy()
        diferenca = np.abs(erro_m0) - np.abs(erro_m1)

        dm = diebold_mariano.teste_diebold_mariano(erro_m0, erro_m1, horizonte, "absoluto")
        ic_inferior, ic_superior = bootstrap_em_blocos(diferenca, gerador)

        linhas.append({
            "algoritmo": nome_algoritmo, "h": horizonte, "semente": semente,
            "n": len(par),
            "MAE_sem": np.abs(erro_m0).mean(), "MAE_com": np.abs(erro_m1).mean(),
            "ganho": diferenca.mean(),
            "IC95_inf": ic_inferior, "IC95_sup": ic_superior,
            "IC_exclui_zero": bool(ic_inferior > 0 or ic_superior < 0),
            "DM_p_bruto": dm.valor_p,
        })

    detalhe = pd.DataFrame(linhas)
    detalhe.to_csv(PASTA_SAIDAS / "h12_por_semente.csv", index=False)

    # Holm sobre as 6 comparacoes pre-declaradas (3 algoritmos x 2 horizontes),
    # usando a MEDIA das sementes - a semente e ruido de implementacao, nao
    # uma comparacao nova.
    medio = detalhe.groupby(["algoritmo", "h"]).agg(
        n=("n", "first"),
        MAE_sem=("MAE_sem", "mean"), MAE_com=("MAE_com", "mean"),
        ganho_medio=("ganho", "mean"), ganho_min=("ganho", "min"), ganho_max=("ganho", "max"),
        sementes_com_ganho=("ganho", lambda valores: int((valores > 0).sum())),
        sementes_com_IC_excluindo_zero=("IC_exclui_zero", "sum"),
        DM_p_mediano=("DM_p_bruto", "median"),
    ).reset_index()
    medio["DM_p_holm_6"] = corrigir_holm(medio["DM_p_mediano"].to_numpy())
    medio["significativo"] = medio["DM_p_holm_6"] < ALFA
    medio.to_csv(PASTA_SAIDAS / "h12_resumo.csv", index=False)

    print("\n" + "=" * 118, flush=True)
    print("RESULTADO — media das 5 sementes, periodo de avaliacao (2024+)", flush=True)
    print("=" * 118, flush=True)
    print(medio.round(4).to_string(index=False), flush=True)

    print("\n=== ESTABILIDADE: o ganho aparece em quantas das 5 sementes? ===", flush=True)
    for _, linha in medio.iterrows():
        print(f"  {linha['algoritmo']:24s} h={int(linha['h']):2d}: "
              f"{int(linha['sementes_com_ganho'])}/5 sementes com ganho | "
              f"faixa [{linha['ganho_min']:+7.1f}, {linha['ganho_max']:+7.1f}] | "
              f"IC exclui zero em {int(linha['sementes_com_IC_excluindo_zero'])}/5", flush=True)

    sobrevivem = int(medio["significativo"].sum())
    print(f"\nVEREDITO: {sobrevivem} de {len(medio)} comparacoes sobrevivem a Holm(6) "
          f"em alfa={ALFA}.", flush=True)
    print(f"tempo total: {(time.time()-inicio_geral)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
