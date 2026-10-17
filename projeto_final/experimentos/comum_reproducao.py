"""Pecas comuns dos experimentos da reproducao da selecao (E6a, E6b, E6c) e do WIS (E7).

Pre-declaracao aprovada: `analises/2026-10-12_pre_declaracao_reproducao_e_wis/PRE_DECLARACAO.md`.

Segue o padrao de `experimentos/comum_ciencia.py`: parciais com escrita atomica,
log com carimbo de tempo, leitura dos gabaritos com precisao total dos floats.
Aqui ficam so as partes que as quatro etapas repartem: caminhos, gabaritos
copiados do codigo antigo e leitura das previsoes de referencia.

Nenhum modulo certificado e alterado: a tabela, os parciais e o log reaproveitam
`experimentos.comum_ciencia` e `experimentos.referencia` por importacao.
"""

import pathlib

import pandas as pd

from aedes.configuracao import COLUNA_DATA_ALVO, COLUNA_DATA_DE_ORIGEM
from experimentos.comum_ciencia import (
    PASTA_DO_PROJETO,
    TOLERANCIA_DAS_TRAVAS,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_json_de_forma_atomica,
    gravar_parcial,
    ler_previsoes_da_referencia,
    validar_horizontes,
)

PASTA_DA_REPRODUCAO = PASTA_DO_PROJETO / "resultados" / "reproducao_selecao"
PASTA_DO_WIS = PASTA_DO_PROJETO / "resultados" / "wis"
PASTA_DOS_GABARITOS = PASTA_DO_PROJETO / "testes" / "referencia_antiga"
CAMINHO_DAS_ESCOLHAS_DO_COMPOSTO_DA_E3 = PASTA_DO_PROJETO / "resultados" / "ciencia" / "E3_composto" / "previsoes.csv"

# Nomes dos bracos da referencia certificada, em `resultados/referencia/previsoes.csv`.
NOME_DA_REFERENCIA_FOLHA_5 = "referencia"
NOME_DA_REFERENCIA_FOLHA_20 = "HistGB_folha20_M1"

# Gabaritos copiados do codigo antigo para `testes/referencia_antiga/` (ver MANIFESTO_E6_E7.csv).
CAMINHOS_DOS_GABARITOS_DA_GRADE_DE_30 = (
    PASTA_DOS_GABARITOS / "e6b_corrigido_previsoes_parciais.csv",
    PASTA_DOS_GABARITOS / "e6b_corrigido_previsoes_padrao.csv",
    PASTA_DOS_GABARITOS / "e6b_corrigido_previsoes_restante.csv",
)
CAMINHO_DO_GABARITO_DA_GRADE_DE_18 = PASTA_DOS_GABARITOS / "e6c_previsoes_por_configuracao.csv"
CAMINHO_DO_RANKING_ANTIGO_DA_GRADE_DE_18 = PASTA_DOS_GABARITOS / "e6c_ranking_calibracao.csv"
CAMINHO_DAS_COMPARACOES_ANTIGAS_DA_GRADE_DE_18 = PASTA_DOS_GABARITOS / "e6c_comparacoes.csv"
CAMINHO_DO_GABARITO_DOS_QUANTIS = PASTA_DOS_GABARITOS / "e7_previsoes_quantis.csv"
CAMINHO_DO_GABARITO_DO_WIS = PASTA_DOS_GABARITOS / "e7_wis_e_cobertura.csv"

# Reexportados para os scripts das etapas.
REEXPORTADOS = (
    TOLERANCIA_DAS_TRAVAS,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_json_de_forma_atomica,
    gravar_parcial,
    ler_previsoes_da_referencia,
    validar_horizontes,
)


def ler_csv_de_previsoes(caminho: pathlib.Path, colunas_de_data: list[str]) -> pd.DataFrame:
    """Le um CSV de previsoes com precisao total dos floats (`round_trip`) e as datas convertidas.

    Raises:
        FileNotFoundError: Se o arquivo nao existir.
    """
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo ausente: {caminho}")
    return pd.read_csv(caminho, parse_dates=colunas_de_data, float_precision="round_trip")


def ler_parciais_com_datas(caminho: pathlib.Path) -> pd.DataFrame:
    """Le um parcial das etapas (com `data_origem` e `data_alvo`) com precisao total dos floats."""
    return ler_csv_de_previsoes(caminho, [COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO])
