"""E7: WIS (Weighted Interval Score), cobertura, regua climatologica e comparacao pareada.

Funcoes puras: nao leem nem gravam arquivo. Replica, sem nenhuma correcao, o
calculo do codigo antigo (`analises/2026-09-26_wis_na_tabela_restaurada/rodar.py`):
    - `calcular_intervalo_score`, `calcular_wis`, `calcular_cobertura`;
    - `montar_historico_por_semana_epidemiologica`, `calcular_previsao_da_regua`
      e `montar_previsoes_da_regua` (a regua climatologica);
e acrescenta o que a pre-declaracao de 12/10/2026 pede de novo: cobertura do
intervalo de 80%, teste Diebold-Mariano com correcao HLN, bootstrap de blocos
e Holm em uma familia de 12 testes (F5).

FORMULAS (Bracher et al., 2021). Com `K = 3` intervalos centrais (50%, 80% e
90%), `m` a mediana prevista e `y` o valor observado:

    IS_a   = (u - l) + (2/a)(l - y) I[y < l] + (2/a)(y - u) I[y > u]
    WIS    = ( 0,5 |y - m| + soma_k (a_k / 2) IS_{a_k} ) / (K + 0,5)

onde `[l, u]` sao os quantis `a/2` e `1 - a/2` e `a = 1 - cobertura nominal`.

REGUA CLIMATOLOGICA. Para a semana-alvo de `data_alvo`, os 7 quantis
(`np.quantile`, interpolacao linear) dos casos DA MESMA SEMANA EPIDEMIOLOGICA
nos anos de 2018 em diante e ANTERIORES ao ano da semana-alvo, com pelo menos 3
anos. Usa a tabela SEM o corte de maturidade (como o antigo): os anos que
entram sao sempre anteriores ao ano-alvo, entao o corte (que so apaga as 12
ultimas semanas, de 2026) nunca muda o resultado da janela de avaliacao. NAO e
a regua sazonal do MAE (casos de 52 semanas antes); sao reguas diferentes.
"""

import dataclasses

import numpy as np
import pandas as pd

from aedes.configuracao import COLUNA_DATA_ALVO, ConfiguracaoDados
from aedes.estatistica import (
    corrigir_por_holm,
    diebold_mariano_hln,
    ganho_percentual,
    intervalo_de_confianca_do_ganho,
)
from aedes.familias import decidir_veredito
from aedes.metricas import COLUNA_DO_REAL
from aedes.quantis import QUANTIS_DO_WIS
from aedes.walk_forward import COLUNA_DO_HORIZONTE

ANO_MINIMO_DA_REGUA = 2018
MINIMO_DE_ANOS_DA_REGUA = 3

NOME_DO_MODELO_FOLHA_5 = "folha5"
NOME_DO_MODELO_FOLHA_20 = "folha20"
NOME_DO_MODELO_COMPOSTO = "composto_N13"
NOME_DA_REGUA_CLIMATOLOGICA = "regua_climatologica"
FOLHA_DO_COMPOSTO_NO_EMPATE = 5
FOLHA_ALTERNATIVA_DO_COMPOSTO = 20

COLUNA_DO_MODELO = "modelo"
COLUNA_DO_WIS = "wis"
COLUNA_DA_JANELA = "janela"
COLUNAS_DOS_ESCORES = (
    COLUNA_DO_MODELO,
    COLUNA_DO_HORIZONTE,
    COLUNA_DATA_ALVO,
    COLUNA_DO_REAL,
    COLUNA_DO_WIS,
    "cobertura_50",
    "cobertura_80",
    "cobertura_90",
)
COLUNAS_DO_RESUMO_DO_WIS = (
    COLUNA_DO_MODELO,
    COLUNA_DO_HORIZONTE,
    COLUNA_DA_JANELA,
    "n",
    "wis_medio",
    "cobertura_50",
    "cobertura_80",
    "cobertura_90",
)

FAMILIA_F5 = "F5"
TOLERANCIA_DO_REAL_ENTRE_MODELOS = 1e-9


@dataclasses.dataclass(frozen=True)
class IntervaloDoWis:
    """Um intervalo central do WIS.

    Attributes:
        cobertura_nominal: 0,50, 0,80 ou 0,90.
        alpha: `1 - cobertura_nominal`.
        quantil_inferior: Nivel do limite inferior (`alpha / 2`).
        quantil_superior: Nivel do limite superior (`1 - alpha / 2`).
    """

    cobertura_nominal: float
    alpha: float
    quantil_inferior: float
    quantil_superior: float


# Os tres intervalos da pre-declaracao, do mais estreito ao mais largo. A ORDEM
# e a do antigo e define a ordem da soma de ponto flutuante do WIS.
INTERVALOS_DO_WIS = (
    IntervaloDoWis(cobertura_nominal=0.50, alpha=0.50, quantil_inferior=0.25, quantil_superior=0.75),
    IntervaloDoWis(cobertura_nominal=0.80, alpha=0.20, quantil_inferior=0.10, quantil_superior=0.90),
    IntervaloDoWis(cobertura_nominal=0.90, alpha=0.10, quantil_inferior=0.05, quantil_superior=0.95),
)
NIVEL_DA_MEDIANA = 0.50


def _posicao_do_nivel(quantis: tuple[float, ...], nivel: float) -> int:
    """Posicao do nivel na tupla de quantis (comparacao exata: os niveis sao os mesmos literais).

    Raises:
        ValueError: Se o nivel nao estiver na tupla.
    """
    for posicao, quantil in enumerate(quantis):
        if quantil == nivel:
            return posicao
    raise ValueError(f"Nivel {nivel} ausente dos quantis {quantis!r}.")


def calcular_escore_de_intervalo(
    reais: np.ndarray,
    limites_inferiores: np.ndarray,
    limites_superiores: np.ndarray,
    alpha: float,
) -> np.ndarray:
    """IS_alpha de cada origem: largura do intervalo mais a penalidade se o real ficar de fora.

    Args:
        reais: Valores observados (1-D).
        limites_inferiores: Quantil inferior do intervalo, por origem.
        limites_superiores: Quantil superior do intervalo, por origem.
        alpha: `1 - cobertura nominal` (0 < alpha < 1).

    Returns:
        Vetor com o escore de cada origem.

    Raises:
        ValueError: Se alpha estiver fora de (0, 1) ou os vetores tiverem tamanhos diferentes.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha deve estar em (0, 1), recebido {alpha!r}.")
    reais_em_float = np.asarray(reais, dtype=float)
    inferiores = np.asarray(limites_inferiores, dtype=float)
    superiores = np.asarray(limites_superiores, dtype=float)
    if not (reais_em_float.shape == inferiores.shape == superiores.shape):
        raise ValueError("reais e limites devem ter o mesmo formato.")

    largura_do_intervalo = superiores - inferiores
    esta_abaixo = reais_em_float < inferiores
    esta_acima = reais_em_float > superiores
    penalidade_por_baixo = np.where(esta_abaixo, (2.0 / alpha) * (inferiores - reais_em_float), 0.0)
    penalidade_por_cima = np.where(esta_acima, (2.0 / alpha) * (reais_em_float - superiores), 0.0)
    return largura_do_intervalo + penalidade_por_baixo + penalidade_por_cima


def calcular_wis(
    reais: np.ndarray,
    quantis_previstos: np.ndarray,
    quantis: tuple[float, ...] = QUANTIS_DO_WIS,
) -> np.ndarray:
    """WIS de cada origem, com a mediana e os tres intervalos (50, 80 e 90%).

    Args:
        reais: Valores observados, vetor de tamanho n.
        quantis_previstos: Matriz n x len(quantis); a coluna j e o quantil `quantis[j]`
            (ja ordenados: sem cruzamento).
        quantis: Niveis das colunas; tem de conter a mediana e os 6 limites dos intervalos.

    Returns:
        Vetor de tamanho n com o WIS (menor e melhor).

    Raises:
        ValueError: Se a matriz nao tiver uma coluna por nivel ou faltar algum nivel.
    """
    reais_em_float = np.asarray(reais, dtype=float)
    matriz = np.asarray(quantis_previstos, dtype=float)
    if matriz.ndim != 2 or matriz.shape[1] != len(quantis) or matriz.shape[0] != len(reais_em_float):
        raise ValueError(
            f"quantis_previstos deve ser {len(reais_em_float)} x {len(quantis)}, recebido {matriz.shape}."
        )

    mediana_prevista = matriz[:, _posicao_do_nivel(quantis, NIVEL_DA_MEDIANA)]
    termo_da_mediana = 0.5 * np.abs(reais_em_float - mediana_prevista)

    soma_dos_intervalos = np.zeros(len(reais_em_float))
    for intervalo in INTERVALOS_DO_WIS:
        limite_inferior = matriz[:, _posicao_do_nivel(quantis, intervalo.quantil_inferior)]
        limite_superior = matriz[:, _posicao_do_nivel(quantis, intervalo.quantil_superior)]
        escore = calcular_escore_de_intervalo(reais_em_float, limite_inferior, limite_superior, intervalo.alpha)
        soma_dos_intervalos = soma_dos_intervalos + (intervalo.alpha / 2.0) * escore

    quantidade_de_intervalos = len(INTERVALOS_DO_WIS)
    return (termo_da_mediana + soma_dos_intervalos) / (quantidade_de_intervalos + 0.5)


def calcular_cobertura(
    reais: np.ndarray,
    quantis_previstos: np.ndarray,
    intervalo: IntervaloDoWis,
    quantis: tuple[float, ...] = QUANTIS_DO_WIS,
) -> np.ndarray:
    """Para cada origem, se o real caiu dentro do intervalo, com os limites INCLUIDOS (`l <= y <= u`).

    Raises:
        ValueError: Se a matriz nao tiver uma coluna por nivel ou faltar o nivel do intervalo.
    """
    reais_em_float = np.asarray(reais, dtype=float)
    matriz = np.asarray(quantis_previstos, dtype=float)
    if matriz.ndim != 2 or matriz.shape[1] != len(quantis) or matriz.shape[0] != len(reais_em_float):
        raise ValueError(f"quantis_previstos deve ser {len(reais_em_float)} x {len(quantis)}, recebido {matriz.shape}.")
    limite_inferior = matriz[:, _posicao_do_nivel(quantis, intervalo.quantil_inferior)]
    limite_superior = matriz[:, _posicao_do_nivel(quantis, intervalo.quantil_superior)]
    return (limite_inferior <= reais_em_float) & (reais_em_float <= limite_superior)


def calcular_escores_por_origem(
    nome_do_modelo: str,
    horizonte: int,
    datas_alvo: pd.Series,
    reais: pd.Series,
    quantis_previstos: np.ndarray,
) -> pd.DataFrame:
    """WIS e cobertura (50, 80 e 90%) de cada origem de um modelo em um horizonte.

    Args:
        nome_do_modelo: `folha5`, `folha20`, `composto_N13` ou `regua_climatologica`.
        horizonte: h.
        datas_alvo: Semana-alvo de cada origem.
        reais: Casos observados na semana-alvo, pareados por posicao.
        quantis_previstos: Matriz n x 7 ja ordenada.

    Returns:
        DataFrame com `COLUNAS_DOS_ESCORES`, uma linha por origem, na ordem recebida.

    Raises:
        ValueError: Se os tamanhos forem incompativeis.
    """
    quantidade_de_origens = len(datas_alvo)
    if len(reais) != quantidade_de_origens:
        raise ValueError("datas_alvo e reais devem ter o mesmo tamanho.")

    valores_reais = np.asarray(reais, dtype=float)
    wis_das_origens = calcular_wis(valores_reais, quantis_previstos)
    cobertura_por_nome: dict[str, np.ndarray] = {}
    for intervalo in INTERVALOS_DO_WIS:
        nome_da_coluna = f"cobertura_{round(intervalo.cobertura_nominal * 100)}"
        cobertura_por_nome[nome_da_coluna] = calcular_cobertura(valores_reais, quantis_previstos, intervalo)

    escores = pd.DataFrame(
        {
            COLUNA_DO_MODELO: nome_do_modelo,
            COLUNA_DO_HORIZONTE: horizonte,
            COLUNA_DATA_ALVO: np.asarray(datas_alvo),
            COLUNA_DO_REAL: valores_reais,
            COLUNA_DO_WIS: wis_das_origens,
            "cobertura_50": cobertura_por_nome["cobertura_50"],
            "cobertura_80": cobertura_por_nome["cobertura_80"],
            "cobertura_90": cobertura_por_nome["cobertura_90"],
        }
    )
    return escores[list(COLUNAS_DOS_ESCORES)]


def montar_historico_da_regua(tabela_crua: pd.DataFrame, configuracao_dados: ConfiguracaoDados) -> pd.DataFrame:
    """Recorta da tabela SEM corte de maturidade so o que a regua usa: data, ano, semana e casos.

    Args:
        tabela_crua: Tabela validada, antes do corte de maturidade.
        configuracao_dados: Nomes da coluna de data e da de casos.

    Returns:
        DataFrame novo com `data`, `ano`, `semana`, `casos`, uma linha por semana.

    Raises:
        KeyError: Se faltar coluna.
    """
    colunas = [configuracao_dados.coluna_de_data, "ano", "semana", configuracao_dados.coluna_de_casos]
    colunas_ausentes = [nome for nome in colunas if nome not in tabela_crua.columns]
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes para a regua: {colunas_ausentes}")
    historico = tabela_crua[colunas].copy()
    historico.columns = ["data", "ano", "semana", "casos"]
    return historico


def calcular_quantis_da_regua(
    historico: pd.DataFrame,
    data_alvo: pd.Timestamp,
    quantis: tuple[float, ...] = QUANTIS_DO_WIS,
    ano_minimo: int = ANO_MINIMO_DA_REGUA,
    minimo_de_anos: int = MINIMO_DE_ANOS_DA_REGUA,
) -> np.ndarray | None:
    """Os quantis da regua climatologica para a semana de `data_alvo`.

    Usa os casos da MESMA semana epidemiologica (coluna `semana`) em linhas com
    `ano >= ano_minimo` e `ano < ano da data_alvo`, descartando semanas sem caso.
    Exige `minimo_de_anos` anos distintos com dado.

    Args:
        historico: Saida de `montar_historico_da_regua`.
        data_alvo: Semana-alvo (um domingo da grade).
        quantis: Niveis a devolver.
        ano_minimo: Primeiro ano que conta (2018).
        minimo_de_anos: Anos distintos exigidos (3).

    Returns:
        Vetor com um valor por nivel, ou `None` se a `data_alvo` nao estiver na
        tabela ou houver menos que `minimo_de_anos` anos com dado.
    """
    linha_da_data_alvo = historico.loc[historico["data"] == data_alvo]
    if linha_da_data_alvo.empty:
        return None

    semana_epidemiologica = int(linha_da_data_alvo["semana"].to_numpy()[0])
    ano_da_data_alvo = int(linha_da_data_alvo["ano"].to_numpy()[0])

    e_da_mesma_semana = historico["semana"] == semana_epidemiologica
    e_de_ano_valido = historico["ano"] >= ano_minimo
    e_de_ano_anterior = historico["ano"] < ano_da_data_alvo
    candidatos = historico.loc[e_da_mesma_semana & e_de_ano_valido & e_de_ano_anterior]
    casos_dos_anos_anteriores = candidatos["casos"].dropna()

    if len(casos_dos_anos_anteriores) == 0:
        return None
    anos_com_dado = candidatos.loc[casos_dos_anos_anteriores.index, "ano"].nunique()
    if anos_com_dado < minimo_de_anos:
        return None

    return np.quantile(casos_dos_anos_anteriores.to_numpy(), list(quantis))


def montar_regua_climatologica(
    historico: pd.DataFrame,
    datas_alvo: pd.Series,
    quantis: tuple[float, ...] = QUANTIS_DO_WIS,
) -> pd.DataFrame:
    """Regua climatologica para cada semana-alvo distinta; as sem historico suficiente ficam de fora.

    Args:
        historico: Saida de `montar_historico_da_regua`.
        datas_alvo: Semanas-alvo a cobrir (repeticoes sao ignoradas).
        quantis: Niveis.

    Returns:
        DataFrame indexado por `data_alvo` (crescente), uma coluna por nivel de quantil.
    """
    datas_distintas = sorted(pd.unique(datas_alvo))
    datas_cobertas: list[pd.Timestamp] = []
    linhas: list[np.ndarray] = []
    for data_alvo in datas_distintas:
        quantis_da_data = calcular_quantis_da_regua(historico, pd.Timestamp(data_alvo), quantis)
        if quantis_da_data is None:
            continue
        datas_cobertas.append(pd.Timestamp(data_alvo))
        linhas.append(quantis_da_data)

    indice = pd.DatetimeIndex(datas_cobertas, name=COLUNA_DATA_ALVO)
    if len(linhas) == 0:
        return pd.DataFrame(index=indice, columns=list(quantis), dtype=float)
    return pd.DataFrame(np.vstack(linhas), index=indice, columns=list(quantis))


def montar_quantis_do_composto(
    quantis_da_folha_5: pd.DataFrame,
    quantis_da_folha_20: pd.DataFrame,
    folha_escolhida: pd.Series,
) -> pd.DataFrame:
    """Em cada semana-alvo, o conjunto de 7 quantis da folha que o composto da E3 escolheu.

    A escolha (5 ou 20) e a da E3 (N = 13, pelo MAE do q0,85); aqui so se
    aplica essa escolha ao conjunto inteiro de quantis ja ordenados.

    Args:
        quantis_da_folha_5: Indexado por `data_alvo`, uma coluna por nivel.
        quantis_da_folha_20: Idem.
        folha_escolhida: Indexada por `data_alvo`, valores 5 ou 20.

    Returns:
        DataFrame indexado pelas `data_alvo` de `folha_escolhida`, mesmas colunas.

    Raises:
        ValueError: Se alguma data da escolha faltar numa das folhas, se as colunas
            diferirem, ou se a escolha tiver valor diferente de 5 e 20.
    """
    if list(quantis_da_folha_5.columns) != list(quantis_da_folha_20.columns):
        raise ValueError("As duas folhas devem ter os mesmos niveis de quantil.")
    valores_validos = {FOLHA_DO_COMPOSTO_NO_EMPATE, FOLHA_ALTERNATIVA_DO_COMPOSTO}
    if not set(folha_escolhida.unique()) <= valores_validos:
        raise ValueError("folha_escolhida so pode ter 5 ou 20.")
    datas = folha_escolhida.index
    datas_ausentes_na_5 = datas.difference(quantis_da_folha_5.index)
    datas_ausentes_na_20 = datas.difference(quantis_da_folha_20.index)
    if len(datas_ausentes_na_5) > 0 or len(datas_ausentes_na_20) > 0:
        raise ValueError("Ha data da escolha do composto sem quantis em uma das folhas.")

    matriz_5 = quantis_da_folha_5.loc[datas].to_numpy(dtype=float)
    matriz_20 = quantis_da_folha_20.loc[datas].to_numpy(dtype=float)
    escolheu_a_folha_20 = (folha_escolhida == FOLHA_ALTERNATIVA_DO_COMPOSTO).to_numpy()
    matriz_do_composto = np.where(escolheu_a_folha_20[:, np.newaxis], matriz_20, matriz_5)
    return pd.DataFrame(matriz_do_composto, index=datas, columns=quantis_da_folha_5.columns)


def recortar_por_data_alvo(
    tabela: pd.DataFrame,
    primeira_data_alvo: pd.Timestamp,
    ultima_data_alvo: pd.Timestamp,
) -> pd.DataFrame:
    """Linhas com `data_alvo` entre as duas datas, limites INCLUIDOS."""
    datas = tabela[COLUNA_DATA_ALVO]
    return tabela.loc[(datas >= primeira_data_alvo) & (datas <= ultima_data_alvo)]


def resumir_escores_por_janela(
    escores: pd.DataFrame,
    janelas: dict[str, tuple[pd.Timestamp, pd.Timestamp]],
) -> pd.DataFrame:
    """WIS medio e cobertura (50, 80 e 90%) por modelo, horizonte e janela de avaliacao.

    Cada modelo e medido em TODAS as suas semanas da janela (a regua pode ter
    menos semanas que os modelos; o `n` de cada linha diz quantas).

    Args:
        escores: Saida empilhada de `calcular_escores_por_origem`.
        janelas: `nome -> (primeira, ultima)` `data_alvo`, inclusivo.

    Returns:
        DataFrame com `COLUNAS_DO_RESUMO_DO_WIS`, na ordem janela, modelo, horizonte.

    Raises:
        KeyError: Se faltar coluna.
    """
    colunas_ausentes = sorted(set(COLUNAS_DOS_ESCORES) - set(escores.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes nos escores: {colunas_ausentes}")

    linhas: list[dict[str, object]] = []
    for nome_da_janela, (primeira_data, ultima_data) in janelas.items():
        na_janela = recortar_por_data_alvo(escores, primeira_data, ultima_data)
        for chave, grupo in na_janela.groupby([COLUNA_DO_MODELO, COLUNA_DO_HORIZONTE], sort=False):
            nome_do_modelo, horizonte = chave
            linhas.append(
                {
                    COLUNA_DO_MODELO: nome_do_modelo,
                    COLUNA_DO_HORIZONTE: int(horizonte),
                    COLUNA_DA_JANELA: nome_da_janela,
                    "n": len(grupo),
                    "wis_medio": float(grupo[COLUNA_DO_WIS].mean()),
                    "cobertura_50": float(grupo["cobertura_50"].mean()),
                    "cobertura_80": float(grupo["cobertura_80"].mean()),
                    "cobertura_90": float(grupo["cobertura_90"].mean()),
                }
            )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_RESUMO_DO_WIS))


@dataclasses.dataclass(frozen=True)
class ComparacaoDeWis:
    """Uma comparacao A x B de WIS em um horizonte, pareada por `data_alvo`.

    Attributes:
        n: Semanas em comum.
        wis_a: WIS medio do candidato A.
        wis_b: WIS medio do comparador B.
        delta: `wis_b - wis_a` (positivo = A erra menos).
        ganho_pct: `delta / wis_b * 100`.
        ic_inf: Limite inferior do IC 95% do `ganho_pct` (bootstrap de blocos de 8 semanas).
        ic_sup: Limite superior.
        dm_hln: Estatistica DM corrigida por HLN (NaN se indefinida).
        p_bruto: p bilateral.
        variancia_fallback: Se o DM usou pesos de Bartlett ou ficou indefinido.
    """

    n: int
    wis_a: float
    wis_b: float
    delta: float
    ganho_pct: float
    ic_inf: float
    ic_sup: float
    dm_hln: float
    p_bruto: float
    variancia_fallback: bool


def parear_escores_por_data_alvo(escores_a: pd.DataFrame, escores_b: pd.DataFrame) -> pd.DataFrame:
    """Cruza os escores de A e B pelas `data_alvo` em comum (um horizonte so) e ordena por data.

    Args:
        escores_a: `data_alvo`, `real`, `wis` de A.
        escores_b: Idem de B.

    Returns:
        DataFrame ordenado com `data_alvo`, `real`, `wis_a`, `wis_b`.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se houver `data_alvo` repetida, nenhuma semana em comum, ou
            o `real` diferir entre os lados.
    """
    colunas = [COLUNA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_WIS]
    for nome_do_lado, tabela in (("A", escores_a), ("B", escores_b)):
        ausentes = sorted(set(colunas) - set(tabela.columns))
        if ausentes:
            raise KeyError(f"Colunas ausentes no lado {nome_do_lado}: {ausentes}")
        if tabela[COLUNA_DATA_ALVO].duplicated().any():
            raise ValueError(f"data_alvo repetida no lado {nome_do_lado}.")

    do_lado_a = escores_a[colunas].rename(columns={COLUNA_DO_REAL: "real_a", COLUNA_DO_WIS: "wis_a"})
    do_lado_b = escores_b[colunas].rename(columns={COLUNA_DO_REAL: "real_b", COLUNA_DO_WIS: "wis_b"})
    em_comum = do_lado_a.merge(do_lado_b, on=COLUNA_DATA_ALVO, how="inner")
    if len(em_comum) == 0:
        raise ValueError("Nenhuma data_alvo em comum entre A e B.")

    diferenca_do_real = (em_comum["real_a"] - em_comum["real_b"]).abs()
    if bool((diferenca_do_real > TOLERANCIA_DO_REAL_ENTRE_MODELOS).any()):
        raise ValueError("A coluna `real` difere entre A e B nas semanas em comum.")

    pareado = em_comum.rename(columns={"real_a": COLUNA_DO_REAL}).drop(columns=["real_b"])
    pareado = pareado.sort_values(COLUNA_DATA_ALVO).reset_index(drop=True)
    return pareado[[COLUNA_DATA_ALVO, COLUNA_DO_REAL, "wis_a", "wis_b"]]


def comparar_wis_pareado(
    escores_a: pd.DataFrame,
    escores_b: pd.DataFrame,
    horizonte: int,
) -> ComparacaoDeWis:
    """WIS medio, ganho, IC por bootstrap de blocos e Diebold-Mariano HLN de A contra B, pareados por `data_alvo`.

    A perda do teste e o WIS semanal: `d_t = WIS_B,t - WIS_A,t`, na serie
    pareada ordenada por `data_alvo`; DM com correcao HLN e defasagens 0 a h-1
    (`aedes.estatistica.diebold_mariano_hln`). O IC 95% e o de
    `intervalo_de_confianca_do_ganho` (blocos de 8 semanas, 2.000 reamostras,
    semente 42) aplicado aos WIS semanais.

    Args:
        escores_a: Candidato A (um horizonte), com `data_alvo`, `real`, `wis`.
        escores_b: Comparador B (mesmo horizonte).
        horizonte: h.

    Returns:
        A `ComparacaoDeWis`.

    Raises:
        ValueError: Ver `parear_escores_por_data_alvo`, `diebold_mariano_hln` e `ganho_percentual`.
    """
    pareado = parear_escores_por_data_alvo(escores_a, escores_b)
    wis_semanal_a = pareado["wis_a"].to_numpy(dtype=float)
    wis_semanal_b = pareado["wis_b"].to_numpy(dtype=float)

    wis_medio_a = float(wis_semanal_a.mean())
    wis_medio_b = float(wis_semanal_b.mean())
    delta = wis_medio_b - wis_medio_a
    ganho = ganho_percentual(wis_medio_b, wis_medio_a)
    ic_inferior, ic_superior = intervalo_de_confianca_do_ganho(wis_semanal_a, wis_semanal_b)

    diferencas_de_perda = wis_semanal_b - wis_semanal_a
    teste = diebold_mariano_hln(diferencas_de_perda, horizonte)
    return ComparacaoDeWis(
        n=len(pareado),
        wis_a=wis_medio_a,
        wis_b=wis_medio_b,
        delta=delta,
        ganho_pct=ganho,
        ic_inf=ic_inferior,
        ic_sup=ic_superior,
        dm_hln=teste.dm_hln,
        p_bruto=teste.p_bilateral,
        variancia_fallback=teste.variancia_fallback,
    )


COLUNAS_DA_TABELA_F5 = (
    "familia",
    "h",
    "A",
    "B",
    "n",
    "wis_A",
    "wis_B",
    "delta",
    "ganho_pct",
    "ic_inf",
    "ic_sup",
    "dm_hln",
    "p_bruto",
    "p_holm",
    "variancia_fallback",
    "veredito",
)


def executar_familia_f5(
    escores_por_modelo_e_horizonte: dict[tuple[str, int], pd.DataFrame],
    nomes_dos_candidatos: tuple[str, ...],
    horizontes: tuple[int, ...],
    nome_da_regua: str = NOME_DA_REGUA_CLIMATOLOGICA,
) -> pd.DataFrame:
    """Familia F5: cada candidato contra a regua climatologica, em cada horizonte, com Holm sobre TODOS os testes.

    Sao `len(nomes_dos_candidatos) * len(horizontes)` testes (12: folha 5,
    folha 20 e composto, em h = 1, 4, 8 e 12) numa familia so. Veredito: `p_holm < 0,05`
    (sem piso de ruido, declarado na pre-declaracao): `delta > 0` = "A melhor"
    (o candidato erra menos que a regua); `delta < 0` = "A pior".

    Args:
        escores_por_modelo_e_horizonte: `(modelo, h) -> DataFrame` com `data_alvo`, `real`, `wis`,
            na janela de avaliacao. Tem de conter a regua em cada horizonte.
        nomes_dos_candidatos: Modelos A.
        horizontes: Horizontes testados.
        nome_da_regua: Nome do comparador B.

    Returns:
        DataFrame com `COLUNAS_DA_TABELA_F5`, na ordem candidato e horizonte.

    Raises:
        KeyError: Se faltarem escores para algum modelo ou horizonte.
    """
    chaves_dos_testes: list[tuple[str, int]] = []
    comparacoes: list[ComparacaoDeWis] = []
    for nome_do_candidato in nomes_dos_candidatos:
        for horizonte in horizontes:
            escores_a = escores_por_modelo_e_horizonte[(nome_do_candidato, horizonte)]
            escores_b = escores_por_modelo_e_horizonte[(nome_da_regua, horizonte)]
            comparacoes.append(comparar_wis_pareado(escores_a, escores_b, horizonte))
            chaves_dos_testes.append((nome_do_candidato, horizonte))

    p_brutos = np.array([comparacao.p_bruto for comparacao in comparacoes], dtype=float)
    p_holm = corrigir_por_holm(p_brutos)

    linhas: list[dict[str, object]] = []
    for posicao, (nome_do_candidato, horizonte) in enumerate(chaves_dos_testes):
        comparacao = comparacoes[posicao]
        veredito = decidir_veredito(float(p_holm[posicao]), comparacao.delta, 0.0)
        linhas.append(
            {
                "familia": FAMILIA_F5,
                "h": horizonte,
                "A": nome_do_candidato,
                "B": nome_da_regua,
                "n": comparacao.n,
                "wis_A": comparacao.wis_a,
                "wis_B": comparacao.wis_b,
                "delta": comparacao.delta,
                "ganho_pct": comparacao.ganho_pct,
                "ic_inf": comparacao.ic_inf,
                "ic_sup": comparacao.ic_sup,
                "dm_hln": comparacao.dm_hln,
                "p_bruto": comparacao.p_bruto,
                "p_holm": float(p_holm[posicao]),
                "variancia_fallback": comparacao.variancia_fallback,
                "veredito": veredito,
            }
        )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DA_TABELA_F5))
