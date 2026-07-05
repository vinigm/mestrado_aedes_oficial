#!/usr/bin/env python3
"""Comparacao controlada com a literatura, nos MESMOS dados de POA / mesmas semanas / mesma metrica.

Como nao temos as previsoes publicadas dos autores, reproduzimos o METODO deles
(so-clima, estilo Oliveira et al. 2025) e comparamos contra o nosso (clima + vetor
de armadilha), ambos vs a realidade.

XGBoost (usado pelo Oliveira) nao esta instalado -> usamos LightGBM (mesmo tipo de
gradient boosting).

Sao dois experimentos:
  PARTE 1 — regressao do volume de casos (R2 por horizonte), so-clima x clima+vetor,
    em walk-forward expansivel.
  PARTE 2 — replica da tarefa do Oliveira: classificacao de "aceleracao de casos"
    (Balanced Accuracy), comparando o protocolo de split aleatorio do artigo com um
    walk-forward honesto.

Entrada:
  - Bases de dados/tabela_modelagem/tabela_final.csv

Saidas (gravadas ao lado deste script):
  - comparacao_casos.png (Parte 1)
  - comparacao_oliveira.png (Parte 2)
"""
import dataclasses
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.metrics import balanced_accuracy_score, r2_score
from sklearn.model_selection import train_test_split

# --------------------------------------------------------------------- config
# Diretorio deste script: as figuras sao gravadas ao lado dele.
DIRETORIO_DO_SCRIPT = Path(__file__).resolve().parent

# Colunas climaticas de base. A ORDEM define a ordem das features (a arvore e
# sensivel a ela) e nao pode ser alterada.
COLUNAS_CLIMA_BASE = [
    "temp_media",
    "precip_total_mm",
    "orvalho_media",
    "umid_media",
    "pressao_media",
]

# Defasagens (lags), em semanas, geradas para cada coluna.
LAGS_SEMANAS = [1, 2, 3, 4]

# Constantes de dominio (evita numeros magicos soltos).
SEMANAS_POR_ANO = 52
JANELA_MEDIA_MOVEL_SEMANAS = 4

# Walk-forward: minimo de semanas de treino antes de comecar a prever (~2 anos)
# e o espacamento entre as semanas de teste em cada parte.
MINIMO_SEMANAS_TREINO = 104
PASSO_WALK_FORWARD_REGRESSAO = 2
PASSO_WALK_FORWARD_CLASSIFICACAO = 1

# Horizontes de previsao da regressao de casos: 1 a 12 semanas a frente.
HORIZONTES_REGRESSAO = range(1, 13)

# Janela (em semanas) usada para definir "aceleracao de casos" na Parte 2:
# casos sobem em relacao a 2 semanas atras (analogo semanal ao "dia vs 15 dias"
# do Oliveira).
JANELA_ACELERACAO_SEMANAS = 2

# Protocolo de split aleatorio da Parte 2 (replica do Oliveira): fracao de teste
# e as sementes cujos resultados sao promediados.
FRACAO_TESTE_SPLIT_ALEATORIO = 0.3
SEMENTES_SPLIT_ALEATORIO = [0, 1, 2, 3, 4]

# Hiperparametros do LightGBM (regressao e classificacao usam os mesmos valores).
PARAMETROS_LGBM_REGRESSAO = {
    "n_estimators": 250,
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_child_samples": 5,
    "verbose": -1,
    "n_jobs": -1,
}
PARAMETROS_LGBM_CLASSIFICACAO = {
    "n_estimators": 250,
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_child_samples": 5,
    "verbose": -1,
    "n_jobs": -1,
}

# --------------------------------------------------------------------- grafico
# Paleta e parametros visuais das figuras.
COR_SO_CLIMA = "#9b9488"      # cinza: modelo so-clima (estilo literatura)
COR_CLIMA_VETOR = "#0e7c7b"   # teal: modelo clima + vetor (nosso)
COR_OLIVEIRA = "#c25a22"      # laranja: linha de referencia do Oliveira
COR_TITULO = "#0f2540"        # azul-tinta: titulos e rotulos de valor
COR_LINHA_GUIA = "#c9c2b4"    # bege: linhas de guia (zero, 0.5)

FIGSIZE_PARTE1 = (8.6, 4.6)
FIGSIZE_PARTE2 = (7.6, 4.6)
LARGURA_BARRA = 0.36

# Balanced Accuracy reportada pelo Oliveira 2025 (linha de referencia da Parte 2).
BALANCED_ACCURACY_OLIVEIRA = 0.6738

# Limites do eixo y do grafico de barras da Parte 2.
LIMITE_Y_PARTE2 = (0.45, 0.8)

# Deslocamento vertical dos rotulos de valor acima das barras.
DESLOCAMENTO_ROTULO_BARRA = 0.006


def encontrar_raiz_do_projeto(marcador_de_diretorio: str = "Raspagem") -> Path:
    """Sobe a partir do diretorio atual e do script ate achar a raiz do projeto.

    A raiz e identificada pela presenca de um subdiretorio marcador (por padrao
    'Raspagem'), o que torna o script executavel de qualquer subpasta.

    Args:
        marcador_de_diretorio: Nome do subdiretorio que identifica a raiz.

    Returns:
        Caminho da raiz do projeto.

    Raises:
        FileNotFoundError: Se nenhum diretorio candidato contiver o marcador.
    """
    diretorios_candidatos = [
        Path.cwd(),
        *Path.cwd().parents,
        *DIRETORIO_DO_SCRIPT.parents,
    ]
    for diretorio_candidato in diretorios_candidatos:
        if (diretorio_candidato / marcador_de_diretorio).is_dir():
            return diretorio_candidato
    raise FileNotFoundError


def media_movel_4_semanas(serie: pd.Series) -> pd.Series:
    """Media movel de 4 semanas de uma serie de um unico bloco (fonte).

    Usada em transform() por grupo, para que a janela nao atravesse o gap entre
    os blocos de dados de fontes diferentes.

    Args:
        serie: Serie temporal de um unico bloco (fonte).

    Returns:
        Serie com a media movel de 4 semanas (NaN nas 3 primeiras posicoes).
    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def montar_lista_de_features_clima() -> list[str]:
    """Monta, na ordem exata, a lista de features do modelo so-clima.

    A ordem e: colunas de base, depois todos os lags (coluna externa, lag interno),
    depois as medias moveis e, por fim, as componentes sazonais seno/cosseno. A
    ordem importa porque a arvore e sensivel a ela.

    Returns:
        Lista ordenada de nomes de colunas de feature do modelo so-clima.
    """
    features_clima = list(COLUNAS_CLIMA_BASE)

    for coluna_base in COLUNAS_CLIMA_BASE:
        for numero_de_semanas in LAGS_SEMANAS:
            features_clima.append(f"{coluna_base}_lag{numero_de_semanas}")

    for coluna_base in COLUNAS_CLIMA_BASE:
        features_clima.append(f"{coluna_base}_mm4")

    features_clima.append("sin")
    features_clima.append("cos")
    return features_clima


def montar_lista_de_features_vetor(features_clima: list[str]) -> list[str]:
    """Monta a lista de features do modelo clima+vetor a partir das de clima.

    Acrescenta, apos todas as features de clima, o vetor da armadilha, seus lags
    e a sua media movel — mantendo a ordem exata.

    Args:
        features_clima: Lista ordenada de features do modelo so-clima.

    Returns:
        Lista ordenada de nomes de colunas de feature do modelo clima+vetor.
    """
    features_vetor = list(features_clima)
    features_vetor.append("vet")

    for numero_de_semanas in LAGS_SEMANAS:
        features_vetor.append(f"vet_lag{numero_de_semanas}")

    features_vetor.append("vet_mm4")
    return features_vetor


def carregar_tabela_final(caminho_tabela_final: Path) -> pd.DataFrame:
    """Le a tabela_final e ordena por fonte e data.

    Args:
        caminho_tabela_final: Caminho do CSV tabela_final.

    Returns:
        DataFrame ordenado por (fonte, data da semana epidemiologica), com o
        indice reiniciado.
    """
    tabela_final = pd.read_csv(
        caminho_tabela_final,
        parse_dates=["data_inicio_semana_epidemi"],
    )
    tabela_final = tabela_final.sort_values(
        ["fonte", "data_inicio_semana_epidemi"]
    ).reset_index(drop=True)
    return tabela_final


def construir_features(tabela_final: pd.DataFrame) -> pd.DataFrame:
    """Cria lags, medias moveis, o vetor e a sazonalidade, tudo por fonte.

    Todas as features temporais sao calculadas POR BLOCO (groupby na fonte), de
    modo que lags e medias moveis nunca atravessem o gap entre os blocos de dados.
    A sazonalidade e derivada da semana epidemiologica.

    Args:
        tabela_final: Tabela semanal ja ordenada por (fonte, data).

    Returns:
        O MESMO DataFrame com as colunas de feature adicionadas.
    """
    dados_com_features = tabela_final
    grupos_por_fonte = dados_com_features.groupby("fonte", group_keys=False)

    for coluna_base in COLUNAS_CLIMA_BASE:
        for numero_de_semanas in LAGS_SEMANAS:
            nome_coluna_lag = f"{coluna_base}_lag{numero_de_semanas}"
            dados_com_features[nome_coluna_lag] = grupos_por_fonte[coluna_base].shift(
                numero_de_semanas
            )
        nome_coluna_media_movel = f"{coluna_base}_mm4"
        dados_com_features[nome_coluna_media_movel] = grupos_por_fonte[
            coluna_base
        ].transform(media_movel_4_semanas)

    dados_com_features["vet"] = dados_com_features["aedes_aegypti_por_armadilha"]
    grupos_por_fonte_com_vetor = dados_com_features.groupby("fonte", group_keys=False)
    for numero_de_semanas in LAGS_SEMANAS:
        nome_coluna_lag_vetor = f"vet_lag{numero_de_semanas}"
        dados_com_features[nome_coluna_lag_vetor] = grupos_por_fonte_com_vetor[
            "vet"
        ].shift(numero_de_semanas)
    dados_com_features["vet_mm4"] = grupos_por_fonte_com_vetor["vet"].transform(
        media_movel_4_semanas
    )

    angulo_sazonal = 2 * np.pi * dados_com_features["semana"] / SEMANAS_POR_ANO
    dados_com_features["sin"] = np.sin(angulo_sazonal)
    dados_com_features["cos"] = np.cos(angulo_sazonal)
    return dados_com_features


def calcular_r2_do_grupo(grupo: pd.DataFrame) -> float:
    """R2 entre valores reais e previstos de um grupo (um horizonte).

    Args:
        grupo: Subconjunto de previsoes de um unico horizonte, com as colunas
            'real' e 'pred'.

    Returns:
        Coeficiente de determinacao R2 do grupo.
    """
    return r2_score(grupo["real"], grupo["pred"])


def walk_forward_regressao(
    dados_com_features: pd.DataFrame,
    features: list[str],
) -> pd.Series:
    """Walk-forward expansivel da regressao de casos, R2 por horizonte.

    Para cada horizonte, o alvo e o volume de casos h semanas a frente (shift por
    fonte). As linhas validas (sem NaN nas features nem no alvo) sao ordenadas por
    data; a partir de MINIMO_SEMANAS_TREINO, treina-se em todo o historico ate a
    semana i e preve-se a semana i, avancando de PASSO_WALK_FORWARD_REGRESSAO em
    PASSO_WALK_FORWARD_REGRESSAO. O R2 e agregado por horizonte.

    Args:
        dados_com_features: Tabela com as features ja construidas.
        features: Colunas de entrada do modelo, na ordem exata.

    Returns:
        Serie de R2 indexada pelo horizonte (h).
    """
    grupos_por_fonte = dados_com_features.groupby("fonte", group_keys=False)
    linhas_resultado = []

    for horizonte in HORIZONTES_REGRESSAO:
        dados_horizonte = dados_com_features.copy()
        dados_horizonte["y"] = grupos_por_fonte["casos_confirmados"].shift(-horizonte)
        dados_validos = (
            dados_horizonte.dropna(subset=features + ["y"])
            .sort_values("data_inicio_semana_epidemi")
            .reset_index(drop=True)
        )

        for indice_corte in range(
            MINIMO_SEMANAS_TREINO, len(dados_validos), PASSO_WALK_FORWARD_REGRESSAO
        ):
            treino = dados_validos.iloc[:indice_corte]
            teste = dados_validos.iloc[indice_corte:indice_corte + 1]

            modelo = LGBMRegressor(**PARAMETROS_LGBM_REGRESSAO)
            modelo.fit(treino[features], treino["y"])
            previsao = modelo.predict(teste[features])[0]

            linhas_resultado.append(
                {
                    "h": horizonte,
                    "real": teste["y"].values[0],
                    "pred": previsao,
                }
            )

    resultado_walk_forward = pd.DataFrame(linhas_resultado)
    return resultado_walk_forward.groupby("h").apply(
        calcular_r2_do_grupo, include_groups=False
    )


def rodar_parte1(dados_com_features: pd.DataFrame) -> pd.DataFrame:
    """Parte 1: regressao de casos, so-clima x clima+vetor, por horizonte.

    Args:
        dados_com_features: Tabela com as features ja construidas.

    Returns:
        DataFrame indexado pelo horizonte, com R2 de cada modelo e o ganho do
        vetor (R2_clima_vetor - R2_so_clima).
    """
    print("PARTE 1: regressão de casos (walk-forward)...")

    features_clima = montar_lista_de_features_clima()
    features_vetor = montar_lista_de_features_vetor(features_clima)

    r2_por_horizonte_clima = walk_forward_regressao(dados_com_features, features_clima)
    r2_por_horizonte_vetor = walk_forward_regressao(dados_com_features, features_vetor)

    resultados_parte1 = pd.DataFrame(
        {
            "R2_so_clima": r2_por_horizonte_clima,
            "R2_clima_vetor": r2_por_horizonte_vetor,
        }
    )
    resultados_parte1["ganho"] = (
        resultados_parte1["R2_clima_vetor"] - resultados_parte1["R2_so_clima"]
    )
    print(resultados_parte1.round(3).to_string())
    return resultados_parte1


def marcar_aceleracao_de_casos(dados_com_features: pd.DataFrame) -> pd.DataFrame:
    """Marca a coluna 'accel': casos sobem vs JANELA_ACELERACAO_SEMANAS atras.

    O alvo e 1 quando a diferenca de casos em relacao a 2 semanas atras (por fonte)
    e positiva, e 0 caso contrario — analogo semanal ao "dia vs 15 dias" do Oliveira.

    Args:
        dados_com_features: Tabela com as features ja construidas.

    Returns:
        O MESMO DataFrame com a coluna 'accel' (0/1) adicionada.
    """
    grupos_por_fonte = dados_com_features.groupby("fonte", group_keys=False)
    diferenca_de_casos = grupos_por_fonte["casos_confirmados"].diff(
        JANELA_ACELERACAO_SEMANAS
    )
    dados_com_features["accel"] = (diferenca_de_casos > 0).astype(int)
    return dados_com_features


def walk_forward_classificacao(
    dados_com_features: pd.DataFrame,
    features: list[str],
) -> tuple[float, int]:
    """Walk-forward honesto da classificacao de aceleracao de casos.

    As linhas validas (sem NaN nas features nem no alvo) sao ordenadas por data; a
    partir de MINIMO_SEMANAS_TREINO, treina-se em todo o historico ate a semana i e
    preve-se a semana i (passo 1). Passos cujo treino tem uma unica classe sao
    pulados. Retorna a Balanced Accuracy sobre todas as previsoes.

    Args:
        dados_com_features: Tabela com as features e a coluna 'accel'.
        features: Colunas de entrada do modelo, na ordem exata.

    Returns:
        Par (balanced_accuracy, numero_de_previsoes).
    """
    dados_validos = (
        dados_com_features.dropna(subset=features + ["accel"])
        .sort_values("data_inicio_semana_epidemi")
        .reset_index(drop=True)
    )
    valores_reais = []
    valores_previstos = []

    for indice_corte in range(
        MINIMO_SEMANAS_TREINO, len(dados_validos), PASSO_WALK_FORWARD_CLASSIFICACAO
    ):
        treino = dados_validos.iloc[:indice_corte]
        teste = dados_validos.iloc[indice_corte:indice_corte + 1]

        if treino["accel"].nunique() < 2:
            continue

        modelo = LGBMClassifier(**PARAMETROS_LGBM_CLASSIFICACAO)
        modelo.fit(treino[features], treino["accel"])
        valores_previstos.append(int(modelo.predict(teste[features])[0]))
        valores_reais.append(int(teste["accel"].values[0]))

    balanced_accuracy = balanced_accuracy_score(valores_reais, valores_previstos)
    return balanced_accuracy, len(valores_reais)


def split_aleatorio(
    dados_com_features: pd.DataFrame,
    features: list[str],
    semente: int = 42,
) -> float:
    """Balanced Accuracy sob o protocolo de split aleatorio do Oliveira.

    Divide as linhas validas em treino/teste de forma aleatoria e estratificada
    pelo alvo, treina o classificador e mede a Balanced Accuracy no teste.

    Args:
        dados_com_features: Tabela com as features e a coluna 'accel'.
        features: Colunas de entrada do modelo, na ordem exata.
        semente: Semente do split aleatorio (reprodutibilidade).

    Returns:
        Balanced Accuracy no conjunto de teste.
    """
    dados_validos = dados_com_features.dropna(subset=features + ["accel"]).copy()
    features_treino, features_teste, alvo_treino, alvo_teste = train_test_split(
        dados_validos[features],
        dados_validos["accel"],
        test_size=FRACAO_TESTE_SPLIT_ALEATORIO,
        random_state=semente,
        stratify=dados_validos["accel"],
    )
    modelo = LGBMClassifier(**PARAMETROS_LGBM_CLASSIFICACAO)
    modelo.fit(features_treino, alvo_treino)
    return balanced_accuracy_score(alvo_teste, modelo.predict(features_teste))


def media_balanced_accuracy_split_aleatorio(
    dados_com_features: pd.DataFrame,
    features: list[str],
) -> float:
    """Media da Balanced Accuracy do split aleatorio sobre varias sementes.

    Args:
        dados_com_features: Tabela com as features e a coluna 'accel'.
        features: Colunas de entrada do modelo, na ordem exata.

    Returns:
        Media das Balanced Accuracy obtidas com cada semente.
    """
    balanced_accuracies = []
    for semente in SEMENTES_SPLIT_ALEATORIO:
        balanced_accuracies.append(split_aleatorio(dados_com_features, features, semente))
    return np.mean(balanced_accuracies)


@dataclasses.dataclass(frozen=True)
class ResultadosParte2:
    """Balanced Accuracies da Parte 2 (replica do Oliveira).

    Attributes:
        ba_split_clima: Split aleatorio, so-clima.
        ba_split_vetor: Split aleatorio, clima+vetor.
        ba_walk_forward_clima: Walk-forward honesto, so-clima.
        ba_walk_forward_vetor: Walk-forward honesto, clima+vetor.
        n_walk_forward: Numero de previsoes do walk-forward.
    """

    ba_split_clima: float
    ba_split_vetor: float
    ba_walk_forward_clima: float
    ba_walk_forward_vetor: float
    n_walk_forward: int


def rodar_parte2(dados_com_features: pd.DataFrame) -> ResultadosParte2:
    """Parte 2: replica da tarefa do Oliveira (aceleracao de casos).

    Compara o protocolo de split aleatorio do artigo com um walk-forward honesto,
    ambos para so-clima e clima+vetor, usando Balanced Accuracy.

    Args:
        dados_com_features: Tabela com as features e a coluna 'accel'.

    Returns:
        ResultadosParte2 com as quatro Balanced Accuracies e o n do walk-forward.
    """
    print("\nPARTE 2: aceleração de casos (réplica Oliveira)...")

    features_clima = montar_lista_de_features_clima()
    features_vetor = montar_lista_de_features_vetor(features_clima)

    ba_walk_forward_clima, n_walk_forward = walk_forward_classificacao(
        dados_com_features, features_clima
    )
    ba_walk_forward_vetor, _ = walk_forward_classificacao(
        dados_com_features, features_vetor
    )
    ba_split_clima = media_balanced_accuracy_split_aleatorio(
        dados_com_features, features_clima
    )
    ba_split_vetor = media_balanced_accuracy_split_aleatorio(
        dados_com_features, features_vetor
    )

    print(
        f"  split aleatório (protocolo Oliveira): só-clima={ba_split_clima:.3f} | "
        f"clima+vetor={ba_split_vetor:.3f}  (Oliveira reportou 0,67)"
    )
    print(
        f"  walk-forward (honesto, n={n_walk_forward}):         "
        f"só-clima={ba_walk_forward_clima:.3f} | clima+vetor={ba_walk_forward_vetor:.3f}"
    )

    return ResultadosParte2(
        ba_split_clima,
        ba_split_vetor,
        ba_walk_forward_clima,
        ba_walk_forward_vetor,
        n_walk_forward,
    )


def configurar_estilo_grafico() -> None:
    """Aplica os parametros globais de estilo do matplotlib usados nas figuras."""
    plt.rcParams.update(
        {
            "font.size": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
        }
    )


def gerar_grafico_parte1(
    resultados_parte1: pd.DataFrame,
    caminho_figura: Path,
) -> None:
    """Gera e salva o grafico de R2 por horizonte da Parte 1.

    Args:
        resultados_parte1: DataFrame indexado pelo horizonte com R2 dos dois modelos.
        caminho_figura: Caminho de saida do PNG.
    """
    figura, eixo = plt.subplots(figsize=FIGSIZE_PARTE1)
    eixo.plot(
        resultados_parte1.index,
        resultados_parte1["R2_so_clima"],
        "s--",
        color=COR_SO_CLIMA,
        lw=2.2,
        ms=6,
        label="só-clima (estilo literatura)",
    )
    eixo.plot(
        resultados_parte1.index,
        resultados_parte1["R2_clima_vetor"],
        "o-",
        color=COR_CLIMA_VETOR,
        lw=2.6,
        ms=7,
        label="clima + vetor (nosso)",
    )
    eixo.axhline(0, color=COR_LINHA_GUIA, lw=1)
    eixo.set_xlabel("horizonte (semanas à frente)")
    eixo.set_ylabel("R² — previsão de casos")
    eixo.set_title(
        "Mesma POA, mesmas semanas: quem prevê melhor os casos?\n"
        "só-clima × clima+vetor · walk-forward",
        fontsize=13,
        fontweight="bold",
        color=COR_TITULO,
        loc="left",
    )
    eixo.set_xticks(list(resultados_parte1.index))
    eixo.legend(frameon=False)
    eixo.grid(alpha=.25)
    figura.tight_layout()
    figura.savefig(caminho_figura, bbox_inches="tight", facecolor="white")


def gerar_grafico_parte2(
    resultados_parte2: ResultadosParte2,
    caminho_figura: Path,
) -> None:
    """Gera e salva o grafico de barras de Balanced Accuracy da Parte 2.

    Args:
        resultados_parte2: Balanced Accuracies dos dois protocolos e modelos.
        caminho_figura: Caminho de saida do PNG.
    """
    figura, eixo = plt.subplots(figsize=FIGSIZE_PARTE2)
    grupos = ["split aleatório\n(protocolo Oliveira)", "walk-forward\n(honesto)"]
    posicoes_grupos = np.arange(2)

    eixo.bar(
        posicoes_grupos - LARGURA_BARRA / 2,
        [resultados_parte2.ba_split_clima, resultados_parte2.ba_walk_forward_clima],
        LARGURA_BARRA,
        color=COR_SO_CLIMA,
        label="só-clima (estilo literatura)",
    )
    eixo.bar(
        posicoes_grupos + LARGURA_BARRA / 2,
        [resultados_parte2.ba_split_vetor, resultados_parte2.ba_walk_forward_vetor],
        LARGURA_BARRA,
        color=COR_CLIMA_VETOR,
        label="clima + vetor (nosso)",
    )
    eixo.axhline(
        BALANCED_ACCURACY_OLIVEIRA,
        color=COR_OLIVEIRA,
        lw=2,
        ls=":",
        label="Oliveira 2025 (0,67)",
    )
    eixo.axhline(0.5, color=COR_LINHA_GUIA, lw=1, ls="--")
    eixo.set_xticks(posicoes_grupos)
    eixo.set_xticklabels(grupos)
    eixo.set_ylim(*LIMITE_Y_PARTE2)
    eixo.set_ylabel("Balanced Accuracy — aceleração de casos")
    eixo.set_title(
        "Réplica da tarefa do Oliveira (POA)\naceleração de casos · LightGBM",
        fontsize=13,
        fontweight="bold",
        color=COR_TITULO,
        loc="left",
    )
    eixo.legend(frameon=False, fontsize=10.5)
    eixo.grid(axis="y", alpha=.25)

    posicoes_rotulos = [
        posicoes_grupos[0] - LARGURA_BARRA / 2,
        posicoes_grupos[0] + LARGURA_BARRA / 2,
        posicoes_grupos[1] - LARGURA_BARRA / 2,
        posicoes_grupos[1] + LARGURA_BARRA / 2,
    ]
    valores_rotulos = [
        resultados_parte2.ba_split_clima,
        resultados_parte2.ba_split_vetor,
        resultados_parte2.ba_walk_forward_clima,
        resultados_parte2.ba_walk_forward_vetor,
    ]
    for posicao_x, valor in zip(posicoes_rotulos, valores_rotulos):
        eixo.text(
            posicao_x,
            valor + DESLOCAMENTO_ROTULO_BARRA,
            f"{valor:.2f}",
            ha="center",
            fontsize=10,
            fontweight="bold",
            color=COR_TITULO,
        )
    figura.tight_layout()
    figura.savefig(caminho_figura, bbox_inches="tight", facecolor="white")


def main() -> None:
    """Orquestra as duas partes: features, regressao, classificacao e figuras."""
    raiz_do_projeto = encontrar_raiz_do_projeto()
    caminho_tabela_final = (
        raiz_do_projeto / "Bases de dados" / "tabela_modelagem" / "tabela_final.csv"
    )

    tabela_final = carregar_tabela_final(caminho_tabela_final)
    dados_com_features = construir_features(tabela_final)

    resultados_parte1 = rodar_parte1(dados_com_features)

    dados_com_features = marcar_aceleracao_de_casos(dados_com_features)
    resultados_parte2 = rodar_parte2(dados_com_features)

    configurar_estilo_grafico()
    gerar_grafico_parte1(resultados_parte1, DIRETORIO_DO_SCRIPT / "comparacao_casos.png")
    gerar_grafico_parte2(
        resultados_parte2, DIRETORIO_DO_SCRIPT / "comparacao_oliveira.png"
    )
    print("\nsalvos: comparacao_casos.png, comparacao_oliveira.png\nDONE")


if __name__ == "__main__":
    main()
