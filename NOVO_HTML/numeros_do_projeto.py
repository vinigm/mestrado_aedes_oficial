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

    Medido rodando o próprio pipeline da folha mínima 5 em 23/09/2026:
    `fontes.carregar_tabela_final` seguido de
    `features.construir_features_temporais` e
    `selecao_features.separar_grupos_de_features`.

    Attributes:
        derivados: Atributos criados em tempo de execução.
        lags_por_coluna: Quantas defasagens cada coluna elegível recebe.
        colunas_com_lag: Quantas colunas recebem defasagem.
        atributos_no_modelo: Quantos chegam ao modelo de folha mínima 5.
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
# com a configuração de folha mínima 5. Só o topo aparece no site; são 42
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
    """Uma coluna que chega ao modelo de folha mínima 5.

    Attributes:
        nome: Nome da coluna.
        grupo: Núcleo, Clima ou Vetor.
        descricao: O que ela carrega, em uma linha.
    """

    nome: str
    grupo: str
    descricao: str


# As 20 colunas que a folha mínima 5 entrega ao modelo, na ordem em que o
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
    ErroPorHorizonteEMetodo("Folha mínima 5", 98.0, 219.7, 272.6, 278.8),
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
    ErroDeMetodoDaLiteratura("Folha mínima 5", "este projeto", 278.8, True, True),
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
    ErroPercentualPublicado("Folha mínima 5", "este projeto", "27%", "65%", True),
    ErroPercentualPublicado("HistGB, folha mínima 20", "este projeto", "49%", "58%", True),
    # O composto herda o valor da folha que manda em cada horizonte: a 5 em
    # 1 semana, a 20 em 3 meses. Recalculado das previsões em 27/09/2026.
    ErroPercentualPublicado("Modelo composto", "este projeto", "27%", "58%", True),
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
    ErroRelativoAoTotalPublicado("Folha mínima 5", "este projeto", "53%", "65%", True),
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
    R2Publicado("Folha mínima 5", "Porto Alegre", "0,63", "0,44", True),
    R2Publicado("HistGB, folha mínima 20", "Porto Alegre", "0,72", "0,56", True),
    # Em 1 mês e em 3 meses o composto usa a folha 20, então repete os
    # números dela. Confere com `painel_do_composto.csv`: 0,717 e 0,558.
    R2Publicado("Modelo composto", "Porto Alegre", "0,72", "0,56", True),
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
        "Folha mínima 5", "este projeto", "1 mês", 1.0, "3 meses", -21.0, True
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
# MODELO COMPOSTO — medido em 26/09/2026
#
# ⚠️ DESCRITIVO E POSTERIOR AOS FATOS. O ponto de corte entre as duas
# configuracoes foi escolhido olhando o periodo de avaliacao, que e o mesmo que
# julga. Serve de ilustracao do que um composto renderia, NAO de configuracao
# adotavel. Ver `analises/2026-09-26_modelo_composto/README.md`.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class DesempenhoDeUmBraco:
    """As tres metricas do painel para um braco, num horizonte.

    Fonte: `analises/2026-09-26_modelo_composto/saidas/painel_do_composto.csv`,
    avaliacao de 2024 em diante, 102 semanas por horizonte.

    Attributes:
        braco: Nome do modelo ou da regua.
        semanas: Quantas semanas a frente a previsao olha.
        rotulo: Como o horizonte e dito em texto.
        erro_medio_absoluto: MAE em casos confirmados por semana.
        r2: Fracao da variacao dos casos que o braco explica.
        captura_do_pico: Fracao da altura do pico que o braco alcanca.
    """

    braco: str
    semanas: int
    rotulo: str
    erro_medio_absoluto: float
    r2: float
    captura_do_pico: float


# ⚠️ "Cenário adotado" saiu de todo o material em 27/09/2026, por decisão do
# Vinicius: o nome sugeria uma configuração em uso na Prefeitura, e isso não
# existe. Só há três modelos, e eles se chamam pelo hiperparâmetro que os
# separa: folha mínima 5, folha mínima 20 e o composto dos dois.
NOME_DO_ADOTADO = "Folha mínima 5"
NOME_DA_FOLHA_20 = "Folha 20, com vetor"
NOME_DO_COMPOSTO = "Composto"
NOME_DA_REGUA = "Régua sazonal"

PAINEL_DO_COMPOSTO: tuple[DesempenhoDeUmBraco, ...] = (
    DesempenhoDeUmBraco(NOME_DO_ADOTADO, 1, "1 semana", 98.0, 0.898, 0.886),
    DesempenhoDeUmBraco(NOME_DO_ADOTADO, 4, "1 mês", 219.7, 0.628, 0.702),
    DesempenhoDeUmBraco(NOME_DO_ADOTADO, 8, "2 meses", 272.6, 0.450, 0.417),
    # 278,7 e o valor do painel publicado; o recalculo de 26/09 da 278,82, dentro
    # da tolerancia de 0,2 da trava. O deck usa 278,7 em toda parte para nao
    # mostrar dois arredondamentos do mesmo numero em slides vizinhos.
    DesempenhoDeUmBraco(NOME_DO_ADOTADO, 12, "3 meses", 278.7, 0.437, 0.388),
    DesempenhoDeUmBraco(NOME_DA_FOLHA_20, 1, "1 semana", 133.6, 0.834, 0.938),
    DesempenhoDeUmBraco(NOME_DA_FOLHA_20, 4, "1 mês", 199.6, 0.717, 0.706),
    DesempenhoDeUmBraco(NOME_DA_FOLHA_20, 8, "2 meses", 223.2, 0.576, 0.510),
    DesempenhoDeUmBraco(NOME_DA_FOLHA_20, 12, "3 meses", 243.8, 0.558, 0.504),
    DesempenhoDeUmBraco(NOME_DO_COMPOSTO, 1, "1 semana", 98.0, 0.898, 0.886),
    DesempenhoDeUmBraco(NOME_DO_COMPOSTO, 4, "1 mês", 199.6, 0.717, 0.706),
    DesempenhoDeUmBraco(NOME_DO_COMPOSTO, 8, "2 meses", 223.2, 0.576, 0.510),
    DesempenhoDeUmBraco(NOME_DO_COMPOSTO, 12, "3 meses", 243.8, 0.558, 0.504),
    DesempenhoDeUmBraco(NOME_DA_REGUA, 1, "1 semana", 202.1, 0.633, 0.567),
    DesempenhoDeUmBraco(NOME_DA_REGUA, 4, "1 mês", 213.2, 0.623, 0.569),
    DesempenhoDeUmBraco(NOME_DA_REGUA, 8, "2 meses", 216.2, 0.618, 0.575),
    DesempenhoDeUmBraco(NOME_DA_REGUA, 12, "3 meses", 217.8, 0.616, 0.574),
)

# O corte do composto: ate 3 semanas usa a folha 5; de 4 em diante, a folha 20.
ULTIMO_HORIZONTE_DA_FOLHA_5 = 3

# Ganho do vetor DENTRO da folha 20, por horizonte, com o p ja corrigido por
# Holm. Fonte: `analises/2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/
# saidas/comparacoes.csv`.
GANHO_DO_VETOR_NA_FOLHA_20: tuple[tuple[str, float, float], ...] = (
    ("1 semana", -15.7, 0.4654),
    ("1 mês", 4.1, 0.8295),
    ("2 meses", 8.1, 0.0056),
    ("3 meses", 12.3, 0.0151),
)


# Os 12 horizontes do composto e da regua, para os graficos do slide.
#
# ⚠️ POR QUE 12 E NAO 4: com so os quatro pontos do painel (1, 4, 8, 12) o
# grafico liga 4 a 8 por uma reta, e essa reta cruza a da regua por volta de
# 6,6 — enquanto o cruzamento REAL, medido semana a semana, e em 5. A reta
# mentia sobre o que acontece no vao. Com os 12 pontos, o desenho mostra o
# ziguezague que existe de fato e o marco cai onde as linhas se cruzam.
#
# Fonte: `analises/2026-09-26_modelo_composto/saidas/painel_12_horizontes.csv`.
# Cada item e (semanas, erro absoluto medio, R2, captura do pico).
COMPOSTO_NOS_12_HORIZONTES: tuple[tuple[int, float, float, float], ...] = (
    (1, 98.0, 0.898, 0.886),
    (2, 162.0, 0.746, 0.758),
    (3, 185.2, 0.698, 0.717),
    (4, 199.6, 0.717, 0.706),
    (5, 225.4, 0.636, 0.606),
    (6, 221.5, 0.609, 0.571),
    (7, 232.4, 0.531, 0.508),
    (8, 223.2, 0.576, 0.510),
    (9, 234.8, 0.545, 0.484),
    (10, 236.8, 0.559, 0.499),
    (11, 241.6, 0.570, 0.479),
    (12, 243.8, 0.558, 0.504),
)

REGUA_NOS_12_HORIZONTES: tuple[tuple[int, float, float, float], ...] = (
    (1, 202.1, 0.633, 0.567),
    (2, 202.4, 0.634, 0.574),
    (3, 211.8, 0.624, 0.566),
    (4, 213.2, 0.623, 0.569),
    (5, 213.6, 0.622, 0.573),
    (6, 213.8, 0.621, 0.575),
    (7, 214.1, 0.620, 0.577),
    (8, 216.2, 0.618, 0.575),
    (9, 217.3, 0.617, 0.574),
    (10, 217.4, 0.616, 0.574),
    (11, 217.6, 0.616, 0.574),
    (12, 217.8, 0.616, 0.574),
)

# Posicao de cada metrica dentro das tuplas acima.
POSICAO_DO_MAE = 1
POSICAO_DO_R2 = 2
POSICAO_DA_CAPTURA = 3


# ---------------------------------------------------------------------------
# O ALARME DE SURTO DO MODELO COMPOSTO — medido em 26/09/2026
#
# Evento: semana acima do piso do estagio ALERTA do Plano Municipal de
# Contingencia de Arboviroses 2026 da SMS-POA — 421 casos por semana, que e
# a incidencia de 30 por 100 mil na populacao de 1.404.269. Trocado em
# 26/09/2026 por decisao do Vinicius: os 100 casos eram convencao do projeto,
# sem base oficial.
#
# ⚠️ SIMPLIFICACAO DECLARADA: no plano o corte numerico nunca aparece sozinho.
# Vem ligado por E a limiares estaduais sobre casos provaveis, mais obito e
# sorotipo novo. Usamos so a metade fixa do criterio.
#
# Avaliacao de 2024 em diante, 102 semanas, das quais 28 (27%) passaram de 421.
#
# 🔴 ATENCAO AOS ALARMES FALSOS POR ANO. A medicao de 13/09/2026 dividiu por
# 3 ANOS CIVIS (2024, 2025, 2026), mas a avaliacao cobre 1,96 ano de tempo
# real: 2024 entra com 45 semanas e 2026 com 5. A taxa publicada esta
# SUBESTIMADA em cerca de 53%. Os valores abaixo usam a conta correta.
# Fonte: `analises/2026-09-26_modelo_composto/saidas/alarme_do_composto.csv`.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class AlarmeDeUmBraco:
    """O alarme de surto de um braco, num horizonte.

    Attributes:
        braco: Nome do modelo ou da regua.
        rotulo: Como o horizonte e dito em texto.
        sensibilidade: Fracao das semanas de surto que o alarme sinalizou.
        precisao: Fracao dos alarmes disparados que eram surto de verdade.
        falsos_por_ano: Alarmes falsos por ano de tempo real.
        surtos_perdidos: Quantas semanas de surto passaram sem alarme.
    """

    braco: str
    rotulo: str
    sensibilidade: float
    precisao: float
    falsos_por_ano: float
    surtos_perdidos: int


ALARME_DO_COMPOSTO: tuple[AlarmeDeUmBraco, ...] = (
    AlarmeDeUmBraco(NOME_DO_COMPOSTO, "1 semana", 0.958, 0.958, 0.5, 1),
    AlarmeDeUmBraco(NOME_DO_COMPOSTO, "1 mês", 1.000, 0.818, 3.1, 0),
    AlarmeDeUmBraco(NOME_DO_COMPOSTO, "2 meses", 0.857, 1.000, 0.0, 4),
    AlarmeDeUmBraco(NOME_DO_COMPOSTO, "3 meses", 0.500, 0.875, 1.0, 14),
    AlarmeDeUmBraco(NOME_DO_ADOTADO, "1 semana", 0.958, 0.958, 0.5, 1),
    AlarmeDeUmBraco(NOME_DO_ADOTADO, "1 mês", 1.000, 0.900, 1.5, 0),
    AlarmeDeUmBraco(NOME_DO_ADOTADO, "2 meses", 0.679, 0.950, 0.5, 9),
    AlarmeDeUmBraco(NOME_DO_ADOTADO, "3 meses", 0.393, 1.000, 0.0, 17),
    AlarmeDeUmBraco(NOME_DA_REGUA, "1 semana", 0.708, 0.944, 0.5, 7),
    AlarmeDeUmBraco(NOME_DA_REGUA, "1 mês", 0.741, 0.952, 0.5, 7),
    AlarmeDeUmBraco(NOME_DA_REGUA, "2 meses", 0.750, 0.955, 0.5, 7),
    AlarmeDeUmBraco(NOME_DA_REGUA, "3 meses", 0.750, 0.955, 0.5, 7),
)

# Quantas semanas de surto existem em cada horizonte. Varia porque o numero de
# semanas com alvo conhecido cai conforme o horizonte cresce.
SURTOS_POR_HORIZONTE = {"1 semana": 24, "1 mês": 27, "2 meses": 28, "3 meses": 28}

# A base, no limiar oficial de Alerta.
LIMIAR_DO_ALARME = 421
NOME_DO_ESTAGIO_DO_ALARME = "Alerta"
SEMANAS_AVALIADAS_NO_ALARME = 102
SEMANAS_DE_SURTO_NO_ALARME = 28
# ---------------------------------------------------------------------------
# OS ESTAGIOS DO PLANO MUNICIPAL DE CONTINGENCIA DE ARBOVIROSES 2026
#
# Fonte: Secretaria Municipal de Saude de Porto Alegre, dezembro de 2025.
# Quadro 1, pagina 15. Imagem do quadro extraida por
# `analises/2026-09-25_limiar_oficial_de_surto/extrair_quadro_1.py`.
#
# 🔴 OS NUMEROS EM CASOS POR SEMANA NAO ESTAO NO PDF. O plano declara taxas de
# incidencia (10,0 · 30,0 · 50,0) e a conversao para casos e nossa, usando a
# populacao abaixo. Alem disso, o plano NAO declara a unidade da taxa: "por 100
# mil habitantes" e a convencao nacional, e e inferencia. Se a unidade for
# outra, todos os limiares do projeto mudam.
#
# ⚠️ SIMPLIFICACAO DECLARADA: no Quadro 1 o corte numerico nunca aparece
# sozinho — vem ligado por E a limiares estaduais sobre casos provaveis (LA e
# LSE), mais obito confirmado e sorotipo novo. Usamos so a metade fixa.
# ---------------------------------------------------------------------------

POPULACAO_DE_PORTO_ALEGRE = 1404269


@dataclasses.dataclass(frozen=True)
class EstagioDoPlano:
    """Um estagio de resposta do plano municipal.

    Attributes:
        estagio: O nome do estagio, como o plano escreve.
        incidencia: O corte de incidencia declarado no plano.
        casos_por_semana: O mesmo corte convertido para a populacao de POA.
    """

    estagio: str
    incidencia: str
    casos_por_semana: int


ESTAGIOS_DO_PLANO: tuple[EstagioDoPlano, ...] = (
    EstagioDoPlano("Normalidade", "abaixo de 10,0", 140),
    EstagioDoPlano("Mobilização", "acima de 10,0", 140),
    EstagioDoPlano("Alerta", "acima de 30,0", 421),
    EstagioDoPlano("Epidemia", "acima de 50,0", 702),
)


# As metricas do alarme nos 12 horizontes, para os graficos do slide. Evento:
# semana acima de 421 casos, o piso do estagio Alerta.
# Fonte: `analises/2026-09-26_modelo_composto/saidas/alarme_12_horizontes.csv`.
# Cada item e (semanas, sensibilidade, precisao, alarmes falsos por ano).
ALARME_DO_COMPOSTO_NOS_12: tuple[tuple[int, float, float, float], ...] = (
    (1, 0.958, 0.958, 0.51),
    (2, 0.960, 1.000, 0.00),
    (3, 1.000, 0.929, 1.02),
    (4, 1.000, 0.818, 3.06),
    (5, 0.893, 0.833, 2.55),
    (6, 0.786, 0.917, 1.02),
    (7, 0.857, 0.923, 1.02),
    (8, 0.857, 1.000, 0.00),
    (9, 0.786, 0.957, 0.51),
    (10, 0.750, 0.955, 0.51),
    (11, 0.607, 0.944, 0.51),
    (12, 0.500, 0.875, 1.02),
)

ALARME_DA_REGUA_NOS_12: tuple[tuple[int, float, float, float], ...] = (
    (1, 0.708, 0.944, 0.51),
    (2, 0.720, 0.947, 0.51),
    (3, 0.731, 0.950, 0.51),
    (4, 0.741, 0.952, 0.51),
    (5, 0.750, 0.955, 0.51),
    (6, 0.750, 0.955, 0.51),
    (7, 0.750, 0.955, 0.51),
    (8, 0.750, 0.955, 0.51),
    (9, 0.750, 0.955, 0.51),
    (10, 0.750, 0.955, 0.51),
    (11, 0.750, 0.955, 0.51),
    (12, 0.750, 0.955, 0.51),
)

# Posicao de cada metrica dentro das tuplas acima.
POSICAO_DA_SENSIBILIDADE = 1
POSICAO_DA_PRECISAO = 2
POSICAO_DOS_FALSOS = 3


# ─────────────────────────────────────────────────────────────────────────────
# O VETOR NAS DUAS CONFIGURAÇÕES — duas medidas que não podem ser confundidas
# ─────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class VetorNoHorizonte:
    """O que o mosquito rende e o quanto o modelo se apoia nele, num horizonte.

    São DUAS medidas diferentes, e confundi-las é o erro clássico:

      - **ganho** vem da ABLAÇÃO: treina um modelo do zero SEM as colunas do
        mosquito e compara com o que tem. Positivo significa que o modelo com
        mosquito erra menos. Responde "dá para viver sem?".
      - **apoio** vem da PERMUTAÇÃO: pega o modelo JÁ TREINADO e embaralha as
        colunas do mosquito na hora de prever. Diz quanto o erro sobe quando o
        modelo perde o acesso ao mosquito. Responde "ele está usando?".

    ⚠️ As duas podem discordar, e discordam na folha 5: o modelo se apoia no
    mosquito, mas um modelo treinado sem ele reaprende pelo histórico de casos,
    que é correlacionado. Por isso "indispensável" não se sustenta.

    ⚠️ **As famílias de Holm são diferentes.** O p da folha 5 foi corrigido numa
    família de **12** comparações (3 algoritmos × 4 horizontes, bloco 5); o da
    folha 20, numa de **4** (bloco 7). Família maior penaliza mais, então os
    dois p não são comparáveis um a um.

    Fontes: `analises/2026-09-23_bateria_noturna/bloco_5_algoritmos/` e
    `bloco_7_vetor_com_folha_20/` para o ganho;
    `analises/2026-09-26_importancia_na_folha_20/` para o apoio.

    Attributes:
        rotulo: Como o horizonte é dito em texto.
        ganho_na_folha_5: Queda percentual do erro com o vetor, folha 5.
        p_holm_na_folha_5: p de Holm do ganho acima, família de 12.
        ganho_na_folha_20: Queda percentual do erro com o vetor, folha 20.
        p_holm_na_folha_20: p de Holm do ganho acima, família de 4.
        apoio_na_folha_5: Quanto o erro sobe sem o mosquito, folha 5.
        apoio_na_folha_20: Quanto o erro sobe sem o mosquito, folha 20.
        erro_na_folha_5: MAE em casos por semana, folha 5. Existe para que o
            ganho relativo não seja lido sobre uma base escondida.
        erro_na_folha_20: MAE em casos por semana, folha 20.
    """

    rotulo: str
    ganho_na_folha_5: float
    p_holm_na_folha_5: float
    ganho_na_folha_20: float
    p_holm_na_folha_20: float
    apoio_na_folha_5: float
    apoio_na_folha_20: float
    erro_na_folha_5: float
    erro_na_folha_20: float


O_VETOR_NAS_DUAS_CONFIGURACOES = (
    VetorNoHorizonte(
        rotulo="1 semana",
        ganho_na_folha_5=-6.53,
        p_holm_na_folha_5=1.0,
        ganho_na_folha_20=-15.70,
        p_holm_na_folha_20=0.4654,
        apoio_na_folha_5=19.96,
        apoio_na_folha_20=23.56,
        erro_na_folha_5=97.99,
        erro_na_folha_20=133.63,
    ),
    VetorNoHorizonte(
        rotulo="1 mês",
        ganho_na_folha_5=-0.13,
        p_holm_na_folha_5=1.0,
        ganho_na_folha_20=4.15,
        p_holm_na_folha_20=0.8295,
        apoio_na_folha_5=62.22,
        apoio_na_folha_20=108.29,
        erro_na_folha_5=219.67,
        erro_na_folha_20=199.64,
    ),
    VetorNoHorizonte(
        rotulo="2 meses",
        ganho_na_folha_5=-7.74,
        p_holm_na_folha_5=1.0,
        ganho_na_folha_20=8.07,
        p_holm_na_folha_20=0.0056,
        apoio_na_folha_5=52.78,
        apoio_na_folha_20=98.67,
        erro_na_folha_5=272.63,
        erro_na_folha_20=223.18,
    ),
    VetorNoHorizonte(
        rotulo="3 meses",
        ganho_na_folha_5=2.17,
        p_holm_na_folha_5=1.0,
        ganho_na_folha_20=12.32,
        p_holm_na_folha_20=0.0151,
        apoio_na_folha_5=38.62,
        apoio_na_folha_20=51.07,
        erro_na_folha_5=278.82,
        erro_na_folha_20=243.76,
    ),
)

# As duas medidas nos 12 horizontes, para as curvas do slide. Cada tupla é
# (horizonte, folha 5, folha 20). Só os horizontes 1, 4, 8 e 12 têm p; os
# demais são descritivos, e é por isso que o p vive na tabela e não na curva.
GANHO_DO_VETOR_NOS_12 = (
    (1, -6.53, -15.70),
    (2, -4.84, -24.63),
    (3, 6.37, -1.81),
    (4, -0.13, 4.15),
    (5, 3.52, -2.02),
    (6, -10.15, 1.75),
    (7, -5.64, 7.03),
    (8, -7.74, 8.07),
    (9, -9.36, 6.17),
    (10, -3.88, 10.28),
    (11, -10.74, 7.49),
    (12, 2.17, 12.32),
)

APOIO_NO_VETOR_NOS_12 = (
    (1, 19.96, 23.56),
    (2, 40.39, 54.37),
    (3, 70.55, 93.59),
    (4, 62.22, 108.29),
    (5, 73.07, 89.73),
    (6, 56.95, 90.69),
    (7, 60.83, 91.74),
    (8, 52.78, 98.67),
    (9, 48.74, 86.99),
    (10, 54.74, 82.28),
    (11, 45.66, 68.36),
    (12, 38.62, 51.07),
)

# Posição de cada configuração dentro das tuplas de 12 horizontes acima.
POSICAO_DA_FOLHA_5 = 1
POSICAO_DA_FOLHA_20 = 2


# ─────────────────────────────────────────────────────────────────────────────
# ONDE O MODELO AINDA FALHA — a calibração por faixa de nível
# ─────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class DuasPerguntasNumaFaixa:
    """O que o modelo acerta numa faixa de nível, nas DUAS perguntas que ele responde.

    São perguntas diferentes, e o modelo vai muito melhor numa que na outra:

      - **"quantos casos?"** — a previsão do número, com a faixa de incerteza;
      - **"vai passar de 421?"** — a decisão binária do alarme.

    🔴 Mostrar só a primeira faz a metodologia parecer pior do que é: nas
    semanas de Alerta a faixa de 90% acerta 14,3%, mas o alarme pega 24 dos 28
    Alertas. O modelo **não sabe dizer quanto, e sabe dizer que vem**.

    ⚠️ Tudo aqui é o **modelo composto em 2 meses** (h=8), na janela de
    avaliação de 102 semanas. O horizonte é o mesmo nas duas perguntas de
    propósito: as coberturas publicadas antes juntavam 4 horizontes e não eram
    comparáveis com as métricas de alarme, que são por horizonte.

    Fonte: coberturas e erro remedidos em 27/09/2026 de
    `analises/2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv`
    (braço `histgb_folha20`, que é o composto em h=8); alarme de
    `analises/2026-09-26_modelo_composto/saidas/alarme_do_composto.csv`.

    Attributes:
        rotulo: Como a faixa é dita em texto.
        semanas: Quantas semanas da avaliação caem nesta faixa.
        cobertura_de_90: Fração das vezes em que o intervalo de 90% conteve o
            valor real. Deveria dar perto de 0,90.
        cobertura_de_50: Idem para o intervalo de 50%. Deveria dar perto de 0,50.
        erro_mediano: Erro absoluto mediano da previsão central, em casos.
        nivel_mediano: Número real mediano de casos na faixa, para dar escala.
    """

    rotulo: str
    semanas: int
    cobertura_de_90: float
    cobertura_de_50: float
    erro_mediano: float
    nivel_mediano: float


CALIBRACAO_EM_DOIS_MESES = (
    DuasPerguntasNumaFaixa(
        rotulo="Calmaria — até 20 casos",
        semanas=54,
        cobertura_de_90=0.907,
        cobertura_de_50=0.315,
        erro_mediano=4.8,
        nivel_mediano=4.0,
    ),
    DuasPerguntasNumaFaixa(
        rotulo="Alerta — mais de 421 casos",
        semanas=28,
        cobertura_de_90=0.143,
        cobertura_de_50=0.036,
        erro_mediano=971.0,
        nivel_mediano=1428.0,
    ),
)


@dataclasses.dataclass(frozen=True)
class AlarmeEmDoisMeses:
    """O alarme do composto em 2 meses, para a linha de baixo da tabela.

    É o contraponto da calibração: o mesmo modelo, o mesmo horizonte e a mesma
    janela, medido na pergunta binária em vez de na do número.

    Fonte: `analises/2026-09-26_modelo_composto/saidas/alarme_do_composto.csv`,
    linha do braço `Composto` em h=8.
    """

    semanas_avaliadas: int = 102
    semanas_de_alerta: int = 28
    alertas_pegos: int = 24
    alarmes_falsos: int = 0
    precisao: float = 1.0

    def sensibilidade(self) -> float:
        """Fração das semanas de Alerta em que o alarme tocou."""
        return self.alertas_pegos / self.semanas_de_alerta


ALARME_EM_DOIS_MESES = AlarmeEmDoisMeses()


@dataclasses.dataclass(frozen=True)
class SerieDeSingapura:
    """Por que Singapura prevê melhor, e o que isso NÃO quer dizer.

    O argumento intuitivo — "lá tem mais dengue, então dá mais dado" — está
    errado, e o número mostra por quê: o pico semanal de Singapura em 2013 foi
    **menor** que o de Porto Alegre em 2025. A diferença não é volume de
    doença, é **volume de história**: dez anos de treino, com anos calmos, que
    ensinam ao modelo o que é o normal da cidade.

    É o mesmo argumento que derrubou a premissa de Porto Rico em 26/09/2026
    (eles usam 38,5 anos de série).

    Fonte: Shi et al. 2016, EHP 124(9):1369-75, ficha em
    `analises/2026-09-25_catalogo_modelos_prontos/2_sistemas_operacionais_mundo.md`
    e `documentacao_completa/partes/06_literatura.md`.
    """

    anos_de_treino: int = 10
    pico_semanal: int = 842
    temporadas_epidemicas_de_porto_alegre: int = 4
    pico_semanal_de_porto_alegre: int = 2381


SINGAPURA = SerieDeSingapura()


# ─────────────────────────────────────────────────────────────────────────────
# OS DOIS ANOS SEPARADOS — partida a frio contra operação com história
# ─────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class DesempenhoDeUmAno:
    """O modelo composto num horizonte, medido num ano só da avaliação.

    Por que separar: 2024 e 2025 são **regimes diferentes**, e a média dos dois
    não descreve nenhum. Ao prever o pico de 2024 o modelo nunca tinha visto
    uma semana acima de **879 casos**, e precisava acertar **1.601**; uma
    árvore de decisão não prevê acima do que viu no treino. Ao prever o pico de
    2025 ele já conhecia os **1.855** de 2024.

    O efeito é enorme no horizonte longo: em 3 meses o R² vai de **0,054** para
    **0,792**, e o alarme de **1 de 14** para **13 de 14**.

    ⚠️ **Descritivo e pós-fato.** O corte por ano foi feito depois de ver o
    resultado, é um ano contra um ano (45 e 52 semanas) e não foi pré-declarado.
    A confirmação certa é pré-declarar e medir em 2027.

    Fonte: recalculado em 27/09/2026 de `analises/2026-09-23_bateria_noturna/
    bloco_7_vetor_com_folha_20/saidas/previsoes_por_braco.csv`, recombinado no
    composto pelas funções de `analises/2026-09-26_modelo_composto/calcular.py`.

    Attributes:
        rotulo: Como o horizonte é dito em texto.
        erro_medio_absoluto: MAE em casos por semana.
        r2: Fração da variação dos casos que o modelo explica.
        captura_do_pico: Fração da altura do pico que o modelo alcança.
        alertas_pegos: Semanas de Alerta em que o alarme tocou.
        alertas_no_ano: Quantas semanas de Alerta o ano teve.
        precisao: Das vezes que o alarme tocou, quantas eram Alerta de verdade.
        falsos_por_ano: Alarmes falsos, normalizados por ano.
    """

    rotulo: str
    erro_medio_absoluto: float
    r2: float
    captura_do_pico: float
    alertas_pegos: int
    alertas_no_ano: int
    precisao: float
    falsos_por_ano: float

    def sensibilidade(self) -> float:
        """Fração das semanas de Alerta em que o alarme tocou."""
        return self.alertas_pegos / self.alertas_no_ano


SEMANAS_AVALIADAS_EM_2024 = 45
SEMANAS_AVALIADAS_EM_2025 = 52

COMPOSTO_EM_2024 = (
    DesempenhoDeUmAno("1 semana", 100.6, 0.851, 0.764, 9, 10, 1.000, 0.0),
    DesempenhoDeUmAno("1 mês", 193.9, 0.629, 0.610, 13, 13, 0.929, 1.2),
    DesempenhoDeUmAno("2 meses", 238.8, 0.414, 0.437, 10, 14, 1.000, 0.0),
    DesempenhoDeUmAno("3 meses", 322.3, 0.054, 0.248, 1, 14, 1.000, 0.0),
)

COMPOSTO_EM_2025 = (
    DesempenhoDeUmAno("1 semana", 103.7, 0.916, 0.958, 14, 14, 0.933, 1.0),
    DesempenhoDeUmAno("1 mês", 221.9, 0.753, 0.773, 14, 14, 0.737, 5.0),
    DesempenhoDeUmAno("2 meses", 226.7, 0.644, 0.565, 14, 14, 1.000, 0.0),
    DesempenhoDeUmAno("3 meses", 196.3, 0.792, 0.700, 13, 14, 0.867, 2.0),
)

# O que o modelo tinha visto ao prever o pico de cada temporada, e o que ele
# precisava acertar. É a explicação mecânica do contraste entre os dois anos.
MAIOR_PICO_CONHECIDO_EM_2024 = 879
PICO_A_PREVER_EM_2024 = 1601
MAIOR_PICO_CONHECIDO_EM_2025 = 1855
PICO_A_PREVER_EM_2025 = 2381
