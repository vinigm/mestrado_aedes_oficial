"""Cópia de trabalho do Seminário de Andamento.

⚠️ **Esta é uma cópia literal de `seminario.py`, criada em 26/09/2026.** O
arquivo original fica intacto: é ele que vai ao ar se o Vinicius decidir usar a
versão de 23/09/2026. Esta cópia existe para ser modificada à vontade, sem
risco de estragar aquela.

Tudo abaixo é idêntico ao original no momento da cópia.

---

Página do Seminário de Andamento: a apresentação em slides.

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
    """Qual configuração ficou, com que hiperparâmetros, e por quê.

    Este slide responde "qual modelo?". O desempenho dele é outra pergunta, e
    vive no tópico de resultados.

    ⚠️ **Mudado em 26/09/2026.** A ficha vinha de `cenario_adotado.py`, que
    também alimenta a página publicada e o deck original — por isso a tabela é
    montada aqui, e não lá: mexer no módulo compartilhado mudaria os três.

    Duas correções em relação à versão de 23/09:

    1. **Os hiperparâmetros passam a aparecer.** Eles faltavam, e a folha
       mínima é justamente o parâmetro que decide se o vetor ajuda — o que o
       slide do vetor agora afirma.
    2. **A validação era descrita como "prevê uma semana à frente"**, e o
       modelo prevê de 1 a 12. A frase também não dizia que o corte é pela data
       da RESPOSTA, que é a correção de 13/09/2026 e custou +52% de erro.

    Os valores vêm de `modelagem_aedes/config/experimentos/cidade_referencia.py`.
    """
    cabecalhos = ["Característica", "Valor"]
    linhas = [
        ["Algoritmo", "<b>HistGradientBoostingRegressor</b> (scikit-learn)"],
        ["Função de perda", "perda quantílica, quantil <b>0,85</b>"],
        [
            "Hiperparâmetros",
            "<code>max_iter</code> 250 · <code>learning_rate</code> 0,05 · "
            "<code>max_leaf_nodes</code> 15 · "
            "<b><code>min_samples_leaf</code> 5</b>",
        ],
        ["Variáveis", "núcleo + clima + <b>variáveis do vetor</b> (mosquito)"],
        ["Alvo", "casos de dengue <b>confirmados</b> (SINAN), nível cidade"],
        [
            "Selecionada por",
            f"menor erro de calibração entre <b>{numeros.TOTAL_DE_CONFIGURACOES_TESTADAS}"
            "</b> configurações (3 algoritmos × 5 perdas × com/sem vetor)",
        ],
        [
            "Validação",
            "<b>walk-forward</b>: treina só com o que já tinha <b>resposta</b> "
            "na data da previsão, prevê de <b>1 a 12 semanas</b> à frente, avança "
            "uma semana e repete",
        ],
    ]
    return deck.Slide(
        topico=TOPICO_CENARIOS,
        titulo="A configuração adotada, e como ela foi escolhida",
        rotulo_curto="Adotado",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
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
            "Aqui é <b>qual modelo</b>, não quanto ele acerta. A frase que "
            f"importa: 'a melhor entre as {numeros.TOTAL_DE_CONFIGURACOES_TESTADAS} "
            "testadas', nunca 'a melhor possível'. Se perguntarem da <b>folha "
            "mínima 5</b>: é ela que separa esta configuração da que extrai ganho "
            "do vetor, no slide do vetor. <b>Cortar pela data da resposta</b> é a "
            "correção de 13/09 — cortar pela data da pergunta custava +52% de erro."
        ),
        e_denso=True,
    )


def _slide_resultados() -> deck.Slide:
    """O desempenho da configuração adotada na previsão de casos."""
    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="Prevendo o número de casos",
        rotulo_curto="Casos de dengue",
        corpo=(
            layout.montar_aviso(
                "info",
                "Medido em",
                f"<b>{numeros.SEMANAS_POR_HORIZONTE_NAS_COMPARACOES} semanas</b> de "
                f"avaliação, de <b>{numeros.PERIODO_DE_AVALIACAO_DAS_COMPARACOES}</b>, "
                "pareadas por data-alvo.",
            )
            + pagina_do_cenario_adotado.tabela_do_desempenho()
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
    """A relação vetor-casos, e o que o modelo já faz com ela.

    ⚠️ **Corrigido em 26/09/2026.** A versão anterior deste slide dizia que o
    modelo "ainda não captura" a relação. A bateria de 24/09/2026 mostrou que
    isso afirma menos do que a medição sustenta, em dois pontos:

    1. O modelo adotado **usa** o vetor com peso — a partir de 1 mês à frente,
       depende mais dele do que do próprio histórico de casos.
    2. Trocando **um único hiperparâmetro** — a folha mínima, de 5 para 20 — o
       vetor passa a **reduzir** o erro de 3 meses, com significância.

    O que continua verdadeiro é que o cenário adotado, com folha 5, não extrai
    ganho do vetor. Isso é escolha de configuração, não ausência do fenômeno.

    Nunca dizer "o vetor não ajuda" nem "não deu correlação": as duas frases
    afirmam mais do que a medição sustenta, e é o que o orientador pediu para
    evitar em 21/09/2026.
    """
    cabecalhos = ["Configuração", "Queda do erro em 3 meses com o vetor", "p de Holm"]
    linhas = [
        ["HistGB, folha 5 — <b>o cenário adotado</b>", "+2,2%", "não significativo"],
        ["HistGB, folha <b>20</b>", "<b>+12,3%</b>", "<b>0,015</b>"],
        ["LightGBM, folha <b>20</b>", "<b>+15,5%</b>", "<b>0,0001</b>"],
    ]
    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="O modelo usa o vetor — e com outro hiperparâmetro, ele reduz o erro",
        rotulo_curto="O vetor",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                "bom",
                "Fato medido em 24/09/2026",
                "A partir de <b>1 mês</b> à frente, o modelo adotado já depende "
                "<b>mais do vetor</b> do que do histórico de casos: embaralhar as "
                "colunas do mosquito aumenta o erro de <b>46% a 73%</b>; embaralhar "
                "o histórico de casos, de <b>20% a 47%</b>.",
            )
            + layout.montar_aviso(
                "atencao",
                "Ressalva que vai junto",
                "O ganho da folha 20 é <b>exploratório</b> e carregado pela "
                "temporada de <b>2024</b>. Em 2025 ele só se repete com "
                "significância no LightGBM, em 11 e 12 semanas.",
            )
        ),
        nota=(
            "⚠️ <b>O slide mais delicado, e ele mudou.</b> A mensagem agora é: o "
            "modelo <b>usa</b> o mosquito, e a configuração adotada é que não "
            "extrai ganho dele. <b>Nunca</b> dizer 'não ajuda' ou 'não deu "
            "correlação'. Se perguntarem por que não adotamos a folha 20: porque "
            "o critério de escolha do projeto olha a calibração de 2020-2023, e "
            "ali a folha 20 é ~30% pior — é pendência declarada, não descuido."
        ),
        e_denso=True,
    )


def _slide_a_defasagem() -> deck.Slide:
    """O atraso entre a curva do mosquito e a dos casos.

    Slide novo, de 26/09/2026. Existe porque a figura do slide anterior
    mostrava a defasagem a olho nu e a apresentação nunca a nomeava — e o
    estudo da mesma cidade a mediu, enquanto nós não.
    """
    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="A subida do mosquito vem antes da subida dos casos",
        rotulo_curto="A defasagem",
        corpo=(
            '<div class="deckFiguraCheia">'
            '<img src="imagens/vetor_vs_casos.png" '
            'alt="Aedes aegypti capturados e casos confirmados de dengue, '
            'semana a semana">'
            + layout.montar_aviso(
                "atencao",
                "Leitura de gráfico, não medição nossa",
                "A ordem entre as duas curvas se repete nas temporadas, mas "
                "<b>nós não estimamos a defasagem</b>. Quem estimou foi o estudo "
                "da mesma cidade e da mesma armadilha (da Silva et al. 2026): a "
                "correlação com os casos sobe de <b>0,27</b> sem atraso para "
                "<b>0,50</b> com <b>4 semanas</b> de atraso.",
            )
            + "</div>"
        ),
        nota=(
            "Estender a memória do vetor para 6 a 12 semanas <b>não</b> ajudou "
            "(bateria de 24/09) — o gargalo não é quanto passado do vetor o "
            "modelo enxerga. Estimar a defasagem é próximo passo declarado."
        ),
        e_figura=True,
    )



def _slide_proximos_passos() -> deck.Slide:
    """O último slide, como o orientador pediu."""
    cabecalhos = ["", "Hoje", "Próxima etapa"]
    # A cor separa os dois cenários que a tabela compara: azul é o que o
    # projeto faz hoje, verde é para onde ele vai.
    CORES_DAS_COLUNAS = ["", layout.COLUNA_AZUL, layout.COLUNA_VERDE]
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
        corpo=layout.montar_tabela(cabecalhos, linhas, CORES_DAS_COLUNAS),
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
        _slide_o_que_o_projeto_faz(),
        _slide_vetor_e_casos(),
        _slide_clima(),
        _slide_colunas_de_clima(),
        _slide_cenarios(),
        _slide_adotado(),
        _slide_resultados(),
        _slide_alarme(),
        _slide_o_vetor(),
        _slide_a_defasagem(),
        _slide_proximos_passos(),
    ]


def montar_metricas() -> list[layout.Metrica]:
    """Sem régua: o palco do deck ocupa a página."""
    return []


def montar_corpo() -> str:
    """Só o deck: a página inteira é a apresentação."""
    return deck.montar(montar_slides())
