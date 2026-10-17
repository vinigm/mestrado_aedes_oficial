"""Confere que dados/tabela_final.csv e o snapshot certificado em 26/09/2026.

Todo numero do artigo parte desta tabela; se ela mudar, nenhuma ancora vale.
"""

import hashlib
import pathlib

import pandas as pd

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
CAMINHO_HASH = PASTA_DO_PROJETO / "dados" / "tabela_final.sha256"

PREFIXO_DO_HASH_CERTIFICADO = "6f34b8549009c01b"
LINHAS_ESPERADAS = 725
COLUNAS_ESPERADAS = 36
TAMANHO_DO_BLOCO_EM_BYTES = 1024 * 1024


def calcular_sha256(caminho: pathlib.Path) -> str:
    """Calcula o sha256 de um arquivo lendo em blocos (arquivo lido como bytes)."""
    calculadora = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        bloco = arquivo.read(TAMANHO_DO_BLOCO_EM_BYTES)
        while bloco:
            calculadora.update(bloco)
            bloco = arquivo.read(TAMANHO_DO_BLOCO_EM_BYTES)
    return calculadora.hexdigest()


def ler_hash_registrado(caminho: pathlib.Path) -> tuple[str, str]:
    """Le `tabela_final.sha256` (formato 'sha256  nome') e devolve (hash, nome)."""
    conteudo = caminho.read_text(encoding="utf-8").strip()
    hash_registrado, nome_do_arquivo = conteudo.split(maxsplit=1)
    return hash_registrado, nome_do_arquivo.strip()


def test_hash_registrado_bate_com_o_arquivo() -> None:
    """O sha256 calculado de dados/tabela_final.csv e o gravado em tabela_final.sha256."""
    hash_registrado, nome_do_arquivo = ler_hash_registrado(CAMINHO_HASH)
    hash_calculado = calcular_sha256(CAMINHO_TABELA)

    assert nome_do_arquivo == "tabela_final.csv"
    assert hash_calculado == hash_registrado, (
        f"tabela_final.csv mudou: calculado {hash_calculado}, registrado {hash_registrado}."
    )


def test_hash_e_o_certificado_de_26_09_2026() -> None:
    """O hash comeca por 6f34b8549009c01b, o snapshot certificado em 26/09/2026."""
    hash_calculado = calcular_sha256(CAMINHO_TABELA)
    assert hash_calculado.startswith(PREFIXO_DO_HASH_CERTIFICADO), (
        f"hash {hash_calculado} nao e o certificado ({PREFIXO_DO_HASH_CERTIFICADO}...)."
    )


def test_tabela_tem_725_linhas_e_36_colunas() -> None:
    """A tabela e uma grade semanal de 725 domingos com 36 colunas."""
    tabela = pd.read_csv(CAMINHO_TABELA)
    assert tabela.shape == (LINHAS_ESPERADAS, COLUNAS_ESPERADAS), (
        f"forma {tabela.shape}, esperada {(LINHAS_ESPERADAS, COLUNAS_ESPERADAS)}."
    )
