"""Página de trabalho: rodada 'notificações como alvo' (25/09/2026).

Só local, não publicada. Registro ENXUTO — os números completos vivem em
`analises/2026-09-25_notificacoes_como_alvo/saidas/`; aqui entra só o que é
preciso para decidir o próximo passo, para não gastar token repetindo tabela
inteira.
"""

import layout


def montar_metricas() -> list[layout.Metrica]:
    """Régua do topo: os dois vereditos da seção 6 do protocolo."""
    return [
        layout.Metrica("TRAVA 1 (T0 = bloco 7)", "válida", "MAE 133,6/199,6/223,2/243,8"),
        layout.Metrica("K1 — notificação ajuda confirmado?", "NÃO", "h=12, p Holm ≥ 1,0"),
        layout.Metrica("Erro relativo 2026 — N1", "9,4×", "contra 397× do C0"),
    ]


def montar_corpo() -> str:
    """Corpo da página: um aviso, uma tabela curta e a figura de 2026."""
    secao = layout.navegacao.PAGINA_NOTIFICACOES_COMO_ALVO.secoes[0]

    aviso_fato = layout.montar_aviso(
        "critico",
        "Fato medido",
        "Em 2026 (até maio, limite da avaliação), os <b>confirmados</b> reais somam "
        "quase zero (máximo 2 por semana). O modelo baseado em confirmados "
        "(<code>C0</code>) não vê essa queda: chega a prever <b>834</b> numa semana "
        "em que o real é <b>0</b>. O modelo baseado em <b>notificações</b> "
        "(<code>N1</code>) também superestima (viés proposital da perda quantílica "
        "0,85), mas por uma margem bem menor — erro relativo médio (h=1,4,8,12) "
        "de <b>9,4×</b> contra <b>397×</b> do <code>C0</code>.",
    )

    aviso_k1 = layout.montar_aviso(
        "info",
        "K1 — notificações como feature extra",
        "Somar notificação (origem + lags) ou taxa de confirmação como coluna extra "
        "de <code>C0</code> <b>não ajuda</b> os confirmados: em h=12, <code>C2a</code> "
        "piora 45,7% (p Holm &lt; 0,0001) e <code>C2b</code> melhora só 0,6%, "
        "sem significância (p Holm = 1,0). Critério da seção 6 não passou.",
    )

    aviso_k2 = layout.montar_aviso(
        "atencao",
        "K2 — modelo contra a régua sazonal",
        "<code>C0</code> bate a régua (mesma semana do ano passado) nos três "
        "horizontes, mas sem significância (p Holm ≥ 0,57). <code>N1</code> "
        "<b>perde</b> para a régua em h=8 e h=12 (p Holm 0,000001 e 0,002) — "
        "o modelo de notificações erra mais que só copiar o ano passado.",
    )

    tabela = layout.montar_tabela(
        ["Braço", "Alvo", "MAE h=12", "Régua h=12", "p Holm (K2)"],
        [
            ["C0", "confirmados CEVS", "252,8", "334,9", "1,000"],
            ["N1", "notificações CEVS", "1212,4", "813,7", "0,002"],
        ],
    )

    figura = layout.montar_figura(
        "imagens/notificacoes_como_alvo_2026.png",
        "Real × previsto × régua em 2026",
        "h=4 e h=12, para C0 (confirmados) e N1 (notificações).",
        "Fonte: analises/2026-09-25_notificacoes_como_alvo/saidas/figura_2026.png",
    )

    corpo_da_secao = (
        "<p>Protocolo completo em "
        "<code>analises/2026-09-25_notificacoes_como_alvo/PRE_DECLARACAO.md</code>. "
        "Exploratória: 2026 é a primeira temporada atípica avaliada.</p>"
        f"{aviso_fato}{aviso_k1}{aviso_k2}{tabela}{figura}"
    )

    return layout.montar_secao(secao, 1, "", corpo_da_secao)
