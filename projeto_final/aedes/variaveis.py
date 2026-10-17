"""Variaveis do modelo: defasagens, medias moveis, sazonalidade e o alvo h semanas a frente.

Funcoes puras: recebem a tabela semanal JA CORTADA (saida de
`aedes.dados.aplicar_corte_de_maturidade`) e uma configuracao, e devolvem um
DataFrame novo. Nenhuma le ou grava arquivo, e nenhuma depende de variavel de
modulo trocada em execucao: as defasagens e as colunas de clima vem de
`ConfiguracaoVariaveis`.

Replica, sem nenhuma correcao, a receita do codigo antigo:
    - `modelagem_aedes/dominio/features.py:64-114` (`construir_features_temporais`):
      defasagens por `shift`, medias moveis por `rolling(4).mean()`, seno e
      cosseno de 2*pi*semana/52;
    - `modelagem_aedes/dominio/features.py:118-156` (`construir_alvo_horizonte`):
      `y_h = casos.shift(-h)` e a sazonalidade da semana-alvo;
    - `analises/2026-09-23_bateria_noturna/harness.py:233-242`: `dropna` das 22
      variaveis mais o alvo, ordenacao por data e renumeracao do indice.
"""

import numpy as np
import pandas as pd

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    ConfiguracaoDados,
    ConfiguracaoVariaveis,
    nome_da_variavel_defasada,
)

UMA_SEMANA = pd.Timedelta(weeks=1)


def validar_tabela_para_variaveis(
    tabela_cortada: pd.DataFrame,
    configuracao_variaveis: ConfiguracaoVariaveis,
    configuracao_dados: ConfiguracaoDados,
) -> None:
    """Confere que a tabela tem o que a receita consome e e uma grade semanal contigua.

    As defasagens sao `shift` por POSICAO. So equivalem a "N semanas atras" se
    cada linha for exatamente uma semana depois da anterior; por isso a grade e
    exigida aqui, e nao reordenada em silencio. (O codigo antigo apenas
    assumia essa ordem, na docstring de `construir_features_temporais`.)

    Args:
        tabela_cortada: Tabela semanal depois do corte de maturidade.
        configuracao_variaveis: Colunas do vetor, da semana e do clima.
        configuracao_dados: Nomes da coluna de data e da de casos.

    Raises:
        KeyError: Se faltar coluna que a receita consome.
        ValueError: Se a data nao for do tipo data, tiver ausente, ou a grade
            nao for estritamente semanal e crescente.
    """
    colunas_necessarias = [
        configuracao_dados.coluna_de_data,
        configuracao_dados.coluna_de_casos,
        configuracao_variaveis.coluna_da_semana,
        configuracao_variaveis.coluna_do_vetor,
    ]
    for variavel_de_clima in configuracao_variaveis.variaveis_de_clima:
        colunas_necessarias.append(variavel_de_clima.coluna_de_origem)

    colunas_ausentes = []
    for nome_da_coluna in colunas_necessarias:
        if nome_da_coluna not in tabela_cortada.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes na tabela das variaveis: {sorted(set(colunas_ausentes))}")

    datas = tabela_cortada[configuracao_dados.coluna_de_data]
    if not pd.api.types.is_datetime64_any_dtype(datas):
        raise ValueError(
            f"A coluna {configuracao_dados.coluna_de_data!r} deve ser de data, "
            f"mas tem dtype {datas.dtype}."
        )
    if datas.isna().any():
        raise ValueError(f"A coluna {configuracao_dados.coluna_de_data!r} tem datas ausentes.")

    intervalos = datas.diff().dropna()
    intervalos_diferentes_de_uma_semana = intervalos[intervalos != UMA_SEMANA]
    if not intervalos_diferentes_de_uma_semana.empty:
        raise ValueError(
            "A grade deve ser semanal, crescente e sem buraco; "
            f"{len(intervalos_diferentes_de_uma_semana)} intervalo(s) diferente(s) de 7 dias."
        )


def calcular_seno_e_cosseno_da_semana(
    semana: pd.Series,
    semanas_por_ano: int,
    nome_do_seno: str,
    nome_do_cosseno: str,
) -> pd.DataFrame:
    """Codifica a epoca do ano como seno e cosseno de `2*pi*semana/semanas_por_ano`.

    A ordem das operacoes e a do codigo antigo (`features.py:111` e `:153`):
    `(2 * pi * semana) / semanas_por_ano`. Semana ausente (NaN) da seno e
    cosseno ausentes.

    Args:
        semana: Numero da semana epidemiologica de cada linha.
        semanas_por_ano: Divisor do angulo (52).
        nome_do_seno: Nome da coluna do seno.
        nome_do_cosseno: Nome da coluna do cosseno.

    Returns:
        DataFrame com duas colunas (seno e cosseno), no indice de `semana`.
    """
    angulo_sazonal = 2 * np.pi * semana / semanas_por_ano
    sazonalidade = pd.DataFrame(index=semana.index)
    sazonalidade[nome_do_seno] = np.sin(angulo_sazonal)
    sazonalidade[nome_do_cosseno] = np.cos(angulo_sazonal)
    return sazonalidade


def construir_variaveis_de_origem(
    tabela_cortada: pd.DataFrame,
    configuracao_variaveis: ConfiguracaoVariaveis,
    configuracao_dados: ConfiguracaoDados,
) -> pd.DataFrame:
    """Monta as variaveis que dependem so da semana de origem (20 das 22).

    Sao: casos, casos atrasados, media movel dos casos, sazonalidade da semana
    de origem, as colunas de clima congeladas, vetor, vetor atrasado e media
    movel do vetor. As duas restantes (seno e cosseno da semana-alvo) dependem
    do horizonte e entram em `montar_matriz_do_horizonte`.

    Ausentes se propagam: `shift` e `rolling(janela).mean()` devolvem NaN onde
    faltar dado (inclusive os casos apagados pelo corte de maturidade); nada
    e preenchido aqui.

    Args:
        tabela_cortada: Tabela semanal depois do corte de maturidade, em grade
            semanal contigua. Nao e modificada.
        configuracao_variaveis: Defasagens, janela e colunas de clima.
        configuracao_dados: Nomes da coluna de data e da de casos.

    Returns:
        DataFrame novo, no mesmo indice da tabela, com uma coluna por variavel
        de origem (nomes de `configuracao_variaveis`), sem ordem relevante.

    Raises:
        KeyError: Se faltar coluna que a receita consome.
        ValueError: Se a grade nao for semanal contigua.
    """
    validar_tabela_para_variaveis(tabela_cortada, configuracao_variaveis, configuracao_dados)

    casos = tabela_cortada[configuracao_dados.coluna_de_casos]
    vetor = tabela_cortada[configuracao_variaveis.coluna_do_vetor]
    semana = tabela_cortada[configuracao_variaveis.coluna_da_semana]
    nome_dos_casos = configuracao_variaveis.nome_da_variavel_de_casos
    nome_do_vetor = configuracao_variaveis.coluna_do_vetor
    janela = configuracao_variaveis.janela_da_media_movel

    variaveis_por_nome: dict[str, pd.Series] = {}

    variaveis_por_nome[nome_dos_casos] = casos
    for defasagem in configuracao_variaveis.defasagens_de_casos:
        nome_da_defasagem = nome_da_variavel_defasada(nome_dos_casos, defasagem)
        variaveis_por_nome[nome_da_defasagem] = casos.shift(defasagem)
    nome_da_media_de_casos = configuracao_variaveis.nome_da_media_movel_de_casos()
    variaveis_por_nome[nome_da_media_de_casos] = casos.rolling(janela).mean()

    variaveis_por_nome[nome_do_vetor] = vetor
    for defasagem in configuracao_variaveis.defasagens_do_vetor:
        nome_da_defasagem = nome_da_variavel_defasada(nome_do_vetor, defasagem)
        variaveis_por_nome[nome_da_defasagem] = vetor.shift(defasagem)
    nome_da_media_do_vetor = configuracao_variaveis.nome_da_media_movel_do_vetor()
    variaveis_por_nome[nome_da_media_do_vetor] = vetor.rolling(janela).mean()

    for variavel_de_clima in configuracao_variaveis.variaveis_de_clima:
        coluna_de_clima = tabela_cortada[variavel_de_clima.coluna_de_origem]
        if variavel_de_clima.defasagem_em_semanas == 0:
            variaveis_por_nome[variavel_de_clima.nome] = coluna_de_clima
        else:
            variaveis_por_nome[variavel_de_clima.nome] = coluna_de_clima.shift(
                variavel_de_clima.defasagem_em_semanas
            )

    nome_do_seno_da_origem, nome_do_cosseno_da_origem = (
        configuracao_variaveis.nomes_da_sazonalidade_da_origem
    )
    sazonalidade_da_origem = calcular_seno_e_cosseno_da_semana(
        semana,
        configuracao_variaveis.semanas_por_ano,
        nome_do_seno_da_origem,
        nome_do_cosseno_da_origem,
    )
    variaveis_por_nome[nome_do_seno_da_origem] = sazonalidade_da_origem[nome_do_seno_da_origem]
    variaveis_por_nome[nome_do_cosseno_da_origem] = sazonalidade_da_origem[nome_do_cosseno_da_origem]

    return pd.DataFrame(variaveis_por_nome, index=tabela_cortada.index)


def montar_matriz_do_horizonte(
    tabela_cortada: pd.DataFrame,
    horizonte: int,
    configuracao_variaveis: ConfiguracaoVariaveis,
    configuracao_dados: ConfiguracaoDados,
) -> pd.DataFrame:
    """Monta a matriz de treino e teste de um horizonte: uma linha por semana de origem.

    Cada linha diz: "a partir da semana de origem `data_origem`, com estas 22
    variaveis, o numero de casos `horizonte` semanas depois (`data_alvo`) foi
    `y_h`".

    Regras (as do codigo antigo, `harness.py:233-242`):
        1. `y_h` e os casos (JA cortados) deslocados `horizonte` semanas para
           tras na grade (`shift(-h)`); as ultimas `h` linhas ficam sem alvo.
        2. `alvo_sin` e `alvo_cos` vem da semana epidemiologica da semana-alvo
           (`semana.shift(-h)`), nao da data.
        3. Descarta toda linha com ausente em QUALQUER das 22 variaveis ou no
           alvo (`dropna`). Isso tira o inicio da serie (casos so a partir de
           18/02/2018 e lags/media movel de 4 semanas), as semanas sem vetor
           (enchente de 2024) e o fim (casos apagados pelo corte).
        4. A ordem das linhas e a cronologica; o indice e renumerado de 0.
        5. A ordem das colunas e `data_origem`, `data_alvo`, as 22 variaveis na
           ordem de `configuracao_variaveis.nomes_das_variaveis` e `y_h`.

    Args:
        tabela_cortada: Tabela semanal depois do corte de maturidade
            (`aplicar_corte_de_maturidade`), em grade semanal contigua. Nao e
            modificada.
        horizonte: Semanas a frente (inteiro >= 1).
        configuracao_variaveis: Receita das variaveis e a ordem final.
        configuracao_dados: Nomes da coluna de data e da de casos.

    Returns:
        DataFrame novo. Pode ter zero linhas (tabela vazia ou sem nenhuma
        linha completa); as colunas saem sempre as mesmas.

    Raises:
        ValueError: Se `horizonte` nao for inteiro >= 1 ou a grade nao for
            semanal contigua.
        KeyError: Se faltar coluna que a receita consome.
    """
    horizonte_e_valido = isinstance(horizonte, int) and not isinstance(horizonte, bool)
    if not horizonte_e_valido or horizonte < 1:
        raise ValueError(f"horizonte deve ser inteiro >= 1, recebido {horizonte!r}.")

    variaveis_de_origem = construir_variaveis_de_origem(
        tabela_cortada, configuracao_variaveis, configuracao_dados
    )

    datas_de_origem = tabela_cortada[configuracao_dados.coluna_de_data]
    casos = tabela_cortada[configuracao_dados.coluna_de_casos]
    semana = tabela_cortada[configuracao_variaveis.coluna_da_semana]

    alvo_em_casos = casos.shift(-horizonte)
    semana_do_alvo = semana.shift(-horizonte)
    nome_do_seno_do_alvo, nome_do_cosseno_do_alvo = (
        configuracao_variaveis.nomes_da_sazonalidade_do_alvo
    )
    sazonalidade_do_alvo = calcular_seno_e_cosseno_da_semana(
        semana_do_alvo,
        configuracao_variaveis.semanas_por_ano,
        nome_do_seno_do_alvo,
        nome_do_cosseno_do_alvo,
    )

    colunas_por_nome: dict[str, pd.Series] = {}
    colunas_por_nome[COLUNA_DATA_DE_ORIGEM] = datas_de_origem
    colunas_por_nome[COLUNA_DATA_ALVO] = datas_de_origem + pd.Timedelta(weeks=horizonte)
    for nome_da_variavel in configuracao_variaveis.nomes_das_variaveis:
        if nome_da_variavel in variaveis_de_origem.columns:
            colunas_por_nome[nome_da_variavel] = variaveis_de_origem[nome_da_variavel]
        else:
            colunas_por_nome[nome_da_variavel] = sazonalidade_do_alvo[nome_da_variavel]
    colunas_por_nome[COLUNA_DO_ALVO] = alvo_em_casos

    matriz_com_ausentes = pd.DataFrame(colunas_por_nome, index=tabela_cortada.index)

    colunas_que_nao_podem_faltar = list(configuracao_variaveis.nomes_das_variaveis)
    colunas_que_nao_podem_faltar.append(COLUNA_DO_ALVO)
    matriz_completa = matriz_com_ausentes.dropna(subset=colunas_que_nao_podem_faltar)

    return matriz_completa.reset_index(drop=True)
