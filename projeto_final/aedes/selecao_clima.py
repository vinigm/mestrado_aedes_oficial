"""E6a: reproducao da escolha das 6 colunas de clima (ranking de ganho de um LightGBM).

Funcoes puras: recebem a tabela semanal JA CORTADA pela maturidade e devolvem
tabelas e series. Nenhuma le ou grava arquivo.

Replica, sem nenhuma correcao, o procedimento do codigo antigo:
    - `modelagem_aedes/dominio/selecao_features.py:60-118`
      (`separar_grupos_de_features` e `selecionar_clima_por_ganho`);
    - parametros em `modelagem_aedes/config/experimentos/cidade_regressao.py:27-38`
      (LightGBM: 250 arvores, taxa 0,05, 15 folhas, folha minima 5, `n_jobs=-1`,
      SEM semente) e `:131-136` (horizontes 1, 4 e 8; fracao de treino 0,60;
      colunas ignoradas e padroes de nome);
    - chamada em `analises/2026-09-23_bateria_noturna/harness.py:185-196`
      (as 6 primeiras do ranking viram o clima do modelo).

O QUE O PROCEDIMENTO FAZ

    1. Monta a tabela das CANDIDATAS: as colunas da tabela, mais as defasagens
       1 a 4 de 7 colunas (casos, vetor, temp_media, precip_total_mm,
       orvalho_media, umid_media, pressao_media), as medias moveis de 4 semanas
       de casos e do vetor, e seno/cosseno da semana (`features.py:64-114`).
    2. Separa as colunas em tres grupos por pedacos de nome: vetor, clima e
       nucleo (as ignoradas ficam fora). Sao 42 candidatas de clima e 8 do nucleo.
    3. Para cada horizonte h em {1, 4, 8}: alvo `y_h = casos.shift(-h)`, seno e
       cosseno da semana-alvo, descarta linhas com ausente em qualquer coluna,
       ordena por data, fica com os PRIMEIROS 60% das linhas validas (a partir
       de 2018 ate nov/2022) e treina um LightGBM de regressao (perda quadratica).
    4. Soma o ganho (`importance_type="gain"`) de cada candidata nos 3
       horizontes e ordena do maior para o menor. As 6 primeiras sao o clima.

LIMITACAO DECLARADA (a mesma do antigo): a selecao usa o inicio da serie, mas
nao esta DENTRO do walk-forward; ela olha os 60% mais antigos de uma tabela
que ja inclui o periodo de avaliacao nas linhas restantes (que nao entram no
treino da selecao).
"""

import dataclasses

import lightgbm
import numpy as np
import pandas as pd

from aedes.configuracao import ConfiguracaoDados

NOME_DA_COLUNA_DE_DATA = "data"
NOME_DA_COLUNA_DE_CASOS = "casos"
NOME_DA_COLUNA_DA_SEMANA = "semana"
NOME_DA_COLUNA_DO_VETOR = "aedes_aegypti_por_armadilha"
NOME_DO_ALVO = "y_h"
NOMES_DA_SAZONALIDADE_DO_ALVO = ("alvo_sin", "alvo_cos")
NOMES_DA_SAZONALIDADE_DA_ORIGEM = ("sem_sin", "sem_cos")
NOME_DA_MEDIA_MOVEL_DE_CASOS = "casos_mm4"
NOME_DA_MEDIA_MOVEL_DO_VETOR = "vetor_mm4"

# Colunas que ganham defasagens (a lista e a ordem do antigo, `features.py:19-27`;
# a ordem importa porque a ordem das colunas candidatas e a ordem de desempate).
COLUNAS_COM_DEFASAGEM = (
    "casos",
    "aedes_aegypti_por_armadilha",
    "temp_media",
    "precip_total_mm",
    "orvalho_media",
    "umid_media",
    "pressao_media",
)
DEFASAGENS_DAS_CANDIDATAS = (1, 2, 3, 4)
JANELA_DA_MEDIA_MOVEL = 4
SEMANAS_POR_ANO = 52

# Colunas que nunca entram em grupo nenhum (`cidade_regressao.py:123-127`).
COLUNAS_IGNORADAS = (
    "fonte",
    "SE",
    "data",
    "ano",
    "semana",
    "interpolado",
    "denominador_aproximado",
    "aedes_aegypti",
    "aedes_albopictus",
    "culex_sp",
    "numero_de_armadilhas",
    "nino34_anom",
    "oni",
)
PADROES_DO_VETOR = ("aedes", "armadilha", "vetor")
PADROES_DO_CLIMA = (
    "temp",
    "precip",
    "orvalho",
    "umid",
    "pressao",
    "radiacao",
    "vento",
    "dias_de_chuva",
)

HORIZONTES_DA_SELECAO = (1, 4, 8)
FRACAO_DE_TREINO_DA_SELECAO = 0.60
QUANTIDADE_DE_COLUNAS_DE_CLIMA = 6
QUANTIDADE_ESPERADA_DE_CANDIDATAS = 42
QUANTIDADE_ESPERADA_DO_NUCLEO = 8


@dataclasses.dataclass(frozen=True)
class ConfiguracaoDoModeloDeSelecao:
    """Hiperparametros do LightGBM que pontua as colunas de clima.

    Os cinco primeiros campos sao os do antigo. `n_jobs` e `semente` sao as duas
    coisas que a E6a varia: o antigo usava `n_jobs=-1` e NAO passava semente.

    Attributes:
        numero_de_arvores: `n_estimators`.
        taxa_de_aprendizado: `learning_rate`.
        numero_de_folhas: `num_leaves`.
        folha_minima: `min_child_samples`.
        nivel_de_mensagens: `verbose` (-1 = silencioso).
        numero_de_processos: `n_jobs` (-1 = todos; 1 = um so).
        semente: `random_state`; `None` = nao passa semente (como o antigo).
    """

    numero_de_arvores: int
    taxa_de_aprendizado: float
    numero_de_folhas: int
    folha_minima: int
    nivel_de_mensagens: int
    numero_de_processos: int
    semente: int | None

    def parametros_do_lightgbm(self) -> dict[str, object]:
        """Argumentos de `LGBMRegressor(**...)`. Sem `random_state` quando a semente e `None`."""
        parametros: dict[str, object] = {
            "n_estimators": self.numero_de_arvores,
            "learning_rate": self.taxa_de_aprendizado,
            "num_leaves": self.numero_de_folhas,
            "min_child_samples": self.folha_minima,
            "verbose": self.nivel_de_mensagens,
            "n_jobs": self.numero_de_processos,
        }
        if self.semente is not None:
            parametros["random_state"] = self.semente
        return parametros


# Variante 1: identica ao antigo (`cidade_regressao.py:27-38`).
MODELO_DE_SELECAO_IDENTICO_AO_ANTIGO = ConfiguracaoDoModeloDeSelecao(
    numero_de_arvores=250,
    taxa_de_aprendizado=0.05,
    numero_de_folhas=15,
    folha_minima=5,
    nivel_de_mensagens=-1,
    numero_de_processos=-1,
    semente=None,
)
# Variante 2: um processo so, sem semente.
MODELO_DE_SELECAO_UM_PROCESSO = dataclasses.replace(
    MODELO_DE_SELECAO_IDENTICO_AO_ANTIGO, numero_de_processos=1
)
# Variante 3: um processo so, com semente 42.
MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE = dataclasses.replace(
    MODELO_DE_SELECAO_UM_PROCESSO, semente=42
)


@dataclasses.dataclass(frozen=True)
class GruposDeColunas:
    """As colunas da tabela candidata separadas em tres grupos, na ordem da tabela.

    Attributes:
        nucleo: Historico dos casos e sazonalidade (8 colunas na tabela certificada).
        clima: Candidatas de clima (42 na tabela certificada).
        vetor: Colunas do vetor (nao entram na selecao; so o M1 as usa).
    """

    nucleo: list[str]
    clima: list[str]
    vetor: list[str]


@dataclasses.dataclass(frozen=True)
class ResultadoDaSelecaoDeClima:
    """O ranking de ganho das candidatas de clima.

    Attributes:
        ranking: Ganho somado de cada candidata nos horizontes da selecao,
            ordenado do maior para o menor (`sort_values(ascending=False)`).
        ganho_por_horizonte: Uma linha por candidata (na ordem da tabela), uma
            coluna por horizonte, com o ganho daquele horizonte. O antigo
            somava e descartava; guardar o ganho de cada horizonte e novo.
        linhas_validas_por_horizonte: Linhas sem ausente em cada horizonte.
        linhas_de_treino_por_horizonte: Linhas dos primeiros 60% usadas no treino.
    """

    ranking: pd.Series
    ganho_por_horizonte: pd.DataFrame
    linhas_validas_por_horizonte: dict[int, int]
    linhas_de_treino_por_horizonte: dict[int, int]


def construir_tabela_de_candidatas(
    tabela_cortada: pd.DataFrame,
    configuracao_dados: ConfiguracaoDados,
) -> pd.DataFrame:
    """Monta a tabela com as colunas candidatas (defasagens, medias moveis e sazonalidade).

    Faz o que `features.construir_features_temporais` fazia sobre a tabela
    ja renomeada (`data`, `casos`): colunas novas ACRESCENTADAS depois das
    originais, na ordem do antigo. A ordem das colunas e relevante porque
    define a ordem das candidatas na selecao.

    Args:
        tabela_cortada: Tabela semanal depois do corte de maturidade, em grade
            semanal contigua. Nao e modificada.
        configuracao_dados: Nomes da coluna de data e da de casos da tabela.

    Returns:
        DataFrame NOVO com as colunas originais (a de data renomeada para `data`
        e a de casos para `casos`) e as colunas novas.

    Raises:
        KeyError: Se faltar a coluna da semana, a de casos, a de data ou o vetor.
    """
    colunas_necessarias = [
        configuracao_dados.coluna_de_data,
        configuracao_dados.coluna_de_casos,
        NOME_DA_COLUNA_DA_SEMANA,
        NOME_DA_COLUNA_DO_VETOR,
    ]
    colunas_ausentes = []
    for nome_da_coluna in colunas_necessarias:
        if nome_da_coluna not in tabela_cortada.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes na tabela das candidatas: {colunas_ausentes}")

    renomeacao = {
        configuracao_dados.coluna_de_data: NOME_DA_COLUNA_DE_DATA,
        configuracao_dados.coluna_de_casos: NOME_DA_COLUNA_DE_CASOS,
    }
    tabela = tabela_cortada.rename(columns=renomeacao).copy()

    colunas_novas: dict[str, pd.Series] = {}
    for coluna_de_origem in COLUNAS_COM_DEFASAGEM:
        if coluna_de_origem not in tabela.columns:
            continue
        for defasagem in DEFASAGENS_DAS_CANDIDATAS:
            nome_da_defasagem = f"{coluna_de_origem}_lag{defasagem}"
            colunas_novas[nome_da_defasagem] = tabela[coluna_de_origem].shift(defasagem)

    casos = tabela[NOME_DA_COLUNA_DE_CASOS]
    vetor = tabela[NOME_DA_COLUNA_DO_VETOR]
    colunas_novas[NOME_DA_MEDIA_MOVEL_DE_CASOS] = casos.rolling(JANELA_DA_MEDIA_MOVEL).mean()
    colunas_novas[NOME_DA_MEDIA_MOVEL_DO_VETOR] = vetor.rolling(JANELA_DA_MEDIA_MOVEL).mean()

    angulo_sazonal = 2 * np.pi * tabela[NOME_DA_COLUNA_DA_SEMANA] / SEMANAS_POR_ANO
    nome_do_seno, nome_do_cosseno = NOMES_DA_SAZONALIDADE_DA_ORIGEM
    colunas_novas[nome_do_seno] = np.sin(angulo_sazonal)
    colunas_novas[nome_do_cosseno] = np.cos(angulo_sazonal)

    tabela_das_novas = pd.DataFrame(colunas_novas, index=tabela.index)
    return pd.concat([tabela, tabela_das_novas], axis=1)


def _nome_contem_algum_padrao(nome_da_coluna: str, padroes: tuple[str, ...]) -> bool:
    """Diz se algum pedaco de texto da lista aparece dentro do nome da coluna."""
    for padrao in padroes:
        if padrao in nome_da_coluna:
            return True
    return False


def separar_grupos_de_colunas(
    nomes_das_colunas: list[str],
    colunas_ignoradas: tuple[str, ...],
    padroes_do_vetor: tuple[str, ...],
    padroes_do_clima: tuple[str, ...],
) -> GruposDeColunas:
    """Separa as colunas em vetor, clima e nucleo pelos pedacos de nome.

    Regra do antigo (`selecao_features.py:43-48`): as ignoradas saem; fica no
    VETOR a coluna com algum padrao do vetor; fica no CLIMA a coluna com algum
    padrao de clima; as demais sao o NUCLEO. Uma coluna que casasse com os dois
    padroes entraria nos dois grupos (a tabela certificada nao tem nenhuma).
    A ordem de cada lista e a ordem das colunas na tabela.

    Args:
        nomes_das_colunas: Colunas da tabela candidata, na ordem da tabela.
        colunas_ignoradas: Nomes exatos que ficam fora dos tres grupos.
        padroes_do_vetor: Pedacos de nome do vetor.
        padroes_do_clima: Pedacos de nome do clima.

    Returns:
        Os tres grupos.
    """
    nomes_das_features: list[str] = []
    for nome_da_coluna in nomes_das_colunas:
        if nome_da_coluna not in colunas_ignoradas:
            nomes_das_features.append(nome_da_coluna)

    colunas_do_vetor: list[str] = []
    for nome_da_coluna in nomes_das_features:
        if _nome_contem_algum_padrao(nome_da_coluna, padroes_do_vetor):
            colunas_do_vetor.append(nome_da_coluna)

    colunas_do_clima: list[str] = []
    for nome_da_coluna in nomes_das_features:
        if _nome_contem_algum_padrao(nome_da_coluna, padroes_do_clima):
            colunas_do_clima.append(nome_da_coluna)

    colunas_do_nucleo: list[str] = []
    for nome_da_coluna in nomes_das_features:
        esta_no_vetor = nome_da_coluna in colunas_do_vetor
        esta_no_clima = nome_da_coluna in colunas_do_clima
        if not esta_no_vetor and not esta_no_clima:
            colunas_do_nucleo.append(nome_da_coluna)

    return GruposDeColunas(nucleo=colunas_do_nucleo, clima=colunas_do_clima, vetor=colunas_do_vetor)


def criar_modelo_de_selecao(configuracao: ConfiguracaoDoModeloDeSelecao) -> lightgbm.LGBMRegressor:
    """Cria um LGBMRegressor NOVO (sem treino) com a configuracao dada."""
    parametros = configuracao.parametros_do_lightgbm()
    return lightgbm.LGBMRegressor(**parametros)


def _montar_dados_validos_do_horizonte(
    tabela_de_candidatas: pd.DataFrame,
    nomes_das_features: list[str],
    horizonte: int,
) -> pd.DataFrame:
    """Alvo `y_h` e sazonalidade da semana-alvo; descarta ausente e ordena por data.

    Replica `construir_alvo_horizonte` (`features.py:118-156`) seguido do
    `dropna(...).sort_values("data").reset_index(drop=True)` do antigo.
    """
    dados = tabela_de_candidatas.copy()
    dados[NOME_DO_ALVO] = tabela_de_candidatas[NOME_DA_COLUNA_DE_CASOS].shift(-horizonte)
    semana_do_alvo = tabela_de_candidatas[NOME_DA_COLUNA_DA_SEMANA].shift(-horizonte)
    angulo_do_alvo = 2 * np.pi * semana_do_alvo / SEMANAS_POR_ANO
    nome_do_seno, nome_do_cosseno = NOMES_DA_SAZONALIDADE_DO_ALVO
    dados[nome_do_seno] = np.sin(angulo_do_alvo)
    dados[nome_do_cosseno] = np.cos(angulo_do_alvo)

    colunas_que_nao_podem_faltar = list(nomes_das_features)
    colunas_que_nao_podem_faltar.append(NOME_DO_ALVO)
    dados_completos = dados.dropna(subset=colunas_que_nao_podem_faltar)
    dados_ordenados = dados_completos.sort_values(NOME_DA_COLUNA_DE_DATA)
    return dados_ordenados.reset_index(drop=True)


def calcular_ganho_do_horizonte(
    tabela_de_candidatas: pd.DataFrame,
    grupos: GruposDeColunas,
    horizonte: int,
    fracao_de_treino: float,
    configuracao_do_modelo: ConfiguracaoDoModeloDeSelecao,
) -> tuple[pd.Series, int, int]:
    """Treina o LightGBM de UM horizonte nos primeiros 60% e devolve o ganho das candidatas de clima.

    Args:
        tabela_de_candidatas: Saida de `construir_tabela_de_candidatas`.
        grupos: Colunas do nucleo e do clima.
        horizonte: Semanas a frente.
        fracao_de_treino: Fracao inicial das linhas validas usada no treino (0,60).
        configuracao_do_modelo: Hiperparametros do LightGBM.

    Returns:
        O ganho de cada candidata de clima (0 para a que o modelo nao usou), as
        linhas validas do horizonte e as linhas de treino.

    Raises:
        ValueError: Se a fracao nao estiver em (0, 1] ou o treino ficar vazio.
    """
    if not 0.0 < fracao_de_treino <= 1.0:
        raise ValueError(f"fracao_de_treino deve estar em (0, 1], recebido {fracao_de_treino!r}.")

    nomes_do_seno_e_cosseno = list(NOMES_DA_SAZONALIDADE_DO_ALVO)
    nomes_das_features = grupos.nucleo + grupos.clima + nomes_do_seno_e_cosseno
    dados_validos = _montar_dados_validos_do_horizonte(tabela_de_candidatas, nomes_das_features, horizonte)

    quantidade_de_linhas_validas = len(dados_validos)
    quantidade_de_linhas_de_treino = int(quantidade_de_linhas_validas * fracao_de_treino)
    if quantidade_de_linhas_de_treino == 0:
        raise ValueError(f"Treino vazio no horizonte {horizonte}: {quantidade_de_linhas_validas} linhas validas.")
    treino = dados_validos.iloc[:quantidade_de_linhas_de_treino]

    modelo = criar_modelo_de_selecao(configuracao_do_modelo)
    variaveis_do_treino = treino[nomes_das_features]
    alvo_do_treino = treino[NOME_DO_ALVO]
    modelo.fit(variaveis_do_treino, alvo_do_treino)

    ganhos_das_features = modelo.booster_.feature_importance(importance_type="gain")
    ganho_por_feature = pd.Series(ganhos_das_features, index=nomes_das_features)
    ganho_do_clima = ganho_por_feature.reindex(grupos.clima).fillna(0)
    return ganho_do_clima, quantidade_de_linhas_validas, quantidade_de_linhas_de_treino


def selecionar_clima_por_ganho(
    tabela_de_candidatas: pd.DataFrame,
    grupos: GruposDeColunas,
    horizontes: tuple[int, ...],
    fracao_de_treino: float,
    configuracao_do_modelo: ConfiguracaoDoModeloDeSelecao,
) -> ResultadoDaSelecaoDeClima:
    """Ranking das candidatas de clima: ganho do LightGBM somado nos horizontes da selecao.

    Args:
        tabela_de_candidatas: Saida de `construir_tabela_de_candidatas`.
        grupos: Colunas do nucleo e do clima.
        horizontes: Horizontes que pontuam (1, 4 e 8).
        fracao_de_treino: Fracao inicial das linhas validas que treina (0,60).
        configuracao_do_modelo: Hiperparametros do LightGBM.

    Returns:
        O `ResultadoDaSelecaoDeClima`; `ranking` e a soma dos ganhos, ordenada
        do maior para o menor.

    Raises:
        ValueError: Se nao houver horizonte.
    """
    if len(horizontes) == 0:
        raise ValueError("horizontes nao pode ser vazio.")

    ganho_acumulado = pd.Series(0.0, index=grupos.clima)
    ganhos_por_horizonte: dict[str, pd.Series] = {}
    linhas_validas: dict[int, int] = {}
    linhas_de_treino: dict[int, int] = {}

    for horizonte in horizontes:
        ganho_do_horizonte, validas, de_treino = calcular_ganho_do_horizonte(
            tabela_de_candidatas, grupos, horizonte, fracao_de_treino, configuracao_do_modelo
        )
        ganho_acumulado = ganho_acumulado.add(ganho_do_horizonte, fill_value=0)
        ganhos_por_horizonte[f"ganho_h{horizonte}"] = ganho_do_horizonte
        linhas_validas[horizonte] = validas
        linhas_de_treino[horizonte] = de_treino

    ranking = ganho_acumulado.sort_values(ascending=False)
    return ResultadoDaSelecaoDeClima(
        ranking=ranking,
        ganho_por_horizonte=pd.DataFrame(ganhos_por_horizonte, index=grupos.clima),
        linhas_validas_por_horizonte=linhas_validas,
        linhas_de_treino_por_horizonte=linhas_de_treino,
    )


def escolher_as_melhores(ranking: pd.Series, quantidade: int) -> list[str]:
    """Os nomes das `quantidade` primeiras candidatas do ranking, na ordem do ranking.

    Raises:
        ValueError: Se a quantidade for menor que 1 ou maior que o ranking.
    """
    if quantidade < 1 or quantidade > len(ranking):
        raise ValueError(f"quantidade deve estar entre 1 e {len(ranking)}, recebido {quantidade}.")
    return ranking.head(quantidade).index.tolist()


def calcular_margem_de_entrada(ranking: pd.Series, quantidade_escolhida: int) -> dict[str, object]:
    """Quanto falta para a primeira candidata de fora entrar: ganho da ultima escolhida contra o da proxima.

    Leitura descritiva (pre-declaracao E6a). Tudo no ganho somado.

    Args:
        ranking: Ganho somado, ordenado do maior para o menor.
        quantidade_escolhida: Quantas entram (6).

    Returns:
        Nome e ganho da ultima escolhida e da proxima, a diferenca absoluta e a
        razao `ganho_da_proxima / ganho_da_ultima_escolhida`.

    Raises:
        ValueError: Se nao houver candidata de fora do ranking.
    """
    if quantidade_escolhida < 1 or quantidade_escolhida >= len(ranking):
        raise ValueError(
            f"quantidade_escolhida deve estar entre 1 e {len(ranking) - 1}, recebido {quantidade_escolhida}."
        )
    nome_da_ultima = str(ranking.index[quantidade_escolhida - 1])
    nome_da_proxima = str(ranking.index[quantidade_escolhida])
    ganho_da_ultima = float(ranking.iloc[quantidade_escolhida - 1])
    ganho_da_proxima = float(ranking.iloc[quantidade_escolhida])
    razao = float("nan")
    if ganho_da_ultima != 0.0:
        razao = ganho_da_proxima / ganho_da_ultima
    return {
        "ultima_escolhida": nome_da_ultima,
        "ganho_da_ultima_escolhida": ganho_da_ultima,
        "proxima": nome_da_proxima,
        "ganho_da_proxima": ganho_da_proxima,
        "diferenca": ganho_da_ultima - ganho_da_proxima,
        "razao_proxima_sobre_ultima": razao,
    }
