"""

Este arquivo treina o modelo varias vezes ao longo do tempo, sempre usando so
o que ja aconteceu pra tentar prever o proximo passo (ou seja: treina no
passado e preve o futuro, semana a semana). Aqui o que se quer adivinhar e um
numero — quantos casos vao acontecer — e nao uma categoria (isso e chamado de
regressao). Serve pra qualquer experimento: quem usa essa funcao manda as
colunas de entrada e os ajustes do modelo por fora.

Tem uma versao parecida pra prever categorias (por exemplo, sim ou nao) no
arquivo motor/walk_forward.py; aqui o resultado e sempre um numero.

"""

import pandas as pd
from lightgbm import LGBMRegressor

from config import settings
from dominio.features import construir_alvo_horizonte


def executar_walk_forward_regressao(
    dados: pd.DataFrame,
    colunas_features: list[str],
    coluna_alvo: str,
    horizontes: tuple[int, ...],
    parametros_lgbm: dict,
    minimo_semanas_treino: int = settings.MINIMO_SEMANAS_TREINO,
    passo: int = 2,
) -> pd.DataFrame:
    """

    Treina e testa o modelo repetidas vezes, sempre aumentando o tanto de
    historico que ele usa pra treinar, e faz isso pra varias distancias no
    futuro (horizontes) ao mesmo tempo.

    Em cada horizonte e cada passo no tempo, o modelo treina com tudo que ja
    aconteceu ate a semana i e tenta prever direto a semana i (sem passar
    pelas semanas do meio).

    Args:
        dados: Tabela semana a semana, ja com as colunas calculadas prontas.
        colunas_features: Colunas de entrada do modelo (sem contar a
            sazonalidade do alvo, que e adicionada aqui dentro).
        coluna_alvo: Nome da coluna que se quer prever (por exemplo, 'casos').
        horizontes: Pra quantas semanas a frente o modelo deve prever.
        parametros_lgbm: Hiperparametros (os ajustes que controlam como o
            modelo aprende) usados no LGBMRegressor.
        minimo_semanas_treino: Quantas semanas de historico sao precisas
            antes de comecar a prever.
        passo: De quantas em quantas semanas o teste e feito.

    Returns:
        Uma tabela com uma linha pra cada combinacao de horizonte e semana
        testada, com as colunas: h, real (valor verdadeiro) e pred (valor
        previsto).

    """
    linhas_resultado = []
    for horizonte in horizontes:
        dados_horizonte = construir_alvo_horizonte(dados, coluna_alvo, horizonte)
        features_com_sazonalidade = colunas_features + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            dados_horizonte.dropna(subset=features_com_sazonalidade + ["y_h"])
            .sort_values("data")
            .reset_index(drop=True)
        )
        for indice_corte in range(minimo_semanas_treino, len(dados_validos), passo):
            treino = dados_validos.iloc[:indice_corte]
            teste = dados_validos.iloc[indice_corte:indice_corte + 1]
            modelo = LGBMRegressor(**parametros_lgbm)
            modelo.fit(treino[features_com_sazonalidade], treino["y_h"])
            previsao = modelo.predict(teste[features_com_sazonalidade])[0]
            linhas_resultado.append(
                {
                    "h": horizonte,
                    "real": teste["y_h"].to_numpy()[0],
                    "pred": previsao,
                }
            )
    return pd.DataFrame(linhas_resultado)
