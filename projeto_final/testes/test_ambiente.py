"""Confere que o ambiente de execucao e o oficial do projeto.

Por que existe: o `.venv` do projeto antigo tem scikit-learn 1.9.0, que muda
resultados do modelo em silencio. Este teste falha, com mensagem clara, se o
Python ou qualquer pacote fixado em `requirements.txt` for de outra versao.
"""

import importlib.metadata
import pathlib
import sys

import pytest

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_REQUIREMENTS = PASTA_DO_PROJETO / "requirements.txt"
VERSAO_PYTHON_OFICIAL = (3, 14, 4)


def ler_versoes_fixadas(caminho: pathlib.Path) -> dict[str, str]:
    """Le o requirements.txt e devolve {pacote: versao} das linhas `pacote==versao`.

    Linhas vazias e comentarios (iniciados por `#`) sao ignorados. Uma linha de
    pacote sem `==` e erro: o projeto exige versoes fixadas, nunca pisos.

    Args:
        caminho: Caminho do requirements.txt.

    Returns:
        Dicionario com o nome do pacote e a versao exata exigida.

    Raises:
        ValueError: Se alguma linha de pacote nao usar `==`.
    """
    versoes_fixadas: dict[str, str] = {}
    linhas = caminho.read_text(encoding="utf-8").splitlines()

    for linha in linhas:
        linha_limpa = linha.strip()
        if linha_limpa == "":
            continue
        if linha_limpa.startswith("#"):
            continue
        if "==" not in linha_limpa:
            raise ValueError(
                f"requirements.txt deve fixar versao com '==': {linha_limpa!r}"
            )
        nome_do_pacote, versao_exigida = linha_limpa.split("==", maxsplit=1)
        versoes_fixadas[nome_do_pacote.strip()] = versao_exigida.strip()

    return versoes_fixadas


VERSOES_FIXADAS = ler_versoes_fixadas(CAMINHO_REQUIREMENTS)


def test_python_e_o_oficial() -> None:
    """O Python em uso tem de ser o 3.14.4 (o `python3` do sistema)."""
    versao_em_uso = sys.version_info[:3]
    assert versao_em_uso == VERSAO_PYTHON_OFICIAL, (
        f"Python {versao_em_uso} em uso, mas o oficial e {VERSAO_PYTHON_OFICIAL}. "
        "Rode com `python3` do sistema, nunca com o `.venv`."
    )


def test_requirements_nao_esta_vazio() -> None:
    """Protege contra um requirements.txt sem pacotes (o teste abaixo passaria vazio)."""
    assert len(VERSOES_FIXADAS) >= 7, (
        f"requirements.txt tem so {len(VERSOES_FIXADAS)} pacotes fixados: "
        f"{sorted(VERSOES_FIXADAS)}"
    )


@pytest.mark.parametrize("nome_do_pacote", sorted(VERSOES_FIXADAS))
def test_versao_instalada_igual_a_fixada(nome_do_pacote: str) -> None:
    """Cada pacote instalado tem de ter exatamente a versao do requirements.txt."""
    versao_exigida = VERSOES_FIXADAS[nome_do_pacote]

    try:
        versao_instalada = importlib.metadata.version(nome_do_pacote)
    except importlib.metadata.PackageNotFoundError:
        pytest.fail(
            f"{nome_do_pacote} nao esta instalado (exigido: =={versao_exigida}). "
            "Confira se esta usando o `python3` do sistema e nao o `.venv`."
        )

    assert versao_instalada == versao_exigida, (
        f"{nome_do_pacote}: instalado {versao_instalada}, exigido =={versao_exigida}. "
        "Versao diferente pode mudar os resultados em silencio. "
        "Rode com `python3` do sistema, nunca com o `.venv`."
    )
