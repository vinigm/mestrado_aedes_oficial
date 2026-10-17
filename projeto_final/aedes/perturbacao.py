"""Perturbacao do ultimo bit da matriz, para medir o piso de ruido numerico (pre-declaracao 8b).

O ACHADO que motiva este modulo (certificacao do ciclo 3): o HistGradientBoosting
quantilico e sensivel ao ULTIMO BIT da entrada. Uma matriz que difere da
original em ate 2,2e-16 (arredondamento de seno, cosseno ou media movel) muda
previsoes da folha 20 em ate 31 casos. Logo, uma diferenca pequena de MAE entre
dois bracos pode ser so ruido numerico. A medida: rodar o mesmo braco com
varias perturbacoes do ultimo bit e ver o quanto o MAE se mexe (o "piso de
ruido").

AS PERTURBACOES
    1. `csv`: a matriz lida do gabarito `testes/referencia_antiga/matriz_hXX.csv`
       (os mesmos numeros, passados por texto de 15 digitos); e a diferenca de
       arredondamento REAL que o achado observou.
    2. Sementes 1 a 4: cada celula de cada coluna CONTINUA soma ou subtrai 1
       ulp (`np.nextafter(x, +inf)` ou `np.nextafter(x, -inf)`), com a direcao
       sorteada por `np.random.default_rng(semente)`. Datas e `y_h` nao mudam;
       colunas de valores inteiros (contagens de casos) tambem nao.

COLUNA CONTINUA: variavel com ao menos um valor nao inteiro na matriz. Contagens
(`casos`, `casos_lag1..4`) ficam de fora porque um numero inteiro nao carrega
arredondamento.

ATENCAO, ZEROS: `np.nextafter(0.0, +-inf)` e +-5e-324 (o menor denormal). Numa
coluna continua com zeros exatos (por exemplo `casos_mm4` = 0 em 91 semanas)
isso transforma UM valor distinto em TRES, o que o modelo pode usar como
particao; nao e o que o arredondamento real faria (a media de zeros e 0 exato).
Por isso `perturbar_ultimo_bit` aceita `perturbar_zeros=False`, que deixa os
zeros exatos intactos; o padrao (`True`) e o literal da pre-declaracao.

Funcoes puras: nao leem nem gravam arquivo.
"""

import numpy as np
import pandas as pd

from aedes.configuracao import COLUNA_DATA_ALVO, COLUNA_DATA_DE_ORIGEM, COLUNA_DO_ALVO
from aedes.walk_forward import COLUNAS_FORA_DAS_VARIAVEIS, nomes_das_variaveis_da_matriz


def identificar_colunas_continuas(matriz_do_horizonte: pd.DataFrame) -> list[str]:
    """Lista as variaveis do modelo com ao menos um valor nao inteiro.

    Args:
        matriz_do_horizonte: Matriz de um horizonte (com `data_origem`,
            `data_alvo` e `y_h`); as variaveis sao as demais colunas.

    Returns:
        Os nomes das colunas continuas, na ordem das colunas da matriz.

    Raises:
        KeyError: Se faltar `data_origem`, `data_alvo` ou `y_h`.
        ValueError: Se alguma variavel tiver valor ausente ou infinito.
    """
    nomes_das_variaveis = nomes_das_variaveis_da_matriz(matriz_do_horizonte)
    colunas_continuas: list[str] = []
    for nome_da_variavel in nomes_das_variaveis:
        valores = matriz_do_horizonte[nome_da_variavel].to_numpy(dtype=float)
        if not np.isfinite(valores).all():
            raise ValueError(f"A variavel {nome_da_variavel!r} tem valor ausente ou infinito.")
        valores_arredondados = np.round(valores)
        tem_valor_nao_inteiro = bool((valores != valores_arredondados).any())
        if tem_valor_nao_inteiro:
            colunas_continuas.append(nome_da_variavel)
    return colunas_continuas


def perturbar_ultimo_bit(
    matriz_do_horizonte: pd.DataFrame,
    semente: int,
    perturbar_zeros: bool = True,
) -> pd.DataFrame:
    """Soma ou subtrai 1 ulp de cada celula das colunas continuas, direcao sorteada pela semente.

    Para cada coluna continua, na ordem das colunas, sorteia (com
    `np.random.default_rng(semente)`, um unico gerador percorrendo as colunas)
    uma direcao por celula: `+inf` ou `-inf`, com probabilidade 1/2; a celula
    vira `np.nextafter(x, direcao)`. Datas, `y_h` e colunas inteiras nao mudam.
    A mesma semente sobre a mesma matriz da sempre o mesmo resultado.

    Args:
        matriz_do_horizonte: Matriz de um horizonte, sem ausentes. Nao e modificada.
        semente: Semente do gerador (1 a 4 na pre-declaracao).
        perturbar_zeros: Se `False`, celulas exatamente iguais a zero nao sao
            perturbadas (ver o aviso sobre zeros no topo do modulo).

    Returns:
        Copia da matriz com as colunas continuas perturbadas; mesmas colunas,
        indice e dtypes.

    Raises:
        KeyError: Se faltar `data_origem`, `data_alvo` ou `y_h`.
        ValueError: Se a semente nao for inteiro, ou se houver variavel ausente
            ou infinita.
    """
    semente_e_valida = isinstance(semente, (int, np.integer)) and not isinstance(semente, bool)
    if not semente_e_valida:
        raise ValueError(f"semente deve ser inteiro, recebido {semente!r}.")

    colunas_continuas = identificar_colunas_continuas(matriz_do_horizonte)
    gerador = np.random.default_rng(int(semente))
    matriz_perturbada = matriz_do_horizonte.copy()
    quantidade_de_linhas = len(matriz_do_horizonte)

    for nome_da_coluna in colunas_continuas:
        valores_originais = matriz_do_horizonte[nome_da_coluna].to_numpy(dtype=float)
        sorteio_para_cima = gerador.random(quantidade_de_linhas) < 0.5
        direcao = np.where(sorteio_para_cima, np.inf, -np.inf)
        valores_perturbados = np.nextafter(valores_originais, direcao)

        if not perturbar_zeros:
            celula_e_zero = valores_originais == 0.0
            valores_perturbados = np.where(celula_e_zero, valores_originais, valores_perturbados)

        matriz_perturbada[nome_da_coluna] = valores_perturbados

    return matriz_perturbada


def alinhar_matriz_do_gabarito(
    matriz_do_pacote: pd.DataFrame,
    matriz_do_gabarito: pd.DataFrame,
) -> pd.DataFrame:
    """Devolve a matriz do pacote com as variaveis trocadas pelas do gabarito (lido do CSV).

    Confere o alinhamento antes: as mesmas linhas (`data_origem` e `data_alvo`
    iguais, na mesma ordem), as mesmas colunas (como conjunto), e `y_h` igual.
    Datas e `y_h` ficam os do pacote; so as variaveis vem do gabarito, na ordem
    de colunas do pacote.

    Args:
        matriz_do_pacote: Matriz montada pelo pacote. Nao e modificada.
        matriz_do_gabarito: Matriz lida de `matriz_hXX.csv` (com as datas ja
            convertidas), com as mesmas 25 colunas.

    Returns:
        Copia da matriz do pacote com os valores das variaveis do gabarito.

    Raises:
        ValueError: Se as linhas, as colunas ou o alvo nao baterem.
    """
    colunas_do_pacote = list(matriz_do_pacote.columns)
    if set(colunas_do_pacote) != set(matriz_do_gabarito.columns):
        faltam = sorted(set(colunas_do_pacote) - set(matriz_do_gabarito.columns))
        sobram = sorted(set(matriz_do_gabarito.columns) - set(colunas_do_pacote))
        raise ValueError(f"Colunas diferentes entre pacote e gabarito: faltam {faltam}, sobram {sobram}.")
    if len(matriz_do_pacote) != len(matriz_do_gabarito):
        raise ValueError(
            f"Numero de linhas diferente: pacote {len(matriz_do_pacote)}, gabarito {len(matriz_do_gabarito)}."
        )

    for coluna_de_data in (COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO):
        datas_do_pacote = matriz_do_pacote[coluna_de_data].to_numpy()
        datas_do_gabarito = matriz_do_gabarito[coluna_de_data].to_numpy()
        if not np.array_equal(datas_do_pacote, datas_do_gabarito):
            raise ValueError(f"A coluna {coluna_de_data!r} nao bate linha a linha entre pacote e gabarito.")

    alvo_do_pacote = matriz_do_pacote[COLUNA_DO_ALVO].to_numpy(dtype=float)
    alvo_do_gabarito = matriz_do_gabarito[COLUNA_DO_ALVO].to_numpy(dtype=float)
    if not np.array_equal(alvo_do_pacote, alvo_do_gabarito):
        raise ValueError("`y_h` nao bate entre pacote e gabarito.")

    matriz_alinhada = matriz_do_pacote.copy()
    for nome_da_coluna in colunas_do_pacote:
        if nome_da_coluna in COLUNAS_FORA_DAS_VARIAVEIS:
            continue
        matriz_alinhada[nome_da_coluna] = matriz_do_gabarito[nome_da_coluna].to_numpy(dtype=float)
    return matriz_alinhada
