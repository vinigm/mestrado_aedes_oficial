"""Familias de testes F1 a F4 da pre-declaracao (secao 4 e Emenda 1): definicao, piso de ruido, Holm e veredito.

Funcoes puras: recebem as previsoes ja carregadas (um DataFrame por candidato e horizonte) e a tabela
do piso de ruido, e devolvem a tabela `familias`. Nenhuma le ou grava arquivo.

Cada teste compara A (candidato) contra B (comparador), pareado por `data_alvo`, em h em {1, 4, 8, 12}:
    - F1 (folha 5, 12 testes):  completo x sem_X, X em {casos, clima, vetor};
    - F2 (folha 5, 12 testes):  so_X x so_calendario;
    - F3 (folha 20, 12 testes): completo x sem_X;
    - F4 (16 testes):           completo f5, completo f20 e composto N=13, cada um contra a regua sazonal,
                                mais composto N=13 contra completo f5.
"""

import dataclasses

import numpy as np
import pandas as pd

from aedes.estatistica import ComparacaoPareada, comparar_pareado, corrigir_por_holm

HORIZONTES_TESTADOS = (1, 4, 8, 12)
FONTES_TESTADAS = ("casos", "clima", "vetor")
BRACO_COMPLETO = "completo"
BRACO_SO_CALENDARIO = "so_calendario"
NOME_DO_COMPOSTO = "composto_N13"
NOME_DA_REGUA_SAZONAL = "regua_sazonal"
FOLHA_PRIMARIA = 5
FOLHA_SECUNDARIA = 20
FATOR_DO_PISO_DE_RUIDO = 2.0
NIVEL_DE_SIGNIFICANCIA = 0.05

VEREDITO_A_MELHOR = "A melhor"
VEREDITO_A_PIOR = "A pior"
VEREDITO_SEM_EVIDENCIA = "sem evidencia"

FAMILIA_F1 = "F1"
FAMILIA_F2 = "F2"
FAMILIA_F3 = "F3"
FAMILIA_F4 = "F4"

COLUNAS_DA_TABELA_DE_FAMILIAS = (
    "familia",
    "h",
    "A",
    "B",
    "n",
    "mae_A",
    "mae_B",
    "delta",
    "ganho_pct",
    "ic_inf",
    "ic_sup",
    "dm_hln",
    "p_bruto",
    "p_holm",
    "limiar_piso",
    "variancia_fallback",
    "veredito",
)


@dataclasses.dataclass(frozen=True)
class DefinicaoDoTeste:
    """Um teste A x B de uma familia.

    Attributes:
        familia: F1, F2, F3 ou F4.
        horizonte: h.
        nome_a: Nome do candidato (por exemplo `completo@f5`, `composto_N13`).
        nome_b: Nome do comparador.
        folhas_do_piso: Folhas cujo piso de ruido entra no limiar; o limiar usa o MAIOR piso entre elas.
            A regua nao tem ruido e nao entra.
    """

    familia: str
    horizonte: int
    nome_a: str
    nome_b: str
    folhas_do_piso: tuple[int, ...]


def nome_do_candidato(braco: str, folha: int) -> str:
    """Nome de um braco da E2 numa folha: `completo@f5`."""
    return f"{braco}@f{folha}"


def montar_definicoes_das_familias() -> list[DefinicaoDoTeste]:
    """Os 52 testes (12 + 12 + 12 + 16) na ordem F1, F2, F3, F4; dentro da familia por fonte e horizonte.

    Returns:
        Lista de `DefinicaoDoTeste`.
    """
    definicoes: list[DefinicaoDoTeste] = []
    candidato_completo_f5 = nome_do_candidato(BRACO_COMPLETO, FOLHA_PRIMARIA)
    candidato_completo_f20 = nome_do_candidato(BRACO_COMPLETO, FOLHA_SECUNDARIA)

    for familia, folha in ((FAMILIA_F1, FOLHA_PRIMARIA), (FAMILIA_F3, FOLHA_SECUNDARIA)):
        nome_do_completo = nome_do_candidato(BRACO_COMPLETO, folha)
        for fonte in FONTES_TESTADAS:
            nome_sem_a_fonte = nome_do_candidato(f"sem_{fonte}", folha)
            for horizonte in HORIZONTES_TESTADOS:
                definicoes.append(DefinicaoDoTeste(familia, horizonte, nome_do_completo, nome_sem_a_fonte, (folha,)))

    nome_so_calendario = nome_do_candidato(BRACO_SO_CALENDARIO, FOLHA_PRIMARIA)
    for fonte in FONTES_TESTADAS:
        nome_so_a_fonte = nome_do_candidato(f"so_{fonte}", FOLHA_PRIMARIA)
        for horizonte in HORIZONTES_TESTADOS:
            definicoes.append(
                DefinicaoDoTeste(FAMILIA_F2, horizonte, nome_so_a_fonte, nome_so_calendario, (FOLHA_PRIMARIA,))
            )

    candidatos_contra_a_regua = (
        (candidato_completo_f5, (FOLHA_PRIMARIA,)),
        (candidato_completo_f20, (FOLHA_SECUNDARIA,)),
        (NOME_DO_COMPOSTO, (FOLHA_PRIMARIA, FOLHA_SECUNDARIA)),
    )
    for nome_do_candidato_a, folhas in candidatos_contra_a_regua:
        for horizonte in HORIZONTES_TESTADOS:
            definicoes.append(DefinicaoDoTeste(FAMILIA_F4, horizonte, nome_do_candidato_a, NOME_DA_REGUA_SAZONAL, folhas))
    for horizonte in HORIZONTES_TESTADOS:
        definicoes.append(
            DefinicaoDoTeste(
                FAMILIA_F4,
                horizonte,
                NOME_DO_COMPOSTO,
                candidato_completo_f5,
                (FOLHA_PRIMARIA, FOLHA_SECUNDARIA),
            )
        )
    return definicoes


def calcular_limiar_do_piso(piso_de_ruido: pd.DataFrame, folhas_do_piso: tuple[int, ...], horizonte: int) -> float:
    """Limiar de leitura da Emenda 1: `2 x` o MAIOR piso de ruido entre as folhas envolvidas, no horizonte.

    Sem folha envolvida (nenhum ruido), o limiar e zero.

    Args:
        piso_de_ruido: `folha`, `h`, `piso_de_ruido` (`piso.csv`).
        folhas_do_piso: Folhas cujo piso entra.
        horizonte: h.

    Returns:
        O limiar em casos por semana.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se alguma (folha, h) nao tiver piso.
    """
    colunas = ["folha", "h", "piso_de_ruido"]
    ausentes = sorted(set(colunas) - set(piso_de_ruido.columns))
    if ausentes:
        raise KeyError(f"Colunas ausentes no piso: {ausentes}")
    if len(folhas_do_piso) == 0:
        return 0.0

    pisos_envolvidos: list[float] = []
    for folha in folhas_do_piso:
        linha = piso_de_ruido.loc[(piso_de_ruido["folha"] == folha) & (piso_de_ruido["h"] == horizonte)]
        if len(linha) != 1:
            raise ValueError(f"Piso ausente ou repetido para folha {folha}, h {horizonte}.")
        pisos_envolvidos.append(float(linha["piso_de_ruido"].iloc[0]))
    return FATOR_DO_PISO_DE_RUIDO * max(pisos_envolvidos)


def decidir_veredito(p_holm: float, delta: float, limiar_do_piso: float) -> str:
    """Veredito da pre-declaracao: so ha efeito se `p_Holm < 0,05` E `|delta| > limiar` (2x o piso).

    Se ha efeito: `delta > 0` -> "A melhor"; `delta < 0` -> "A pior". Caso contrario, "sem evidencia".
    Limites estritos: `p_Holm = 0,05` nao passa; `|delta| = limiar` nao passa.
    """
    passa_em_holm = p_holm < NIVEL_DE_SIGNIFICANCIA
    passa_no_piso = abs(delta) > limiar_do_piso
    if not (passa_em_holm and passa_no_piso):
        return VEREDITO_SEM_EVIDENCIA
    if delta > 0.0:
        return VEREDITO_A_MELHOR
    if delta < 0.0:
        return VEREDITO_A_PIOR
    return VEREDITO_SEM_EVIDENCIA


def executar_familias(
    definicoes: list[DefinicaoDoTeste],
    previsoes_por_candidato_e_horizonte: dict[tuple[str, int], pd.DataFrame],
    piso_de_ruido: pd.DataFrame,
) -> pd.DataFrame:
    """Roda todos os testes, aplica Holm DENTRO de cada familia e decide o veredito de cada um.

    Args:
        definicoes: Os testes (de `montar_definicoes_das_familias`).
        previsoes_por_candidato_e_horizonte: `(nome, h) -> DataFrame` com `data_alvo`, `real`, `previsto`.
        piso_de_ruido: `piso.csv`.

    Returns:
        DataFrame com `COLUNAS_DA_TABELA_DE_FAMILIAS`, uma linha por teste, na ordem das definicoes.

    Raises:
        KeyError: Se faltarem previsoes para algum candidato ou horizonte.
    """
    comparacoes: list[ComparacaoPareada] = []
    for definicao in definicoes:
        previsoes_a = previsoes_por_candidato_e_horizonte[(definicao.nome_a, definicao.horizonte)]
        previsoes_b = previsoes_por_candidato_e_horizonte[(definicao.nome_b, definicao.horizonte)]
        comparacoes.append(comparar_pareado(previsoes_a, previsoes_b, definicao.horizonte))

    p_brutos = np.array([comparacao.p_bruto for comparacao in comparacoes], dtype=float)
    p_holm = np.zeros(len(comparacoes))
    nomes_das_familias = [definicao.familia for definicao in definicoes]
    for familia in dict.fromkeys(nomes_das_familias):
        posicoes_da_familia = [posicao for posicao, nome in enumerate(nomes_das_familias) if nome == familia]
        p_holm[posicoes_da_familia] = corrigir_por_holm(p_brutos[posicoes_da_familia])

    linhas: list[dict[str, object]] = []
    for posicao, definicao in enumerate(definicoes):
        comparacao = comparacoes[posicao]
        limiar = calcular_limiar_do_piso(piso_de_ruido, definicao.folhas_do_piso, definicao.horizonte)
        veredito = decidir_veredito(float(p_holm[posicao]), comparacao.delta, limiar)
        linhas.append(
            {
                "familia": definicao.familia,
                "h": definicao.horizonte,
                "A": definicao.nome_a,
                "B": definicao.nome_b,
                "n": comparacao.n,
                "mae_A": comparacao.mae_a,
                "mae_B": comparacao.mae_b,
                "delta": comparacao.delta,
                "ganho_pct": comparacao.ganho_pct,
                "ic_inf": comparacao.ic_inf,
                "ic_sup": comparacao.ic_sup,
                "dm_hln": comparacao.dm_hln,
                "p_bruto": comparacao.p_bruto,
                "p_holm": float(p_holm[posicao]),
                "limiar_piso": limiar,
                "variancia_fallback": comparacao.variancia_fallback,
                "veredito": veredito,
            }
        )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DA_TABELA_DE_FAMILIAS))
