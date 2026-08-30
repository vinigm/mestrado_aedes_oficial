"""

Features de longo prazo ajudam o modelo em horizonte longo?

Pre-declarado em PRE_DECLARACAO.md antes de rodar.

A configuracao de referencia captura 98% do pico em 1 semana e so 62% em 12
semanas. A causa foi medida: a autocorrelacao dos casos explica 91% da
variacao em h=1 e cai a ZERO em h=12. Todas as features do projeto sao de
curto prazo (defasagens de 1 a 4 semanas), entao quando a muleta autorregressiva
some nao sobra nada de longo prazo para sustentar a previsao.

Aqui entram quatro grupos de features longas, todos construidos SO COM PASSADO.

Uso:  python testar_features_longas.py

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
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from dominio.features import construir_alvo_horizonte

PASTA_SAIDAS = PASTA_ANALISE / "saidas"

HORIZONTES = (1, 4, 8, 12)
PASSO_TESTE = 1
LIMITE_PICO = 100
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")

# A configuracao de referencia do projeto, definida pelo grid de 30/08.
PARAMETROS_REFERENCIA = {
    "max_iter": 250,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 5,
    "random_state": 42,
    "loss": "quantile",
    "quantile": 0.80,
}

# Colunas que recebem norma historica e anomalia.
COLUNAS_PARA_ANOMALIA = ("temp_media", "precip_total_mm", "umid_media")
# Colunas que recebem acumulo de longo prazo.
COLUNAS_PARA_ACUMULO = ("precip_total_mm", "temp_media")
JANELAS_DE_ACUMULO = (8, 12)


def calcular_norma_historica(valores: pd.Series) -> pd.Series:
    """

    Media das ocorrencias ANTERIORES da mesma semana do ano.

    E o que torna a anomalia livre de vazamento: em cada linha, a norma usa
    apenas as vezes em que aquela semana do ano ja aconteceu ANTES. Usar a
    media da serie inteira faria a feature enxergar o futuro.

    """
    return valores.expanding().mean().shift(1)


def acrescentar_features_longas(tabela: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """

    Cria os quatro grupos de features longas e devolve a tabela e o mapa de grupos.

    Returns:
        A tabela com as colunas novas e um dicionario ligando o nome de cada
        grupo as colunas que ele acrescenta.

    """
    dados = tabela.copy()
    dados["semana_do_ano"] = dados["data"].dt.isocalendar().week.astype(int)

    grupos: dict[str, list[str]] = {"B_lags_anuais": [], "C_anomalia": [],
                                    "D_acumulo": [], "E_enso": []}

    # --- B: lags anuais ---
    dados["casos_lag52"] = dados["casos"].shift(52)
    dados["casos_lag104"] = dados["casos"].shift(104)
    dados["vetor_lag52"] = dados["aedes_aegypti_por_armadilha"].shift(52)
    grupos["B_lags_anuais"] = ["casos_lag52", "casos_lag104", "vetor_lag52"]

    # --- C: anomalia contra a norma historica daquela semana do ano ---
    agrupado_por_semana = dados.groupby("semana_do_ano", group_keys=False)
    for nome_coluna in COLUNAS_PARA_ANOMALIA:
        nome_norma = f"{nome_coluna}_norma"
        nome_anomalia = f"{nome_coluna}_anomalia"
        dados[nome_norma] = agrupado_por_semana[nome_coluna].transform(calcular_norma_historica)
        dados[nome_anomalia] = dados[nome_coluna] - dados[nome_norma]
        grupos["C_anomalia"].append(nome_anomalia)

    # --- D: acumulo de longo prazo ---
    for nome_coluna in COLUNAS_PARA_ACUMULO:
        for janela in JANELAS_DE_ACUMULO:
            nome_acumulo = f"{nome_coluna}_acum{janela}"
            dados[nome_acumulo] = dados[nome_coluna].rolling(janela).sum()
            grupos["D_acumulo"].append(nome_acumulo)

    # --- E: ENSO (ja esta na tabela, so estava sendo descartado pelo config) ---
    grupos["E_enso"] = ["nino34_anom", "oni"]

    return dados, grupos


def montar_base() -> tuple[pd.DataFrame, list[str], dict[str, list[str]]]:
    """Reproduz o preparo do cenario 1 e acrescenta as features longas."""
    config = CIDADE_REGRESSAO

    tabela = fontes.carregar_tabela_final()
    tabela = surto.aplicar_corte_maturidade(tabela, config.semanas_corte_maturidade)
    tabela = features.construir_features_temporais(tabela)

    colunas_nucleo, colunas_clima, colunas_vetor = selecao_features.separar_grupos_de_features(
        tabela, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )
    ranking_clima = selecao_features.selecionar_clima_por_ganho(
        tabela, colunas_nucleo, colunas_clima, config.coluna_alvo,
        config.horizontes_selecao_clima, config.modelo_selecao_clima,
        config.fracao_treino_selecao,
    )
    conjunto_referencia = colunas_nucleo + ranking_clima.head(6).index.tolist() + colunas_vetor

    tabela, grupos = acrescentar_features_longas(tabela)
    return tabela, conjunto_referencia, grupos


def rodar(tabela: pd.DataFrame, colunas: list[str], horizonte: int) -> pd.DataFrame:
    """Walk-forward da configuracao de referencia com o conjunto de colunas dado."""
    config = CIDADE_REGRESSAO

    dados = construir_alvo_horizonte(tabela, config.coluna_alvo, horizonte)
    colunas_usadas = colunas + ["alvo_sin", "alvo_cos"]

    validos = (
        dados.dropna(subset=colunas_usadas + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    linhas = []
    for indice_corte in range(config.minimo_semanas_treino, len(validos), PASSO_TESTE):
        treino = validos.iloc[:indice_corte]
        teste = validos.iloc[indice_corte:indice_corte + 1]

        modelo = HistGradientBoostingRegressor(**PARAMETROS_REFERENCIA)
        modelo.fit(treino[colunas_usadas], treino["y_h"])
        previsao = float(modelo.predict(teste[colunas_usadas])[0])

        data_alvo = teste["data"].to_numpy()[0] + np.timedelta64(horizonte * 7, "D")
        linhas.append({
            "h": horizonte, "data_alvo": data_alvo,
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": max(previsao, 0.0),
        })

    return pd.DataFrame(linhas)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela, referencia, grupos = montar_base()
    print(f"conjunto de referencia (A): {len(referencia)} colunas", flush=True)
    for nome_grupo, colunas in grupos.items():
        print(f"  {nome_grupo}: {colunas}", flush=True)

    variantes = {
        "A_referencia": referencia,
        "A+B_lags_anuais": referencia + grupos["B_lags_anuais"],
        "A+C+D_clima_longo": referencia + grupos["C_anomalia"] + grupos["D_acumulo"],
        "A+E_enso": referencia + grupos["E_enso"],
        "A+TUDO": (referencia + grupos["B_lags_anuais"] + grupos["C_anomalia"]
                   + grupos["D_acumulo"] + grupos["E_enso"]),
    }

    todas = []
    for rotulo, colunas in variantes.items():
        print(f"\n--- {rotulo} ({len(colunas)} colunas) ---", flush=True)
        for horizonte in HORIZONTES:
            inicio = time.time()
            previsoes = rodar(tabela, colunas, horizonte)
            previsoes["variante"] = rotulo
            todas.append(previsoes)
            print(f"  h={horizonte:2d}: {len(previsoes)} semanas "
                  f"({(time.time() - inicio) / 60:.1f} min)", flush=True)

    p = pd.concat(todas, ignore_index=True)
    p["periodo"] = np.where(
        pd.to_datetime(p["data_alvo"]) <= FIM_DA_CALIBRACAO, "calibracao", "avaliacao"
    )
    p["erro"] = p["pred"] - p["real"]
    p.to_csv(PASTA_SAIDAS / "features_longas_previsoes.csv", index=False)

    linhas_resumo = []
    for (variante, horizonte, periodo), grupo in p.groupby(["variante", "h", "periodo"]):
        reais = grupo["real"].to_numpy()
        soma_total = float(((reais - reais.mean()) ** 2).sum())
        picos = grupo.loc[grupo["real"] > LIMITE_PICO]
        linhas_resumo.append({
            "variante": variante, "h": horizonte, "periodo": periodo, "n": len(grupo),
            "MAE": grupo["erro"].abs().mean(),
            "R2": 1 - float((grupo["erro"].to_numpy() ** 2).sum()) / soma_total if soma_total > 0 else np.nan,
            "vies_pico": picos["erro"].mean() if len(picos) else np.nan,
            "captura_pico": picos["pred"].mean() / picos["real"].mean() if len(picos) else np.nan,
        })

    resumo = pd.DataFrame(linhas_resumo)
    resumo.to_csv(PASTA_SAIDAS / "features_longas_resumo.csv", index=False)

    for periodo in ("calibracao", "avaliacao"):
        print("\n" + "=" * 100, flush=True)
        print(f"MAE — periodo de {periodo.upper()}", flush=True)
        print("=" * 100, flush=True)
        print(resumo[resumo["periodo"] == periodo]
              .pivot_table(index="h", columns="variante", values="MAE").round(1).to_string(),
              flush=True)

    print("\n=== CAPTURA DO PICO no periodo de AVALIACAO (quanto mais perto de 1, melhor) ===",
          flush=True)
    print(resumo[resumo["periodo"] == "avaliacao"]
          .pivot_table(index="h", columns="variante", values="captura_pico").round(3).to_string(),
          flush=True)

    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
