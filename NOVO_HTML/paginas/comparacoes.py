"""Página Comparações: o cenário adotado contra réguas simples e a literatura.

⚠️ Página só de leitura numérica — o pedido foi texto mínimo, mais tabela,
gráfico e cartão. Nenhuma frase aqui deve repetir o que a tabela ou o gráfico
ao lado já mostram.

Todas as quatro seções usam a mesma janela de avaliação: 102 semanas, de 2024
a fev/2026 (`numeros.PERIODO_DE_AVALIACAO_DAS_COMPARACOES`). Fonte de cada
número: `numeros_do_projeto.py`, que aponta a pasta de análise de origem no
comentário de cada dataclass.

⚠️ Página gerada apenas em `NOVO_HTML/saida/` — não publicada em `docs/`.
"""

import layout
import navegacao
import numeros_do_projeto as numeros

import graficos


# Cores usadas nos gráficos desta página. O acento marca o que é deste
# projeto; o cinza-azulado (--muted) marca o que vem de fora.
_COR_DESTE_PROJETO = "#1B6EF3"
_COR_EXTERNA = "#8593A3"
_COR_HORIZONTE_LONGO = "#C0392B"


def _celula_do_projeto(texto: str, este_projeto: bool) -> str:
    """Envolve o texto de uma célula em negrito quando a linha é deste projeto.

    É a mesma marcação usada nas quatro tabelas da seção "Resultados
    publicados" e na tabela da seção "Contra as regras simples", para que o
    leitor ache as linhas do projeto sem precisar ler a coluna de origem.

    Args:
        texto: O conteúdo já pronto para exibição.
        este_projeto: Se a linha pertence ao cenário adotado ou ao HistGB de
            folha mínima 20, os dois modelos deste projeto.

    Returns:
        A célula em HTML, escapada e em negrito quando `este_projeto`.
    """
    texto_escapado = layout.escapar(texto)
    if este_projeto:
        return f"<b>{texto_escapado}</b>"
    return texto_escapado


def _secao_contra_regras_simples() -> str:
    """Tabela, gráfico e três cartões: o cenário adotado contra três réguas."""
    cabecalhos = ["", "1 semana", "1 mês", "2 meses", "3 meses"]

    linhas = []
    for metodo in numeros.REGUA_DE_METODOS_SIMPLES:
        e_deste_projeto = metodo.metodo in ("Cenário adotado", "HistGB, folha mínima 20")
        linhas.append(
            [
                _celula_do_projeto(metodo.metodo, e_deste_projeto),
                _celula_do_projeto(numeros.formatar_decimal(metodo.uma_semana, 1), e_deste_projeto),
                _celula_do_projeto(numeros.formatar_decimal(metodo.um_mes, 1), e_deste_projeto),
                _celula_do_projeto(numeros.formatar_decimal(metodo.dois_meses, 1), e_deste_projeto),
                _celula_do_projeto(numeros.formatar_decimal(metodo.tres_meses, 1), e_deste_projeto),
            ]
        )
    tabela = layout.montar_tabela(cabecalhos, linhas)

    series_do_grafico: dict[str, list[tuple[float, float]]] = {}
    for metodo in numeros.REGUA_DE_METODOS_SIMPLES:
        series_do_grafico[metodo.metodo] = [
            (1.0, metodo.uma_semana),
            (4.0, metodo.um_mes),
            (8.0, metodo.dois_meses),
            (12.0, metodo.tres_meses),
        ]
    grafico = graficos.montar_grafico_de_linhas(
        series_do_grafico, "horizonte (semanas)", "MAE (casos confirmados/semana)"
    )

    cartoes_por_horizonte = []
    for rotulo_do_horizonte, nome_do_campo in _HORIZONTES_DOS_CARTOES:
        vencedor = _menor_erro_no_horizonte(nome_do_campo)
        erro_do_vencedor = numeros.formatar_decimal(getattr(vencedor, nome_do_campo), 1)
        cartoes_por_horizonte.append(
            layout.montar_cartao(
                rotulo=rotulo_do_horizonte,
                titulo="",
                corpo=(
                    f"<p>{layout.escapar(vencedor.metodo)} erra menos: "
                    f"<b>{erro_do_vencedor}</b>.</p>"
                ),
            )
        )
    cartoes = layout.montar_grade(cartoes_por_horizonte, colunas=3)

    return tabela + grafico + cartoes


# Os três horizontes dos cartões da seção 1, com o campo correspondente em
# `numeros.ErroPorHorizonteEMetodo`.
_HORIZONTES_DOS_CARTOES = (
    ("1 semana", "uma_semana"),
    ("1 mês", "um_mes"),
    ("3 meses", "tres_meses"),
)


def _menor_erro_no_horizonte(nome_do_campo: str) -> numeros.ErroPorHorizonteEMetodo:
    """O método de menor MAE num horizonte, entre os da régua de métodos simples."""
    vencedor = numeros.REGUA_DE_METODOS_SIMPLES[0]
    for metodo in numeros.REGUA_DE_METODOS_SIMPLES:
        if getattr(metodo, nome_do_campo) < getattr(vencedor, nome_do_campo):
            vencedor = metodo
    return vencedor


def _metodo_fora_do_grafico() -> numeros.ErroDeMetodoDaLiteratura:
    """O método que fica fora do gráfico de barras, por achatar a escala."""
    for metodo in numeros.METODOS_DA_LITERATURA_NOS_DADOS:
        if not metodo.entra_no_grafico:
            return metodo
    raise ValueError("Nenhum método marcado para ficar fora do gráfico.")


def _secao_literatura_nos_dados() -> str:
    """Tabela, cartão de destaque e gráfico: métodos publicados nos dados do projeto."""
    cabecalhos = ["Método", "De onde vem", "Erro em 3 meses"]

    linhas = []
    for metodo in numeros.METODOS_DA_LITERATURA_NOS_DADOS:
        celula_do_erro = numeros.formatar_decimal(metodo.erro_em_tres_meses, 1)
        linhas.append(
            [
                _celula_do_projeto(metodo.nome, metodo.este_projeto),
                _celula_do_projeto(metodo.origem, metodo.este_projeto),
                _celula_do_projeto(celula_do_erro, metodo.este_projeto),
            ]
        )
    tabela = layout.montar_tabela(cabecalhos, linhas)

    destaque = layout.montar_faixa(
        "Nenhum método supera a mesma semana do ano passado em 3 meses"
    )

    itens_do_grafico = []
    cores_do_grafico = []
    for metodo in numeros.METODOS_DA_LITERATURA_NOS_DADOS:
        if not metodo.entra_no_grafico:
            continue
        itens_do_grafico.append(
            (
                metodo.nome,
                numeros.formatar_decimal(metodo.erro_em_tres_meses, 1),
                metodo.erro_em_tres_meses,
            )
        )
        cores_do_grafico.append(_COR_DESTE_PROJETO if metodo.este_projeto else _COR_EXTERNA)

    fora_do_grafico = _metodo_fora_do_grafico()
    erro_fora_do_grafico = numeros.formatar_decimal(fora_do_grafico.erro_em_tres_meses, 1)
    nota_do_grafico = (
        f"{fora_do_grafico.nome} errou {erro_fora_do_grafico} em 3 meses e fica fora "
        "do gráfico, para não achatar a escala das demais barras."
    )
    grafico = graficos.montar_grafico_de_barras_horizontais(
        itens_do_grafico,
        "MAE em 3 meses (casos confirmados/semana)",
        cores=cores_do_grafico,
        nota=nota_do_grafico,
    )

    return tabela + destaque + grafico


def _sub_tabela_mape() -> str:
    """3a — erro percentual médio (MAPE), 1 semana e 3 meses."""
    cabecalhos = ["Modelo", "Uso", "1 semana", "3 meses"]
    linhas = []
    for item in numeros.MAPE_PUBLICADO:
        linhas.append(
            [
                _celula_do_projeto(item.modelo, item.este_projeto),
                _celula_do_projeto(item.uso, item.este_projeto),
                _celula_do_projeto(item.uma_semana, item.este_projeto),
                _celula_do_projeto(item.tres_meses, item.este_projeto),
            ]
        )
    tabela = layout.montar_tabela(cabecalhos, linhas)
    nota = (
        '<p class="figuraLegenda" style="border:none;padding:4px 0 0;margin:0 0 22px">'
        "Projeto: semanas com 100 casos confirmados ou mais.</p>"
    )
    return f"<h3>Erro percentual (MAPE)</h3>{tabela}{nota}"


def _sub_tabela_erro_relativo() -> str:
    """3b — erro como fração do total de casos, 1 mês e 3 meses."""
    cabecalhos = ["Modelo", "Uso", "1 mês", "3 meses"]
    linhas = []
    for item in numeros.ERRO_RELATIVO_AO_TOTAL_PUBLICADO:
        linhas.append(
            [
                _celula_do_projeto(item.modelo, item.este_projeto),
                _celula_do_projeto(item.uso, item.este_projeto),
                _celula_do_projeto(item.um_mes, item.este_projeto),
                _celula_do_projeto(item.tres_meses, item.este_projeto),
            ]
        )
    tabela = layout.montar_tabela(cabecalhos, linhas)
    return f'<h3 style="margin-top:26px">Erro relativo ao total de casos</h3>{tabela}'


def _sub_tabela_r2() -> str:
    """3c — R², no horizonte que cada artigo declara."""
    cabecalhos = ["Modelo", "Onde", "1 mês", "3 meses"]
    linhas = []
    for item in numeros.R2_PUBLICADO:
        linhas.append(
            [
                _celula_do_projeto(item.modelo, item.este_projeto),
                _celula_do_projeto(item.onde, item.este_projeto),
                _celula_do_projeto(item.um_mes, item.este_projeto),
                _celula_do_projeto(item.tres_meses, item.este_projeto),
            ]
        )
    tabela = layout.montar_tabela(cabecalhos, linhas)
    return f'<h3 style="margin-top:26px">R² (o quanto explica)</h3>{tabela}'


def _formatar_vantagem(valor: float) -> str:
    """Formata uma vantagem percentual com o sinal explícito ("+13%", "−21%").

    O negativo usa o sinal de menos tipográfico (U+2212), não o hífen.
    """
    valor_absoluto = numeros.formatar_decimal(abs(valor), 0)
    if valor > 0:
        return f"+{valor_absoluto}%"
    if valor < 0:
        return f"\u2212{valor_absoluto}%"
    return f"{valor_absoluto}%"


def _sub_tabela_vantagem_sobre_a_regua() -> str:
    """3d — vantagem sobre "a mesma época do ano anterior", com gráfico."""
    cabecalhos = ["Sistema", "Uso", "Curto prazo", "Horizonte longo"]
    linhas = []
    for item in numeros.VANTAGEM_SOBRE_A_REGUA:
        celula_curto_prazo = (
            f"{_formatar_vantagem(item.valor_curto_prazo)} ({item.rotulo_curto_prazo})"
        )
        if item.valor_horizonte_longo is None:
            celula_horizonte_longo = f"vantagem some ({item.rotulo_horizonte_longo})"
        else:
            celula_horizonte_longo = (
                f"{_formatar_vantagem(item.valor_horizonte_longo)} "
                f"({item.rotulo_horizonte_longo})"
            )

        linhas.append(
            [
                _celula_do_projeto(item.sistema, item.este_projeto),
                _celula_do_projeto(item.uso, item.este_projeto),
                _celula_do_projeto(celula_curto_prazo, item.este_projeto),
                _celula_do_projeto(celula_horizonte_longo, item.este_projeto),
            ]
        )
    tabela = layout.montar_tabela(cabecalhos, linhas)

    categorias = []
    curto_prazo = []
    horizonte_longo = []
    for item in numeros.VANTAGEM_SOBRE_A_REGUA:
        if item.valor_horizonte_longo is None:
            continue
        categorias.append(item.sistema)
        curto_prazo.append(item.valor_curto_prazo)
        horizonte_longo.append(item.valor_horizonte_longo)

    nota_do_grafico = (
        "Horizonte longo: 6 meses no D-MOSS, 3 meses neste projeto. "
        "O Superensemble não publica o número de 4 a 6 meses."
    )
    grafico = graficos.montar_grafico_de_barras_agrupadas(
        categorias,
        {"Curto prazo": curto_prazo, "Horizonte longo": horizonte_longo},
        cores=[_COR_DESTE_PROJETO, _COR_HORIZONTE_LONGO],
        titulo="Vantagem sobre a mesma época do ano anterior",
        nota=nota_do_grafico,
    )

    return f'<h3 style="margin-top:26px">Vantagem sobre a régua sazonal</h3>{tabela}{grafico}'


def _secao_resultados_publicados() -> str:
    """As quatro tabelas compactas que comparam o projeto a artigos e sistemas."""
    return (
        _sub_tabela_mape()
        + _sub_tabela_erro_relativo()
        + _sub_tabela_r2()
        + _sub_tabela_vantagem_sobre_a_regua()
    )


def _secao_o_que_sustenta() -> str:
    """Os dois cartões finais: o que os números sustentam, e o que não."""
    cartao_sustentado = layout.montar_cartao(
        rotulo="Sustentado",
        titulo="",
        corpo=layout.montar_lista(
            [
                "Até 1 mês, desempenho na faixa dos sistemas publicados, "
                "inclusive operacionais.",
                "Nos estudos com Porto Alegre, números iguais ou melhores.",
                "Em 3 meses, nenhum método testado nos nossos dados supera a "
                "mesma semana do ano anterior.",
            ]
        ),
    )

    cartao_fora_do_alcance = layout.montar_cartao(
        rotulo="Fora do alcance hoje",
        titulo="",
        corpo=layout.montar_lista(
            [
                "Nível dos sistemas operacionais em 3 meses: eles vencem a "
                "régua; nós, não.",
                "Comparação entre artigos como prova: períodos, escalas e "
                "métricas diferem.",
            ]
        ),
    )

    grade = layout.montar_grade([cartao_sustentado, cartao_fora_do_alcance], colunas=2)

    linha_fina = (
        '<p style="color:var(--muted);font-size:.85rem;margin:2px 0 0">'
        "O que os sistemas que vencem em 3 meses têm: 10 a 20 anos de dados, "
        "dengue o ano todo e, no Vietnã, previsão climática dos próximos "
        "meses.</p>"
    )

    return grade + linha_fina


_MONTADORES_POR_ANCORA = {
    "contra-regras-simples": _secao_contra_regras_simples,
    "literatura-nos-dados": _secao_literatura_nos_dados,
    "resultados-publicados": _secao_resultados_publicados,
    "o-que-sustenta": _secao_o_que_sustenta,
}


def montar_corpo() -> str:
    """Monta o corpo da página, seção por seção, na ordem da navegação."""
    pagina = navegacao.PAGINA_COMPARACOES

    blocos = []
    for ordem, secao in enumerate(pagina.secoes, start=1):
        montador = _MONTADORES_POR_ANCORA[secao.ancora]
        blocos.append(layout.montar_secao(secao, ordem, intro="", corpo=montador()))

    return "".join(blocos)


def _regua_nos_dados() -> numeros.ErroDeMetodoDaLiteratura:
    """A linha da régua sazonal na tabela de métodos aplicados aos dados."""
    for metodo in numeros.METODOS_DA_LITERATURA_NOS_DADOS:
        if metodo.origem == "régua":
            return metodo
    raise ValueError("A régua sazonal não está em METODOS_DA_LITERATURA_NOS_DADOS.")


def _melhor_modelo_nos_dados() -> numeros.ErroDeMetodoDaLiteratura:
    """O modelo de menor erro em 3 meses, excluída a própria régua."""
    regua = _regua_nos_dados()
    melhor = None
    for metodo in numeros.METODOS_DA_LITERATURA_NOS_DADOS:
        if metodo is regua:
            continue
        if melhor is None or metodo.erro_em_tres_meses < melhor.erro_em_tres_meses:
            melhor = metodo
    return melhor


def _contar_configuracoes_da_literatura() -> int:
    """Quantas configurações vindas da literatura rodaram nos nossos dados."""
    quantidade = 0
    for metodo in numeros.METODOS_DA_LITERATURA_NOS_DADOS:
        vem_de_fora = not metodo.este_projeto and metodo.origem != "régua"
        if vem_de_fora:
            quantidade += 1
    return quantidade


def _vantagem_do_histgb_folha_20() -> numeros.VantagemSobreARegua:
    """A linha do HistGB com folha mínima 20 na tabela de vantagem sobre a régua."""
    for item in numeros.VANTAGEM_SOBRE_A_REGUA:
        if item.sistema == "HistGB, folha mínima 20":
            return item
    raise ValueError("HistGB, folha mínima 20 ausente de VANTAGEM_SOBRE_A_REGUA.")


def montar_metricas() -> list[layout.Metrica]:
    """Régua de números do topo: o resumo das quatro comparações da página."""
    regua = _regua_nos_dados()
    melhor_modelo = _melhor_modelo_nos_dados()
    vantagem_em_um_mes = _vantagem_do_histgb_folha_20()
    return [
        layout.Metrica(
            rotulo="3 meses — mesma semana do ano passado",
            valor=numeros.formatar_decimal(regua.erro_em_tres_meses, 1),
            nota="MAE, casos/semana",
        ),
        layout.Metrica(
            rotulo="3 meses — melhor modelo testado",
            valor=numeros.formatar_decimal(melhor_modelo.erro_em_tres_meses, 1),
            nota=melhor_modelo.nome,
        ),
        layout.Metrica(
            rotulo="1 mês — vantagem sobre a régua",
            valor=_formatar_vantagem(vantagem_em_um_mes.valor_curto_prazo),
            nota=vantagem_em_um_mes.sistema,
        ),
        layout.Metrica(
            rotulo="Configurações da literatura testadas",
            valor=str(_contar_configuracoes_da_literatura()),
            nota="nos dados deste projeto",
        ),
    ]
