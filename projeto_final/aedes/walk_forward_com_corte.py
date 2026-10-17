"""Walk-forward com a regra de corte do treino como parametro (E4 e E1).

O laco e o de `aedes.walk_forward.executar_walk_forward`, linha por linha; a
UNICA diferenca e quem escolhe o treino de cada origem. Duas regras:

    RESPOSTA  (a certificada, a do artigo): a linha de origem `s` entra no
              treino se `s + h semanas <= t`, ou seja, so entra o que ja tinha
              resposta em `t`. Reaproveita `selecionar_treino_ja_respondido`.
    PERGUNTA  (o corte ingenuo, da E4): entra toda linha com `s < t`. Isso deixa
              entrar as `h - 1` linhas mais recentes, cujo rotulo `y_h` e datado
              DEPOIS de `t` (vazamento do futuro). E o que a E4 mede: quanto o
              resultado muda se alguem cortar pela data da pergunta.

Em h = 1 as duas regras sao a mesma (numa grade semanal, `s + 1 semana <= t`
equivale a `s < t`); por isso a E4 so difere de h = 2 em diante.

Tambem traz `recortar_matriz_ate_a_data_alvo`, usado pela E1 (so calibracao):
cortar a matriz em `data_alvo <= limite` ANTES do laco da as mesmas previsoes
(bit a bit) que rodar a matriz inteira e filtrar depois, porque, com a regra
RESPOSTA, o treino de cada origem so usa linhas com `data_alvo <= t < data_alvo
da origem`; nenhuma linha removida pelo recorte entraria em algum treino das
origens que sobram.
"""

import enum

import pandas as pd

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    ConfiguracaoAvaliacao,
    ConfiguracaoModelo,
)
from aedes.corte_temporal import selecionar_treino_ja_respondido
from aedes.walk_forward import (
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_PREVISTO,
    COLUNA_DO_REAL,
    COLUNAS_DAS_PREVISOES,
    criar_modelo,
    validar_matriz_para_walk_forward,
)


class RegraDeCorte(enum.Enum):
    """Como o treino de cada origem `t` e cortado."""

    RESPOSTA = "resposta"
    PERGUNTA = "pergunta"


def selecionar_treino_pela_regra(
    matriz_do_horizonte: pd.DataFrame,
    data_de_origem_do_teste: pd.Timestamp,
    horizonte: int,
    regra_de_corte: RegraDeCorte,
) -> pd.DataFrame:
    """Devolve as linhas de treino liberadas para a origem `t` pela regra escolhida.

    Args:
        matriz_do_horizonte: Matriz de um horizonte, sem ausentes, em ordem
            cronologica, com a coluna `data_origem`. Nao e modificada.
        data_de_origem_do_teste: Data `t` da origem do teste.
        horizonte: Semanas a frente (inteiro >= 1).
        regra_de_corte: RESPOSTA (`s + h <= t`, a certificada) ou PERGUNTA
            (`s < t`, o corte ingenuo; a propria linha de teste, `s = t`, fica
            de fora nas duas regras).

    Returns:
        Recorte da matriz (mesmas colunas, mesmo indice, mesma ordem).

    Raises:
        ValueError: Se a regra nao for um `RegraDeCorte`, ou pelas validacoes
            de `selecionar_treino_ja_respondido` (horizonte, data ausente).
        KeyError: Se faltar a coluna `data_origem`.
    """
    if not isinstance(regra_de_corte, RegraDeCorte):
        raise ValueError(f"regra_de_corte deve ser um RegraDeCorte, recebido {regra_de_corte!r}.")

    if regra_de_corte is RegraDeCorte.RESPOSTA:
        return selecionar_treino_ja_respondido(matriz_do_horizonte, data_de_origem_do_teste, horizonte)

    # Regra PERGUNTA: valida pelo mesmo caminho da certificada (horizonte, coluna, data).
    selecionar_treino_ja_respondido(matriz_do_horizonte, data_de_origem_do_teste, horizonte)
    data_do_teste = pd.Timestamp(data_de_origem_do_teste)
    datas_de_origem = matriz_do_horizonte[COLUNA_DATA_DE_ORIGEM]
    linha_anterior_a_pergunta = datas_de_origem < data_do_teste
    return matriz_do_horizonte.loc[linha_anterior_a_pergunta]


def recortar_matriz_ate_a_data_alvo(
    matriz_do_horizonte: pd.DataFrame,
    ultima_data_alvo: pd.Timestamp,
) -> pd.DataFrame:
    """Mantem so as linhas cuja `data_alvo` e menor ou igual ao limite (a calibracao da E1).

    O indice NAO e renumerado: as linhas mantidas sao as mesmas, na mesma
    posicao, da matriz inteira (so o fim some).

    Args:
        matriz_do_horizonte: Matriz de um horizonte, com a coluna `data_alvo`.
        ultima_data_alvo: Limite inclusivo (31/12/2023 na calibracao).

    Returns:
        Copia do recorte, mesmas colunas e ordem.

    Raises:
        KeyError: Se faltar a coluna `data_alvo`.
    """
    if COLUNA_DATA_ALVO not in matriz_do_horizonte.columns:
        raise KeyError(f"Coluna {COLUNA_DATA_ALVO!r} ausente na matriz do horizonte.")
    datas_do_alvo = matriz_do_horizonte[COLUNA_DATA_ALVO]
    linha_dentro_do_limite = datas_do_alvo <= pd.Timestamp(ultima_data_alvo)
    return matriz_do_horizonte.loc[linha_dentro_do_limite].copy()


def executar_walk_forward_com_corte(
    matriz_do_horizonte: pd.DataFrame,
    horizonte: int,
    configuracao_modelo: ConfiguracaoModelo,
    configuracao_avaliacao: ConfiguracaoAvaliacao,
    regra_de_corte: RegraDeCorte,
) -> pd.DataFrame:
    """Roda o walk-forward de UM horizonte com a regra de corte escolhida.

    Identico a `aedes.walk_forward.executar_walk_forward` quando a regra e
    RESPOSTA (teste diferencial, bit a bit). Com PERGUNTA, o treino de cada
    origem `t` inclui as linhas com `data_origem < t`, mesmo as de rotulo
    posterior a `t`.

    Args:
        matriz_do_horizonte: Matriz de um horizonte (de `montar_matriz_do_horizonte`
            ou `montar_matriz_do_braco`), sem ausentes, cronologica.
        horizonte: Semanas a frente (inteiro >= 1); o da matriz.
        configuracao_modelo: Hiperparametros do modelo (inclui a semente).
        configuracao_avaliacao: Usa so treino minimo e passo.
        regra_de_corte: RESPOSTA ou PERGUNTA.

    Returns:
        DataFrame com `h`, `data_origem`, `data_alvo`, `real`, `previsto`, uma
        linha por origem de teste.

    Raises:
        KeyError: Se faltar `data_origem`, `data_alvo` ou `y_h`.
        ValueError: Se a matriz nao passar em `validar_matriz_para_walk_forward`,
            a regra for invalida ou alguma origem ficar sem linha de treino.
    """
    if not isinstance(regra_de_corte, RegraDeCorte):
        raise ValueError(f"regra_de_corte deve ser um RegraDeCorte, recebido {regra_de_corte!r}.")
    nomes_das_variaveis = validar_matriz_para_walk_forward(matriz_do_horizonte, horizonte)

    treino_minimo = configuracao_avaliacao.treino_minimo_em_semanas
    passo = configuracao_avaliacao.passo_do_retreino_em_semanas
    quantidade_de_linhas = len(matriz_do_horizonte)
    atraso_do_horizonte = pd.Timedelta(weeks=horizonte)

    previsoes_por_origem: list[dict[str, object]] = []

    for posicao_da_origem in range(treino_minimo, quantidade_de_linhas, passo):
        linha_de_teste = matriz_do_horizonte.iloc[posicao_da_origem : posicao_da_origem + 1]
        data_de_origem = pd.Timestamp(linha_de_teste[COLUNA_DATA_DE_ORIGEM].iloc[0])

        treino = selecionar_treino_pela_regra(
            matriz_do_horizonte, data_de_origem, horizonte, regra_de_corte
        )
        if len(treino) == 0:
            raise ValueError(
                f"Nenhuma linha de treino liberada em {data_de_origem.date()} "
                f"(horizonte {horizonte}, posicao {posicao_da_origem}, regra {regra_de_corte.value})."
            )

        variaveis_do_treino = treino[nomes_das_variaveis]
        alvo_do_treino = treino[COLUNA_DO_ALVO]
        variaveis_do_teste = linha_de_teste[nomes_das_variaveis]

        # Modelo novo a cada origem: nada da semana anterior e reaproveitado.
        modelo = criar_modelo(configuracao_modelo)
        modelo.fit(variaveis_do_treino, alvo_do_treino)
        previsao_da_semana = float(modelo.predict(variaveis_do_teste)[0])

        valor_real = float(linha_de_teste[COLUNA_DO_ALVO].iloc[0])

        previsoes_por_origem.append(
            {
                COLUNA_DO_HORIZONTE: horizonte,
                COLUNA_DATA_DE_ORIGEM: data_de_origem,
                COLUNA_DATA_ALVO: data_de_origem + atraso_do_horizonte,
                COLUNA_DO_REAL: valor_real,
                COLUNA_DO_PREVISTO: previsao_da_semana,
            }
        )

    return pd.DataFrame(previsoes_por_origem, columns=list(COLUNAS_DAS_PREVISOES))
