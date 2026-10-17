"""Walk-forward: a cada semana de origem, retreina do zero e preve `horizonte` semanas a frente.

Laco unico e puro (nao le nem grava arquivo, sem estado global). Replica, sem
nenhuma correcao, o laco do codigo antigo:
    - `analises/2026-09-23_bateria_noturna/harness.py:218-283` (`rodar_walk_forward`),
      que por sua vez espelha `modelagem_aedes/motor/walk_forward_regressao.py`;
    - minimo de 104 semanas de treino e passo 1: `config/experimentos/cidade_referencia.py`
      (`minimo_semanas_treino`, `passo`);
    - corte do treino pela data da RESPOSTA: `aedes.corte_temporal`.

O QUE O LACO FAZ EM CADA ORIGEM `t`

    1. A origem de teste e a linha de posicao `i` da matriz (a primeira e a
       posicao `treino_minimo_em_semanas`, contando de 0), e `t` e a
       `data_origem` dessa linha.
    2. O treino e so o que ja tinha resposta em `t`: as linhas cuja
       `data_origem + horizonte semanas <= t`. Nunca entra rotulo posterior a `t`.
    3. Um modelo NOVO e treinado nesse treino (nada e reaproveitado da semana
       anterior) e preve a linha de teste. O resultado e a previsao para a
       semana `t + horizonte`.
"""

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    ConfiguracaoAvaliacao,
    ConfiguracaoModelo,
)
from aedes.corte_temporal import selecionar_treino_ja_respondido

COLUNA_DO_HORIZONTE = "h"
COLUNA_DO_REAL = "real"
COLUNA_DO_PREVISTO = "previsto"

COLUNAS_DAS_PREVISOES = (
    COLUNA_DO_HORIZONTE,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DATA_ALVO,
    COLUNA_DO_REAL,
    COLUNA_DO_PREVISTO,
)

# Colunas da matriz que NAO sao variaveis do modelo: as duas datas e o alvo.
COLUNAS_FORA_DAS_VARIAVEIS = (COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO, COLUNA_DO_ALVO)


def nomes_das_variaveis_da_matriz(matriz_do_horizonte: pd.DataFrame) -> list[str]:
    """Lista as variaveis do modelo: todas as colunas da matriz, menos datas e alvo.

    A ORDEM e a da matriz (a de `ConfiguracaoVariaveis.nomes_das_variaveis`,
    com a sazonalidade do alvo no fim). Treinar e prever usam sempre essa mesma
    ordem, como no codigo antigo (`colunas_do_modelo + ["alvo_sin", "alvo_cos"]`).

    Args:
        matriz_do_horizonte: Matriz de um horizonte, saida de
            `aedes.variaveis.montar_matriz_do_horizonte`.

    Returns:
        Os nomes das variaveis, na ordem das colunas.

    Raises:
        KeyError: Se faltar `data_origem`, `data_alvo` ou `y_h`.
    """
    colunas_ausentes = []
    for nome_da_coluna in COLUNAS_FORA_DAS_VARIAVEIS:
        if nome_da_coluna not in matriz_do_horizonte.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes na matriz do horizonte: {colunas_ausentes}")

    nomes_das_variaveis = []
    for nome_da_coluna in matriz_do_horizonte.columns:
        if nome_da_coluna not in COLUNAS_FORA_DAS_VARIAVEIS:
            nomes_das_variaveis.append(nome_da_coluna)
    return nomes_das_variaveis


def validar_matriz_para_walk_forward(
    matriz_do_horizonte: pd.DataFrame,
    horizonte: int,
) -> list[str]:
    """Confere a matriz antes do laco e devolve os nomes das variaveis do modelo.

    Cada erro de entrada aparece aqui, com mensagem clara, e nao como uma
    excecao obscura dentro do treino. O codigo antigo nao validava nada disso
    (DESVIO de seguranca, nao muda resultado em entrada valida).

    Args:
        matriz_do_horizonte: Matriz de um horizonte, sem ausentes, em ordem
            cronologica. Nao e modificada.
        horizonte: Semanas a frente (inteiro >= 1).

    Returns:
        Os nomes das variaveis do modelo, na ordem da matriz.

    Raises:
        KeyError: Se faltar `data_origem`, `data_alvo` ou `y_h`.
        ValueError: Se o horizonte for invalido, a matriz tiver ausente em
            variavel ou alvo, as datas nao forem crescentes, ou `data_alvo`
            nao for `data_origem` mais `horizonte` semanas.
    """
    horizonte_e_valido = isinstance(horizonte, int) and not isinstance(horizonte, bool)
    if not horizonte_e_valido or horizonte < 1:
        raise ValueError(f"horizonte deve ser inteiro >= 1, recebido {horizonte!r}.")

    nomes_das_variaveis = nomes_das_variaveis_da_matriz(matriz_do_horizonte)
    if len(nomes_das_variaveis) == 0:
        raise ValueError("A matriz nao tem nenhuma variavel alem das datas e do alvo.")

    colunas_do_modelo = nomes_das_variaveis + [COLUNA_DO_ALVO]
    quantidade_de_ausentes = int(matriz_do_horizonte[colunas_do_modelo].isna().sum().sum())
    if quantidade_de_ausentes > 0:
        raise ValueError(
            f"A matriz tem {quantidade_de_ausentes} valor(es) ausente(s) nas variaveis ou no alvo; "
            "o walk-forward exige a matriz sem ausentes (saida de montar_matriz_do_horizonte)."
        )

    datas_de_origem = matriz_do_horizonte[COLUNA_DATA_DE_ORIGEM]
    if not datas_de_origem.is_monotonic_increasing or datas_de_origem.duplicated().any():
        raise ValueError("`data_origem` deve ser estritamente crescente.")

    datas_do_alvo_esperadas = datas_de_origem + pd.Timedelta(weeks=horizonte)
    alvo_confere = (matriz_do_horizonte[COLUNA_DATA_ALVO] == datas_do_alvo_esperadas).all()
    if not alvo_confere:
        raise ValueError(
            f"`data_alvo` nao e `data_origem` + {horizonte} semana(s) em todas as linhas; "
            "a matriz nao e a do horizonte informado."
        )

    return nomes_das_variaveis


def criar_modelo(configuracao_modelo: ConfiguracaoModelo) -> HistGradientBoostingRegressor:
    """Cria um HistGradientBoostingRegressor NOVO (sem treino) com a configuracao dada.

    Args:
        configuracao_modelo: Hiperparametros (folha 5 ou folha 20).

    Returns:
        O modelo, nao treinado.
    """
    parametros = configuracao_modelo.parametros_do_sklearn()
    return HistGradientBoostingRegressor(**parametros)


def executar_walk_forward(
    matriz_do_horizonte: pd.DataFrame,
    horizonte: int,
    configuracao_modelo: ConfiguracaoModelo,
    configuracao_avaliacao: ConfiguracaoAvaliacao,
) -> pd.DataFrame:
    """Roda o walk-forward de UM horizonte: janela expansiva, retreino a cada origem.

    Para cada origem de teste `t` (a partir da posicao
    `treino_minimo_em_semanas`, de `passo_do_retreino_em_semanas` em
    `passo_do_retreino_em_semanas` linhas), treina um modelo novo so com as
    linhas ja respondidas em `t` (`selecionar_treino_ja_respondido`) e preve a
    linha de `t`. A previsao e para a semana `t + horizonte`.

    A funcao nao filtra pela janela de avaliacao: devolve TODAS as previsoes
    do walk-forward (a partir da 105a linha, em 2020-03), e quem avalia recorta
    a janela por `data_alvo` (como as previsoes salvas do codigo antigo).

    Args:
        matriz_do_horizonte: Matriz de um horizonte (saida de
            `aedes.variaveis.montar_matriz_do_horizonte`), sem ausentes, em
            ordem cronologica. As variaveis do modelo sao as colunas fora
            `data_origem`, `data_alvo` e `y_h`, nessa ordem. Nao e modificada.
        horizonte: Semanas a frente (inteiro >= 1); deve ser o da matriz.
        configuracao_modelo: Hiperparametros do modelo (inclui a semente).
        configuracao_avaliacao: Usa so `treino_minimo_em_semanas` e
            `passo_do_retreino_em_semanas`.

    Returns:
        DataFrame novo com uma linha por origem de teste e as colunas `h`,
        `data_origem`, `data_alvo`, `real`, `previsto`, na ordem das origens.
        `real` e `y_h` da linha; `previsto` e a previsao (float). Vazio, mas
        com as mesmas colunas, se a matriz nao tiver linhas depois do treino
        minimo.

    Raises:
        KeyError: Se faltar `data_origem`, `data_alvo` ou `y_h`.
        ValueError: Se a matriz nao passar em `validar_matriz_para_walk_forward`
            ou se alguma origem de teste ficar sem nenhuma linha de treino.
    """
    nomes_das_variaveis = validar_matriz_para_walk_forward(matriz_do_horizonte, horizonte)

    treino_minimo = configuracao_avaliacao.treino_minimo_em_semanas
    passo = configuracao_avaliacao.passo_do_retreino_em_semanas
    quantidade_de_linhas = len(matriz_do_horizonte)
    atraso_do_horizonte = pd.Timedelta(weeks=horizonte)

    previsoes_por_origem: list[dict[str, object]] = []

    for posicao_da_origem in range(treino_minimo, quantidade_de_linhas, passo):
        linha_de_teste = matriz_do_horizonte.iloc[posicao_da_origem : posicao_da_origem + 1]
        data_de_origem = pd.Timestamp(linha_de_teste[COLUNA_DATA_DE_ORIGEM].iloc[0])

        treino = selecionar_treino_ja_respondido(matriz_do_horizonte, data_de_origem, horizonte)
        if len(treino) == 0:
            raise ValueError(
                f"Nenhuma linha de treino ja respondida em {data_de_origem.date()} "
                f"(horizonte {horizonte}, posicao {posicao_da_origem})."
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

    previsoes = pd.DataFrame(previsoes_por_origem, columns=list(COLUNAS_DAS_PREVISOES))
    return previsoes
