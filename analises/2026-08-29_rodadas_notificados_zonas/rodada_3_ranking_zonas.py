"""

Rodada 3 de 29/08/2026: o modelo acerta a ORDEM das zonas de maior risco
entomologico com antecedencia util para a vigilancia?

Pre-declarado em PRE_DECLARACAO.md (Rodada 3) ANTES de rodar. A metrica
primaria e o Spearman entre o ranking previsto e o ranking real das zonas, em
cada semana - e nao o R2. O motivo e operacional: quem decide para onde mandar
a equipe de campo precisa da ORDEM certa, nao do valor absoluto da densidade.

Baselines obrigatorios (a regra de decisao pre-declarada exige vencer a
persistencia; bater so a climatologia nao basta, porque persistencia e o que a
vigilancia ja faz de graca):
  - persistencia: a ordem das zonas HOJE vale para daqui a h semanas;
  - climatologia sazonal: a ordem media historica daquela epoca do ano.

O script e AUTOCONTIDO e SO LE o parquet certificado - nao importa nada do
pacote modelagem_aedes e nao escreve em nenhum caminho do pacote.

Uso:  python rodada_3_ranking_zonas.py

"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy.stats import spearmanr
from sklearn.cluster import KMeans

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_SAIDAS = PASTA_ANALISE / "saidas"
PARQUET_ARMADILHAS = (
    PASTA_ANALISE.parents[1]
    / "modelagem_aedes"
    / "dados"
    / "entradas"
    / "arquivos_secretaria_saude_poa"
    / "secretaria_poa_armadilhas.parquet"
)

# Janela e criterios de elegibilidade IDENTICOS ao teste B de 16/08/2026, para
# que os dois resultados sejam comparaveis lado a lado.
DATA_INICIO_JANELA = "2019-01-01"
LIMIAR_ARMADILHAS_ELEGIBILIDADE = 10
FRACAO_MINIMA_SEMANAS_COBERTAS = 0.5
SEMENTE_ALEATORIA = 42
VALORES_DE_K = (8, 16)

# Horizontes em semanas. 1 e 2 sao o giro operacional de uma equipe de campo;
# 4 e 8 testam ate onde a antecedencia se sustenta.
HORIZONTES = (1, 2, 4, 8)

# Semanas de historico exigidas antes de comecar a testar. 104 = 2 anos, o
# mesmo minimo que o resto do projeto usa (config/settings.MINIMO_SEMANAS_TREINO).
MINIMO_SEMANAS_TREINO = 104

# De quantas em quantas semanas testar. 1 = testa toda semana.
PASSO_TESTE = 1

# Janela da media movel que suaviza o alvo, igual ao teste B.
JANELA_SUAVIZACAO = 4
MINIMO_SEMANAS_NA_JANELA = 2

SEMANAS_POR_ANO = 52

PARAMETROS_LIGHTGBM = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "verbose": -1,
    "n_jobs": 1,
    "random_state": SEMENTE_ALEATORIA,
}

COLUNAS_LAG = ["dens_lag1", "dens_lag2", "dens_lag3", "dens_lag4"]
COLUNAS_MODELO = COLUNAS_LAG + [
    "dens_mm4",
    "dens_lag8",
    "dens_lag52",
    "sem_sin",
    "sem_cos",
    "alvo_sin",
    "alvo_cos",
    "codigo_zona",
]


def carregar_inspecoes_com_zona(numero_de_zonas: int) -> pd.DataFrame:
    """

    Abre o parquet certificado, fica so com as inspecoes realizadas de 2019 em
    diante e marca a zona sintetica de cada armadilha.

    A zona vem de um K-Means nas coordenadas MEDIAS de cada armadilha - a mesma
    construcao do teste B de 16/08/2026, com a mesma semente, pra que as duas
    analises falem das mesmas zonas. O filtro por inspecao realizada restringe
    automaticamente a serie a 2019+, porque a coluna 'inspecao_realizada' e
    nula em 100% das linhas anteriores (pendencia de dicionario com a
    Secretaria).

    Args:
        numero_de_zonas: Quantos grupos o K-Means deve formar (8 ou 16).

    Returns:
        Uma linha por inspecao, com a coluna 'zona'. Linhas de armadilha sem
        coordenada ficam sem zona (NaN) e sao descartadas depois.

    """
    colunas_necessarias = [
        "ano", "data_inicio_semana", "id_armadilha", "bairro",
        "latitude", "longitude", "aegypti_femea", "inspecao_realizada",
    ]
    inspecoes = pd.read_parquet(PARQUET_ARMADILHAS, columns=colunas_necessarias)
    inspecoes = inspecoes.loc[inspecoes["inspecao_realizada"] == True].copy()  # noqa: E712
    inspecoes = inspecoes.loc[inspecoes["data_inicio_semana"] >= DATA_INICIO_JANELA]

    coordenadas_por_armadilha = (
        inspecoes.groupby("id_armadilha")[["latitude", "longitude"]].mean().dropna()
    )
    agrupador = KMeans(
        n_clusters=numero_de_zonas, random_state=SEMENTE_ALEATORIA, n_init=10
    ).fit(coordenadas_por_armadilha)
    coordenadas_por_armadilha["zona"] = [
        f"zona_k{numero_de_zonas}_{rotulo}" for rotulo in agrupador.labels_
    ]

    inspecoes = inspecoes.merge(
        coordenadas_por_armadilha[["zona"]],
        left_on="id_armadilha",
        right_index=True,
        how="left",
    )
    return inspecoes.dropna(subset=["zona"])


def montar_painel_zona_semana(inspecoes: pd.DataFrame) -> pd.DataFrame:
    """

    Agrega as inspecoes em uma linha por zona e semana, com a densidade.

    Densidade = femeas de Aedes aegypti divididas pelo numero de armadilhas
    distintas efetivamente inspecionadas naquela zona naquela semana.

    """
    painel = (
        inspecoes.groupby(["zona", "data_inicio_semana"])
        .agg(
            n_armadilhas=("id_armadilha", "nunique"),
            femeas=("aegypti_femea", "sum"),
        )
        .reset_index()
    )
    painel["densidade"] = painel["femeas"] / painel["n_armadilhas"]
    return painel


def selecionar_zonas_elegiveis(
    painel: pd.DataFrame,
    semanas_da_grade: list,
) -> list[str]:
    """

    Fica so com as zonas que tem cobertura suficiente para serem analisadas.

    Uma zona e elegivel quando tem pelo menos
    LIMIAR_ARMADILHAS_ELEGIBILIDADE armadilhas inspecionadas em pelo menos
    FRACAO_MINIMA_SEMANAS_COBERTAS das semanas da grade. O denominador e a
    grade COMPLETA de semanas, e nao so as semanas em que a zona aparece -
    senao uma zona que so aparece em 10 semanas, todas bem cobertas, passaria
    com 100% de cobertura. Mesmo criterio do teste B.

    """
    zonas = painel["zona"].unique()
    indice_completo = pd.MultiIndex.from_product(
        [zonas, semanas_da_grade], names=["zona", "data_inicio_semana"]
    )
    painel_completo = (
        painel.set_index(["zona", "data_inicio_semana"]).reindex(indice_completo)
    )
    painel_completo["n_armadilhas"] = painel_completo["n_armadilhas"].fillna(0)

    tem_cobertura = painel_completo["n_armadilhas"] >= LIMIAR_ARMADILHAS_ELEGIBILIDADE
    fracao_coberta = tem_cobertura.groupby(level="zona").mean()

    elegiveis = fracao_coberta[fracao_coberta >= FRACAO_MINIMA_SEMANAS_COBERTAS]
    return sorted(elegiveis.index.tolist())


def construir_serie_com_features(
    painel: pd.DataFrame,
    semanas_da_grade: list,
    zonas_elegiveis: list[str],
) -> pd.DataFrame:
    """

    Monta a serie zona x semana na grade completa e cria as colunas do modelo.

    O alvo e a densidade SUAVIZADA por media movel de 4 semanas (mm4), como no
    teste B: a densidade crua de uma zona-semana carrega muito ruido de
    amostragem, e suavizar e o que torna o sinal espacial legivel.

    Semana sem inspecao numa zona fica NaN e propaga NaN pelos lags - nao se
    inventa zero.

    """
    indice_completo = pd.MultiIndex.from_product(
        [zonas_elegiveis, semanas_da_grade], names=["zona", "data_inicio_semana"]
    )
    serie = (
        painel.set_index(["zona", "data_inicio_semana"])
        .reindex(indice_completo)
        .reset_index()
        .sort_values(["zona", "data_inicio_semana"])
    )

    agrupado_por_zona = serie.groupby("zona", group_keys=False)

    serie["dens"] = agrupado_por_zona["densidade"].transform(
        lambda valores: valores.rolling(
            JANELA_SUAVIZACAO, min_periods=MINIMO_SEMANAS_NA_JANELA
        ).mean()
    )

    for numero_de_semanas in (1, 2, 3, 4, 8, 52):
        serie[f"dens_lag{numero_de_semanas}"] = agrupado_por_zona["dens"].shift(
            numero_de_semanas
        )

    serie["dens_mm4"] = agrupado_por_zona["dens"].transform(
        lambda valores: valores.rolling(JANELA_SUAVIZACAO).mean()
    )

    semana_do_ano = pd.to_datetime(serie["data_inicio_semana"]).dt.isocalendar().week
    angulo_sazonal = 2 * np.pi * semana_do_ano.astype(float) / SEMANAS_POR_ANO
    serie["sem_sin"] = np.sin(angulo_sazonal)
    serie["sem_cos"] = np.cos(angulo_sazonal)
    serie["semana_do_ano"] = semana_do_ano.astype(int)

    # A zona entra no modelo como numero: ela carrega o nivel tipico daquela
    # regiao da cidade, que e justamente o que separa uma zona da outra no
    # ranking. Sem isso o modelo so enxergaria a sazonalidade comum.
    codigos_de_zona = {nome: codigo for codigo, nome in enumerate(zonas_elegiveis)}
    serie["codigo_zona"] = serie["zona"].map(codigos_de_zona)

    return serie


def calcular_spearman(valores_previstos: np.ndarray, valores_reais: np.ndarray) -> float:
    """

    Correlacao de Spearman entre a ordem prevista e a ordem real das zonas.

    Devolve NaN quando ha menos de 3 zonas comparaveis ou quando um dos lados
    e constante (nesses casos a correlacao nao esta definida).

    """
    if valores_previstos.size < 3:
        return float("nan")
    if np.unique(valores_previstos).size < 2 or np.unique(valores_reais).size < 2:
        return float("nan")

    correlacao = spearmanr(valores_previstos, valores_reais).statistic
    return float(correlacao)


def calcular_climatologia_por_zona(treino: pd.DataFrame, semana_do_ano_alvo: int) -> pd.Series:
    """

    Nivel medio historico de cada zona naquela epoca do ano.

    Usa uma janela circular de +-1 semana em volta da semana-alvo (a semana 52
    e vizinha da 1). Se nenhuma zona tiver historico nessa janela, cai para a
    media geral de cada zona - fallback declarado, nao silencioso.

    """
    distancia_bruta = (treino["semana_do_ano"] - semana_do_ano_alvo).abs()
    distancia_circular = np.minimum(distancia_bruta, SEMANAS_POR_ANO - distancia_bruta)
    mesma_epoca = treino.loc[distancia_circular <= 1]

    if mesma_epoca.empty:
        return treino.groupby("zona")["dens"].mean()

    media_na_epoca = mesma_epoca.groupby("zona")["dens"].mean()
    if media_na_epoca.notna().sum() < 3:
        return treino.groupby("zona")["dens"].mean()

    return media_na_epoca


def executar_walk_forward_ranking(
    serie: pd.DataFrame,
    horizonte: int,
) -> pd.DataFrame:
    """

    Treina no passado e preve o ranking das zonas h semanas a frente, semana a
    semana.

    Em cada semana de origem, o modelo treina com TODAS as zonas-semana ate
    aquela data e preve a densidade suavizada de cada zona em t+h. As tres
    abordagens sao avaliadas exatamente nas mesmas semanas e nas mesmas zonas:
    o modelo, a persistencia (a ordem de hoje) e a climatologia (a ordem media
    daquela epoca do ano).

    Args:
        serie: A serie zona x semana com as colunas do modelo prontas.
        horizonte: Quantas semanas a frente prever.

    Returns:
        Uma linha por semana de origem testada, com o Spearman de cada
        abordagem e quantas zonas entraram na comparacao.

    """
    serie_ordenada = serie.sort_values(["data_inicio_semana", "zona"]).copy()

    # O alvo de cada linha e a densidade suavizada da MESMA zona, h semanas a frente.
    serie_ordenada["alvo"] = serie_ordenada.groupby("zona", group_keys=False)["dens"].shift(
        -horizonte
    )
    semana_do_ano_alvo = serie_ordenada.groupby("zona", group_keys=False)[
        "semana_do_ano"
    ].shift(-horizonte)
    angulo_alvo = 2 * np.pi * semana_do_ano_alvo / SEMANAS_POR_ANO
    serie_ordenada["alvo_sin"] = np.sin(angulo_alvo)
    serie_ordenada["alvo_cos"] = np.cos(angulo_alvo)
    serie_ordenada["semana_do_ano_alvo"] = semana_do_ano_alvo

    colunas_exigidas = COLUNAS_MODELO + ["alvo", "dens", "semana_do_ano_alvo"]
    dados_validos = serie_ordenada.dropna(subset=colunas_exigidas)

    semanas_testaveis = sorted(dados_validos["data_inicio_semana"].unique())

    linhas_resultado = []
    for indice_semana in range(MINIMO_SEMANAS_TREINO, len(semanas_testaveis), PASSO_TESTE):
        semana_de_origem = semanas_testaveis[indice_semana]

        treino = dados_validos.loc[dados_validos["data_inicio_semana"] < semana_de_origem]
        teste = dados_validos.loc[dados_validos["data_inicio_semana"] == semana_de_origem]

        if len(teste) < 3 or treino.empty:
            continue

        modelo = LGBMRegressor(**PARAMETROS_LIGHTGBM)
        modelo.fit(treino[COLUNAS_MODELO], treino["alvo"])
        previsao_do_modelo = modelo.predict(teste[COLUNAS_MODELO])

        # Persistencia: a ordem de hoje continua valendo daqui a h semanas.
        previsao_persistencia = teste["dens"].to_numpy()

        # Climatologia: o nivel medio historico de cada zona naquela epoca do ano.
        semana_alvo = int(teste["semana_do_ano_alvo"].iloc[0])
        climatologia_por_zona = calcular_climatologia_por_zona(treino, semana_alvo)
        previsao_climatologia = teste["zona"].map(climatologia_por_zona).to_numpy(dtype=float)

        valores_reais = teste["alvo"].to_numpy()

        linhas_resultado.append(
            {
                "h": horizonte,
                "data_origem": semana_de_origem,
                "n_zonas": len(teste),
                "spearman_modelo": calcular_spearman(previsao_do_modelo, valores_reais),
                "spearman_persistencia": calcular_spearman(previsao_persistencia, valores_reais),
                "spearman_climatologia": calcular_spearman(previsao_climatologia, valores_reais),
            }
        )

    return pd.DataFrame(linhas_resultado)


def resumir_por_horizonte(detalhado: pd.DataFrame, numero_de_zonas: int) -> pd.DataFrame:
    """

    Resume o Spearman semana a semana em uma linha por horizonte.

    Reporta mediana e media das tres abordagens, a fracao de semanas em que o
    modelo supera a persistencia e o veredito da regra pre-declarada (o modelo
    so e util se vencer a persistencia).

    """
    linhas_resumo = []
    for horizonte, grupo in detalhado.groupby("h"):
        comparaveis = grupo.dropna(subset=["spearman_modelo", "spearman_persistencia"])

        mediana_modelo = grupo["spearman_modelo"].median()
        mediana_persistencia = grupo["spearman_persistencia"].median()

        linhas_resumo.append(
            {
                "k": numero_de_zonas,
                "h": horizonte,
                "semanas_testadas": len(grupo),
                "spearman_modelo_mediana": mediana_modelo,
                "spearman_persistencia_mediana": mediana_persistencia,
                "spearman_climatologia_mediana": grupo["spearman_climatologia"].median(),
                "spearman_modelo_media": grupo["spearman_modelo"].mean(),
                "spearman_persistencia_media": grupo["spearman_persistencia"].mean(),
                "spearman_climatologia_media": grupo["spearman_climatologia"].mean(),
                "fracao_semanas_modelo_vence_persistencia": (
                    comparaveis["spearman_modelo"] > comparaveis["spearman_persistencia"]
                ).mean(),
                "modelo_vence_persistencia": bool(mediana_modelo > mediana_persistencia),
            }
        )

    return pd.DataFrame(linhas_resumo)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    detalhados = []
    resumos = []
    coberturas = []

    for numero_de_zonas in VALORES_DE_K:
        print(f"\n{'=' * 70}", flush=True)
        print(f"ZONAS SINTETICAS k={numero_de_zonas}", flush=True)
        print("=" * 70, flush=True)

        inspecoes = carregar_inspecoes_com_zona(numero_de_zonas)
        semanas_da_grade = sorted(inspecoes["data_inicio_semana"].unique())
        print(f"  {len(inspecoes):,} inspecoes | {len(semanas_da_grade)} semanas "
              f"({semanas_da_grade[0]} a {semanas_da_grade[-1]})", flush=True)

        painel = montar_painel_zona_semana(inspecoes)
        zonas_elegiveis = selecionar_zonas_elegiveis(painel, semanas_da_grade)
        print(f"  zonas elegiveis: {len(zonas_elegiveis)} de {numero_de_zonas}", flush=True)

        coberturas.append(
            {
                "k": numero_de_zonas,
                "zonas_totais": numero_de_zonas,
                "zonas_elegiveis": len(zonas_elegiveis),
                "semanas": len(semanas_da_grade),
                "inspecoes": len(inspecoes),
            }
        )

        serie = construir_serie_com_features(painel, semanas_da_grade, zonas_elegiveis)

        for horizonte in HORIZONTES:
            print(f"  h={horizonte}: rodando walk-forward...", end=" ", flush=True)
            detalhado = executar_walk_forward_ranking(serie, horizonte)
            detalhado.insert(0, "k", numero_de_zonas)
            detalhados.append(detalhado)

            mediana_modelo = detalhado["spearman_modelo"].median()
            mediana_persistencia = detalhado["spearman_persistencia"].median()
            print(
                f"{len(detalhado)} semanas | modelo={mediana_modelo:.3f} "
                f"persistencia={mediana_persistencia:.3f}",
                flush=True,
            )

        resumos.append(resumir_por_horizonte(pd.concat(
            [d for d in detalhados if d["k"].iloc[0] == numero_de_zonas], ignore_index=True
        ), numero_de_zonas))

    detalhado_final = pd.concat(detalhados, ignore_index=True)
    resumo_final = pd.concat(resumos, ignore_index=True)
    cobertura_final = pd.DataFrame(coberturas)

    detalhado_final.to_csv(PASTA_SAIDAS / "rodada_3_ranking_por_semana.csv", index=False)
    resumo_final.to_csv(PASTA_SAIDAS / "rodada_3_ranking_resumo.csv", index=False)
    cobertura_final.to_csv(PASTA_SAIDAS / "rodada_3_cobertura_zonas.csv", index=False)

    print(f"\n{'=' * 70}", flush=True)
    print("RESUMO — Spearman mediano do ranking das zonas", flush=True)
    print("=" * 70, flush=True)
    colunas_exibidas = [
        "k", "h", "semanas_testadas",
        "spearman_modelo_mediana", "spearman_persistencia_mediana",
        "spearman_climatologia_mediana",
        "fracao_semanas_modelo_vence_persistencia", "modelo_vence_persistencia",
    ]
    print(resumo_final[colunas_exibidas].round(3).to_string(index=False), flush=True)

    horizontes_vencidos = int(resumo_final["modelo_vence_persistencia"].sum())
    print(f"\nVEREDITO (regra pre-declarada): o modelo supera a persistencia em "
          f"{horizontes_vencidos} de {len(resumo_final)} combinacoes k x h.", flush=True)
    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
