"""Testes estatisticos das comparacoes pareadas: Diebold-Mariano (HLN), Holm e bootstrap de blocos moveis.

Funcoes puras: recebem arrays ou DataFrames pequenos e devolvem numeros. Nenhuma le ou
grava arquivo. Definicoes fixadas em `resultados/ciencia/estatistica/METODO_ESTATISTICO.md`
(pre-declaracao de 12/10/2026, secao 2):

    - perda = erro absoluto; `d_t = |e_B,t| - |e_A,t|` (positivo = A erra menos);
    - Diebold-Mariano com a correcao de Harvey, Leybourne e Newbold (HLN),
      defasagens 0 a h-1, bilateral, t de Student com n-1 graus de liberdade;
    - bootstrap de blocos moveis de 8 semanas, 2.000 reamostragens, semente 42;
    - Holm dentro de cada familia.
"""

import dataclasses

import numpy as np
import pandas as pd
from scipy import stats

from aedes.configuracao import COLUNA_DATA_ALVO
from aedes.metricas import COLUNA_DO_PREVISTO, COLUNA_DO_REAL

TAMANHO_DO_BLOCO_DO_BOOTSTRAP = 8
REAMOSTRAGENS_DO_BOOTSTRAP = 2000
SEMENTE_DO_BOOTSTRAP = 42
PERCENTIL_INFERIOR_DO_IC = 2.5
PERCENTIL_SUPERIOR_DO_IC = 97.5
TOLERANCIA_DO_REAL_ENTRE_LADOS = 1e-9


@dataclasses.dataclass(frozen=True)
class ResultadoDieboldMariano:
    """Resultado do teste de Diebold-Mariano com a correcao HLN.

    Attributes:
        n: Numero de pares usados.
        horizonte: Horizonte h (define quantas defasagens entram na variancia).
        media_das_diferencas: `dbar`, media de `d_t`.
        variancia: Variancia de `dbar` (`V`) efetivamente usada (com pesos de Bartlett se houve fallback).
        dm: Estatistica DM sem correcao (NaN se indefinida).
        dm_hln: Estatistica corrigida por HLN (NaN se indefinida).
        p_bilateral: p-valor bilateral (1,0 se a estatistica e indefinida).
        variancia_fallback: Verdadeiro se `V <= 0` e foram usados os pesos de Bartlett.
        definido: Falso se a variancia ficou nao positiva mesmo com Bartlett.
    """

    n: int
    horizonte: int
    media_das_diferencas: float
    variancia: float
    dm: float
    dm_hln: float
    p_bilateral: float
    variancia_fallback: bool
    definido: bool


def calcular_autocovariancias(diferencas_de_perda: np.ndarray, quantidade_de_defasagens: int) -> np.ndarray:
    """Autocovariancias amostrais `gamma_k = (1/n) * soma_{t>=k} (d_t - dbar)(d_{t-k} - dbar)`, k = 0..K-1.

    Divide sempre por `n` (nao por `n-k`), como na definicao do teste.

    Args:
        diferencas_de_perda: Serie `d_t` em ordem cronologica.
        quantidade_de_defasagens: K, quantas defasagens (de 0 a K-1) devolver.

    Returns:
        Vetor com `gamma_0 ... gamma_{K-1}`.

    Raises:
        ValueError: Se K for menor que 1 ou maior que o numero de pares.
    """
    diferencas = np.asarray(diferencas_de_perda, dtype=float)
    quantidade_de_pares = len(diferencas)
    if quantidade_de_defasagens < 1 or quantidade_de_defasagens > quantidade_de_pares:
        raise ValueError(
            f"quantidade_de_defasagens deve estar entre 1 e n={quantidade_de_pares}, recebido {quantidade_de_defasagens}."
        )
    media = diferencas.mean()
    centradas = diferencas - media

    autocovariancias = np.zeros(quantidade_de_defasagens)
    for defasagem in range(quantidade_de_defasagens):
        produtos = centradas[defasagem:] * centradas[: quantidade_de_pares - defasagem]
        autocovariancias[defasagem] = produtos.sum() / quantidade_de_pares
    return autocovariancias


def _variancia_da_media(
    autocovariancias: np.ndarray,
    quantidade_de_pares: int,
    usar_pesos_de_bartlett: bool,
) -> float:
    """`V = (gamma_0 + 2 * soma_{k>=1} w_k * gamma_k) / n`, com `w_k = 1` ou `w_k = 1 - k/h` (Bartlett)."""
    horizonte = len(autocovariancias)
    soma_ponderada = 0.0
    for defasagem in range(1, horizonte):
        if usar_pesos_de_bartlett:
            peso = 1.0 - defasagem / horizonte
        else:
            peso = 1.0
        soma_ponderada += peso * autocovariancias[defasagem]
    variancia_bruta = autocovariancias[0] + 2.0 * soma_ponderada
    return float(variancia_bruta / quantidade_de_pares)


def diebold_mariano_hln(diferencas_de_perda: np.ndarray, horizonte: int) -> ResultadoDieboldMariano:
    """Diebold-Mariano com a correcao de Harvey, Leybourne e Newbold (perda = erro absoluto, bilateral).

    `diferencas_de_perda` e `d_t = |e_B,t| - |e_A,t|` na serie pareada ordenada por `data_alvo`
    (buracos de calendario simplesmente omitidos). `dbar` positivo quer dizer que A erra menos.

    Regras:
        - `V = (gamma_0 + 2 * soma_{k=1}^{h-1} gamma_k) / n`;
        - se `V <= 0`, refaz com pesos de Bartlett `(1 - k/h)` nos mesmos lags e marca `variancia_fallback`;
        - se `V` continua `<= 0` (por exemplo, `d_t` constante), o teste e indefinido: `dm`, `dm_hln` NaN,
          `p_bilateral = 1,0`;
        - `DM_HLN = DM * sqrt((n + 1 - 2h + h(h-1)/n) / n)`; p pela t de Student com n-1 graus de liberdade.

    Args:
        diferencas_de_perda: Serie `d_t` (sem ausente nem infinito).
        horizonte: Horizonte h >= 1.

    Returns:
        O `ResultadoDieboldMariano`.

    Raises:
        ValueError: Se h < 1, houver ausente ou infinito, n < 2, h > n ou o fator HLN nao for positivo.
    """
    diferencas = np.asarray(diferencas_de_perda, dtype=float)
    if diferencas.ndim != 1:
        raise ValueError("diferencas_de_perda deve ser 1-D.")
    if not np.isfinite(diferencas).all():
        raise ValueError("diferencas_de_perda tem valor ausente ou infinito.")
    if horizonte < 1:
        raise ValueError(f"horizonte deve ser >= 1, recebido {horizonte!r}.")
    quantidade_de_pares = len(diferencas)
    if quantidade_de_pares < 2 or horizonte > quantidade_de_pares:
        raise ValueError(f"n={quantidade_de_pares} insuficiente para h={horizonte}.")

    media = float(diferencas.mean())
    autocovariancias = calcular_autocovariancias(diferencas, horizonte)

    variancia = _variancia_da_media(autocovariancias, quantidade_de_pares, usar_pesos_de_bartlett=False)
    usou_fallback = False
    if variancia <= 0.0:
        variancia = _variancia_da_media(autocovariancias, quantidade_de_pares, usar_pesos_de_bartlett=True)
        usou_fallback = True

    if variancia <= 0.0:
        return ResultadoDieboldMariano(
            n=quantidade_de_pares,
            horizonte=horizonte,
            media_das_diferencas=media,
            variancia=variancia,
            dm=float("nan"),
            dm_hln=float("nan"),
            p_bilateral=1.0,
            variancia_fallback=True,
            definido=False,
        )

    estatistica_dm = media / np.sqrt(variancia)
    argumento_do_fator = (
        quantidade_de_pares + 1 - 2 * horizonte + horizonte * (horizonte - 1) / quantidade_de_pares
    ) / quantidade_de_pares
    if argumento_do_fator <= 0.0:
        raise ValueError(f"Fator HLN nao positivo para n={quantidade_de_pares}, h={horizonte}.")
    estatistica_hln = float(estatistica_dm * np.sqrt(argumento_do_fator))

    graus_de_liberdade = quantidade_de_pares - 1
    p_bilateral = float(2.0 * stats.t.sf(abs(estatistica_hln), df=graus_de_liberdade))
    return ResultadoDieboldMariano(
        n=quantidade_de_pares,
        horizonte=horizonte,
        media_das_diferencas=media,
        variancia=float(variancia),
        dm=float(estatistica_dm),
        dm_hln=estatistica_hln,
        p_bilateral=p_bilateral,
        variancia_fallback=usou_fallback,
        definido=True,
    )


def corrigir_por_holm(p_valores_brutos: np.ndarray) -> np.ndarray:
    """Ajuste de Holm-Bonferroni (step-down) dentro de uma familia.

    Ordena os `m` p-valores do menor para o maior; o i-esimo (i = 1..m) vira `(m - i + 1) * p_(i)`;
    depois garante monotonia (maximo acumulado) e trunca em 1. Devolve na ordem ORIGINAL.

    Args:
        p_valores_brutos: p-valores da familia, em [0, 1].

    Returns:
        p-valores ajustados, mesma ordem da entrada.

    Raises:
        ValueError: Se houver valor fora de [0, 1] ou nao finito.
    """
    p_brutos = np.asarray(p_valores_brutos, dtype=float)
    if p_brutos.ndim != 1:
        raise ValueError("p_valores_brutos deve ser 1-D.")
    if len(p_brutos) == 0:
        return p_brutos.copy()
    if not np.isfinite(p_brutos).all() or (p_brutos < 0.0).any() or (p_brutos > 1.0).any():
        raise ValueError("p_valores_brutos deve ter valores finitos em [0, 1].")

    quantidade_de_testes = len(p_brutos)
    ordem_crescente = np.argsort(p_brutos, kind="stable")
    ajustados_na_ordem_crescente = np.zeros(quantidade_de_testes)
    maximo_acumulado = 0.0
    for posicao in range(quantidade_de_testes):
        multiplicador = quantidade_de_testes - posicao
        p_do_teste = p_brutos[ordem_crescente[posicao]]
        valor_ajustado = min(1.0, multiplicador * p_do_teste)
        maximo_acumulado = max(maximo_acumulado, valor_ajustado)
        ajustados_na_ordem_crescente[posicao] = maximo_acumulado

    p_ajustados = np.zeros(quantidade_de_testes)
    p_ajustados[ordem_crescente] = ajustados_na_ordem_crescente
    return p_ajustados


def ganho_percentual(mae_do_comparador: float, mae_do_candidato: float) -> float:
    """`(MAE_B - MAE_A) / MAE_B * 100`: positivo quando o candidato A erra menos.

    Raises:
        ValueError: Se o MAE do comparador for zero.
    """
    if mae_do_comparador == 0.0:
        raise ValueError("MAE do comparador zero: ganho percentual indefinido.")
    return 100.0 * (mae_do_comparador - mae_do_candidato) / mae_do_comparador


def sortear_indices_de_blocos_moveis(
    quantidade_de_pares: int,
    tamanho_do_bloco: int,
    reamostragens: int,
    gerador: np.random.Generator,
) -> np.ndarray:
    """Indices de `reamostragens` series reamostradas por blocos moveis, cada uma com `n` posicoes.

    Cada reamostra concatena `ceil(n / tamanho_do_bloco)` blocos de posicoes CONSECUTIVAS; o inicio de
    cada bloco e sorteado uniforme em `0..n-tamanho_do_bloco`; a concatenacao e truncada em `n`.
    Uma unica chamada `gerador.integers(..., size=(reamostragens, blocos))` define os inicios (linha
    i = reamostra i), o que fixa a sequencia para uma dada semente.

    Args:
        quantidade_de_pares: n, tamanho da serie pareada.
        tamanho_do_bloco: Comprimento de cada bloco (8).
        reamostragens: Numero de reamostras B (2.000).
        gerador: Gerador do NumPy (novo por comparacao, semente 42).

    Returns:
        Matriz `(B, n)` de indices inteiros em `0..n-1`.

    Raises:
        ValueError: Se n < tamanho_do_bloco ou algum argumento nao for positivo.
    """
    if tamanho_do_bloco < 1 or reamostragens < 1:
        raise ValueError("tamanho_do_bloco e reamostragens devem ser >= 1.")
    if quantidade_de_pares < tamanho_do_bloco:
        raise ValueError(f"n={quantidade_de_pares} menor que o bloco ({tamanho_do_bloco}).")

    quantidade_de_blocos = int(np.ceil(quantidade_de_pares / tamanho_do_bloco))
    limite_superior_exclusivo = quantidade_de_pares - tamanho_do_bloco + 1
    inicios_dos_blocos = gerador.integers(0, limite_superior_exclusivo, size=(reamostragens, quantidade_de_blocos))

    deslocamentos_dentro_do_bloco = np.arange(tamanho_do_bloco)
    indices_por_bloco = inicios_dos_blocos[:, :, np.newaxis] + deslocamentos_dentro_do_bloco[np.newaxis, np.newaxis, :]
    indices_concatenados = indices_por_bloco.reshape(reamostragens, quantidade_de_blocos * tamanho_do_bloco)
    return indices_concatenados[:, :quantidade_de_pares]


def intervalo_de_confianca_do_ganho(
    erros_absolutos_do_candidato: np.ndarray,
    erros_absolutos_do_comparador: np.ndarray,
    tamanho_do_bloco: int = TAMANHO_DO_BLOCO_DO_BOOTSTRAP,
    reamostragens: int = REAMOSTRAGENS_DO_BOOTSTRAP,
    semente: int = SEMENTE_DO_BOOTSTRAP,
) -> tuple[float, float]:
    """IC 95% do `ganho_pct` por bootstrap de blocos moveis, pareado (mesmos indices nos dois lados).

    A cada reamostra recalcula `ganho_pct = (MAE_B - MAE_A) / MAE_B * 100` e o IC e o par de percentis
    2,5 e 97,5. O gerador e NOVO a cada chamada (`np.random.default_rng(semente)`).

    Args:
        erros_absolutos_do_candidato: `|e_A,t|` na serie pareada ordenada.
        erros_absolutos_do_comparador: `|e_B,t|`, mesma ordem e tamanho.
        tamanho_do_bloco: 8.
        reamostragens: 2.000.
        semente: 42.

    Returns:
        `(ic_inferior, ic_superior)`.

    Raises:
        ValueError: Se os tamanhos diferirem ou n for menor que o bloco.
    """
    erros_a = np.asarray(erros_absolutos_do_candidato, dtype=float)
    erros_b = np.asarray(erros_absolutos_do_comparador, dtype=float)
    if erros_a.shape != erros_b.shape or erros_a.ndim != 1:
        raise ValueError("Os erros dos dois lados devem ser 1-D e do mesmo tamanho.")

    gerador = np.random.default_rng(semente)
    indices = sortear_indices_de_blocos_moveis(len(erros_a), tamanho_do_bloco, reamostragens, gerador)
    mae_a_reamostrado = erros_a[indices].mean(axis=1)
    mae_b_reamostrado = erros_b[indices].mean(axis=1)
    ganhos_reamostrados = 100.0 * (mae_b_reamostrado - mae_a_reamostrado) / mae_b_reamostrado
    limite_inferior = float(np.percentile(ganhos_reamostrados, PERCENTIL_INFERIOR_DO_IC))
    limite_superior = float(np.percentile(ganhos_reamostrados, PERCENTIL_SUPERIOR_DO_IC))
    return limite_inferior, limite_superior


@dataclasses.dataclass(frozen=True)
class ComparacaoPareada:
    """Uma comparacao A x B em um horizonte, pareada por `data_alvo`.

    Attributes:
        n: Semanas em comum.
        mae_a: MAE do candidato A.
        mae_b: MAE do comparador B.
        delta: `MAE_B - MAE_A` (positivo = A erra menos).
        ganho_pct: `delta / MAE_B * 100`.
        ic_inf: Limite inferior do IC 95% do `ganho_pct`.
        ic_sup: Limite superior.
        dm_hln: Estatistica DM corrigida (NaN se indefinida).
        p_bruto: p-valor bilateral.
        variancia_fallback: Se usou pesos de Bartlett (ou DM indefinido).
    """

    n: int
    mae_a: float
    mae_b: float
    delta: float
    ganho_pct: float
    ic_inf: float
    ic_sup: float
    dm_hln: float
    p_bruto: float
    variancia_fallback: bool


def parear_por_data_alvo(previsoes_a: pd.DataFrame, previsoes_b: pd.DataFrame) -> pd.DataFrame:
    """Cruza A e B pelas `data_alvo` em comum (um horizonte so) e ordena por `data_alvo`.

    Args:
        previsoes_a: `data_alvo`, `real`, `previsto` de um lado.
        previsoes_b: Idem do outro.

    Returns:
        DataFrame ordenado com `data_alvo`, `real`, `previsto_a`, `previsto_b`.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se houver `data_alvo` repetida num lado, nenhuma semana em comum, ou o `real` diferir entre lados.
    """
    colunas = [COLUNA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
    for nome_do_lado, tabela in (("A", previsoes_a), ("B", previsoes_b)):
        ausentes = sorted(set(colunas) - set(tabela.columns))
        if ausentes:
            raise KeyError(f"Colunas ausentes no lado {nome_do_lado}: {ausentes}")
        if tabela[COLUNA_DATA_ALVO].duplicated().any():
            raise ValueError(f"data_alvo repetida no lado {nome_do_lado}.")

    do_lado_a = previsoes_a[colunas].rename(columns={COLUNA_DO_REAL: "real_a", COLUNA_DO_PREVISTO: "previsto_a"})
    do_lado_b = previsoes_b[colunas].rename(columns={COLUNA_DO_REAL: "real_b", COLUNA_DO_PREVISTO: "previsto_b"})
    em_comum = do_lado_a.merge(do_lado_b, on=COLUNA_DATA_ALVO, how="inner")
    if len(em_comum) == 0:
        raise ValueError("Nenhuma data_alvo em comum entre A e B.")

    diferenca_do_real = (em_comum["real_a"] - em_comum["real_b"]).abs()
    if bool((diferenca_do_real > TOLERANCIA_DO_REAL_ENTRE_LADOS).any()):
        raise ValueError("A coluna `real` difere entre A e B nas semanas em comum.")

    pareado = em_comum.rename(columns={"real_a": COLUNA_DO_REAL})
    pareado = pareado.drop(columns=["real_b"])
    pareado = pareado.sort_values(COLUNA_DATA_ALVO).reset_index(drop=True)
    return pareado[[COLUNA_DATA_ALVO, COLUNA_DO_REAL, "previsto_a", "previsto_b"]]


def comparar_pareado(
    previsoes_a: pd.DataFrame,
    previsoes_b: pd.DataFrame,
    horizonte: int,
) -> ComparacaoPareada:
    """MAE, delta, ganho, IC por bootstrap e Diebold-Mariano HLN de A contra B, pareados por `data_alvo`.

    Args:
        previsoes_a: Candidato A (um horizonte), com `data_alvo`, `real`, `previsto`.
        previsoes_b: Comparador B (mesmo horizonte).
        horizonte: Horizonte h (defasagens do DM).

    Returns:
        A `ComparacaoPareada`.

    Raises:
        ValueError: Ver `parear_por_data_alvo`, `diebold_mariano_hln` e `ganho_percentual`.
    """
    pareado = parear_por_data_alvo(previsoes_a, previsoes_b)
    valores_reais = pareado[COLUNA_DO_REAL].to_numpy(dtype=float)
    previsto_a = pareado["previsto_a"].to_numpy(dtype=float)
    previsto_b = pareado["previsto_b"].to_numpy(dtype=float)

    erros_absolutos_a = np.abs(valores_reais - previsto_a)
    erros_absolutos_b = np.abs(valores_reais - previsto_b)
    mae_a = float(erros_absolutos_a.mean())
    mae_b = float(erros_absolutos_b.mean())
    delta = mae_b - mae_a
    ganho = ganho_percentual(mae_b, mae_a)

    ic_inferior, ic_superior = intervalo_de_confianca_do_ganho(erros_absolutos_a, erros_absolutos_b)

    diferencas_de_perda = erros_absolutos_b - erros_absolutos_a
    teste = diebold_mariano_hln(diferencas_de_perda, horizonte)
    return ComparacaoPareada(
        n=len(pareado),
        mae_a=mae_a,
        mae_b=mae_b,
        delta=delta,
        ganho_pct=ganho,
        ic_inf=ic_inferior,
        ic_sup=ic_superior,
        dm_hln=teste.dm_hln,
        p_bruto=teste.p_bilateral,
        variancia_fallback=teste.variancia_fallback,
    )
