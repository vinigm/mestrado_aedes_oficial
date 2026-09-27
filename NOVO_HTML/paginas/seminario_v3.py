"""Segunda cópia de trabalho do Seminário de Andamento.

⚠️ **Cópia literal de `seminario_v2.py`, criada em 27/09/2026.** As duas
anteriores ficam intactas:

  - `seminario.py` — a versão de 23/09/2026, a que a banca viu;
  - `seminario_v2.py` — a cópia de trabalho, com o arco sobe-desce-sobe.

Esta existe para testar **mostrar 2024 e 2025 separados** em vez da média dos
dois, depois que a medição de 27/09 mostrou que os dois anos são regimes
diferentes: 2024 é partida a frio, com o modelo nunca tendo visto uma epidemia
grande, e 2025 é o método operando com história. Em 3 meses o alarme vai de
50% para 92,9% entre um e outro.

Se der certo, esta vira a versão de trabalho; se não, é só apagar.
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


def _slide_da_folha_5() -> deck.Slide:
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
    # A linha do ALGORITMO vem dentro do retangulo claro: numa tabela de sete
    # caracteristicas, "qual e o modelo" e a unica pergunta que a plateia faz
    # de imediato, e sem destaque ela se perde entre perda, alvo e validacao.
    classes_das_linhas = ["linhaVencedora"] + [""] * (len(linhas) - 1)

    return deck.Slide(
        topico=TOPICO_CENARIOS,
        titulo="A configuração de folha mínima 5, e como ela foi escolhida",
        rotulo_curto="Folha mínima 5",
        corpo=(
            layout.montar_tabela(
                cabecalhos, linhas, classes_das_linhas=classes_das_linhas
            )
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
    folha mínima 5, e a bateria de 23-24/09/2026 mediu uma segunda que
    vai melhor em horizonte longo — e que é a única das duas que extrai ganho
    das colunas do vetor.
    """
    por_braco = {}
    for linha in numeros.PAINEL_DO_COMPOSTO:
        por_braco.setdefault(linha.braco, {})[linha.rotulo] = linha

    rotulos = list(ROTULOS_DOS_HORIZONTES)
    cabecalhos_do_erro = [
        "Horizonte",
        "Folha mínima 5",
        "Folha mínima 20, com vetor",
    ]
    linhas_do_erro = []
    for rotulo in rotulos:
        erro_da_folha_5 = por_braco[numeros.NOME_DO_ADOTADO][rotulo].erro_medio_absoluto
        erro_folha20 = por_braco[numeros.NOME_DA_FOLHA_20][rotulo].erro_medio_absoluto
        a_folha_5_e_melhor = erro_da_folha_5 < erro_folha20
        linhas_do_erro.append(
            [
                f"<b>{layout.escapar(rotulo)}</b>",
                _destacar(numeros.formatar_decimal(erro_da_folha_5, 1), a_folha_5_e_melhor),
                _destacar(
                    numeros.formatar_decimal(erro_folha20, 1), not a_folha_5_e_melhor
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
        rotulo_curto="Folha mínima 5 × 20",
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

# O viewBox dos tres graficos do composto. O padrao de 720 deixava a fonte dos
# eixos, fixa em 11 unidades, chegar a tela com 5,7px — os graficos ficam lado
# a lado e recebem 376px cada. Com 400 ela chega com 10,3px.
#
# A altura de 245 nao e proporcional: ela e escolhida para o desenho ocupar
# a folga que sobrava no slide. Como a largura na tela e fixa em 376px, a
# altura renderizada e 376 x 245 / 400 = 230px, contra os 130px do padrao.
TAMANHO_DO_DESENHO_DO_COMPOSTO = (400, 245)

# O viewBox dos graficos dos slides que tem DUAS tabelas acima deles — o do
# alarme e o dos dois anos. Eles sobram menos altura que o slide do composto,
# que tem uma tabela so, entao a altura e menor: 212 contra 245. A largura e a
# mesma, e e ela que manda na fonte, que chega a tela com 10,3px nos tres.
TAMANHO_DO_DESENHO_COM_DUAS_TABELAS = (400, 212)
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
        "horizonte",
        rotulo_do_eixo,
        cores=[cor, COR_DA_REGUA_SAZONAL],
        series_tracejadas={NOME_DA_LINHA_DA_REGUA},
        tamanho_do_desenho=TAMANHO_DO_DESENHO_DO_COMPOSTO,
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
        "horizonte",
        rotulo_do_eixo,
        cores=[cor, COR_DA_REGUA_SAZONAL],
        series_tracejadas={NOME_DA_LINHA_DA_REGUA},
        tamanho_do_desenho=TAMANHO_DO_DESENHO_COM_DUAS_TABELAS,
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
    """O desempenho da folha mínima 5 na previsão de casos.

    🚫 **FORA DA APRESENTAÇÃO desde 26/09/2026, por decisão do Vinicius.**

    Motivo: os professores já foram informados de que "as armadilhas não fazem
    diferença", e depois disso a mudança de hiperparâmetro mostrou que fazem. O
    que ele quer apresentar agora é o **modelo composto**, e este slide traz só
    os números da folha 5 — a versão anterior à melhora.

    A função continua aqui, fora da lista de `montar_slides()`, para o caso de
    ele querer o slide de volta. O que se perde ao tirá-lo: o R² e a captura do
    pico da folha mínima 5 sozinha. O erro médio dela continua visível no
    slide da folha 5 × 20, e nos horizontes de 1 a 3 semanas o composto **é** a
    folha mínima 5.
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
    """A folha mínima 5 lida como alarme de surto, no limiar de 100 casos.

    🚫 **FORA DA APRESENTAÇÃO desde 26/09/2026, por decisão do Vinicius.**

    Ficou obsoleto quando o slide do alarme do composto assumiu o lugar dele:
    aquele usa a configuração melhor (o composto, e não a folha 5 sozinha) e o
    limiar oficial (421, o piso do estágio Alerta do plano municipal, e não os
    100 casos que eram convenção do projeto). Este slide mostraria a versão
    antiga das duas coisas ao mesmo tempo.

    A função continua aqui, fora da lista de `montar_slides()`, caso ele
    queira de volta. O que se perde ao tirá-la: as métricas de alarme da
    folha mínima 5 no limiar de 100 — que são as que estão publicadas no
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


# As duas colunas do slide dos dois anos. Vermelho para a partida a frio,
# verde para o ano em que o metodo ja tinha historia — a mesma leitura de cor
# do slide dos limites.
COR_DA_PARTIDA_A_FRIO = "#C0392B"
COR_DO_ANO_COM_HISTORIA = "#1F7A4D"


# As tres medidas, na ordem em que aparecem na tabela e nos graficos.
MEDIDAS_DOS_DOIS_ANOS = (
    ("R²", numeros.POSICAO_DO_R2_POR_ANO),
    ("Captura do pico", numeros.POSICAO_DA_CAPTURA_POR_ANO),
    ("Alarme pega", numeros.POSICAO_DO_ALARME_POR_ANO),
)


def _grafico_dos_dois_anos(rotulo_do_eixo: str, posicao_da_medida: int) -> str:
    """Desenha uma medida nos 12 horizontes, com uma curva por ano.

    A forma das curvas e o argumento do slide: em 2024 a medida cai sem parar
    conforme o horizonte cresce, e em 2025 ela se mantem alta — o R2 ate sobe
    no fim. Por isso os graficos cobrem os 12 horizontes, e nao so os quatro da
    tabela: com quatro pontos a queda de 2024 vira um degrau, e nao uma curva.

    Args:
        rotulo_do_eixo: Texto do eixo vertical, tambem usado no titulo.
        posicao_da_medida: Indice da medida dentro das tuplas de 12 horizontes.

    Returns:
        O HTML do grafico.
    """
    pontos_de_2024 = [
        (float(linha[0]), linha[posicao_da_medida])
        for linha in numeros.COMPOSTO_EM_2024_NOS_12
    ]
    pontos_de_2025 = [
        (float(linha[0]), linha[posicao_da_medida])
        for linha in numeros.COMPOSTO_EM_2025_NOS_12
    ]

    return graficos.montar_grafico_de_linhas(
        {"2024": pontos_de_2024, "2025": pontos_de_2025},
        "horizonte",
        rotulo_do_eixo,
        cores=[COR_DA_PARTIDA_A_FRIO, COR_DO_ANO_COM_HISTORIA],
        tamanho_do_desenho=TAMANHO_DO_DESENHO_COM_DUAS_TABELAS,
    )


def _slide_os_dois_anos() -> deck.Slide:
    """O que a media de 2024 e 2025 escondia.

    Slide novo de 27/09/2026, e ele nasceu de uma pergunta do Vinicius: se o
    modelo retreina a cada semana, por que os resultados de 3 meses sao tao
    ruins? A medicao respondeu que nao sao — eles sao a media de dois regimes
    que nao deveriam ser lidos juntos.

    ⚠️ Os slides do painel e do alarme continuam com os numeros agregados, que
    estao corretos. Este slide nao os substitui: ele mostra o que a media
    esconde, e so existe porque 2024 esta na conta.

    🔴 **Descritivo e pos-fato.** O corte por ano foi feito depois de ver o
    resultado, e um ano contra um ano, e nao foi pre-declarado. A nota do
    apresentador manda dizer isso em voz alta.
    """
    cabecalhos = ["Horizonte", "R²", "Captura do pico", "Alarme pega"]

    def montar_tabela_de_um_ano(do_ano, cor: str, e_o_ano_bom: bool) -> str:
        """Monta a tabela de um dos dois anos.

        Args:
            do_ano: As quatro linhas daquele ano.
            cor: A cor da coluna, a mesma do rotulo.
            e_o_ano_bom: True para 2025, cujas celulas vem em negrito.

        Returns:
            O HTML da tabela.
        """
        linhas = []
        for linha in do_ano:
            linhas.append(
                [
                    f"<b>{layout.escapar(linha.rotulo)}</b>",
                    _celula_colorida_com_destaque(
                        numeros.formatar_decimal(linha.r2, 3), cor, e_o_ano_bom
                    ),
                    _celula_colorida_com_destaque(
                        numeros.formatar_percentual(linha.captura_do_pico, 1),
                        cor,
                        e_o_ano_bom,
                    ),
                    _celula_colorida_com_destaque(
                        f"{linha.alertas_pegos} de {linha.alertas_no_ano} · "
                        f"{numeros.formatar_percentual(linha.sensibilidade(), 1)}",
                        cor,
                        e_o_ano_bom,
                    ),
                ]
            )
        return layout.montar_tabela(cabecalhos, linhas)

    as_duas_tabelas = (
        '<div class="deckTabelasLadoALado">'
        f'<div><p class="deckTabelaRotulo" style="color:{COR_DA_PARTIDA_A_FRIO}">'
        f"2024 — nunca tinha visto epidemia grande "
        f'<span style="font-weight:400;opacity:.62">· {numeros.SEMANAS_AVALIADAS_EM_2024} '
        "semanas</span></p>"
        f"{montar_tabela_de_um_ano(numeros.COMPOSTO_EM_2024, COR_DA_PARTIDA_A_FRIO, False)}</div>"
        f'<div><p class="deckTabelaRotulo" style="color:{COR_DO_ANO_COM_HISTORIA}">'
        f"2025 — com 2024 na história "
        f'<span style="font-weight:400;opacity:.62">· {numeros.SEMANAS_AVALIADAS_EM_2025} '
        "semanas</span></p>"
        f"{montar_tabela_de_um_ano(numeros.COMPOSTO_EM_2025, COR_DO_ANO_COM_HISTORIA, True)}</div>"
        "</div>"
    )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="O modelo não previa o pico porque nunca tinha visto um",
        rotulo_curto="Os dois anos",
        corpo=(
            as_duas_tabelas
            + '<div class="graficosLadoALado">'
            + "".join(
                _grafico_dos_dois_anos(rotulo, posicao)
                for rotulo, posicao in MEDIDAS_DOS_DOIS_ANOS
            )
            + "</div>"
        ),
        nota=(
            "🔴 <b>A explicação, para dizer em voz alta:</b> ao prever o pico de "
            "<b>2024</b> a maior semana que o modelo já tinha visto na vida tinha "
            "<b>879</b> casos, e ele precisava acertar <b>1.601</b> — uma árvore de "
            "decisão <b>nunca</b> prevê acima do que viu. Ao prever o pico de <b>2025</b> "
            "ele já conhecia os <b>1.855</b> de 2024, e previu <b>1.614</b> para um real "
            "de 2.381. "
            "🔴 <b>O número da apresentação:</b> em 3 meses o alarme vai de <b>1 de 14</b> "
            "para <b>13 de 14</b>, e o R² de <b>0,054</b> para <b>0,792</b>. O "
            "\"modelo não serve a 3 meses\" era, na verdade, <b>não servia antes de ter "
            "visto uma epidemia</b>. ⚠️ <b>Dizer em voz alta que isto é descritivo e "
            "pós-fato</b>: o corte por ano foi feito depois de ver o resultado, é um ano "
            "contra um ano (45 e 52 semanas) e não foi pré-declarado. A confirmação é "
            "pré-declarar e medir em 2027. ⚠️ E não é melhora em tudo: em 2025 os "
            "<b>alarmes falsos sobem</b> (1 mês vai de 1,2 para 5,0 por ano) e a "
            "<b>precisão de 1 mês cai</b> de 92,9% para 73,7% — o modelo fica mais "
            "sensível. ⚠️ A régua sazonal também melhora em 2025, e volta a vencer em "
            "erro médio; o que o modelo ganha dela é justamente no ano inédito."
        ),
        e_denso=True,
    )


# As duas medidas do slide do vetor, cada uma com a sua cor — a mesma na
# coluna da tabela e na curva, para ligar as duas sem precisar de legenda.
COR_DO_GANHO = "#1F7A4D"
COR_DO_APOIO = "#1B6EF3"

# A folha 5 é a COMPARAÇÃO deste slide, e por isso usa o mesmo tratamento que a
# régua sazonal usa nos slides de resultado: cinza e pontilhada.
COR_DA_FOLHA_5 = COR_DA_REGUA_SAZONAL
NOME_DA_LINHA_DA_FOLHA_5 = "Folha mínima 5"

# O viewBox dos dois gráficos deste slide, mais estreito e mais alto que o
# padrão de 720 × 250. Não muda a largura na tela, que vem do CSS: muda o
# tamanho RELATIVO do que está dentro.
#
# Por que: os dois gráficos ficam lado a lado e recebem ~580px cada. No padrão
# de 720 de largura, a fonte dos eixos, fixa em 11 unidades, chega à tela com
# uns 9px — e o slide ainda é reduzido para caber na projeção, o que a leva
# para perto de 7px. Com 540, a mesma fonte chega com ~12px.
#
# A altura cai para 200, e não sobe: com a grade de colunas corrigida cada
# gráfico passou a ocupar 574px em vez de 376, e manter a proporção antiga
# deixaria o slide 17px acima dos 720.
TAMANHO_DO_DESENHO_DO_VETOR = (540, 200)


def _formatar_com_sinal(valor_percentual: float) -> str:
    """Formata um percentual sempre com sinal explícito.

    O sinal importa aqui: no ganho, negativo significa que o vetor atrapalhou
    naquele horizonte, e omitir o "+" deixaria a leitura ambígua.

    Args:
        valor_percentual: O número já em pontos percentuais.

    Returns:
        O texto formatado, com vírgula decimal.
    """
    return f"{valor_percentual:+.1f}%".replace(".", ",")


def _formatar_p_de_holm(p_de_holm: float) -> str:
    """Formata o p com casas suficientes para ele não perder força.

    ⚠️ O corte é em 0,1, e não em 0,05 ou 0,01: com duas casas, o p de 0,0151
    da folha 20 sairia como **0,02** — que lido de relance parece quase no
    limite, quando na verdade está três vezes abaixo dele.

    Args:
        p_de_holm: O p já corrigido por Holm.

    Returns:
        Duas casas quando o p é grande, quatro quando é pequeno.
    """
    if p_de_holm >= 0.1:
        return f"{p_de_holm:.2f}".replace(".", ",")

    # Guarda para p muito pequeno: arredondar 0,000058 para quatro casas daria
    # "0,0001", que é MAIOR que o valor real e faz o resultado parecer mais
    # fraco do que é. Nenhum p do slide cai aqui hoje, mas a guarda fica para
    # que um valor futuro não saia distorcido em silêncio.
    if p_de_holm < 0.0001:
        return "&lt; 0,0001"

    return f"{p_de_holm:.4f}".replace(".", ",")


def _grafico_do_vetor(
    rotulo_do_eixo: str,
    serie_dos_12_horizontes: tuple[tuple[int, float, float], ...],
    cor_da_folha_20: str,
    destacar_o_sinal: bool = False,
) -> str:
    """Desenha uma das duas medidas do vetor ao longo dos 12 horizontes.

    ⚠️ Sem marco vertical, ao contrário do slide do composto: no ganho a folha
    20 cruza o zero mais de uma vez (sobe em h=4, volta a cair em h=5 e só
    então se firma), e um marco fingiria um ponto de virada único que não
    existe.

    Args:
        rotulo_do_eixo: Texto do eixo vertical, também usado no título.
        serie_dos_12_horizontes: Tuplas de (horizonte, folha 5, folha 20).
        cor_da_folha_20: A cor desta medida, a mesma da coluna na tabela.
        destacar_o_sinal: True marca o zero no eixo e pinta os números por
            sinal. Vale para o GANHO, em que negativo significa que o vetor
            atrapalhou naquele horizonte. Não vale para o apoio, que é sempre
            positivo por construção — ali um zero destacado só poluiria.

    Returns:
        O HTML do gráfico.
    """
    pontos_da_folha_5 = [
        (float(linha[0]), linha[numeros.POSICAO_DA_FOLHA_5])
        for linha in serie_dos_12_horizontes
    ]
    pontos_da_folha_20 = [
        (float(linha[0]), linha[numeros.POSICAO_DA_FOLHA_20])
        for linha in serie_dos_12_horizontes
    ]

    return graficos.montar_grafico_de_linhas(
        {
            NOME_DA_LINHA_DA_FOLHA_5: pontos_da_folha_5,
            "Folha mínima 20": pontos_da_folha_20,
        },
        "horizonte",
        rotulo_do_eixo,
        cores=[COR_DA_FOLHA_5, cor_da_folha_20],
        series_tracejadas={NOME_DA_LINHA_DA_FOLHA_5},
        tamanho_do_desenho=TAMANHO_DO_DESENHO_DO_VETOR,
        eixo_y_destaca_o_sinal=destacar_o_sinal,
        pintar_area_ate_o_zero=destacar_o_sinal,
    )


def _slide_o_vetor() -> deck.Slide:
    """O que o mosquito rende e o quanto o modelo se apoia nele, nas duas folhas.

    ⚠️ **Refeito em 26/09/2026**, a pedido do Vinicius: menos texto, mais tabela
    e gráfico, com cor ligando cada medida à sua curva. A versão anterior tinha
    uma tabela de 3 linhas e dois avisos de texto corrido.

    O slide junta **duas medições diferentes**, e a nota de rodapé existe para
    impedir que elas sejam confundidas:

      - **ganho** (ablação): treinar do zero sem o mosquito e comparar;
      - **erro sem o mosquito** (permutação): embaralhar as colunas no modelo
        já treinado.

    Na folha 5 as duas discordam — o modelo se apoia no mosquito e mesmo assim
    treinar sem ele não piora. É exatamente por isso que **"indispensável" não
    pode ser dito**, e a nota registra isso.

    Nunca dizer "o vetor não ajuda" nem "não deu correlação": as duas frases
    afirmam mais do que a medição sustenta, e é o que o orientador pediu para
    evitar em 21/09/2026.
    """
    # "Erro médio" é a BASE sobre a qual os dois percentuais são calculados, e
    # existe como coluna porque percentual sem base engana: sem ela, +12,3% e
    # +2,2% parecem medidos sobre o mesmo erro, e não são. Vem em casos por
    # semana, sem sinal e sem "%", para não se confundir com as outras duas.
    cabecalhos = [
        "Horizonte",
        "Erro médio",
        _celula_colorida("Ganho do vetor", COR_DO_GANHO),
        "p de Holm",
        _celula_colorida("Erro sem o mosquito", COR_DO_APOIO),
    ]

    def montar_tabela_de_uma_configuracao(e_a_folha_20: bool) -> str:
        """Monta a tabela de uma das duas configurações.

        A folha 20 vem em negrito onde supera a folha 5, que é a comparação —
        o mesmo critério visual do slide do alarme.

        Args:
            e_a_folha_20: True para a configuração de folha mínima 20.

        Returns:
            O HTML da tabela.
        """
        linhas_da_tabela = []
        for do_horizonte in numeros.O_VETOR_NAS_DUAS_CONFIGURACOES:
            if e_a_folha_20:
                erro_medio = do_horizonte.erro_na_folha_20
                ganho = do_horizonte.ganho_na_folha_20
                p_de_holm = do_horizonte.p_holm_na_folha_20
                apoio = do_horizonte.apoio_na_folha_20
            else:
                erro_medio = do_horizonte.erro_na_folha_5
                ganho = do_horizonte.ganho_na_folha_5
                p_de_holm = do_horizonte.p_holm_na_folha_5
                apoio = do_horizonte.apoio_na_folha_5

            ganho_vence = e_a_folha_20 and ganho > do_horizonte.ganho_na_folha_5
            apoio_vence = e_a_folha_20 and apoio > do_horizonte.apoio_na_folha_5
            p_passa = p_de_holm < 0.05

            # No erro médio, MENOR é melhor — ao contrário das outras colunas.
            erro_vence = (
                e_a_folha_20 and erro_medio < do_horizonte.erro_na_folha_5
            )

            linhas_da_tabela.append(
                [
                    f"<b>{layout.escapar(do_horizonte.rotulo)}</b>",
                    _destacar(numeros.formatar_decimal(erro_medio, 0), erro_vence),
                    _celula_colorida_com_destaque(
                        _formatar_com_sinal(ganho), COR_DO_GANHO, ganho_vence
                    ),
                    _destacar(_formatar_p_de_holm(p_de_holm), p_passa),
                    _celula_colorida_com_destaque(
                        _formatar_com_sinal(apoio), COR_DO_APOIO, apoio_vence
                    ),
                ]
            )

        return layout.montar_tabela(cabecalhos, linhas_da_tabela)

    # Duas tabelas lado a lado, uma por configuração, como no slide do alarme:
    # sem os dois blocos na tela a comparação ficaria só nas curvas.
    #
    # ⚠️ O erro base já viveu aqui no rótulo, como faixa ("erro 98 a 279
    # casos"). Saiu em 27/09/2026 porque o Vinicius perguntou o que era: a
    # faixa não dizia o que variava entre as duas pontas, e parecia intervalo
    # de incerteza. Virou coluna da tabela, onde cada número fica ao lado do
    # horizonte a que pertence.
    as_duas_tabelas = (
        '<div class="deckTabelasLadoALado">'
        '<div><p class="deckTabelaRotulo" style="color:var(--tinta)">'
        "Folha mínima 5</p>"
        f"{montar_tabela_de_uma_configuracao(e_a_folha_20=False)}</div>"
        '<div><p class="deckTabelaRotulo" style="color:var(--acento)">'
        "Folha mínima 20</p>"
        f"{montar_tabela_de_uma_configuracao(e_a_folha_20=True)}</div>"
        "</div>"
    )

    os_dois_graficos = (
        _grafico_do_vetor(
            "Ganho do vetor (%)",
            numeros.GANHO_DO_VETOR_NOS_12,
            COR_DO_GANHO,
            destacar_o_sinal=True,
        )
        + _grafico_do_vetor(
            "Erro sem o mosquito (%)", numeros.APOIO_NO_VETOR_NOS_12, COR_DO_APOIO
        )
    )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="Com folha 20, o mosquito reduz o erro em 2 e 3 meses",
        rotulo_curto="O vetor",
        corpo=(
            as_duas_tabelas
            + f'<div class="graficosLadoALado">{os_dois_graficos}</div>'
        ),
        nota=(
            "<b>Ganho</b> = treino um modelo do zero <b>sem</b> o mosquito e comparo; "
            "responde <i>dá para viver sem?</i>. <b>Erro sem o mosquito</b> = pego o "
            "modelo <b>já treinado</b> e embaralho as colunas dele; responde <i>ele "
            "está usando?</i>. 🔴 <b>Nunca dizer 'indispensável'</b>: na folha 5 o "
            "modelo se apoia no mosquito e mesmo assim treinar sem ele não piora "
            "(p de Holm <b>1,00</b>) — ele reaprende pelo histórico de casos. "
            "🔴 <b>Nem 'a folha decide'</b>: a folha 20 só ganha mais em 8 dos 12 "
            "horizontes, e o GradBoost de folha 5 rende +10,1% em 1 mês. "
            "⚠️ <b>Exploratório e carregado por 2024</b>: em 2025, em 2 meses, o sinal "
            "chega a inverter. ⚠️ As "
            "famílias de Holm são diferentes: 12 na folha 5, 4 na folha 20. ⚠️ Por que "
            "não usamos a folha 20: o critério do projeto olha a calibração de "
            "2020-2023, e ali ela é <b>~30% pior</b>. É pendência declarada. A linha "
            "cinza pontilhada é sempre a folha 5."
        ),
        e_denso=True,
    )


# As duas faixas de nível do slide que mostra onde o modelo ainda falha. Azul
# para a calmaria, vermelho para o Alerta — a mesma leitura de cor do plano
# municipal, em que o Alerta é o estágio que exige resposta.
COR_DA_CALMARIA = "#1B6EF3"
COR_DO_ALERTA = "#C0392B"

# A cor da tabela que dá a boa notícia do slide. Verde, a mesma de "pega
# quantos Alertas" no slide do alarme, para o olho ligar os dois.
COR_DO_ALARME_QUE_FUNCIONA = "#1F7A4D"

# 52 semanas em 12 meses. Serve só para dar tamanho a uma contagem de semanas;
# as semanas contadas não são seguidas, então é equivalência, não período.
SEMANAS_POR_MES = 52 / 12

# As duas metades do slide da literatura. A primeira é a comparação JUSTA, a
# segunda é a que perdemos — e cada uma tem a sua cor, como nos demais slides.
# Como o composto se chama nas tabelas de literatura. Ali ele fica ao lado
# de nomes de artigo ("LASSO, Shi et al. 2016"), e só "Composto" ficaria
# críptico — por isso não usa NOME_DO_COMPOSTO, que serve aos slides de
# resultado, onde o contexto já é o nosso modelo.
NOME_NA_LITERATURA = "Modelo composto"

COR_DA_MESMA_CIDADE = "#1F7A4D"
COR_DE_SINGAPURA = "#8A94A6"


def _slide_onde_ainda_falha() -> deck.Slide:
    """O contrapeso do slide do vetor: o ganho é real e mesmo assim não basta.

    ⚠️ **Refeito duas vezes em 27/09/2026.**

    Na primeira, deixou de ser "A defasagem", que repetia o slide 4 — o título
    dele era literalmente a nota do slide 4. Passou a mostrar a calibração por
    faixa, dentro do arco que o Vinicius desenhou: o slide do vetor **sobe** a
    moral, este **desce**, e o da literatura **sobe** de novo.

    Na segunda, ganhou a linha do ALARME, e o motivo é do Vinicius: *"parece
    que a nossa metodologia está ruim, olhando puramente esses números"*. E
    parecia mesmo. A tabela mostrava só a pergunta em que o modelo vai mal — o
    número de casos — e escondia a pergunta em que ele vai bem, que é a que o
    projeto está propondo. A descida continua honesta; o que sai é a leitura
    errada de que o método falhou.

    ⚠️ **Tudo no mesmo horizonte, 2 meses.** A versão anterior juntava 4
    horizontes nas coberturas, e isso não era comparável com as métricas de
    alarme, que são por horizonte. Remedido em 27/09.
    """
    calmaria, alerta = numeros.CALIBRACAO_EM_DOIS_MESES
    alarme = numeros.ALARME_EM_DOIS_MESES

    # Uma tabela só, no formato que o Vinicius aprovou: rótulo, calmaria e
    # Alerta. As quatro primeiras linhas são a pergunta em que o modelo vai MAL,
    # sem suavizar nada — é a concessão que compra credibilidade para a última.
    #
    # ⚠️ O alarme entra como LINHA, e não como par de colunas dentro de cada
    # faixa. Quatro colunas deixariam metade das células vazias: o alarme não
    # tem "intervalo de 90%" e a previsão não tem "alarmes falsos". Como linha
    # destacada, a virada aparece sem buraco na grade.
    # A contagem de semanas vive no cabeçalho, e não numa linha própria: ela
    # qualifica a coluna inteira, e como linha custava ~25px de altura que a
    # figura aproveita melhor.
    def cabecalho_da_faixa(faixa, cor: str) -> str:
        """O nome da faixa com a contagem de semanas ao lado, em tom leve."""
        return _celula_colorida(
            f"{layout.escapar(faixa.rotulo)} "
            f'<span style="opacity:.62">· {faixa.semanas} semanas '
            f"(≈ {numeros.formatar_decimal(faixa.semanas / SEMANAS_POR_MES, 0)} "
            "meses)</span>",
            cor,
        )

    cabecalhos = [
        "",
        cabecalho_da_faixa(calmaria, COR_DA_CALMARIA),
        cabecalho_da_faixa(alerta, COR_DO_ALERTA),
    ]

    def par_de_celulas(da_calmaria: str, do_alerta: str) -> list[str]:
        """As duas células de uma linha, cada uma na cor da sua faixa."""
        return [
            _celula_colorida(da_calmaria, COR_DA_CALMARIA),
            _celula_colorida_com_destaque(do_alerta, COR_DO_ALERTA, True),
        ]

    linhas_da_tabela = [
        ["<b>O intervalo de 90% acerta</b>"]
        + par_de_celulas(
            numeros.formatar_percentual(calmaria.cobertura_de_90, 1),
            numeros.formatar_percentual(alerta.cobertura_de_90, 1),
        ),
        ["<b>O intervalo de 50% acerta</b>"]
        + par_de_celulas(
            numeros.formatar_percentual(calmaria.cobertura_de_50, 1),
            numeros.formatar_percentual(alerta.cobertura_de_50, 1),
        ),
        ["<b>Erro mediano</b>"]
        + par_de_celulas(
            f"{numeros.formatar_decimal(calmaria.erro_mediano, 0)} casos",
            f"{numeros.formatar_decimal(alerta.erro_mediano, 0)} sobre "
            f"{numeros.formatar_decimal(alerta.nivel_mediano, 0)} reais",
        ),
        # A virada do slide, em verde e dentro do retângulo de linha destacada.
        [
            '<b>O alarme de surto acerta</b><span class="deckSubrotulo">'
            "a mesma previsão, na pergunta binária</span>",
            _celula_colorida_com_destaque(
                "nenhum alarme falso", COR_DO_ALARME_QUE_FUNCIONA, True
            ),
            _celula_colorida_com_destaque(
                f"{alarme.alertas_pegos} de {alarme.semanas_de_alerta} · "
                f"{numeros.formatar_percentual(alarme.sensibilidade(), 1)} · "
                f"precisão {numeros.formatar_percentual(alarme.precisao, 0)}",
                COR_DO_ALARME_QUE_FUNCIONA,
                True,
            ),
        ],
    ]
    classes_das_linhas = ["", "", "", "linhaVencedora"]

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="A previsão do número não serve — o alarme serve",
        rotulo_curto="O que falta",
        corpo=(
            layout.montar_tabela(
                cabecalhos, linhas_da_tabela, classes_das_linhas=classes_das_linhas
            )
            # A explicação e a figura dividem a faixa que sobra embaixo da
            # tabela. Em largura cheia o texto ocupava três linhas e deixava
            # metade do slide vazia; ao lado dele a figura cabe sem apertar.
            + '<div class="deckTextoEFigura">'
            + '<p class="deckNotaDeGrafico">⚠️ <b>A causa é viés, não '
            "variância:</b> o modelo subestima o pico de forma sistemática. "
            "Alargar a faixa não conserta, e mudar a escala (raiz, log) "
            "<b>piorou</b> em todas as faixas. É a razão de o projeto tratar o "
            "modelo como <b>alarme</b>, e não como previsão de número.</p>"
            # Sem teto de altura: a figura preenche a coluna, e a largura dela
            # (metade do slide, 574px) é que define o tamanho. Dá 264px de
            # altura, e o slide fecha em 680 dos 720.
            + '<img src="imagens/vetor_vs_casos.png" '
            'alt="Aedes aegypti capturados e casos confirmados de dengue, '
            'semana a semana">'
            + "</div>"
        ),
        nota=(
            "🔴 <b>As quatro primeiras linhas são para chocar, e não devem ser "
            "suavizadas.</b> Dizer: no pico de 2025 o modelo prometeu <b>no máximo "
            "1.118 casos, com 90% de confiança</b>, e vieram <b>2.381</b>. O "
            "intervalo de 50% acerta <b>3,6%</b> — ele é quase decorativo onde a "
            "decisão acontece. 🟢 <b>E então a última linha, a verde:</b> a mesma "
            "previsão, no mesmo horizonte e nas mesmas 28 semanas, pega <b>24 dos 28 "
            "Alertas sem um único alarme falso</b>. Não saber o tamanho não impede "
            "saber que vem — e é isso que a metodologia propõe. "
            "⚠️ Tudo em <b>2 meses</b>, nas 102 semanas da "
            "avaliação; as 28 de Alerta são as mesmas do slide do alarme. "
            "⚠️ <b>Os meses entre parênteses são equivalência, não período</b>: as "
            "semanas não são seguidas — as de calmaria são as entressafras e as de "
            "Alerta formam dois blocos, um por epidemia. Não dizer 'durante seis "
            "meses'. Se perguntarem por que não alargamos o intervalo: porque "
            "medimos, e o problema não é a largura, é o centro."
        ),
        e_denso=True,
    )


def _slide_literatura() -> deck.Slide:
    """O resultado em contexto: contra quem mediu a mesma cidade, e contra Singapura.

    Slide novo de 27/09/2026, ideia do Vinicius. Fecha o arco que ele desenhou:
    o slide do vetor sobe a moral, o anterior a desce, e este a levanta de
    novo — pondo o número num contexto em vez de num vácuo.

    ⚠️ **As duas metades existem por honestidade, não por simetria.** A
    comparação direta só é legítima com o estudo da MESMA cidade e da mesma
    unidade; a da direita nós perdemos, e o slide diz isso. Uma apresentação
    que só mostrasse a metade favorável seria desmontada na primeira pergunta.

    🚫 **Oliveira et al. 2025 ficou de fora, deliberadamente.** Ele prevê
    aceleração binária em 10 a 15 dias, com acurácia balanceada de 0,67; nós
    prevemos casos a 12 semanas. Não existe número nosso nas mesmas condições,
    e dizer "somos melhores" seria indefensável.
    """
    # 🔴 O filtro era `onde == "Porto Alegre"` e derrubava justamente a linha
    # que dá título ao slide: a do CatBoost das 27 capitais, cujo campo é
    # "Porto Alegre, 1999-2021". Sem ela a tabela dizia "a comparação justa" e
    # não mostrava o estudo comparável. Corrigido em 27/09/2026.
    #
    # Das linhas do projeto fica só o COMPOSTO: os slides de resultado falam de
    # um modelo só, e separar folha 5 de folha 20 aqui repetiria a discussão que
    # já aconteceu no slide do vetor.
    def entra_na_tabela_da_cidade(linha) -> bool:
        """Diz se a linha é de Porto Alegre e, sendo nossa, se é a do composto."""
        if not linha.onde.startswith("Porto Alegre"):
            return False

        return not linha.este_projeto or linha.modelo == NOME_NA_LITERATURA

    da_mesma_cidade = [
        linha for linha in numeros.R2_PUBLICADO if entra_na_tabela_da_cidade(linha)
    ]

    cabecalhos_da_cidade = ["Modelo", _celula_colorida("R² em 1 mês", COR_DA_MESMA_CIDADE)]
    linhas_da_cidade = []
    for linha in da_mesma_cidade:
        linhas_da_cidade.append(
            [
                f"<b>{layout.escapar(linha.modelo)}</b>"
                if linha.este_projeto
                else layout.escapar(linha.modelo),
                _celula_colorida_com_destaque(
                    linha.um_mes, COR_DA_MESMA_CIDADE, linha.este_projeto
                ),
            ]
        )

    cabecalhos_de_singapura = [
        "Modelo",
        _celula_colorida("1 semana", COR_DE_SINGAPURA),
        _celula_colorida("3 meses", COR_DE_SINGAPURA),
    ]
    linhas_de_singapura = []
    for linha in numeros.MAPE_PUBLICADO:
        if linha.este_projeto and linha.modelo != NOME_NA_LITERATURA:
            continue

        linhas_de_singapura.append(
            [
                f"<b>{layout.escapar(linha.modelo)}</b>"
                if linha.este_projeto
                else layout.escapar(linha.modelo),
                _celula_colorida(linha.uma_semana, COR_DE_SINGAPURA),
                _celula_colorida(linha.tres_meses, COR_DE_SINGAPURA),
            ]
        )

    de_singapura = numeros.SINGAPURA
    as_duas_tabelas = (
        '<div class="deckTabelasLadoALado">'
        f'<div><p class="deckTabelaRotulo" style="color:{COR_DA_MESMA_CIDADE}">'
        "Porto Alegre — a comparação justa</p>"
        f"{layout.montar_tabela(cabecalhos_da_cidade, linhas_da_cidade)}</div>"
        f'<div><p class="deckTabelaRotulo" style="color:{COR_DE_SINGAPURA}">'
        f"Singapura — {de_singapura.anos_de_treino} anos de série · erro "
        "percentual</p>"
        f"{layout.montar_tabela(cabecalhos_de_singapura, linhas_de_singapura)}</div>"
        "</div>"
    )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="Ganhamos de quem mediu a mesma cidade, e perdemos para 10 anos de série",
        rotulo_curto="A literatura",
        corpo=as_duas_tabelas,
        nota=(
            f"🔴 <b>A frase que explica a derrota, para dizer em voz alta:</b> não é "
            "porque lá tem mais dengue. O pico semanal de Singapura em 2013 foi de "
            "<b>{numeros.formatar_decimal(de_singapura.pico_semanal, 0)}</b> casos; o de Porto Alegre em "
            "2025, <b>{numeros.formatar_decimal(de_singapura.pico_semanal_de_porto_alegre, 0)}</b>. Eles têm "
            "<b>mais anos</b>, e anos calmos, que ensinam ao modelo o que é o normal "
            "da cidade. Nós temos <b>{de_singapura.temporadas_epidemicas_de_porto_alegre} temporadas</b>. "
            "🟢 <b>Este slide levanta a moral de novo, e é o último dos resultados.</b> "
            "À esquerda, o <b>único</b> estudo marcado como comparável no nosso "
            "catálogo de 14: mesma cidade, mesma unidade, validação em avanço. "
            "⚠️ À direita <b>não é páreo direto</b>: nosso erro percentual conta só "
            "semanas com 100 casos ou mais e o modelo prevê o quantil 0,85 — as duas "
            "coisas inflam o nosso número. Dizer isso antes que perguntem. "
            "⚠️ <b>Nunca dizer que batemos o Oliveira 2025</b>: ele prevê aceleração "
            "binária em 10 a 15 dias, e não existe número nosso nas mesmas condições. "
            "⚠️ Ressalva do nosso R²: a janela tem as duas maiores epidemias da série, "
            "e variância alta infla R²."
        ),
        e_denso=True,
    )


# As cores do slide da limitacao: vermelho para o que o modelo disse, cinza
# para a regua, verde para as saidas que dependem so do que ja temos.
COR_DO_QUE_O_MODELO_DISSE = "#C0392B"
COR_DA_REGUA_NA_LIMITACAO = "#8A94A6"
COR_DA_SAIDA_POSSIVEL = "#1F7A4D"


def _slide_limitacao_de_2026() -> deck.Slide:
    """O alarme que tocou num ano sem dengue, e o que faltaria para evita-lo.

    Slide novo de 27/09/2026. Nasceu de uma preocupacao do Vinicius — o modelo
    aprendeu numa serie que so cresce, e 2026 nao teve dengue — e a medicao deu
    razao a ele: em marco de 2026 o composto previu 1.808 casos para uma semana
    que teve ZERO, e disparou alarme em 10 das 17 semanas do ano em 3 meses.

    ⚠️ **A regua falha junto**, com 9 disparos. Isso e deliberado no slide: sem
    ela, a limitacao parece defeito deste modelo, quando e o limite de qualquer
    metodo que so olhe casos, clima e vetor.

    ⚠️ **As saidas respeitam a regra de nao contar com dado novo da
    Prefeitura.** As tres primeiras sao engenharia de atributo sobre a serie que
    ja esta em disco; a quarta e declarada indisponivel de proposito, para nao
    virar promessa que o projeto nao pode cumprir.
    """
    cabecalhos_de_2026 = [
        "Horizonte",
        "Maior real",
        _celula_colorida("Maior previsto", COR_DO_QUE_O_MODELO_DISSE),
        _celula_colorida("Alarmes do modelo", COR_DO_QUE_O_MODELO_DISSE),
        _celula_colorida("Alarmes da régua", COR_DA_REGUA_NA_LIMITACAO),
    ]
    linhas_de_2026 = []
    classes_das_linhas = []
    for linha in numeros.ALARME_FALSO_EM_2026:
        disparou = linha.alarmes_do_modelo > 0
        linhas_de_2026.append(
            [
                f"<b>{layout.escapar(linha.rotulo)}</b>",
                f"<b>{numeros.formatar_decimal(linha.maior_real, 0)}</b>",
                _celula_colorida_com_destaque(
                    numeros.formatar_decimal(linha.maior_previsto, 0),
                    COR_DO_QUE_O_MODELO_DISSE,
                    disparou,
                ),
                _celula_colorida_com_destaque(
                    f"{linha.alarmes_do_modelo} de {linha.semanas}",
                    COR_DO_QUE_O_MODELO_DISSE,
                    disparou,
                ),
                _celula_colorida(
                    f"{linha.alarmes_da_regua} de {linha.semanas}",
                    COR_DA_REGUA_NA_LIMITACAO,
                ),
            ]
        )
        classes_das_linhas.append("linhaVencedora" if disparou else "")

    cabecalhos_das_saidas = ["O que acrescentar", "O que isso captura", "Precisa de"]
    linhas_das_saidas = []
    for saida in numeros.SAIDAS_PARA_A_LIMITACAO:
        # Sem emoticon: a distincao entre o que da para fazer e o que nao da
        # fica so na cor, que ja marcava a coluna "Precisa de" e agora marca o
        # nome da ideia tambem.
        cor = COR_DA_SAIDA_POSSIVEL if saida.temos else COR_DO_QUE_O_MODELO_DISSE
        linhas_das_saidas.append(
            [
                _celula_colorida_com_destaque(
                    layout.escapar(saida.ideia), cor, True
                ),
                layout.escapar(saida.captura),
                _celula_colorida(layout.escapar(saida.precisa_de), cor),
            ]
        )

    as_duas_tabelas = (
        '<div class="deckTabelasLadoALado">'
        f'<div><p class="deckTabelaRotulo" style="color:{COR_DO_QUE_O_MODELO_DISSE}">'
        f"2026 — {numeros.CASOS_EM_2026} casos no ano inteiro "
        f'<span style="font-weight:400;opacity:.62">· maior semana: '
        f"{numeros.MAIOR_SEMANA_DE_2026} casos</span></p>"
        f"{layout.montar_tabela(cabecalhos_de_2026, linhas_de_2026, classes_das_linhas=classes_das_linhas)}</div>"
        f'<div><p class="deckTabelaRotulo" style="color:{COR_DA_SAIDA_POSSIVEL}">'
        "Possibilidades de alternativas</p>"
        f"{layout.montar_tabela(cabecalhos_das_saidas, linhas_das_saidas)}</div>"
        "</div>"
    )

    return deck.Slide(
        topico=TOPICO_RESULTADOS,
        titulo="A limitação: o modelo não sabe quem já teve dengue",
        rotulo_curto="A limitação",
        corpo=as_duas_tabelas,
        nota=(
            "🔴 <b>O número para dizer em voz alta:</b> em <b>22/03/2026</b> o modelo "
            "previu <b>1.808 casos</b> para uma semana que teve <b>zero</b>. Ele "
            "aprendeu o calendário e a tendência de alta da série — 5.583 casos em "
            "2022, 24.793 em 2025 — e projetou a continuação. As armadilhas "
            "continuaram pegando mosquito; o que mudou não está em nenhuma coluna "
            "dele. "
            "🔴 <b>Este slide é a limitação, e ele é meu escudo, não meu problema.</b> "
            "Mostrar que eu conheço o limite do modelo, com número, vale mais que "
            "esconder. ⚠️ <b>Dizer que a régua falha junto</b>: 9 disparos contra 10 "
            "do modelo em 3 meses. Não é defeito deste modelo — é o limite de "
            "qualquer método que só olhe casos, clima e vetor. ⚠️ <b>Em 1 semana não "
            "há nenhum alarme falso</b>: ali manda o histórico recente de casos, que "
            "dizia 'quase nada'. O erro cresce com o horizonte, onde o calendário e o "
            "vetor mandam. 🟢 <b>As três primeiras saídas não exigem dado novo</b> — "
            "são engenharia de atributo sobre a série que já temos, e é isso que "
            "torna a proposta viável. A quarta está ali para ser honesta sobre o que "
            "faria falta e não existe. ⚠️ Nenhum número de erro de 2026 entra aqui: "
            "prever 12 casos a partir de uma série crescente é impossível, e a "
            "pergunta deste bloco é binária."
        ),
        e_denso=True,
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
        _slide_da_folha_5(),
        _slide_folha_5_contra_folha_20(),
        _slide_modelo_composto(),
        _slide_do_modelo_ao_alarme(),
        _slide_estagios_do_plano(),
        _slide_alarme_do_composto(),
        _slide_o_vetor(),
        _slide_os_dois_anos(),
        _slide_onde_ainda_falha(),
        _slide_literatura(),
        _slide_limitacao_de_2026(),
        _slide_proximos_passos(),
    ]


def montar_metricas() -> list[layout.Metrica]:
    """Sem régua: o palco do deck ocupa a página."""
    return []


def montar_corpo() -> str:
    """Só o deck: a página inteira é a apresentação.

    A trilha vai só com as bolinhas. Com dezenove slides, os rótulos poluíam
    mais do que orientavam: o tópico se repetia onze vezes seguidas e os nomes
    curtos saíam truncados com reticências. As bolinhas dizem o que a trilha
    precisa dizer — onde estou e quanto falta. O tópico e o título continuam
    no próprio slide.
    """
    return deck.montar(montar_slides(), mostrar_rotulos=False)
