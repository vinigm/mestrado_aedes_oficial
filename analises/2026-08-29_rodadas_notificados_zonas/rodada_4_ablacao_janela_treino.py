"""

Rodada 4 de 29/08/2026: treinar com os 14 anos inteiros e melhor do que treinar
so com o passado recente?

Pre-declarado em PRE_DECLARACAO.md (Rodada 4) ANTES de rodar. E uma secao de
ROBUSTEZ, nao de descoberta: sem teste de significancia e sem entrar na
contagem de multiplas comparacoes.

A pergunta nao e retorica. A rede de armadilhas mudou muito em 14 anos - numero
de armadilhas, protocolo de inspecao, a enchente de maio/2024 (tres semanas sem
vistoria) e o choque de controle de 2025. Dado de 2013 pode estar descrevendo
um sistema que nao existe mais; nesse caso ele e ruido, nao informacao.

O alvo aqui e a DENSIDADE DO VETOR (aedes_aegypti_por_armadilha), e nao os
casos, por dois motivos: e a serie que realmente tem 14 anos (casos so existem
de 2018 em diante, entao nela a pergunta "desde 2012?" nem se coloca), e e o
alvo que a letra do PEP pede.

Os tres regimes sao avaliados EXATAMENTE nas mesmas semanas de teste. Sem isso
a comparacao nao existe: um regime que comeca a testar mais cedo pegaria um
periodo diferente da serie e a diferenca seria de periodo, nao de janela.

Uso:  python rodada_4_ablacao_janela_treino.py

"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_SAIDAS = PASTA_ANALISE / "saidas"
CAMINHO_TABELA_FINAL = (
    PASTA_ANALISE.parents[1]
    / "modelagem_aedes"
    / "dados"
    / "entradas"
    / "tabela_modelagem"
    / "tabela_final.csv"
)

COLUNA_DATA = "data_inicio_semana_epidemi"
COLUNA_ALVO = "aedes_aegypti_por_armadilha"

SEMANAS_POR_ANO = 52
LAGS_SEMANAS = (1, 2, 3, 4)
JANELA_MEDIA_MOVEL = 4
HORIZONTES = (1, 4, 8, 12)
SEMENTE_ALEATORIA = 42

# A janela de avaliacao comum aos tres regimes. Comeca em 2022 porque o regime
# "expansivel desde 2020" precisa de 2 anos de historico antes de prever, e os
# tres tem que ser julgados nas MESMAS semanas.
DATA_INICIO_AVALIACAO = pd.Timestamp("2022-01-02")

# Quantos anos a janela deslizante carrega.
ANOS_JANELA_DESLIZANTE = 6

PARAMETROS_LIGHTGBM = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "verbose": -1,
    "n_jobs": 1,
    "random_state": SEMENTE_ALEATORIA,
}

PREFIXOS_CLIMA = (
    "temp_media_lag",
    "precip_total_mm_lag",
    "orvalho_media_lag",
    "umid_media_lag",
    "pressao_media_lag",
)


def carregar_serie_semanal() -> pd.DataFrame:
    """

    Abre a tabela_final e deixa uma linha por semana, em ordem cronologica.

    Le apenas; nao escreve nada no pacote.

    """
    tabela = pd.read_csv(CAMINHO_TABELA_FINAL, parse_dates=[COLUNA_DATA], low_memory=False)
    return tabela.sort_values(COLUNA_DATA).reset_index(drop=True)


def construir_features(serie: pd.DataFrame) -> pd.DataFrame:
    """

    Cria as colunas do modelo: defasagens do vetor e do clima, media movel e a
    marcacao circular da epoca do ano.

    Usa a mesma receita do pacote (dominio/features.py): defasagens de 1 a 4
    semanas, media movel de 4 semanas e seno/cosseno da semana do ano. Semana
    sem dado propaga NaN naturalmente - nada e preenchido.

    """
    dados = serie.copy()

    colunas_para_defasar = [
        COLUNA_ALVO,
        "temp_media",
        "precip_total_mm",
        "orvalho_media",
        "umid_media",
        "pressao_media",
    ]
    for nome_coluna in colunas_para_defasar:
        for numero_de_semanas in LAGS_SEMANAS:
            dados[f"{nome_coluna}_lag{numero_de_semanas}"] = dados[nome_coluna].shift(
                numero_de_semanas
            )

    dados["vetor_mm4"] = dados[COLUNA_ALVO].rolling(JANELA_MEDIA_MOVEL).mean()

    angulo_sazonal = 2 * np.pi * dados["semana"] / SEMANAS_POR_ANO
    dados["sem_sin"] = np.sin(angulo_sazonal)
    dados["sem_cos"] = np.cos(angulo_sazonal)
    return dados


def selecionar_colunas_do_modelo(dados: pd.DataFrame) -> list[str]:
    """

    Monta a lista de colunas do modelo, na ordem em que aparecem na tabela.

    A ordem importa: treinar e prever precisam usar as mesmas colunas na mesma
    ordem.

    """
    colunas_vetor = []
    colunas_clima = []
    for nome_coluna in dados.columns:
        if nome_coluna.startswith(f"{COLUNA_ALVO}_lag") or nome_coluna == "vetor_mm4":
            colunas_vetor.append(nome_coluna)
        elif nome_coluna.startswith(PREFIXOS_CLIMA):
            colunas_clima.append(nome_coluna)

    return colunas_vetor + colunas_clima + ["sem_sin", "sem_cos", "alvo_sin", "alvo_cos"]


def preparar_horizonte(dados: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """

    Desloca o alvo h semanas para frente e marca a epoca do ano da semana-alvo.

    """
    preparados = dados.copy()
    preparados["y_h"] = dados[COLUNA_ALVO].shift(-horizonte)

    semana_alvo = dados["semana"].shift(-horizonte)
    angulo_alvo = 2 * np.pi * semana_alvo / SEMANAS_POR_ANO
    preparados["alvo_sin"] = np.sin(angulo_alvo)
    preparados["alvo_cos"] = np.cos(angulo_alvo)
    return preparados


def selecionar_treino_do_regime(
    dados_validos: pd.DataFrame,
    data_de_corte: pd.Timestamp,
    regime: str,
) -> pd.DataFrame:
    """

    Devolve as linhas de treino disponiveis para um regime, numa data de corte.

    Os tres regimes:
      - 'expansivel_2012': tudo o que existe ate a data de corte;
      - 'expansivel_2020': o mesmo, mas descartando o que e anterior a 2020;
      - 'deslizante_6anos': so os ultimos ANOS_JANELA_DESLIZANTE anos.

    Args:
        dados_validos: Todas as linhas utilizaveis, em ordem cronologica.
        data_de_corte: A semana que esta sendo prevista; o treino usa so o que
            e anterior a ela.
        regime: Qual dos tres regimes aplicar.

    Returns:
        As linhas de treino daquele regime naquela data.

    Raises:
        ValueError: Se o regime pedido nao existir.

    """
    passado = dados_validos.loc[dados_validos[COLUNA_DATA] < data_de_corte]

    if regime == "expansivel_2012":
        return passado

    if regime == "expansivel_2020":
        return passado.loc[passado[COLUNA_DATA] >= pd.Timestamp("2020-01-01")]

    if regime == "deslizante_6anos":
        inicio_da_janela = data_de_corte - pd.DateOffset(years=ANOS_JANELA_DESLIZANTE)
        return passado.loc[passado[COLUNA_DATA] >= inicio_da_janela]

    raise ValueError(f"regime desconhecido: {regime!r}")


REGIMES = ("expansivel_2012", "expansivel_2020", "deslizante_6anos")


def executar_ablacao(dados: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """

    Roda os tres regimes de janela de treino no mesmo horizonte e nas mesmas
    semanas de teste.

    Em cada semana da janela de avaliacao, os tres regimes treinam com o
    subconjunto de passado que lhes cabe e preveem a MESMA semana. A previsao
    de cada um vai para a mesma linha do resultado, entao a comparacao e
    pareada semana a semana.

    Returns:
        Uma linha por semana avaliada, com o valor real e a previsao de cada
        regime, alem do tamanho do treino que cada um teve.

    """
    preparados = preparar_horizonte(dados, horizonte)
    colunas_modelo = selecionar_colunas_do_modelo(preparados)

    colunas_exigidas = colunas_modelo + ["y_h"]
    dados_validos = preparados.dropna(subset=colunas_exigidas).reset_index(drop=True)

    semanas_de_avaliacao = dados_validos.loc[
        dados_validos[COLUNA_DATA] >= DATA_INICIO_AVALIACAO, COLUNA_DATA
    ].tolist()

    linhas_resultado = []
    for data_de_corte in semanas_de_avaliacao:
        linha_teste = dados_validos.loc[dados_validos[COLUNA_DATA] == data_de_corte]

        linha_resultado = {
            "h": horizonte,
            "data_origem": data_de_corte,
            "real": float(linha_teste["y_h"].to_numpy()[0]),
        }

        for regime in REGIMES:
            treino = selecionar_treino_do_regime(dados_validos, data_de_corte, regime)

            if len(treino) < 52:
                linha_resultado[f"previsao_{regime}"] = np.nan
                linha_resultado[f"n_treino_{regime}"] = len(treino)
                continue

            modelo = LGBMRegressor(**PARAMETROS_LIGHTGBM)
            modelo.fit(treino[colunas_modelo], treino["y_h"])
            previsao = float(modelo.predict(linha_teste[colunas_modelo])[0])

            linha_resultado[f"previsao_{regime}"] = previsao
            linha_resultado[f"n_treino_{regime}"] = len(treino)

        linhas_resultado.append(linha_resultado)

    return pd.DataFrame(linhas_resultado)


def resumir_regimes(detalhado: pd.DataFrame) -> pd.DataFrame:
    """

    Resume o desempenho de cada regime em MAE, RMSE e R2, por horizonte.

    Todas as metricas sao calculadas nas MESMAS semanas para os tres regimes
    (as semanas em que os tres tem previsao), senao a comparacao seria injusta.

    """
    linhas_resumo = []
    for horizonte, grupo in detalhado.groupby("h"):
        colunas_previsao = [f"previsao_{regime}" for regime in REGIMES]
        comparaveis = grupo.dropna(subset=colunas_previsao + ["real"])

        valores_reais = comparaveis["real"].to_numpy()
        media_dos_reais = valores_reais.mean()
        soma_dos_quadrados_total = float(((valores_reais - media_dos_reais) ** 2).sum())

        for regime in REGIMES:
            previsoes = comparaveis[f"previsao_{regime}"].to_numpy()
            erros = previsoes - valores_reais

            erro_absoluto_medio = float(np.abs(erros).mean())
            raiz_do_erro_quadratico = float(np.sqrt((erros ** 2).mean()))
            soma_dos_quadrados_residual = float((erros ** 2).sum())

            if soma_dos_quadrados_total > 0:
                r2 = 1.0 - soma_dos_quadrados_residual / soma_dos_quadrados_total
            else:
                r2 = float("nan")

            linhas_resumo.append(
                {
                    "h": horizonte,
                    "regime": regime,
                    "semanas_avaliadas": len(comparaveis),
                    "n_treino_mediano": int(comparaveis[f"n_treino_{regime}"].median()),
                    "MAE": erro_absoluto_medio,
                    "RMSE": raiz_do_erro_quadratico,
                    "R2": r2,
                }
            )

    return pd.DataFrame(linhas_resumo)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    serie = carregar_serie_semanal()
    dados = construir_features(serie)

    print(f"serie: {len(serie)} semanas | alvo: {COLUNA_ALVO}", flush=True)
    print(f"janela de avaliacao comum: a partir de {DATA_INICIO_AVALIACAO.date()}", flush=True)
    print(f"regimes: {', '.join(REGIMES)}\n", flush=True)

    detalhados = []
    for horizonte in HORIZONTES:
        print(f"h={horizonte}: rodando os 3 regimes...", end=" ", flush=True)
        detalhado = executar_ablacao(dados, horizonte)
        detalhados.append(detalhado)
        print(f"{len(detalhado)} semanas avaliadas", flush=True)

    detalhado_final = pd.concat(detalhados, ignore_index=True)
    resumo_final = resumir_regimes(detalhado_final)

    detalhado_final.to_csv(PASTA_SAIDAS / "rodada_4_ablacao_por_semana.csv", index=False)
    resumo_final.to_csv(PASTA_SAIDAS / "rodada_4_ablacao_resumo.csv", index=False)

    print("\n" + "=" * 78, flush=True)
    print("RESUMO — ablacao de janela de treino (alvo: densidade do vetor)", flush=True)
    print("=" * 78, flush=True)
    print(resumo_final.round(4).to_string(index=False), flush=True)

    print("\n=== melhor regime por horizonte (menor MAE) ===", flush=True)
    for horizonte, grupo in resumo_final.groupby("h"):
        melhor = grupo.loc[grupo["MAE"].idxmin()]
        print(f"  h={horizonte:2d}: {melhor['regime']:20s} "
              f"MAE={melhor['MAE']:.4f}  R2={melhor['R2']:.4f}", flush=True)

    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
