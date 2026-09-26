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
class ColunaDeClimaCandidata:
    """Uma coluna de clima na disputa por uma das seis vagas.

    Attributes:
        nome: Nome da coluna na tabela de modelagem.
        ganho: Fatia do ganho total que ela levou, em porcento.
        entra: Se ficou entre as seis escolhidas.
    """

    nome: str
    ganho: float
    entra: bool


# Ranking medido em 23/09/2026 rodando `selecao_features.selecionar_clima_por_ganho`
# com a configuração do cenário adotado. Só o topo aparece no site; são 42
# candidatas ao todo. O ganho é somado nos horizontes de 1, 4 e 8 semanas.
RANKING_DE_CLIMA: tuple[ColunaDeClimaCandidata, ...] = (
    ColunaDeClimaCandidata("temp_media_lag4", 14.69, True),
    ColunaDeClimaCandidata("umid_media", 13.54, True),
    ColunaDeClimaCandidata("temp_media_lag3", 10.82, True),
    ColunaDeClimaCandidata("temp_max", 8.90, True),
    ColunaDeClimaCandidata("pressao_media_lag3", 8.03, True),
    ColunaDeClimaCandidata("pressao_media_lag4", 6.16, True),
    ColunaDeClimaCandidata("temp_amplitude_media", 5.29, False),
    ColunaDeClimaCandidata("umid_media_lag2", 4.75, False),
    ColunaDeClimaCandidata("umid_media_lag1", 4.28, False),
    ColunaDeClimaCandidata("umid_media_lag3", 4.24, False),
)

GANHO_DAS_SEIS_ESCOLHIDAS = 62.1
HORIZONTES_DA_SELECAO_DE_CLIMA = "1, 4 e 8 semanas"


@dataclasses.dataclass(frozen=True)
class FeatureDoModelo:
    """Uma coluna que chega ao modelo do cenário adotado.

    Attributes:
        nome: Nome da coluna.
        grupo: Núcleo, Clima ou Vetor.
        descricao: O que ela carrega, em uma linha.
    """

    nome: str
    grupo: str
    descricao: str


# As 20 colunas que o cenário adotado entrega ao modelo, na ordem em que o
# pipeline as monta: núcleo, depois o clima escolhido, depois o vetor.
# Medido em 23/09/2026.
FEATURES_FINAIS: tuple[FeatureDoModelo, ...] = (
    FeatureDoModelo("casos", "Núcleo", "Casos confirmados na própria semana."),
    FeatureDoModelo("casos_lag1", "Núcleo", "Casos de 1 semana atrás."),
    FeatureDoModelo("casos_lag2", "Núcleo", "Casos de 2 semanas atrás."),
    FeatureDoModelo("casos_lag3", "Núcleo", "Casos de 3 semanas atrás."),
    FeatureDoModelo("casos_lag4", "Núcleo", "Casos de 4 semanas atrás."),
    FeatureDoModelo("casos_mm4", "Núcleo", "Média dos casos nas últimas 4 semanas."),
    FeatureDoModelo("sem_sin", "Núcleo", "Seno da semana do ano: onde estamos no ciclo."),
    FeatureDoModelo("sem_cos", "Núcleo", "Cosseno da semana do ano, par do anterior."),
    FeatureDoModelo("temp_media_lag4", "Clima", "Temperatura média de 4 semanas atrás."),
    FeatureDoModelo("umid_media", "Clima", "Umidade relativa média da própria semana."),
    FeatureDoModelo("temp_media_lag3", "Clima", "Temperatura média de 3 semanas atrás."),
    FeatureDoModelo("temp_max", "Clima", "Temperatura máxima da própria semana."),
    FeatureDoModelo("pressao_media_lag3", "Clima", "Pressão média de 3 semanas atrás."),
    FeatureDoModelo("pressao_media_lag4", "Clima", "Pressão média de 4 semanas atrás."),
    FeatureDoModelo(
        "aedes_aegypti_por_armadilha", "Vetor", "Densidade do vetor na própria semana."
    ),
    FeatureDoModelo(
        "aedes_aegypti_por_armadilha_lag1", "Vetor", "Densidade de 1 semana atrás."
    ),
    FeatureDoModelo(
        "aedes_aegypti_por_armadilha_lag2", "Vetor", "Densidade de 2 semanas atrás."
    ),
    FeatureDoModelo(
        "aedes_aegypti_por_armadilha_lag3", "Vetor", "Densidade de 3 semanas atrás."
    ),
    FeatureDoModelo(
        "aedes_aegypti_por_armadilha_lag4", "Vetor", "Densidade de 4 semanas atrás."
    ),
    FeatureDoModelo("vetor_mm4", "Vetor", "Média da densidade nas últimas 4 semanas."),
)


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


# --------------------------------------------------- página Comparações ----
#
# Período de avaliação comum a toda a página: 2024 a fev/2026, 102 semanas por
# horizonte — a mesma grade de `data_alvo` do braço `referencia` (ver
# `analises/2026-09-25_regua_regras_simples/README.md`).
PERIODO_DE_AVALIACAO_DAS_COMPARACOES = "2024 a fev/2026"
SEMANAS_POR_HORIZONTE_NAS_COMPARACOES = 102


@dataclasses.dataclass(frozen=True)
class ErroPorHorizonteEMetodo:
    """MAE (casos confirmados por semana) de um método, nos quatro horizontes.

    Fonte: `analises/2026-09-25_regua_regras_simples/README.md` e `saidas/`,
    medido nas mesmas 102 semanas de avaliação do braço `referencia`.

    Attributes:
        metodo: Nome do método ou modelo.
        uma_semana: MAE em 1 semana.
        um_mes: MAE em 1 mês (4 semanas).
        dois_meses: MAE em 2 meses (8 semanas).
        tres_meses: MAE em 3 meses (12 semanas).
    """

    metodo: str
    uma_semana: float
    um_mes: float
    dois_meses: float
    tres_meses: float


REGUA_DE_METODOS_SIMPLES: tuple[ErroPorHorizonteEMetodo, ...] = (
    ErroPorHorizonteEMetodo("Cenário adotado", 98.0, 219.7, 272.6, 278.8),
    ErroPorHorizonteEMetodo("HistGB, folha mínima 20", 133.6, 199.6, 223.2, 243.8),
    ErroPorHorizonteEMetodo("Repetir a semana atual", 83.3, 279.0, 531.0, 697.5),
    ErroPorHorizonteEMetodo("Mesma semana do ano passado", 202.1, 213.2, 216.2, 217.8),
)


@dataclasses.dataclass(frozen=True)
class ErroDeMetodoDaLiteratura:
    """MAE em 3 meses de um método aplicado aos dados do projeto.

    Fonte: `analises/2026-09-25_modelos_de_fundacao/README.md`,
    `analises/2026-09-25_sarima_lasso_ensemble/README.md` e
    `analises/2026-09-25_bateria_formulacao_do_alvo/README.md` — mesmas 102
    semanas de avaliação de `REGUA_DE_METODOS_SIMPLES`.

    Attributes:
        nome: Nome do método.
        origem: De onde o método vem (projeto, artigo ou fornecedor).
        erro_em_tres_meses: MAE em 3 meses.
        este_projeto: Se o método é deste projeto (para destacar na tabela).
        entra_no_grafico: Se entra no gráfico de barras da seção. O SARIMA
            fica de fora: seu erro (1.971,0) achataria a escala das demais.
    """

    nome: str
    origem: str
    erro_em_tres_meses: float
    este_projeto: bool
    entra_no_grafico: bool


METODOS_DA_LITERATURA_NOS_DADOS: tuple[ErroDeMetodoDaLiteratura, ...] = (
    ErroDeMetodoDaLiteratura("Mesma semana do ano passado", "régua", 217.8, False, True),
    ErroDeMetodoDaLiteratura(
        "Chronos-2, só casos", "modelo pré-treinado, Amazon, 2025", 227.2, False, True
    ),
    ErroDeMetodoDaLiteratura("HistGB, folha mínima 20", "este projeto", 243.8, True, True),
    # O ensemble é construção deste projeto (5 componentes, pesos aprendidos no
    # walk-forward local), inspirada nos ensembles de Wu et al. 2025 e de
    # Colón-González et al. 2021 — não é a reprodução do método deles.
    ErroDeMetodoDaLiteratura(
        "Ensemble com pesos aprendidos",
        "este projeto, inspirado em Wu et al. 2025",
        254.3,
        True,
        True,
    ),
    ErroDeMetodoDaLiteratura(
        "Chronos-2, casos + clima + vetor",
        "modelo pré-treinado, Amazon, 2025",
        265.2,
        False,
        True,
    ),
    ErroDeMetodoDaLiteratura("Cenário adotado", "este projeto", 278.8, True, True),
    ErroDeMetodoDaLiteratura(
        "Chronos-Bolt, só casos", "modelo pré-treinado, Amazon, 2024", 289.5, False, True
    ),
    ErroDeMetodoDaLiteratura("LASSO", "método de Shi et al. 2016, Singapura", 291.5, False, True),
    ErroDeMetodoDaLiteratura(
        "SARIMA", "clássico; Johansson et al. 2019", 1_971.0, False, False
    ),
)


@dataclasses.dataclass(frozen=True)
class ErroPercentualPublicado:
    """MAPE (erro percentual médio) publicado, em 1 semana e em 3 meses.

    Fonte: `analises/2026-09-25_comparacao_direta_literatura/README.md` e
    `metricas_do_projeto.csv`; definições conferidas em `grupo_1.md`. As
    linhas do projeto usam só semanas com 100 casos confirmados ou mais, para
    o percentual não estourar perto de zero.

    Attributes:
        modelo: Nome do modelo ou sistema.
        uso: Onde e como ele é usado.
        uma_semana: MAPE em 1 semana, já formatado ("—" quando não publicado).
        tres_meses: MAPE em 3 meses, já formatado.
        este_projeto: Se a linha é deste projeto.
    """

    modelo: str
    uso: str
    uma_semana: str
    tres_meses: str
    este_projeto: bool


MAPE_PUBLICADO: tuple[ErroPercentualPublicado, ...] = (
    ErroPercentualPublicado("LASSO, Shi et al. 2016", "operacional, Singapura", "17%", "24%", False),
    ErroPercentualPublicado("SARIMA, mesmo artigo", "régua do artigo", "—", "29%", False),
    ErroPercentualPublicado("Cenário adotado", "este projeto", "27%", "65%", True),
    ErroPercentualPublicado("HistGB, folha mínima 20", "este projeto", "49%", "58%", True),
)


@dataclasses.dataclass(frozen=True)
class ErroRelativoAoTotalPublicado:
    """Erro como fração do total de casos, em 1 mês e em 3 meses.

    Fonte: mesma origem de `MAPE_PUBLICADO`.
    """

    modelo: str
    uso: str
    um_mes: str
    tres_meses: str
    este_projeto: bool


ERRO_RELATIVO_AO_TOTAL_PUBLICADO: tuple[ErroRelativoAoTotalPublicado, ...] = (
    ErroRelativoAoTotalPublicado(
        "Ensemble, Wu et al. 2025",
        "operacional, 5 países, mensal por estado",
        "38,5%",
        "62,7%",
        False,
    ),
    ErroRelativoAoTotalPublicado("Cenário adotado", "este projeto", "53%", "65%", True),
    ErroRelativoAoTotalPublicado("HistGB, folha mínima 20", "este projeto", "48%", "57%", True),
)


@dataclasses.dataclass(frozen=True)
class R2Publicado:
    """R² publicado, no horizonte que cada artigo declara.

    Fonte: mesma origem de `MAPE_PUBLICADO`.

    Attributes:
        modelo: Nome do modelo ou artigo.
        onde: Cidade e período dos dados.
        um_mes: R² em 1 mês (ou o horizonte mais próximo declarado), já
            formatado, com a ressalva entre parênteses quando o horizonte
            difere de 1 mês.
        tres_meses: R² em 3 meses, já formatado. "—" quando o artigo não
            declara esse horizonte.
        este_projeto: Se a linha é deste projeto.
    """

    modelo: str
    onde: str
    um_mes: str
    tres_meses: str
    este_projeto: bool


R2_PUBLICADO: tuple[R2Publicado, ...] = (
    R2Publicado("CatBoost, Aleixo et al. 2022", "Rio, distrito e mês", "0,47", "0,38", False),
    R2Publicado(
        "CatBoost, 27 capitais, 2026",
        "Porto Alegre, 1999-2021",
        "−0,21 (até 4 semanas)",
        "—",
        False,
    ),
    R2Publicado(
        "da Silva et al. 2026",
        "Porto Alegre",
        "0,46 (escala log, horizonte não declarado)",
        "—",
        False,
    ),
    R2Publicado("Cenário adotado", "Porto Alegre", "0,63", "0,44", True),
    R2Publicado("HistGB, folha mínima 20", "Porto Alegre", "0,72", "0,56", True),
)


@dataclasses.dataclass(frozen=True)
class VantagemSobreARegua:
    """Vantagem percentual de um sistema sobre "a mesma época do ano anterior".

    Positivo é o sistema errar MENOS que essa régua sazonal; negativo é errar
    mais. Fonte: `analises/2026-09-25_comparacao_direta_literatura/README.md`.

    Attributes:
        sistema: Nome do sistema, modelo ou artigo.
        uso: Onde e como ele é usado.
        rotulo_curto_prazo: Horizonte do valor de curto prazo, em texto.
        valor_curto_prazo: A vantagem percentual nesse horizonte.
        rotulo_horizonte_longo: Horizonte mais longo declarado, em texto.
        valor_horizonte_longo: A vantagem percentual nesse horizonte, ou
            `None` quando o artigo só relata que ela desaparece, sem número
            (o caso do Superensemble em 4-6 meses).
        este_projeto: Se a linha é deste projeto.
    """

    sistema: str
    uso: str
    rotulo_curto_prazo: str
    valor_curto_prazo: float
    rotulo_horizonte_longo: str
    valor_horizonte_longo: float | None
    este_projeto: bool


VANTAGEM_SOBRE_A_REGUA: tuple[VantagemSobreARegua, ...] = (
    VantagemSobreARegua(
        "D-MOSS",
        "operacional, Ministério da Saúde do Vietnã, desde 2019",
        "1 mês",
        15.0,
        "6 meses",
        27.0,
        False,
    ),
    VantagemSobreARegua(
        "Superensemble, Colón-González et al. 2021",
        "Vietnã",
        "1 a 3 meses",
        16.0,
        "4 a 6 meses",
        None,
        False,
    ),
    VantagemSobreARegua(
        "HistGB, folha mínima 20", "este projeto", "1 mês", 13.0, "3 meses", -7.0, True
    ),
    VantagemSobreARegua(
        "Cenário adotado", "este projeto", "1 mês", 1.0, "3 meses", -21.0, True
    ),
)


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


# ---------------------------------------------------------------------------
# NÚMEROS DA REVISÃO DE 26/09/2026
#
# Tudo abaixo entrou depois da bateria de 25 e 26/09/2026 e alimenta APENAS a
# página "Seminário — revisão de 26/09". A página original do seminário não usa
# nada daqui, de propósito: ela continua contando a versão de 23/09/2026.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ComparacaoDeAlarmeContraRegua:
    """O índice de Youden do alarme, por regra, em um horizonte.

    Youden = sensibilidade + especificidade − 1. Quanto mais perto de 1, melhor.

    Fonte: `analises/2026-09-25_alarme_contra_canal_endemico/saidas/
    metricas_por_regra.csv`, evento "semana com mais de 100 casos", avaliação
    de 2024 em diante, 102 semanas.

    Attributes:
        regra: Nome da regra ou do modelo.
        e_modelo: True quando a linha é um modelo, e não uma regra simples.
        youden_um_mes: Índice de Youden em 1 mês (4 semanas).
        youden_tres_meses: Índice de Youden em 3 meses (12 semanas).
    """

    regra: str
    e_modelo: bool
    youden_um_mes: float
    youden_tres_meses: float


ALARME_CONTRA_REGUAS: tuple[ComparacaoDeAlarmeContraRegua, ...] = (
    ComparacaoDeAlarmeContraRegua("Cenário adotado", True, 0.94, 0.66),
    ComparacaoDeAlarmeContraRegua("HistGB, folha mínima 20", True, 0.90, 0.78),
    ComparacaoDeAlarmeContraRegua("Mesma semana do ano passado", False, 0.84, 0.80),
    ComparacaoDeAlarmeContraRegua("Hoje já passou do limiar", False, 0.68, 0.11),
)


@dataclasses.dataclass(frozen=True)
class TesteDeAlarmeComHolm:
    """Um teste de McNemar pareado do alarme, já com correção de Holm.

    Fonte: `analises/2026-09-25_alarme_contra_canal_endemico/saidas/
    mcnemar_holm.csv`, evento de 100 casos, família de 16 testes.

    Attributes:
        horizonte: Como o horizonte é dito em texto.
        regra_base: Contra qual regra o cenário adotado foi comparado.
        discordantes: Quantas semanas as duas regras classificaram diferente.
            Só elas entram no teste de McNemar.
        divisao: Como os discordantes se dividem, a favor e contra o modelo.
        p_holm: O valor-p depois da correção de Holm.
        vence: True quando o resultado é significativo a 5%.
    """

    horizonte: str
    regra_base: str
    discordantes: int
    divisao: str
    p_holm: float
    vence: bool


# 🔴 É o quadro mais importante da revisão: ele impede afirmar que o alarme de
# 1 mês vence as regras simples.
TESTES_DO_ALARME: tuple[TesteDeAlarmeComHolm, ...] = (
    TesteDeAlarmeComHolm("1 mês", "Hoje já passou", 15, "13 a 2", 0.103, False),
    TesteDeAlarmeComHolm("1 mês", "Ano passado", 7, "5 a 2", 1.000, False),
    TesteDeAlarmeComHolm("3 meses", "Hoje já passou", 37, "31 a 6", 0.00062, True),
    TesteDeAlarmeComHolm("3 meses", "Ano passado", 16, "4 a 12", 0.845, False),
)


@dataclasses.dataclass(frozen=True)
class CalibracaoPorFaixa:
    """A cobertura dos intervalos de previsão, por nível de casos reais.

    Se as faixas fossem honestas, a cobertura observada seria igual à nominal:
    50% e 90%.

    Fonte: `analises/2026-09-26_calibracao_por_faixa/saidas/
    cobertura_por_faixa.csv`, cenário adotado.

    Attributes:
        faixa: O nome da faixa de casos reais.
        semanas: Quantas semanas caíram nessa faixa.
        cobertura_50: Fração das semanas dentro do intervalo de 50%.
        cobertura_90: Fração das semanas dentro do intervalo de 90%.
    """

    faixa: str
    semanas: int
    cobertura_50: float
    cobertura_90: float


CALIBRACAO_POR_FAIXA: tuple[CalibracaoPorFaixa, ...] = (
    CalibracaoPorFaixa("Calmaria (0 a 20 casos)", 814, 0.592, 0.905),
    CalibracaoPorFaixa("Subida (21 a 140)", 110, 0.182, 0.636),
    CalibracaoPorFaixa("Mobilização (141 a 421)", 72, 0.278, 0.472),
    CalibracaoPorFaixa("Alerta ou mais (acima de 421)", 163, 0.080, 0.178),
)


@dataclasses.dataclass(frozen=True)
class EscoreDeIntervaloPonderado:
    """O escore de intervalo ponderado (WIS), por horizonte.

    O WIS avalia a distribuição prevista inteira, e não um número só. É a
    métrica oficial dos sprints brasileiros de previsão de dengue. Menor é
    melhor.

    Fonte: `analises/2026-09-26_wis_na_tabela_restaurada/`, recorte de 2024 a
    2025, tabela oficial.

    Attributes:
        horizonte: Como o horizonte é dito em texto.
        adotado: WIS do cenário adotado.
        folha20: WIS do HistGB de folha mínima 20.
        regua_climatologica: WIS da régua climatológica.
    """

    horizonte: str
    adotado: float
    folha20: float
    regua_climatologica: float


ESCORE_DE_INTERVALO: tuple[EscoreDeIntervaloPonderado, ...] = (
    EscoreDeIntervaloPonderado("1 semana", 101.9, 121.3, 292.7),
    EscoreDeIntervaloPonderado("1 mês", 215.4, 199.0, 313.5),
    EscoreDeIntervaloPonderado("2 meses", 288.6, 259.0, 322.2),
    EscoreDeIntervaloPonderado("3 meses", 300.7, 278.6, 324.2),
)


@dataclasses.dataclass(frozen=True)
class EstagioDoPlanoMunicipal:
    """Um estágio de resposta do Plano Municipal de Contingência de 2026.

    Fonte: Plano Municipal de Contingência de Arboviroses 2026 da Secretaria
    Municipal de Saúde de Porto Alegre, Quadro 1, página 15. Conversão para
    casos por semana na população de 1.404.269.

    ⚠️ SIMPLIFICAÇÃO DECLARADA: no plano, o corte numérico nunca aparece
    sozinho — vem sempre ligado por E ao Limite de Alerta ou ao Limite Superior
    Endêmico, que são curvas do Rio Grande do Sul sobre casos prováveis. Mais
    óbito confirmado e sorotipo novo. Usamos só a metade fixa do critério.

    Attributes:
        estagio: O nome do estágio.
        incidencia: O corte de incidência declarado no plano.
        casos_por_semana: O mesmo corte em casos por semana.
        semanas_acima: Quantas das 121 semanas avaliadas ficaram acima dele.
    """

    estagio: str
    incidencia: str
    casos_por_semana: int
    semanas_acima: int


ESTAGIOS_DO_PLANO: tuple[EstagioDoPlanoMunicipal, ...] = (
    EstagioDoPlanoMunicipal("Normalidade", "abaixo de 10", 140, 83),
    EstagioDoPlanoMunicipal("Mobilização", "acima de 10", 140, 38),
    EstagioDoPlanoMunicipal("Alerta", "acima de 30", 421, 28),
    EstagioDoPlanoMunicipal("Epidemia", "acima de 50", 702, 23),
)


@dataclasses.dataclass(frozen=True)
class AbordagemTestada:
    """Uma família de abordagens testada, com o veredito.

    Sustenta a afirmação de que o limite não é de configuração nem de código.

    Attributes:
        abordagem: O que foi testado.
        quantidade: Quantas variantes, em texto.
        veredito: O resultado, em poucas palavras.
    """

    abordagem: str
    quantidade: str
    veredito: str


ABORDAGENS_TESTADAS: tuple[AbordagemTestada, ...] = (
    AbordagemTestada("Busca de hiperparâmetros", "120 configurações", "nenhuma passa"),
    AbordagemTestada("Algoritmos no grid", "9 algoritmos", "nenhum bate a régua em 3 meses"),
    AbordagemTestada("Formulações do alvo", "6 variantes", "nenhuma passa; duas explodem"),
    AbordagemTestada("Modelos de fundação", "2 modelos", "227,2 e 289,5 contra 217,8 da régua"),
    AbordagemTestada("Modelos estatísticos clássicos", "SARIMA e LASSO", "explodem em epidemia"),
    AbordagemTestada("Transformações de escala", "raiz e logaritmo", "pioram a calibração"),
    AbordagemTestada("Correção conformal", "1 variante", "alarmes falsos de 15 para 124"),
)


# Contagem de blocos contíguos de semanas de surto, por limiar, na avaliação de
# 121 semanas desde 2024. Fonte: `analises/2026-09-26_calibracao_por_faixa/` e
# a medição de 26/09/2026. É o número que mais limita o que pode ser afirmado.
BLOCOS_DE_SURTO = 2
SEMANAS_ACIMA_DE_100 = 39
MAIOR_BLOCO_EM_SEMANAS = 20

# Captura do pico em 3 meses: razão entre a média prevista e a média real nas
# semanas de surto. Fonte: `analises/2026-09-13_metrica_de_alarme/`.
CAPTURA_DO_PICO_TRES_MESES = 0.388
SEMANA_DE_PICO_REAL = 917
SEMANA_DE_PICO_PREVISTA = 356

# Erro mediano nas semanas acima de 421 casos, contra o valor real mediano.
# Fonte: `analises/2026-09-26_calibracao_por_faixa/`.
ERRO_MEDIANO_EM_EPIDEMIA = 539
REAL_MEDIANO_EM_EPIDEMIA = 917
