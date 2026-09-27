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

# Cores dos números do eixo Y quando o gráfico mede algo que muda de sinal, e o
# sinal é o que interessa — um ganho, por exemplo, em que negativo significa
# que a variável testada atrapalhou. Só entram com `eixo_y_destaca_o_sinal`.
COR_DO_EIXO_ACIMA_DO_ZERO = "#1F7A4D"
COR_DO_EIXO_ABAIXO_DO_ZERO = "#C0392B"
COR_DA_LINHA_DO_ZERO = "#9AA5B4"

# Faixas de fundo que separam o que esta acima do zero do que esta abaixo.
# A opacidade e baixa de proposito: elas sao PANO DE FUNDO, e nao podem
# competir com as curvas nem com a grade.
OPACIDADE_DAS_FAIXAS_DO_SINAL = 0.07


def _cor_do_numero_do_eixo(valor: float) -> str:
    """Diz em que cor um número do eixo Y aparece, pelo sinal dele.

    Args:
        valor: O valor daquela marca do eixo.

    Returns:
        Verde acima de zero, vermelho abaixo, e a cor neutra no próprio zero.
    """
    if valor > 0:
        return COR_DO_EIXO_ACIMA_DO_ZERO

    if valor < 0:
        return COR_DO_EIXO_ABAIXO_DO_ZERO

    return COR_DO_TEXTO_DO_EIXO
COR_DO_TEXTO_PRINCIPAL = "#16202C"  # mesma tinta de --tinta, em tema.py

# Largura máxima do envelope de um gráfico de barras. Maior que a dos
# gráficos de linhas (620px) porque as barras carregam rótulo de método, que
# precisa de mais espaço horizontal para não cortar.
LARGURA_MAXIMA_GRAFICO_DE_BARRAS = 760

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
    series_tracejadas: set[str] | None = None,
    marco_vertical: tuple[float, str] | None = None,
    tamanho_do_desenho: tuple[int, int] = (720, 250),
    eixo_y_destaca_o_sinal: bool = False,
    pintar_faixas_do_sinal: bool = False,
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
        cores: Uma cor por série, na ordem em que `series` é percorrido.
        series_tracejadas: Nomes das séries desenhadas com linha pontilhada e
            sem bolinha nos pontos, para marcar que são **referência** e não
            resultado — o caso da régua sazonal. Quando não vem, todas as
            linhas são contínuas, que é o desenho de sempre.
        marco_vertical: Um par (posição no eixo X, rótulo) que desenha uma
            linha vertical pontilhada atravessando o gráfico, com o rótulo
            acima dela. Serve para marcar onde algo muda — por exemplo, o
            horizonte em que a régua passa a vencer o modelo.
        tamanho_do_desenho: O par (largura, altura) do `viewBox`, em unidades
            de desenho. **Não é o tamanho na tela**: a largura na tela vem do
            CSS, e o SVG é esticado até ela.

            ⚠️ O que este parâmetro controla de verdade é o tamanho RELATIVO
            de tudo que está dentro do gráfico. As fontes e as margens são
            fixas em unidades de desenho, então um `viewBox` mais estreito faz
            números e rótulos aparecerem MAIORES na tela, e um mais alto deixa
            o gráfico mais alto. Dois gráficos lado a lado num slide recebem
            cerca de metade da largura, e no padrão de 720 a fonte de 11
            unidades chega à tela com uns 7 pixels — pequena demais para
            projeção.

            O padrão reproduz exatamente o desenho de antes deste parâmetro
            existir, então nenhuma chamada que não o passe muda de resultado.
        eixo_y_destaca_o_sinal: Quando True, o gráfico mede algo em que o SINAL
            é a informação — um ganho, por exemplo, em que negativo significa
            que a variável testada atrapalhou. Nesse caso o desenho ganha duas
            coisas: uma linha marcando o **zero**, mais forte que a grade, e os
            números do eixo Y coloridos por sinal, verde acima e vermelho
            abaixo.

            A linha do zero só aparece quando o zero cai dentro da faixa do
            gráfico. Num gráfico só de valores positivos, pedir o destaque
            colore os números e não desenha linha nenhuma.
        pintar_faixas_do_sinal: Quando True, o fundo do gráfico ganha duas
            faixas: verde do zero para cima e vermelha do zero para baixo.
            Serve para deixar óbvio, de relance, em que lado cada trecho da
            curva está — e sobretudo ONDE ela cruza.

            ⚠️ É separado de `eixo_y_destaca_o_sinal` de propósito: pintar o
            fundo é uma escolha visual mais forte, e há gráficos que querem o
            zero marcado sem o fundo colorido. Como as faixas ficam atrás de
            tudo, elas não mudam a leitura das curvas.

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

    largura, altura = tamanho_do_desenho
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

    # As faixas vem ANTES da grade e das curvas, para ficarem atras de tudo.
    if pintar_faixas_do_sinal and minimo_y < 0 < maximo_y:
        y_do_zero = posicao_y(0.0)
        largura_da_area = largura - margem_direita - margem_esquerda
        altura_acima = y_do_zero - margem_topo
        altura_abaixo = (altura - margem_base) - y_do_zero
        partes_do_svg.append(
            f'<rect x="{margem_esquerda}" y="{margem_topo}" '
            f'width="{largura_da_area}" height="{altura_acima:.1f}" '
            f'fill="{COR_DO_EIXO_ACIMA_DO_ZERO}" '
            f'fill-opacity="{OPACIDADE_DAS_FAIXAS_DO_SINAL}"/>'
        )
        partes_do_svg.append(
            f'<rect x="{margem_esquerda}" y="{y_do_zero:.1f}" '
            f'width="{largura_da_area}" height="{altura_abaixo:.1f}" '
            f'fill="{COR_DO_EIXO_ABAIXO_DO_ZERO}" '
            f'fill-opacity="{OPACIDADE_DAS_FAIXAS_DO_SINAL}"/>'
        )

    # Grade horizontal + números do eixo Y.
    for passo in range(5):
        valor_do_passo = minimo_y + (maximo_y - minimo_y) * passo / 4
        y = posicao_y(valor_do_passo)
        partes_do_svg.append(
            f'<line x1="{margem_esquerda}" y1="{y:.1f}" x2="{largura - margem_direita}" y2="{y:.1f}" '
            f'stroke="{COR_DA_GRADE}" stroke-width="1"/>'
        )
        cor_do_numero = COR_DO_TEXTO_DO_EIXO
        if eixo_y_destaca_o_sinal:
            cor_do_numero = _cor_do_numero_do_eixo(valor_do_passo)

        partes_do_svg.append(
            f'<text x="{margem_esquerda - 8}" y="{y + 3:.1f}" text-anchor="end" '
            f'fill="{cor_do_numero}" font-size="11">{formatar_numero(valor_do_passo)}</text>'
        )

    # A linha do zero, desenhada por cima da grade e mais forte que ela. As
    # marcas da grade caem em valores quebrados (o eixo é dividido em quatro
    # partes iguais entre o mínimo e o máximo), então o zero quase nunca
    # coincide com uma delas — e sem esta linha não dá para ver, de relance, de
    # que lado cada trecho da curva está.
    if eixo_y_destaca_o_sinal and minimo_y < 0 < maximo_y:
        y_do_zero = posicao_y(0.0)
        partes_do_svg.append(
            f'<line x1="{margem_esquerda}" y1="{y_do_zero:.1f}" '
            f'x2="{largura - margem_direita}" y2="{y_do_zero:.1f}" '
            f'stroke="{COR_DA_LINHA_DO_ZERO}" stroke-width="1.5"/>'
        )
        partes_do_svg.append(
            f'<text x="{margem_esquerda - 8}" y="{y_do_zero + 3:.1f}" text-anchor="end" '
            f'fill="{COR_DO_TEXTO_DO_EIXO}" font-size="11" font-weight="700">0</text>'
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

    # Marco vertical, desenhado antes das linhas para ficar atrás delas.
    if marco_vertical is not None:
        posicao_do_marco, rotulo_do_marco = marco_vertical
        x_do_marco = posicao_x(posicao_do_marco)
        partes_do_svg.append(
            f'<line x1="{x_do_marco:.1f}" y1="{margem_topo}" '
            f'x2="{x_do_marco:.1f}" y2="{altura - margem_base}" '
            f'stroke="{COR_DO_TEXTO_DO_EIXO}" stroke-width="1.4" '
            'stroke-dasharray="4 4"/>'
        )
        partes_do_svg.append(
            f'<text x="{x_do_marco + 4:.1f}" y="{margem_topo + 10}" '
            f'fill="{COR_DO_TEXTO_DO_EIXO}" font-size="10" font-weight="600">'
            f"{layout.escapar(rotulo_do_marco)}</text>"
        )

    # As linhas de cada série, com bolinha no último ponto.
    nomes_tracejados = series_tracejadas or set()
    for indice_da_serie, (nome_da_serie, pontos_da_serie) in enumerate(series_com_dado.items()):
        cor_da_serie = paleta[indice_da_serie % len(paleta)]
        pontos_ordenados = sorted(pontos_da_serie)
        caminho_da_linha = " ".join(
            f"{posicao_x(x):.1f},{posicao_y(y):.1f}" for x, y in pontos_ordenados
        )
        e_tracejada = nome_da_serie in nomes_tracejados
        tracejado = ' stroke-dasharray="6 5"' if e_tracejada else ""
        partes_do_svg.append(
            f'<polyline fill="none" stroke="{cor_da_serie}" stroke-width="2.4" '
            f'stroke-linejoin="round" stroke-linecap="round"{tracejado} '
            f'points="{caminho_da_linha}"/>'
        )
        if e_tracejada:
            continue
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


def montar_grafico_de_barras_horizontais(
    itens: list[tuple[str, str, float]],
    titulo: str,
    cores: list[str] | None = None,
    nota: str = "",
) -> str:
    """Desenha barras horizontais, uma por item, na ordem em que `itens` vem.

    O rótulo do item fica acima da barra, e o valor já formatado ao final
    dela — em vez de um rótulo à esquerda de largura fixa, que cortaria nomes
    de método mais longos que os do gráfico de linhas.

    Args:
        itens: Trincas (rótulo, valor_formatado, valor_numérico). O valor
            numérico só decide o comprimento da barra; o texto mostrado é
            sempre `valor_formatado`, para manter a vírgula decimal do site.
        titulo: Título do gráfico, dizendo o que a barra mede.
        cores: Uma cor por item, para destacar barras específicas (ex.: os
            resultados deste projeto). Quando não vem, todas usam a cor de
            acento do tema.
        nota: Nota de uma linha sob o gráfico, para avisar de um item deixado
            de fora por estourar a escala. Vazia quando não há nota.

    Returns:
        O HTML do gráfico (SVG + nota), ou string vazia se `itens` vier vazio.
    """
    if not itens:
        return ""

    cor_de_acento_do_tema = "#1B6EF3"
    if cores is None:
        cores = [cor_de_acento_do_tema] * len(itens)

    valores_numericos = [valor_numerico for _rotulo, _valor_formatado, valor_numerico in itens]
    maior_valor = max(valores_numericos)

    largura = 720
    altura_por_item = 46
    margem_esquerda = 4
    margem_direita = 68
    margem_topo = 6
    altura_da_barra = 16
    largura_util_da_barra = largura - margem_esquerda - margem_direita
    altura = margem_topo + altura_por_item * len(itens)

    partes_do_svg = [
        f'<svg viewBox="0 0 {largura} {altura}" role="img" '
        f'aria-label="{layout.escapar(titulo)}">'
    ]

    for indice, (rotulo, valor_formatado, valor_numerico) in enumerate(itens):
        topo_do_item = margem_topo + indice * altura_por_item
        y_do_rotulo = topo_do_item + 12
        y_da_barra = topo_do_item + 18
        cor_da_barra = cores[indice % len(cores)]

        comprimento_da_barra = 0.0
        if maior_valor > 0:
            comprimento_da_barra = (valor_numerico / maior_valor) * largura_util_da_barra

        partes_do_svg.append(
            f'<text x="{margem_esquerda}" y="{y_do_rotulo:.1f}" '
            f'fill="{COR_DO_TEXTO_DO_EIXO}" font-size="12">{layout.escapar(rotulo)}</text>'
        )
        partes_do_svg.append(
            f'<rect x="{margem_esquerda}" y="{y_da_barra:.1f}" '
            f'width="{comprimento_da_barra:.1f}" height="{altura_da_barra}" '
            f'rx="3" fill="{cor_da_barra}"/>'
        )
        partes_do_svg.append(
            f'<text x="{margem_esquerda + comprimento_da_barra + 8:.1f}" '
            f'y="{y_da_barra + altura_da_barra - 3:.1f}" '
            f'fill="{COR_DO_TEXTO_PRINCIPAL}" font-size="12" font-weight="650">'
            f"{layout.escapar(valor_formatado)}</text>"
        )

    partes_do_svg.append("</svg>")

    nota_html = ""
    if nota:
        nota_html = (
            f'<p class="figuraLegenda" style="border:none;padding:8px 0 0;margin:0">{nota}</p>'
        )

    titulo_do_grafico = f'<div class="graficoTitulo">{layout.escapar(titulo)}</div>'

    return (
        f'<div class="grafico" style="max-width:{LARGURA_MAXIMA_GRAFICO_DE_BARRAS}px">'
        f"{titulo_do_grafico}{''.join(partes_do_svg)}{nota_html}</div>"
    )


def _formatar_percentual_com_sinal(valor: float) -> str:
    """Percentual inteiro com sinal explícito; o negativo usa o menos tipográfico."""
    valor_absoluto = f"{abs(valor):.0f}"
    if valor > 0:
        return f"+{valor_absoluto}%"
    if valor < 0:
        return f"\u2212{valor_absoluto}%"
    return f"{valor_absoluto}%"


def montar_grafico_de_barras_agrupadas(
    categorias: list[str],
    series: dict[str, list[float]],
    cores: list[str],
    titulo: str,
    nota: str = "",
) -> str:
    """Barras verticais agrupadas por categoria, com linha de base em zero.

    Serve para comparar sistemas quando o valor pode ser positivo ou
    negativo (vantagem ou desvantagem sobre uma régua): a linha de zero marca
    onde a vantagem desaparece.

    Args:
        categorias: Nome de cada grupo, na ordem em que aparecem da esquerda
            para a direita.
        series: Um dicionário {nome_da_série: [um_valor_por_categoria]}. Toda
            série precisa ter um valor para cada categoria, na mesma ordem de
            `categorias`.
        cores: Uma cor por série, na ordem em que `series` é percorrido.
        titulo: Título do gráfico, dizendo o que o valor mede.
        nota: Nota de uma linha sob o gráfico. Vazia quando não há nota.

    Returns:
        O HTML do gráfico (SVG + legenda), ou string vazia se `categorias`
        vier vazio.

    Raises:
        ValueError: Se alguma série não tiver um valor por categoria.
    """
    if not categorias:
        return ""

    quantidade_de_categorias = len(categorias)
    for nome_da_serie, valores_da_serie in series.items():
        if len(valores_da_serie) != quantidade_de_categorias:
            raise ValueError(
                f"Série {nome_da_serie!r} tem {len(valores_da_serie)} valores; "
                f"esperado {quantidade_de_categorias}."
            )

    todos_os_valores = []
    for valores_da_serie in series.values():
        todos_os_valores.extend(valores_da_serie)

    menor_valor = min(0.0, min(todos_os_valores))
    maior_valor = max(0.0, max(todos_os_valores))
    folga = 1.0
    if maior_valor != menor_valor:
        folga = (maior_valor - menor_valor) * 0.12
    menor_valor -= folga
    maior_valor += folga

    largura, altura = 720, 300
    margem_esquerda, margem_direita, margem_topo, margem_base = 46, 16, 16, 40
    area_util_largura = largura - margem_esquerda - margem_direita
    area_util_altura = altura - margem_topo - margem_base

    def posicao_y(valor: float) -> float:
        fracao_do_topo = (maior_valor - valor) / (maior_valor - menor_valor)
        return margem_topo + fracao_do_topo * area_util_altura

    nomes_das_series = list(series.keys())
    quantidade_de_series = len(nomes_das_series)
    largura_do_grupo = area_util_largura / quantidade_de_categorias
    espaco_entre_barras = 4.0
    largura_da_barra = (largura_do_grupo * 0.62 - espaco_entre_barras * (quantidade_de_series - 1)) / quantidade_de_series

    posicao_do_zero = posicao_y(0.0)

    partes_do_svg = [
        f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="{layout.escapar(titulo)}">'
    ]

    partes_do_svg.append(
        f'<line x1="{margem_esquerda}" y1="{posicao_do_zero:.1f}" '
        f'x2="{largura - margem_direita}" y2="{posicao_do_zero:.1f}" '
        f'stroke="{COR_DO_TEXTO_DO_EIXO}" stroke-width="1.4"/>'
    )
    partes_do_svg.append(
        f'<text x="{margem_esquerda - 8}" y="{posicao_do_zero + 3:.1f}" text-anchor="end" '
        f'fill="{COR_DO_TEXTO_DO_EIXO}" font-size="11">0%</text>'
    )

    for indice_da_categoria, nome_da_categoria in enumerate(categorias):
        centro_do_grupo = margem_esquerda + largura_do_grupo * (indice_da_categoria + 0.5)
        largura_total_das_barras = (
            largura_da_barra * quantidade_de_series
            + espaco_entre_barras * (quantidade_de_series - 1)
        )
        inicio_do_grupo = centro_do_grupo - largura_total_das_barras / 2

        for indice_da_serie, nome_da_serie in enumerate(nomes_das_series):
            valor_da_barra = series[nome_da_serie][indice_da_categoria]
            cor_da_barra = cores[indice_da_serie % len(cores)]
            x_da_barra = inicio_do_grupo + indice_da_serie * (largura_da_barra + espaco_entre_barras)
            y_do_valor = posicao_y(valor_da_barra)
            y_do_topo_da_barra = min(y_do_valor, posicao_do_zero)
            altura_da_barra = max(abs(y_do_valor - posicao_do_zero), 1.0)

            partes_do_svg.append(
                f'<rect x="{x_da_barra:.1f}" y="{y_do_topo_da_barra:.1f}" '
                f'width="{largura_da_barra:.1f}" height="{altura_da_barra:.1f}" '
                f'fill="{cor_da_barra}"/>'
            )

            # O valor fica acima da barra positiva e abaixo da negativa, para
            # nunca cair em cima da linha de zero.
            if valor_da_barra >= 0:
                y_do_rotulo = y_do_topo_da_barra - 5
            else:
                y_do_rotulo = y_do_topo_da_barra + altura_da_barra + 13
            centro_da_barra = x_da_barra + largura_da_barra / 2
            partes_do_svg.append(
                f'<text x="{centro_da_barra:.1f}" y="{y_do_rotulo:.1f}" text-anchor="middle" '
                f'fill="{COR_DO_TEXTO_DO_EIXO}" font-size="11" font-weight="600">'
                f"{_formatar_percentual_com_sinal(valor_da_barra)}</text>"
            )

        partes_do_svg.append(
            f'<text x="{centro_do_grupo:.1f}" y="{altura - margem_base + 16}" '
            f'text-anchor="middle" fill="{COR_DO_TEXTO_DO_EIXO}" font-size="10.5">'
            f"{layout.escapar(nome_da_categoria)}</text>"
        )

    partes_do_svg.append("</svg>")

    itens_da_legenda = []
    for indice_da_serie, nome_da_serie in enumerate(nomes_das_series):
        cor_da_serie = cores[indice_da_serie % len(cores)]
        itens_da_legenda.append(
            f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px">'
            f'<i style="width:10px;height:10px;border-radius:50%;background:{cor_da_serie};'
            f'display:inline-block"></i>{layout.escapar(nome_da_serie)}</span>'
        )
    legenda_html = f'<div class="graficoLegenda">{"".join(itens_da_legenda)}</div>'

    nota_html = ""
    if nota:
        nota_html = (
            f'<p class="figuraLegenda" style="border:none;padding:8px 0 0;margin:0">{nota}</p>'
        )

    titulo_do_grafico = f'<div class="graficoTitulo">{layout.escapar(titulo)}</div>'

    return (
        '<div class="grafico">'
        f"{titulo_do_grafico}{''.join(partes_do_svg)}{legenda_html}{nota_html}</div>"
    )
