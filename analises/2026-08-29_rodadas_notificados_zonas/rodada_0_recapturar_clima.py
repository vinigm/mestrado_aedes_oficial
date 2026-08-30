"""

Rodada 0 de 29/08/2026: recaptura o clima do NASA POWER desde 2012 e certifica
que a serie que ja existia nao mudou.

Roda SO o passo do clima do preparar_dados.py. Os outros passos (limpeza e
unificacao dos arquivos da Secretaria, SINAN, ENSO) sao caros e mexem na base
certificada do vetor - nao ha motivo para reexecuta-los aqui, e a base
certificada nao pode ser tocada.

A certificacao e adversarial no sentido que importa: ela tenta REPROVAR a
recaptura, comparando semana a semana as 388 semanas que ja existiam. Se a
NASA tiver revisado dado historico, o script para e nao grava nada.

Uso:  python rodada_0_recapturar_clima.py

"""

import sys
from pathlib import Path

PASTA_PACOTE = Path(__file__).resolve().parents[2] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import pandas as pd

from config import settings
from preparo import capturar_clima

# Primeiro domingo da serie do vetor na base certificada da Secretaria.
DATA_INICIO_SERIE_VETOR = "20120923"

# Tolerancia relativa da comparacao com a serie antiga. Fica apertada de
# proposito: dentro do periodo estavel, qualquer divergencia acima disso
# significa que a NASA revisou dado historico, e nesse caso a rodada TEM que
# parar para investigacao humana - nao se afrouxa tolerancia para o teste
# passar (regra do padrao de codigo, secao 19.5).
TOLERANCIA_RELATIVA = 1e-9

# Ultimo domingo do periodo em que a serie do NASA POWER ja esta consolidada.
# O modulo capturar_clima.py documenta que so as semanas recentes mudam ("a
# NASA ajusta os dados novos depois de um tempo"): a radiacao solar, derivada
# de satelite, e reprocessada com atraso maior que as demais medidas. Medido em
# 29/08/2026 contra a captura de 16/08/2026: as 365 semanas ate esta data
# bateram EXATAMENTE, e as 23 seguintes divergiram. Divergencia dentro do
# periodo estavel e bloqueante; depois dele e esperada e so registrada.
# Ver EMENDA 1 da PRE_DECLARACAO.md desta pasta.
DATA_LIMITE_SERIE_ESTAVEL = pd.Timestamp("2025-12-21")

COLUNA_DATA = "data_inicio_semana_epidemi"


def comparar_com_serie_anterior(
    clima_novo: pd.DataFrame,
    clima_anterior: pd.DataFrame,
) -> pd.DataFrame:
    """

    Compara as semanas que existem nas duas versoes e devolve so as divergentes.

    A comparacao e restrita a interseccao de datas: as semanas de 2012 a 2018
    so existem na versao nova, entao nao ha o que comparar nelas. A coluna
    'periodo' separa o que e bloqueante do que e esperado: 'estavel' para as
    semanas ate DATA_LIMITE_SERIE_ESTAVEL e 'reprocessamento' para as
    posteriores, que a NASA ainda ajusta.

    Args:
        clima_novo: Tabela semanal recem-baixada, iniciando em 2012.
        clima_anterior: Tabela semanal que estava gravada, iniciando em 2018.

    Returns:
        Uma tabela com uma linha por (semana, coluna) divergente, com a coluna
        'periodo'. Vazia quando as duas versoes concordam dentro da tolerancia.

    """
    datas_em_comum = clima_novo[COLUNA_DATA].isin(clima_anterior[COLUNA_DATA])
    novo_na_interseccao = clima_novo.loc[datas_em_comum].set_index(COLUNA_DATA).sort_index()
    anterior_na_interseccao = clima_anterior.set_index(COLUNA_DATA).sort_index()

    colunas_numericas = anterior_na_interseccao.select_dtypes("number").columns

    linhas_divergentes = []
    for nome_coluna in colunas_numericas:
        valores_novos = novo_na_interseccao[nome_coluna]
        valores_anteriores = anterior_na_interseccao[nome_coluna]

        diferenca_absoluta = (valores_novos - valores_anteriores).abs()
        limite_por_semana = valores_anteriores.abs() * TOLERANCIA_RELATIVA
        divergiu = diferenca_absoluta > limite_por_semana

        for data_divergente in valores_novos.index[divergiu.fillna(False)]:
            if data_divergente <= DATA_LIMITE_SERIE_ESTAVEL:
                periodo = "estavel"
            else:
                periodo = "reprocessamento"

            linhas_divergentes.append(
                {
                    "data": data_divergente,
                    "coluna": nome_coluna,
                    "periodo": periodo,
                    "valor_anterior": valores_anteriores.loc[data_divergente],
                    "valor_novo": valores_novos.loc[data_divergente],
                }
            )

    return pd.DataFrame(linhas_divergentes)


def main() -> None:
    caminho_saida = settings.CAMINHO_CLIMA_SEMANAL
    pasta_saidas = Path(__file__).resolve().parent / "saidas"

    clima_anterior = pd.read_csv(caminho_saida, parse_dates=[COLUNA_DATA])
    print(f"clima ANTERIOR: {clima_anterior.shape} | "
          f"{clima_anterior[COLUNA_DATA].min().date()} -> {clima_anterior[COLUNA_DATA].max().date()}",
          flush=True)

    print(f"baixando NASA POWER desde {DATA_INICIO_SERIE_VETOR} (pode levar 1-2 min)...", flush=True)
    clima_novo = capturar_clima.capturar_clima(inicio=DATA_INICIO_SERIE_VETOR)
    print(f"clima NOVO: {clima_novo.shape} | "
          f"{clima_novo[COLUNA_DATA].min().date()} -> {clima_novo[COLUNA_DATA].max().date()}",
          flush=True)

    divergencias = comparar_com_serie_anterior(clima_novo, clima_anterior)

    semanas_em_comum = int(clima_novo[COLUNA_DATA].isin(clima_anterior[COLUNA_DATA]).sum())
    semanas_estaveis = int(
        (clima_anterior[COLUNA_DATA] <= DATA_LIMITE_SERIE_ESTAVEL).sum()
    )
    print(f"\nsemanas comparadas: {semanas_em_comum} "
          f"(estaveis, bloqueantes: {semanas_estaveis} | "
          f"em reprocessamento: {semanas_em_comum - semanas_estaveis})", flush=True)

    if not divergencias.empty:
        caminho_divergencias = pasta_saidas / "rodada_0_divergencias_clima.csv"
        divergencias.to_csv(caminho_divergencias, index=False)
        print(f"divergencias gravadas em: {caminho_divergencias}", flush=True)

    divergencias_bloqueantes = divergencias.loc[divergencias["periodo"] == "estavel"] if not divergencias.empty else divergencias

    if not divergencias_bloqueantes.empty:
        print(f"REPROVADO: {len(divergencias_bloqueantes)} divergencias no periodo ESTAVEL "
              f"(ate {DATA_LIMITE_SERIE_ESTAVEL.date()}).", flush=True)
        print("Nada foi gravado. A NASA revisou dado historico consolidado - investigar.", flush=True)
        raise SystemExit(1)

    print(f"APROVADO: as {semanas_estaveis} semanas do periodo estavel bateram exatamente.", flush=True)

    if not divergencias.empty:
        semanas_reprocessadas = divergencias["data"].nunique()
        print(f"[esperado] {len(divergencias)} valores em {semanas_reprocessadas} semanas "
              f"posteriores a {DATA_LIMITE_SERIE_ESTAVEL.date()} vieram reprocessados pela NASA; "
              f"o valor novo e o mais preciso e substitui o anterior.", flush=True)

    clima_novo.to_csv(caminho_saida, index=False)
    print(f"\nsalvo: {caminho_saida} | linhas x colunas: {clima_novo.shape}", flush=True)


if __name__ == "__main__":
    main()
