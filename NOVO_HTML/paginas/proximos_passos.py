"""Página de próximos passos: por que a investigação continua, e para onde vai.

⚠️ Esta página tem um equilíbrio delicado e deliberado.

O projeto mediu que a contagem de armadilha não melhora a previsão de casos e
piora o alarme de surto em horizonte longo. Esse resultado **continua válido e
continua publicado** na página do cenário adotado — nada aqui o desmente, e
nada aqui pode desmenti-lo sem medição nova.

O que esta página faz é outra coisa: mostra que a leitura "o mosquito não
importa" **não se deduz** desse resultado, e lista as razões concretas pelas
quais o desenho atual pode não estar captando um sinal que existe. Tudo o que
é leitura, e não medição, aparece rotulado como hipótese.
"""

import layout
import navegacao
import numeros_do_projeto as numeros


def _secao_o_que_os_dados_mostram() -> str:
    """A defasagem visível entre a curva do vetor e a curva dos casos."""
    figura = layout.montar_figura(
        arquivo="imagens/slide_vetor_vs_casos_anotado.png",
        titulo="",
        subtitulo="",
        legenda=(
            "Barras azuis: mosquitos capturados. Linha vermelha: casos "
            "confirmados. As setas marcam onde cada série começa a subir — em "
            "<b>2022, 2023, 2024 e 2025</b> a do mosquito vem <b>antes</b>. "
            "⚠️ Leitura de gráfico — a defasagem ainda não foi medida."
        ),
    )

    return figura


def _secao_por_que_a_questao_segue_aberta() -> str:
    """O contraste entre o que foi medido e o que não se deduz disso."""
    contraste = layout.montar_grade(
        [
            layout.montar_cartao(
                rotulo="✅ O que foi medido",
                titulo="",
                corpo=(
                    "<p>Sobre um modelo que <b>já tem clima e histórico de "
                    "casos</b>, a armadilha não melhora a previsão.</p>"
                ),
            ),
            layout.montar_cartao(
                rotulo="🚫 O que NÃO se deduz",
                titulo="",
                corpo=(
                    "<p>Que o mosquito não influencia a doença. "
                    "<b>Sem vetor não há transmissão</b> — isso é biologia.</p>"
                ),
            ),
        ],
        colunas=2,
    )

    quatro_hipoteses = layout.montar_grade(
        [
            layout.montar_cartao(
                rotulo="Hipótese 01 · o alvo",
                titulo="Prevemos a consequência",
                corpo=(
                    "<p>Quando o caso é notificado, a transmissão <b>já "
                    "aconteceu</b>. A causa é a proliferação do vetor.</p>"
                ),
            ),
            layout.montar_cartao(
                rotulo="Hipótese 02 · saturação",
                titulo="O histórico já diz tudo",
                corpo=(
                    f"<p>Os casos recentes explicam "
                    f"<b>{numeros.formatar_percentual(numeros.DEGRADACAO.fracao_explicada_em_uma_semana, 0)}"
                    "</b> do acerto em uma semana. <b>Redundante ≠ "
                    "irrelevante.</b></p>"
                ),
            ),
            layout.montar_cartao(
                rotulo="Hipótese 03 · horizonte",
                titulo="Paramos em 3 meses",
                corpo=(
                    "<p>A defasagem do gráfico parece maior. Efeito fora da "
                    "janela medida <b>não aparece</b>.</p>"
                ),
            ),
            layout.montar_cartao(
                rotulo="Hipótese 04 · escopo",
                titulo="Só a dengue tem alvo",
                corpo=(
                    "<p>O mesmo mosquito transmite <b>quatro doenças</b>. "
                    "Três ficaram de fora da conta.</p>"
                ),
            ),
            layout.montar_cartao(
                rotulo="Hipótese 05 · biologia",
                titulo="Mosquito não é vírus",
                corpo=(
                    "<p>A armadilha conta mosquito, não mosquito "
                    "<b>infectado</b>. Pode haver muito vetor e pouco vírus "
                    "circulando — e o PCR do mosquito deixou de ser feito.</p>"
                ),
            ),
        ],
        colunas=3,
    )

    return contraste + quatro_hipoteses


def _secao_o_que_muda() -> str:
    """O novo desenho, em tabela de antes e depois."""
    cabecalhos = ["", "Hoje", "Próxima etapa"]
    linhas = [
        [
            "<b>Alvo primário</b>",
            "casos de dengue",
            "casos das <b>quatro arboviroses</b>, previstos <b>a partir da "
            "proliferação do vetor</b>",
        ],
        [
            "<b>Alvo secundário</b>",
            "—",
            "<b>a própria proliferação do vetor</b>, a partir de clima e captura",
        ],
        ["<b>Horizonte</b>", "até 3 meses", "até <b>6 meses</b>"],
        [
            "<b>Treino e teste</b>",
            "toda a série disponível",
            "treinar em <b>2022-2024</b>, prever <b>2025</b>",
        ],
        [
            "<b>Pergunta</b>",
            "o vetor melhora a previsão?",
            "<b>qual é a defasagem</b> entre as duas curvas?",
        ],
        [
            "<b>Espécie</b>",
            "Aedes aegypti",
            "<b>Aedes aegypti</b> — Culex fica de fora",
        ],
    ]

    justificativa = layout.montar_aviso(
        tom="bom",
        rotulo="Por que somar as arboviroses é legítimo",
        texto=(
            "<b>Um único vetor</b> transmite as quatro. Sem transmissão pessoa "
            "a pessoa, sem outro artrópode. Somar não mistura fenômenos — "
            "agrupa manifestações do <b>mesmo</b> evento entomológico. "
            "⏳ Cada decisão dessas precisa de <b>referência bibliográfica</b> "
            "que a respalde."
        ),
    )

    return layout.montar_tabela(cabecalhos, linhas) + justificativa


def _secao_literatura_a_buscar() -> str:
    """O levantamento bibliográfico que o desenho novo exige.

    Entra porque a biologia do vetor mudou nas últimas décadas, e a mudança
    afeta como a série de captura deve ser lida — um mesmo número de mosquitos
    não significa o mesmo risco hoje e há dez anos.
    """
    cartoes = [
        layout.montar_cartao(
            rotulo="01",
            titulo="Ovos que atravessam o inverno",
            corpo=(
                "<p>A temporada termina com ovos que não eclodiram e seguem "
                "<b>viáveis até a seguinte</b>. Uma temporada intensa pode "
                "carregar risco para a próxima.</p>"
            ),
        ),
        layout.montar_cartao(
            rotulo="02",
            titulo="Transmissão pelo ovo",
            corpo=(
                "<p>O mosquito pode <b>já nascer com o vírus</b>, sem precisar "
                "picar alguém doente antes. Muda a dinâmica clássica de "
                "transmissão.</p>"
            ),
        ),
        layout.montar_cartao(
            rotulo="03",
            titulo="Criadouro menos exigente",
            corpo=(
                "<p>A dependência de <b>água parada e limpa</b> não é mais o "
                "que era. Afeta onde o vetor consegue se desenvolver.</p>"
            ),
        ),
        layout.montar_cartao(
            rotulo="04",
            titulo="Limiar térmico do ovo",
            corpo=(
                "<p>Abaixo de certa temperatura o ovo <b>inviabiliza</b> — a "
                "hipótese que explica por que há regiões estéreis ao vetor "
                "apesar de clima aparentemente favorável.</p>"
            ),
        ),
    ]

    porque = layout.montar_aviso(
        tom="info",
        rotulo="Por que isso entra na modelagem",
        texto=(
            "Se a biologia do vetor mudou, <b>o mesmo número de mosquitos não "
            "significa o mesmo risco</b> em 2013 e em 2026. Ler a série de 14 "
            "anos sem isso é tratar como homogêneo um fenômeno que não é."
        ),
    )

    return layout.montar_grade(cartoes, colunas=4) + porque


def _secao_o_que_precisa_ser_verificado() -> str:
    """As ressalvas já medidas, em tabela de risco e verificação."""
    cabecalhos = ["Risco", "O número que já se conhece", "O que medir antes"]
    linhas = [
        [
            "<b>Agregar soma pouco</b>",
            "chikungunya: dezenas de casos<br>zika: <b>zero</b> desde 2022",
            "o ganho real de volume",
        ],
        [
            "<b>Poucas epidemias no teste</b>",
            f"a janela <b>{numeros.JANELA_UTIL_DE_TRABALHO}</b> deixa ~1 episódio",
            "se a janela sustenta conclusão",
        ],
        [
            "<b>6 meses pode não alcançar</b>",
            "a memória dos casos já é <b>nula</b> em 3 meses",
            "o horizonte útil para o vetor",
        ],
    ]

    honestidade = layout.montar_aviso(
        tom="atencao",
        rotulo="Esta página não revoga nada",
        texto=(
            "O resultado do cenário adotado <b>continua válido</b>. O que muda "
            "é alvo, horizonte e conjunto de doenças — e cada teste exigirá "
            "<b>pré-declaração escrita antes de rodar</b>."
        ),
    )

    return layout.montar_tabela(cabecalhos, linhas) + honestidade


def _secao_o_desafio() -> str:
    """A previsão guardada para conferência futura."""
    return layout.montar_grade(
        [
            layout.montar_cartao(
                rotulo="Hoje",
                titulo="Gerar a curva prevista",
                corpo="<p>Captura de mosquito para a temporada <b>2026-2027</b>.</p>",
            ),
            layout.montar_cartao(
                rotulo="Julho de 2027",
                titulo="Comparar com o real",
                corpo="<p>Previsão registrada <b>antes</b>, sem ajuste posterior.</p>",
            ),
        ],
        colunas=2,
    )


def montar_metricas() -> list[layout.Metrica]:
    """Sem régua de números: esta página é de direção, não de resultado."""
    return []


def montar_corpo() -> str:
    """Monta o corpo da página, seção por seção, na ordem da navegação."""
    montadores_por_ancora = {
        "o-que-se-ve": _secao_o_que_os_dados_mostram,
        "questao-aberta": _secao_por_que_a_questao_segue_aberta,
        "o-que-muda": _secao_o_que_muda,
        "literatura": _secao_literatura_a_buscar,
        "a-verificar": _secao_o_que_precisa_ser_verificado,
        "o-desafio": _secao_o_desafio,
    }

    blocos = []
    for ordem, secao in enumerate(navegacao.PAGINA_PROXIMOS_PASSOS.secoes, start=1):
        montador = montadores_por_ancora[secao.ancora]
        blocos.append(layout.montar_secao(secao, ordem, intro="", corpo=montador()))

    return "".join(blocos)
