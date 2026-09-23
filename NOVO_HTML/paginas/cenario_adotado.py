"""Página do cenário adotado: a configuração de referência e o resultado dela.

Mostra só o que vale hoje. Não conta a história de como o projeto chegou até
aqui — essa história fica no registro cronológico do repositório, não no
painel para banca.
"""

import layout
import navegacao
import numeros_do_projeto as numeros

import graficos
import linha_do_treino


# Restrições que encolhem a janela de avaliação, lidas da configuração de
# referência (`modelagem_aedes/config/experimentos/cidade_regressao.py`) e da
# tabela de modelagem. Ficam aqui nomeadas porque entram no texto da página.
MINIMO_DE_SEMANAS_DE_TREINO = 104
ULTIMA_SEMANA_COM_CASO = "26/04/2026"

# Aproximado de propósito: as 104 semanas de treino mínimo contam a partir da
# primeira semana COM alvo, e o passo do walk-forward é de 2 semanas. O valor
# exato depende da rodada, então a página diz "cerca de".
INICIO_APROXIMADO_DA_AVALIACAO = "fevereiro de 2020"

# Tamanho da janela de treino contra o tamanho da série de captura. A
# diferença entre os dois é o ponto da figura logo abaixo da configuração.
ANOS_APROXIMADOS_DE_TREINO = 8
ANOS_DA_SERIE_DE_CAPTURA = 14


def _secao_a_configuracao() -> str:
    """Tabela com a configuração de referência e o que é a perda quantílica."""
    cabecalhos = ["Característica", "Valor"]
    linhas = [
        ["Algoritmo", "<b>HistGradientBoostingRegressor</b> (scikit-learn)"],
        ["Função de perda", "perda quantílica, quantil <b>0,85</b>"],
        ["Variáveis", "núcleo + clima + <b>variáveis do vetor</b> (mosquito)"],
        ["Alvo", "casos de dengue <b>confirmados</b> (SINAN), nível cidade"],
        [
            "Selecionada por",
            f"menor erro de calibração entre <b>{numeros.TOTAL_DE_CONFIGURACOES_TESTADAS}"
            "</b> configurações testadas",
        ],
        [
            "Validação",
            "<b>walk-forward</b>: treina só com o passado, prevê uma semana à "
            "frente, repete",
        ],
    ]
    tabela = layout.montar_tabela(cabecalhos, linhas)

    explicacao_do_quantil = layout.montar_aviso(
        tom="info",
        rotulo="O que é perda quantílica em 0,85",
        texto=(
            "A previsão não é a <b>média esperada</b> de casos: é um "
            "<b>patamar ultrapassado em cerca de 15% das semanas</b>. O viés é "
            "para cima de propósito, porque para a vigilância <b>subestimar um "
            "surto custa mais caro</b> do que superestimar."
        ),
    )

    periodo_usado = _figura_do_periodo_usado()

    return tabela + explicacao_do_quantil + periodo_usado


def _figura_do_periodo_usado() -> str:
    """A linha do tempo do que entrou no treino, com a ressalva do tamanho.

    A página de dados já mostra de quando até quando cada fonte tem dado. Aqui
    a pergunta é outra: de qual período o modelo aprendeu. Mostrar a cobertura
    das fontes neste lugar superestimaria a evidência, porque a série de
    captura tem 14 anos e a janela de treino tem bem menos.
    """
    figura = linha_do_treino.montar()

    tamanho_da_janela = layout.montar_aviso(
        tom="atencao",
        rotulo="O que isso significa para o tamanho da evidência",
        texto=(
            "O modelo aprendeu de uma janela de pouco mais de "
            f"<b>{ANOS_APROXIMADOS_DE_TREINO} anos</b>, não dos "
            f"<b>{ANOS_DA_SERIE_DE_CAPTURA} anos</b> da série de captura. "
            "Nesse período cabem poucos ciclos epidêmicos completos, e é essa "
            "escassez — não o algoritmo — que limita o quanto se pode afirmar."
        ),
    )

    return figura + tamanho_da_janela


# As três medidas do desempenho, uma por gráfico, lado a lado. Cada tupla é
# (rótulo do eixo, atributo em DesempenhoPorHorizonte, nome da série).
#
# As três contam a mesma história por ângulos diferentes: o erro sobe, o R² cai
# e a captura do pico cai. Vê-las juntas evita a leitura de que só uma métrica
# piorou.
MEDIDAS_DO_DESEMPENHO = (
    ("R² (o quanto explica)", "r2", "R² do modelo", "#1B6EF3"),
    ("Erro médio (casos/semana)", "erro_medio_absoluto", "Erro médio", "#C0392B"),
    ("Captura do pico", "captura_do_pico", "Captura do pico", "#1F7A4D"),
)


def _montar_grafico_de_uma_medida(
    rotulo_do_eixo: str,
    atributo: str,
    nome_da_serie: str,
    cor: str,
) -> str:
    """Desenha uma medida do desempenho ao longo dos horizontes.

    Args:
        rotulo_do_eixo: Texto do eixo vertical, também usado no título.
        atributo: Nome do campo em `DesempenhoPorHorizonte` a ler.
        nome_da_serie: Rótulo da linha na legenda.
        cor: Cor da linha, a mesma que marca a coluna dessa medida na tabela.

    Returns:
        O HTML do gráfico.
    """
    pontos = []
    for desempenho in numeros.DESEMPENHO_DO_MODELO:
        valor = getattr(desempenho, atributo)
        pontos.append((float(desempenho.semanas), valor))

    series = {nome_da_serie: pontos}

    return graficos.montar_grafico_de_linhas(
        series, "horizonte (semanas)", rotulo_do_eixo, cores=[cor]
    )


def _montar_graficos_do_desempenho() -> str:
    """Os três gráficos do desempenho, lado a lado."""
    blocos = []
    for rotulo_do_eixo, atributo, nome_da_serie, cor in MEDIDAS_DO_DESEMPENHO:
        blocos.append(
            _montar_grafico_de_uma_medida(rotulo_do_eixo, atributo, nome_da_serie, cor)
        )

    return f'<div class="graficosLadoALado">{"".join(blocos)}</div>'


def _celula_colorida(texto: str, cor: str) -> str:
    """Envolve o conteúdo de uma célula na cor da medida.

    A cor é a mesma da linha no gráfico correspondente: é o que deixa claro,
    sem legenda, qual coluna da tabela virou qual curva.

    Args:
        texto: O conteúdo já formatado da célula.
        cor: A cor em hexadecimal, vinda de `MEDIDAS_DO_DESEMPENHO`.

    Returns:
        A célula com a cor aplicada.
    """
    # A cor entra no próprio elemento, e não só num <span> em volta, porque a
    # regra global de <b> define `color` e sobrescreveria a herança.
    return f'<span style="color:{cor}"><b style="color:{cor}">{texto}</b></span>'


def _secao_o_desempenho() -> str:
    """Tabela dos quatro horizontes, os três gráficos e a causa da degradação.

    A ordem das colunas da tabela segue a ordem dos gráficos, e cada par
    compartilha a cor — a tabela dá o número exato, o gráfico dá o formato da
    curva, e a cor liga os dois sem precisar de legenda.
    """
    rotulo_r2, _, _, cor_r2 = MEDIDAS_DO_DESEMPENHO[0]
    rotulo_erro, _, _, cor_erro = MEDIDAS_DO_DESEMPENHO[1]
    rotulo_captura, _, _, cor_captura = MEDIDAS_DO_DESEMPENHO[2]

    cabecalhos = [
        "Horizonte",
        _celula_colorida(rotulo_r2, cor_r2),
        _celula_colorida(rotulo_erro, cor_erro),
        _celula_colorida(rotulo_captura, cor_captura),
    ]

    linhas = []
    for desempenho in numeros.DESEMPENHO_DO_MODELO:
        linhas.append(
            [
                f"<b>{layout.escapar(desempenho.rotulo)}</b>",
                _celula_colorida(numeros.formatar_decimal(desempenho.r2, 3), cor_r2),
                _celula_colorida(
                    numeros.formatar_decimal(desempenho.erro_medio_absoluto, 1), cor_erro
                ),
                _celula_colorida(
                    numeros.formatar_percentual(desempenho.captura_do_pico, 1),
                    cor_captura,
                ),
            ]
        )

    tabela = layout.montar_tabela(cabecalhos, linhas)
    grafico = _montar_graficos_do_desempenho()

    desempenho_em_um_mes = numeros.DESEMPENHO_DO_MODELO[1]
    desempenho_em_tres_meses = numeros.DESEMPENHO_DO_MODELO[3]

    leitura = layout.montar_aviso(
        tom="atencao",
        rotulo="Como ler",
        texto=(
            "O modelo é honesto até <b>um mês</b>: explica "
            f"{numeros.formatar_percentual(desempenho_em_um_mes.r2, 0)} da "
            "variação dos casos. Em <b>três meses</b> explica "
            f"{numeros.formatar_percentual(desempenho_em_tres_meses.r2, 0)}."
        ),
    )

    causa_da_degradacao = layout.montar_aviso(
        tom="bom",
        rotulo="Fato · a causa da degradação é medida",
        texto=(
            "O histórico recente da própria série de casos explica "
            f"{numeros.formatar_percentual(numeros.DEGRADACAO.fracao_explicada_em_uma_semana, 0)} "
            "do acerto em uma semana, e "
            f"{numeros.formatar_percentual(numeros.DEGRADACAO.fracao_explicada_em_doze_semanas, 0)} "
            "em doze semanas. Não é defeito de ajuste do modelo: em três meses "
            "o passado recente simplesmente não informa mais."
        ),
    )

    return tabela + grafico + leitura + causa_da_degradacao


def _secao_como_alarme() -> str:
    """A leitura do modelo como alarme de surto, com a ressalva de amostra."""
    cabecalhos = ["Horizonte", "Sensibilidade", "Precisão", "Falsos por ano"]
    linhas = [
        [
            "<b>1 mês</b>",
            numeros.formatar_percentual(numeros.ALARME.sensibilidade_um_mes),
            numeros.formatar_percentual(numeros.ALARME.precisao_um_mes),
            numeros.formatar_decimal(numeros.ALARME.falsos_por_ano_um_mes, 1),
        ],
        [
            "<b>3 meses</b>",
            numeros.formatar_percentual(numeros.ALARME.sensibilidade_tres_meses),
            numeros.formatar_percentual(numeros.ALARME.precisao_tres_meses),
            numeros.formatar_decimal(numeros.ALARME.falsos_por_ano_tres_meses, 1),
        ],
    ]
    tabela = layout.montar_tabela(cabecalhos, linhas)

    porque_importa = layout.montar_aviso(
        tom="bom",
        rotulo="Por que isto importa mais que a captura do pico",
        texto=(
            "A captura do pico mede se o modelo acerta o <b>tamanho</b> da "
            "epidemia. Para a vigilância, o que importa é se o <b>alarme "
            "toca</b> a tempo. São perguntas diferentes, e a operacional é a "
            "segunda."
        ),
    )

    ressalva = layout.montar_aviso(
        tom="critico",
        rotulo="Ressalva · poucos episódios",
        texto=(
            f"Só há <b>{numeros.ALARME.episodios_na_avaliacao}</b> episódios de "
            "surto no período avaliado. Nenhum número por episódio pode ser "
            "citado como estatisticamente estável."
        ),
    )

    return tabela + porque_importa + ressalva


def _secao_o_vetor() -> str:
    """Os dois achados de sinal oposto sobre a contribuição do vetor."""
    cartao_previsao = layout.montar_cartao(
        rotulo="Fato · na previsão de casos",
        titulo="Sem efeito demonstrável",
        corpo=(
            f"<p>Em <b>{numeros.VETOR.comparacoes_em_que_o_vetor_erra_menos} de "
            f"{numeros.VETOR.comparacoes_pareadas}</b> comparações pareadas, o "
            "modelo com vetor erra menos que o modelo só com clima. "
            f"<b>Nenhuma</b> das {numeros.VETOR.comparacoes_pareadas} sobrevive "
            "à correção para múltiplas comparações.</p>"
        ),
    )

    cartao_alarme = layout.montar_cartao(
        rotulo="Fato · no alarme de surto, três meses",
        titulo="O vetor piora",
        corpo=(
            f"<p>Em <b>{numeros.VETOR.semanas_no_teste_de_alarme}</b> semanas "
            "avaliadas, o modelo só com clima acerta onde o modelo com vetor "
            f"erra em <b>{numeros.VETOR.semanas_em_que_so_clima_acerta}</b> "
            "semanas, contra "
            f"<b>{numeros.VETOR.semanas_em_que_clima_mais_vetor_acerta}</b> no "
            "sentido inverso. É o <b>único</b> resultado do projeto que "
            "sobrevive à correção múltipla (p de Holm = "
            f"{numeros.formatar_decimal(numeros.VETOR.p_holm_do_alarme, 3)}).</p>"
        ),
    )

    grade = layout.montar_grade([cartao_previsao, cartao_alarme], colunas=2)

    enquadramento = layout.montar_aviso(
        tom="atencao",
        rotulo="Enquadramento obrigatório",
        texto=(
            "Isto <b>não</b> diz que o mosquito não importa — sem vetor não há "
            "doença. Diz que, para <b>este alvo</b>, <b>neste horizonte</b> e "
            "sobre <b>estas variáveis</b>, a contagem de armadilha é "
            "redundante: o histórico recente de casos já carrega a informação."
        ),
    )

    return grade + enquadramento


def _secao_limitacoes() -> str:
    """Quatro afirmações que os dados não sustentam, mesmo lidos a favor."""
    cartoes = [
        layout.montar_cartao(
            rotulo="Não se pode afirmar",
            titulo="Que o vetor melhora a previsão de casos",
            corpo=(
                f"<p><b>{numeros.VETOR.comparacoes_que_sobrevivem_a_holm} de "
                f"{numeros.VETOR.comparacoes_pareadas}</b> comparações "
                "sobrevivem à correção múltipla.</p>"
            ),
        ),
        layout.montar_cartao(
            rotulo="Não se pode afirmar",
            titulo="Que clima e vetor são equivalentes",
            corpo=(
                "<p>Com a margem pré-declarada e o alvo decidido, a "
                "equivalência fecha em "
                f"<b>{numeros.LIMITES.equivalencia_clima_vetor_fechada} de "
                f"{numeros.LIMITES.equivalencia_clima_vetor_testada}</b> "
                "comparações.</p>"
            ),
        ),
        layout.montar_cartao(
            rotulo="Não se pode afirmar",
            titulo="Que a perda importa mais que o algoritmo",
            corpo=(
                "<p>A função de perda pesa "
                f"{numeros.formatar_percentual(numeros.LIMITES.peso_da_perda_percentual)}, "
                "o algoritmo pesa "
                f"{numeros.formatar_percentual(numeros.LIMITES.peso_do_algoritmo_percentual)}. "
                "A ordem entre os dois se inverteu.</p>"
            ),
        ),
        layout.montar_cartao(
            rotulo="Não se pode afirmar",
            titulo="Que estas 6 variáveis de clima são as que importam",
            corpo=(
                "<p>Recortando a série em 2023, "
                f"<b>{numeros.LIMITES.colunas_de_clima_que_mudam_ao_recortar} das "
                f"{numeros.LIMITES.colunas_de_clima_total}</b> colunas "
                "escolhidas mudam.</p>"
            ),
        ),
    ]

    return layout.montar_grade(cartoes, colunas=2)


# Um montador de HTML por âncora de seção, e a frase de abertura de cada uma.
_MONTADORES_POR_ANCORA = {
    "a-configuracao": _secao_a_configuracao,
    "o-desempenho": _secao_o_desempenho,
    "como-alarme": _secao_como_alarme,
    "o-vetor": _secao_o_vetor,
    "limitacoes": _secao_limitacoes,
}

_INTRODUCOES_POR_ANCORA = {
    "limitacoes": (
        "Quatro leituras que os números não sustentam, mesmo tomadas com a "
        "interpretação mais favorável possível."
    ),
}


def montar_corpo() -> str:
    """Monta o corpo da página, seção por seção, na ordem da navegação."""
    pagina = navegacao.PAGINA_CENARIO_ADOTADO

    blocos = []
    for ordem, secao in enumerate(pagina.secoes, start=1):
        montador = _MONTADORES_POR_ANCORA[secao.ancora]
        intro = _INTRODUCOES_POR_ANCORA.get(secao.ancora, "")
        blocos.append(layout.montar_secao(secao, ordem, intro=intro, corpo=montador()))

    return "".join(blocos)


def montar_metricas() -> list[layout.Metrica]:
    """Régua de números do topo: o resumo do cenário adotado."""
    desempenho_em_um_mes = numeros.DESEMPENHO_DO_MODELO[1]

    return [
        layout.Metrica(
            rotulo="Configuração vencedora",
            valor=f"1ª de {numeros.TOTAL_DE_CONFIGURACOES_TESTADAS}",
            nota="menor erro de calibração",
        ),
        layout.Metrica(
            rotulo="R² em 1 mês",
            valor=numeros.formatar_decimal(desempenho_em_um_mes.r2, 3),
            nota=(
                f"MAE de {numeros.formatar_decimal(desempenho_em_um_mes.erro_medio_absoluto, 1)} "
                "casos/semana"
            ),
        ),
        layout.Metrica(
            rotulo="Sensibilidade do alarme, 1 mês",
            valor=numeros.formatar_percentual(numeros.ALARME.sensibilidade_um_mes),
            nota=f"{numeros.formatar_decimal(numeros.ALARME.falsos_por_ano_um_mes, 1)} falsos/ano",
        ),
        layout.Metrica(
            rotulo="Vetor no alarme, 3 meses",
            valor="piora",
            nota=f"p de Holm {numeros.formatar_decimal(numeros.VETOR.p_holm_do_alarme, 3)}",
        ),
    ]
