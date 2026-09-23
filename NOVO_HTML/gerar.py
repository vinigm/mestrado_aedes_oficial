"""Gera o site novo em `saida/`.

Uso:
    python3 gerar.py

O site antigo, em `pagina_web/` e `docs/`, não é lido nem escrito por este
script. Os dois convivem até que a migração seja decidida.
"""

import argparse
import datetime
import pathlib
import shutil
import sys

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent

# As páginas são importadas como módulos soltos (`import inicio`), então a pasta
# precisa estar no caminho de busca antes dos imports do projeto.
sys.path.insert(0, str(PASTA_DESTE_ARQUIVO))
sys.path.insert(0, str(PASTA_DESTE_ARQUIVO / "paginas"))

import layout  # noqa: E402  (depende do sys.path ajustado acima)
import navegacao  # noqa: E402

import cenario_adotado as pagina_cenario_adotado  # noqa: E402
import cenarios as pagina_cenarios  # noqa: E402
import dados as pagina_dados  # noqa: E402
import inicio as pagina_inicio  # noqa: E402
import proximos_passos as pagina_proximos_passos  # noqa: E402
import seminario as pagina_seminario  # noqa: E402


PASTA_DE_SAIDA = PASTA_DESTE_ARQUIVO / "saida"
PASTA_DE_IMAGENS_ORIGEM = PASTA_DESTE_ARQUIVO.parent / "pagina_web" / "imagens"
PASTA_DE_IMAGENS_DESTINO = PASTA_DE_SAIDA / "imagens"

# Figuras herdadas do gerador antigo, copiadas de `pagina_web/imagens/`.
#
# ⚠️ As figuras dos slides NÃO entram aqui: `figuras_slides.py` já as escreve
# direto em `saida/imagens/`, e listá-las faria o gerador procurá-las na pasta
# do site antigo, onde elas não existem — nem devem existir.
FIGURAS_USADAS = (
    "series_para_modelar.png",
    "walkforward.png",
    "ciclo_anual.png",
    "cobertura_fontes.png",
    "vetor_vs_casos.png",
    "riqueza_da_armadilha.png",
)

# Cada página do site, com o módulo que sabe montar seu corpo e sua régua.
MODULOS_POR_PAGINA = {
    navegacao.PAGINA_INICIO.chave: pagina_inicio,
    navegacao.PAGINA_DADOS.chave: pagina_dados,
    navegacao.PAGINA_CENARIO_ADOTADO.chave: pagina_cenario_adotado,
    navegacao.PAGINA_PROXIMOS_PASSOS.chave: pagina_proximos_passos,
    navegacao.PAGINA_SEMINARIO.chave: pagina_seminario,
    navegacao.PAGINA_CENARIOS.chave: pagina_cenarios,
}


def copiar_figuras() -> list[str]:
    """Copia para a saída as figuras que as páginas referenciam.

    Returns:
        Os nomes dos arquivos que não foram encontrados na origem.

    Raises:
        FileNotFoundError: Se a pasta de imagens de origem não existir.
    """
    if not PASTA_DE_IMAGENS_ORIGEM.is_dir():
        raise FileNotFoundError(
            f"Pasta de imagens não encontrada: {PASTA_DE_IMAGENS_ORIGEM}"
        )

    PASTA_DE_IMAGENS_DESTINO.mkdir(parents=True, exist_ok=True)

    figuras_ausentes = []
    for nome_do_arquivo in FIGURAS_USADAS:
        caminho_de_origem = PASTA_DE_IMAGENS_ORIGEM / nome_do_arquivo

        if not caminho_de_origem.is_file():
            figuras_ausentes.append(nome_do_arquivo)
            continue

        caminho_de_destino = PASTA_DE_IMAGENS_DESTINO / nome_do_arquivo
        shutil.copyfile(caminho_de_origem, caminho_de_destino)

    return figuras_ausentes


# As figuras que `figuras_slides.py` desenha. O gerador não as cria, mas avisa
# quando faltam, para o deck não sair com imagem quebrada.
FIGURAS_DOS_SLIDES = (
    "slide_vetor_e_casos.png",
    "slide_clima.png",
    "slide_vetor_vs_casos_anotado.png",
)


def _figuras_de_slide_ausentes() -> list[str]:
    """Diz quais figuras de slide ainda não foram desenhadas.

    Returns:
        Os nomes que faltam em `saida/imagens/`. Lista vazia quando está tudo lá.
    """
    ausentes = []
    for nome_do_arquivo in FIGURAS_DOS_SLIDES:
        if not (PASTA_DE_IMAGENS_DESTINO / nome_do_arquivo).is_file():
            ausentes.append(nome_do_arquivo)

    return ausentes


def gerar_pagina(
    pagina: navegacao.PaginaDoSite,
    gerado_em: str,
) -> pathlib.Path:
    """Monta e grava uma página do site.

    Args:
        pagina: A página a gerar, vinda de `navegacao.PAGINAS_DO_SITE`.
        gerado_em: Data de geração, escrita no rodapé.

    Returns:
        O caminho do arquivo gravado.

    Raises:
        KeyError: Se não houver módulo registrado para a chave da página.
    """
    if pagina.chave not in MODULOS_POR_PAGINA:
        chaves_registradas = sorted(MODULOS_POR_PAGINA)
        raise KeyError(
            f"Sem módulo para a página {pagina.chave!r}. "
            f"Registradas: {chaves_registradas}"
        )

    modulo_da_pagina = MODULOS_POR_PAGINA[pagina.chave]

    metricas_do_topo = modulo_da_pagina.montar_metricas()
    corpo_da_pagina = modulo_da_pagina.montar_corpo()

    documento = layout.montar_documento(
        pagina=pagina,
        metricas=metricas_do_topo,
        corpo=corpo_da_pagina,
        gerado_em=gerado_em,
    )

    caminho_de_saida = PASTA_DE_SAIDA / pagina.arquivo
    caminho_de_saida.write_text(documento, encoding="utf-8")

    return caminho_de_saida


def gerar_site(gerado_em: str) -> None:
    """Gera todas as páginas e copia as figuras.

    Args:
        gerado_em: Data de geração no formato DD/MM/AAAA.
    """
    PASTA_DE_SAIDA.mkdir(parents=True, exist_ok=True)

    figuras_ausentes = copiar_figuras()
    if figuras_ausentes:
        print(f"  aviso: figuras não encontradas: {figuras_ausentes}")

    figuras_de_slide_faltando = _figuras_de_slide_ausentes()
    if figuras_de_slide_faltando:
        print(
            "  aviso: figura de slide ausente "
            f"({figuras_de_slide_faltando}) — rode `python3 figuras_slides.py`"
        )

    for pagina in navegacao.PAGINAS_DO_SITE:
        caminho_gravado = gerar_pagina(pagina, gerado_em)
        print(f"  {caminho_gravado.name}")

    print(f"\nSite gerado em {PASTA_DE_SAIDA}")


def _data_de_hoje_formatada() -> str:
    """Data de hoje no formato DD/MM/AAAA."""
    return datetime.date.today().strftime("%d/%m/%Y")


def main() -> None:
    """Ponto de entrada da linha de comando."""
    analisador = argparse.ArgumentParser(
        description="Gera o site novo do projeto em NOVO_HTML/saida/."
    )
    analisador.add_argument(
        "--data",
        default=_data_de_hoje_formatada(),
        help="Data mostrada no rodapé (padrão: hoje, em DD/MM/AAAA).",
    )
    argumentos = analisador.parse_args()

    gerar_site(gerado_em=argumentos.data)


if __name__ == "__main__":
    main()
