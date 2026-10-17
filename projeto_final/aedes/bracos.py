"""Bracos da ablacao (E2): quais blocos de variaveis cada braco recebe, e a matriz de cada um.

A ablacao mede quanto cada FONTE de informacao contribui para a previsao. As 22
variaveis do modelo pertencem a quatro blocos (Tabela 1 do artigo):

    casos       (C, 6)  casos, casos_lag1..4, casos_mm4
    clima       (M, 6)  as 6 colunas de clima congeladas
    vetor       (V, 6)  aedes_aegypti_por_armadilha, _lag1..4, vetor_mm4
    calendario  (K, 4)  sem_sin, sem_cos (semana de origem), alvo_sin, alvo_cos
                        (semana-alvo)

e cada braco e um subconjunto desses blocos; o calendario esta em TODOS os bracos
(pre-declaracao de 12/10/2026, secao 4).

PROTOCOLO DA MATRIZ DE CADA BRACO (fixado pela trava 2 da pre-declaracao)

    A trava 2 exige reproduzir o braco antigo `HistGB_folha20_M0` (sem vetor). O
    codigo antigo descartava as linhas com ausente SO nas colunas do proprio
    braco (mais o alvo). Por isso `montar_matriz_do_braco` faz `dropna` apenas
    nas colunas do braco e em `y_h`. Consequencia: os bracos sem vetor ganham as
    semanas em que a armadilha nao foi vistoriada (enchente de 2024), e o
    numero de linhas (e de previsoes) deles e maior que o do `completo`.
    As colunas saem na ordem de `ConfiguracaoVariaveis.nomes_das_variaveis`,
    filtrada: treinar e prever usam sempre a mesma ordem.

Para o braco `completo`, a matriz e IDENTICA, bit a bit, a de
`aedes.variaveis.montar_matriz_do_horizonte` (teste diferencial).

Funcoes puras: nao leem nem gravam arquivo.
"""

import dataclasses

import pandas as pd

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    ConfiguracaoDados,
    ConfiguracaoVariaveis,
    nome_da_variavel_defasada,
)
from aedes.variaveis import (
    calcular_seno_e_cosseno_da_semana,
    construir_variaveis_de_origem,
)

BLOCO_CASOS = "casos"
BLOCO_CLIMA = "clima"
BLOCO_VETOR = "vetor"
BLOCO_CALENDARIO = "calendario"

BLOCOS_CONHECIDOS = (BLOCO_CASOS, BLOCO_CLIMA, BLOCO_VETOR, BLOCO_CALENDARIO)


@dataclasses.dataclass(frozen=True)
class Braco:
    """Um braco da ablacao: um nome e os blocos de variaveis que ele recebe.

    Attributes:
        nome: Identificador do braco nos resultados (`completo`, `sem_vetor`, ...).
        blocos: Blocos de variaveis do braco, em qualquer ordem; as colunas
            saem sempre na ordem de `ConfiguracaoVariaveis.nomes_das_variaveis`.
    """

    nome: str
    blocos: tuple[str, ...]

    def __post_init__(self) -> None:
        """Rejeita braco sem calendario, com bloco desconhecido ou com bloco repetido.

        Raises:
            ValueError: Se algum bloco nao for um dos quatro conhecidos, se
                houver bloco repetido, ou se o calendario nao estiver entre
                eles (a pre-declaracao poe o calendario em todos os bracos).
        """
        for bloco in self.blocos:
            if bloco not in BLOCOS_CONHECIDOS:
                raise ValueError(f"Bloco desconhecido {bloco!r} no braco {self.nome!r}.")
        if len(set(self.blocos)) != len(self.blocos):
            raise ValueError(f"Bloco repetido no braco {self.nome!r}: {self.blocos!r}.")
        if BLOCO_CALENDARIO not in self.blocos:
            raise ValueError(f"O braco {self.nome!r} deve conter o bloco {BLOCO_CALENDARIO!r}.")


# Ordem = ordem da pre-declaracao (secao 4) e a ordem dos arquivos de saida.
BRACOS: tuple[Braco, ...] = (
    Braco("completo", (BLOCO_CASOS, BLOCO_CLIMA, BLOCO_VETOR, BLOCO_CALENDARIO)),
    Braco("sem_casos", (BLOCO_CLIMA, BLOCO_VETOR, BLOCO_CALENDARIO)),
    Braco("sem_clima", (BLOCO_CASOS, BLOCO_VETOR, BLOCO_CALENDARIO)),
    Braco("sem_vetor", (BLOCO_CASOS, BLOCO_CLIMA, BLOCO_CALENDARIO)),
    Braco("so_casos", (BLOCO_CASOS, BLOCO_CALENDARIO)),
    Braco("so_clima", (BLOCO_CLIMA, BLOCO_CALENDARIO)),
    Braco("so_vetor", (BLOCO_VETOR, BLOCO_CALENDARIO)),
    Braco("so_calendario", (BLOCO_CALENDARIO,)),
)

NOMES_DOS_BRACOS = tuple(braco.nome for braco in BRACOS)


def obter_braco(nome_do_braco: str) -> Braco:
    """Devolve o braco pelo nome.

    Raises:
        ValueError: Se o nome nao for um dos 8 bracos.
    """
    for braco in BRACOS:
        if braco.nome == nome_do_braco:
            return braco
    raise ValueError(f"Braco desconhecido {nome_do_braco!r}; esperado um de {NOMES_DOS_BRACOS}.")


def nomes_das_variaveis_do_bloco(
    bloco: str,
    configuracao_variaveis: ConfiguracaoVariaveis,
) -> list[str]:
    """Lista as variaveis de um bloco, derivadas da configuracao (nada escrito a mao).

    Args:
        bloco: Um dos quatro blocos conhecidos.
        configuracao_variaveis: Defasagens, janela e colunas de clima.

    Returns:
        Os nomes das variaveis do bloco (sem ordem relevante).

    Raises:
        ValueError: Se o bloco for desconhecido.
    """
    if bloco not in BLOCOS_CONHECIDOS:
        raise ValueError(f"Bloco desconhecido {bloco!r}; esperado um de {BLOCOS_CONHECIDOS}.")

    nomes: list[str] = []
    if bloco == BLOCO_CASOS:
        nome_dos_casos = configuracao_variaveis.nome_da_variavel_de_casos
        nomes.append(nome_dos_casos)
        for defasagem in configuracao_variaveis.defasagens_de_casos:
            nomes.append(nome_da_variavel_defasada(nome_dos_casos, defasagem))
        nomes.append(configuracao_variaveis.nome_da_media_movel_de_casos())
    elif bloco == BLOCO_CLIMA:
        for variavel_de_clima in configuracao_variaveis.variaveis_de_clima:
            nomes.append(variavel_de_clima.nome)
    elif bloco == BLOCO_VETOR:
        nome_do_vetor = configuracao_variaveis.coluna_do_vetor
        nomes.append(nome_do_vetor)
        for defasagem in configuracao_variaveis.defasagens_do_vetor:
            nomes.append(nome_da_variavel_defasada(nome_do_vetor, defasagem))
        nomes.append(configuracao_variaveis.nome_da_media_movel_do_vetor())
    else:
        nomes.extend(configuracao_variaveis.nomes_da_sazonalidade_da_origem)
        nomes.extend(configuracao_variaveis.nomes_da_sazonalidade_do_alvo)
    return nomes


def nomes_das_variaveis_do_braco(
    nome_do_braco: str,
    configuracao_variaveis: ConfiguracaoVariaveis,
) -> list[str]:
    """Lista as variaveis do braco na ORDEM de `nomes_das_variaveis` (a ordem do modelo).

    Args:
        nome_do_braco: Um dos 8 bracos.
        configuracao_variaveis: Define as 22 variaveis e a ordem delas.

    Returns:
        Os nomes das variaveis que o braco recebe, filtrados da ordem oficial.

    Raises:
        ValueError: Se o braco for desconhecido.
    """
    braco = obter_braco(nome_do_braco)
    nomes_do_braco: set[str] = set()
    for bloco in braco.blocos:
        nomes_do_bloco = nomes_das_variaveis_do_bloco(bloco, configuracao_variaveis)
        nomes_do_braco.update(nomes_do_bloco)

    nomes_na_ordem_do_modelo: list[str] = []
    for nome_da_variavel in configuracao_variaveis.nomes_das_variaveis:
        if nome_da_variavel in nomes_do_braco:
            nomes_na_ordem_do_modelo.append(nome_da_variavel)
    return nomes_na_ordem_do_modelo


def montar_matriz_do_braco(
    tabela_cortada: pd.DataFrame,
    horizonte: int,
    nome_do_braco: str,
    configuracao_variaveis: ConfiguracaoVariaveis,
    configuracao_dados: ConfiguracaoDados,
) -> pd.DataFrame:
    """Monta a matriz de um horizonte para um braco: so as colunas do braco entram.

    Mesmas regras de `aedes.variaveis.montar_matriz_do_horizonte` (alvo
    `y_h = casos.shift(-h)`, sazonalidade da semana-alvo, ordem cronologica,
    indice renumerado), com UMA diferenca declarada: o `dropna` olha so as
    colunas do braco e `y_h`. Linhas com ausente em variavel de outro braco
    (por exemplo, o vetor na semana da enchente) ficam, se as colunas do
    braco estiverem completas.

    Colunas da saida: `data_origem`, `data_alvo`, as variaveis do braco (na
    ordem de `nomes_das_variaveis`) e `y_h`.

    Args:
        tabela_cortada: Tabela semanal depois do corte de maturidade, em grade
            semanal contigua. Nao e modificada.
        horizonte: Semanas a frente (inteiro >= 1).
        nome_do_braco: Um dos 8 bracos.
        configuracao_variaveis: Receita das variaveis e a ordem final.
        configuracao_dados: Nomes da coluna de data e da de casos.

    Returns:
        DataFrame novo; pode ter zero linhas.

    Raises:
        ValueError: Se o horizonte for invalido, o braco for desconhecido ou a
            grade nao for semanal contigua.
        KeyError: Se faltar coluna que a receita consome.
    """
    horizonte_e_valido = isinstance(horizonte, int) and not isinstance(horizonte, bool)
    if not horizonte_e_valido or horizonte < 1:
        raise ValueError(f"horizonte deve ser inteiro >= 1, recebido {horizonte!r}.")
    colunas_do_braco = nomes_das_variaveis_do_braco(nome_do_braco, configuracao_variaveis)

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
    for nome_da_variavel in colunas_do_braco:
        if nome_da_variavel in variaveis_de_origem.columns:
            colunas_por_nome[nome_da_variavel] = variaveis_de_origem[nome_da_variavel]
        else:
            colunas_por_nome[nome_da_variavel] = sazonalidade_do_alvo[nome_da_variavel]
    colunas_por_nome[COLUNA_DO_ALVO] = alvo_em_casos

    matriz_com_ausentes = pd.DataFrame(colunas_por_nome, index=tabela_cortada.index)

    # O descarte olha so as colunas do proprio braco (trava 2 da pre-declaracao).
    colunas_que_nao_podem_faltar = list(colunas_do_braco)
    colunas_que_nao_podem_faltar.append(COLUNA_DO_ALVO)
    matriz_completa = matriz_com_ausentes.dropna(subset=colunas_que_nao_podem_faltar)

    return matriz_completa.reset_index(drop=True)
