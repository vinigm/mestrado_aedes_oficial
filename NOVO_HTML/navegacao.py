"""Mapa do site novo: as páginas e as seções de cada uma.

É a fonte única da navegação. O menu primário (coluna escura da esquerda) lista
as páginas; o menu secundário (coluna ao lado) lista as seções da página aberta
e acompanha a rolagem. Qualquer página nova entra aqui, e os dois menus a
absorvem sozinhos.
"""

import dataclasses


@dataclasses.dataclass(frozen=True)
class SecaoDaPagina:
    """Uma seção de conteúdo, que vira um item do menu secundário.

    Attributes:
        ancora: Identificador usado no `id` do bloco e no link `#ancora`.
        titulo: Texto mostrado no cabeçalho da seção, dentro da página.
        titulo_no_menu: Versão curta para o menu secundário, que tem largura
            fixa e corta o texto com reticências. Quando vem vazio, o menu usa
            o próprio `titulo`.
    """

    ancora: str
    titulo: str
    titulo_no_menu: str = ""

    def rotulo_do_menu(self) -> str:
        """Texto que o menu secundário deve mostrar para esta seção."""
        if self.titulo_no_menu:
            return self.titulo_no_menu

        return self.titulo


@dataclasses.dataclass(frozen=True)
class PaginaDoSite:
    """Uma página do site, com tudo que os dois menus precisam saber.

    Attributes:
        chave: Nome interno, usado para marcar qual item do menu está ativo.
        arquivo: Nome do arquivo HTML gerado.
        titulo_no_menu: Texto curto do item no menu primário.
        icone: Chave do ícone em `icones.py`.
        titulo: Título grande no topo da página.
        resumo: Uma frase logo abaixo do título, dizendo o que a página responde.
        rotulo_do_submenu: Versalete no topo do menu secundário.
        secoes: Seções da página, na ordem em que aparecem.
        abre_grupo: Quando True, um filete com respiro aparece antes deste item
            no menu, separando-o do bloco anterior.
        oculta_cabecalho: Quando True, a página não mostra trilha nem título —
            para páginas que SÃO o próprio conteúdo, como a apresentação.
    """

    chave: str
    arquivo: str
    titulo_no_menu: str
    icone: str
    titulo: str
    resumo: str
    rotulo_do_submenu: str
    secoes: tuple[SecaoDaPagina, ...]
    abre_grupo: bool = False
    oculta_cabecalho: bool = False


PAGINA_INICIO = PaginaDoSite(
    chave="inicio",
    arquivo="index.html",
    titulo_no_menu="Início",
    icone="casa",
    titulo="Modelo preditivo de casos de dengue em Porto Alegre",
    resumo="Pesquisa de mestrado no PPGC/UFRGS.",
    rotulo_do_submenu="A pesquisa",
    secoes=(
        SecaoDaPagina("o-caminho-dos-dados", "O caminho dos dados", "O caminho"),
        SecaoDaPagina(
            "os-horizontes",
            "Até onde a previsão alcança (cenário adotado)",
            "Os horizontes",
        ),
        SecaoDaPagina("walk-forward", "Validação walk-forward", "Como validamos"),
        SecaoDaPagina("dicionario", "Tabela de Atributos Final", "Atributos"),
    ),
)

PAGINA_DADOS = PaginaDoSite(
    chave="dados",
    arquivo="dados.html",
    titulo_no_menu="Dados",
    icone="camadas",
    titulo="Os dados",
    resumo="",
    rotulo_do_submenu="As fontes",
    secoes=(
        SecaoDaPagina("as-series", "As séries lado a lado", "As séries"),
        SecaoDaPagina("as-fontes", "As fontes"),
        SecaoDaPagina("o-clima", "O clima"),
        SecaoDaPagina("a-janela-util", "A janela útil"),
    ),
)

PAGINA_CENARIO_ADOTADO = PaginaDoSite(
    chave="cenario-adotado",
    arquivo="cenario-adotado.html",
    titulo_no_menu="Cenário adotado",
    icone="grafico",
    titulo="O cenário adotado",
    resumo=(
        "A configuração de referência do projeto e os resultados que ela "
        "produz hoje — a leitura que vale, sem o histórico de como chegamos aqui."
    ),
    rotulo_do_submenu="O cenário",
    secoes=(
        SecaoDaPagina("a-configuracao", "A configuração de referência", "A configuração"),
        SecaoDaPagina("o-desempenho", "O desempenho do modelo", "O desempenho"),
        SecaoDaPagina("como-alarme", "O modelo como alarme de surto", "Como alarme"),
        SecaoDaPagina("o-vetor", "O que a armadilha realmente muda", "O vetor"),
        SecaoDaPagina("limitacoes", "O que não se pode afirmar", "Limitações"),
    ),
)

PAGINA_CENARIOS = PaginaDoSite(
    chave="cenarios",
    arquivo="cenarios.html",
    titulo_no_menu="Cenários testados",
    icone="grafico",
    titulo="Cenários testados",
    resumo="",
    rotulo_do_submenu="Os cenários",
    secoes=(
        SecaoDaPagina("sem-el-nino", "Casos de dengue — sem El Niño"),
        SecaoDaPagina("com-el-nino", "Casos de dengue — com El Niño"),
        SecaoDaPagina("com-corte-maturidade", "Casos de dengue — com corte de maturidade"),
        SecaoDaPagina("ganho-do-mosquito", "O ganho do mosquito"),
        SecaoDaPagina("ganho-e-real", "O ganho é real ou é sorte?"),
        SecaoDaPagina("contra-literatura", "Comparação com a literatura"),
        SecaoDaPagina("surto-confirmados", "Vai ter surto? — casos confirmados"),
        SecaoDaPagina("surto-notificados", "Vai ter surto? — casos notificados"),
        SecaoDaPagina("mosquito-por-bairro", "Mosquito por bairro"),
    ),
)


PAGINA_PROXIMOS_PASSOS = PaginaDoSite(
    chave="proximos-passos",
    arquivo="proximos-passos.html",
    titulo_no_menu="Próximos passos",
    icone="calendario",
    titulo="Próximos passos",
    resumo="",
    rotulo_do_submenu="A direção",
    secoes=(
        SecaoDaPagina("o-que-se-ve", "O que os dados mostram a olho nu", "O que se vê"),
        SecaoDaPagina("questao-aberta", "Por que a questão segue aberta", "Questão aberta"),
        SecaoDaPagina("o-que-muda", "O que muda na próxima etapa", "O que muda"),
        SecaoDaPagina("literatura", "A literatura que falta levantar", "Literatura"),
        SecaoDaPagina("a-verificar", "O que precisa ser verificado antes", "A verificar"),
        SecaoDaPagina("o-desafio", "O desafio da temporada 2026-2027", "O desafio"),
    ),
)


PAGINA_SEMINARIO = PaginaDoSite(
    chave="seminario",
    arquivo="seminario.html",
    titulo_no_menu="Seminário de Andamento",
    icone="apresentacao",
    titulo="Seminário de Andamento",
    resumo="",
    rotulo_do_submenu="A apresentação",
    secoes=(),
    abre_grupo=True,
    oculta_cabecalho=True,
)


# Ordem dos itens no menu primário.
PAGINAS_DO_SITE: tuple[PaginaDoSite, ...] = (
    PAGINA_INICIO,
    PAGINA_DADOS,
    PAGINA_CENARIOS,
    PAGINA_CENARIO_ADOTADO,
    PAGINA_PROXIMOS_PASSOS,
    PAGINA_SEMINARIO,
)


IDENTIDADE_DO_SITE = {
    "selo": "AE",
    "nome": "Aedes aegypti · POA",
    "subtitulo": "PPGC · UFRGS",
}


def pagina_por_chave(chave: str) -> PaginaDoSite:
    """Devolve a página cujo identificador interno é `chave`.

    Args:
        chave: O identificador declarado no campo `chave` da página.

    Returns:
        A página correspondente.

    Raises:
        KeyError: Se nenhuma página do site usar essa chave.
    """
    for pagina in PAGINAS_DO_SITE:
        if pagina.chave == chave:
            return pagina

    chaves_conhecidas = [pagina.chave for pagina in PAGINAS_DO_SITE]
    raise KeyError(
        f"Página desconhecida: {chave!r}. Disponíveis: {chaves_conhecidas}"
    )
