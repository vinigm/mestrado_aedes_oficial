"""Gráfico de linhas em SVG e tabela de resultados para a página de cenários.

Lê os objetos que `mlflow_leitor.py` devolve (um `Cenario` com seus `Modelo`)
e monta dois blocos de HTML: a tabela comparativa dos modelos do cenário e,
quando a tabela de resultado tiver uma coluna de horizonte, o gráfico de
métrica por horizonte. Tudo em SVG puro, sem dependência externa, nas cores do
tema novo do site.
"""

import dataclasses
import datetime

import layout
import mlflow_leitor

# Cores das linhas do gráfico, na ordem em que as séries aparecem. Paleta do
# tema novo (ver NOVO_HTML/tema.py), repetida em ciclo se houver mais séries
# que cores.
CORES_DAS_SERIES = ["#1B6EF3", "#C0392B", "#1F7A4D", "#B4761C", "#6B7A8C", "#8E44AD"]

# Cor da grade e do texto dos eixos, também do tema novo (--borda e --muted).
COR_DA_GRADE = "#E3E8EE"
COR_DO_TEXTO_DO_EIXO = "#6B7A8C"

# Nomes de coluna aceitos para o eixo X (horizonte de previsão) e para a
# métrica do eixo Y, na ordem de preferência. A busca ignora maiúsculas.
NOMES_ACEITOS_PARA_HORIZONTE = ["h", "horizonte"]
NOMES_ACEITOS_PARA_METRICA = ["mae", "rmse", "r2"]
NOMES_ACEITOS_PARA_CONJUNTO = ["conjunto", "grupo"]

# Nome bonito da métrica usada no eixo Y do gráfico, por nome de coluna do CSV.
ROTULO_DA_COLUNA_DE_METRICA = {
    "mae": "Erro médio (MAE)",
    "rmse": "Erro quadrático (RMSE)",
    "r2": "R² (o quanto explica)",
}

# Nome bonito das métricas de resumo da tabela comparativa (o que o MLflow
# guarda como MAE_media, R2_media...).
ROTULO_DA_METRICA_DE_RESUMO = {
    "MAE_media": "Erro médio (MAE)",
    "R2_media": "R² (o quanto explica)",
    "RMSE_media": "Erro quadrático (RMSE)",
    "acuracia_media": "Acerto (acurácia)",
    "precisao_media": "Precisão",
    "recall_media": "Sensibilidade (recall)",
    "f1_media": "F1",
    "auc_media": "AUC",
    # Saídas do teste de McNemar, usado nos cenários de alarme de surto. Ele
    # conta em quantas semanas um modelo acerta onde o outro erra, e diz se
    # esse desequilíbrio é maior do que o acaso explicaria.
    "clima_certo_vetor_errado": "Só clima acerta, com vetor erra",
    "vetor_certo_clima_errado": "Com vetor acerta, só clima erra",
    "discordantes": "Semanas em desacordo",
    "n": "Semanas avaliadas",
    "n_pos": "Semanas de surto",
    "h": "Horizonte (semanas)",
    "alfa": "Nível de significância",
    "pctl": "Percentil do limiar",
    "p_bruto": "p sem correção",
    "p_holm": "p corrigido (Holm)",
    "significativo_holm": "Sobrevive a Holm",
    "estatistica": "Estatística do teste",
    # Classificação de surto: a matriz de confusão e o que sai dela.
    "tp": "Acertos de surto",
    "tn": "Acertos de calmaria",
    "fp": "Alarmes falsos",
    "fn": "Surtos perdidos",
    "sensib": "Sensibilidade",
    "precisao": "Precisão",
    "espec": "Especificidade",
    "bal_acc": "Acerto balanceado",
    "ap": "Precisão média (AP)",
    "p": "p sem correção",
    # Comparação entre conjuntos de variáveis e contra a literatura.
    "so_clima": "Só clima",
    "clima_vetor": "Clima + mosquito",
    "R2_so_clima": "R² só clima",
    "R2_clima_vetor": "R² clima + mosquito",
    "ganho": "Ganho do mosquito",
    "referencia_oliveira": "Referência da literatura",
    # Teste de Diebold-Mariano: erro absoluto e quadrático.
    "dm_abs": "Estatística (erro absoluto)",
    "dm_sq": "Estatística (erro quadrático)",
    "p_abs": "p (erro absoluto)",
    "p_sq": "p (erro quadrático)",
    "dmae": "Diferença de erro médio",
    # Camada por bairro.
    "base_own": "Base, só o bairro",
    "base_viz": "Base, com vizinhos",
    "enh_own": "Melhorado, só o bairro",
    "enh_viz": "Melhorado, com vizinhos",
    "ganho_enh": "Ganho das colunas novas",
    "lift_viz_enh": "Ganho da vizinhança",
}

# Ordem preferida das métricas de resumo na tabela (o resto vem depois, em
# ordem alfabética).
ORDEM_PREFERIDA_DAS_METRICAS = [
    "MAE_media",
    "RMSE_media",
    "R2_media",
    "acuracia_media",
    "auc_media",
    "f1_media",
    "recall_media",
    "precisao_media",
]

# Métricas de resumo que não são "nota de qualidade" do modelo (contagens e
# parâmetros de corte) — ficam de fora da tabela comparativa.
METRICAS_DE_RESUMO_ESCONDIDAS = {"h_media", "n_media", "passo_media", "step_media"}

# Tradução do jargão dos conjuntos de colunas testados (o valor bruto vem do
# CSV de resultado) para o rótulo mostrado na legenda do gráfico. Um rótulo
# ausente daqui passa para a tela exatamente como veio do CSV.
ROTULOS_DE_CONJUNTO_POR_JARGAO = {
    "M0_clima6": "Só clima (6 colunas)",
    "M0_clima8": "Só clima (8 colunas)",
    "M1_clima6_vetor": "Clima (6) + mosquito",
    "M1_clima8_vetor": "Clima (8) + mosquito",
    "so_clima": "Só clima",
    "so_vetor": "Só mosquito",
    "clima_vetor": "Clima + mosquito",
}

# Data em que o vazamento temporal do treino foi corrigido (ver PENDENCIAS.md,
# registro de 13/09/2026). Execução de cenário anterior a esta data carrega
# número superado pela correção.
DATA_DA_CORRECAO_DO_VAZAMENTO = datetime.date(2026, 9, 13)


def traduzir_rotulo_de_conjunto(rotulo_bruto: str) -> str:
    """Troca o jargão técnico de um conjunto de colunas pelo nome de exibição.

    A paleta padrão distingue séries DENTRO de um gráfico. Quando vários
    gráficos aparecem lado a lado, cada um com uma série só, passe `cores`
    para que cada gráfico tenha a sua — é o que liga o gráfico à coluna
    correspondente da tabela.

    Args:
        rotulo_bruto: O valor como está gravado no CSV de resultado (ex.:
            "M0_clima6").

    Returns:
        O rótulo traduzido, ou o próprio `rotulo_bruto` quando ele não está no
        dicionário `ROTULOS_DE_CONJUNTO_POR_JARGAO`.
    """
    return ROTULOS_DE_CONJUNTO_POR_JARGAO.get(rotulo_bruto, rotulo_bruto)


def _achar_coluna(colunas: list[str], nomes_procurados: list[str]) -> str | None:
    """Acha, numa lista de colunas, a primeira que bate com um nome procurado.

    Args:
        colunas: Nomes das colunas disponíveis, na grafia original do CSV.
        nomes_procurados: Nomes candidatos, em ordem de preferência e em
            minúsculas.

    Returns:
        O nome da coluna na grafia original, ou None se nenhuma bater.
    """
    coluna_por_nome_em_minusculas = {coluna.lower(): coluna for coluna in colunas}
    for nome_procurado in nomes_procurados:
        if nome_procurado in coluna_por_nome_em_minusculas:
            return coluna_por_nome_em_minusculas[nome_procurado]
    return None


def _valor_numerico(texto: str | None) -> float | None:
    """Converte o texto de uma célula em número, ou None se não der.

    Args:
        texto: O texto bruto da célula, como veio do CSV.

    Returns:
        O número convertido, ou None se `texto` for vazio ou não numérico.
    """
    try:
        return float(texto)
    except (ValueError, TypeError):
        return None


def formatar_numero(valor: float | str | None) -> str:
    """Formata um número para leitura (inteiro, ou com 2-3 casas conforme o tamanho).

    Args:
        valor: O valor a formatar. Aceita já vir como texto ou vazio.

    Returns:
        O número formatado, ou um travessão quando `valor` for vazio ou não
        numérico.
    """
    if valor is None or valor == "":
        return "—"
    try:
        numero = float(valor)
    except (ValueError, TypeError):
        return layout.escapar(valor)
    if numero == int(numero) and abs(numero) < 1e6:
        return f"{int(numero)}"
    tamanho_absoluto = abs(numero)
    if tamanho_absoluto >= 100:
        return f"{numero:.1f}"
    if tamanho_absoluto >= 1:
        return f"{numero:.2f}"
    return f"{numero:.3f}"


def formatar_data(momento: datetime.datetime | None) -> str:
    """Formata uma data e hora no jeito brasileiro, ou travessão se ausente."""
    if momento is None:
        return "—"
    return momento.strftime("%d/%m/%Y %H:%M")


def formatar_duracao(segundos: float | None) -> str:
    """Formata uma duração em segundos de forma curta (s, min ou h).

    Args:
        segundos: A duração em segundos, ou None se desconhecida.

    Returns:
        A duração formatada, ou travessão quando `segundos` for None.
    """
    if segundos is None:
        return "—"
    total_de_segundos = int(round(segundos))
    if total_de_segundos < 60:
        return f"{total_de_segundos}s"
    minutos, segundos_restantes = divmod(total_de_segundos, 60)
    if minutos < 60:
        return f"{minutos}min {segundos_restantes}s"
    horas, minutos_restantes = divmod(minutos, 60)
    return f"{horas}h {minutos_restantes}min"


def menor_e_melhor(nome_da_metrica: str) -> bool:
    """Diz se, para essa métrica, um valor MENOR é melhor (erro) ou maior é (acerto).

    Args:
        nome_da_metrica: Nome da métrica de resumo (ex.: "MAE_media").

    Returns:
        True quando a métrica é de erro (contém "mae", "rmse" ou "erro"),
        False caso contrário.
    """
    nome_em_minusculas = nome_da_metrica.lower()
    return "mae" in nome_em_minusculas or "rmse" in nome_em_minusculas or "erro" in nome_em_minusculas


def rotulo_da_metrica_de_resumo(chave: str) -> str:
    """Devolve o nome bonito de uma métrica de resumo, ou a própria chave.

    Args:
        chave: Nome da métrica como o MLflow gravou (ex.: "MAE_media").

    Returns:
        O rótulo de exibição, do dicionário `ROTULO_DA_METRICA_DE_RESUMO`
        quando existir, ou uma versão minimamente arrumada da chave.
    """
    if chave in ROTULO_DA_METRICA_DE_RESUMO:
        return ROTULO_DA_METRICA_DE_RESUMO[chave]

    nome_limpo = _tirar_prefixo_do_experimento(chave)

    if nome_limpo in ROTULO_DA_METRICA_DE_RESUMO:
        return ROTULO_DA_METRICA_DE_RESUMO[nome_limpo]

    return nome_limpo.replace("_media", "").replace("_", " ").capitalize()


# O MLflow grava a métrica como "<arquivo_de_resultado>__<metrica>_media": o
# nome do arquivo entra na frente, separado por DOIS sublinhados, e a agregação
# entra no fim. Nenhum dos dois diz nada a quem lê a página, e juntos fazem o
# cabeçalho estourar a largura da coluna.
SEPARADOR_DE_ARQUIVO_E_METRICA = "__"
SUFIXO_DE_AGREGACAO = "_media"


def _tirar_prefixo_do_experimento(chave: str) -> str:
    """Isola o nome da métrica, sem o arquivo de origem nem o sufixo de agregação.

    Args:
        chave: Nome da métrica como o MLflow gravou, por exemplo
            "surto_notificados_mcnemar__p_holm_media".

    Returns:
        Só o miolo da métrica, no exemplo acima "p_holm". Quando a chave não
        segue esse padrão, ela volta como está.
    """
    nome = chave

    if SEPARADOR_DE_ARQUIVO_E_METRICA in nome:
        _, _, nome = nome.partition(SEPARADOR_DE_ARQUIVO_E_METRICA)

    if nome.endswith(SUFIXO_DE_AGREGACAO):
        nome = nome[: -len(SUFIXO_DE_AGREGACAO)]

    return nome


def montar_grafico_de_linhas(
    series: dict[str, list[tuple[float, float]]],
    rotulo_x: str,
    rotulo_y: str,
    cores: list[str] | None = None,
) -> str:
    """Desenha um gráfico de linhas em SVG a partir de várias séries de pontos.

    Faz na mão: acha o mínimo e o máximo, encaixa os pontos na área de
    desenho, põe uma grade leve, os números dos eixos e uma bolinha destacando
    o último ponto de cada linha. Fundo transparente (sem `<rect>` de fundo),
    nas cores do tema novo do site.

    Args:
        series: Um dicionário {nome_da_linha: [(x, y), ...]}. Séries vazias
            são descartadas antes de desenhar.
        rotulo_x: Nome do eixo X, mostrado abaixo dos números.
        rotulo_y: Nome do eixo Y, mostrado no título do gráfico.

    Returns:
        O HTML do gráfico (SVG + legenda), ou string vazia se não houver
        nenhuma série com dado.
    """
    series_com_dado = {nome: pontos for nome, pontos in series.items() if pontos}
    if not series_com_dado:
        return ""

    todos_os_x = sorted({x for pontos in series_com_dado.values() for x, _ in pontos})
    todos_os_y = [y for pontos in series_com_dado.values() for _, y in pontos]
    minimo_y, maximo_y = min(todos_os_y), max(todos_os_y)
    if minimo_y == maximo_y:
        minimo_y, maximo_y = minimo_y - 1, maximo_y + 1
    folga_do_eixo_y = (maximo_y - minimo_y) * 0.08
    minimo_y, maximo_y = minimo_y - folga_do_eixo_y, maximo_y + folga_do_eixo_y

    largura, altura = 720, 250
    margem_esquerda, margem_direita, margem_topo, margem_base = 56, 16, 18, 44
    area_util_largura = largura - margem_esquerda - margem_direita
    area_util_altura = altura - margem_topo - margem_base

    def posicao_x(x: float) -> float:
        if len(todos_os_x) == 1:
            return margem_esquerda + area_util_largura / 2
        return margem_esquerda + (x - todos_os_x[0]) / (todos_os_x[-1] - todos_os_x[0]) * area_util_largura

    def posicao_y(y: float) -> float:
        return margem_topo + (maximo_y - y) / (maximo_y - minimo_y) * area_util_altura

    paleta = cores if cores else CORES_DAS_SERIES

    partes_do_svg = [
        f'<svg viewBox="0 0 {largura} {altura}" role="img" '
        f'aria-label="{layout.escapar(rotulo_y)} por {layout.escapar(rotulo_x)}">'
    ]

    # Grade horizontal + números do eixo Y.
    for passo in range(5):
        valor_do_passo = minimo_y + (maximo_y - minimo_y) * passo / 4
        y = posicao_y(valor_do_passo)
        partes_do_svg.append(
            f'<line x1="{margem_esquerda}" y1="{y:.1f}" x2="{largura - margem_direita}" y2="{y:.1f}" '
            f'stroke="{COR_DA_GRADE}" stroke-width="1"/>'
        )
        partes_do_svg.append(
            f'<text x="{margem_esquerda - 8}" y="{y + 3:.1f}" text-anchor="end" '
            f'fill="{COR_DO_TEXTO_DO_EIXO}" font-size="11">{formatar_numero(valor_do_passo)}</text>'
        )

    # Números do eixo X (os horizontes).
    for x in todos_os_x:
        partes_do_svg.append(
            f'<text x="{posicao_x(x):.1f}" y="{altura - margem_base + 18}" text-anchor="middle" '
            f'fill="{COR_DO_TEXTO_DO_EIXO}" font-size="11">{formatar_numero(x)}</text>'
        )
    partes_do_svg.append(
        f'<text x="{margem_esquerda + area_util_largura / 2:.1f}" y="{altura - 6}" text-anchor="middle" '
        f'fill="{COR_DO_TEXTO_DO_EIXO}" font-size="11">{layout.escapar(rotulo_x)}</text>'
    )

    # As linhas de cada série, com bolinha no último ponto.
    for indice_da_serie, (nome_da_serie, pontos_da_serie) in enumerate(series_com_dado.items()):
        cor_da_serie = paleta[indice_da_serie % len(paleta)]
        pontos_ordenados = sorted(pontos_da_serie)
        caminho_da_linha = " ".join(
            f"{posicao_x(x):.1f},{posicao_y(y):.1f}" for x, y in pontos_ordenados
        )
        partes_do_svg.append(
            f'<polyline fill="none" stroke="{cor_da_serie}" stroke-width="2.4" '
            f'stroke-linejoin="round" stroke-linecap="round" points="{caminho_da_linha}"/>'
        )
        for x, y in pontos_ordenados:
            partes_do_svg.append(
                f'<circle cx="{posicao_x(x):.1f}" cy="{posicao_y(y):.1f}" r="2.6" fill="{cor_da_serie}"/>'
            )
        ultimo_x, ultimo_y = pontos_ordenados[-1]
        partes_do_svg.append(
            f'<circle cx="{posicao_x(ultimo_x):.1f}" cy="{posicao_y(ultimo_y):.1f}" r="4.4" '
            f'fill="{cor_da_serie}" stroke="#FFFFFF" stroke-width="2"/>'
        )

    partes_do_svg.append("</svg>")

    # Legenda com o nome de cada linha.
    itens_da_legenda = []
    for indice_da_serie, nome_da_serie in enumerate(series_com_dado):
        cor_da_serie = paleta[indice_da_serie % len(paleta)]
        itens_da_legenda.append(
            f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px">'
            f'<i style="width:10px;height:10px;border-radius:50%;background:{cor_da_serie};'
            f'display:inline-block"></i>{layout.escapar(nome_da_serie)}</span>'
        )
    legenda_html = (
        f'<div class="graficoLegenda">{"".join(itens_da_legenda)}</div>'
    )

    titulo_do_grafico = (
        f'<div class="graficoTitulo">{layout.escapar(rotulo_y)} '
        f"por {layout.escapar(rotulo_x)}</div>"
    )

    # A largura fica no CSS (`.grafico`), não aqui: o SVG usa só `viewBox`, e
    # sem um teto ele estica até a largura da página, onde as linhas ficam
    # esparramadas e difíceis de comparar.
    return (
        '<div class="grafico">'
        f"{titulo_do_grafico}{''.join(partes_do_svg)}{legenda_html}</div>"
    )


@dataclasses.dataclass(frozen=True)
class _ReferenciaDeGrafico:
    """Qual coluna do CSV vira o eixo X e qual vira a métrica do eixo Y."""

    coluna_de_horizonte: str
    coluna_de_metrica: str


def _achar_referencia_de_grafico(cenario: mlflow_leitor.Cenario) -> _ReferenciaDeGrafico | None:
    """Procura, entre as tabelas dos modelos do cenário, a primeira com horizonte e métrica.

    Args:
        cenario: O cenário cujas tabelas serão inspecionadas.

    Returns:
        A referência de colunas encontrada, ou None se nenhuma tabela do
        cenário tiver as duas colunas necessárias.
    """
    for modelo in cenario.modelos:
        for tabela in modelo.tabelas.values():
            coluna_de_horizonte = _achar_coluna(tabela.colunas, NOMES_ACEITOS_PARA_HORIZONTE)
            coluna_de_metrica = _achar_coluna(tabela.colunas, NOMES_ACEITOS_PARA_METRICA)
            if coluna_de_horizonte and coluna_de_metrica:
                return _ReferenciaDeGrafico(coluna_de_horizonte, coluna_de_metrica)
    return None


def _media_por_horizonte(
    linhas: list[dict[str, str]],
    coluna_de_horizonte: str,
    coluna_de_metrica: str,
) -> list[tuple[float, float]]:
    """Agrupa as linhas de uma tabela por horizonte e tira a média da métrica.

    Args:
        linhas: As linhas da tabela de resultado.
        coluna_de_horizonte: Nome da coluna com o horizonte (eixo X).
        coluna_de_metrica: Nome da coluna com a métrica (eixo Y).

    Returns:
        Uma lista de pontos (horizonte, média_da_métrica), ordenada pelo
        horizonte.
    """
    valores_por_horizonte: dict[float, list[float]] = {}
    for linha in linhas:
        horizonte = _valor_numerico(linha.get(coluna_de_horizonte))
        valor_da_metrica = _valor_numerico(linha.get(coluna_de_metrica))
        if horizonte is not None and valor_da_metrica is not None:
            valores_por_horizonte.setdefault(horizonte, []).append(valor_da_metrica)

    pontos = [
        (horizonte, sum(valores) / len(valores))
        for horizonte, valores in sorted(valores_por_horizonte.items())
    ]
    return pontos


def montar_grafico_do_cenario(cenario: mlflow_leitor.Cenario) -> str:
    """Monta o gráfico de métrica por horizonte de um cenário, se houver dado.

    Cada modelo guarda uma tabela de resultado (o CSV anexado). Se essa tabela
    tiver a coluna de horizonte e uma coluna de erro/acerto, dá para desenhar
    um gráfico de "métrica por horizonte". A regra: se há vários modelos, cada
    linha do gráfico é um modelo (comparação direta); se há um modelo só mas
    com vários conjuntos de colunas testados, cada linha é um conjunto — e o
    rótulo desse conjunto passa por `traduzir_rotulo_de_conjunto` antes de
    virar legenda. Sem coluna de horizonte em nenhuma tabela, não desenha nada.

    Args:
        cenario: O cenário cujo gráfico se quer montar.

    Returns:
        O HTML do gráfico, ou string vazia se não houver dado para desenhar.
    """
    referencia = _achar_referencia_de_grafico(cenario)
    if referencia is None:
        return ""

    rotulo_do_eixo_y = ROTULO_DA_COLUNA_DE_METRICA.get(
        referencia.coluna_de_metrica.lower(), referencia.coluna_de_metrica
    )

    series: dict[str, list[tuple[float, float]]] = {}

    if len(cenario.modelos) > 1:
        for modelo in cenario.modelos:
            for tabela in modelo.tabelas.values():
                if _achar_coluna(tabela.colunas, NOMES_ACEITOS_PARA_HORIZONTE):
                    pontos = _media_por_horizonte(
                        tabela.linhas, referencia.coluna_de_horizonte, referencia.coluna_de_metrica
                    )
                    series[modelo.nome] = pontos
                    break
    else:
        modelo_unico = cenario.modelos[0]
        tabela_com_horizonte = next(
            (
                tabela
                for tabela in modelo_unico.tabelas.values()
                if _achar_coluna(tabela.colunas, NOMES_ACEITOS_PARA_HORIZONTE)
            ),
            None,
        )
        if tabela_com_horizonte is None:
            return ""

        coluna_de_conjunto = _achar_coluna(tabela_com_horizonte.colunas, NOMES_ACEITOS_PARA_CONJUNTO)
        conjuntos_distintos: set[str] = set()
        if coluna_de_conjunto:
            conjuntos_distintos = {
                linha.get(coluna_de_conjunto)
                for linha in tabela_com_horizonte.linhas
                if linha.get(coluna_de_conjunto)
            }

        if coluna_de_conjunto and len(conjuntos_distintos) > 1:
            for conjunto in sorted(conjuntos_distintos):
                linhas_do_conjunto = [
                    linha
                    for linha in tabela_com_horizonte.linhas
                    if linha.get(coluna_de_conjunto) == conjunto
                ]
                pontos = _media_por_horizonte(
                    linhas_do_conjunto, referencia.coluna_de_horizonte, referencia.coluna_de_metrica
                )
                series[traduzir_rotulo_de_conjunto(conjunto)] = pontos
        else:
            pontos = _media_por_horizonte(
                tabela_com_horizonte.linhas, referencia.coluna_de_horizonte, referencia.coluna_de_metrica
            )
            series[modelo_unico.nome] = pontos

    return montar_grafico_de_linhas(series, "horizonte (semanas)", rotulo_do_eixo_y)


def _metricas_de_resumo_do_cenario(cenario: mlflow_leitor.Cenario) -> list[str]:
    """Descobre, em ordem, quais métricas de resumo entram na tabela comparativa.

    Args:
        cenario: O cenário cujas métricas se quer listar.

    Returns:
        Os nomes das métricas presentes em pelo menos um modelo do cenário,
        exceto as escondidas, na ordem preferida seguida do restante em ordem
        alfabética.
    """
    metricas_presentes: set[str] = set()
    for modelo in cenario.modelos:
        metricas_presentes.update(modelo.metricas)
    metricas_presentes -= METRICAS_DE_RESUMO_ESCONDIDAS

    metricas_ordenadas = [
        metrica for metrica in ORDEM_PREFERIDA_DAS_METRICAS if metrica in metricas_presentes
    ]
    metricas_ordenadas += sorted(metricas_presentes - set(metricas_ordenadas))
    return metricas_ordenadas


def montar_tabela_de_resultados(cenario: mlflow_leitor.Cenario) -> str:
    """Monta a tabela que compara os modelos de um cenário.

    Uma linha por modelo, com as métricas de resumo dele, a duração da
    execução e quando ela aconteceu. Quando o cenário tem mais de um modelo,
    o melhor valor de cada métrica (menor para erro, maior para acerto) entra
    em negrito — com um modelo só, nenhum valor é destacado, porque não há
    com o que comparar.

    Args:
        cenario: O cenário cuja tabela se quer montar.

    Returns:
        O HTML da tabela, pronto para entrar na página.
    """
    metricas = _metricas_de_resumo_do_cenario(cenario)

    melhor_valor_por_metrica: dict[str, float] = {}
    if len(cenario.modelos) > 1:
        for metrica in metricas:
            valores_da_metrica = [
                modelo.metricas[metrica] for modelo in cenario.modelos if metrica in modelo.metricas
            ]
            if valores_da_metrica:
                melhor_valor_por_metrica[metrica] = (
                    min(valores_da_metrica) if menor_e_melhor(metrica) else max(valores_da_metrica)
                )

    cabecalhos = ["Modelo"] + [rotulo_da_metrica_de_resumo(metrica) for metrica in metricas]
    cabecalhos += ["Duração", "Quando"]

    linhas: list[list[str]] = []
    for modelo in cenario.modelos:
        celulas = [layout.escapar(modelo.nome)]
        for metrica in metricas:
            valor_da_metrica = modelo.metricas.get(metrica)
            texto_formatado = formatar_numero(valor_da_metrica)
            e_o_melhor_valor = (
                metrica in melhor_valor_por_metrica
                and valor_da_metrica is not None
                and abs(valor_da_metrica - melhor_valor_por_metrica[metrica]) < 1e-9
            )
            if e_o_melhor_valor:
                celulas.append(f"<b>{texto_formatado}</b>")
            else:
                celulas.append(texto_formatado)
        celulas.append(formatar_duracao(modelo.duracao_segundos))
        celulas.append(formatar_data(modelo.fim))
        linhas.append(celulas)

    return layout.montar_tabela(cabecalhos, linhas)


def _instante_de_execucao(modelo: mlflow_leitor.Modelo) -> datetime.datetime | None:
    """Instante de referência da execução de um modelo, para checar a data da correção.

    Args:
        modelo: O modelo cuja data se quer.

    Returns:
        O fim da execução, ou o início quando não houver fim registrado, ou
        None se nenhum dos dois existir.
    """
    if modelo.fim is not None:
        return modelo.fim
    return modelo.inicio


def _algum_modelo_e_anterior_a_correcao(cenario: mlflow_leitor.Cenario) -> bool:
    """Diz se pelo menos um modelo do cenário foi executado antes da correção do vazamento.

    Args:
        cenario: O cenário a checar.

    Returns:
        True se algum modelo tiver instante de execução anterior a
        `DATA_DA_CORRECAO_DO_VAZAMENTO`, ou se algum modelo não tiver data
        registrada (situação tratada como número não confirmado, por cautela).
    """
    for modelo in cenario.modelos:
        instante = _instante_de_execucao(modelo)
        if instante is None:
            return True
        if instante.date() < DATA_DA_CORRECAO_DO_VAZAMENTO:
            return True
    return False


def montar_aviso_de_numero_superado_se_necessario(cenario: mlflow_leitor.Cenario) -> str:
    """Monta o aviso de número superado quando algum modelo é anterior à correção do vazamento.

    Em 13/09/2026 foi corrigido um vazamento temporal no treino (o corte usava
    a data da pergunta, em vez da data da resposta). Resultado de execução
    anterior a essa data reflete o vazamento e está superado. Ver
    `Meu_Projeto/PENDENCIAS.md`, registro de 13/09/2026.

    Args:
        cenario: O cenário a checar.

    Returns:
        O HTML do aviso, ou string vazia quando todos os modelos do cenário
        foram executados em ou após a correção.
    """
    if not _algum_modelo_e_anterior_a_correcao(cenario):
        return ""

    texto_do_aviso = (
        "Este cenário tem pelo menos um modelo executado antes de 13/09/2026, "
        "data em que um vazamento temporal no treino foi corrigido (o corte "
        "usava a data da pergunta, em vez da data da resposta). Os números "
        "desse modelo refletem o vazamento e estão <b>superados</b>."
    )
    return layout.montar_aviso(
        tom="atencao",
        rotulo="Número anterior à correção do vazamento",
        texto=texto_do_aviso,
    )
