"""Ícones da navegação, em SVG embutido.

São desenhados com traço (`stroke`) e herdam a cor do texto do item de menu
(`currentColor`), para acompanharem sozinhos o estado ativo, que inverte a cor.
Não há dependência externa: o SVG entra direto no HTML.
"""

# Traçado comum a todos: contorno fino, pontas arredondadas, sem preenchimento.
_ATRIBUTOS_DE_TRACO = (
    'fill="none" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round"'
)

# Cada entrada guarda só o miolo do SVG; a moldura é montada em `desenhar`.
_MIOLO_POR_NOME = {
    "casa": '<path d="M3 8.2 8.5 3.4a1 1 0 0 1 1.3 0L15 8.2"/>'
            '<path d="M4.6 7.6V15a.8.8 0 0 0 .8.8h7.2a.8.8 0 0 0 .8-.8V7.6"/>',
    "camadas": '<path d="M9 2.4 2.6 5.6 9 8.8l6.4-3.2L9 2.4Z"/>'
               '<path d="M2.6 9.2 9 12.4l6.4-3.2"/>'
               '<path d="M2.6 12.6 9 15.8l6.4-3.2"/>',
    "balao": '<path d="M7.2 2.4v3.9L3.4 13a1.6 1.6 0 0 0 1.4 2.4h8.4A1.6 1.6 0 0 0 14.6 13l-3.8-6.7V2.4"/>'
             '<path d="M6.4 2.4h5.2"/><path d="M5.4 10.6h7.2"/>',
    "grafico": '<path d="M3 15V7.4"/><path d="M7.3 15V3.6"/>'
               '<path d="M11.6 15v-5.4"/><path d="M15.4 15V5.8"/>',
    "relogio": '<circle cx="8" cy="8" r="5.6"/><path d="M8 4.9V8l2.1 1.5"/>',
    "lupa": '<circle cx="7.2" cy="7.2" r="4.4"/><path d="m10.6 10.6 3 3"/>',
}


# O mosquito do selo da marca é desenhado à parte: em 30 pixels o traço fino
# dos outros ícones some, então ele usa corpo e asas preenchidos, com só as
# pernas em traço.
_MOSQUITO = (
    # Probóscide e cabeça, apontando para a esquerda.
    '<path d="M2.6 8.2 L7 10.4" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" fill="none"/>'
    '<circle cx="8.4" cy="11" r="1.9" fill="currentColor"/>'
    # Tórax e abdômen, numa gota alongada na diagonal.
    '<path d="M10 12.2 Q14 13.4 20.4 19.4 Q16.4 16.6 11.4 14.6 Z" '
    'fill="currentColor"/>'
    '<ellipse cx="11.6" cy="13.4" rx="2.5" ry="1.9" fill="currentColor" '
    'transform="rotate(38 11.6 13.4)"/>'
    # As duas asas, abertas para cima e para a direita.
    '<ellipse cx="14.6" cy="8.2" rx="4.6" ry="1.7" fill="currentColor" '
    'opacity=".78" transform="rotate(-22 14.6 8.2)"/>'
    '<ellipse cx="15.4" cy="11.4" rx="4.9" ry="1.6" fill="currentColor" '
    'opacity=".55" transform="rotate(6 15.4 11.4)"/>'
    # Três pares de pernas, em traço.
    '<g stroke="currentColor" stroke-width="1.15" fill="none" '
    'stroke-linecap="round">'
    '<path d="M10.6 14.4 Q8.4 18 4.6 18.6"/>'
    '<path d="M12.8 15.4 Q12 19.4 8.8 21.2"/>'
    '<path d="M15 16.8 Q16.4 20 14.6 22"/>'
    "</g>"
)


def mosquito(classe: str) -> str:
    """Desenha o mosquito do selo da marca.

    Args:
        classe: Classe CSS aplicada ao `<svg>`, que define o tamanho.

    Returns:
        A marcação `<svg>` pronta para ser inserida no HTML.
    """
    return (
        f'<svg class="{classe}" viewBox="0 0 24 24" aria-hidden="true">'
        f"{_MOSQUITO}</svg>"
    )


def desenhar(nome: str, classe: str, lado: int) -> str:
    """Devolve o SVG de um ícone da navegação.

    Args:
        nome: Chave do ícone. Precisa existir em `_MIOLO_POR_NOME`.
        classe: Classe CSS aplicada ao `<svg>`, que define o tamanho final.
        lado: Lado da `viewBox`, em unidades de desenho.

    Returns:
        A marcação `<svg>` pronta para ser inserida no HTML.

    Raises:
        KeyError: Se o nome pedido não corresponder a nenhum ícone conhecido.
    """
    if nome not in _MIOLO_POR_NOME:
        nomes_conhecidos = sorted(_MIOLO_POR_NOME)
        raise KeyError(
            f"Ícone desconhecido: {nome!r}. Disponíveis: {nomes_conhecidos}"
        )

    miolo = _MIOLO_POR_NOME[nome]

    return (
        f'<svg class="{classe}" viewBox="0 0 {lado} {lado}" '
        f'aria-hidden="true" {_ATRIBUTOS_DE_TRACO}>{miolo}</svg>'
    )


def icone_de_menu(nome: str) -> str:
    """Ícone no tamanho do menu primário."""
    return desenhar(nome, classe="navIcone", lado=18)


def icone_de_submenu(nome: str) -> str:
    """Ícone no tamanho do menu secundário."""
    return desenhar(nome, classe="nav2Icone", lado=16)
