"""Página do Seminário de Andamento: a apresentação em slides.

Formato pedido pelo orientador em 21/09/2026: **até 10 minutos**, cobrindo
problema, importância, metodologia, resultados e próximos passos, com o
**último slide de direcionamentos**.

A apresentação é organizada em **tópicos**, que o índice horizontal no topo do
palco destaca conforme ela avança. Um tópico pode ocupar mais de um slide — é
só repetir o nome do tópico no slide seguinte.

⚠️ Instrução direta do orientador, que manda no tom do bloco de resultados:
não chegar à banca dizendo "não teve correlação com mosquito ou clima". O
achado negativo aparece, porque escondê-lo seria desonesto, mas enquadrado
pelo que de fato significa.

⏳ ESTADO: rascunho de estrutura. Os tópicos e a ordem estão fechados; o
conteúdo de cada slide ainda vai ser refinado com o autor.
"""

import deck
import layout
import numeros_do_projeto as numeros


# Os tópicos da apresentação, na ordem. Ficam nomeados aqui porque a agenda e o
# índice horizontal precisam da mesma lista — e uma lista só evita que os dois
# divirjam quando um tópico for renomeado.
TOPICO_AGENDA = "Agenda"
TOPICO_OBJETIVO = "Objetivo"
TOPICO_DADOS = "Dados"
TOPICO_CENARIOS = "Cenários testados"
TOPICO_ADOTADO = "Cenário adotado"
TOPICO_RESULTADOS = "Resultados parciais"
TOPICO_PROXIMOS = "Próximos passos"

# O que a agenda lista. A capa e a própria agenda ficam de fora: elas situam a
# apresentação, não fazem parte do conteúdo dela.
TOPICOS_DA_AGENDA = (
    TOPICO_OBJETIVO,
    TOPICO_DADOS,
    TOPICO_CENARIOS,
    TOPICO_ADOTADO,
    TOPICO_RESULTADOS,
    TOPICO_PROXIMOS,
)


def _slide_capa() -> deck.Slide:
    """Abertura. Sem tópico, então fica fora do índice."""
    return deck.Slide(
        topico="",
        titulo="Modelo preditivo de casos de dengue em Porto Alegre",
        corpo=(
            "<p>A partir da captura de mosquito das armadilhas municipais, "
            "do clima e do histórico de notificação.</p>"
            "<p><b>Vinicius Guerra</b> · Seminário de Andamento<br>"
            "PPGC — UFRGS · Orientação: Prof. Weverton Cordeiro</p>"
        ),
        nota="Dez minutos.",
    )


def _slide_agenda() -> deck.Slide:
    """O roteiro da apresentação, numerado."""
    itens = []
    for ordem, topico in enumerate(TOPICOS_DA_AGENDA, start=1):
        itens.append(f"<li><b>{ordem}.</b>&nbsp;&nbsp;{layout.escapar(topico)}</li>")

    return deck.Slide(
        topico=TOPICO_AGENDA,
        titulo="Agenda",
        corpo=f'<ul class="listaAgenda">{"".join(itens)}</ul>',
        nota="Passar rápido. Serve para a banca saber onde a fala vai chegar.",
    )


def _slide_objetivo() -> deck.Slide:
    """A pergunta da pesquisa e por que ela importa."""
    return deck.Slide(
        topico=TOPICO_OBJETIVO,
        titulo="Medir se a rede de armadilhas antecipa a dengue — e com quanto tempo",
        corpo=(
            layout.montar_fluxo(
                [
                    ("Picada", "a transmissão acontece"),
                    ("Sintoma", "dias depois"),
                    ("Atendimento", "se a pessoa procurar"),
                    ("Notificação", "só então o caso existe"),
                ]
            )
            + layout.montar_aviso(
                tom="atencao",
                rotulo="Por que antecipar importa mais do que acertar o tamanho",
                texto=(
                    "Quando a curva de casos sobe, a transmissão <b>já "
                    "aconteceu</b>. Agir nesse momento é agir tarde."
                ),
            )
        ),
        nota="⏳ Refinar: falta dizer o custo da rede e que ela já existe.",
    )


def _slide_o_que_o_projeto_faz() -> deck.Slide:
    """O que o projeto se propõe a construir, depois do porquê."""
    horizontes = []
    for desempenho in numeros.DESEMPENHO_DO_MODELO:
        horizontes.append(
            layout.montar_cartao(
                rotulo="Horizonte",
                titulo=desempenho.rotulo,
                corpo="",
            )
        )

    return deck.Slide(
        topico=TOPICO_OBJETIVO,
        titulo="Construir um modelo que preveja quantos casos de dengue virão",
        corpo=(
            layout.montar_fluxo(
                [
                    ("Captura de mosquito", "as armadilhas da cidade, toda semana"),
                    ("Clima", "chuva, temperatura, umidade e mais"),
                    ("Histórico de casos", "o que já foi notificado"),
                    ("Previsão", "quantos casos na semana-alvo"),
                ],
                # As três primeiras são fontes que entram juntas; só a última é
                # consequência delas. Daí a soma entre elas e a seta no fim.
                conectores=[
                    layout.CONECTOR_DE_SOMA,
                    layout.CONECTOR_DE_SOMA,
                    layout.CONECTOR_DE_SEQUENCIA,
                ],
            )
            + layout.montar_grade(horizontes, colunas=4)
        ),
        nota=(
            "O slide anterior diz <b>por quê</b>; este diz <b>o quê</b>. "
            "Entradas à esquerda, previsão à direita, e os quatro horizontes "
            "que o trabalho avalia."
        ),
    )


def _slide_dados() -> deck.Slide:
    """A série reunida — a contribuição mais sólida do trabalho."""
    intervalo = f"{numeros.BASE.primeira_semana} a {numeros.BASE.ultima_semana}"

    return deck.Slide(
        topico=TOPICO_DADOS,
        titulo="14 anos de captura reunidos, corrigidos e certificados",
        corpo=(
            layout.montar_regua(
                [
                    layout.Metrica(
                        "Semanas", str(numeros.BASE.semanas_com_dado), intervalo
                    ),
                    layout.Metrica(
                        "Inspeções",
                        numeros.formatar_inteiro(numeros.BASE.inspecoes),
                        "conferidas célula a célula",
                    ),
                    layout.Metrica(
                        "Fêmeas de Aedes aegypti",
                        numeros.formatar_inteiro(numeros.BASE.femeas_de_aedes_aegypti),
                        "a medida que o modelo usa",
                    ),
                ]
            )
            + layout.montar_aviso(
                tom="bom",
                rotulo="Por que isso é contribuição, e não preparação",
                texto=(
                    "A série não existia reunida. Foi recuperada junto à "
                    "Secretaria, corrigida e documentada — faltam "
                    f"<b>{numeros.BASE.semanas_faltantes} semanas em 14 anos</b>."
                ),
            )
        ),
        nota="Os números. A figura vem no slide seguinte.",
    )


def _slide_vetor_e_casos() -> deck.Slide:
    """O par que sustenta a pergunta: vetor em cima, casos embaixo."""
    return deck.Slide(
        topico=TOPICO_DADOS,
        titulo="A curva do mosquito e a curva da doença, no mesmo eixo de tempo",
        corpo=(
            '<div class="deckFiguraCheia">'
            '<img src="imagens/slide_vetor_e_casos.png" '
            'alt="Densidade de Aedes aegypti e casos confirmados, semana a semana">'
            "</div>"
        ),
        nota=(
            "Apontar: o vetor é <b>cíclico</b> ano a ano; os casos só existem "
            "de 2018; e a subida do mosquito vem <b>antes</b> da subida dos "
            "casos em 2022, 2023, 2024 e 2025."
        ),
        e_figura=True,
    )


def _slide_clima() -> deck.Slide:
    """O contexto climático que alimenta o modelo."""
    return deck.Slide(
        topico=TOPICO_DADOS,
        titulo="E o clima, que é o que faz o mosquito proliferar",
        corpo=(
            '<div class="deckFiguraCheia">'
            '<img src="imagens/slide_clima.png" '
            'alt="Chuva, temperatura, umidade e índice ENSO, semana a semana">'
            "</div>"
        ),
        nota=(
            "Passar rápido. Só situar que o clima cobre os 14 anos inteiros, "
            "diferente dos casos."
        ),
        e_figura=True,
    )


def _slide_cenarios() -> deck.Slide:
    """O mapa dos experimentos."""
    return deck.Slide(
        topico=TOPICO_CENARIOS,
        titulo="Nove cenários, cada um mudando um parâmetro por vez",
        corpo=(
            "<p>⏳ <b>Rascunho.</b> Aqui entra a tabela dos nove cenários, com "
            "o alvo de cada um — a mesma da página <i>Cenários testados</i>.</p>"
        ),
        nota="⏳ A fazer: trazer a tabela resumo dos 9 cenários.",
    )


def _slide_adotado() -> deck.Slide:
    """A configuração que ficou."""
    return deck.Slide(
        topico=TOPICO_ADOTADO,
        titulo="A configuração de referência, e como ela foi escolhida",
        corpo=(
            "<p>⏳ <b>Rascunho.</b> HistGradientBoosting, perda quantílica em "
            "0,85, com vetor — vencedora entre as "
            f"<b>{numeros.TOTAL_DE_CONFIGURACOES_TESTADAS}</b> testadas pelo "
            "menor erro de calibração.</p>"
            "<p>Falta aqui: a validação walk-forward e o período efetivamente "
            "usado no treino.</p>"
        ),
        nota="⏳ A fazer: tabela da configuração + figura do walk-forward.",
    )


def _slide_resultados() -> deck.Slide:
    """O desempenho da configuração adotada."""
    cabecalhos = ["Horizonte", "R²", "Erro médio", "Captura do pico"]
    linhas = []
    for desempenho in numeros.DESEMPENHO_DO_MODELO:
        linhas.append(
            [
                f"<b>{layout.escapar(desempenho.rotulo)}</b>",
                f"<b>{numeros.formatar_decimal(desempenho.r2, 3)}</b>",
                numeros.formatar_decimal(desempenho.erro_medio_absoluto, 1),
                numeros.formatar_percentual(desempenho.captura_do_pico, 0),
            ]
        )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="O modelo é honesto até um mês, e perde força em três",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                tom="bom",
                rotulo="A degradação tem causa medida",
                texto=(
                    "A memória da própria série de casos explica <b>91%</b> do "
                    "acerto em uma semana e <b>0%</b> em três meses."
                ),
            )
        ),
        nota="⏳ Refinar junto com os dois slides seguintes deste tópico.",
    )


def _slide_alarme() -> deck.Slide:
    """O mesmo modelo lido como alarme de surto."""
    cabecalhos = ["Horizonte", "Sensibilidade", "Precisão", "Falsos por ano"]
    linhas = [
        [
            "<b>1 mês</b>",
            f"<b>{numeros.formatar_percentual(numeros.ALARME.sensibilidade_um_mes)}</b>",
            numeros.formatar_percentual(numeros.ALARME.precisao_um_mes),
            numeros.formatar_decimal(numeros.ALARME.falsos_por_ano_um_mes, 1),
        ],
        [
            "<b>3 meses</b>",
            f"<b>{numeros.formatar_percentual(numeros.ALARME.sensibilidade_tres_meses)}</b>",
            numeros.formatar_percentual(numeros.ALARME.precisao_tres_meses),
            numeros.formatar_decimal(numeros.ALARME.falsos_por_ano_tres_meses, 1),
        ],
    ]

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="Como alarme de surto, ele acerta 97% das semanas a um mês",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                tom="atencao",
                rotulo="Ressalva que limita a leitura",
                texto=(
                    f"A avaliação contém apenas <b>{numeros.ALARME.episodios_na_avaliacao} "
                    "episódios</b> de surto."
                ),
            )
        ),
        nota="Aqui a pergunta muda: não é o tamanho, é se a epidemia chegou.",
    )


def _slide_o_vetor() -> deck.Slide:
    """O achado central, com o enquadramento que ele exige."""
    contraste = layout.montar_grade(
        [
            layout.montar_cartao(
                rotulo="O que foi medido",
                titulo="",
                corpo=(
                    "<p>Sobre um modelo que <b>já tem clima e histórico de "
                    "casos</b>, a armadilha não melhora a previsão em nenhuma "
                    "comparação que sobreviva à correção.</p>"
                ),
            ),
            layout.montar_cartao(
                rotulo="O que isso NÃO significa",
                titulo="",
                corpo=(
                    "<p>Que o mosquito não importa. <b>Sem vetor não há "
                    "transmissão</b> — e a subida da captura aparece "
                    "<b>antes</b> da subida dos casos.</p>"
                ),
            ),
        ],
        colunas=2,
    )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="A armadilha não adiciona sobre clima e histórico — e isso pede explicação",
        corpo=(
            contraste
            + layout.montar_aviso(
                tom="info",
                rotulo="A leitura mais provável",
                texto=(
                    "Um resultado nulo diante de um padrão visível e "
                    "biologicamente esperado aponta mais para <b>um efeito que "
                    "o desenho atual não captura</b> do que para ausência de "
                    "efeito."
                ),
            )
        ),
        nota=(
            "⚠️ <b>O slide mais delicado.</b> Nunca dizer 'não deu correlação'. "
            "Dizer: medimos isto, sob estas condições."
        ),
    )


def _slide_proximos_passos() -> deck.Slide:
    """O último slide, como o orientador pediu."""
    cabecalhos = ["", "Hoje", "Próxima etapa"]
    linhas = [
        [
            "<b>Alvo primário</b>",
            "casos de dengue",
            "casos das <b>quatro arboviroses</b>, a partir do vetor",
        ],
        [
            "<b>Alvo secundário</b>",
            "—",
            "<b>a proliferação do vetor</b>, de clima e captura",
        ],
        ["<b>Horizonte</b>", "até 3 meses", "até <b>6 meses</b>"],
        [
            "<b>Primeira pergunta</b>",
            "o vetor melhora a previsão?",
            "<b>qual é a defasagem</b> entre as duas curvas?",
        ],
    ]

    return deck.Slide(
        topico=TOPICO_PROXIMOS,
        titulo="Deslocar a pergunta da consequência para a causa",
        corpo=layout.montar_tabela(cabecalhos, linhas),
        nota=(
            "Fechar aqui. Este slide saiu da reunião de "
            f"{numeros.DATA_DA_REUNIAO_DE_ALINHAMENTO}."
        ),
    )


def montar_slides() -> list[deck.Slide]:
    """Os slides da apresentação, na ordem."""
    return [
        _slide_capa(),
        _slide_agenda(),
        _slide_objetivo(),
        _slide_o_que_o_projeto_faz(),
        _slide_dados(),
        _slide_vetor_e_casos(),
        _slide_clima(),
        _slide_cenarios(),
        _slide_adotado(),
        _slide_resultados(),
        _slide_alarme(),
        _slide_o_vetor(),
        _slide_proximos_passos(),
    ]


def montar_metricas() -> list[layout.Metrica]:
    """Sem régua: o palco do deck ocupa a página."""
    return []


def montar_corpo() -> str:
    """Só o deck: a página inteira é a apresentação."""
    return deck.montar(montar_slides())
