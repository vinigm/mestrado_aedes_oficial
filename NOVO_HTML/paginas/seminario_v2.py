"""Seminário de Andamento — revisão de 26/09/2026.

⚠️ **Esta página é uma CÓPIA de trabalho.** A página `seminario.py` continua
intacta, contando a versão de 23/09/2026, e é ela que vai ao ar se o Vinicius
decidir usar a original. Nada aqui altera aquela.

**Por que a cópia existe.** Os slides de 23/09 foram montados antes das rodadas
de 25 e 26/09/2026, que mudaram o que pode ser afirmado:

- a régua sazonal — repetir a mesma semana do ano anterior — **vence** o modelo
  em 2 e 3 meses;
- o alarme de 1 mês tem números altos, mas a vantagem sobre as regras simples
  **não sobrevive** ao teste de McNemar com correção de Holm;
- a calibração das faixas é boa na calmaria e ruim em epidemia;
- pelo escore de intervalo ponderado, o modelo **vence** a régua climatológica
  em 1 mês, e isso tem significância.

A apresentação antiga prometia um modelo de previsão de casos sem dizer que uma
regra trivial o supera em 3 meses. Apresentar isso e ser perguntado depois é o
pior cenário possível — daí a revisão.

**A sequência.** Referência da literatura → comparação com os nossos números →
a régua, dita por nós antes que perguntem → a virada para classificação de
nível de alerta → o que está medido → por que não é defeito de configuração →
direcionamentos.

**O desenho segue o pedido:** o mínimo de texto, o máximo de tabela e gráfico.
"""

import deck
import graficos
import layout
import numeros_do_projeto as numeros

import cenario_adotado as pagina_do_cenario_adotado


# Tópicos da apresentação, na ordem. A agenda e o índice horizontal leem daqui,
# para que não possam divergir.
TOPICO_AGENDA = "Agenda"
TOPICO_PROBLEMA = "O problema"
TOPICO_LITERATURA = "A literatura"
TOPICO_REGUA = "A régua"
TOPICO_VIRADA = "A virada"
TOPICO_MEDIDO = "O que está medido"
TOPICO_LIMITE = "O limite"
TOPICO_PROXIMOS = "Direcionamentos"

TOPICOS_DA_AGENDA = (
    TOPICO_PROBLEMA,
    TOPICO_LITERATURA,
    TOPICO_REGUA,
    TOPICO_VIRADA,
    TOPICO_MEDIDO,
    TOPICO_LIMITE,
    TOPICO_PROXIMOS,
)

# Cores usadas para separar, num mesmo gráfico, o que é modelo do que é régua.
COR_DO_MODELO = "var(--acento)"
COR_DA_REGUA = "var(--texto-fraco)"
COR_DE_ALERTA = "var(--critico)"


def _porcentagem(fracao: float) -> str:
    """Formata uma fração como percentual com uma casa, à brasileira."""
    return numeros.formatar_percentual(fracao, 1)


# Abaixo deste valor, escrever o p com três casas vira "0,001" e esconde a
# ordem de grandeza — o que muda a leitura de quão forte é o resultado.
MENOR_P_ESCRITO_POR_EXTENSO = 0.001


def _valor_de_p(p: float) -> str:
    """Escreve um valor-p sem que o arredondamento esconda a ordem de grandeza.

    Args:
        p: O valor-p já corrigido por Holm.

    Returns:
        O número com três casas, ou "menor que 0,001" quando for pequeno
        demais para caber nelas.
    """
    if p < MENOR_P_ESCRITO_POR_EXTENSO:
        return "menor que 0,001"

    return numeros.formatar_decimal(p, 3)


def _slide_capa() -> deck.Slide:
    """Abertura. Sem tópico, então fica fora do índice horizontal."""
    return deck.Slide(
        topico="",
        titulo="Quanto vale a rede de armadilhas para antecipar a dengue em Porto Alegre",
        corpo=layout.montar_cartao(
            "Seminário de andamento",
            "",
            "<p>Vinicius Guerra · PPGC/UFRGS · orientação do Prof. Weverton Cordeiro</p>"
            "<p class='cartaoSub'>Revisão de 26/09/2026</p>",
        ),
        nota=(
            "Abrir dizendo que a apresentação tem um resultado positivo e um "
            "negativo, e que os dois vêm medidos. Não esconder o negativo para o fim."
        ),
    )


def _slide_agenda() -> deck.Slide:
    """O percurso, para a banca saber onde a argumentação chega."""
    itens = [f"<b>{layout.escapar(topico)}</b>" for topico in TOPICOS_DA_AGENDA]
    return deck.Slide(
        topico=TOPICO_AGENDA,
        titulo="O percurso desta apresentação",
        rotulo_curto="Agenda",
        corpo=layout.montar_grade(
            [layout.montar_cartao("", "", item) for item in itens], colunas=4
        ),
        nota="Sete blocos, dez minutos. Avisar que a régua aparece cedo, de propósito.",
    )


def _slide_o_problema() -> deck.Slide:
    """Por que três meses é o problema difícil, com a autocorrelação."""
    cartoes = [
        layout.montar_cartao(
            "1 semana à frente",
            "Fácil",
            "<p>A semana que vem se parece com a de hoje.</p>",
        ),
        layout.montar_cartao(
            "3 meses à frente",
            "Difícil",
            "<p>A memória da série não informa mais nada. Sobra o calendário.</p>",
        ),
        layout.montar_cartao(
            "E daí decorre",
            "O adversário",
            "<p>Se só a sazonalidade informa, uma regra que só olha o calendário é forte.</p>",
        ),
    ]
    return deck.Slide(
        topico=TOPICO_PROBLEMA,
        titulo="Três meses é o prazo que a vigilância precisa — e é onde o problema é difícil",
        rotulo_curto="O problema",
        corpo=layout.montar_grade(cartoes, colunas=3),
        nota=(
            "Este slide monta a armadilha do resto da apresentação: se em três "
            "meses só a sazonalidade informa, a régua sazonal é adversário duro. "
            "Não adiantar o resultado ainda."
        ),
    )


def _slide_porto_alegre() -> deck.Slide:
    """O contexto que diferencia Porto Alegre da literatura."""
    cabecalhos = ["Ano", "Casos confirmados em Porto Alegre"]
    linhas = [
        ["2022", "5.144"],
        ["2023", "6.461"],
        ["2024", "<b>17.686</b>"],
        ["2025", "<b>21.329</b> (parcial até 20/11)"],
    ]
    return deck.Slide(
        topico=TOPICO_PROBLEMA,
        titulo="Porto Alegre está na fronteira de expansão da dengue — não é área endêmica",
        rotulo_curto="Porto Alegre",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                "critico",
                "O que isso custa",
                "Entre 2018 e 2021 quase não houve casos. A série tem "
                f"<b>{numeros.BLOCOS_DE_SURTO} epidemias</b> para aprender. "
                "A literatura de previsão trabalha com vinte, trinta ou quarenta anos.",
            )
        ),
        nota=(
            "Fonte dos números: Plano Municipal de Contingência de 2026. "
            "Este slide é a defesa antecipada de tudo que vem depois."
        ),
    )


def _slide_literatura() -> deck.Slide:
    """O teto do que é possível com série longa, e o estudo da mesma cidade."""
    cabecalhos = ["Estudo", "Série", "O que mediram", "Comparável?"]
    linhas = [
        [
            "Singapura",
            "mais de 20 anos",
            "sistema operacional de previsão",
            "<b>Não</b> — série e contexto diferentes",
        ],
        [
            "Porto Rico",
            "<b>38,5 anos</b>",
            "limiar de alerta por percentil",
            "<b>Não</b> — o método exige a série longa",
        ],
        [
            "da Silva et al. 2026 · <b>mesma cidade e armadilha</b>",
            "2018 a 2025",
            "correlação com defasagem de 0 a 4 semanas",
            "<b>Não</b> — alvo e validação diferentes",
        ],
    ]
    return deck.Slide(
        topico=TOPICO_LITERATURA,
        titulo="O que a literatura obtém, e por que quase nada é comparável direto",
        rotulo_curto="A literatura",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                "atencao",
                "Ressalva que vai junto",
                "O estudo da mesma cidade é <b>preprint não revisado por pares</b> "
                "e valida por validação cruzada embaralhada no tempo — o mesmo tipo "
                "de defeito que corrigimos aqui em 13/09/2026.",
            )
        ),
        nota=(
            "Dizer que comparação entre estudos é de CONTEXTO, não ranking. "
            "Se perguntarem do da Silva, a diferença está na coluna 'comparável'."
        ),
        e_denso=True,
    )


def _slide_regua() -> deck.Slide:
    """A régua sazonal contra o modelo — o resultado negativo, dito por nós."""
    por_metodo = {
        metodo.metodo: metodo for metodo in numeros.REGUA_DE_METODOS_SIMPLES
    }
    modelo = por_metodo["Cenário adotado"]
    regua = por_metodo["Mesma semana do ano passado"]

    horizontes = (
        ("1 semana", modelo.uma_semana, regua.uma_semana),
        ("1 mês", modelo.um_mes, regua.um_mes),
        ("2 meses", modelo.dois_meses, regua.dois_meses),
        ("3 meses", modelo.tres_meses, regua.tres_meses),
    )

    itens = []
    cores = []
    for rotulo, erro_do_modelo, erro_da_regua in horizontes:
        itens.append(
            (
                f"{rotulo} · modelo",
                numeros.formatar_decimal(erro_do_modelo, 1),
                erro_do_modelo,
            )
        )
        cores.append(COR_DO_MODELO)
        itens.append(
            (
                f"{rotulo} · régua sazonal",
                numeros.formatar_decimal(erro_da_regua, 1),
                erro_da_regua,
            )
        )
        cores.append(COR_DE_ALERTA if erro_da_regua < erro_do_modelo else COR_DA_REGUA)
    return deck.Slide(
        topico=TOPICO_REGUA,
        titulo="Em 3 meses, repetir a mesma semana do ano passado erra menos que o modelo",
        rotulo_curto="A régua sazonal",
        corpo=(
            graficos.montar_grafico_de_barras_horizontais(
                itens,
                "Erro absoluto médio, em casos por semana — menor é melhor",
                cores=cores,
                nota=(
                    "Avaliação de 2024 a fevereiro de 2026, 102 semanas pareadas "
                    "por data-alvo. Em vermelho, onde a régua vence."
                ),
            )
            + layout.montar_aviso(
                "info",
                "Por que dizemos isso primeiro",
                "É o resultado mais desconfortável da pesquisa, e é o primeiro que "
                "alguém checaria. Perder para a régua em horizonte longo é comum na "
                "literatura da área.",
            )
        ),
        nota=(
            "Dizer em voz alta: 'a régua nos vence em dois e três meses'. "
            "Não deixar para a banca descobrir. Em UMA semana o modelo ganha com folga."
        ),
    )


def _slide_a_virada() -> deck.Slide:
    """De cravar o número para classificar o nível de alerta."""
    cartoes = [
        layout.montar_cartao(
            "O que era",
            "Cravar o número",
            "<p>Quantos casos haverá na semana X? Exige acertar a magnitude.</p>",
        ),
        layout.montar_cartao(
            "O que passa a ser",
            "Classificar o nível",
            "<p>Em que estágio de resposta a cidade estará? Basta cruzar o limiar.</p>",
        ),
        layout.montar_cartao(
            "Por que é legítimo",
            "Já é o que o modelo faz",
            "<p>Prever o quantil 0,85 acima de um limiar <b>é</b> dizer que a chance de "
            "ultrapassá-lo passa de 15%.</p>",
        ),
    ]
    return deck.Slide(
        topico=TOPICO_VIRADA,
        titulo="A virada: de cravar o número para classificar o nível de alerta",
        rotulo_curto="A virada",
        corpo=(
            layout.montar_grade(cartoes, colunas=3)
            + layout.montar_aviso(
                "bom",
                "Referência",
                "Porto Rico converteu vigilância contínua num sistema de limiares de "
                "alerta que dispara ação de governo. Adotamos o <b>conceito</b>; o "
                "método de cálculo deles exige 38,5 anos de série.",
            )
        ),
        nota=(
            "O terceiro cartão é o fundamento matemático: quantil e probabilidade "
            "são a mesma coisa vista de dois lados. Se perguntarem, escrever no quadro."
        ),
    )


def _slide_estagios_oficiais() -> deck.Slide:
    """Os limiares não são nossos: vêm do plano da Prefeitura."""
    cabecalhos = ["Estágio", "Incidência no plano", "Casos por semana", "Semanas assim em 2024-25"]
    linhas = [
        [
            f"<b>{layout.escapar(estagio.estagio)}</b>",
            layout.escapar(estagio.incidencia),
            f"<b>{numeros.formatar_inteiro(estagio.casos_por_semana)}</b>",
            numeros.formatar_inteiro(estagio.semanas_acima),
        ]
        for estagio in numeros.ESTAGIOS_DO_PLANO
    ]
    return deck.Slide(
        topico=TOPICO_VIRADA,
        titulo="Os limiares não são nossos — são do Plano Municipal de Contingência",
        rotulo_curto="Limiares oficiais",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                "atencao",
                "Simplificação declarada",
                "No plano, o corte numérico <b>nunca aparece sozinho</b>: vem ligado por "
                "<b>E</b> a limiares estaduais sobre casos prováveis, mais óbito e "
                "sorotipo novo. Usamos só a metade fixa do critério, e isso faz a nossa "
                "versão disparar <b>mais</b> que a oficial.",
            )
        ),
        nota=(
            "Este slide tira de nós a responsabilidade pelo número. "
            "A ressalva é obrigatória — sem ela, estaríamos alegando conformidade."
        ),
    )


def _slide_o_alarme_funciona() -> deck.Slide:
    """O resultado positivo do alarme, em números descritivos."""
    cabecalhos = ["Horizonte", "Pega quantos surtos", "Precisão", "Alarmes falsos por ano"]
    linhas = [
        [
            layout.escapar(alarme.rotulo),
            f"<b>{_porcentagem(alarme.sensibilidade)}</b>",
            _porcentagem(alarme.precisao),
            numeros.formatar_decimal(alarme.falsos_por_ano, 1),
        ]
        for alarme in numeros.ALARME_POR_HORIZONTE
    ]
    return deck.Slide(
        topico=TOPICO_MEDIDO,
        titulo="Como alarme, em 1 mês o modelo pega 97% dos surtos com menos de 1 falso por ano",
        rotulo_curto="O alarme",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                "atencao",
                "O que NÃO está demonstrado",
                "Que essa vantagem supere as regras simples. Ver o próximo slide.",
            )
        ),
        nota=(
            "Números altos e verdadeiros. Mas emendar IMEDIATAMENTE no slide "
            "seguinte — nunca deixar este número sozinho na tela."
        ),
    )


def _slide_o_teste_honesto() -> deck.Slide:
    """🔴 O quadro que impede afirmar vitória em 1 mês."""
    cabecalhos = ["Horizonte", "Contra", "Semanas discordantes", "p de Holm", "Vence?"]
    linhas = []
    for teste in numeros.TESTES_DO_ALARME:
        veredito = (
            layout.montar_etiqueta("sim", "alvo")
            if teste.vence
            else layout.montar_etiqueta("não", "vetor")
        )
        linhas.append(
            [
                layout.escapar(teste.horizonte),
                layout.escapar(teste.regra_base),
                f"{teste.discordantes} ({layout.escapar(teste.divisao)})",
                f"<b>{_valor_de_p(teste.p_holm)}</b>",
                veredito,
            ]
        )
    return deck.Slide(
        topico=TOPICO_MEDIDO,
        titulo="Mas a vantagem em 1 mês não sobrevive ao teste estatístico",
        rotulo_curto="O teste honesto",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                "info",
                "A causa provável é falta de poder, não ausência de efeito",
                "Em 1 mês há apenas <b>15</b> e <b>7</b> semanas em que as regras "
                "discordam — e a divisão é favorável ao modelo. Hipótese, não fato.",
            )
        ),
        nota=(
            "🔴 O slide mais importante da apresentação. Dizer: 'o número é alto, "
            "a vitória não está demonstrada'. Quem apresentar isso antes de ser "
            "perguntado ganha credibilidade para o resto."
        ),
        e_denso=True,
    )


def _slide_onde_vence() -> deck.Slide:
    """O resultado positivo COM significância: o escore de intervalo."""
    itens = []
    cores = []
    for escore in numeros.ESCORE_DE_INTERVALO:
        itens.append(
            (
                f"{escore.horizonte} · modelo adotado",
                numeros.formatar_decimal(escore.adotado, 1),
                escore.adotado,
            )
        )
        cores.append(COR_DO_MODELO)
        itens.append(
            (
                f"{escore.horizonte} · régua climatológica",
                numeros.formatar_decimal(escore.regua_climatologica, 1),
                escore.regua_climatologica,
            )
        )
        cores.append(COR_DA_REGUA)
    return deck.Slide(
        topico=TOPICO_MEDIDO,
        titulo="Onde o modelo vence com significância: a métrica oficial dos sprints brasileiros",
        rotulo_curto="Onde vence",
        corpo=(
            graficos.montar_grafico_de_barras_horizontais(
                itens,
                "Escore de intervalo ponderado — menor é melhor",
                cores=cores,
                nota=(
                    "Avalia a faixa de previsão inteira, não só um número. "
                    "Recorte de 2024 a 2025. Em todos os horizontes o modelo "
                    "fica abaixo da régua."
                ),
            )
            + layout.montar_aviso(
                "bom",
                "Fato medido",
                "Em <b>1 mês</b>, os dois modelos vencem a régua climatológica com "
                "<b>p de Holm menor que 0,0001</b>. Em 3 meses, só o de folha 20 vence.",
            )
        ),
        nota=(
            "Aqui está o resultado positivo defensável. Note que o comparador é "
            "OUTRO: régua climatológica, não 'o ano passado'. Não confundir os dois."
        ),
    )


def _slide_calibracao() -> deck.Slide:
    """O modelo é honesto na calmaria e confiante demais na epidemia."""
    cabecalhos = ["Faixa de casos reais", "Semanas", "Intervalo de 50%", "Intervalo de 90%"]
    linhas = [
        [
            layout.escapar(faixa.faixa),
            numeros.formatar_inteiro(faixa.semanas),
            _porcentagem(faixa.cobertura_50),
            f"<b>{_porcentagem(faixa.cobertura_90)}</b>",
        ]
        for faixa in numeros.CALIBRACAO_POR_FAIXA
    ]
    return deck.Slide(
        topico=TOPICO_MEDIDO,
        titulo="O modelo sabe quando está calmo — e não sabe que não sabe na epidemia",
        rotulo_curto="A calibração",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                "critico",
                "Reconhecemos a subestimação",
                f"Nas semanas de surto o modelo captura em média "
                f"<b>{_porcentagem(numeros.CAPTURA_DO_PICO_TRES_MESES)}</b> da magnitude "
                f"real: numa semana com <b>{numeros.REAL_MEDIANO_EM_EPIDEMIA}</b> casos, "
                f"prevê por volta de <b>{numeros.SEMANA_DE_PICO_PREVISTA}</b>. "
                "Testamos raiz e logaritmo para corrigir: <b>pioraram</b>.",
            )
        ),
        nota=(
            "O esperado seria 50% e 90%. Na calmaria bate; acima de 421 casos "
            "cobre 17,8%. Dizer que por isso a faixa NÃO deve ser usada para "
            "dimensionar recursos."
        ),
        e_denso=True,
    )


def _slide_nao_e_configuracao() -> deck.Slide:
    """Por que o limite não é de código nem de ajuste."""
    cabecalhos = ["O que foi testado", "Quantas variantes", "Veredito"]
    linhas = [
        [
            f"<b>{layout.escapar(abordagem.abordagem)}</b>",
            layout.escapar(abordagem.quantidade),
            layout.escapar(abordagem.veredito),
        ]
        for abordagem in numeros.ABORDAGENS_TESTADAS
    ]
    return deck.Slide(
        topico=TOPICO_LIMITE,
        titulo="Não é defeito de configuração — é limite dos dados",
        rotulo_curto="Não é config",
        corpo=(
            layout.montar_tabela(cabecalhos, linhas)
            + layout.montar_aviso(
                "critico",
                "A raiz do limite",
                f"As semanas de surto formam <b>{numeros.BLOCOS_DE_SURTO} blocos "
                f"contíguos</b>, um em 2024 e outro em 2025. Faltam também sorotipo "
                "circulante, imunidade populacional e mobilidade entre os atributos.",
            )
        ),
        nota=(
            "Não dizer 'nenhum algoritmo de machine learning consegue'. Dizer "
            "'nenhuma arquitetura que testamos'. A diferença é o que separa uma "
            "afirmação sustentada de uma alegação teórica."
        ),
        e_denso=True,
    )


def _slide_o_metodo() -> deck.Slide:
    """O rigor do processo, que é contribuição e costuma ser subvendido."""
    cartoes = [
        layout.montar_cartao(
            "Vazamento temporal",
            f"+{_porcentagem(numeros.VAZAMENTO.piora_do_erro_em_tres_meses)} de erro",
            "<p>Identificado, quantificado e corrigido em 13/09/2026.</p>",
        ),
        layout.montar_cartao(
            "Pré-declaração",
            "Antes de cada rodada",
            "<p>Hipótese, métrica e critério escritos antes de medir.</p>",
        ),
        layout.montar_cartao(
            "Certificação adversarial",
            "Por avaliador independente",
            "<p>Que tenta reprovar o resultado, medindo do zero.</p>",
        ),
        layout.montar_cartao(
            "Réguas triviais",
            "Sempre no gráfico",
            "<p>O modelo é comparado com regras simples, não só consigo mesmo.</p>",
        ),
    ]
    return deck.Slide(
        topico=TOPICO_LIMITE,
        titulo="O método é parte da contribuição",
        rotulo_curto="O método",
        corpo=layout.montar_grade(cartoes, colunas=4),
        nota=(
            "A literatura da área raramente faz isso. O vazamento temporal é o "
            "exemplo concreto: era um defeito real, foi medido e foi corrigido."
        ),
    )


def _slide_direcionamentos() -> deck.Slide:
    """O último slide, como o orientador pediu em 21/09/2026."""
    cabecalhos = ["Direcionamento", "Por quê", "Quando"]
    linhas = [
        [
            "<b>Teoria de valores extremos</b>",
            "existe exatamente para eventos raros, que é o nosso problema declarado",
            "antes do artigo",
        ],
        [
            "<b>Confirmar na temporada 2026-2027</b>",
            "só uma epidemia nova torna qualquer achado confirmatório",
            "jul/2027",
        ],
        [
            "<b>Estimar a defasagem entre vetor e casos</b>",
            "o estudo da mesma cidade mediu; nós não",
            "antes do artigo",
        ],
        [
            "<b>Alarme por estágio do plano municipal</b>",
            "entrega que a Secretaria usa direto",
            "próxima etapa",
        ],
        [
            "<b>Calibração condicionada ao nível</b>",
            "a correção constante não resolve; o defeito depende do nível",
            "próxima etapa",
        ],
    ]
    return deck.Slide(
        topico=TOPICO_PROXIMOS,
        titulo="Direcionamentos",
        rotulo_curto="Direcionamentos",
        corpo=layout.montar_tabela(cabecalhos, linhas),
        nota=(
            "Último slide, como pedido em 21/09/2026. A teoria de valores extremos "
            "vem primeiro de propósito: é a lacuna que um estatístico apontaria, e "
            "é melhor dizermos antes."
        ),
        e_denso=True,
    )


def montar_slides() -> list[deck.Slide]:
    """A apresentação inteira, na ordem em que será projetada."""
    return [
        _slide_capa(),
        _slide_agenda(),
        _slide_o_problema(),
        _slide_porto_alegre(),
        _slide_literatura(),
        _slide_regua(),
        _slide_a_virada(),
        _slide_estagios_oficiais(),
        _slide_o_alarme_funciona(),
        _slide_o_teste_honesto(),
        _slide_onde_vence(),
        _slide_calibracao(),
        _slide_nao_e_configuracao(),
        _slide_o_metodo(),
        _slide_direcionamentos(),
    ]


def montar_metricas() -> list[layout.Metrica]:
    """A página é o próprio deck, então não tem régua de métricas no topo."""
    return []


def montar_corpo() -> str:
    """Monta o deck inteiro para a página."""
    return deck.montar(montar_slides())
