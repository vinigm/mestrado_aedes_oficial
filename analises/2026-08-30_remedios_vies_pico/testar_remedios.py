"""

Testa quatro remedios para o vies de subestimacao do pico no cenario 1.

Diagnostico que motivou (30/08/2026): o modelo subestima os picos de dengue e a
subestimacao cresce com o horizonte (-89 em h=1 ate -429 em h=12). A causa NAO
e limite de extrapolacao das arvores - isso foi testado e refutado (o teto do
treino era 1.439 e o pico medio 829; so 5 de 32 picos ficavam acima do teto).
A causa e a assimetria da serie: 61% das semanas tem ate 5 casos, e o objetivo
padrao do LightGBM (erro quadratico) puxa toda previsao para o centro dessa
distribuicao.

As tres primeiras ideias vieram de um projeto anterior do Vinicius (previsao de
demanda no varejo, pasta Sortimento/codigos_antigos...), que ja tinha resolvido
um problema de forma parecida:

  A - MES-ALVO CATEGORICO. O projeto antigo passava 'target_mes' como categoria
      1-12, com o comentario "esse e o sinal-chave de sazonalidade". Hoje o
      projeto usa alvo_sin/alvo_cos, que sao senoides suaves. A diferenca
      importa porque a serie de POA NAO e suave: marco a maio tem mediana de
      705 a 879 casos e setembro a janeiro tem mediana 3. Categoria deixa a
      arvore cortar seco onde a senoide obriga a interpolar.

  B - OBJETIVO TWEEDIE (potencia 1,5). O projeto antigo usava tweedie para
      contagem. E o objetivo desenhado para dado nao-negativo com muitos zeros
      e cauda longa - exatamente o nosso caso. Ataca a causa diagnosticada.

  C - REGRESSAO QUANTILICA (alpha 0,8). O comentario do codigo antigo era
      "calibra o vies". Prever um quantil alto em vez da media e o remedio
      classico para subestimacao sistematica.

  D - A + B juntos.

Todas as variantes clipam a previsao em zero (caso de dengue nao e negativo);
o clip vale igualmente para a referencia, para nao favorecer ninguem.

Uso:  python testar_remedios.py

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

from acesso import fontes
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from dominio.features import construir_alvo_horizonte

PASTA_SAIDAS = PASTA_ANALISE / "saidas"
HORIZONTES = (1, 4, 8, 12)
LIMITE_ENTRESSAFRA = 5
LIMITE_PICO = 100
MESES_DO_ANO = list(range(1, 13))

# Hiperparametros iguais aos do cenario 1, para que a unica diferenca entre as
# variantes seja o que cada uma se propoe a mudar.
HIPERPARAMETROS_BASE = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "verbose": -1,
    "n_jobs": -1,
    "random_state": 42,
}

# Cada variante: (rotulo, usa mes categorico, parametros extras do LightGBM).
VARIANTES = (
    ("atual", False, {}),
    ("A_mes_categorico", True, {}),
    ("B_tweedie", False, {"objective": "tweedie", "tweedie_variance_power": 1.5}),
    ("C_quantile_08", False, {"objective": "quantile", "alpha": 0.8}),
    ("D_mes_cat_+_tweedie", True, {"objective": "tweedie", "tweedie_variance_power": 1.5}),
)


def montar_dados_e_colunas() -> tuple[pd.DataFrame, list[str]]:
    """Reproduz o preparo do cenario 1 e devolve a tabela e as colunas do modelo."""
    config = CIDADE_REGRESSAO

    tabela = fontes.carregar_tabela_final()
    tabela = surto.aplicar_corte_maturidade(tabela, config.semanas_corte_maturidade)
    tabela = features.construir_features_temporais(tabela)

    colunas_nucleo, colunas_clima, _ = selecao_features.separar_grupos_de_features(
        tabela, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )
    ranking_clima = selecao_features.selecionar_clima_por_ganho(
        tabela, colunas_nucleo, colunas_clima, config.coluna_alvo,
        config.horizontes_selecao_clima, config.modelo_selecao_clima,
        config.fracao_treino_selecao,
    )
    return tabela, colunas_nucleo + ranking_clima.head(6).index.tolist()


def rodar_variante(
    tabela: pd.DataFrame,
    colunas_modelo: list[str],
    horizonte: int,
    usar_mes_categorico: bool,
    parametros_extras: dict,
) -> pd.DataFrame:
    """

    Walk-forward de uma variante, num horizonte.

    Args:
        tabela: Tabela semanal com as features prontas.
        colunas_modelo: Colunas de entrada comuns a todas as variantes.
        horizonte: Quantas semanas a frente prever.
        usar_mes_categorico: Se verdadeiro, acrescenta o mes da semana-alvo
            como variavel categorica de 1 a 12.
        parametros_extras: O que muda no LightGBM nesta variante (objetivo,
            potencia do tweedie, alpha do quantil).

    Returns:
        Uma linha por semana testada, com o valor real e o previsto (ja
        clipado em zero).

    """
    config = CIDADE_REGRESSAO

    dados = construir_alvo_horizonte(tabela, config.coluna_alvo, horizonte)

    # O mes da semana-alvo: a data de hoje mais o horizonte, em meses de calendario.
    dados["mes_alvo"] = (dados["data"] + pd.to_timedelta(horizonte, unit="W")).dt.month

    colunas_usadas = colunas_modelo + ["alvo_sin", "alvo_cos"]
    if usar_mes_categorico:
        colunas_usadas = colunas_usadas + ["mes_alvo"]

    validos = (
        dados.dropna(subset=colunas_usadas + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )
    if usar_mes_categorico:
        validos["mes_alvo"] = pd.Categorical(validos["mes_alvo"], categories=MESES_DO_ANO)

    parametros = dict(HIPERPARAMETROS_BASE)
    parametros.update(parametros_extras)

    linhas = []
    for indice_corte in range(config.minimo_semanas_treino, len(validos), config.passo):
        treino = validos.iloc[:indice_corte]
        teste = validos.iloc[indice_corte:indice_corte + 1]

        modelo = LGBMRegressor(**parametros)
        modelo.fit(treino[colunas_usadas], treino["y_h"])
        previsao = float(modelo.predict(teste[colunas_usadas])[0])

        # Caso de dengue nao e negativo. Vale para todas as variantes, inclusive
        # a referencia, para nao favorecer nenhuma.
        previsao_valida = max(previsao, 0.0)

        linhas.append({
            "h": horizonte,
            "data": teste["data"].to_numpy()[0],
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": previsao_valida,
        })

    return pd.DataFrame(linhas)


def classificar_faixa(casos_reais: float) -> str:
    """Rotula a semana pela intensidade real de casos."""
    if casos_reais <= LIMITE_ENTRESSAFRA:
        return "entressafra"
    if casos_reais <= LIMITE_PICO:
        return "intermediaria"
    return "pico"


def resumir(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Resume MAE global, R2 global e o vies do pico, por variante e horizonte."""
    trabalho = previsoes.copy()
    trabalho["faixa"] = trabalho["real"].apply(classificar_faixa)
    trabalho["erro"] = trabalho["pred"] - trabalho["real"]

    linhas = []
    for (variante, horizonte), grupo in trabalho.groupby(["variante", "h"]):
        reais = grupo["real"].to_numpy()
        soma_quadrados_total = float(((reais - reais.mean()) ** 2).sum())
        soma_quadrados_residual = float((grupo["erro"].to_numpy() ** 2).sum())

        picos = grupo.loc[grupo["faixa"] == "pico"]
        entressafra = grupo.loc[grupo["faixa"] == "entressafra"]

        linhas.append({
            "variante": variante,
            "h": horizonte,
            "MAE_global": grupo["erro"].abs().mean(),
            "R2_global": 1 - soma_quadrados_residual / soma_quadrados_total,
            "n_picos": len(picos),
            "pico_real_medio": picos["real"].mean(),
            "pico_previsto_medio": picos["pred"].mean(),
            "pico_VIES": picos["erro"].mean(),
            "pico_MAE": picos["erro"].abs().mean(),
            "entressafra_MAE": entressafra["erro"].abs().mean(),
        })

    return pd.DataFrame(linhas)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela, colunas_modelo = montar_dados_e_colunas()
    print(f"colunas base: {len(colunas_modelo)}\n", flush=True)

    todas = []
    for rotulo, usa_mes, extras in VARIANTES:
        print(f"--- {rotulo} ---", flush=True)
        for horizonte in HORIZONTES:
            previsoes = rodar_variante(tabela, colunas_modelo, horizonte, usa_mes, extras)
            previsoes["variante"] = rotulo
            todas.append(previsoes)
            print(f"  h={horizonte}: {len(previsoes)} semanas", flush=True)

    previsoes_finais = pd.concat(todas, ignore_index=True)
    resumo = resumir(previsoes_finais)

    previsoes_finais.to_csv(PASTA_SAIDAS / "remedios_previsoes.csv", index=False)
    resumo.to_csv(PASTA_SAIDAS / "remedios_resumo.csv", index=False)

    print("\n" + "=" * 118, flush=True)
    print("VIES NO PICO (o alvo do teste) — quanto mais perto de zero, melhor", flush=True)
    print("=" * 118, flush=True)
    tabela_vies = resumo.pivot_table(index="h", columns="variante", values="pico_VIES")
    print(tabela_vies.round(1).to_string(), flush=True)

    print("\n=== MAE no pico ===", flush=True)
    print(resumo.pivot_table(index="h", columns="variante", values="pico_MAE").round(1).to_string(),
          flush=True)

    print("\n=== R2 global (para conferir que nao se quebrou o resto) ===", flush=True)
    print(resumo.pivot_table(index="h", columns="variante", values="R2_global").round(3).to_string(),
          flush=True)

    print("\n=== MAE global ===", flush=True)
    print(resumo.pivot_table(index="h", columns="variante", values="MAE_global").round(1).to_string(),
          flush=True)

    print("\n=== MAE na entressafra (o custo do remedio) ===", flush=True)
    print(resumo.pivot_table(index="h", columns="variante", values="entressafra_MAE").round(2).to_string(),
          flush=True)

    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
