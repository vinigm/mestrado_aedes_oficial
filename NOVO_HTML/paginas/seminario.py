"""Página do Seminário de Andamento: a apresentação em slides.

O formato foi pedido pelo orientador em 21/09/2026: **até 10 minutos**,
cobrindo problema, importância, metodologia, resultados e próximos passos, com
o **último slide de direcionamentos**.

Dez slides, um minuto cada. Cada slide defende uma frase só — a frase está no
título, e o corpo existe para sustentá-la.

⚠️ Instrução direta do orientador, que manda no tom dos slides 7 e 8: não
chegar à banca dizendo "não teve correlação com mosquito ou clima". O achado
negativo aparece, porque escondê-lo seria desonesto, mas enquadrado pelo que
ele de fato significa — e seguido da leitura de que o desenho atual
provavelmente não captura um efeito que existe.
"""

import deck
import layout
import numeros_do_projeto as numeros


def _slide_capa() -> deck.Slide:
    """Abertura: a pergunta da pesquisa e a identificação."""
    return deck.Slide(
        rotulo="",
        titulo="Modelo preditivo de casos de dengue em Porto Alegre",
        corpo=(
            "<p>A partir da captura de mosquito das armadilhas municipais, "
            "do clima e do histórico de notificação.</p>"
            "<p><b>Vinicius Guerra</b> · Seminário de Andamento<br>"
            "PPGC — UFRGS · Orientação: Prof. Weverton Cordeiro</p>"
        ),
        nota=(
            "Abrir dizendo que a rede existe, custa caro e ninguém tinha medido "
            "se ela antecipa a doença. <b>Dez minutos, dez slides.</b>"
        ),
    )


def _slide_o_problema() -> deck.Slide:
    """O que a cidade faz hoje, e o que ninguém tinha medido."""
    cartoes = [
        layout.montar_cartao(
            rotulo="A rede",
            titulo=f"{numeros.formatar_inteiro(numeros.BASE.armadilhas)} armadilhas",
            corpo=f"<p>em {numeros.BASE.bairros} bairros, lidas toda semana</p>",
        ),
        layout.montar_cartao(
            rotulo="O custo",
            titulo="Campo semanal",
            corpo="<p>agentes recolhem e contam, há mais de uma década</p>",
        ),
        layout.montar_cartao(
            rotulo="A pergunta",
            titulo="Ela antecipa?",
            corpo="<p>e, se antecipa, com quanto tempo?</p>",
        ),
    ]

    return deck.Slide(
        rotulo="O problema",
        titulo="Porto Alegre mede o mosquito toda semana — e nunca mediu se isso antecipa a dengue",
        corpo=layout.montar_grade(cartoes, colunas=3),
        nota=(
            "Um minuto. O ponto é que a rede <b>já existe e já custa</b>: a "
            "pergunta não é se vale a pena criá-la, é o que ela entrega."
        ),
    )


def _slide_por_que_importa() -> deck.Slide:
    """A latência do caso, e o que ela impõe à vigilância."""
    return deck.Slide(
        rotulo="Por que importa",
        titulo="Quando a curva de casos sobe, a transmissão já aconteceu",
        corpo=(
            layout.montar_fluxo(
                [
                    ("Picada", "a transmissão acontece"),
                    ("Sintoma", "dias depois"),
                    ("Atendimento", "se a pessoa procurar"),
                    ("Notificação", "e só então o caso existe no sistema"),
                ]
            )
            + layout.montar_aviso(
                tom="atencao",
                rotulo="A consequência prática",
                texto=(
                    "Agir quando o surto aparece é <b>agir tarde</b>. O valor de "
                    "uma previsão está em avisar cedo o bastante para que a "
                    "resposta ainda mude o resultado."
                ),
            )
        ),
        nota=(
            "Este slide justifica a tese inteira. Sem ele, a banca não entende "
            "por que antecipar importa mais do que acertar o tamanho."
        ),
    )


def _slide_os_dados() -> deck.Slide:
    """A contribuição mais sólida: a série reunida e certificada."""
    intervalo = f"{numeros.BASE.primeira_semana} a {numeros.BASE.ultima_semana}"

    return deck.Slide(
        rotulo="Contribuição · dados",
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
                    f"Faltam <b>{numeros.BASE.semanas_faltantes} semanas em 14 "
                    f"anos</b>, {numeros.BASE.semanas_perdidas_na_enchente} delas "
                    "a enchente de maio de 2024. A série não existia reunida: "
                    "foi recuperada junto à Secretaria, corrigida e documentada."
                ),
            )
        ),
        nota=(
            "Se a banca só levar uma coisa, que seja esta. É o que o trabalho "
            "entrega <b>independentemente</b> do resultado da modelagem."
        ),
    )


def _slide_o_metodo() -> deck.Slide:
    """Como a avaliação simula o uso real."""
    return deck.Slide(
        rotulo="Metodologia",
        titulo="O modelo nunca vê o futuro que tenta prever",
        corpo=(
            layout.montar_figura(
                arquivo="imagens/walkforward.png",
                titulo="",
                subtitulo="",
                legenda="",
            )
            + layout.montar_aviso(
                tom="info",
                rotulo="E nada vira afirmação sem sobreviver à correção",
                texto=(
                    "Toda rodada é <b>pré-declarada por escrito antes</b>, e "
                    "nenhum resultado é chamado de significativo sem passar pela "
                    "correção de múltiplas comparações."
                ),
            )
        ),
        nota=(
            "Falar rápido: treina só com o passado, avança no tempo, repete. "
            "A parte que importa é a <b>pré-declaração</b> — é o que separa "
            "achado de garimpo."
        ),
    )


def _slide_desempenho() -> deck.Slide:
    """Até onde a previsão alcança."""
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
        rotulo="Resultados · previsão",
        titulo="O modelo é honesto até um mês, e perde força em três",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                tom="bom",
                rotulo="A degradação tem causa medida",
                texto=(
                    "A memória da própria série de casos explica <b>91%</b> do "
                    "acerto em uma semana e <b>0%</b> em três meses. Não é "
                    "defeito de ajuste: em três meses o passado recente não "
                    "informa mais."
                ),
            )
        ),
        nota=(
            "Não pedir desculpa pela queda — <b>explicá-la</b>. A causa medida "
            "é o que transforma um número ruim em achado."
        ),
    )


def _slide_alarme() -> deck.Slide:
    """O modelo lido como alarme, que é o uso operacional."""
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
        rotulo="Resultados · alarme",
        titulo="Como alarme de surto, ele acerta 97% das semanas a um mês",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                tom="atencao",
                rotulo="Ressalva que limita a leitura",
                texto=(
                    f"A avaliação contém apenas <b>{numeros.ALARME.episodios_na_avaliacao} "
                    "episódios</b> de surto. Nada por episódio pode ser afirmado."
                ),
            )
        ),
        nota=(
            "Aqui muda a pergunta: não é acertar o tamanho, é acertar que a "
            "epidemia <b>chegou</b>. Para vigilância, é a segunda que importa."
        ),
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
                    "casos</b>, a contagem de armadilha não melhora a previsão "
                    f"em nenhuma das {numeros.VETOR.comparacoes_pareadas} "
                    "comparações que sobrevivem à correção.</p>"
                ),
            ),
            layout.montar_cartao(
                rotulo="O que isso NÃO significa",
                titulo="",
                corpo=(
                    "<p>Que o mosquito não importa. <b>Sem vetor não há "
                    "transmissão</b> — e a subida da captura aparece "
                    "<b>antes</b> da subida dos casos, temporada após "
                    "temporada.</p>"
                ),
            ),
        ],
        colunas=2,
    )

    return deck.Slide(
        rotulo="Resultados · o vetor",
        titulo="A armadilha não adiciona sobre clima e histórico — e isso pede explicação, não conclusão",
        corpo=(
            contraste
            + layout.montar_aviso(
                tom="info",
                rotulo="A leitura mais provável",
                texto=(
                    "Um resultado nulo diante de um padrão visível e "
                    "biologicamente esperado aponta menos para ausência de "
                    "efeito e mais para <b>um efeito que o desenho atual não "
                    "captura</b>: o alvo é a consequência, o horizonte para em "
                    "três meses, e o histórico de casos ocupa o lugar do vetor."
                ),
            )
        ),
        nota=(
            "⚠️ <b>O slide mais delicado.</b> Nunca dizer 'não deu correlação'. "
            "Dizer: medimos isto, sob estas condições, e a explicação mais "
            "provável é que o desenho não alcança o efeito. O próximo slide "
            "mostra o que fazer a respeito."
        ),
    )


def _slide_limites() -> deck.Slide:
    """O que o trabalho não pode afirmar, dito antes que perguntem."""
    return deck.Slide(
        rotulo="Honestidade",
        titulo="O que este trabalho ainda não pode afirmar",
        corpo=layout.montar_lista(
            [
                "Que <b>o vetor melhora</b> a previsão de casos — 0 de "
                f"{numeros.VETOR.comparacoes_pareadas} sobrevivem à correção.",
                "Que <b>clima e vetor são equivalentes</b> — fecha "
                f"{numeros.LIMITES.equivalencia_clima_vetor_fechada} de "
                f"{numeros.LIMITES.equivalencia_clima_vetor_testada}.",
                "Que <b>estas variáveis de clima são as que importam</b> — "
                f"recortando a série, {numeros.LIMITES.colunas_de_clima_que_mudam_ao_recortar} "
                f"das {numeros.LIMITES.colunas_de_clima_total} mudam.",
                "Nada <b>por episódio de surto</b> — só há "
                f"{numeros.ALARME.episodios_na_avaliacao} na avaliação.",
            ]
        ),
        nota=(
            "Dizer isto <b>antes</b> que a banca pergunte. Mostra domínio do "
            "próprio limite, e tira da mesa a pergunta difícil."
        ),
    )


def _slide_direcionamentos() -> deck.Slide:
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
        rotulo="Direcionamentos",
        titulo="Deslocar a pergunta da consequência para a causa",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                tom="bom",
                rotulo="E um teste guardado",
                texto=(
                    "Prever agora a curva de captura da temporada "
                    "<b>2026-2027</b> e conferir contra o real em <b>julho de "
                    "2027</b> — previsão registrada antes, sem ajuste posterior."
                ),
            )
        ),
        nota=(
            "Fechar aqui. Este slide saiu da reunião de "
            f"{numeros.DATA_DA_REUNIAO_DE_ALINHAMENTO} e é o que a banca vai "
            "comentar."
        ),
    )


def montar_slides() -> list[deck.Slide]:
    """Os dez slides da apresentação, na ordem."""
    return [
        _slide_capa(),
        _slide_o_problema(),
        _slide_por_que_importa(),
        _slide_os_dados(),
        _slide_o_metodo(),
        _slide_desempenho(),
        _slide_alarme(),
        _slide_o_vetor(),
        _slide_limites(),
        _slide_direcionamentos(),
    ]


def montar_metricas() -> list[layout.Metrica]:
    """Sem régua: o palco do deck começa logo abaixo do título."""
    return []


def montar_corpo() -> str:
    """Só o deck: a página inteira é a apresentação."""
    return deck.montar(montar_slides())
