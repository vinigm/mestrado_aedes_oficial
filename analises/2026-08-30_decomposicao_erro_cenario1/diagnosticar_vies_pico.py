"""

Diagnostica POR QUE o modelo do cenario 1 subestima os picos de dengue.

Dois testes, pre-declarados em 30/08/2026 antes de rodar:

  TESTE A - a hipotese da nao-extrapolacao.
    LightGBM e um conjunto de arvores, e arvore nao extrapola: a previsao dela
    e sempre uma media ponderada de valores que ela ja viu no treino, entao ela
    NAO CONSEGUE prever um numero maior que o maximo do treino. Como cada
    epidemia de POA foi maior que todas as anteriores (2022: 879 -> 2023: 762
    -> 2024: 1.855 -> 2025: 2.381), o modelo estaria batendo num teto estrutural.
    O teste grava, em cada passo, o maximo do alvo no treino e compara com o
    real e com o previsto.

  TESTE B - o remedio padrao (alvo em log).
    Reroda tudo treinando em log1p(casos) e desfazendo com expm1. E o que se
    faz normalmente com serie muito assimetrica.

PREVISAO REGISTRADA ANTES DE RODAR: se a causa for a nao-extrapolacao, o log
NAO conserta o vies do pico - ele comprime a escala, mas a arvore continua
limitada ao maximo visto, e ao voltar para a escala original o teto continua
sendo o mesmo pico historico. Se o log CONSERTAR, minha hipotese esta errada.

Uso:  python diagnosticar_vies_pico.py

"""

import sys
import time
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import numpy as np
import pandas as pd

from acesso import fontes
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from dominio.features import construir_alvo_horizonte

PASTA_SAIDAS = PASTA_ANALISE / "saidas"
HORIZONTES = (1, 4, 8, 12)
LIMITE_PICO = 100


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


def rodar_walk_forward(
    tabela: pd.DataFrame,
    colunas_modelo: list[str],
    horizonte: int,
    usar_log: bool,
) -> pd.DataFrame:
    """

    Walk-forward do cenario 1, gravando o teto do treino em cada passo.

    Args:
        tabela: A tabela semanal ja com as features.
        colunas_modelo: As colunas de entrada.
        horizonte: Quantas semanas a frente prever.
        usar_log: Se verdadeiro, treina em log1p(casos) e desfaz com expm1.

    Returns:
        Uma linha por semana testada, com real, previsto e o maximo que o
        modelo tinha visto no treino ate ali.

    """
    config = CIDADE_REGRESSAO

    dados = construir_alvo_horizonte(tabela, config.coluna_alvo, horizonte)
    colunas_com_sazonalidade = colunas_modelo + ["alvo_sin", "alvo_cos"]
    validos = (
        dados.dropna(subset=colunas_com_sazonalidade + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    linhas = []
    for indice_corte in range(config.minimo_semanas_treino, len(validos), config.passo):
        treino = validos.iloc[:indice_corte]
        teste = validos.iloc[indice_corte:indice_corte + 1]

        alvo_treino = treino["y_h"]
        if usar_log:
            alvo_treino = np.log1p(alvo_treino)

        modelo = config.modelo.criar()
        modelo.fit(treino[colunas_com_sazonalidade], alvo_treino)
        previsao = modelo.predict(teste[colunas_com_sazonalidade])[0]

        if usar_log:
            previsao = np.expm1(previsao)

        linhas.append({
            "h": horizonte,
            "data": teste["data"].to_numpy()[0],
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": float(previsao),
            "maximo_visto_no_treino": float(treino["y_h"].max()),
        })

    return pd.DataFrame(linhas)


def resumir_picos(previsoes: pd.DataFrame, rotulo: str) -> pd.DataFrame:
    """Resume, so nas semanas de pico, o erro e a relacao com o teto do treino."""
    picos = previsoes.loc[previsoes["real"] > LIMITE_PICO].copy()

    linhas = []
    for horizonte, grupo in picos.groupby("h"):
        acima_do_teto = grupo["real"] > grupo["maximo_visto_no_treino"]
        linhas.append({
            "variante": rotulo,
            "h": horizonte,
            "n_picos": len(grupo),
            "real_medio": grupo["real"].mean(),
            "pred_medio": grupo["pred"].mean(),
            "vies_medio": (grupo["pred"] - grupo["real"]).mean(),
            "teto_treino_medio": grupo["maximo_visto_no_treino"].mean(),
            "picos_ACIMA_do_teto": int(acima_do_teto.sum()),
            "pred_como_pct_do_teto": (grupo["pred"] / grupo["maximo_visto_no_treino"]).mean(),
        })

    return pd.DataFrame(linhas)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela, colunas_modelo = montar_dados_e_colunas()
    print(f"colunas do modelo: {len(colunas_modelo)}\n", flush=True)

    todas_previsoes = []
    resumos = []

    for usar_log, rotulo in ((False, "original"), (True, "log1p")):
        print(f"--- variante: {rotulo} ---", flush=True)
        for horizonte in HORIZONTES:
            previsoes = rodar_walk_forward(tabela, colunas_modelo, horizonte, usar_log)
            previsoes["variante"] = rotulo
            todas_previsoes.append(previsoes)
            print(f"  h={horizonte}: {len(previsoes)} semanas", flush=True)

        previsoes_da_variante = pd.concat(
            [p for p in todas_previsoes if p["variante"].iloc[0] == rotulo], ignore_index=True
        )
        resumos.append(resumir_picos(previsoes_da_variante, rotulo))

    previsoes_finais = pd.concat(todas_previsoes, ignore_index=True)
    resumo_final = pd.concat(resumos, ignore_index=True)

    previsoes_finais.to_csv(PASTA_SAIDAS / "diagnostico_previsoes.csv", index=False)
    resumo_final.to_csv(PASTA_SAIDAS / "diagnostico_picos.csv", index=False)

    print("\n" + "=" * 110, flush=True)
    print("TESTE A — o modelo bate no teto do que ja viu?  (so semanas de pico, real > 100)")
    print("=" * 110, flush=True)
    print(resumo_final.round(2).to_string(index=False), flush=True)

    print("\n" + "=" * 110, flush=True)
    print("TESTE B — o log consertou o vies do pico?")
    print("=" * 110, flush=True)
    comparacao = resumo_final.pivot_table(index="h", columns="variante", values="vies_medio")
    comparacao["melhorou_com_log"] = comparacao["log1p"].abs() < comparacao["original"].abs()
    print(comparacao.round(2).to_string(), flush=True)

    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
