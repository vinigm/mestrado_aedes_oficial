"""

Testa as colunas calculadas que dependem do tempo (arquivo dominio/features.py).

Confere a media movel, a escolha de colunas pelo comeco do nome, e se montar
essas colunas e o alvo (o que o modelo tenta prever) respeita cada bloco de
dados (cada fonte) e nao mexe na tabela original. E rapido, usa so pandas e
numpy. Pra rodar: python tests/test_features.py (ou pytest).

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from dominio import features



# Monta uma tabela de teste com 2 blocos (fontes) e um valor vazio (NaN), pra testar as colunas de "semanas atras" (lag), a media movel e a sazonalidade.
def montar_dados_sinteticos():
    linhas = []
    for fonte in ["a", "b"]:
        for indice in range(8):
            if fonte == "a" and indice == 3:
                casos = np.nan
            else:
                casos = float(indice * 2)
            linhas.append(
                {
                    "fonte": fonte,
                    "semana": (indice % 52) + 1,
                    "casos": casos,
                    "aedes_aegypti_por_armadilha": float(indice) * 0.5,
                    "temp_media": 20.0 + indice,
                    "umid_media": 70.0 + indice,
                    "precip_total_mm": float(indice),
                    "orvalho_media": 15.0 + indice,
                    "pressao_media": 1000.0 + indice,
                }
            )
    return pd.DataFrame(linhas)



def test_media_movel_4_semanas_igual_rolling():
    serie = pd.Series([1.0, np.nan, 3.0, 4.0, 5.0, 6.0])
    esperado = serie.rolling(4).mean()
    obtido = features.media_movel_4_semanas(serie)
    pd.testing.assert_series_equal(obtido, esperado, check_exact=False, rtol=1e-12)



def test_selecionar_colunas_por_prefixo_preserva_ordem():
    dados = pd.DataFrame(
        columns=["casos_lag1", "casos_mm4", "temp_media_lag2", "sem_sin", "outra"]
    )
    prefixos = ("casos_lag", "casos_mm", "temp_media_lag")
    obtido = features.selecionar_colunas_por_prefixo(dados, prefixos)
    assert obtido == ["casos_lag1", "casos_mm4", "temp_media_lag2"]



def test_construir_features_nao_muta_a_entrada():
    dados = montar_dados_sinteticos()
    colunas_antes = list(dados.columns)
    features.construir_features_temporais(dados)
    assert list(dados.columns) == colunas_antes



def test_construir_features_gera_lags_por_bloco():
    dados = montar_dados_sinteticos()
    com_features = features.construir_features_temporais(dados)
    bloco_a = com_features[com_features["fonte"] == "a"].reset_index(drop=True)
    # A 1a linha do bloco nao tem uma linha anterior dentro do mesmo bloco -> a coluna "1 semana atras" (lag1) fica vazia (NaN).
    assert pd.isna(bloco_a.loc[0, "casos_lag1"])
    # Na 2a linha, o valor de "1 semana atras" (lag1) e o valor de casos da 1a linha do MESMO bloco.
    assert bloco_a.loc[1, "casos_lag1"] == bloco_a.loc[0, "casos"]
    assert "sem_sin" in com_features.columns
    assert "sem_cos" in com_features.columns



def test_construir_alvo_horizonte_desloca_para_frente():
    dados = montar_dados_sinteticos()
    horizonte = 2
    com_alvo = features.construir_alvo_horizonte(dados, "casos", horizonte)
    bloco_b = com_alvo[com_alvo["fonte"] == "b"].reset_index(drop=True)
    # O valor de y_h (o alvo, o que o modelo tenta prever) numa linha e igual aos casos "horizonte" semanas depois, dentro do mesmo bloco.
    assert bloco_b.loc[0, "y_h"] == bloco_b.loc[horizonte, "casos"]
    # As ultimas linhas do bloco (tantas quanto o horizonte) nao tem semana futura pra olhar -> ficam vazias (NaN).
    assert pd.isna(bloco_b["y_h"].iloc[-1])



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
