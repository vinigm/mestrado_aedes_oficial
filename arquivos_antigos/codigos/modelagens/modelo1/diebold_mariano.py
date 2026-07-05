"""Teste de Diebold-Mariano: o lift do vetor (M1) sobre o clima (M0) e significativo?

Compara, ponto a ponto e por horizonte, os erros de:
  M0 = nucleo + clima_enxuto (sem ENSO)        -- baseline "literatura"
  M1 = M0 + vetor (densidade de aegypti, 6)    -- + armadilha

DM proprio para previsao de h passos: variancia HAC (Newey-West, lag h-1) +
correcao de amostra pequena Harvey-Leybourne-Newbold (HLN), comparada a t(n-1).
H1 (unilateral): M1 erra MENOS que M0 (d_bar > 0, d = loss_M0 - loss_M1).

Roda nas DUAS versoes do alvo:
  - SEM corte de maturidade (= setup do Modelo 4b)
  - COM corte de maturidade 12 sem (= setup do Modelo 4c)
para checar se a significancia depende do corte.

PAREAMENTO: M0 e M1 sao avaliados nos MESMOS pontos de teste (dropna pela uniao
das features), senao o teste pareado nao e valido.
"""
import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy import stats

# --------------------------------------------------------------------- config
# Subdiretorio marcador que identifica a raiz do projeto (executavel de qualquer
# subpasta).
MARCADOR_RAIZ = "Raspagem"

# Hiperparametros do LightGBM. Arvores pequenas (num_leaves=15, min_child=5) por
# causa da serie curta; verbose=-1 silencia o log; n_jobs=-1 usa todos os nucleos.
PARAMETROS_LGBM = dict(
    n_estimators=250,
    learning_rate=0.05,
    num_leaves=15,
    min_child_samples=5,
    verbose=-1,
    n_jobs=-1,
)

# Quantas features de clima sobrevivem a selecao por importancia (clima_enxuto).
NUMERO_FEATURES_CLIMA = 6

# Colunas cujos lags 1-4 sao gerados.
COLUNAS_PARA_LAG = [
    "casos_confirmados",
    "aedes_aegypti_por_armadilha",
    "temp_media",
    "precip_total_mm",
    "orvalho_media",
    "umid_media",
    "pressao_media",
]
LAGS_SEMANAS = [1, 2, 3, 4]

# Constantes de dominio (evita numeros magicos soltos).
SEMANAS_POR_ANO = 52
JANELA_MEDIA_MOVEL_SEMANAS = 4
SEMANAS_CORTE_MATURIDADE = 12          # right-censoring do SINAN (Modelo 4c)
MINIMO_SEMANAS_TREINO = 104            # ~2 anos antes de comecar a prever
FRACAO_TREINO_SELECAO_CLIMA = 0.60     # fatia inicial usada na selecao de clima
HORIZONTES_SELECAO_CLIMA = (1, 4, 8)   # horizontes usados para pontuar o clima
HORIZONTES_TESTE = range(1, 13)        # h = 1..12 semanas no teste DM

# Colunas ignoradas na montagem da lista de features candidatas.
COLUNAS_DESCARTADAS = [
    "aedes_aegypti",
    "aedes_albopictus",
    "culex_sp",
    "numero_de_armadilhas",
]
COLUNAS_ENSO = ["nino34_anom", "oni"]
COLUNAS_META = [
    "fonte",
    "SE",
    "data_inicio_semana_epidemi",
    "ano",
    "semana",
    "interpolado",
]

# Substrings que classificam cada feature candidata como vetor ou como clima.
SUBSTRINGS_VETOR = ("aedes", "armadilha", "vetor")
SUBSTRINGS_CLIMA = (
    "temp",
    "precip",
    "orvalho",
    "umid",
    "pressao",
    "radiacao",
    "vento",
    "dias_de_chuva",
)

# Tipos de funcao de perda no teste DM.
PERDA_QUADRATICA = "sq"
PERDA_ABSOLUTA = "abs"

# Piso numerico da correcao HLN (evita raiz de valor nao positivo).
PISO_CORRECAO_HLN = 1e-9

# Limiares de significancia dos p-valores (unilaterais).
LIMIAR_P_ALTISSIMA = 0.01
LIMIAR_P_ALTA = 0.05
LIMIAR_P_MODERADA = 0.10


def encontrar_raiz_do_projeto(marcador_de_diretorio: str = MARCADOR_RAIZ) -> Path:
    """Sobe a partir do diretorio atual ate achar a raiz do projeto.

    A raiz e identificada pela presenca de um subdiretorio marcador (por padrao
    'Raspagem'), o que torna o script executavel de qualquer subpasta.

    Args:
        marcador_de_diretorio: Nome do subdiretorio que identifica a raiz.

    Returns:
        Caminho da raiz do projeto.

    Raises:
        FileNotFoundError: Se nenhum diretorio ancestral contiver o marcador.
    """
    diretorio_atual = Path.cwd()
    for diretorio_candidato in [diretorio_atual, *diretorio_atual.parents]:
        if (diretorio_candidato / marcador_de_diretorio).is_dir():
            return diretorio_candidato
    raise FileNotFoundError("raiz nao encontrada")


RAIZ_DO_PROJETO = encontrar_raiz_do_projeto()
DIRETORIO_TABELA_MODELAGEM = RAIZ_DO_PROJETO / "Bases de dados" / "tabela_modelagem"
CAMINHO_TABELA_FINAL = DIRETORIO_TABELA_MODELAGEM / "tabela_final.csv"


@dataclasses.dataclass(frozen=True)
class ResultadoDieboldMariano:
    """Resultado do teste de Diebold-Mariano para um horizonte e uma perda.

    Attributes:
        diferenca_media: Media da diferenca de perda (d_bar); >0 indica que M1
            (com vetor) erra menos que M0.
        estatistica: Estatistica DM ja com a correcao de amostra pequena (HLN);
            NaN quando a variancia HAC nao e positiva.
        valor_p: p-valor unilateral (H1: M1 melhor); NaN quando a estatistica e NaN.
        numero_observacoes: Numero de pontos de teste pareados.
    """

    diferenca_media: float
    estatistica: float
    valor_p: float
    numero_observacoes: int


def media_movel_4_semanas(serie: pd.Series) -> pd.Series:
    """Media movel de 4 semanas de uma serie de um unico bloco (fonte).

    Usada em transform() por grupo, para que a janela nao atravesse o gap entre
    os blocos de dados.
    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def selecionar_por_substring(
    colunas: list[str],
    substrings: tuple[str, ...],
) -> list[str]:
    """Retorna as colunas cujo nome contem alguma das substrings informadas.

    A ordem segue a ordem das colunas de entrada (a ordem das features importa:
    a arvore depende dela). Cada coluna entra no maximo uma vez.
    """
    colunas_selecionadas = []
    for nome_coluna in colunas:
        for substring in substrings:
            if substring in nome_coluna:
                colunas_selecionadas.append(nome_coluna)
                break
    return colunas_selecionadas


def selecionar_colunas_candidatas(
    dados: pd.DataFrame,
    colunas_ignoradas: list[str],
) -> list[str]:
    """Retorna, na ordem do DataFrame, as colunas que nao estao em ignoradas."""
    colunas_candidatas = []
    for nome_coluna in dados.columns:
        if nome_coluna not in colunas_ignoradas:
            colunas_candidatas.append(nome_coluna)
    return colunas_candidatas


def selecionar_nucleo(
    colunas_candidatas: list[str],
    colunas_vetor: list[str],
    colunas_clima: list[str],
) -> list[str]:
    """Retorna as candidatas que nao sao nem vetor nem clima (o nucleo)."""
    colunas_nucleo = []
    for nome_coluna in colunas_candidatas:
        if nome_coluna not in colunas_vetor and nome_coluna not in colunas_clima:
            colunas_nucleo.append(nome_coluna)
    return colunas_nucleo


def montar_tabela(
    aplicar_corte_maturidade: bool,
) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    """Le a tabela_final, cria as features e separa nucleo/clima/vetor.

    Ordena por fonte e data, opcionalmente aplica o corte de maturidade do
    Modelo 4c (zera para NaN os casos das ultimas 12 semanas, ainda em
    confirmacao), gera lags 1-4, medias moveis de 4 semanas e sazonalidade, e
    entao particiona as features candidatas em tres blocos por substring.

    Args:
        aplicar_corte_maturidade: Se True, aplica o right-censoring do SINAN.

    Returns:
        Tupla (tabela, nucleo, clima, vetor), onde os tres ultimos sao listas de
        nomes de coluna na ordem em que serao passados aos modelos.
    """
    tabela = pd.read_csv(
        CAMINHO_TABELA_FINAL,
        parse_dates=["data_inicio_semana_epidemi"],
    )
    tabela = tabela.sort_values(
        ["fonte", "data_inicio_semana_epidemi"]
    ).reset_index(drop=True)

    if aplicar_corte_maturidade:
        data_referencia = tabela["data_inicio_semana_epidemi"].max()
        limite_maturidade = data_referencia - pd.Timedelta(weeks=SEMANAS_CORTE_MATURIDADE)
        linhas_imaturas = tabela["data_inicio_semana_epidemi"] > limite_maturidade
        tabela.loc[linhas_imaturas, "casos_confirmados"] = np.nan

    grupos_por_fonte = tabela.groupby("fonte", group_keys=False)
    for coluna_origem in COLUNAS_PARA_LAG:
        for numero_de_semanas in LAGS_SEMANAS:
            nome_coluna_lag = f"{coluna_origem}_lag{numero_de_semanas}"
            tabela[nome_coluna_lag] = grupos_por_fonte[coluna_origem].shift(numero_de_semanas)

    tabela["casos_mm4"] = grupos_por_fonte["casos_confirmados"].transform(
        media_movel_4_semanas
    )
    tabela["vetor_mm4"] = grupos_por_fonte["aedes_aegypti_por_armadilha"].transform(
        media_movel_4_semanas
    )

    angulo_sazonal = 2 * np.pi * tabela["semana"] / SEMANAS_POR_ANO
    tabela["sem_sin"] = np.sin(angulo_sazonal)
    tabela["sem_cos"] = np.cos(angulo_sazonal)

    colunas_ignoradas = COLUNAS_META + COLUNAS_DESCARTADAS + COLUNAS_ENSO
    colunas_candidatas = selecionar_colunas_candidatas(tabela, colunas_ignoradas)
    colunas_vetor = selecionar_por_substring(colunas_candidatas, SUBSTRINGS_VETOR)
    colunas_clima = selecionar_por_substring(colunas_candidatas, SUBSTRINGS_CLIMA)
    colunas_nucleo = selecionar_nucleo(colunas_candidatas, colunas_vetor, colunas_clima)
    return tabela, colunas_nucleo, colunas_clima, colunas_vetor


def construir_alvo_horizonte(tabela: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Cria o alvo h passos a frente e a sazonalidade da semana-alvo.

    Args:
        tabela: Tabela ja com as features montadas.
        horizonte: Numero de semanas a frente a prever.

    Returns:
        COPIA da tabela com as colunas y_h, alvo_sin e alvo_cos.
    """
    grupos_por_fonte = tabela.groupby("fonte", group_keys=False)
    tabela_com_alvo = tabela.copy()
    tabela_com_alvo["y_h"] = grupos_por_fonte["casos_confirmados"].shift(-horizonte)
    semana_alvo = grupos_por_fonte["semana"].shift(-horizonte)
    tabela_com_alvo["alvo_sin"] = np.sin(2 * np.pi * semana_alvo / SEMANAS_POR_ANO)
    tabela_com_alvo["alvo_cos"] = np.cos(2 * np.pi * semana_alvo / SEMANAS_POR_ANO)
    return tabela_com_alvo


def selecionar_clima_enxuto(
    tabela: pd.DataFrame,
    colunas_nucleo: list[str],
    colunas_clima: list[str],
) -> list[str]:
    """Escolhe as NUMERO_FEATURES_CLIMA colunas de clima mais importantes.

    Soma o ganho (feature_importance por 'gain') de cada coluna de clima em tres
    horizontes (1, 4 e 8 semanas), treinando em 60% inicial dos pontos validos de
    cada horizonte, e retorna as de maior importancia acumulada.

    Args:
        tabela: Tabela ja com as features montadas.
        colunas_nucleo: Colunas do nucleo (sempre presentes).
        colunas_clima: Colunas candidatas de clima a ranquear.

    Returns:
        Lista com as NUMERO_FEATURES_CLIMA colunas de clima mais importantes.
    """
    importancia_acumulada = pd.Series(0.0, index=colunas_clima)
    for horizonte in HORIZONTES_SELECAO_CLIMA:
        tabela_com_alvo = construir_alvo_horizonte(tabela, horizonte)
        features = colunas_nucleo + colunas_clima + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            tabela_com_alvo.dropna(subset=features + ["y_h"])
            .sort_values("data_inicio_semana_epidemi")
            .reset_index(drop=True)
        )
        tamanho_treino = int(len(dados_validos) * FRACAO_TREINO_SELECAO_CLIMA)
        treino = dados_validos.iloc[:tamanho_treino]

        modelo = LGBMRegressor(**PARAMETROS_LGBM).fit(treino[features], treino["y_h"])
        importancia_por_feature = pd.Series(
            modelo.booster_.feature_importance(importance_type="gain"),
            index=features,
        )
        importancia_do_clima = importancia_por_feature.reindex(colunas_clima).fillna(0)
        importancia_acumulada = importancia_acumulada.add(
            importancia_do_clima, fill_value=0
        )

    clima_ordenado = importancia_acumulada.sort_values(ascending=False)
    return clima_ordenado.head(NUMERO_FEATURES_CLIMA).index.tolist()


def calcular_erros_pareados(
    tabela: pd.DataFrame,
    colunas_m0: list[str],
    colunas_m1: list[str],
    horizonte: int,
    minimo_treino: int = MINIMO_SEMANAS_TREINO,
    passo: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Treina M0 e M1 nos MESMOS pontos e retorna os erros pareados.

    Os pontos validos sao definidos pelo dropna da uniao das features de M1
    (superset que inclui M0 + vetor), garantindo pareamento. Em cada passo do
    walk-forward expansivel, treina ate o ponto i e preve o ponto i, para os dois
    modelos.

    Args:
        tabela: Tabela ja com as features montadas.
        colunas_m0: Features do modelo baseline (nucleo + clima).
        colunas_m1: Features do modelo com vetor (superset de M0).
        horizonte: Numero de semanas a frente a prever.
        minimo_treino: Tamanho minimo do treino antes de comecar a prever.
        passo: Espacamento entre os pontos de teste.

    Returns:
        Par (erros_m0, erros_m1), arrays de erro (y - previsao) por ponto de teste.
    """
    tabela_com_alvo = construir_alvo_horizonte(tabela, horizonte)
    features_m1 = colunas_m1 + ["alvo_sin", "alvo_cos"]      # superset (M0 + vetor)
    features_m0 = colunas_m0 + ["alvo_sin", "alvo_cos"]
    dados_validos = (
        tabela_com_alvo.dropna(subset=features_m1 + ["y_h"])
        .sort_values("data_inicio_semana_epidemi")
        .reset_index(drop=True)
    )

    erros_m0 = []
    erros_m1 = []
    for indice_corte in range(minimo_treino, len(dados_validos), passo):
        treino = dados_validos.iloc[:indice_corte]
        teste = dados_validos.iloc[indice_corte:indice_corte + 1]

        previsao_m0 = (
            LGBMRegressor(**PARAMETROS_LGBM)
            .fit(treino[features_m0], treino["y_h"])
            .predict(teste[features_m0])[0]
        )
        previsao_m1 = (
            LGBMRegressor(**PARAMETROS_LGBM)
            .fit(treino[features_m1], treino["y_h"])
            .predict(teste[features_m1])[0]
        )
        valor_real = teste["y_h"].values[0]
        erros_m0.append(valor_real - previsao_m0)
        erros_m1.append(valor_real - previsao_m1)
    return np.array(erros_m0), np.array(erros_m1)


def autocovariancia(desvios: np.ndarray, defasagem: int, numero_observacoes: int) -> float:
    """Autocovariancia amostral (divisao por n) da serie ja centrada em zero."""
    produto_defasado = desvios[defasagem:] * desvios[:numero_observacoes - defasagem]
    return np.sum(produto_defasado) / numero_observacoes


def testar_diebold_mariano(
    erros_m0: np.ndarray,
    erros_m1: np.ndarray,
    horizonte: int,
    tipo_perda: str = PERDA_QUADRATICA,
) -> ResultadoDieboldMariano:
    """Aplica o teste de Diebold-Mariano com variancia HAC e correcao HLN.

    A diferenca de perda e d = perda(M0) - perda(M1) (perda quadratica ou
    absoluta). A variancia usa Newey-West truncado no lag h-1. Aplica a correcao
    de amostra pequena Harvey-Leybourne-Newbold e compara a t(n-1), unilateral
    (H1: M1 erra menos, d_bar > 0).

    Args:
        erros_m0: Erros do baseline.
        erros_m1: Erros do modelo com vetor.
        horizonte: Numero de passos a frente (define o truncamento HAC).
        tipo_perda: PERDA_QUADRATICA ('sq') ou PERDA_ABSOLUTA ('abs').

    Returns:
        ResultadoDieboldMariano. Quando a variancia HAC nao e positiva, retorna
        estatistica e p-valor NaN.
    """
    if tipo_perda == PERDA_QUADRATICA:
        diferenca_perda = erros_m0**2 - erros_m1**2
    else:
        diferenca_perda = np.abs(erros_m0) - np.abs(erros_m1)

    numero_observacoes = len(diferenca_perda)
    diferenca_media = diferenca_perda.mean()
    desvios = diferenca_perda - diferenca_media

    variancia = autocovariancia(desvios, 0, numero_observacoes)
    for defasagem in range(1, horizonte):
        variancia += 2 * autocovariancia(desvios, defasagem, numero_observacoes)

    if variancia <= 0:
        return ResultadoDieboldMariano(
            diferenca_media, np.nan, np.nan, numero_observacoes
        )

    estatistica = diferenca_media / np.sqrt(variancia / numero_observacoes)
    correcao_hln = (
        numero_observacoes
        + 1
        - 2 * horizonte
        + horizonte * (horizonte - 1) / numero_observacoes
    ) / numero_observacoes
    estatistica *= np.sqrt(max(correcao_hln, PISO_CORRECAO_HLN))
    valor_p = stats.t.cdf(-estatistica, df=numero_observacoes - 1)
    return ResultadoDieboldMariano(
        diferenca_media, estatistica, valor_p, numero_observacoes
    )


def classificar_significancia(menor_valor_p: float) -> str:
    """Traduz o menor p-valor (sq/abs) nas estrelas de significancia.

    Segue os mesmos limiares do relatorio (0.01/0.05/0.10). Um p-valor NaN cai em
    todas as comparacoes 'menor que' como False e resulta em string vazia.
    """
    if menor_valor_p < LIMIAR_P_ALTISSIMA:
        return "***"
    if menor_valor_p < LIMIAR_P_ALTA:
        return "**"
    if menor_valor_p < LIMIAR_P_MODERADA:
        return "*"
    return ""


def imprimir_relatorio_de_versao(
    tabela: pd.DataFrame,
    colunas_nucleo: list[str],
    colunas_clima: list[str],
    colunas_vetor: list[str],
    titulo_versao: str,
) -> None:
    """Roda o teste DM por horizonte de uma versao do alvo e imprime a tabela.

    Seleciona o clima_enxuto, monta M0 (nucleo + clima) e M1 (M0 + vetor), e para
    cada horizonte de 1 a 12 imprime dMAE, estatistica e p-valor das perdas
    quadratica e absoluta, mais as estrelas de significancia.

    Args:
        tabela: Tabela ja com as features montadas.
        colunas_nucleo: Colunas do nucleo.
        colunas_clima: Colunas candidatas de clima.
        colunas_vetor: Colunas de vetor.
        titulo_versao: Titulo da versao (com/sem corte) exibido no cabecalho.
    """
    clima_enxuto = selecionar_clima_enxuto(tabela, colunas_nucleo, colunas_clima)
    features_m0 = colunas_nucleo + clima_enxuto
    features_m1 = colunas_nucleo + clima_enxuto + colunas_vetor

    print(f"\n================ {titulo_versao} ================")
    print("clima_enxuto:", clima_enxuto)
    print(
        f"{'h':>3} {'n':>4} {'dMAE':>7} {'DM(sq)':>8} {'p_sq':>8} "
        f"{'DM(abs)':>8} {'p_abs':>8}  sig?"
    )
    for horizonte in HORIZONTES_TESTE:
        erros_m0, erros_m1 = calcular_erros_pareados(
            tabela, features_m0, features_m1, horizonte
        )
        diferenca_mae = np.abs(erros_m0).mean() - np.abs(erros_m1).mean()  # >0 => vetor melhor
        resultado_sq = testar_diebold_mariano(
            erros_m0, erros_m1, horizonte, PERDA_QUADRATICA
        )
        resultado_abs = testar_diebold_mariano(
            erros_m0, erros_m1, horizonte, PERDA_ABSOLUTA
        )
        menor_valor_p = min(resultado_sq.valor_p, resultado_abs.valor_p)
        significancia = classificar_significancia(menor_valor_p)
        print(
            f"{horizonte:>3} {resultado_sq.numero_observacoes:>4} "
            f"{diferenca_mae:>+7.2f} {resultado_sq.estatistica:>8.2f} "
            f"{resultado_sq.valor_p:>8.3f} {resultado_abs.estatistica:>8.2f} "
            f"{resultado_abs.valor_p:>8.3f}  {significancia}"
        )


def main() -> None:
    """Roda o teste DM nas duas versoes do alvo (sem e com corte de maturidade)."""
    for aplicar_corte_maturidade in (False, True):
        if aplicar_corte_maturidade:
            titulo_versao = "COM corte de maturidade (Modelo 4c)"
        else:
            titulo_versao = "SEM corte (Modelo 4b)"
        tabela, colunas_nucleo, colunas_clima, colunas_vetor = montar_tabela(
            aplicar_corte_maturidade
        )
        imprimir_relatorio_de_versao(
            tabela, colunas_nucleo, colunas_clima, colunas_vetor, titulo_versao
        )
    print(
        "\np = prob. de a vantagem do vetor ser acaso (unilateral, H1: vetor erra "
        "menos). *** p<0.01  ** p<0.05  * p<0.10"
    )


if __name__ == "__main__":
    main()
