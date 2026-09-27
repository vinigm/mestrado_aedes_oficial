"""Extrai o Quadro 1 do Plano Municipal de Contingencia como imagem.

Por que existe
--------------
O slide do seminario mostra o Quadro 1 do plano como prova documental: e ele
que define os quatro estagios de resposta e os cortes de incidencia dos quais
saem os limiares de 140, 421 e 702 casos por semana que o projeto usa.

O recorte e feito do PDF original, e nao de um print de tela, por dois motivos:
a resolucao fica alta o bastante para projecao, e a extracao e reproduzivel —
qualquer pessoa roda este script e obtem exatamente a mesma imagem.

⚠️ O PDF vive em `../../../Artigos de referencia/`, que esta FORA do repositorio
e fora do git. Se ele sumir, este script para de funcionar e a imagem ja
gerada em `saidas/` passa a ser a unica copia.

Fonte
-----
Plano Municipal de Contingencia de Arboviroses 2026, Secretaria Municipal de
Saude de Porto Alegre, dezembro de 2025. Quadro 1, pagina 15 do documento
(pagina 21 do PDF).
"""

from __future__ import annotations

import pathlib

import fitz

# Pagina do PDF onde esta o Quadro 1. E a 21 no arquivo, que corresponde a
# pagina 15 impressa — o documento tem 6 paginas de capa e sumario antes.
PAGINA_DO_QUADRO = 20  # indice de base zero

# Recorte em pontos do PDF, do titulo "Quadro 1" ate o fim das notas de rodape
# que definem SE, LSE e LA. A pagina inteira mede 792 x 612 pontos.
RECORTE = (30, 66, 762, 562)

# Escala da renderizacao. Em 3x o texto do quadro fica legivel projetado.
ESCALA = 3

PASTA_DESTE_SCRIPT = pathlib.Path(__file__).resolve().parent
CAMINHO_DO_PDF = (
    PASTA_DESTE_SCRIPT.parent.parent.parent
    / "Artigos de referencia"
    / "2026_Plano_Municipal_de_Contingencia_Arboviroses.docx_0.pdf"
)
NOME_DA_IMAGEM = "quadro_1_plano_municipal.png"


def extrair_quadro(caminho_do_pdf: pathlib.Path, destino: pathlib.Path) -> None:
    """Renderiza o recorte do Quadro 1 e grava como PNG.

    Args:
        caminho_do_pdf: O PDF do plano municipal.
        destino: Onde gravar a imagem.

    Raises:
        FileNotFoundError: Se o PDF nao estiver no lugar esperado.
    """
    if not caminho_do_pdf.exists():
        raise FileNotFoundError(
            f"PDF do plano nao encontrado em {caminho_do_pdf}. "
            "Ele vive fora do repositorio, em 'Artigos de referencia/'."
        )

    documento = fitz.open(caminho_do_pdf)
    pagina = documento[PAGINA_DO_QUADRO]

    # Confere que a pagina e mesmo a do quadro antes de recortar, para o script
    # nao gerar silenciosamente a imagem errada se o PDF for trocado.
    if not pagina.search_for("Quadro 1"):
        raise ValueError(
            f"A pagina {PAGINA_DO_QUADRO + 1} do PDF nao contem 'Quadro 1'. "
            "O documento pode ter mudado de versao."
        )

    imagem = pagina.get_pixmap(
        clip=fitz.Rect(*RECORTE), matrix=fitz.Matrix(ESCALA, ESCALA)
    )
    destino.parent.mkdir(exist_ok=True)
    imagem.save(destino)
    print(f"{destino.name}: {imagem.width} x {imagem.height} px")


def main() -> None:
    """Extrai o quadro para `saidas/`."""
    extrair_quadro(CAMINHO_DO_PDF, PASTA_DESTE_SCRIPT / "saidas" / NOME_DA_IMAGEM)


if __name__ == "__main__":
    main()
