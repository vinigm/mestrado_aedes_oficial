"""

TESTE A — Equivalência clima x vetor na previsão de casos (nível cidade).

Pergunta de tese: um modelo que usa SÓ clima e um modelo que usa SÓ dados do
vetor (armadilhas) são estatisticamente EQUIVALENTES para prever casos
confirmados de dengue em Porto Alegre, semana a semana?

Este script é AUTOCONTIDO e SÓ LÊ dados existentes do projeto (nenhum arquivo
do projeto é alterado). A engenharia de features (sazonalidade seno/cosseno,
defasagens e médias móveis) replica exatamente as fórmulas usadas em
modelagem_aedes/dominio/features.py; os hiperparâmetros do LightGBM e o
janela de walk-forward (mínimo de 104 semanas, expansível) replicam
modelagem_aedes/config/experimentos/cidade_regressao.py e
modelagem_aedes/motor/walk_forward_regressao.py. O script não importa esses
módulos (para não depender do pacote nem do diretório de execução do
projeto) — ele recalcula as mesmas fórmulas de forma independente.

Protocolo (duas versões, pré-declaradas):

    (i) "puro": SO_CLIMA_PURO x SO_VETOR_PURO — sem nenhuma defasagem de
        casos, para isolar a fonte de informação (clima vs vetor) da
        autocorrelação da própria série de casos.

    (ii) "com_ar": SO_CLIMA_AR x SO_VETOR_AR — os dois conjuntos recebem os
        mesmos componentes autorregressivos de casos (casos_lag1..4,
        casos_mm4); esta é a versão operacionalmente realista (o que se
        rodaria em produção).

Para cada versão e horizonte, o script:
    1. Roda o walk-forward (idêntico ao projeto) para os dois conjuntos e
       salva as previsões semana a semana em CSV.
    2. Alinha as previsões pelas mesmas semanas de teste (interseção de
       datas entre clima e vetor) e calcula, sobre os erros pareados:
       MAE de cada conjunto, MAE da persistência (mesma janela, referência),
       teste de Diebold-Mariano com correção HLN, teste de equivalência
       TOST (margens de 5%, 10% e 15% do MAE do SO_CLIMA) e IC 95% de
       ΔMAE por bootstrap em blocos de 8 semanas (2000 reamostras).

Saídas (todas nesta mesma pasta):
    previsoes_{CONJUNTO}_h{H}.csv       — previsões semana a semana.
    previsoes_persistencia_h{H}.csv     — previsão ingênua (repete o valor
        atual), usada só como referência.
    resultados_testes_equivalencia.csv  — uma linha por versão x horizonte,
        com todos os números-âncora (MAE, ΔMAE, IC, DM-HLN, TOST).

"""

import dataclasses
import time
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy import stats


# --- Caminhos (leitura em outra pasta do projeto; escrita só nesta pasta) ---

CAMINHO_TABELA_FINAL = Path(
    "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/"
    "Meu Drive/Mestrado/Pesquisa/Meu_Projeto/modelagem_aedes/dados/entradas/"
    "tabela_modelagem/tabela_final.csv"
)
PASTA_SAIDA = Path(__file__).resolve().parent


# --- Constantes do protocolo (idênticas ao projeto, ver docstring acima) ---

SEMANAS_POR_ANO = 52
LAGS_SEMANAS = (1, 2, 3, 4)
JANELA_MEDIA_MOVEL_SEMANAS = 4
MINIMO_SEMANAS_TREINO = 104
PASSO_RETREINO_SEMANAS = 1
HORIZONTES = (1, 4, 8, 12)

PARAMETROS_LIGHTGBM = {
    "n_estimators": 250,
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_child_samples": 5,
    "verbose": -1,
    # n_jobs=1: com so ~100-420 linhas de treino por rodada, o overhead de
    # criar um pool de threads a cada re-treino (n_jobs=-1) multiplicou o
    # tempo por ~12x num teste de bancada (0,03s -> 0,36s por fit). Rodar em
    # 1 thread e' puramente uma escolha de desempenho: nao muda a arvore
    # construida (sem bagging/feature_fraction, o LightGBM e' determinístico
    # em 1 thread) nem o resultado do modelo, so' o tempo de parede.
    "n_jobs": 1,
}

TAMANHO_BLOCO_BOOTSTRAP = 8
NUMERO_REAMOSTRAS_BOOTSTRAP = 2000
SEMENTE_BOOTSTRAP = 20260816
MARGENS_TOST_FRACAO_MAE_CLIMA = (0.05, 0.10, 0.15)
NIVEL_SIGNIFICANCIA = 0.05

PREFIXOS_COLUNAS_CLIMA = (
    "temp", "precip", "umid", "orvalho", "pressao", "radiacao", "vento", "dias_de_chuva",
)
COLUNA_VETOR = "aedes_aegypti_por_armadilha"
COLUNA_CASOS = "casos"


# --- Estruturas de configuração ---


@dataclasses.dataclass(frozen=True)
class ConjuntoDeFeatures:
    """Um dos quatro conjuntos de entrada comparados no Teste A.

    Attributes:
        nome: Identificador curto usado nos nomes dos arquivos de saída.
        versao: 'puro' (sem defasagem de casos) ou 'com_ar' (com defasagem
            de casos, igual nos dois lados da comparação).
        colunas_features: Nomes das colunas usadas como entrada do modelo
            (a sazonalidade do alvo, alvo_sin/alvo_cos, é adicionada à parte
            dentro do walk-forward, igual ao motor do projeto).
    """

    nome: str
    versao: str
    colunas_features: tuple[str, ...]


# --- Carregamento e engenharia de features (leitura; nenhuma escrita fora desta pasta) ---


def carregar_tabela_final(caminho_arquivo: Path) -> pd.DataFrame:
    """Lê a tabela_final.csv do projeto e a deixa em ordem cronológica.

    Args:
        caminho_arquivo: Caminho do CSV original do projeto (só leitura).

    Returns:
        Cópia da tabela com a coluna de data renomeada para 'data' e a
        coluna de casos confirmados renomeada para 'casos' (mesmo nome que
        o pipeline do projeto usa), ordenada por data.

    Raises:
        FileNotFoundError: Se o arquivo não existir no caminho informado.
    """
    if not caminho_arquivo.exists():
        raise FileNotFoundError(f"Tabela final não encontrada em: {caminho_arquivo}")

    tabela = pd.read_csv(caminho_arquivo, parse_dates=["data_inicio_semana_epidemi"])
    tabela = tabela.rename(
        columns={
            "data_inicio_semana_epidemi": "data",
            "casos_confirmados": COLUNA_CASOS,
        }
    )
    tabela_ordenada = tabela.sort_values("data").reset_index(drop=True)
    return tabela_ordenada


def calcular_media_movel(serie: pd.Series, janela_semanas: int) -> pd.Series:
    """Média móvel das últimas N semanas (mesma fórmula do projeto)."""
    return serie.rolling(janela_semanas).mean()


def construir_features_temporais(dados: pd.DataFrame) -> pd.DataFrame:
    """Cria sazonalidade, defasagens de casos e defasagens do vetor.

    Replica as fórmulas de modelagem_aedes/dominio/features.py, restritas
    às colunas que o protocolo do Teste A usa: sem_sin/sem_cos (época do
    ano), casos_lag1..4 e casos_mm4 (autorregressivo de casos), e
    aedes_aegypti_por_armadilha_lag1..4 e vetor_mm4 (autorregressivo do
    vetor). As colunas de clima entram no modelo pelo valor contemporâneo
    (sem defasagem) — ver README desta pasta, seção "Definição dos
    conjuntos de features".

    Args:
        dados: Tabela semanal, em ordem cronológica, com as colunas
            'semana', 'casos' e a coluna do vetor.

    Returns:
        Cópia da tabela com as colunas novas adicionadas.
    """
    dados_com_features = dados.copy()

    angulo_sazonal = 2 * np.pi * dados_com_features["semana"] / SEMANAS_POR_ANO
    dados_com_features["sem_sin"] = np.sin(angulo_sazonal)
    dados_com_features["sem_cos"] = np.cos(angulo_sazonal)

    for numero_de_semanas in LAGS_SEMANAS:
        dados_com_features[f"casos_lag{numero_de_semanas}"] = dados_com_features[
            COLUNA_CASOS
        ].shift(numero_de_semanas)
        dados_com_features[f"{COLUNA_VETOR}_lag{numero_de_semanas}"] = dados_com_features[
            COLUNA_VETOR
        ].shift(numero_de_semanas)

    dados_com_features["casos_mm4"] = calcular_media_movel(
        dados_com_features[COLUNA_CASOS], JANELA_MEDIA_MOVEL_SEMANAS
    )
    dados_com_features["vetor_mm4"] = calcular_media_movel(
        dados_com_features[COLUNA_VETOR], JANELA_MEDIA_MOVEL_SEMANAS
    )
    return dados_com_features


def construir_alvo_horizonte(dados: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Desloca 'casos' para frente e marca a sazonalidade da semana-alvo.

    Réplica de dominio/features.py:construir_alvo_horizonte. Cria 'y_h'
    (o valor a prever, horizonte semanas à frente) e 'alvo_sin'/'alvo_cos'
    (a época do ano dessa semana futura) — estas duas últimas entram como
    feature em TODOS os conjuntos, igual ao motor de walk-forward do
    projeto (motor/walk_forward_regressao.py).

    Args:
        dados: Tabela semanal, em ordem cronológica.
        horizonte: Quantas semanas à frente se quer prever.

    Returns:
        Cópia da tabela com as colunas y_h, alvo_sin e alvo_cos.
    """
    resultado = dados.copy()
    resultado["y_h"] = dados[COLUNA_CASOS].shift(-horizonte)
    semana_alvo = dados["semana"].shift(-horizonte)
    angulo_sazonal_alvo = 2 * np.pi * semana_alvo / SEMANAS_POR_ANO
    resultado["alvo_sin"] = np.sin(angulo_sazonal_alvo)
    resultado["alvo_cos"] = np.cos(angulo_sazonal_alvo)
    return resultado


def definir_conjuntos_de_features(dados_com_features: pd.DataFrame) -> list[ConjuntoDeFeatures]:
    """Monta os quatro conjuntos de features do protocolo pré-declarado.

    Args:
        dados_com_features: Tabela já passada por construir_features_temporais
            (usada só para checar quais colunas de clima existem).

    Returns:
        Lista com os quatro ConjuntoDeFeatures: SO_CLIMA_PURO, SO_VETOR_PURO,
        SO_CLIMA_AR e SO_VETOR_AR.
    """
    colunas_clima = [
        nome_coluna
        for nome_coluna in dados_com_features.columns
        if nome_coluna.startswith(PREFIXOS_COLUNAS_CLIMA)
    ]
    colunas_vetor = [COLUNA_VETOR] + [
        f"{COLUNA_VETOR}_lag{n}" for n in LAGS_SEMANAS
    ] + ["vetor_mm4"]
    colunas_ar_casos = [f"casos_lag{n}" for n in LAGS_SEMANAS] + ["casos_mm4"]
    colunas_sazonalidade_entrada = ["sem_sin", "sem_cos"]

    so_clima_puro = tuple(colunas_clima + colunas_sazonalidade_entrada)
    so_vetor_puro = tuple(colunas_vetor + colunas_sazonalidade_entrada)
    so_clima_ar = tuple(colunas_clima + colunas_sazonalidade_entrada + colunas_ar_casos)
    so_vetor_ar = tuple(colunas_vetor + colunas_sazonalidade_entrada + colunas_ar_casos)

    return [
        ConjuntoDeFeatures(nome="SO_CLIMA_PURO", versao="puro", colunas_features=so_clima_puro),
        ConjuntoDeFeatures(nome="SO_VETOR_PURO", versao="puro", colunas_features=so_vetor_puro),
        ConjuntoDeFeatures(nome="SO_CLIMA_AR", versao="com_ar", colunas_features=so_clima_ar),
        ConjuntoDeFeatures(nome="SO_VETOR_AR", versao="com_ar", colunas_features=so_vetor_ar),
    ]


# --- Walk-forward (idêntico a motor/walk_forward_regressao.py do projeto) ---


def executar_walk_forward(
    dados_com_features: pd.DataFrame,
    colunas_features: tuple[str, ...],
    horizonte: int,
) -> pd.DataFrame:
    """Treina no passado e prevê a próxima semana, repetidamente.

    Janela expansível: a cada passo, o modelo treina com tudo que já
    aconteceu (mínimo de MINIMO_SEMANAS_TREINO semanas) e prevê só a
    semana seguinte, sem pular semanas (PASSO_RETREINO_SEMANAS=1). Réplica
    de motor/walk_forward_regressao.py:executar_walk_forward_regressao.

    Args:
        dados_com_features: Tabela com as features e o alvo já calculados
            (construir_features_temporais + construir_alvo_horizonte já
            aplicados para este horizonte).
        colunas_features: Colunas de entrada deste conjunto (sem contar
            alvo_sin/alvo_cos, adicionadas aqui dentro).
        horizonte: Horizonte de previsão em semanas (só usado para rotular
            a saída; o deslocamento do alvo já veio pronto em 'y_h').

    Returns:
        Tabela com uma linha por semana testada: data, h, real, pred.
    """
    features_com_sazonalidade = list(colunas_features) + ["alvo_sin", "alvo_cos"]
    colunas_obrigatorias = features_com_sazonalidade + ["y_h"]

    dados_validos = (
        dados_com_features.dropna(subset=colunas_obrigatorias)
        .sort_values("data")
        .reset_index(drop=True)
    )

    linhas_resultado = []
    numero_de_semanas_validas = len(dados_validos)
    for indice_corte in range(
        MINIMO_SEMANAS_TREINO, numero_de_semanas_validas, PASSO_RETREINO_SEMANAS
    ):
        treino = dados_validos.iloc[:indice_corte]
        teste = dados_validos.iloc[indice_corte : indice_corte + 1]

        modelo = LGBMRegressor(**PARAMETROS_LIGHTGBM)
        modelo.fit(treino[features_com_sazonalidade], treino["y_h"])
        previsao = modelo.predict(teste[features_com_sazonalidade])[0]

        linhas_resultado.append(
            {
                "data": teste["data"].to_numpy()[0],
                "h": horizonte,
                "real": teste["y_h"].to_numpy()[0],
                "pred": previsao,
            }
        )

    return pd.DataFrame(linhas_resultado)


def construir_previsao_persistencia(dados_com_features: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Previsão ingênua: repete o valor de casos da semana atual.

    Usada só como referência (item 4 do protocolo do Teste A) — não entra
    nos testes de equivalência entre clima e vetor.

    Args:
        dados_com_features: Tabela com a coluna 'casos' já presente.
        horizonte: Horizonte de previsão em semanas.

    Returns:
        Tabela com uma linha por semana onde tanto o valor atual quanto o
        valor horizonte semanas à frente são conhecidos: data, h, real, pred.
    """
    valor_atual = dados_com_features[COLUNA_CASOS]
    valor_futuro = dados_com_features[COLUNA_CASOS].shift(-horizonte)
    linhas_validas = valor_atual.notna() & valor_futuro.notna()

    resultado = pd.DataFrame(
        {
            "data": dados_com_features.loc[linhas_validas, "data"],
            "h": horizonte,
            "real": valor_futuro.loc[linhas_validas],
            "pred": valor_atual.loc[linhas_validas],
        }
    )
    return resultado.reset_index(drop=True)


# --- Estatística sobre os erros pareados ---


def calcular_variancia_longo_prazo(diferenca: np.ndarray, horizonte: int) -> float:
    """Variância de longo prazo da média de uma série pareada autocorrelacionada.

    Usa a mesma estrutura do teste de Diebold-Mariano: variância da
    diferença (gama_0) mais duas vezes a soma das autocovariâncias até a
    defasagem (horizonte - 1) — o truncamento padrão da literatura de DM,
    porque erros de previsão h-passos-à-frente só podem ser autocorrelacionados
    até a defasagem h-1 sob a hipótese nula de previsão ótima.

    Args:
        diferenca: Série pareada (ex.: erro_absoluto_vetor - erro_absoluto_clima),
            em ordem cronológica.
        horizonte: Horizonte de previsão em semanas (define o truncamento).

    Returns:
        Estimativa da variância de longo prazo de diferenca (não dividida
        por n ainda). Nunca retorna valor menor ou igual a zero: se a soma
        das autocovariâncias deixar o resultado não positivo (possível com
        autocovariâncias negativas em amostras pequenas), o retorno é
        travado em gama_0 (a variância simples, sem o ajuste de
        autocorrelação) — preserva a variância mínima observável da série
        em vez de propagar um número sem sentido estatístico.
    """
    numero_observacoes = len(diferenca)
    media_diferenca = diferenca.mean()
    desvios = diferenca - media_diferenca

    gama_zero = float((desvios**2).sum() / numero_observacoes)

    soma_autocovariancias = 0.0
    for defasagem in range(1, horizonte):
        autocovariancia_na_defasagem = float(
            (desvios[defasagem:] * desvios[:-defasagem]).sum() / numero_observacoes
        )
        soma_autocovariancias += 2 * autocovariancia_na_defasagem

    variancia_longo_prazo = gama_zero + soma_autocovariancias
    if variancia_longo_prazo <= 0:
        variancia_longo_prazo = gama_zero
    return variancia_longo_prazo


def testar_diebold_mariano_hln(diferenca: np.ndarray, horizonte: int) -> tuple[float, float]:
    """Teste de Diebold-Mariano com a correção de amostra pequena de Harvey-
    Leybourne-Newbold (1997), bicaudal.

    Args:
        diferenca: erro_absoluto_vetor - erro_absoluto_clima, pareado,
            em ordem cronológica.
        horizonte: Horizonte de previsão em semanas.

    Returns:
        Tupla (estatística DM-HLN, p-valor bicaudal, com base na
        distribuição t de Student com n-1 graus de liberdade).
    """
    numero_observacoes = len(diferenca)
    media_diferenca = diferenca.mean()
    variancia_longo_prazo = calcular_variancia_longo_prazo(diferenca, horizonte)
    variancia_da_media = variancia_longo_prazo / numero_observacoes

    estatistica_dm = media_diferenca / np.sqrt(variancia_da_media)
    fator_correcao_hln = np.sqrt(
        (
            numero_observacoes
            + 1
            - 2 * horizonte
            + horizonte * (horizonte - 1) / numero_observacoes
        )
        / numero_observacoes
    )
    estatistica_dm_hln = estatistica_dm * fator_correcao_hln

    graus_de_liberdade = numero_observacoes - 1
    p_valor = 2 * (1 - stats.t.cdf(abs(estatistica_dm_hln), df=graus_de_liberdade))
    return float(estatistica_dm_hln), float(p_valor)


@dataclasses.dataclass(frozen=True)
class ResultadoTost:
    """Resultado de um teste de equivalência TOST para uma margem."""

    margem_absoluta: float
    p_unilateral_inferior: float
    p_unilateral_superior: float
    p_tost: float
    equivalente_a_5pct: bool


def testar_tost_equivalencia(
    diferenca: np.ndarray, horizonte: int, margem_absoluta: float
) -> ResultadoTost:
    """Teste de equivalência TOST (two one-sided tests) sobre ΔMAE.

    Declara equivalência, ao nível de 5%, quando ΔMAE está dentro de
    [-margem, +margem] com confiança estatística — operacionalmente,
    quando o maior dos dois p-valores unilaterais é menor que 0,05. Usa o
    mesmo estimador de variância de longo prazo do teste de Diebold-Mariano
    (calcular_variancia_longo_prazo), SEM o fator de correção HLN: o fator
    HLN corrige especificamente a estatística DM sob a hipótese nula de
    diferença zero; aqui a hipótese nula testada é diferença = ±margem, um
    caso para o qual a correção HLN não foi derivada. Usar o mesmo
    estimador de variância (em vez do desvio-padrão simples, que ignora
    autocorrelação) evita subestimar o erro-padrão nos horizontes mais
    longos, onde os erros de previsão são mais autocorrelacionados.

    Args:
        diferenca: erro_absoluto_vetor - erro_absoluto_clima, pareado.
        horizonte: Horizonte de previsão em semanas.
        margem_absoluta: Margem de equivalência, em unidades de casos
            (calculada por fora como fração do MAE do SO_CLIMA).

    Returns:
        ResultadoTost com os dois p-valores unilaterais, o p do TOST (o
        maior dos dois) e se a equivalência foi declarada a 5%.
    """
    numero_observacoes = len(diferenca)
    media_diferenca = diferenca.mean()
    variancia_longo_prazo = calcular_variancia_longo_prazo(diferenca, horizonte)
    erro_padrao = np.sqrt(variancia_longo_prazo / numero_observacoes)
    graus_de_liberdade = numero_observacoes - 1

    estatistica_limite_inferior = (media_diferenca - (-margem_absoluta)) / erro_padrao
    estatistica_limite_superior = (media_diferenca - margem_absoluta) / erro_padrao

    p_unilateral_inferior = 1 - stats.t.cdf(estatistica_limite_inferior, df=graus_de_liberdade)
    p_unilateral_superior = stats.t.cdf(estatistica_limite_superior, df=graus_de_liberdade)
    p_tost = max(p_unilateral_inferior, p_unilateral_superior)

    return ResultadoTost(
        margem_absoluta=margem_absoluta,
        p_unilateral_inferior=float(p_unilateral_inferior),
        p_unilateral_superior=float(p_unilateral_superior),
        p_tost=float(p_tost),
        equivalente_a_5pct=bool(p_tost < NIVEL_SIGNIFICANCIA),
    )


def bootstrap_em_blocos_ic95(
    diferenca: np.ndarray, tamanho_bloco: int, numero_reamostras: int, semente: int
) -> tuple[float, float]:
    """IC 95% da média de uma série pareada por bootstrap em blocos móveis.

    Reamostra blocos de tamanho_bloco semanas CONSECUTIVAS (com reposição),
    preservando a autocorrelação de curto prazo dentro de cada bloco, até
    reconstruir uma série do mesmo tamanho da original; repete isso
    numero_reamostras vezes e toma os percentis 2,5 e 97,5 das médias
    obtidas.

    Args:
        diferenca: erro_absoluto_vetor - erro_absoluto_clima, pareado, em
            ordem cronológica.
        tamanho_bloco: Quantas semanas consecutivas cada bloco reamostrado tem.
        numero_reamostras: Quantas reamostras de bootstrap gerar.
        semente: Semente do gerador aleatório (reprodutibilidade).

    Returns:
        Tupla (limite inferior do IC 95%, limite superior do IC 95%).
    """
    gerador_aleatorio = np.random.default_rng(semente)
    numero_observacoes = len(diferenca)
    numero_blocos_por_reamostra = int(np.ceil(numero_observacoes / tamanho_bloco))
    posicoes_iniciais_possiveis = numero_observacoes - tamanho_bloco + 1

    medias_das_reamostras = np.empty(numero_reamostras)
    for indice_reamostra in range(numero_reamostras):
        posicoes_iniciais_sorteadas = gerador_aleatorio.integers(
            0, posicoes_iniciais_possiveis, size=numero_blocos_por_reamostra
        )
        blocos_sorteados = []
        for posicao_inicial in posicoes_iniciais_sorteadas:
            bloco = diferenca[posicao_inicial : posicao_inicial + tamanho_bloco]
            blocos_sorteados.append(bloco)
        serie_reamostrada = np.concatenate(blocos_sorteados)[:numero_observacoes]
        medias_das_reamostras[indice_reamostra] = serie_reamostrada.mean()

    limite_inferior = float(np.percentile(medias_das_reamostras, 2.5))
    limite_superior = float(np.percentile(medias_das_reamostras, 97.5))
    return limite_inferior, limite_superior


# --- Orquestração ---


def calcular_mae(erro_absoluto: np.ndarray) -> float:
    """Erro absoluto médio."""
    return float(erro_absoluto.mean())


def montar_linha_de_resultado(
    versao: str,
    horizonte: int,
    previsoes_clima: pd.DataFrame,
    previsoes_vetor: pd.DataFrame,
    previsoes_persistencia: pd.DataFrame,
) -> dict:
    """Alinha clima e vetor pelas mesmas semanas de teste e roda os testes.

    O alinhamento é necessário porque cada conjunto pode ter um subconjunto
    de semanas válidas ligeiramente diferente (o vetor tem 7 semanas faltantes
    isoladas na série toda, que se propagam para até 4 semanas seguintes via
    defasagem; o clima começa em 2018-12-30, mais tarde que os casos). Os
    testes pareados (DM, TOST, bootstrap) só fazem sentido sobre a
    INTERSEÇÃO de semanas onde os dois conjuntos produziram previsão.

    Args:
        versao: 'puro' ou 'com_ar'.
        horizonte: Horizonte de previsão em semanas.
        previsoes_clima: Saída de executar_walk_forward para o conjunto
            SO_CLIMA_* deste horizonte.
        previsoes_vetor: Saída de executar_walk_forward para o conjunto
            SO_VETOR_* deste horizonte.
        previsoes_persistencia: Saída de construir_previsao_persistencia
            para este horizonte.

    Returns:
        Dicionário com uma linha da tabela final de resultados.
    """
    pareado = previsoes_clima.merge(
        previsoes_vetor, on=["data", "h", "real"], suffixes=("_clima", "_vetor")
    )
    pareado = pareado.merge(
        previsoes_persistencia[["data", "h", "pred"]].rename(columns={"pred": "pred_persistencia"}),
        on=["data", "h"],
        how="left",
    )
    pareado = pareado.sort_values("data").reset_index(drop=True)

    erro_absoluto_clima = (pareado["real"] - pareado["pred_clima"]).abs().to_numpy()
    erro_absoluto_vetor = (pareado["real"] - pareado["pred_vetor"]).abs().to_numpy()
    diferenca_de_erro = erro_absoluto_vetor - erro_absoluto_clima

    mae_clima = calcular_mae(erro_absoluto_clima)
    mae_vetor = calcular_mae(erro_absoluto_vetor)
    delta_mae = mae_vetor - mae_clima

    previsao_persistencia_valida = pareado["pred_persistencia"].notna()
    erro_absoluto_persistencia = (
        pareado.loc[previsao_persistencia_valida, "real"]
        - pareado.loc[previsao_persistencia_valida, "pred_persistencia"]
    ).abs().to_numpy()
    mae_persistencia = calcular_mae(erro_absoluto_persistencia)

    estatistica_dm_hln, p_valor_dm_hln = testar_diebold_mariano_hln(diferenca_de_erro, horizonte)
    intervalo_inferior_boot, intervalo_superior_boot = bootstrap_em_blocos_ic95(
        diferenca_de_erro, TAMANHO_BLOCO_BOOTSTRAP, NUMERO_REAMOSTRAS_BOOTSTRAP, SEMENTE_BOOTSTRAP
    )

    linha_resultado = {
        "versao": versao,
        "h": horizonte,
        "n_semanas_pareadas": len(pareado),
        "MAE_SO_CLIMA": mae_clima,
        "MAE_SO_VETOR": mae_vetor,
        "MAE_persistencia_mesmas_semanas": mae_persistencia,
        "n_semanas_persistencia_valida": int(previsao_persistencia_valida.sum()),
        "delta_MAE_vetor_menos_clima": delta_mae,
        "delta_MAE_ic95_boot_inferior": intervalo_inferior_boot,
        "delta_MAE_ic95_boot_superior": intervalo_superior_boot,
        "DM_HLN_estatistica": estatistica_dm_hln,
        "DM_HLN_p_valor_bicaudal": p_valor_dm_hln,
    }

    for fracao_margem in MARGENS_TOST_FRACAO_MAE_CLIMA:
        margem_absoluta = fracao_margem * mae_clima
        resultado_tost = testar_tost_equivalencia(diferenca_de_erro, horizonte, margem_absoluta)
        rotulo_margem = f"{int(fracao_margem * 100)}pct"
        linha_resultado[f"TOST_margem_{rotulo_margem}_valor_absoluto"] = margem_absoluta
        linha_resultado[f"TOST_margem_{rotulo_margem}_p_valor"] = resultado_tost.p_tost
        linha_resultado[f"TOST_margem_{rotulo_margem}_equivalente_a_5pct"] = (
            resultado_tost.equivalente_a_5pct
        )

    return linha_resultado


def main() -> None:
    tempo_inicio = time.time()

    tabela_final = carregar_tabela_final(CAMINHO_TABELA_FINAL)
    tabela_com_features = construir_features_temporais(tabela_final)
    conjuntos_de_features = definir_conjuntos_de_features(tabela_com_features)

    print(f"Tabela final carregada: {len(tabela_com_features)} semanas.")
    for conjunto in conjuntos_de_features:
        print(f"  {conjunto.nome} ({conjunto.versao}): {len(conjunto.colunas_features)} features")

    previsoes_por_conjunto_e_horizonte: dict[tuple[str, int], pd.DataFrame] = {}
    previsoes_persistencia_por_horizonte: dict[int, pd.DataFrame] = {}

    for horizonte in HORIZONTES:
        dados_do_horizonte = construir_alvo_horizonte(tabela_com_features, horizonte)

        previsao_persistencia = construir_previsao_persistencia(tabela_com_features, horizonte)
        previsoes_persistencia_por_horizonte[horizonte] = previsao_persistencia
        caminho_persistencia = PASTA_SAIDA / f"previsoes_persistencia_h{horizonte}.csv"
        previsao_persistencia.to_csv(caminho_persistencia, index=False)

        for conjunto in conjuntos_de_features:
            previsoes = executar_walk_forward(
                dados_do_horizonte, conjunto.colunas_features, horizonte
            )
            previsoes_por_conjunto_e_horizonte[(conjunto.nome, horizonte)] = previsoes

            caminho_previsoes = PASTA_SAIDA / f"previsoes_{conjunto.nome}_h{horizonte}.csv"
            previsoes.to_csv(caminho_previsoes, index=False)

            tempo_decorrido = time.time() - tempo_inicio
            print(
                f"  [{tempo_decorrido:6.1f}s] {conjunto.nome} h={horizonte}: "
                f"{len(previsoes)} previsões -> {caminho_previsoes.name}"
            )

    linhas_de_resultado = []
    for versao, nome_clima, nome_vetor in (
        ("puro", "SO_CLIMA_PURO", "SO_VETOR_PURO"),
        ("com_ar", "SO_CLIMA_AR", "SO_VETOR_AR"),
    ):
        for horizonte in HORIZONTES:
            previsoes_clima = previsoes_por_conjunto_e_horizonte[(nome_clima, horizonte)]
            previsoes_vetor = previsoes_por_conjunto_e_horizonte[(nome_vetor, horizonte)]
            previsoes_persistencia = previsoes_persistencia_por_horizonte[horizonte]

            linha_resultado = montar_linha_de_resultado(
                versao, horizonte, previsoes_clima, previsoes_vetor, previsoes_persistencia
            )
            linhas_de_resultado.append(linha_resultado)

    tabela_de_resultados = pd.DataFrame(linhas_de_resultado)
    caminho_resultados = PASTA_SAIDA / "resultados_testes_equivalencia.csv"
    tabela_de_resultados.to_csv(caminho_resultados, index=False)

    tempo_total = time.time() - tempo_inicio
    print(f"\nResultados salvos em: {caminho_resultados}")
    print(f"Tempo total: {tempo_total:.1f}s ({tempo_total / 60:.1f} min)")


if __name__ == "__main__":
    main()
