"""

Teste que roda os experimentos de verdade, do comeco ao fim, so quando alguem pedir por ele (ele e LENTO).

Chama cada experimento atraves do main.py e compara o que ele gerou com os CSVs de resultados que ja estavam salvos (a referencia). Assim da pra saber se uma mudanca no codigo mudou os numeros.

Isso NAO e um teste rapido: ele treina o modelo de verdade (usa o LightGBM, a biblioteca que faz esse trabalho) e demora minutos. Por isso o nome do arquivo nao comeca com test_ — assim o pytest (a ferramenta que roda os testes automaticos sozinha) nao pega ele. Rode a mao, e so quando mexer no motor do modelo ou nas colunas que entram nele:

    python tests/validar_experimentos.py

Os CSVs de referencia moram na propria pasta de resultados, e rodar o experimento sobrescreve eles. Por isso o script guarda uma copia numa pasta temporaria antes de rodar, e devolve essa copia pro lugar certo no final — a referencia nunca se perde.

Como ler o resultado:
  - Deteccao de surto roda o LightGBM usando um processador so, entao sempre da o mesmo resultado -> esperamos que fique IDENTICO byte a byte.
  - Regressao roda o LightGBM usando varios processadores ao mesmo tempo, o que muda um pouco a ordem das contas e cria pequenas diferencas -> em vez de exigir igualdade exata, mostramos a maior diferenca encontrada (diferenca minuscula e normal, nao e sinal de que o codigo quebrou algo).

"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from config import settings

PASTA_PACOTE = Path(__file__).resolve().parents[1]

# Para cada experimento: quais CSVs ele gera e se a comparacao com a referencia precisa ser exata.
CSVS_POR_EXPERIMENTO = {
    "cidade_deteccao_surto": {
        "arquivos": ["deteccao_surto_resultados.csv", "deteccao_surto_mcnemar.csv"],
        "exata": True,
    },
    "cidade_regressao": {
        "arquivos": ["clima_enxuto_maturidade_resultados.csv"],
        "exata": False,
    },
}



# Manda o main.py rodar um experimento, chamando ele a partir da pasta raiz do projeto.
def rodar_experimento(nome_experimento):
    processo = subprocess.run(
        [sys.executable, "main.py", "--experimento", nome_experimento],
        cwd=PASTA_PACOTE,
        capture_output=True,
        text=True,
    )
    if processo.returncode != 0:
        print(f"  ERRO ao rodar {nome_experimento} (rc={processo.returncode}):")
        print(processo.stdout[-1500:])
        print(processo.stderr[-1500:])
    return processo.returncode



# Diz True quando os dois arquivos sao exatamente iguais, byte a byte.
def comparar_exato(caminho_referencia, caminho_gerado):
    return caminho_referencia.read_bytes() == caminho_gerado.read_bytes()



# Mostra qual foi a maior diferenca de numero entre a referencia e o resultado novo (usado na regressao).
def descrever_diferenca_numerica(caminho_referencia, caminho_gerado):
    referencia = pd.read_csv(caminho_referencia).sort_values(["conjunto", "h"]).reset_index(drop=True)
    gerado = pd.read_csv(caminho_gerado).sort_values(["conjunto", "h"]).reset_index(drop=True)
    mesmas_linhas = referencia[["conjunto", "h", "n"]].equals(gerado[["conjunto", "h", "n"]])
    max_diff_mae = (referencia["MAE"] - gerado["MAE"]).abs().max()
    max_diff_r2 = (referencia["R2"] - gerado["R2"]).abs().max()
    return (
        f"linhas(conjunto,h,n) iguais={mesmas_linhas} | "
        f"max|dMAE|={max_diff_mae:.6g} | max|dR2|={max_diff_r2:.6g}"
    )



# Roda todos os experimentos, compara cada um com a referencia, e devolve a referencia pro lugar no final.
def validar():
    pasta_referencia = Path(tempfile.mkdtemp(prefix="validar_experimentos_"))
    todos_os_arquivos = [
        arquivo
        for config in CSVS_POR_EXPERIMENTO.values()
        for arquivo in config["arquivos"]
    ]
    for arquivo in todos_os_arquivos:
        shutil.copy(settings.PASTA_RESULTADOS / arquivo, pasta_referencia / arquivo)

    try:
        for nome_experimento, config in CSVS_POR_EXPERIMENTO.items():
            print(f"== {nome_experimento} ==", flush=True)
            rodar_experimento(nome_experimento)
            for arquivo in config["arquivos"]:
                caminho_referencia = pasta_referencia / arquivo
                caminho_gerado = settings.PASTA_RESULTADOS / arquivo
                if config["exata"]:
                    iguais = comparar_exato(caminho_referencia, caminho_gerado)
                    print(f"  {arquivo}: {'IDENTICO' if iguais else 'DIFERE'}", flush=True)
                else:
                    print(f"  {arquivo}: {descrever_diferenca_numerica(caminho_referencia, caminho_gerado)}", flush=True)
    finally:
        # Devolve a referencia pro lugar de novo (rodar a regressao mexe nesses arquivos e muda numeros por causa de como o trabalho e dividido entre os processadores).
        for arquivo in todos_os_arquivos:
            shutil.copy(pasta_referencia / arquivo, settings.PASTA_RESULTADOS / arquivo)
        shutil.rmtree(pasta_referencia)
    print("== FIM (referencia restaurada) ==")


if __name__ == "__main__":
    validar()
