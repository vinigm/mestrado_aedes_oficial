"""

Compara os resultados ANTES e DEPOIS da regeneracao oficial de 29/08/2026.

A pergunta que este script responde e simples e importante: o que exatamente
mudou quando a tabela_final passou a ter clima desde 2012? Sem isso, a
regeneracao seria um ato de fe - "rodei de novo, confia".

Compara so os CSVs que existem nas duas versoes, celula a celula quando o
formato bate, e relata:
  - arquivos identicos (a recaptura nao mexeu neles);
  - arquivos que mudaram de formato (ganharam ou perderam linhas/colunas);
  - por coluna numerica, o tamanho tipico e maximo da mudanca.

Uso:  python comparar_antes_depois.py

"""

from pathlib import Path

import numpy as np
import pandas as pd

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_ANTES = PASTA_ANALISE / "resultados_ANTES"
PASTA_DEPOIS = PASTA_ANALISE.parents[1] / "modelagem_aedes" / "dados" / "saidas" / "resultados"
PASTA_SAIDAS = PASTA_ANALISE / "saidas"

# Abaixo disso a diferenca e ruido de ponto flutuante, nao mudanca de resultado.
TOLERANCIA_RUIDO = 1e-9


def comparar_um_arquivo(nome_arquivo: str) -> dict:
    """

    Compara uma tabela de resultados nas duas versoes.

    Returns:
        Um dicionario com o veredito daquele arquivo: se o formato mudou, se os
        valores mudaram e qual foi a maior mudanca relativa observada.

    """
    antes = pd.read_csv(PASTA_ANTES / nome_arquivo)
    depois = pd.read_csv(PASTA_DEPOIS / nome_arquivo)

    if antes.shape != depois.shape or list(antes.columns) != list(depois.columns):
        return {
            "arquivo": nome_arquivo,
            "situacao": "FORMATO MUDOU",
            "formato_antes": str(antes.shape),
            "formato_depois": str(depois.shape),
            "colunas_comparadas": 0,
            "celulas_diferentes": np.nan,
            "maior_diferenca_relativa": np.nan,
        }

    colunas_numericas = antes.select_dtypes("number").columns

    total_celulas_diferentes = 0
    maior_diferenca_relativa = 0.0

    for nome_coluna in colunas_numericas:
        valores_antes = pd.to_numeric(antes[nome_coluna], errors="coerce")
        valores_depois = pd.to_numeric(depois[nome_coluna], errors="coerce")

        diferenca_absoluta = (valores_depois - valores_antes).abs()
        mudou = diferenca_absoluta > TOLERANCIA_RUIDO
        total_celulas_diferentes += int(mudou.sum())

        # A diferenca relativa usa o valor antigo como referencia; onde ele e
        # zero nao ha razao definida, entao essas celulas ficam de fora do maximo.
        referencia = valores_antes.abs()
        pode_dividir = referencia > TOLERANCIA_RUIDO
        if pode_dividir.any():
            relativa = (diferenca_absoluta[pode_dividir] / referencia[pode_dividir]).max()
            if pd.notna(relativa):
                maior_diferenca_relativa = max(maior_diferenca_relativa, float(relativa))

    if total_celulas_diferentes == 0:
        situacao = "IDENTICO"
    else:
        situacao = "VALORES MUDARAM"

    return {
        "arquivo": nome_arquivo,
        "situacao": situacao,
        "formato_antes": str(antes.shape),
        "formato_depois": str(depois.shape),
        "colunas_comparadas": len(colunas_numericas),
        "celulas_diferentes": total_celulas_diferentes,
        "maior_diferenca_relativa": maior_diferenca_relativa,
    }


def main() -> None:
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    arquivos_antes = {caminho.name for caminho in PASTA_ANTES.glob("*.csv")}
    arquivos_depois = {caminho.name for caminho in PASTA_DEPOIS.glob("*.csv")}

    em_comum = sorted(arquivos_antes & arquivos_depois)
    so_antes = sorted(arquivos_antes - arquivos_depois)
    so_depois = sorted(arquivos_depois - arquivos_antes)

    print(f"arquivos nas duas versoes: {len(em_comum)}", flush=True)
    if so_antes:
        print(f"so na versao ANTIGA (nao regerados): {so_antes}", flush=True)
    if so_depois:
        print(f"NOVOS nesta regeneracao: {so_depois}", flush=True)

    linhas_comparacao = []
    for nome_arquivo in em_comum:
        linhas_comparacao.append(comparar_um_arquivo(nome_arquivo))

    comparacao = pd.DataFrame(linhas_comparacao)
    comparacao.to_csv(PASTA_SAIDAS / "comparacao_antes_depois.csv", index=False)

    print("\n" + "=" * 100, flush=True)
    print("O QUE MUDOU COM O CLIMA RECAPTURADO", flush=True)
    print("=" * 100, flush=True)
    print(comparacao.to_string(index=False), flush=True)

    print("\n=== resumo ===", flush=True)
    print(comparacao["situacao"].value_counts().to_string(), flush=True)

    mudaram = comparacao.loc[comparacao["situacao"] == "VALORES MUDARAM"]
    if not mudaram.empty:
        print(f"\nmaior mudanca relativa observada: "
              f"{mudaram['maior_diferenca_relativa'].max():.1%}", flush=True)


if __name__ == "__main__":
    main()
