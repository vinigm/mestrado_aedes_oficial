"""

Teste que confere que consolidar_sinan usa UM SO arquivo do SINAN por ano.

Reproduz o cenario real de 13/09/2026: a pasta bases_governo tinha, ao mesmo
tempo, o DENGBR26.csv.zip antigo e uma reexportacao mais nova do mesmo ano
(sufixo "_atualizado"). O glob("DENGBR*.csv.zip") batia com os dois, e a
versao anterior de consolidar_sinan() (antes de 25/09/2026) concatenava os
dois sem selecao nenhuma, contando os casos daquele ano em dobro.

Este teste cria uma pasta temporaria com 3 arquivos DENGBR sinteticos (ano 25
com 1 arquivo, ano 26 com 2 - o antigo e o "_atualizado") e confere que
consolidar_sinan() traz so os casos do arquivo mais novo do ano 26, nunca os
dois. Rodado contra a versao anterior de consolidar_sinan.py (glob + concat
sem selecionar_um_arquivo_por_ano), este teste FALHA: o ano 26 apareceria com
5 casos (2 do arquivo antigo + 3 do atualizado) em vez dos 3 esperados.

Pra rodar: python tests/test_consolidar_sinan.py (ou pytest).

"""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings
from preparo import consolidar_sinan


# Colunas minimas que filtrar_poa_confirmados precisa pra identificar um caso
# confirmado de Porto Alegre (ver preparo/consolidar_sinan.py).
COLUNAS_SINAN_TESTE = ["SEM_PRI", "NU_ANO", "ID_MUNICIP", "CLASSI_FIN"]

# Codigo de Porto Alegre e um CLASSI_FIN confirmado, iguais aos usados pelo
# modulo real (ver CODIGO_MUNICIPIO_POA e CLASSIFICACOES_CONFIRMADAS).
CODIGO_MUNICIPIO_POA_TESTE = 431490
CLASSI_FIN_CONFIRMADO_TESTE = 10


def escrever_dengbr_sintetico(caminho_zip: Path, semanas_dos_casos: list[int], ano: int) -> None:
    """Cria um DENGBR*.csv.zip minimo, com um caso confirmado de POA por semana.

    Args:
        caminho_zip: Onde salvar o .csv.zip sintetico.
        semanas_dos_casos: Uma linha (um caso confirmado) por semana da lista.
        ano: Valor da coluna NU_ANO em todas as linhas.
    """
    linhas_do_csv = [",".join(COLUNAS_SINAN_TESTE)]
    for semana_do_caso in semanas_dos_casos:
        linha_do_caso = (
            f"{semana_do_caso},{ano},"
            f"{CODIGO_MUNICIPIO_POA_TESTE},{CLASSI_FIN_CONFIRMADO_TESTE}"
        )
        linhas_do_csv.append(linha_do_caso)
    conteudo_csv = "\n".join(linhas_do_csv)

    nome_csv_dentro_do_zip = caminho_zip.with_suffix("").name  # tira o ".zip"
    with zipfile.ZipFile(caminho_zip, "w") as arquivo_zip:
        arquivo_zip.writestr(nome_csv_dentro_do_zip, conteudo_csv)


def test_consolidar_sinan_usa_um_arquivo_por_ano_quando_ha_duplicata():
    """Ano com 2 arquivos deve contar so os casos do mais novo ("_atualizado")."""
    pasta_sinan_original = settings.PASTA_SINAN_NACIONAL
    try:
        with tempfile.TemporaryDirectory() as nome_pasta_temporaria:
            pasta_sinan_de_teste = Path(nome_pasta_temporaria)
            settings.PASTA_SINAN_NACIONAL = pasta_sinan_de_teste

            escrever_dengbr_sintetico(
                pasta_sinan_de_teste / "DENGBR25.csv.zip",
                semanas_dos_casos=[202501, 202502],
                ano=2025,
            )
            escrever_dengbr_sintetico(
                pasta_sinan_de_teste / "DENGBR26.csv.zip",
                semanas_dos_casos=[202601, 202602],
                ano=2026,
            )
            escrever_dengbr_sintetico(
                pasta_sinan_de_teste / "DENGBR26_atualizado_teste.csv.zip",
                semanas_dos_casos=[202601, 202602, 202603],
                ano=2026,
            )

            casos = consolidar_sinan.consolidar_sinan()
    finally:
        settings.PASTA_SINAN_NACIONAL = pasta_sinan_original

    casos_do_ano_2025 = casos[casos["NU_ANO"] == 2025]
    casos_do_ano_2026 = casos[casos["NU_ANO"] == 2026]

    assert len(casos_do_ano_2025) == 2
    assert len(casos_do_ano_2026) == 3
    assert set(casos_do_ano_2026["arquivo_origem"]) == {"DENGBR26_atualizado_teste.csv.zip"}
    assert len(casos) == 5  # 2 (ano 25) + 3 (ano 26, so o arquivo atualizado) - nunca 7.


def test_selecionar_um_arquivo_por_ano_preserva_anos_sem_duplicata():
    """Anos com um unico arquivo devem passar direto, sem escolha nenhuma."""
    caminhos_zip = [
        "/pasta/DENGBR23.csv.zip",
        "/pasta/DENGBR24.csv.zip",
        "/pasta/DENGBR25.csv.zip",
    ]
    caminhos_selecionados = consolidar_sinan.selecionar_um_arquivo_por_ano(caminhos_zip)
    assert caminhos_selecionados == caminhos_zip


if __name__ == "__main__":
    testes = [
        valor
        for nome, valor in sorted(globals().items())
        if nome.startswith("test_") and callable(valor)
    ]
    for teste in testes:
        teste()
        print("OK:", teste.__name__)
    print(f"\n{len(testes)} teste(s) passaram")
