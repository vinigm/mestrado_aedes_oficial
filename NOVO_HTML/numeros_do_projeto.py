"""Números-âncora do projeto, copiados do ESTADO.md de 13/09/2026.

Existe para que nenhuma página do site escreva um número solto no meio de uma
frase. Toda afirmação numérica do site sai daqui, e a atualização acontece num
lugar só. Se um número divergir do ESTADO.md, o ESTADO.md vence.

⚠️ Todos os valores de desempenho abaixo são POSTERIORES à correção do
vazamento temporal de 13/09/2026. Números anteriores a essa data estão
superados e não devem aparecer no site como resultado corrente.
"""

import dataclasses


@dataclasses.dataclass(frozen=True)
class DesempenhoPorHorizonte:
    """Desempenho do modelo de referência em um horizonte de previsão.

    Attributes:
        semanas: Quantas semanas à frente a previsão olha.
        rotulo: Como o horizonte é dito em texto ("1 mês", "3 meses").
        erro_medio_absoluto: MAE em casos confirmados por semana.
        r2: Fração da variação dos casos que o modelo explica.
        captura_do_pico: Fração da altura do pico que o modelo alcança.
    """

    semanas: int
    rotulo: str
    erro_medio_absoluto: float
    r2: float
    captura_do_pico: float


# Configuração de referência: HistGradientBoosting com perda quantílica em 0,85
# e o vetor entre as variáveis. Venceu entre as 30 testadas pelo menor erro de
# calibração — "a melhor entre as 30", nunca "a melhor possível".
DESEMPENHO_DO_MODELO: tuple[DesempenhoPorHorizonte, ...] = (
    DesempenhoPorHorizonte(1, "1 semana", 98.0, 0.898, 0.886),
    DesempenhoPorHorizonte(4, "1 mês", 219.7, 0.628, 0.702),
    DesempenhoPorHorizonte(8, "2 meses", 272.6, 0.450, 0.417),
    DesempenhoPorHorizonte(12, "3 meses", 278.7, 0.437, 0.388),
)


@dataclasses.dataclass(frozen=True)
class BaseCertificada:
    """A série de captura conferida célula a célula em 13/09/2026."""

    inspecoes: int = 636_587
    femeas_de_aedes_aegypti: int = 236_166
    semanas_com_dado: int = 718
    bairros: int = 81
    armadilhas: int = 2_742
    primeira_semana: str = "23/09/2012"
    ultima_semana: str = "09/08/2026"
    semanas_faltantes: int = 7
    semanas_perdidas_na_enchente: int = 3


BASE = BaseCertificada()


@dataclasses.dataclass(frozen=True)
class TabelaDeModelagem:
    """A tabela semanal única que alimenta os modelos."""

    linhas: int = 725
    colunas: int = 36
    primeira_semana_com_casos: str = "18/02/2018"
    semanas_com_casos: int = 428


TABELA = TabelaDeModelagem()


@dataclasses.dataclass(frozen=True)
class DesempenhoDoAlarme:
    """O modelo lido como alarme: cruzou o limiar ou não.

    Mede coisa diferente da captura do pico. O alarme só precisa acertar que a
    epidemia chegou; não precisa acertar o tamanho dela.
    """

    sensibilidade_um_mes: float = 0.971
    precisao_um_mes: float = 0.943
    falsos_por_ano_um_mes: float = 0.7
    sensibilidade_tres_meses: float = 0.769
    precisao_tres_meses: float = 0.811
    falsos_por_ano_tres_meses: float = 2.3
    episodios_na_avaliacao: int = 2


ALARME = DesempenhoDoAlarme()


@dataclasses.dataclass(frozen=True)
class EfeitoDoVetor:
    """O que foi medido sobre a contribuição da armadilha.

    São dois achados de sinal oposto e peso muito diferente: na previsão de
    casos não há efeito demonstrável; no alarme de surto de horizonte longo o
    vetor piora, e esse é o único resultado do projeto que sobrevive a Holm.
    """

    comparacoes_pareadas: int = 60
    comparacoes_em_que_o_vetor_erra_menos: int = 27
    comparacoes_que_sobrevivem_a_holm: int = 0
    semanas_no_teste_de_alarme: int = 553
    semanas_em_que_so_clima_acerta: int = 23
    semanas_em_que_clima_mais_vetor_acerta: int = 7
    p_bruto_do_alarme: float = 0.0062
    p_holm_do_alarme: float = 0.037


VETOR = EfeitoDoVetor()


@dataclasses.dataclass(frozen=True)
class CustoDoVazamento:
    """O que o vazamento temporal escondia, medido em 13/09/2026.

    Entra no site como contribuição metodológica: é um defeito que a literatura
    da área comete, e ele não é neutro — favorece exatamente as escolhas que o
    projeto tinha adotado.
    """

    piora_do_erro_em_tres_meses: float = 0.52
    r2_inflado_em_tres_meses: float = 0.758
    r2_real_em_tres_meses: float = 0.437
    celulas_re_rodadas: int = 152
    controles_independentes: int = 6


VAZAMENTO = CustoDoVazamento()


@dataclasses.dataclass(frozen=True)
class CamadaEspacial:
    """A comparação entre a regra simples e o aprendizado de máquina por zona."""

    combinacoes_testadas: int = 8
    combinacoes_vencidas_pela_regra_simples: int = 8
    correlacao_da_persistencia: float = 0.89
    correlacao_da_climatologia: float = 0.46


ESPACIAL = CamadaEspacial()


@dataclasses.dataclass(frozen=True)
class CausaDaDegradacao:
    """Por que o modelo piora em horizontes longos (ESTADO.md §3.1).

    A autocorrelação da própria série de casos — quanto o valor de uma semana
    se explica pelo valor das semanas mais recentes — carrega quase todo o
    acerto em horizonte curto, e nenhum em horizonte longo. A degradação não é
    defeito de ajuste: em três meses o passado recente simplesmente não
    informa mais.
    """

    fracao_explicada_em_uma_semana: float = 0.91
    fracao_explicada_em_doze_semanas: float = 0.0


DEGRADACAO = CausaDaDegradacao()


@dataclasses.dataclass(frozen=True)
class LimitesDeAfirmacao:
    """Números por trás do que NÃO se pode afirmar (ESTADO.md §3.7).

    Cada campo sustenta uma afirmação que os dados, lidos com a leitura mais
    favorável possível, ainda assim não demonstram.
    """

    equivalencia_clima_vetor_fechada: int = 1
    equivalencia_clima_vetor_testada: int = 8
    peso_da_perda_percentual: float = 0.099
    peso_do_algoritmo_percentual: float = 0.118
    colunas_de_clima_total: int = 6
    colunas_de_clima_que_mudam_ao_recortar: int = 4


LIMITES = LimitesDeAfirmacao()


# Datas e marcos que aparecem em texto. Ficam aqui para não haver data relativa
# ("mês passado") em lugar nenhum do site.
DATA_DA_CORRECAO_DO_VAZAMENTO = "13/09/2026"
DATA_DA_REUNIAO_DE_ALINHAMENTO = "21/09/2026"
JANELA_UTIL_DE_TRABALHO = "2022 a 2025"
TOTAL_DE_CONFIGURACOES_TESTADAS = 30


def formatar_inteiro(valor: int) -> str:
    """Formata um inteiro no padrão brasileiro, com ponto de milhar."""
    return f"{valor:,}".replace(",", ".")


def formatar_decimal(valor: float, casas: int) -> str:
    """Formata um número com vírgula decimal e ponto de milhar."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def formatar_percentual(fracao: float, casas: int = 1) -> str:
    """Converte uma fração (0 a 1) em percentual escrito."""
    return f"{formatar_decimal(fracao * 100, casas)}%"
