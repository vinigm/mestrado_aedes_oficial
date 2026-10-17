"""Corte temporal do treino: so entra o que ja tinha resposta na data da previsao.

Copiado e simplificado de `modelagem_aedes/motor/corte_temporal.py:36-65`
(`selecionar_treino_ja_respondido`), a regra que corrigiu o vazamento de
13/09/2026.

POR QUE EXISTE

    Cada linha da matriz de um horizonte tem DUAS datas: a de ORIGEM (de onde
    vem as variaveis) e a de RESPOSTA, a origem mais `h` semanas (`data_alvo`).
    A linha so fica pronta na data da resposta: antes disso o rotulo `y_h`
    ainda nao aconteceu. Cortar o treino pela data de origem deixaria entrar
    as `h - 1` linhas mais recentes com rotulo datado DEPOIS da semana que se
    quer prever.

    Exemplo real (docstring do antigo), h = 12: ao prever 26/05/2024 a partir
    de 03/03/2024, o treino incluia a linha de 18/02/2024, cujo rotulo e
    12/05/2024 = 1.510 casos, o pico da epidemia. Em 03/03 esse numero nao
    existia. Medido em 13/09/2026: corrigir custa +31,5% de MAE em h = 4 e
    +52,5% em h = 12.

POR QUE FILTRAR POR DATA E NAO POR POSICAO

    Depois do `dropna` a matriz tem buracos (o vetor e NaN nas semanas da
    enchente de maio/2024). Recuar 12 POSICOES nao equivale a recuar 12
    SEMANAS; a forma curta `iloc[:indice - h + 1]` esta errada.
"""

import pandas as pd

from aedes.configuracao import COLUNA_DATA_DE_ORIGEM


def selecionar_treino_ja_respondido(
    matriz_do_horizonte: pd.DataFrame,
    data_de_origem_do_teste: pd.Timestamp,
    horizonte: int,
) -> pd.DataFrame:
    """Devolve so as linhas cuja RESPOSTA ja tinha acontecido na data da previsao.

    Regra: a linha `s` entra no treino se `s + horizonte semanas <= t`, onde
    `s` e a `data_origem` da linha e `t` e a data de origem do teste.

    A comparacao e `<=`: a linha cuja resposta cai exatamente em `t` ENTRA (o
    valor dela ja e conhecido nesse dia); a que cai em `t + 1 semana` NAO.
    Como `data_alvo = data_origem + horizonte semanas`, a regra equivale a
    `data_alvo <= t`, e nenhuma linha de treino tem resposta posterior a `t`.

    A funcao calcula `s + horizonte` a partir de `data_origem` (como o
    codigo antigo), sem ler a coluna `data_alvo`.

    Args:
        matriz_do_horizonte: Matriz de um horizonte (saida de
            `aedes.variaveis.montar_matriz_do_horizonte`), sem ausentes e em
            ordem cronologica, com a coluna `data_origem`. Nao e modificada.
        data_de_origem_do_teste: Data da semana a partir da qual a previsao
            e feita (`t`).
        horizonte: Quantas semanas a frente se preve (inteiro >= 1).

    Returns:
        Um recorte de `matriz_do_horizonte` (mesmas colunas, mesmo indice e
        mesma ordem das linhas liberadas). Pode ser vazio.

    Raises:
        KeyError: Se faltar a coluna `data_origem`.
        ValueError: Se `horizonte` nao for inteiro >= 1 ou a data de origem
            do teste for ausente (NaT).
    """
    horizonte_e_valido = isinstance(horizonte, int) and not isinstance(horizonte, bool)
    if not horizonte_e_valido or horizonte < 1:
        raise ValueError(f"horizonte deve ser inteiro >= 1, recebido {horizonte!r}.")

    if COLUNA_DATA_DE_ORIGEM not in matriz_do_horizonte.columns:
        raise KeyError(f"Coluna {COLUNA_DATA_DE_ORIGEM!r} ausente na matriz do horizonte.")

    data_do_teste = pd.Timestamp(data_de_origem_do_teste)
    if pd.isna(data_do_teste):
        raise ValueError("data_de_origem_do_teste nao pode ser ausente (NaT).")

    atraso_do_horizonte = pd.Timedelta(weeks=horizonte)
    datas_de_origem = matriz_do_horizonte[COLUNA_DATA_DE_ORIGEM]
    datas_da_resposta = datas_de_origem + atraso_do_horizonte
    linha_ja_respondida = datas_da_resposta <= data_do_teste

    return matriz_do_horizonte.loc[linha_ja_respondida]
