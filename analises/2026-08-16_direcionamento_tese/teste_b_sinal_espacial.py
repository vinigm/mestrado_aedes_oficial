"""
TESTE B — Sinal espacial do vetor (Aedes aegypti) por bairro e por zona sintética.

Pergunta: o sinal de densidade de Aedes por bairro é persistente o bastante para
ser previsível? Em que granularidade (bairro vs zona sintética) o ruído de
amostragem (poucas armadilhas por bairro-semana) é aceitável?

Fonte de dados (SOMENTE LEITURA, nenhum arquivo do projeto é modificado):
    secretaria_poa_armadilhas.parquet (636.587 linhas, 2012-2026)

Escopo temporal: 2019-2026. Motivo: a coluna `inspecao_realizada` só é
preenchida (True/False) a partir de 2018-12-30 — antes disso ela é NA para
100% das linhas, então não há como saber quais armadilhas foram de fato
inspecionadas numa dada semana antes dessa data. Usar `inspecao_realizada`
== True automaticamente restringe a amostra a 2019+.

Saída: 6 CSVs numéricos (sem figuras) nesta mesma pasta.
"""

import os
import time

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

PARQUET_ARMADILHAS = (
    "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/"
    "Meu Drive/Mestrado/Pesquisa/Meu_Projeto/modelagem_aedes/dados/entradas/"
    "arquivos_secretaria_saude_poa/secretaria_poa_armadilhas.parquet"
)
PASTA_SAIDA = (
    "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/"
    "Meu Drive/Mestrado/Pesquisa/Meu_Projeto/analises/2026-08-16_direcionamento_tese"
)

DATA_INICIO_JANELA = "2019-01-01"
LIMIAR_ARMADILHAS_ELEGIBILIDADE = 10  # cobertura mínima p/ bairro entrar no painel
FRACAO_MINIMA_SEMANAS_COBERTAS = 0.5  # bairro precisa ter >=10 armadilhas em >=50% das semanas
LIMIAR_ARMADILHAS_SPLIT_HALF = 8      # bairro-semana precisa ter >=8 armadilhas p/ dividir ao meio
N_SORTEIOS_SPLIT_HALF = 50
SEMENTE_ALEATORIA = 42
LAGS_AUTOCORRELACAO = (1, 2, 4, 8)
LAGS_RANKING = (4, 8)


def carregar_dados_inspecionados():
    """Carrega o parquet de armadilhas, filtra só inspeções realizadas e 2019+.

    Normaliza um artefato de encoding: 'CAMAQUÃƑ' e 'CAMAQUÃ' são o MESMO
    bairro (confirmado por não haver sobreposição de anos entre as duas
    grafias: a primeira aparece só em partes de 2020/2025, a segunda no
    resto — é o mesmo texto salvo com uma codificação diferente em algum
    arquivo de origem). Essa normalização é feita só em memória, não altera
    o parquet original.
    """
    colunas = [
        "ano", "data_inicio_semana", "id_armadilha", "bairro",
        "latitude", "longitude", "aegypti_femea", "inspecao_realizada",
    ]
    df = pd.read_parquet(PARQUET_ARMADILHAS, columns=colunas)
    df = df[df["inspecao_realizada"] == True].copy()  # noqa: E712
    df["bairro"] = df["bairro"].replace({"CAMAQUÃƑ": "CAMAQUÃ"})
    df = df[df["data_inicio_semana"] >= DATA_INICIO_JANELA]
    return df


def montar_painel_grupo_semana(df, coluna_grupo):
    """Painel grupo-semana: nº de armadilhas inspecionadas, fêmeas e densidade."""
    painel = (
        df.groupby([coluna_grupo, "data_inicio_semana"])
        .agg(n_armadilhas=("id_armadilha", "nunique"), femeas=("aegypti_femea", "sum"))
        .reset_index()
    )
    painel["densidade"] = painel["femeas"] / painel["n_armadilhas"]
    return painel


def calcular_elegibilidade(painel, coluna_grupo, semanas_completas):
    """Reindexa o painel na grade completa de semanas (preenchendo ausências
    com 0 armadilhas) e calcula, por grupo, a fração de semanas com
    >= LIMIAR_ARMADILHAS_ELEGIBILIDADE armadilhas inspecionadas.
    """
    grupos = painel[coluna_grupo].unique()
    indice_completo = pd.MultiIndex.from_product(
        [grupos, semanas_completas], names=[coluna_grupo, "data_inicio_semana"]
    )
    reindexado = painel.set_index([coluna_grupo, "data_inicio_semana"]).reindex(indice_completo)
    reindexado["n_armadilhas"] = reindexado["n_armadilhas"].fillna(0)
    fracao_cobertura = reindexado.groupby(coluna_grupo)["n_armadilhas"].apply(
        lambda x: (x >= LIMIAR_ARMADILHAS_ELEGIBILIDADE).mean()
    )
    elegiveis = fracao_cobertura[fracao_cobertura >= FRACAO_MINIMA_SEMANAS_COBERTAS].index.tolist()
    return elegiveis, fracao_cobertura


def construir_serie_completa(painel, coluna_grupo, semanas_completas, elegiveis):
    """Série grupo-semana só dos grupos elegíveis, na grade completa de
    semanas, com o alvo suavizado mm4 (média móvel de 4 semanas, mínimo 2
    semanas não-nulas na janela).
    """
    indice_completo = pd.MultiIndex.from_product(
        [elegiveis, semanas_completas], names=[coluna_grupo, "data_inicio_semana"]
    )
    serie = painel.set_index([coluna_grupo, "data_inicio_semana"]).reindex(indice_completo).reset_index()
    serie = serie.sort_values([coluna_grupo, "data_inicio_semana"])
    serie["mm4"] = serie.groupby(coluna_grupo)["densidade"].transform(
        lambda x: x.rolling(4, min_periods=2).mean()
    )
    return serie


def autocorrelacao_mediana(serie_completa, coluna_grupo, lags=LAGS_AUTOCORRELACAO):
    """Autocorrelação do mm4 por grupo, em cada lag (semanas), usando só
    pares (t, t+lag) com ambos os valores não-nulos. Retorna a mediana entre
    grupos e o nº de grupos com dados suficientes (>=20 pares) em cada lag.
    """
    linhas = []
    for lag in lags:
        correlacoes = []
        for _, sub in serie_completa.groupby(coluna_grupo):
            sub = sub.sort_values("data_inicio_semana")
            valores = sub["mm4"].to_numpy()
            if len(valores) <= lag:
                continue
            a, b = valores[:-lag], valores[lag:]
            mascara = ~np.isnan(a) & ~np.isnan(b)
            if mascara.sum() < 20:
                continue
            r = np.corrcoef(a[mascara], b[mascara])[0, 1]
            correlacoes.append(r)
        linhas.append({
            "lag_semanas": lag,
            "autocorrelacao_mediana": np.median(correlacoes) if correlacoes else np.nan,
            "n_grupos_validos": len(correlacoes),
        })
    return pd.DataFrame(linhas)


def spearman_ranking_mediano(serie_completa, coluna_grupo, lags=LAGS_RANKING):
    """Spearman do ranking de grupos (por mm4) entre a semana t e t+lag,
    mediana ao longo de todas as semanas t com >=5 grupos válidos nos dois
    momentos.
    """
    pivot = serie_completa.pivot(index="data_inicio_semana", columns=coluna_grupo, values="mm4")
    pivot = pivot.sort_index()
    linhas = []
    for lag in lags:
        rhos = []
        n_semanas_total = len(pivot) - lag
        for i in range(max(n_semanas_total, 0)):
            linha_t = pivot.iloc[i]
            linha_t_lag = pivot.iloc[i + lag]
            mascara = linha_t.notna() & linha_t_lag.notna()
            if mascara.sum() < 5:
                continue
            rho, _ = stats.spearmanr(linha_t[mascara], linha_t_lag[mascara])
            if not np.isnan(rho):
                rhos.append(rho)
        linhas.append({
            "lag_semanas": lag,
            "spearman_ranking_mediano": np.median(rhos) if rhos else np.nan,
            "n_semanas_validas": len(rhos),
        })
    return pd.DataFrame(linhas)


def split_half_confiabilidade(df, coluna_grupo, elegiveis, n_sorteios=N_SORTEIOS_SPLIT_HALF,
                               semente=SEMENTE_ALEATORIA):
    """Confiabilidade split-half: em cada grupo-semana com
    >= LIMIAR_ARMADILHAS_SPLIT_HALF armadilhas, divide as armadilhas ao meio
    aleatoriamente e compara a densidade das duas metades.

    Repete N_SORTEIOS_SPLIT_HALF vezes (sorteio novo a cada rodada) e reporta
    a mediana da correlação de Pearson entre as metades:
      - 'raw'  -> densidade bruta da semana isolada.
      - 'mm4'  -> média móvel de 4 semanas aplicada à sequência de
                  semanas qualificadas de cada metade (mesmo sorteio ao
                  longo do tempo dentro de uma rodada). Isso testa se
                  suavizar no tempo reduz o ruído de amostragem.
    """
    rng = np.random.default_rng(semente)
    dfe = df[df[coluna_grupo].isin(elegiveis)]
    nivel_armadilha = (
        dfe.groupby([coluna_grupo, "data_inicio_semana", "id_armadilha"])["aegypti_femea"]
        .sum()
        .reset_index()
    )
    contagem = nivel_armadilha.groupby([coluna_grupo, "data_inicio_semana"])["id_armadilha"].transform("size")
    qualificados = nivel_armadilha[contagem >= LIMIAR_ARMADILHAS_SPLIT_HALF]

    grupos_semana = []
    vetores_femeas = []
    for chave, sub in qualificados.groupby([coluna_grupo, "data_inicio_semana"]):
        grupos_semana.append(chave)
        vetores_femeas.append(sub["aegypti_femea"].to_numpy())

    n_qualificados = len(grupos_semana)
    r_raw_por_sorteio = []
    r_mm4_por_sorteio = []

    for _ in range(n_sorteios):
        densidade_a = np.empty(n_qualificados)
        densidade_b = np.empty(n_qualificados)
        for i, femeas in enumerate(vetores_femeas):
            n = len(femeas)
            ordem = rng.permutation(n)
            metade = n // 2
            idx_a, idx_b = ordem[:metade], ordem[metade:]
            densidade_a[i] = femeas[idx_a].sum() / len(idx_a)
            densidade_b[i] = femeas[idx_b].sum() / len(idx_b)

        registro = pd.DataFrame(grupos_semana, columns=[coluna_grupo, "data_inicio_semana"])
        registro["densidade_a"] = densidade_a
        registro["densidade_b"] = densidade_b
        r_raw = np.corrcoef(registro["densidade_a"], registro["densidade_b"])[0, 1]
        r_raw_por_sorteio.append(r_raw)

        registro = registro.sort_values([coluna_grupo, "data_inicio_semana"])
        registro["mm4_a"] = registro.groupby(coluna_grupo)["densidade_a"].transform(
            lambda x: x.rolling(4, min_periods=2).mean()
        )
        registro["mm4_b"] = registro.groupby(coluna_grupo)["densidade_b"].transform(
            lambda x: x.rolling(4, min_periods=2).mean()
        )
        validos = registro.dropna(subset=["mm4_a", "mm4_b"])
        r_mm4 = np.corrcoef(validos["mm4_a"], validos["mm4_b"])[0, 1]
        r_mm4_por_sorteio.append(r_mm4)

    return {
        "n_grupo_semana_qualificados": n_qualificados,
        "raw_mediana": float(np.median(r_raw_por_sorteio)),
        "raw_min": float(np.min(r_raw_por_sorteio)),
        "raw_max": float(np.max(r_raw_por_sorteio)),
        "mm4_mediana": float(np.median(r_mm4_por_sorteio)),
        "mm4_min": float(np.min(r_mm4_por_sorteio)),
        "mm4_max": float(np.max(r_mm4_por_sorteio)),
    }


def decompor_variancia(serie_completa, coluna_grupo):
    """Decompõe a variância do mm4 (painel grupo-semana) em:
      - efeito de semana (sazonalidade comum a todos os grupos)
      - efeito fixo de grupo (bairro ou zona)
      - resíduo (só o dado espacial por grupo poderia prever isso)

    Método: two-way fixed effects por demeaning iterativo (Gauss-Seidel),
    igual ao que pacotes como reghdfe usam para painéis não-balanceados.
    Para deixar a decomposição exata (soma dos quadrados aditiva, sem termo
    de interação), roda em cima do SUBCONJUNTO de semanas 100% completas
    (todo grupo elegível tem mm4 não-nulo) — reporta quantas semanas isso é.
    """
    pivot = serie_completa.pivot(index="data_inicio_semana", columns=coluna_grupo, values="mm4")
    pivot = pivot.sort_index()
    semanas_completas_mask = pivot.notna().all(axis=1)
    n_semanas_totais = len(pivot)
    n_semanas_completas = int(semanas_completas_mask.sum())

    y = pivot.loc[semanas_completas_mask].to_numpy(dtype=float)
    media_geral = float(np.mean(y))

    n_semanas, n_grupos = y.shape
    efeito_semana = np.zeros(n_semanas)
    efeito_grupo = np.zeros(n_grupos)
    for _ in range(200):
        residuo_temp = y - efeito_semana[:, None] - media_geral
        novo_efeito_grupo = residuo_temp.mean(axis=0)
        residuo_temp2 = y - novo_efeito_grupo[None, :] - media_geral
        novo_efeito_semana = residuo_temp2.mean(axis=1)
        delta = np.max(np.abs(novo_efeito_grupo - efeito_grupo)) + np.max(np.abs(novo_efeito_semana - efeito_semana))
        efeito_grupo, efeito_semana = novo_efeito_grupo, novo_efeito_semana
        if delta < 1e-10:
            break

    residuo = y - media_geral - efeito_grupo[None, :] - efeito_semana[:, None]

    var_total = np.var(y - media_geral)
    # componentes: variância da matriz de efeitos replicada (balanceado, por construção exato)
    var_semana = np.var(np.tile(efeito_semana[:, None], (1, n_grupos)))
    var_grupo = np.var(np.tile(efeito_grupo[None, :], (n_semanas, 1)))
    var_residuo = np.var(residuo)

    return {
        "n_semanas_totais_no_periodo": n_semanas_totais,
        "n_semanas_100pct_completas_usadas": n_semanas_completas,
        "n_grupos": n_grupos,
        "variancia_total": var_total,
        "variancia_semana_pct": 100 * var_semana / var_total,
        "variancia_grupo_pct": 100 * var_grupo / var_total,
        "variancia_residuo_pct": 100 * var_residuo / var_total,
        "soma_pct_checagem": 100 * (var_semana + var_grupo + var_residuo) / var_total,
    }


def rodar_protocolo_completo(df, coluna_grupo, semanas_completas, nome_granularidade):
    """Roda elegibilidade + persistência + split-half + decomposição para uma
    granularidade (bairro, zona_k8 ou zona_k16). Retorna um dicionário de
    DataFrames de resultado, todos com a coluna 'granularidade' marcada.
    """
    painel = montar_painel_grupo_semana(df, coluna_grupo)
    elegiveis, fracao_cobertura = calcular_elegibilidade(painel, coluna_grupo, semanas_completas)
    serie_completa = construir_serie_completa(painel, coluna_grupo, semanas_completas, elegiveis)

    autocorr = autocorrelacao_mediana(serie_completa, coluna_grupo)
    autocorr["granularidade"] = nome_granularidade

    ranking = spearman_ranking_mediano(serie_completa, coluna_grupo)
    ranking["granularidade"] = nome_granularidade

    split_half = split_half_confiabilidade(df, coluna_grupo, elegiveis)
    split_half["granularidade"] = nome_granularidade

    decomposicao = decompor_variancia(serie_completa, coluna_grupo)
    decomposicao["granularidade"] = nome_granularidade

    resumo_cobertura = {
        "granularidade": nome_granularidade,
        "n_grupos_totais": int(painel[coluna_grupo].nunique()),
        "n_grupos_elegiveis": len(elegiveis),
        "grupos_elegiveis": ";".join(sorted(str(g) for g in elegiveis)),
    }

    return {
        "autocorrelacao": autocorr,
        "ranking": ranking,
        "split_half": split_half,
        "decomposicao": decomposicao,
        "cobertura": resumo_cobertura,
    }


def main():
    inicio = time.time()
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    print("Carregando dados de inspeções (parquet, leitura apenas)...")
    df = carregar_dados_inspecionados()
    semanas_completas = sorted(df["data_inicio_semana"].unique())
    print(f"  {len(df):,} linhas inspecionadas, {len(semanas_completas)} semanas "
          f"({semanas_completas[0]} a {semanas_completas[-1]})")

    # --------------------------------------------------------------
    # Zonas sintéticas via K-Means nas coordenadas das armadilhas
    # --------------------------------------------------------------
    print("Calculando zonas sintéticas (K-Means k=8 e k=16)...")
    coordenadas_armadilha = df.groupby("id_armadilha")[["latitude", "longitude"]].mean().dropna()
    kmeans_k8 = KMeans(n_clusters=8, random_state=SEMENTE_ALEATORIA, n_init=10).fit(coordenadas_armadilha)
    kmeans_k16 = KMeans(n_clusters=16, random_state=SEMENTE_ALEATORIA, n_init=10).fit(coordenadas_armadilha)
    coordenadas_armadilha["zona_k8"] = ["zona_k8_" + str(c) for c in kmeans_k8.labels_]
    coordenadas_armadilha["zona_k16"] = ["zona_k16_" + str(c) for c in kmeans_k16.labels_]

    df = df.merge(coordenadas_armadilha[["zona_k8", "zona_k16"]], left_on="id_armadilha", right_index=True, how="left")
    n_sem_zona = df["zona_k8"].isna().sum()
    if n_sem_zona:
        print(f"  aviso: {n_sem_zona} linhas sem coordenada válida (armadilha sem lat/lon), ficam fora das zonas")

    resultados = {}
    for coluna_grupo, nome in [
        ("bairro", "bairro"),
        ("zona_k8", "zona_k8"),
        ("zona_k16", "zona_k16"),
    ]:
        print(f"Rodando protocolo para granularidade: {nome}...")
        resultados[nome] = rodar_protocolo_completo(df, coluna_grupo, semanas_completas, nome)

    # --------------------------------------------------------------
    # Consolidação e gravação dos CSVs de saída
    # --------------------------------------------------------------
    autocorr_final = pd.concat([r["autocorrelacao"] for r in resultados.values()], ignore_index=True)
    ranking_final = pd.concat([r["ranking"] for r in resultados.values()], ignore_index=True)
    split_half_final = pd.DataFrame([r["split_half"] for r in resultados.values()])
    decomposicao_final = pd.DataFrame([r["decomposicao"] for r in resultados.values()])
    cobertura_final = pd.DataFrame([r["cobertura"] for r in resultados.values()])

    autocorr_final.to_csv(os.path.join(PASTA_SAIDA, "teste_b_persistencia_autocorrelacao.csv"), index=False)
    ranking_final.to_csv(os.path.join(PASTA_SAIDA, "teste_b_persistencia_ranking_spearman.csv"), index=False)
    split_half_final.to_csv(os.path.join(PASTA_SAIDA, "teste_b_split_half_confiabilidade.csv"), index=False)
    decomposicao_final.to_csv(os.path.join(PASTA_SAIDA, "teste_b_decomposicao_variancia.csv"), index=False)
    cobertura_final.to_csv(os.path.join(PASTA_SAIDA, "teste_b_cobertura_elegibilidade.csv"), index=False)

    print("\n=== RESUMO ===")
    print(cobertura_final[["granularidade", "n_grupos_totais", "n_grupos_elegiveis"]])
    print()
    print(autocorr_final)
    print()
    print(ranking_final)
    print()
    print(split_half_final[["granularidade", "n_grupo_semana_qualificados", "raw_mediana", "mm4_mediana"]])
    print()
    print(decomposicao_final[["granularidade", "n_semanas_100pct_completas_usadas",
                               "variancia_semana_pct", "variancia_grupo_pct", "variancia_residuo_pct"]])

    tempo_total = time.time() - inicio
    print(f"\nTempo total de execução: {tempo_total:.1f}s")


if __name__ == "__main__":
    main()
