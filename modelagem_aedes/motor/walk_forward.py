"""

Este arquivo e o "motor" que treina no passado e tenta prever o futuro,
semana a semana, pra saber se vai dar surto de dengue.

Antes, esse pedaco de codigo ficava copiado dentro de cada script de
modelagem; agora ele mora aqui, em um lugar so. As colunas usadas no modelo
e os ajustes do modelo chegam como argumentos, entao esse mesmo motor serve
pra qualquer experimento de deteccao de surto da cidade, nao so um caso
especifico.

"""

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

from config import settings

# Quantas semanas de diferenca ainda contam como "a mesma epoca do ano" (o
# calendario e circular: a semana 52 fica pertinho da semana 1 de novo).
DISTANCIA_MAXIMA_SEMANA_SAZONAL = 1

# A partir de qual probabilidade a gente diz que vai dar surto.
LIMIAR_DECISAO_PROBABILIDADE = 0.5


def executar_walk_forward_surto(
    dados: pd.DataFrame,
    features: list[str],
    coluna_fonte: str,
    horizonte: int,
    percentil: int,
    parametros_lgbm: dict,
    passo: int = 1,
) -> pd.DataFrame:
    """

    Este e o loop que treina so com o que ja aconteceu ate uma certa semana e
    tenta prever se vai dar surto la na frente, pra um horizonte (quantas
    semanas a frente) e um percentil (o corte que decide o que conta como
    surto) escolhidos.

    Em cada passo, o modelo treina com todo o historico ate a semana i e tenta
    prever a semana i. Em cada passo, "deu surto" quer dizer: os casos daqui a
    h semanas ficaram maiores ou iguais a um percentil calculado usando SO os
    dados de treino daquele passo (ou seja, sem espiar dado que ainda esta no
    futuro). Tres jeitos de prever usam exatamente as mesmas divisoes de
    treino e teste e o mesmo ponto de corte:
      - o modelo (LGBM) com as colunas escolhidas: clima (e talvez captura de
        mosquito) + o proprio historico de casos + a epoca do ano;
      - o palpite pela epoca do ano: quantas vezes deu surto no treino nessa
        mesma epoca do ano (+-1 semana);
      - o palpite por repeticao: se esta em surto agora, a aposta e que
        continua em surto daqui a h semanas.

    Args:
        dados: Tabela, semana a semana, ja com as colunas calculadas prontas.
        features: Colunas que entram no modelo (sem contar a epoca do ano do
            alvo, que ja e calculada aqui dentro).
        coluna_fonte: Coluna que diz de qual fonte (bloco de dados) cada linha
            veio.
        horizonte: Quantas semanas a frente a gente quer prever.
        percentil: Percentil dos casos que define o corte pra contar como
            surto.
        parametros_lgbm: Ajustes do modelo (LGBMClassifier), escolhidos em
            cada experimento.
        passo: De quantas em quantas semanas testar (1 = testa toda semana).

    Returns:
        Uma tabela com uma linha por semana testada e as colunas: h
        (horizonte), real (se deu surto de verdade), data, prob (probabilidade
        do modelo), pred (previsao do modelo), prob_saz e pred_saz (palpite
        pela epoca do ano), pred_pers (palpite por repeticao).

    """
    dados_trabalho = dados.copy()
    grupos_por_fonte = dados_trabalho.groupby(coluna_fonte, group_keys=False)
    dados_trabalho["casos_h"] = grupos_por_fonte["casos"].shift(-horizonte)
    dados_trabalho["semana_alvo"] = grupos_por_fonte["semana"].shift(-horizonte)

    angulo_sazonal_alvo = 2 * np.pi * dados_trabalho["semana_alvo"] / settings.SEMANAS_POR_ANO
    dados_trabalho["alvo_sin"] = np.sin(angulo_sazonal_alvo)
    dados_trabalho["alvo_cos"] = np.cos(angulo_sazonal_alvo)

    features_com_sazonalidade = features + ["alvo_sin", "alvo_cos"]
    colunas_obrigatorias = features_com_sazonalidade + ["casos_h", "casos", "semana_alvo"]
    dados_validos = (
        dados_trabalho.dropna(subset=colunas_obrigatorias)
        .sort_values("data")
        .reset_index(drop=True)
    )

    linhas_resultado = []
    for indice_corte in range(settings.MINIMO_SEMANAS_TREINO, len(dados_validos), passo):
        treino = dados_validos.iloc[:indice_corte]
        teste = dados_validos.iloc[indice_corte:indice_corte + 1]

        limiar_surto = np.percentile(treino["casos_h"], percentil)
        surto_treino = (treino["casos_h"].to_numpy() >= limiar_surto).astype(int)
        surto_teste = int(teste["casos_h"].to_numpy()[0] >= limiar_surto)
        if len(np.unique(surto_treino)) < 2:
            # Se no treino so apareceu um resultado (so surto ou so
            # nao-surto), pula este passo — nao da pra treinar assim.
            continue

        modelo = LGBMClassifier(**parametros_lgbm)
        modelo.fit(treino[features_com_sazonalidade], surto_treino)
        probabilidade_surto = float(
            modelo.predict_proba(teste[features_com_sazonalidade])[0, 1]
        )

        # Palpite pela epoca do ano: quantas vezes deu surto no treino, na
        # semana do ano (+-1) mais parecida com a que queremos prever (o
        # calendario e circular: a semana 52 fica pertinho da semana 1).
        semana_do_alvo = teste["semana_alvo"].to_numpy()[0]
        diferenca_semanas = np.abs(treino["semana_alvo"].to_numpy() - semana_do_alvo)
        distancia_circular = np.minimum(
            diferenca_semanas, settings.SEMANAS_POR_ANO - diferenca_semanas
        )
        mascara_mesma_semana = distancia_circular <= DISTANCIA_MAXIMA_SEMANA_SAZONAL
        if mascara_mesma_semana.sum() > 0:
            probabilidade_sazonal = float(surto_treino[mascara_mesma_semana].mean())
        else:
            probabilidade_sazonal = float(surto_treino.mean())

        # Palpite por repeticao: se agora esta em surto (casos de hoje >=
        # limiar), a aposta e que continua em surto la na frente.
        surto_persistencia = int(teste["casos"].to_numpy()[0] >= limiar_surto)

        linhas_resultado.append(
            {
                "h": horizonte,
                "real": surto_teste,
                "data": teste["data"].to_numpy()[0],
                "prob": probabilidade_surto,
                "pred": int(probabilidade_surto >= LIMIAR_DECISAO_PROBABILIDADE),
                "prob_saz": probabilidade_sazonal,
                "pred_saz": int(probabilidade_sazonal >= LIMIAR_DECISAO_PROBABILIDADE),
                "pred_pers": surto_persistencia,
            }
        )
    return pd.DataFrame(linhas_resultado)
