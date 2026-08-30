"""

Certificacao adversarial da Rodada 0: a recaptura do clima nao pode ter mexido
em nada alem do clima.

O script tenta REPROVAR a regeneracao da tabela_final, conferindo os cinco
criterios de aceitacao escritos na PRE_DECLARACAO.md desta pasta (criterio 4 na
redacao da EMENDA 1). Compara a tabela regerada contra a copia congelada antes
da recaptura.

Uso:  python rodada_0_certificar_tabela_final.py

"""

import sys
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import numpy as np
import pandas as pd

from config import settings

CAMINHO_TABELA_ANTES = PASTA_ANALISE / "saidas" / "tabela_final_ANTES_recaptura_clima.csv"
COLUNA_DATA = "data_inicio_semana_epidemi"

# Ancoras medidas em 29/08/2026, antes de qualquer alteracao (PRE_DECLARACAO.md).
FORMATO_ESPERADO = (725, 36)
VETOR_NAO_NULOS_ESPERADO = 718
VETOR_SOMA_ESPERADA = 280.8343
CASOS_NAO_NULOS_ESPERADO = 428
CASOS_SOMA_ESPERADA = 56624.0
TEMP_MEDIA_NAO_NULOS_MINIMO = 700

# Colunas que a recaptura do clima NAO pode ter tocado.
COLUNAS_INTOCAVEIS = [
    "fonte", "SE", "ano", "semana", "numero_de_armadilhas",
    "aedes_aegypti", "aedes_albopictus", "culex_sp",
    "aedes_aegypti_por_armadilha", "denominador_aproximado",
    "casos_confirmados", "nino34_anom", "oni",
]

TOLERANCIA_SOMA = 1e-3


def conferir(descricao: str, passou: bool, detalhe: str) -> bool:
    """Imprime o veredito de um criterio e devolve se ele passou."""
    marca = "OK  " if passou else "FALHA"
    print(f"[{marca}] {descricao}: {detalhe}", flush=True)
    return passou


def main() -> None:
    tabela_antes = pd.read_csv(CAMINHO_TABELA_ANTES, parse_dates=[COLUNA_DATA], low_memory=False)
    tabela_depois = pd.read_csv(
        settings.CAMINHO_TABELA_FINAL, parse_dates=[COLUNA_DATA], low_memory=False
    )

    resultados = []

    resultados.append(
        conferir(
            "criterio 1 - formato 725x36",
            tabela_depois.shape == FORMATO_ESPERADO,
            f"{tabela_depois.shape}",
        )
    )

    resultados.append(
        conferir(
            "criterio 1 - ordem das colunas preservada",
            list(tabela_depois.columns) == list(tabela_antes.columns),
            "identica" if list(tabela_depois.columns) == list(tabela_antes.columns) else "MUDOU",
        )
    )

    resultados.append(
        conferir(
            "criterio 1 - grade de datas preservada",
            tabela_depois[COLUNA_DATA].equals(tabela_antes[COLUNA_DATA]),
            f"{tabela_depois[COLUNA_DATA].min().date()} -> {tabela_depois[COLUNA_DATA].max().date()}",
        )
    )

    vetor_nao_nulos = int(tabela_depois["aedes_aegypti_por_armadilha"].notna().sum())
    vetor_soma = float(tabela_depois["aedes_aegypti_por_armadilha"].sum())
    resultados.append(
        conferir(
            "criterio 2 - vetor intocado",
            vetor_nao_nulos == VETOR_NAO_NULOS_ESPERADO
            and abs(vetor_soma - VETOR_SOMA_ESPERADA) < TOLERANCIA_SOMA,
            f"nao-nulos={vetor_nao_nulos} (esperado {VETOR_NAO_NULOS_ESPERADO}) "
            f"soma={vetor_soma:.4f} (esperado {VETOR_SOMA_ESPERADA})",
        )
    )

    casos_nao_nulos = int(tabela_depois["casos_confirmados"].notna().sum())
    casos_soma = float(tabela_depois["casos_confirmados"].sum())
    resultados.append(
        conferir(
            "criterio 3 - casos intocados",
            casos_nao_nulos == CASOS_NAO_NULOS_ESPERADO
            and abs(casos_soma - CASOS_SOMA_ESPERADA) < TOLERANCIA_SOMA,
            f"nao-nulos={casos_nao_nulos} (esperado {CASOS_NAO_NULOS_ESPERADO}) "
            f"soma={casos_soma:.0f} (esperado {CASOS_SOMA_ESPERADA:.0f})",
        )
    )

    # Conferencia coluna a coluna das colunas que nao sao de clima: nenhuma
    # celula pode ter mudado, nem de valor nem de nulidade.
    colunas_alteradas = []
    for nome_coluna in COLUNAS_INTOCAVEIS:
        iguais = tabela_depois[nome_coluna].equals(tabela_antes[nome_coluna])
        if not iguais:
            colunas_alteradas.append(nome_coluna)

    resultados.append(
        conferir(
            "criterio 2+3 - nenhuma coluna nao-clima alterada",
            len(colunas_alteradas) == 0,
            "nenhuma" if not colunas_alteradas else f"ALTERADAS: {colunas_alteradas}",
        )
    )

    temp_nao_nulos = int(tabela_depois["temp_media"].notna().sum())
    resultados.append(
        conferir(
            "criterio 5 - clima cobre a serie",
            temp_nao_nulos >= TEMP_MEDIA_NAO_NULOS_MINIMO,
            f"temp_media nao-nulos={temp_nao_nulos} (antes 388, minimo exigido {TEMP_MEDIA_NAO_NULOS_MINIMO})",
        )
    )

    # Ganho efetivo: a interseccao que o Teste A usa.
    trio_antes = (
        tabela_antes["temp_media"].notna()
        & tabela_antes["aedes_aegypti_por_armadilha"].notna()
        & tabela_antes["casos_confirmados"].notna()
    ).sum()
    trio_depois = (
        tabela_depois["temp_media"].notna()
        & tabela_depois["aedes_aegypti_por_armadilha"].notna()
        & tabela_depois["casos_confirmados"].notna()
    ).sum()
    dupla_depois = (
        tabela_depois["temp_media"].notna()
        & tabela_depois["aedes_aegypti_por_armadilha"].notna()
    ).sum()

    print(f"\nGANHO MEDIDO:", flush=True)
    print(f"  clima+vetor+casos_confirmados: {trio_antes} -> {trio_depois} semanas", flush=True)
    print(f"  clima+vetor (teto p/ notificados): {dupla_depois} semanas", flush=True)

    print("", flush=True)
    if all(resultados):
        print("CERTIFICACAO APROVADA: a recaptura do clima nao alterou nada alem do clima.", flush=True)
    else:
        print("CERTIFICACAO REPROVADA: ver as linhas [FALHA] acima.", flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
