"""E6c: reproducao da busca de 18 hiperparametros do HistGB (quantil 0,85, M1).

Funcoes puras: nao leem nem gravam arquivo. Replica, sem nenhuma correcao, a
busca do codigo antigo:
    - grade, referencia e criterio da fase 1:
      `analises/2026-09-23_bateria_noturna/bloco_6_hiperparametros/rodar.py` e
      `PRE_DECLARACAO.md` do mesmo bloco;
    - comparacao pareada da fase 2 (Wilcoxon + Holm):
      `analises/2026-09-23_bateria_noturna/harness.py:comparar_pareado`,
      `corrigir_por_holm` e `relatar_comparacoes`.

A GRADE (18 = 3 x 3 x 2)

    ritmo `taxa x iteracoes`   0,05 x 250  |  0,03 x 400  |  0,10 x 150
    folhas maximas             15  |  7  |  31
    folha minima               5   |  20
    fixos: quantil 0,85, M1 (22 variaveis), `random_state` 42, sem truncar em 0.

FASE 1 (escolha, so calibracao): menor MAE medio, em h = 1, 4, 8 e 12, das
semanas-alvo ate 31/12/2023. A avaliacao NAO participa.

FASE 2 (um teste na avaliacao): a vencedora contra a referencia (0,05 x 250,
15 folhas, folha minima 5), Wilcoxon pareado por `data_alvo`, Holm sobre os 4
horizontes. A referencia SO e trocada se a vencedora reduzir o MAE em h = 8 E
h = 12 com p de Holm < 0,05 nos dois. Se a vencedora da fase 1 for a propria
referencia, nao ha teste e nada muda.
"""

import dataclasses

import numpy as np
import pandas as pd
from scipy import stats

from aedes.configuracao import COLUNA_DATA_ALVO, FOLHA_5, ConfiguracaoModelo
from aedes.estatistica import corrigir_por_holm
from aedes.metricas import COLUNA_DO_PREVISTO, COLUNA_DO_REAL, erro_absoluto_medio, r_quadrado
from aedes.walk_forward import COLUNA_DO_HORIZONTE

HORIZONTES_DA_BUSCA = (1, 4, 8, 12)
HORIZONTES_DE_DECISAO = (8, 12)
NIVEL_DE_SIGNIFICANCIA = 0.05

# Ritmo: `taxa de aprendizado, iteracoes` andam juntos (taxa menor pede mais arvores).
RITMOS_DA_BUSCA = ((0.05, 250), (0.03, 400), (0.10, 150))
MAXIMOS_DE_FOLHAS_DA_BUSCA = (15, 7, 31)
FOLHAS_MINIMAS_DA_BUSCA = (5, 20)

NOME_DA_REFERENCIA = "lr0.05_it250_folhas15_min5"
COLUNA_DA_CONFIGURACAO = "configuracao"
COLUNA_DO_MAE_DE_CALIBRACAO = "mae_calibracao"


@dataclasses.dataclass(frozen=True)
class ConfiguracaoDeHiperparametros:
    """Uma das 18 combinacoes de hiperparametros do HistGB.

    Attributes:
        nome: Identificador do antigo, por exemplo `lr0.03_it400_folhas15_min5`.
        taxa_de_aprendizado: Passo de cada arvore.
        numero_de_iteracoes: Quantas arvores.
        maximo_de_folhas: Tamanho maximo de cada arvore.
        folha_minima: Menor numero de semanas numa folha.
    """

    nome: str
    taxa_de_aprendizado: float
    numero_de_iteracoes: int
    maximo_de_folhas: int
    folha_minima: int

    def para_configuracao_do_modelo(self) -> ConfiguracaoModelo:
        """O `ConfiguracaoModelo` do pacote: a `FOLHA_5` (quantil 0,85, semente 42) trocando os 4 hiperparametros."""
        return dataclasses.replace(
            FOLHA_5,
            nome=f"histgb_{self.nome}",
            taxa_de_aprendizado=self.taxa_de_aprendizado,
            numero_de_iteracoes=self.numero_de_iteracoes,
            maximo_de_folhas=self.maximo_de_folhas,
            folha_minima=self.folha_minima,
        )


def montar_nome_da_configuracao(
    taxa_de_aprendizado: float,
    numero_de_iteracoes: int,
    maximo_de_folhas: int,
    folha_minima: int,
) -> str:
    """Nome do antigo: `lr0.03_it400_folhas15_min5` (a taxa 0,10 vira `lr0.1`)."""
    return f"lr{taxa_de_aprendizado}_it{numero_de_iteracoes}_folhas{maximo_de_folhas}_min{folha_minima}"


def montar_a_grade_de_18() -> list[ConfiguracaoDeHiperparametros]:
    """As 18 configuracoes na ordem do antigo (ritmo, folhas maximas, folha minima).

    A referencia (0,05 x 250, 15 folhas, folha minima 5) e a PRIMEIRA: sem ela
    nao ha trava nem comparacao.
    """
    grade: list[ConfiguracaoDeHiperparametros] = []
    for taxa_de_aprendizado, numero_de_iteracoes in RITMOS_DA_BUSCA:
        for maximo_de_folhas in MAXIMOS_DE_FOLHAS_DA_BUSCA:
            for folha_minima in FOLHAS_MINIMAS_DA_BUSCA:
                nome = montar_nome_da_configuracao(
                    taxa_de_aprendizado, numero_de_iteracoes, maximo_de_folhas, folha_minima
                )
                grade.append(
                    ConfiguracaoDeHiperparametros(
                        nome, taxa_de_aprendizado, numero_de_iteracoes, maximo_de_folhas, folha_minima
                    )
                )
    return grade


def calcular_mae_medio_de_calibracao(
    previsoes_da_configuracao: pd.DataFrame,
    horizontes: tuple[int, ...] = HORIZONTES_DA_BUSCA,
) -> float:
    """Criterio da fase 1: media, nos horizontes, do MAE das previsoes da calibracao.

    Aqui `previsoes_da_configuracao` ja traz SO as semanas-alvo da calibracao
    (o script corta a matriz em 31/12/2023 antes do laco; o resultado e igual
    ao de rodar tudo e filtrar). Cada horizonte pesa igual, qualquer que seja o `n`.

    Args:
        previsoes_da_configuracao: `h`, `real`, `previsto` de UMA configuracao.
        horizontes: Horizontes da media (1, 4, 8 e 12).

    Returns:
        O MAE medio.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se algum horizonte nao tiver nenhuma previsao.
    """
    colunas_ausentes = sorted({COLUNA_DO_HORIZONTE, COLUNA_DO_REAL, COLUNA_DO_PREVISTO} - set(previsoes_da_configuracao.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes: {colunas_ausentes}")

    maes_por_horizonte: list[float] = []
    for horizonte in horizontes:
        do_horizonte = previsoes_da_configuracao.loc[previsoes_da_configuracao[COLUNA_DO_HORIZONTE] == horizonte]
        if len(do_horizonte) == 0:
            raise ValueError(f"Nenhuma previsao no horizonte {horizonte}.")
        maes_por_horizonte.append(erro_absoluto_medio(do_horizonte[COLUNA_DO_REAL], do_horizonte[COLUNA_DO_PREVISTO]))
    return sum(maes_por_horizonte) / len(maes_por_horizonte)


def montar_ranking_da_fase_1(maes_de_calibracao: dict[str, float]) -> pd.DataFrame:
    """Ordena as configuracoes pelo MAE medio de calibracao (menor primeiro).

    A ordenacao e ESTAVEL: com MAE identico, vale a ordem em que as
    configuracoes foram dadas (a da grade). No antigo havia empates exatos
    (por exemplo `lr0.1_it150_folhas15_min20` e `..._folhas31_min20`), cuja
    ordem relativa a ordenacao padrao do pandas nao garante; empate nao muda a
    vencedora, que e uma configuracao de folha minima 5.

    Args:
        maes_de_calibracao: `nome -> MAE medio`, na ordem da grade.

    Returns:
        DataFrame com `configuracao`, `mae_calibracao`, `pos` (a partir de 1).

    Raises:
        ValueError: Se o dicionario for vazio.
    """
    if len(maes_de_calibracao) == 0:
        raise ValueError("maes_de_calibracao nao pode ser vazio.")
    linhas = pd.DataFrame(
        {
            COLUNA_DA_CONFIGURACAO: list(maes_de_calibracao.keys()),
            COLUNA_DO_MAE_DE_CALIBRACAO: list(maes_de_calibracao.values()),
        }
    )
    ordenado = linhas.sort_values(COLUNA_DO_MAE_DE_CALIBRACAO, kind="stable").reset_index(drop=True)
    ordenado.insert(0, "pos", ordenado.index + 1)
    return ordenado


@dataclasses.dataclass(frozen=True)
class ComparacaoDaFase2:
    """A vencedora contra a referencia em UM horizonte, pareada por `data_alvo`.

    Attributes:
        horizonte: h.
        n_pares: Semanas em comum.
        mae_referencia: MAE da referencia nessas semanas.
        mae_vencedora: MAE da vencedora nessas semanas.
        reducao_percentual: `100 * (mae_referencia - mae_vencedora) / mae_referencia`; negativo = piorou.
        r2_referencia: R2 da referencia.
        r2_vencedora: R2 da vencedora.
        p_bruto: p do Wilcoxon pareado sobre os erros absolutos.
    """

    horizonte: int
    n_pares: int
    mae_referencia: float
    mae_vencedora: float
    reducao_percentual: float
    r2_referencia: float
    r2_vencedora: float
    p_bruto: float


def comparar_vencedora_com_referencia(
    previsoes_da_referencia: pd.DataFrame,
    previsoes_da_vencedora: pd.DataFrame,
    horizonte: int,
) -> ComparacaoDaFase2:
    """Wilcoxon pareado dos erros absolutos da vencedora e da referencia, por `data_alvo` (`harness.comparar_pareado`).

    Regras do antigo, preservadas: so entram as semanas que os dois preveem;
    se os dois vetores de erro forem iguais (`np.allclose`) o p e 1,0 sem chamar
    o teste; senao `scipy.stats.wilcoxon(erro_ref, erro_var)` com os argumentos
    padrao (zero_method `wilcox`, metodo `auto`).

    Args:
        previsoes_da_referencia: `h`, `data_alvo`, `real`, `previsto`, ja na janela de avaliacao.
        previsoes_da_vencedora: Idem.
        horizonte: h.

    Returns:
        A `ComparacaoDaFase2`.

    Raises:
        ValueError: Se nenhuma semana for comum ou se uma `data_alvo` se repetir.
    """
    colunas = [COLUNA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
    do_horizonte_da_referencia = previsoes_da_referencia.loc[previsoes_da_referencia[COLUNA_DO_HORIZONTE] == horizonte]
    do_horizonte_da_vencedora = previsoes_da_vencedora.loc[previsoes_da_vencedora[COLUNA_DO_HORIZONTE] == horizonte]
    da_referencia = do_horizonte_da_referencia[colunas]
    da_vencedora = do_horizonte_da_vencedora[colunas]
    if da_referencia[COLUNA_DATA_ALVO].duplicated().any() or da_vencedora[COLUNA_DATA_ALVO].duplicated().any():
        raise ValueError("data_alvo repetida em uma das previsoes.")

    pareado = da_referencia.merge(da_vencedora, on=COLUNA_DATA_ALVO, suffixes=("_ref", "_var"))
    if pareado.empty:
        raise ValueError(f"Nenhuma semana em comum no horizonte {horizonte}.")

    erro_da_referencia = np.abs(pareado[f"{COLUNA_DO_REAL}_ref"] - pareado[f"{COLUNA_DO_PREVISTO}_ref"])
    erro_da_vencedora = np.abs(pareado[f"{COLUNA_DO_REAL}_var"] - pareado[f"{COLUNA_DO_PREVISTO}_var"])

    if np.allclose(erro_da_referencia, erro_da_vencedora):
        p_bruto = 1.0
    else:
        _, p_do_teste = stats.wilcoxon(erro_da_referencia, erro_da_vencedora)
        p_bruto = float(p_do_teste)

    mae_da_referencia = erro_absoluto_medio(pareado[f"{COLUNA_DO_REAL}_ref"], pareado[f"{COLUNA_DO_PREVISTO}_ref"])
    mae_da_vencedora = erro_absoluto_medio(pareado[f"{COLUNA_DO_REAL}_var"], pareado[f"{COLUNA_DO_PREVISTO}_var"])
    r2_da_referencia = r_quadrado(pareado[f"{COLUNA_DO_REAL}_ref"], pareado[f"{COLUNA_DO_PREVISTO}_ref"])
    r2_da_vencedora = r_quadrado(pareado[f"{COLUNA_DO_REAL}_var"], pareado[f"{COLUNA_DO_PREVISTO}_var"])
    reducao = 100.0 * (mae_da_referencia - mae_da_vencedora) / mae_da_referencia

    return ComparacaoDaFase2(
        horizonte=horizonte,
        n_pares=len(pareado),
        mae_referencia=mae_da_referencia,
        mae_vencedora=mae_da_vencedora,
        reducao_percentual=reducao,
        r2_referencia=r2_da_referencia,
        r2_vencedora=r2_da_vencedora,
        p_bruto=p_bruto,
    )


@dataclasses.dataclass(frozen=True)
class DecisaoDaFase2:
    """Veredito da fase 2.

    Attributes:
        comparacoes: Uma por horizonte, na ordem dos horizontes.
        p_holm: p de Holm de cada comparacao (Holm sobre todas as comparacoes).
        troca_a_referencia: Verdadeiro se, em TODOS os horizontes de decisao,
            a vencedora reduziu o MAE e o p de Holm ficou abaixo de 0,05.
    """

    comparacoes: list[ComparacaoDaFase2]
    p_holm: list[float]
    troca_a_referencia: bool


def decidir_a_fase_2(
    comparacoes: list[ComparacaoDaFase2],
    horizontes_de_decisao: tuple[int, ...] = HORIZONTES_DE_DECISAO,
    nivel_de_significancia: float = NIVEL_DE_SIGNIFICANCIA,
) -> DecisaoDaFase2:
    """Holm sobre todas as comparacoes e a regra de troca do antigo.

    A vencedora so ENTRA se, em h = 8 E h = 12, `mae_vencedora < mae_referencia`
    (reduziu, estrito) e `p_holm < 0,05` (estrito) nos dois.

    Args:
        comparacoes: As comparacoes por horizonte (4 na busca).
        horizontes_de_decisao: Onde a regra decide (8 e 12).
        nivel_de_significancia: 0,05.

    Returns:
        A `DecisaoDaFase2`.

    Raises:
        ValueError: Se faltar comparacao para algum horizonte de decisao.
    """
    horizontes_comparados = [comparacao.horizonte for comparacao in comparacoes]
    for horizonte in horizontes_de_decisao:
        if horizonte not in horizontes_comparados:
            raise ValueError(f"Falta a comparacao do horizonte de decisao {horizonte}.")

    p_brutos = np.array([comparacao.p_bruto for comparacao in comparacoes], dtype=float)
    p_holm = corrigir_por_holm(p_brutos)

    troca = True
    for comparacao, p_ajustado in zip(comparacoes, p_holm):
        if comparacao.horizonte not in horizontes_de_decisao:
            continue
        reduziu = comparacao.mae_vencedora < comparacao.mae_referencia
        significativo = float(p_ajustado) < nivel_de_significancia
        troca = troca and reduziu and significativo

    return DecisaoDaFase2(comparacoes=comparacoes, p_holm=[float(p) for p in p_holm], troca_a_referencia=bool(troca))
