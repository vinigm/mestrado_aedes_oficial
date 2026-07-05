"""

Teste que confere se a montagem da tabela_final continua batendo certinho.

Monta a tabela_final de novo, usando o mesmo caminho que o projeto usa
(primeiro abre os arquivos em "acesso", depois junta tudo em
"dominio.montagem_tabela"), e confere se o resultado fica exatamente igual,
byte por byte, ao arquivo que ja estava salvo (esse arquivo foi gerado pelo
notebook original). Esse teste garante que o script montar.py continua
gerando exatamente a mesma base de dados que os experimentos usam.

Roda rapido, so usa a biblioteca pandas. Pra rodar: python tests/test_montagem.py
(ou pytest).

"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from acesso import fontes
from config import settings
from dominio import montagem_tabela



# Monta a tabela_final chamando as mesmas funcoes que o script montar.py usa.
def montar_tabela_pelo_pacote():
    return montagem_tabela.montar_tabela_final(
        fontes.carregar_raspagem_consolidada(),
        fontes.carregar_marilia_consolidada(),
        fontes.carregar_clima(),
        fontes.carregar_casos_nivel_caso(),
        fontes.carregar_enso(),
    )



def test_montagem_reproduz_tabela_final_byte_a_byte():
    tabela = montar_tabela_pelo_pacote()
    with tempfile.TemporaryDirectory() as pasta_temporaria:
        caminho_gerado = Path(pasta_temporaria) / "tabela_final_gerada.csv"
        tabela.to_csv(caminho_gerado, index=False)
        bytes_gerados = caminho_gerado.read_bytes()
    bytes_salvos = settings.CAMINHO_TABELA_FINAL.read_bytes()
    assert bytes_gerados == bytes_salvos



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
