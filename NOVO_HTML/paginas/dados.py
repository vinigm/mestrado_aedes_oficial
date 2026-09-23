"""Página de dados: as fontes e a janela de trabalho.

O conteúdo é tabelado de propósito. Fonte de dado se lê comparando linha a
linha — período, cadência, papel, ressalva —, não em prosa corrida.
"""

import layout
import navegacao
import numeros_do_projeto as numeros


# Uma linha por fonte: (nome, família, período, cadência, o que é, ressalva).
# A ressalva entra na própria tabela para que nenhuma fonte apareça sem o
# limite que ela carrega.
FONTES = (
    (
        "Captura de mosquito",
        "vetor",
        f"{numeros.BASE.primeira_semana} a 2025",
        "semanal",
        "Fêmeas de <i>Aedes aegypti</i> por armadilha inspecionada. Densidade, "
        "não contagem bruta. Só fêmeas, porque só a fêmea transmite.",
        "Secretaria Municipal de Saúde. Série histórica oficial do MI-Aedes.",
    ),
    (
        "Captura de mosquito",
        "vetor",
        f"2026 a {numeros.BASE.ultima_semana}",
        "semanal",
        "A mesma medida, continuando a série sem vão.",
        "Raspagem própria do portal MI-Aedes. <b>É manual, e o portal só expõe "
        "a semana corrente</b> — semana perdida é irrecuperável.",
    ),
    (
        "Casos confirmados de dengue",
        "alvo",
        f"{numeros.TABELA.primeira_semana_com_casos} em diante",
        "semanal",
        f"O alvo da previsão: casos confirmados em Porto Alegre. "
        f"{numeros.TABELA.semanas_com_casos} semanas.",
        "SINAN, via Open Data SUS. <b>Ruidoso</b> por latência de atendimento "
        "e subnotificação.",
    ),
    (
        "Clima",
        "clima",
        "série longa",
        "diária, agregada para semanal",
        "Chuva, temperatura, orvalho, umidade, pressão, radiação e vento. "
        "Detalhe na tabela da seção seguinte.",
        "NASA POWER (satélite e reanálise).",
    ),
    (
        "Índice ENSO",
        "clima",
        "série longa",
        "mensal",
        "A fase El Niño / La Niña do Pacífico, que empurra o clima da região "
        "para mais quente ou mais chuvoso.",
        "NOAA. Cadência mensal, diferente das demais.",
    ),
)


# Um tema climático por linha: (tema, colunas que ele gera, o que resume).
TEMAS_CLIMATICOS = (
    (
        "Chuva",
        ("precip_total_mm", "precip_max_dia_mm", "precip_media_dia_mm", "dias_de_chuva"),
        "Total da semana e dias com chuva dizem mais sobre criadouro do que "
        "uma média diária diria.",
    ),
    (
        "Temperatura",
        ("temp_media", "temp_min", "temp_max", "temp_amplitude_media"),
        "Mínimo, média, máximo e a amplitude média do dia.",
    ),
    (
        "Ponto de orvalho",
        ("orvalho_min", "orvalho_media", "orvalho_max"),
        "Mínimo, média e máximo.",
    ),
    (
        "Umidade",
        ("umid_min", "umid_media", "umid_max"),
        "Mínimo, média e máximo.",
    ),
    (
        "Pressão",
        ("pressao_min", "pressao_media", "pressao_max"),
        "Mínimo, média e máximo.",
    ),
    (
        "Radiação solar",
        ("radiacao_min", "radiacao_media", "radiacao_max"),
        "Mínimo, média e máximo.",
    ),
    (
        "Vento",
        ("vento_media", "vento_max"),
        "Só média e máximo; a mínima não é usada.",
    ),
)


def _metricas_do_topo() -> list[layout.Metrica]:
    """Os quatro números que dimensionam a base."""
    periodo = f"{numeros.BASE.primeira_semana} a {numeros.BASE.ultima_semana}"

    return [
        layout.Metrica(
            rotulo="Semanas de série",
            valor=str(numeros.BASE.semanas_com_dado),
            nota=periodo,
        ),
        layout.Metrica(
            rotulo="Inspeções de armadilha",
            valor=numeros.formatar_inteiro(numeros.BASE.inspecoes),
            nota=(
                f"{numeros.formatar_inteiro(numeros.BASE.armadilhas)} armadilhas · "
                f"{numeros.BASE.bairros} bairros"
            ),
        ),
        layout.Metrica(
            rotulo="Fêmeas de Aedes aegypti",
            valor=numeros.formatar_inteiro(numeros.BASE.femeas_de_aedes_aegypti),
            nota="capturadas e contadas em campo",
        ),
        layout.Metrica(
            rotulo="Colunas da tabela final",
            valor=str(numeros.TABELA.colunas),
            nota=f"{numeros.TABELA.linhas} linhas, uma por semana",
        ),
    ]


def _secao_as_series() -> str:
    """Só a figura das séries empilhadas, sem moldura de texto."""
    return layout.montar_figura(
        arquivo="imagens/series_para_modelar.png",
        titulo="",
        subtitulo="",
        legenda="",
    )


def _secao_as_fontes() -> str:
    """Tabela das fontes que entram na tabela semanal única."""
    cabecalhos = ["Fonte", "Período", "Cadência", "O que é", "Origem e ressalva"]

    linhas = []
    for nome, familia, periodo, cadencia, descricao, origem in FONTES:
        etiqueta = layout.montar_etiqueta(nome, familia)
        linhas.append([etiqueta, periodo, cadencia, descricao, origem])

    return layout.montar_tabela(cabecalhos, linhas)


def _secao_o_clima() -> str:
    """Tabela separada do clima: um tema por linha, com as colunas que gera."""
    cabecalhos = ["Tema", "Colunas geradas", "O que resume"]

    linhas = []
    for tema, colunas, resumo in TEMAS_CLIMATICOS:
        nomes_de_coluna = []
        for coluna in colunas:
            nomes_de_coluna.append(f'<code class="nomeColuna">{coluna}</code>')

        linhas.append([f"<b>{tema}</b>", " ".join(nomes_de_coluna), resumo])

    return layout.montar_tabela(cabecalhos, linhas)


def _secao_a_janela_util() -> str:
    """Justifica por que a janela de trabalho é mais curta que os 14 anos."""
    corpo = (
        f"<p>Apesar de <b>{numeros.BASE.semanas_com_dado} semanas</b> de captura "
        "do vetor, a janela usada para relacionar vetor e doença é "
        f"<b>{numeros.JANELA_UTIL_DE_TRABALHO}</b>.</p>"
    )

    motivos = layout.montar_lista(
        [
            "<b>Casos só existem desde 2018</b> — sem série de casos, não há o "
            "que comparar.",
            "<b>2020 e 2021 foram pandemia</b> — a vigilância se voltou para a "
            "COVID-19, distorcendo notificação e rotina de campo.",
            "<b>2026 ainda está incompleto</b> na fonte federal de casos.",
        ]
    )

    limitacao = layout.montar_aviso(
        tom="atencao",
        rotulo="Fato · limitação estrutural",
        texto=(
            "O recorte deixa <b>poucos ciclos epidemiológicos completos</b> para "
            "treinar e testar. Não é detalhe de implementação."
        ),
    )

    contraponto = layout.montar_aviso(
        tom="bom",
        rotulo="Fato · a série longa vale para outro alvo",
        texto=(
            "Para prever o <b>próprio vetor</b>, e não os casos, treinar desde "
            "2012 vence em <b>3 de 4</b> horizontes — e a vantagem cresce com o "
            "horizonte."
        ),
    )

    return corpo + motivos + limitacao + contraponto


def montar_corpo() -> str:
    """Monta o corpo da página, seção por seção, na ordem da navegação."""
    pagina = navegacao.PAGINA_DADOS

    montadores_por_ancora = {
        "as-series": _secao_as_series,
        "as-fontes": _secao_as_fontes,
        "o-clima": _secao_o_clima,
        "a-janela-util": _secao_a_janela_util,
    }

    blocos = []
    for ordem, secao in enumerate(pagina.secoes, start=1):
        montador = montadores_por_ancora[secao.ancora]
        blocos.append(
            layout.montar_secao(secao, ordem, intro="", corpo=montador())
        )

    return "".join(blocos)


def montar_metricas() -> list[layout.Metrica]:
    """Régua de números do topo da página de dados."""
    return _metricas_do_topo()
