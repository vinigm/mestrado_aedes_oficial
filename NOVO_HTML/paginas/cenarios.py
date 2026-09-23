"""Página dos cenários testados: tabela-resumo e uma seção por cenário.

Para acrescentar um cenário, edite três lugares:
  1. `navegacao.PAGINA_CENARIOS.secoes` — a âncora e o título;
  2. `_ALVO_POR_ANCORA` — o alvo dele na tabela do topo;
  3. `_CORPO_POR_ANCORA`  — o texto da seção dele.
"""

import layout
import navegacao

import graficos
import mlflow_leitor


# Nome do cenário no MLflow, por âncora da seção. É o elo entre a seção da
# página e o experimento que ela mostra.
_NOME_NO_MLFLOW_POR_ANCORA = {
    "sem-el-nino": "cidade_regressao_sem_enso",
    "com-el-nino": "cidade_regressao_com_enso",
    "com-corte-maturidade": "cidade_regressao",
    "ganho-do-mosquito": "cidade_lift_vetor",
    "ganho-e-real": "cidade_diebold",
    "contra-literatura": "comparacao_literatura",
    "surto-confirmados": "cidade_deteccao_surto",
    "surto-notificados": "cidade_surto_notificados",
    "mosquito-por-bairro": "bairro_surto",
}

# Cache do que foi lido do MLflow, para ler a pasta mlruns uma única vez por
# geração do site (todas as seções desta página chamam a função abaixo).
_cenarios_do_mlflow_por_nome: dict[str, mlflow_leitor.Cenario] | None = None


def _obter_cenarios_do_mlflow() -> dict[str, mlflow_leitor.Cenario]:
    """Carrega os cenários do MLflow uma única vez e reaproveita nas chamadas seguintes.

    Returns:
        Um dicionário nome_do_cenario_no_mlflow -> cenário lido.
    """
    global _cenarios_do_mlflow_por_nome
    if _cenarios_do_mlflow_por_nome is None:
        cenarios_lidos = mlflow_leitor.carregar_cenarios()
        _cenarios_do_mlflow_por_nome = {cenario.nome: cenario for cenario in cenarios_lidos}
    return _cenarios_do_mlflow_por_nome


def _resultados_do_cenario(ancora: str) -> str:
    """Monta o aviso (se precisar), a tabela de resultados e o gráfico de um cenário.

    Args:
        ancora: Âncora da seção, usada para achar o nome do cenário no MLflow.

    Returns:
        HTML com aviso + tabela + gráfico, na ordem em que devem aparecer, ou
        string vazia se a âncora não tiver cenário mapeado ou o cenário não
        tiver nenhum modelo concluído registrado no MLflow.
    """
    nome_no_mlflow = _NOME_NO_MLFLOW_POR_ANCORA.get(ancora)
    if nome_no_mlflow is None:
        return ""

    cenario = _obter_cenarios_do_mlflow().get(nome_no_mlflow)
    if cenario is None or not cenario.modelos:
        return ""

    aviso = graficos.montar_aviso_de_numero_superado_se_necessario(cenario)
    tabela = graficos.montar_tabela_de_resultados(cenario)
    grafico = graficos.montar_grafico_do_cenario(cenario)

    return aviso + tabela + grafico


# O alvo de cada cenário: o que ele tenta prever, e sob qual restrição. Absorve
# o que antes era uma coluna separada de "o que muda", porque as duas diziam a
# mesma coisa por ângulos diferentes.
_ALVO_POR_ANCORA = {
    "sem-el-nino": "Casos confirmados de dengue, <b>sem</b> índices oceânicos",
    "com-el-nino": "Casos confirmados de dengue, <b>com</b> índices oceânicos",
    "com-corte-maturidade": (
        "Casos confirmados, apagando do treino as <b>12 semanas</b> mais recentes"
    ),
    "ganho-do-mosquito": (
        "Casos confirmados, com conjuntos <b>fixos</b> de variáveis: "
        "só clima · clima + mosquito · só mosquito"
    ),
    "ganho-e-real": (
        "A diferença de erro entre dois modelos, submetida a <b>teste estatístico</b>"
    ),
    "contra-literatura": (
        "Casos confirmados e a subida (sim/não) que um <b>artigo publicado</b> prevê"
    ),
    "surto-confirmados": (
        "Surto de casos <b>confirmados</b>: a semana passou do limiar ou não"
    ),
    "surto-notificados": (
        "Surto de casos <b>notificados</b>: a semana passou do limiar ou não"
    ),
    "mosquito-por-bairro": (
        "Densidade de mosquito de cada <b>bairro</b>, a partir dele e dos vizinhos"
    ),
}


# O mesmo alvo, em versão curta. A página tem largura para a frase inteira; um
# slide projetado não tem, e nove linhas longas estouram o palco.
_ALVO_CURTO_POR_ANCORA = {
    "sem-el-nino": "Casos, <b>sem</b> El Niño",
    "com-el-nino": "Casos, <b>com</b> El Niño",
    "com-corte-maturidade": "Casos, com corte de <b>12 semanas</b>",
    "ganho-do-mosquito": "Casos, com conjuntos <b>fixos</b> de variáveis",
    "ganho-e-real": "A diferença de erro, sob <b>teste estatístico</b>",
    "contra-literatura": "Casos e a subida que um <b>artigo</b> prevê",
    "surto-confirmados": "<b>Surto</b> de casos confirmados",
    "surto-notificados": "<b>Surto</b> de casos notificados",
    "mosquito-por-bairro": "Densidade de mosquito por <b>bairro</b>",
}


# O corpo de cada cenário. Vazio por enquanto: o texto de cada um será escrito
# à mão aqui, uma âncora por vez. Âncora ausente significa seção sem corpo.
_CORPO_POR_ANCORA: dict[str, str] = {}


# Nome de exibição de cada algoritmo. A chave é como ele aparece registrado no
# parâmetro `modelo` de cada execução.
_NOME_DO_ALGORITMO = {
    "lightgbm": "LightGBM",
    "hist_gradient_boosting": "HistGradientBoosting",
    "gradient_boosting": "GradientBoosting",
    "random_forest": "Random Forest",
    "extra_trees": "Extra Trees",
    "elastic_net": "Elastic Net",
    "ridge": "Ridge",
    "knn": "KNN",
    "svr": "SVR",
}


# Modelos efetivamente executados em cada cenário, com o número de execuções —
# contados no registro do MLflow em 23/09/2026, não declarados à mão.
#
# ⚠️ Só o cenário "com corte de maturidade" foi rodado com a grade completa de
# algoritmos. Os outros oito usam LightGBM apenas, por decisão de desenho: eles
# testam HIPÓTESES (o índice oceânico ajuda? o mosquito ajuda?), e variar o
# algoritmo junto impediria isolar o efeito.
_MODELOS_POR_ANCORA = {
    "sem-el-nino": (("lightgbm", 4),),
    "com-el-nino": (("lightgbm", 4),),
    "com-corte-maturidade": (
        ("lightgbm", 5),
        ("hist_gradient_boosting", 4),
        ("gradient_boosting", 4),
        ("random_forest", 4),
        ("extra_trees", 4),
        ("elastic_net", 4),
        ("ridge", 4),
        ("knn", 4),
        ("svr", 4),
    ),
    "ganho-do-mosquito": (("lightgbm", 4),),
    "ganho-e-real": (("lightgbm", 5),),
    "contra-literatura": (("lightgbm", 5),),
    "surto-confirmados": (("lightgbm", 5),),
    "surto-notificados": (("lightgbm", 2),),
    "mosquito-por-bairro": (("lightgbm", 3),),
}


def _cards_de_modelos(ancora: str) -> str:
    """Um card por algoritmo executado no cenário.

    Args:
        ancora: A âncora da seção, usada para achar os modelos do cenário.

    Returns:
        A grade de cards, ou string vazia se o cenário não tiver registro.
    """
    modelos = _MODELOS_POR_ANCORA.get(ancora, ())
    if not modelos:
        return ""

    cartoes = []
    for chave_do_algoritmo, execucoes in modelos:
        nome = _NOME_DO_ALGORITMO.get(chave_do_algoritmo, chave_do_algoritmo)
        plural = "execuções" if execucoes > 1 else "execução"
        cartoes.append(
            layout.montar_cartao(
                rotulo="",
                titulo=nome,
                corpo=f'<p class="fluxoTexto">{execucoes} {plural}</p>',
            )
        )

    colunas = 3 if len(cartoes) > 1 else 2

    return layout.montar_grade(cartoes, colunas=colunas)


def _modelos_em_linha(ancora: str) -> str:
    """Lista os algoritmos de um cenário numa célula de tabela.

    Args:
        ancora: A âncora da seção, usada para achar os modelos do cenário.

    Returns:
        Os nomes numa grade de duas colunas, ou um travessão se não houver
        registro para essa âncora. A grade existe porque um dos cenários tem
        nove algoritmos: em linha única eles atravessam a tabela inteira.
    """
    modelos = _MODELOS_POR_ANCORA.get(ancora, ())
    if not modelos:
        return "—"

    itens = []
    for chave_do_algoritmo, _execucoes in modelos:
        nome = _NOME_DO_ALGORITMO.get(chave_do_algoritmo, chave_do_algoritmo)
        itens.append(f"<span>{layout.escapar(nome)}</span>")

    return f'<span class="celulaModelos">{"".join(itens)}</span>'


def resumo_dos_cenarios() -> list[tuple[int, str, str, str]]:
    """Os cenários como dados, para quem quiser montar outra visão deles.

    A página monta a tabela completa; a apresentação monta uma versão enxuta.
    Os dois leem daqui, então não podem divergir.

    Returns:
        Uma tupla por cenário: (ordem, título, alvo curto, resumo dos modelos).
        O resumo dos modelos traz o nome do algoritmo quando há só um, e a
        contagem quando há vários.
    """
    linhas = []
    for ordem, secao in enumerate(navegacao.PAGINA_CENARIOS.secoes, start=1):
        modelos = _MODELOS_POR_ANCORA.get(secao.ancora, ())

        if len(modelos) == 1:
            chave_do_algoritmo = modelos[0][0]
            resumo_dos_modelos = _NOME_DO_ALGORITMO.get(
                chave_do_algoritmo, chave_do_algoritmo
            )
        elif modelos:
            resumo_dos_modelos = f"{len(modelos)} algoritmos"
        else:
            resumo_dos_modelos = "—"

        linhas.append(
            (
                ordem,
                secao.titulo,
                _ALVO_CURTO_POR_ANCORA[secao.ancora],
                resumo_dos_modelos,
            )
        )

    return linhas


def _tabela_resumo() -> str:
    """Tabela do topo: um cenário por linha, com link para a seção dele."""
    cabecalhos = ["#", "Cenário", "Alvo", "Modelos testados"]

    linhas = []
    for ordem, secao in enumerate(navegacao.PAGINA_CENARIOS.secoes, start=1):
        alvo = _ALVO_POR_ANCORA[secao.ancora]
        linhas.append(
            [
                f'<span class="num">{ordem}</span>',
                f'<a href="#{layout.escapar(secao.ancora)}">'
                f"<b>{layout.escapar(secao.titulo)}</b></a>",
                alvo,
                _modelos_em_linha(secao.ancora),
            ]
        )

    return layout.montar_tabela(cabecalhos, linhas)


def montar_metricas() -> list[layout.Metrica]:
    """Sem régua de números nesta página."""
    return []


def montar_corpo() -> str:
    """Tabela-resumo no topo, seguida de uma seção por cenário."""
    blocos = [_tabela_resumo()]

    for ordem, secao in enumerate(navegacao.PAGINA_CENARIOS.secoes, start=1):
        corpo = _CORPO_POR_ANCORA.get(secao.ancora, "")
        corpo += _cards_de_modelos(secao.ancora)
        corpo += _resultados_do_cenario(secao.ancora)
        blocos.append(layout.montar_secao(secao, ordem, intro="", corpo=corpo))

    return "".join(blocos)
