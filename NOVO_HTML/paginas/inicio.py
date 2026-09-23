"""Página inicial: a porta de entrada da pesquisa.

Reduzida a pedido do autor em 23/09/2026 ao essencial — a régua de números e o
caminho que o dado percorre. As cinco seções de texto que existiam antes (o
problema, por que importa, a contribuição, o que já se sabe e como navegar)
foram retiradas; o conteúdo delas está no histórico do arquivo, em `git log`.
"""

import layout
import navegacao
import numeros_do_projeto as numeros


# O caminho que o dado percorre, da fonte ao painel. Uma etapa por tupla,
# na ordem em que acontecem: (nome, o que acontece ali).
CAMINHO_DOS_DADOS = [
    ("Fontes", "mosquito, clima, casos, El Niño"),
    ("Montagem", "junta tudo por semana (tabela_final)"),
    ("Experimento", "treina o modelo e mede o acerto"),
    ("Resultados", "métricas, gráficos e este painel"),
]


def montar_metricas() -> list[layout.Metrica]:
    """Os quatro números que resumem a pesquisa para quem chega agora.

    A escolha é deliberada: três medem a base de dados construída, que é a
    contribuição mais sólida do trabalho, e um mede o desempenho que sobrevive
    à correção do vazamento. Números de esforço, como quantos modelos foram
    treinados, ficam de fora porque não dizem nada a quem avalia.
    """
    periodo_da_serie = f"{numeros.BASE.primeira_semana} a {numeros.BASE.ultima_semana}"

    return [
        layout.Metrica(
            rotulo="Série de captura",
            valor=f"{numeros.BASE.semanas_com_dado} semanas",
            nota=periodo_da_serie,
        ),
        layout.Metrica(
            rotulo="Inspeções de armadilha",
            valor=numeros.formatar_inteiro(numeros.BASE.inspecoes),
            nota="conferidas célula a célula",
        ),
        layout.Metrica(
            rotulo="Fêmeas de Aedes aegypti",
            valor=numeros.formatar_inteiro(numeros.BASE.femeas_de_aedes_aegypti),
            nota=(
                f"{numeros.BASE.bairros} bairros · "
                f"{numeros.formatar_inteiro(numeros.BASE.armadilhas)} armadilhas"
            ),
        ),
        layout.Metrica(
            rotulo="Alarme a um mês",
            valor=numeros.formatar_percentual(numeros.ALARME.sensibilidade_um_mes),
            nota="das semanas de surto sinalizadas",
        ),
    ]


def _secao_walk_forward() -> str:
    """Explica a validação walk-forward a partir do diagrama de cortes.

    ⚠️ A figura desenha oito cortes só para caber na página; a avaliação real
    repete o procedimento em toda semana da série. A ressalva foi tirada do
    texto visível a pedido do autor, em 23/09/2026 — se alguém da banca
    perguntar quantos cortes existem, a resposta não está na página.
    """
    figura = layout.montar_figura(
        arquivo="imagens/walkforward.png",
        titulo="Como o modelo é avaliado ao longo do tempo",
        subtitulo=(
            "Cada corte simula um instante real de uso: o modelo só vê o que já "
            "tinha acontecido até ali."
        ),
        legenda="",
    )

    return figura




def _classificar_familia_da_etiqueta(grupo: str) -> str:
    """Decide a família de cor da etiqueta a partir do nome do grupo da coluna.

    Args:
        grupo: Nome do grupo como aparece em `conteudo.DICIONARIO_COLUNAS`
            (ex.: "Vetor", "Alvo", "Clima · chuva", "El Nino", "Nucleo").

    Returns:
        Uma das famílias aceitas por `layout.montar_etiqueta`.
    """
    if grupo.startswith("Vetor"):
        return "vetor"
    if grupo.startswith("Alvo"):
        return "alvo"
    if grupo.startswith("Clima") or grupo.startswith("El Nino"):
        return "clima"
    return "contexto"


# As 36 colunas da tabela única que alimenta os modelos, com acentuação
# corrigida a partir de `pagina_web/conteudo.DICIONARIO_COLUNAS` (que foi
# escrito sem acentos). Cada item é (coluna, grupo, descrição, unidade).
_DICIONARIO_COM_ACENTOS: tuple[tuple[str, str, str, str], ...] = (
    ("fonte", "Núcleo", "De onde veio a linha (Secretaria ou raspagem própria).", "texto"),
    ("SE", "Núcleo", "Semana epidemiológica no formato ANOSS (ex.: 201901).", "código"),
    ("data_inicio_semana_epidemi", "Núcleo", "Data em que a semana epidemiológica começa.", "data"),
    ("ano", "Núcleo", "Ano.", "ano"),
    ("semana", "Núcleo", "Número da semana no ano.", "1-53"),
    ("numero_de_armadilhas", "Vetor", "Quantas armadilhas foram lidas na semana.", "contagem"),
    ("aedes_aegypti", "Vetor", "Aedes aegypti capturados na semana (soma da cidade).", "contagem"),
    ("aedes_albopictus", "Contexto", "Aedes albopictus capturados (outra espécie).", "contagem"),
    ("culex_sp", "Contexto", "Culex sp capturados (pernilongo comum).", "contagem"),
    ("aedes_aegypti_por_armadilha", "Vetor", "Aedes aegypti por armadilha: a densidade do vetor. É a principal medida do mosquito.", "índice"),
    ("denominador_aproximado", "Núcleo", "Diz se o número de armadilhas da semana é aproximado (2012 a 2018, quando o dado não informa quais inspeções foram concluídas).", "0/1"),
    ("precip_total_mm", "Clima · chuva", "Chuva total na semana.", "mm"),
    ("precip_max_dia_mm", "Clima · chuva", "Maior chuva num único dia da semana.", "mm"),
    ("precip_media_dia_mm", "Clima · chuva", "Chuva média por dia na semana.", "mm"),
    ("dias_de_chuva", "Clima · chuva", "Quantos dias choveu na semana.", "dias"),
    ("temp_media", "Clima · temperatura", "Temperatura média da semana.", "°C"),
    ("temp_min", "Clima · temperatura", "Temperatura mínima da semana.", "°C"),
    ("temp_max", "Clima · temperatura", "Temperatura máxima da semana.", "°C"),
    ("temp_amplitude_media", "Clima · temperatura", "Diferença média entre a máxima e a mínima do dia.", "°C"),
    ("orvalho_min", "Clima · orvalho", "Ponto de orvalho mínimo (indica a umidade do ar).", "°C"),
    ("orvalho_media", "Clima · orvalho", "Ponto de orvalho médio.", "°C"),
    ("orvalho_max", "Clima · orvalho", "Ponto de orvalho máximo.", "°C"),
    ("umid_min", "Clima · umidade", "Umidade relativa mínima.", "%"),
    ("umid_media", "Clima · umidade", "Umidade relativa média.", "%"),
    ("umid_max", "Clima · umidade", "Umidade relativa máxima.", "%"),
    ("pressao_min", "Clima · pressão", "Pressão atmosférica mínima.", "kPa"),
    ("pressao_media", "Clima · pressão", "Pressão atmosférica média.", "kPa"),
    ("pressao_max", "Clima · pressão", "Pressão atmosférica máxima.", "kPa"),
    ("radiacao_min", "Clima · radiação", "Radiação solar mínima.", "MJ/m²"),
    ("radiacao_media", "Clima · radiação", "Radiação solar média.", "MJ/m²"),
    ("radiacao_max", "Clima · radiação", "Radiação solar máxima.", "MJ/m²"),
    ("vento_media", "Clima · vento", "Velocidade média do vento.", "m/s"),
    ("vento_max", "Clima · vento", "Velocidade máxima do vento.", "m/s"),
    ("casos_confirmados", "Alvo", "Casos de dengue confirmados na semana. É o que o modelo quer prever.", "contagem"),
    ("nino34_anom", "El Nino", "Anomalia de temperatura do Pacífico (região Niño 3.4).", "°C"),
    ("oni", "El Nino", "Índice ONI: mede a fase El Niño / La Niña.", "°C"),
)


def _tabela_do_dicionario() -> str:
    """Monta a tabela completa das 36 colunas da tabela de modelagem."""
    cabecalhos = ["#", "Coluna", "Grupo", "O que é", "Unidade"]

    linhas = []
    for posicao, (coluna, grupo, descricao, unidade) in enumerate(
        _DICIONARIO_COM_ACENTOS, start=1
    ):
        familia = _classificar_familia_da_etiqueta(grupo)
        linhas.append(
            [
                f'<span class="num">{posicao}</span>',
                f'<code class="nomeColuna">{layout.escapar(coluna)}</code>',
                layout.montar_etiqueta(grupo, familia),
                layout.escapar(descricao),
                layout.escapar(unidade),
            ]
        )

    return layout.montar_tabela(cabecalhos, linhas)


def _tabela_dos_derivados() -> str:
    """De onde vem cada um dos atributos criados em tempo de execução."""
    cabecalhos = ["Coluna de origem", "Atributos que ela gera", "Quantos"]

    lags = ", ".join(
        f"<code>_lag{semana}</code>" for semana in range(1, numeros.ATRIBUTOS.lags_por_coluna + 1)
    )

    linhas = [
        [
            "<code>casos</code>",
            f"{lags} e <code>casos_mm4</code> (média de 4 semanas)",
            "<b>5</b>",
        ],
        [
            "<code>aedes_aegypti_por_armadilha</code>",
            f"{lags} e <code>vetor_mm4</code> (média de 4 semanas)",
            "<b>5</b>",
        ],
        [
            "<code>temp_media</code>, <code>precip_total_mm</code>, "
            "<code>orvalho_media</code>, <code>umid_media</code>, "
            "<code>pressao_media</code>",
            f"{lags} para cada uma das cinco",
            "<b>20</b>",
        ],
        [
            "semana do ano",
            "<code>sem_sin</code> e <code>sem_cos</code>, a sazonalidade "
            "escrita como seno e cosseno",
            "<b>2</b>",
        ],
        ["", "<b>Total</b>", f"<b>{numeros.ATRIBUTOS.derivados}</b>"],
    ]

    return layout.montar_tabela(cabecalhos, linhas)


def _secao_atributos_do_modelo() -> str:
    """Mostra as defasagens que o pipeline cria em tempo de execução.

    ⚠️ Esta seção existe para corrigir uma omissão. A página listava as
    colunas do arquivo sob o título "Tabela de Atributos Final", e quem lia
    concluía que o modelo prevê casos a três meses usando apenas valores da
    própria semana — o que não faria sentido. As defasagens existem; elas só
    não estão gravadas no arquivo, porque nascem em tempo de execução.
    """
    caminho = layout.montar_fluxo(
        [
            (f"{numeros.TABELA.colunas} colunas", "o que o arquivo guarda"),
            (
                f"+{numeros.ATRIBUTOS.derivados} lag features",
                "criadas ao rodar",
            ),
            (
                f"{numeros.ATRIBUTOS.atributos_no_modelo} atributos",
                "o que o modelo recebe",
            ),
        ]
    )

    titulo_derivados = (
        f"<h3>As {numeros.ATRIBUTOS.derivados} lag features criadas em tempo "
        "de execução</h3>"
    )

    return caminho + titulo_derivados + _tabela_dos_derivados()


def _secao_dicionario() -> str:
    """Introduz e monta a tabela do dicionário de dados."""
    intro = (
        "<p>Cada linha abaixo é uma coluna do arquivo único que alimenta os "
        f"modelos — {numeros.TABELA.colunas} colunas ao todo, uma semana por "
        "linha. São os valores <b>como foram coletados</b>; as defasagens "
        "derivadas deles estão na seção seguinte.</p>"
    )

    return intro + _tabela_do_dicionario()

def _secao_decisao_de_clima() -> str:
    """Como as seis colunas de clima são escolhidas entre as 42 candidatas.

    A escolha não é manual nem teórica: um LightGBM é treinado só para isso, e
    o critério é o ganho que cada coluna trouxe. A seção mostra o ranking para
    que a escolha possa ser conferida, em vez de aceita.
    """
    passos = layout.montar_fluxo(
        [
            (
                f"{numeros.ATRIBUTOS.clima_candidatos} candidatas",
                "todo o clima, bruto e defasado",
            ),
            ("LightGBM interno", "treinado só para ranquear"),
            (
                f"{numeros.ATRIBUTOS.clima_escolhidos} escolhidas",
                "as de maior ganho entram",
            ),
        ]
    )

    como = layout.montar_lista(
        [
            f"Um <b>LightGBM</b> é treinado com o núcleo mais <b>todas</b> as "
            f"{numeros.ATRIBUTOS.clima_candidatos} colunas de clima.",
            "Ele reporta o <b>ganho</b> de cada coluna, que é o quanto ela "
            "reduziu o erro nas divisões da árvore.",
            f"Isso é repetido nos horizontes de "
            f"<b>{numeros.HORIZONTES_DA_SELECAO_DE_CLIMA}</b>, e os ganhos "
            "são somados.",
            f"As <b>{numeros.ATRIBUTOS.clima_escolhidos} maiores</b> entram no "
            "modelo. As outras ficam de fora.",
            f"O treino dessa escolha usa os "
            f"<b>{numeros.ATRIBUTOS.fracao_da_selecao_de_clima} mais "
            f"antigos</b> da série, de "
            f"{numeros.ATRIBUTOS.inicio_da_selecao_de_clima} a "
            f"{numeros.ATRIBUTOS.fim_da_selecao_de_clima}.",
        ]
    )

    cabecalhos = ["#", "Coluna", "Fatia do ganho", "Entra?"]
    linhas = []
    for posicao, candidata in enumerate(numeros.RANKING_DE_CLIMA, start=1):
        if candidata.entra:
            veredito = layout.montar_etiqueta("entra", "clima")
        else:
            veredito = '<span class="apagado">fica de fora</span>'

        linhas.append(
            [
                f'<span class="num">{posicao}</span>',
                f'<code class="nomeColuna">{layout.escapar(candidata.nome)}</code>',
                f"<b>{candidata.ganho:.2f}%".replace(".", ",") + "</b>",
                veredito,
            ]
        )

    titulo = "<h3>O ranking, do topo para baixo</h3>"
    rodape = (
        f"<p>As {numeros.ATRIBUTOS.clima_escolhidos} escolhidas somam "
        f"<b>{numeros.GANHO_DAS_SEIS_ESCOLHIDAS:.1f}%".replace(".", ",")
        + "</b> do ganho de clima. A tabela mostra as 10 primeiras de "
        f"{numeros.ATRIBUTOS.clima_candidatos}.</p>"
    )

    return passos + como + titulo + layout.montar_tabela(cabecalhos, linhas) + rodape


def _secao_features_finais() -> str:
    """A lista fechada do que o modelo do cenário adotado recebe."""
    cabecalhos = ["#", "Coluna", "Grupo", "O que carrega"]

    familia_por_grupo = {"Núcleo": "alvo", "Clima": "clima", "Vetor": "vetor"}

    linhas = []
    for posicao, feature in enumerate(numeros.FEATURES_FINAIS, start=1):
        linhas.append(
            [
                f'<span class="num">{posicao}</span>',
                f'<code class="nomeColuna">{layout.escapar(feature.nome)}</code>',
                layout.montar_etiqueta(feature.grupo, familia_por_grupo[feature.grupo]),
                layout.escapar(feature.descricao),
            ]
        )

    intro = (
        f"<p>São <b>{numeros.ATRIBUTOS.atributos_no_modelo} colunas</b>: "
        f"{numeros.ATRIBUTOS.nucleo} de núcleo, "
        f"{numeros.ATRIBUTOS.clima_escolhidos} de clima e "
        f"{numeros.ATRIBUTOS.vetor} de vetor.</p>"
    )

    return intro + layout.montar_tabela(cabecalhos, linhas)


def _secao_caminho_dos_dados() -> str:
    """O trajeto do dado, da fonte ao painel, em etapas ligadas por setas."""
    return layout.montar_fluxo(CAMINHO_DOS_DADOS)


# Cor da faixa no topo de cada cartão de horizonte, pelo R² daquele prazo. O
# corte é de leitura, não estatístico: serve para o leitor ver de relance até
# onde a previsão ainda se sustenta.
R2_MINIMO_PARA_FAIXA_VERDE = 0.60
R2_MINIMO_PARA_FAIXA_AMBAR = 0.44


def _cor_da_faixa_do_horizonte(r2: float) -> str:
    """Escolhe a cor da faixa do cartão a partir do R² do horizonte.

    Args:
        r2: Fração da variação dos casos que o modelo explica nesse prazo.

    Returns:
        A variável CSS da cor, pronta para entrar no atributo `style`.
    """
    if r2 >= R2_MINIMO_PARA_FAIXA_VERDE:
        return "var(--bom)"

    if r2 >= R2_MINIMO_PARA_FAIXA_AMBAR:
        return "var(--atencao)"

    return "var(--critico)"


def _cartao_de_horizonte(desempenho) -> str:
    """Monta o cartão de um horizonte de previsão.

    O R² ocupa o centro do cartão porque é a medida que responde à pergunta
    "dá para confiar nesse prazo?". Erro médio e captura do pico ficam no
    rodapé, menores, como detalhe de quem quiser ir além.

    Args:
        desempenho: Um item de `numeros.DESEMPENHO_DO_MODELO`.

    Returns:
        O HTML do cartão.
    """
    cor_da_faixa = _cor_da_faixa_do_horizonte(desempenho.r2)

    erro_formatado = numeros.formatar_decimal(desempenho.erro_medio_absoluto, 1)
    captura_formatada = numeros.formatar_percentual(desempenho.captura_do_pico, 0)

    return (
        f'<div class="cardHorizonte" style="--faixa:{cor_da_faixa}">'
        f'<div class="cardPrazo">{layout.escapar(desempenho.rotulo)}</div>'
        f'<div class="cardR2">{numeros.formatar_decimal(desempenho.r2, 3)}</div>'
        '<div class="cardR2Rotulo">da variação dos casos explicada</div>'
        '<div class="cardMedidas">'
        '<div class="cardMedida">'
        f'<div class="cardMedidaValor">{erro_formatado}</div>'
        '<div class="cardMedidaRotulo">erro médio, casos/semana</div>'
        "</div>"
        '<div class="cardMedida">'
        f'<div class="cardMedidaValor">{captura_formatada}</div>'
        '<div class="cardMedidaRotulo">do pico alcançado</div>'
        "</div>"
        "</div></div>"
    )


def _secao_os_horizontes() -> str:
    """Um cartão por prazo de previsão, do mais curto ao mais longo."""
    cartoes = []
    for desempenho in numeros.DESEMPENHO_DO_MODELO:
        cartoes.append(_cartao_de_horizonte(desempenho))

    grade = layout.montar_grade(cartoes, colunas=4)

    leitura = layout.montar_aviso(
        tom="info",
        rotulo="Como ler",
        texto=(
            "O modelo é honesto até <b>um mês</b>. Em três meses ele ainda "
            "explica pouco mais de <b>40%</b> da variação, e alcança menos de "
            "<b>40%</b> da altura do pico — serve para avisar que a epidemia "
            "vem, não para dimensionar o tamanho dela."
        ),
    )

    return grade + leitura


def montar_corpo() -> str:
    """Monta o corpo da página, seção por seção, na ordem da navegação."""
    montadores_por_ancora = {
        "o-caminho-dos-dados": _secao_caminho_dos_dados,
        "os-horizontes": _secao_os_horizontes,
        "walk-forward": _secao_walk_forward,
        "dicionario": _secao_dicionario,
        "atributos-do-modelo": _secao_atributos_do_modelo,
        "decisao-de-clima": _secao_decisao_de_clima,
        "features-finais": _secao_features_finais,
    }

    blocos = []
    for ordem, secao in enumerate(navegacao.PAGINA_INICIO.secoes, start=1):
        montador = montadores_por_ancora[secao.ancora]
        blocos.append(layout.montar_secao(secao, ordem, intro="", corpo=montador()))

    return "".join(blocos)
