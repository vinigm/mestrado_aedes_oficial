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
class AtributosDoModelo:
    """O que o modelo recebe, que não é o mesmo que o arquivo guarda.

    A distinção existe porque o arquivo `tabela_final.csv` guarda o valor de
    cada grandeza NA SEMANA, e só. Nenhuma defasagem está gravada ali: elas
    nascem em tempo de execução, em `dominio/features.py`, e por isso não
    aparecem numa listagem das colunas do arquivo.

    Medido rodando o próprio pipeline do cenário adotado em 23/09/2026:
    `fontes.carregar_tabela_final` seguido de
    `features.construir_features_temporais` e
    `selecao_features.separar_grupos_de_features`.

    Attributes:
        derivados: Atributos criados em tempo de execução.
        lags_por_coluna: Quantas defasagens cada coluna elegível recebe.
        colunas_com_lag: Quantas colunas recebem defasagem.
        atributos_no_modelo: Quantos chegam ao modelo do cenário adotado.
        nucleo: Atributos do grupo núcleo — histórico do alvo e sazonalidade.
        vetor: Atributos do grupo vetor.
        clima_candidatos: Atributos de clima disponíveis para escolha.
        clima_escolhidos: Quantos de clima entram, escolhidos por ganho.
        fracao_da_selecao_de_clima: Que fatia inicial da série a escolha das
            colunas de clima usa como treino.
        inicio_da_selecao_de_clima: Primeira semana dessa fatia.
        fim_da_selecao_de_clima: Última semana dessa fatia, medida no
            horizonte de 1 semana. Nos horizontes 4 e 8 ela recua algumas
            semanas, porque há menos linhas válidas.
    """

    derivados: int = 32
    lags_por_coluna: int = 4
    colunas_com_lag: int = 7
    atributos_no_modelo: int = 20
    nucleo: int = 8
    vetor: int = 6
    clima_candidatos: int = 42
    clima_escolhidos: int = 6
    fracao_da_selecao_de_clima: str = "60%"
    inicio_da_selecao_de_clima: str = "18/03/2018"
    fim_da_selecao_de_clima: str = "27/11/2022"


ATRIBUTOS = AtributosDoModelo()


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
class AlarmePorHorizonte:
    """O alarme de surto medido em um horizonte.

    Attributes:
        semanas: Quantas semanas à frente a previsão olha.
        rotulo: Como o horizonte é dito em texto.
        sensibilidade: Fração das semanas de surto que o alarme sinaliza.
        precisao: Fração dos alarmes disparados que eram surto de verdade.
        falsos_por_ano: Quantos alarmes falsos por ano, em média.
    """

    semanas: int
    rotulo: str
    sensibilidade: float
    precisao: float
    falsos_por_ano: float


# Lido de `analises/2026-09-13_metrica_de_alarme/saidas/
# alarme_configuracao_de_referencia.csv`, medido em 102 semanas com 2 episódios
# de surto.
#
# ⚠️ O ESTADO.md §3.4 cita só 1 mês e 3 meses; os outros dois horizontes vêm do
# CSV da mesma medição. A avaliação tem apenas 2 episódios, então nada por
# episódio pode ser afirmado a partir deles.
ALARME_POR_HORIZONTE: tuple[AlarmePorHorizonte, ...] = (
    AlarmePorHorizonte(1, "1 semana", 0.969, 0.912, 1.0),
    AlarmePorHorizonte(4, "1 mês", 0.971, 0.943, 0.7),
    AlarmePorHorizonte(8, "2 meses", 0.816, 0.861, 1.7),
    AlarmePorHorizonte(12, "3 meses", 0.769, 0.811, 2.3),
)

SEMANAS_NA_AVALIACAO_DO_ALARME = 102


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
