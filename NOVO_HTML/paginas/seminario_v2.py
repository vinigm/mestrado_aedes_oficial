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
import graficos
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
ROTULOS_DOS_HORIZONTES = ("1 semana", "1 mês", "2 meses", "3 meses")


def _destacar(texto_da_celula: str, em_destaque: bool) -> str:
    """Poe a celula em negrito quando ela e a melhor da comparacao.

    Args:
        texto_da_celula: O valor ja formatado.
        em_destaque: True quando esta celula vence a comparacao da linha.

    Returns:
        A celula, com ou sem negrito.
    """
    if em_destaque:
        return f"<b>{texto_da_celula}</b>"

    return texto_da_celula


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


def _slide_folha_5_contra_folha_20() -> deck.Slide:
    """As duas configurações lado a lado, e o ganho do vetor dentro da folha 20.

    Slide novo de 26/09/2026. Existe porque a apresentação mostrava só a
    configuração adotada, e a bateria de 23-24/09/2026 mediu uma segunda que
    vai melhor em horizonte longo — e que é a única das duas que extrai ganho
    das colunas do vetor.
    """
    por_braco = {}
    for linha in numeros.PAINEL_DO_COMPOSTO:
        por_braco.setdefault(linha.braco, {})[linha.rotulo] = linha

    rotulos = list(ROTULOS_DOS_HORIZONTES)
    cabecalhos_do_erro = ["Horizonte", "Adotado · folha 5", "Folha 20, com vetor"]
    linhas_do_erro = []
    for rotulo in rotulos:
        erro_adotado = por_braco[numeros.NOME_DO_ADOTADO][rotulo].erro_medio_absoluto
        erro_folha20 = por_braco[numeros.NOME_DA_FOLHA_20][rotulo].erro_medio_absoluto
        melhor_e_adotado = erro_adotado < erro_folha20
        linhas_do_erro.append(
            [
                f"<b>{layout.escapar(rotulo)}</b>",
                _destacar(numeros.formatar_decimal(erro_adotado, 1), melhor_e_adotado),
                _destacar(
                    numeros.formatar_decimal(erro_folha20, 1), not melhor_e_adotado
                ),
            ]
        )

    cabecalhos_do_vetor = ["Horizonte", "Ganho do vetor na folha 20", "p de Holm"]
    linhas_do_vetor = []
    for rotulo, ganho, p_holm in numeros.GANHO_DO_VETOR_NA_FOLHA_20:
        significativo = p_holm < 0.05
        linhas_do_vetor.append(
            [
                f"<b>{layout.escapar(rotulo)}</b>",
                _destacar(f"{numeros.formatar_decimal(ganho, 1)}%", significativo),
                _destacar(numeros.formatar_decimal(p_holm, 4), significativo),
            ]
        )

    return deck.Slide(
        topico=TOPICO_CENARIOS,
        titulo="Um único hiperparâmetro troca qual horizonte o modelo acerta",
        rotulo_curto="Folha 5 × 20",
        corpo=(
            "<p class='deckLegenda'><b>Erro médio, em casos por semana</b> — menor é melhor</p>"
            + layout.montar_tabela(cabecalhos_do_erro, linhas_do_erro)
            + "<p class='deckLegenda'><b>E o que o vetor rende dentro da folha 20</b></p>"
            + layout.montar_tabela(cabecalhos_do_vetor, linhas_do_vetor)
        ),
        nota=(
            "<b>Folha mínima</b> é o número mínimo de semanas por folha da "
            "árvore. Folha 5 fica detalhista e acerta o curto prazo; folha 20 "
            "é obrigada a achar padrão que se repete, e acerta o longo. É por "
            "isso que só ela aproveita o vetor: o sinal do mosquito é "
            "estrutural, não é ruído semanal."
        ),
        e_denso=True,
    )


# As tres medidas do painel, cada uma com a sua cor — as mesmas do slide de
# resultados, para que tabela e grafico se liguem sem legenda. A regua sazonal
# tem cor propria, cinza, e linha pontilhada: ela e REFERENCIA, nao resultado.
# O quarto item de cada medida e o horizonte em que a regua sazonal PASSA a
# vencer o composto naquela medida, medido nos 12 horizontes em
# `analises/2026-09-26_modelo_composto/`. Ate 4 semanas o composto ganha nas
# tres; depois disso, nao.
MEDIDAS_DO_COMPOSTO = (
    ("R² (o quanto explica)", "r2", 3, "#1B6EF3", 6, numeros.POSICAO_DO_R2),
    ("Erro médio (casos/semana)", "erro_medio_absoluto", 1, "#C0392B", 5, numeros.POSICAO_DO_MAE),
    ("Captura do pico", "captura_do_pico", 3, "#1F7A4D", 6, numeros.POSICAO_DA_CAPTURA),
)
COR_DA_REGUA_SAZONAL = "#8A94A6"
NOME_DA_LINHA_DA_REGUA = "Régua sazonal"


def _celula_colorida(conteudo: str, cor: str) -> str:
    """Poe a celula na cor da medida, ligando coluna e grafico."""
    return f'<span style="color:{cor}">{conteudo}</span>'


def _celula_colorida_com_destaque(valor: str, cor: str, em_destaque: bool) -> str:
    """Celula colorida que pode vir em negrito sem perder a cor.

    ⚠️ Por que nao basta embrulhar `_destacar` em `_celula_colorida`: o tema
    tem uma regra global `strong, b {color: var(--tinta)}` que sobrepoe a cor
    herdada do span pai, e o valor sairia preto. A cor precisa estar no PROPRIO
    elemento em negrito, como estilo inline, para vencer a regra da folha.

    Args:
        valor: O numero ja formatado.
        cor: A cor da medida, a mesma da coluna e do grafico.
        em_destaque: True quando esta celula vence a comparacao da linha.

    Returns:
        O HTML da celula.
    """
    if em_destaque:
        return f'<b style="color:{cor}">{valor}</b>'

    return _celula_colorida(valor, cor)


def _grafico_de_uma_medida(
    rotulo_do_eixo: str,
    atributo: str,
    cor: str,
    horizonte_em_que_a_regua_passa: int,
    posicao_da_medida: int,
) -> str:
    """Desenha uma medida ao longo dos horizontes, com a regua pontilhada.

    Args:
        rotulo_do_eixo: Texto do eixo vertical, tambem usado no titulo.
        atributo: Campo de `DesempenhoDeUmBraco` a ler.
        cor: Cor da linha do composto, a mesma da coluna na tabela.
        horizonte_em_que_a_regua_passa: A partir de quantas semanas a regua
            sazonal passa a vencer o composto nesta medida. Vira uma linha
            vertical pontilhada no grafico.
        posicao_da_medida: Indice desta medida dentro das tuplas de 12
            horizontes em `numeros_do_projeto`.

    Returns:
        O HTML do grafico.
    """
    pontos_do_composto = [
        (float(linha[0]), linha[posicao_da_medida])
        for linha in numeros.COMPOSTO_NOS_12_HORIZONTES
    ]
    pontos_da_regua = [
        (float(linha[0]), linha[posicao_da_medida])
        for linha in numeros.REGUA_NOS_12_HORIZONTES
    ]

    return graficos.montar_grafico_de_linhas(
        {"Composto": pontos_do_composto, NOME_DA_LINHA_DA_REGUA: pontos_da_regua},
        "horizonte (semanas)",
        rotulo_do_eixo,
        cores=[cor, COR_DA_REGUA_SAZONAL],
        series_tracejadas={NOME_DA_LINHA_DA_REGUA},
        marco_vertical=(
            float(horizonte_em_que_a_regua_passa),
            f"a régua passa a vencer · {horizonte_em_que_a_regua_passa} sem",
        ),
    )


def _slide_modelo_composto() -> deck.Slide:
    """O composto, no mesmo formato do slide de resultados.

    Tres medidas, tres cores, tres graficos lado a lado — e em cada grafico a
    regua sazonal aparece na mesma medida, em cinza e pontilhada, para deixar
    claro que ela e referencia e nao um quarto resultado.

    ⚠️ Refeito em 26/09/2026: a versao anterior punha as tres linhas num
    grafico so, todas medindo erro medio, e a coluna da regua na tabela ficava
    ao lado do R2 como se fosse outra metrica. Confundia.
    """
    por_braco = {}
    for linha in numeros.PAINEL_DO_COMPOSTO:
        por_braco.setdefault(linha.braco, {})[linha.rotulo] = linha

    cabecalhos = ["Horizonte"] + [
        _celula_colorida(rotulo, cor) for rotulo, _, _, cor, _, _ in MEDIDAS_DO_COMPOSTO
    ]
    linhas = []
    for rotulo in ROTULOS_DOS_HORIZONTES:
        do_composto = por_braco[numeros.NOME_DO_COMPOSTO][rotulo]
        celulas = [f"<b>{layout.escapar(rotulo)}</b>"]
        for _, atributo, casas, cor, _, _ in MEDIDAS_DO_COMPOSTO:
            valor = getattr(do_composto, atributo)
            formatado = (
                numeros.formatar_percentual(valor, 1)
                if atributo == "captura_do_pico"
                else numeros.formatar_decimal(valor, casas)
            )
            celulas.append(_celula_colorida(formatado, cor))
        linhas.append(celulas)

    graficos_das_medidas = "".join(
        _grafico_de_uma_medida(rotulo, atributo, cor, cruzamento, posicao)
        for rotulo, atributo, _, cor, cruzamento, posicao in MEDIDAS_DO_COMPOSTO
    )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="O modelo composto, e onde ele ainda perde",
        rotulo_curto="Composto",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + '<p class="deckNotaDeGrafico">⚠️ O ponto de corte entre as duas '
            "configurações foi escolhido olhando o período de avaliação — "
            "adotá-lo exige pré-declarar o critério e repetir a medição.</p>"
            + f'<div class="graficosLadoALado">{graficos_das_medidas}</div>'
        ),
        nota=(
            "O composto vence a régua em <b>1 semana</b> e <b>1 mês</b>. Em 2 e 3 "
            "meses a régua ainda vence: a distância cai de 28% para <b>12%</b>, e "
            "não fecha. ⚠️ <b>Dizer que ainda não é adotável</b>: o ponto de corte "
            "entre as configurações foi escolhido olhando o período de avaliação, "
            "que é o mesmo que julga. Se perguntarem o que é a linha pontilhada: "
            "é a <b>régua sazonal</b> na mesma medida do gráfico — repetir o número "
            "da mesma semana do ano passado. Ela <b>não olha o mosquito nem o clima</b>."
        ),
        e_denso=True,
    )


def _slide_do_modelo_ao_alarme() -> deck.Slide:
    """Slide de transicao: o modelo de previsao vira um sistema de alerta.

    Slide novo de 26/09/2026, desenhado pelo Vinicius. Ele e deliberadamente
    simples — dois blocos e uma seta. A funcao dele e anunciar a virada antes
    de os numeros aparecerem, para que os tres slides seguintes (limiares do
    plano, alarme do composto, e a objecao da regua) sejam lidos como uma
    sequencia, e nao como assuntos soltos.
    """
    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="Do modelo de previsão para um sistema de alerta",
        rotulo_curto="A virada",
        corpo=(
            '<div class="deckFluxoDeDois">'
            '<div class="deckFluxoBloco">'
            '<div class="deckFluxoTitulo">Modelo de previsão</div>'
            '<div class="deckFluxoTexto">quantos casos haverá<br>daqui a 1 a 3 meses</div>'
            "</div>"
            '<div class="deckFluxoSeta">&rarr;</div>'
            '<div class="deckFluxoBloco destaque">'
            '<div class="deckFluxoTitulo">Alarme de alerta</div>'
            '<div class="deckFluxoTexto">em que estágio de resposta<br>'
            "a cidade vai estar</div>"
            "</div></div>"
        ),
        nota=(
            "A frase: <b>pegamos as previsões do modelo e construímos um sistema de "
            "alerta com elas.</b> Não é desistir da previsão — é usá-la para responder "
            "a pergunta que a vigilância faz. Os próximos três slides são: de onde vêm "
            "os limiares, como o alarme se sai, e por que não usar só a régua."
        ),
    )


def _slide_estagios_do_plano() -> deck.Slide:
    """O Quadro 1 do plano municipal, e a tradução dele para casos por semana.

    Slide novo de 26/09/2026. Ele existe para responder, antes que perguntem,
    de onde vem o limiar de 421 — e a resposta é que ele **não está no plano**:
    o plano declara uma taxa de incidência, e o 421 é a conversão dela para a
    população de Porto Alegre.

    Mostrar o quadro inteiro, e não só a linha do Alerta, é deliberado: prova
    que o 421 é o terceiro degrau de uma escala que já existia, e não um corte
    escolhido por nós.
    """
    cabecalhos = ["Estágio", "O plano declara", "Em Porto Alegre"]
    linhas = []
    for estagio in numeros.ESTAGIOS_DO_PLANO:
        e_o_alerta = estagio.estagio == numeros.NOME_DO_ESTAGIO_DO_ALARME
        linhas.append(
            [
                _destacar(layout.escapar(estagio.estagio), e_o_alerta),
                _destacar(layout.escapar(estagio.incidencia), e_o_alerta),
                _destacar(
                    f"{numeros.formatar_inteiro(estagio.casos_por_semana)} casos/semana",
                    e_o_alerta,
                ),
            ]
        )

    # A conta que leva da taxa do plano ao numero de casos, montada como
    # formula. As ressalvas sobre a unidade e sobre a metade fixa do criterio
    # saem da tela por decisao do Vinicius em 26/09 — ele diz em voz alta.
    a_conta = (
        '<div class="deckFormula">'
        '<span class="deckFormulaTermo">'
        '<span class="deckFormulaValor">30,0</span>'
        '<span class="deckFormulaRotulo">o que o plano diz</span></span>'
        '<span class="deckFormulaOperador">×</span>'
        '<span class="deckFormulaTermo">'
        '<span class="deckFracao">'
        f'<span class="deckFracaoTopo">{numeros.formatar_inteiro(numeros.POPULACAO_DE_PORTO_ALEGRE)}</span>'
        '<span class="deckFracaoBase">100.000</span></span>'
        '<span class="deckFormulaRotulo">população de Porto Alegre</span></span>'
        '<span class="deckFormulaOperador">=</span>'
        '<span class="deckFormulaTermo deckFormulaResultado">'
        f'<span class="deckFormulaValor">{numeros.formatar_inteiro(numeros.LIMIAR_DO_ALARME)}</span>'
        '<span class="deckFormulaRotulo">casos por semana</span></span>'
        "</div>"
    )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="O limiar não é nosso: é o estágio Alerta do plano da Prefeitura",
        rotulo_curto="Limiares oficiais",
        corpo=(
            '<div class="deckDuasColunas">'
            '<div><img src="imagens/quadro_1_plano_municipal.png" '
            'alt="Quadro 1 do Plano Municipal de Contingência de Arboviroses 2026, '
            'com os quatro estágios de resposta e seus indicadores">'
            '<p class="deckFonte">Plano Municipal de Contingência de Arboviroses '
            "2026 · Secretaria Municipal de Saúde de Porto Alegre · Quadro 1, "
            "página 15</p></div>"
            f"<div>{layout.montar_tabela(cabecalhos, linhas)}{a_conta}</div></div>"
        ),
        nota=(
            "Mostrar o quadro inteiro é de propósito: prova que o <b>421 é o terceiro "
            "degrau de uma escala que já existia</b>, e não um corte que escolhemos. "
            "⚠️ O número 421 <b>não aparece no PDF</b> — o plano diz 30,0, e a conversão "
            "é nossa. 🔴 <b>As duas ressalvas saíram da tela — você diz em voz alta:</b> "
            "(1) o plano escreve 30,0 <b>sem declarar a unidade</b>, e 'por 100 mil' é "
            "convenção nacional, inferência nossa; (2) o <b>E</b> está visível na imagem, "
            "ligando o corte a limiares estaduais — usamos só a metade fixa do critério."
        ),
        e_denso=True,
    )


# As tres medidas do alarme, cada uma com a sua cor — a mesma paleta das
# medidas de desempenho, para que o olho reconheca o padrao entre os slides.
# O quarto item e a posicao da medida nas tuplas de 12 horizontes.
MEDIDAS_DO_ALARME = (
    ("Pega quantos Alertas", "#1F7A4D", numeros.POSICAO_DA_SENSIBILIDADE, True),
    ("Precisão", "#1B6EF3", numeros.POSICAO_DA_PRECISAO, True),
    ("Alarmes falsos por ano", "#C0392B", numeros.POSICAO_DOS_FALSOS, False),
)


def _grafico_de_uma_medida_do_alarme(
    rotulo_do_eixo: str, cor: str, posicao_da_medida: int
) -> str:
    """Desenha uma medida do alarme ao longo dos 12 horizontes.

    A regua sazonal entra pontilhada, em cinza, como referencia — e o desenho
    dela mostra sozinho o argumento: ela e quase uma reta horizontal, porque
    repetir o ano anterior custa o mesmo em qualquer horizonte.

    ⚠️ Sem marco vertical aqui, ao contrario do slide do composto: o
    cruzamento das curvas cai em horizontes diferentes em cada medida (11 na
    sensibilidade, 3 na precisao), e tres marcos com significados diferentes na
    mesma tela confundiriam mais do que ajudariam.

    Args:
        rotulo_do_eixo: Texto do eixo vertical, tambem usado no titulo.
        cor: Cor da linha do composto, a mesma da coluna na tabela.
        posicao_da_medida: Indice da medida dentro das tuplas de 12 horizontes.

    Returns:
        O HTML do grafico.
    """
    pontos_do_composto = [
        (float(linha[0]), linha[posicao_da_medida])
        for linha in numeros.ALARME_DO_COMPOSTO_NOS_12
    ]
    pontos_da_regua = [
        (float(linha[0]), linha[posicao_da_medida])
        for linha in numeros.ALARME_DA_REGUA_NOS_12
    ]
    return graficos.montar_grafico_de_linhas(
        {"Composto": pontos_do_composto, NOME_DA_LINHA_DA_REGUA: pontos_da_regua},
        "horizonte (semanas)",
        rotulo_do_eixo,
        cores=[cor, COR_DA_REGUA_SAZONAL],
        series_tracejadas={NOME_DA_LINHA_DA_REGUA},
    )


def _slide_alarme_do_composto() -> deck.Slide:
    """O alarme do composto no limiar oficial, com tabela e os tres graficos.

    ⚠️ **Refeito em 26/09/2026.** A versao anterior tinha a tabela e um aviso
    explicando o que e uma semana de Alerta. O aviso saiu a pedido do Vinicius
    — ele diz em voz alta — e no lugar entraram tres graficos, no mesmo formato
    do slide do composto: uma cor por medida, ligando coluna e curva sem
    precisar de legenda.
    """
    por_braco = {}
    for linha in numeros.ALARME_DO_COMPOSTO:
        por_braco.setdefault(linha.braco, {})[linha.rotulo] = linha

    cores = [cor for _, cor, _, _ in MEDIDAS_DO_ALARME]
    cabecalhos = ["Horizonte"] + [
        _celula_colorida(rotulo, cor) for rotulo, cor, _, _ in MEDIDAS_DO_ALARME
    ]

    # Diferenca abaixo da qual os dois contam como empate. Os valores ja vem
    # arredondados a uma casa, entao comparar direto criaria "vencedor" onde ha
    # so ruido de arredondamento.
    empate = 0.001

    def valores_de(nome_do_braco: str, rotulo: str) -> tuple[float, float, float]:
        """As tres medidas de um braco num horizonte, na ordem das colunas."""
        medidas = por_braco[nome_do_braco][rotulo]
        return (medidas.sensibilidade, medidas.precisao, medidas.falsos_por_ano)

    def montar_tabela_de_um_braco(nome_do_braco: str, nome_do_outro: str) -> str:
        """Monta a tabela de um braco, com a celula vencedora em negrito.

        Args:
            nome_do_braco: O braco desta tabela.
            nome_do_outro: O braco da tabela ao lado, para saber quem vence.

        Returns:
            O HTML da tabela.
        """
        linhas_do_braco = []
        classes_das_linhas = []
        for rotulo in ROTULOS_DOS_HORIZONTES:
            meus = valores_de(nome_do_braco, rotulo)
            dele = valores_de(nome_do_outro, rotulo)
            celulas = [f"<b>{layout.escapar(rotulo)}</b>"]
            for meu, seu, (_, cor, _, maior_e_melhor) in zip(meus, dele, MEDIDAS_DO_ALARME):
                if maior_e_melhor:
                    eu_venco = meu - seu > empate
                    formatado = numeros.formatar_percentual(meu, 1)
                else:
                    eu_venco = seu - meu > empate
                    formatado = numeros.formatar_decimal(meu, 1)
                celulas.append(_celula_colorida_com_destaque(formatado, cor, eu_venco))
            linhas_do_braco.append(celulas)

            # A linha inteira e marcada pelo criterio de SENSIBILIDADE, e nao
            # pelo placar das tres medidas. Motivo: num alarme, deixar passar um
            # surto custa mais que um alarme falso, entao "pega quantos Alertas"
            # e a medida que decide. Em 1 mes isso importa — la o composto pega
            # mais e a regua e mais precisa, e a linha fica com o composto.
            venci_a_sensibilidade = meus[0] - dele[0] > empate
            classes_das_linhas.append("linhaVencedora" if venci_a_sensibilidade else "")

        return layout.montar_tabela(
            cabecalhos, linhas_do_braco, classes_das_linhas=classes_das_linhas
        )

    # Duas tabelas lado a lado, em vez de colunas pareadas numa so: o titulo do
    # slide afirma que o composto vence a regua, e sem os dois numeros na tela
    # essa afirmacao so apareceria nos graficos.
    as_duas_tabelas = (
        '<div class="deckTabelasLadoALado">'
        f'<div><p class="deckTabelaRotulo" style="color:var(--acento)">Modelo composto</p>'
        f"{montar_tabela_de_um_braco(numeros.NOME_DO_COMPOSTO, numeros.NOME_DA_REGUA)}</div>"
        f'<div><p class="deckTabelaRotulo" style="color:{COR_DA_REGUA_SAZONAL}">'
        f"Régua sazonal</p>"
        f"{montar_tabela_de_um_braco(numeros.NOME_DA_REGUA, numeros.NOME_DO_COMPOSTO)}</div>"
        "</div>"
    )

    graficos_das_medidas = "".join(
        _grafico_de_uma_medida_do_alarme(rotulo, cor, posicao)
        for rotulo, cor, posicao, _ in MEDIDAS_DO_ALARME
    )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="Como alarme de Alerta, o composto vence a régua até 2 meses",
        rotulo_curto="Alarme do composto",
        corpo=(
            as_duas_tabelas
            + f'<div class="graficosLadoALado">{graficos_das_medidas}</div>'
        ),
        nota=(
            "<b>Semana de Alerta = mais de 421 casos</b>, o piso do estágio Alerta do "
            "plano — aconteceu em <b>28 das 102</b> semanas avaliadas. <b>Pega</b> = "
            "das semanas que foram Alerta, em quantas o alarme tocou. 🔴 Em 2 meses: "
            "<b>85,7% com precisão de 100% e zero alarmes falsos</b>, o melhor número "
            "do projeto. A linha cinza pontilhada é a régua, e ela é quase reta — "
            "repetir o ano anterior custa o mesmo em qualquer horizonte."
        ),
        e_denso=True,
    )


def _slide_resultados() -> deck.Slide:
    """O desempenho da configuração adotada na previsão de casos.

    🚫 **FORA DA APRESENTAÇÃO desde 26/09/2026, por decisão do Vinicius.**

    Motivo: os professores já foram informados de que "as armadilhas não fazem
    diferença", e depois disso a mudança de hiperparâmetro mostrou que fazem. O
    que ele quer apresentar agora é o **modelo composto**, e este slide traz só
    os números da folha 5 — a versão anterior à melhora.

    A função continua aqui, fora da lista de `montar_slides()`, para o caso de
    ele querer o slide de volta. O que se perde ao tirá-lo: o R² e a captura do
    pico da configuração adotada sozinha. O erro médio dela continua visível no
    slide da folha 5 × 20, e nos horizontes de 1 a 3 semanas o composto **é** a
    configuração adotada.
    """
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
    """O modelo adotado lido como alarme de surto, no limiar de 100 casos.

    🚫 **FORA DA APRESENTAÇÃO desde 26/09/2026, por decisão do Vinicius.**

    Ficou obsoleto quando o slide do alarme do composto assumiu o lugar dele:
    aquele usa a configuração melhor (o composto, e não a folha 5 sozinha) e o
    limiar oficial (421, o piso do estágio Alerta do plano municipal, e não os
    100 casos que eram convenção do projeto). Este slide mostraria a versão
    antiga das duas coisas ao mesmo tempo.

    A função continua aqui, fora da lista de `montar_slides()`, caso ele
    queira de volta. O que se perde ao tirá-la: as métricas de alarme da
    configuração adotada no limiar de 100 — que são as que estão publicadas no
    site, e por isso ainda valem como referência histórica.
    """
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
        _slide_folha_5_contra_folha_20(),
        _slide_modelo_composto(),
        _slide_do_modelo_ao_alarme(),
        _slide_estagios_do_plano(),
        _slide_alarme_do_composto(),
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
