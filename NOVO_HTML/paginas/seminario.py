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

# A lista de temas climáticos vive na página de dados. Importar de lá evita
# que o slide e a página divirjam quando uma coluna for acrescentada.
import cenario_adotado as pagina_do_cenario_adotado
import cenarios as pagina_de_cenarios
import dados as pagina_de_dados


# Os tópicos da apresentação, na ordem. Ficam nomeados aqui porque a agenda e o
# índice horizontal precisam da mesma lista — e uma lista só evita que os dois
# divirjam quando um tópico for renomeado.
TOPICO_AGENDA = "Agenda"
TOPICO_OBJETIVO = "Objetivo"
TOPICO_DADOS = "Dados"
TOPICO_CENARIOS = "Cenários"
TOPICO_RESULTADOS = "Resultados"
TOPICO_PROXIMOS = "Próximos passos"

# O que a agenda lista. A capa e a própria agenda ficam de fora: elas situam a
# apresentação, não fazem parte do conteúdo dela.
TOPICOS_DA_AGENDA = (
    TOPICO_OBJETIVO,
    TOPICO_DADOS,
    TOPICO_CENARIOS,
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
        # O rótulo do slide já diz "Agenda": repetir a palavra no título
        # gastaria a linha mais visível do slide com uma informação que o
        # leitor acabou de ler.
        titulo="O percurso desta apresentação",
        rotulo_curto="Roteiro",
        corpo=f'<ul class="listaAgenda">{"".join(itens)}</ul>',
        nota="Passar rápido. Serve para a banca saber onde a fala vai chegar.",
    )


def _slide_objetivo() -> deck.Slide:
    """A pergunta da pesquisa e por que ela importa."""
    return deck.Slide(
        topico=TOPICO_OBJETIVO,
        titulo="Medir se a rede de armadilhas antecipa a dengue — e com quanto tempo",
        rotulo_curto="A pergunta",
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
        rotulo_curto="O modelo",
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



def _slide_vetor_e_casos() -> deck.Slide:
    """O par que sustenta a pergunta: vetor em cima, casos embaixo."""
    return deck.Slide(
        topico=TOPICO_DADOS,
        titulo="A curva do mosquito e a curva da doença, no mesmo eixo de tempo",
        rotulo_curto="Mosquito e casos",
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
        rotulo_curto="Clima",
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


def _slide_colunas_de_clima() -> deck.Slide:
    """De quantas variáveis o clima é feito, e como cada uma é resumida."""
    cabecalhos = ["Tema", "Colunas geradas"]

    linhas = []
    total_de_colunas = 0
    for tema, colunas, _resumo in pagina_de_dados.TEMAS_CLIMATICOS:
        total_de_colunas += len(colunas)

        nomes = []
        for coluna in colunas:
            nomes.append(f'<code class="nomeColuna">{coluna}</code>')

        linhas.append([f"<b>{tema}</b>", " ".join(nomes)])

    return deck.Slide(
        topico=TOPICO_DADOS,
        titulo=f"O clima entra como {total_de_colunas} variáveis, não como uma",
        rotulo_curto="As variáveis",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + '<p class="fonteDoSlide">Fonte: NASA POWER</p>'
        ),
        nota=(
            "Só situar a dimensão: o modelo não recebe 'o clima', recebe "
            f"<b>{total_de_colunas} colunas</b>. Não ler a tabela."
        ),
    )


def _slide_cenarios() -> deck.Slide:
    """O mapa dos experimentos, em versão enxuta para projetar."""
    resumo = pagina_de_cenarios.resumo_dos_cenarios()

    cabecalhos = ["#", "Cenário", "Alvo", "Modelos"]

    linhas = []
    for ordem, titulo, alvo, modelos in resumo:
        linhas.append(
            [
                f'<span class="num">{ordem}</span>',
                f"<b>{layout.escapar(titulo)}</b>",
                alvo,
                modelos,
            ]
        )

    return deck.Slide(
        topico=TOPICO_CENARIOS,
        titulo=f"{len(resumo)} cenários, cada um mudando um parâmetro por vez",
        rotulo_curto="9 testados",
        corpo=layout.montar_tabela(cabecalhos, linhas),
        nota=(
            "Não ler a tabela. Dizer que cada cenário isola <b>uma</b> "
            "mudança, e que por isso o algoritmo fica constante — exceto no "
            "cenário 3, onde a escolha do algoritmo é justamente a pergunta."
        ),
        e_denso=True,
    )


def _slide_adotado() -> deck.Slide:
    """Qual configuração ficou, e por quê.

    Este slide responde "qual modelo?". O desempenho dele é outra pergunta, e
    vive no tópico de resultados.
    """
    return deck.Slide(
        topico=TOPICO_CENARIOS,
        titulo="A configuração adotada, e como ela foi escolhida",
        rotulo_curto="Adotado",
        corpo=(
            pagina_do_cenario_adotado.tabela_da_configuracao()
            + layout.montar_aviso(
                tom="info",
                rotulo="O que é perda quantílica em 0,85",
                texto=(
                    "A previsão não é a <b>média esperada</b> de casos: é um "
                    "<b>patamar ultrapassado em cerca de 15% das semanas</b>. "
                    "Enviesado para cima de propósito, porque subestimar um "
                    "surto custa mais caro do que superestimar."
                ),
            )
        ),
        nota=(
            "Aqui é <b>qual modelo</b>, não quanto ele acerta. O desempenho vem "
            "no próximo tópico. A frase que importa: 'a melhor entre as "
            f"{numeros.TOTAL_DE_CONFIGURACOES_TESTADAS} testadas', nunca 'a "
            "melhor possível'."
        ),
    )


def _slide_resultados() -> deck.Slide:
    """O desempenho da configuração adotada na previsão de casos."""
    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="Prevendo o número de casos",
        rotulo_curto="Casos de dengue",
        corpo=(
            pagina_do_cenario_adotado.tabela_do_desempenho()
            + pagina_do_cenario_adotado.graficos_do_desempenho()
        ),
        nota=(
            "Apontar o formato das três curvas: o erro sobe, o R² cai, a "
            "captura do pico cai. E a causa é medida — a memória da própria "
            "série explica <b>91%</b> em uma semana e <b>0%</b> em três meses."
        ),
        e_denso=True,
    )


def _slide_alarme() -> deck.Slide:
    """O mesmo modelo lido como alarme de surto, nos quatro horizontes."""
    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="O modelo como alarme de surto",
        rotulo_curto="Alarme de surto",
        corpo=(
            pagina_do_cenario_adotado.tabela_do_alarme()
            + pagina_do_cenario_adotado.graficos_do_alarme()
        ),
        nota=(
            "A pergunta muda: não é acertar o tamanho, é acertar se a epidemia "
            "<b>chegou</b>. Dizer <b>alarme de surto</b>, nunca 'alarme de "
            f"pico'. Ressalva: só {numeros.ALARME.episodios_na_avaliacao} "
            "episódios na avaliação."
        ),
        e_denso=True,
    )


def _slide_o_vetor() -> deck.Slide:
    """A relação vetor-casos que se vê no gráfico, e que o modelo ainda não capta.

    ⚠️ Este é o slide mais delicado da apresentação, e o enquadramento é
    deliberado. O que foi medido é que as comparações feitas até aqui não
    capturaram ganho do vetor. Daí NÃO se deduz que o mosquito não ajude —
    sem vetor não há transmissão, e o padrão está visível no gráfico. A leitura
    honesta é que o desenho atual não alcança a relação, e isso é limitação do
    modelo, não ausência do fenômeno.

    Nunca dizer "o vetor não ajuda" nem "não deu correlação": as duas frases
    afirmam mais do que a medição sustenta, e é justamente o que o orientador
    pediu para evitar em 21/09/2026.
    """
    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="A relação existe no gráfico — o modelo ainda não a captura",
        rotulo_curto="O vetor",
        corpo=(
            '<div class="deckFiguraCheia">'
            '<img src="imagens/slide_vetor_vs_casos_anotado.png" '
            'alt="Aedes aegypti capturados e casos confirmados de dengue, '
            'com a subida de cada série marcada por seta">'
            + layout.montar_aviso(
                "atencao",
                "Limitação do modelo",
                "Setas azuis: subida do <b>mosquito</b>. Vermelhas: subida "
                "dos <b>casos</b>. O padrão está nas quatro temporadas — e o "
                "modelo <b>ainda não consegue agregar essa relação</b>.",
            )
            + "</div>"
        ),
        nota=(
            "⚠️ <b>O slide mais delicado.</b> Dizer: o padrão está no gráfico, o "
            "modelo ainda não o alcança, e isso é <b>limitação do desenho</b> — "
            "alvo na consequência, horizonte curto, histórico de casos ocupando "
            "o lugar do vetor. <b>Nunca</b> dizer 'não ajuda' ou 'não deu "
            "correlação'."
        ),
        e_figura=True,
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
        rotulo_curto="A direção",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_virada(
                (
                    "Atual",
                    "Modelo de previsão de <b>surto de dengue</b>",
                ),
                (
                    "Futuro",
                    "Modelo de previsão de <b>doenças transmitidas "
                    "pelo mesmo vetor</b>",
                ),
                (
                    "O que entra junto",
                    "Dados das <b>outras arboviroses</b>, agregados ao modelo",
                ),
            )
        ),
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
        _slide_vetor_e_casos(),
        _slide_clima(),
        _slide_colunas_de_clima(),
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
