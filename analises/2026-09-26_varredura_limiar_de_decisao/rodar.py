"""Varredura do limiar de decisao e estagios oficiais — 26/09/2026.

POR QUE ESTE SCRIPT EXISTE

  Copia estendida de `analises/2026-09-25_alarme_contra_canal_endemico/rodar.py`
  (o original NAO foi alterado). A pre-declaracao desta rodada e
  `PRE_DECLARACAO.md` nesta mesma pasta (com a emenda 1) — leitura obrigatoria
  antes de qualquer numero.

  O achado que motiva a extensao (linha ~565 do original): o alarme do modelo
  comparava a previsao contra o MESMO limite do evento (`definicao_evento.
  limite_alvo`). O limiar de DECISAO (o que a previsao precisa passar para
  disparar) e o limiar do EVENTO (o que o real precisa passar para ser
  "semana de surto") sao coisas diferentes, e nunca foram separados. Esta
  versao separa os dois: o evento fica fixo (E_421 na Parte A; E_100/E_140/
  E_421/E_702 na Parte B) e o limiar de decisao dos modelos passa a ser um
  parametro explicito (`limite_decisao`).

  Partes novas, nesta ordem de execucao (nao a de leitura do resultado):
    D — trava (roda primeiro, antes de qualquer numero ser lido);
    A — varredura descritiva do limiar de decisao, evento fixo em E_421;
    B — os 4 estagios oficiais como evento, com McNemar confirmatorio em
        E_421 somado a familia de Holm ja aberta em 25/09;
    C — bloco-bootstrap da inflacao do p, sobre os testes de E_421 (e, se
        localizada, a previsao do teste de 13/09 que sobrevive a Holm).

  Nenhum modelo e treinado aqui. Sao lidas previsoes ja salvas (bateria noturna de
  23/09/2026, bloco 7) e a serie de casos confirmados (tabela_final.csv), e
  calculadas estatisticas descritivas e testes de McNemar pareados.

DEFINICOES, FIXADAS ANTES DE OLHAR O RESULTADO (ver PRE_DECLARACAO.md para o texto
completo e as referencias bibliograficas)

  Dois eventos de "semana de surto":
    E_100   real > 100 casos (a definicao de 13/09/2026, para travar contra ela).
    E_canal real acima do limite superior do canal endemico da semana
            epidemiologica, calculado com todos os anos anteriores disponiveis
            desde 2018 (minimo 3 anos). Canal principal: C_log (Singh et al.
            2026). Secundarios, descritivos: C_conv e C_p75.

  Cinco regras de alarme, emitidas na semana de origem t para a semana t+h:
    M_adotado         previsao do cenario adotado (branco 'referencia') em t+h
                       passa do limite do evento.
    M_folha20         previsao do HistGB folha minima 20 (branco
                       'HistGB_folha20_M1') em t+h passa do limite do evento.
    R_hoje            real[t] passa do limite da SEMANA t (o mesmo tipo de canal,
                       calculado para a semana de origem).
    R_hoje_crescendo  R_hoje E real[t] > real[t-1].
    R_ano_passado     real[t+h-52] passa do limite da semana t+h (o limite do
                       ALVO, nao o da semana do ano passado).

  Metricas: sensibilidade, precisao, especificidade, falsos por ano, indice de
  Youden (sensibilidade + especificidade - 1). Horizontes 1, 4, 8 e 12 semanas.
  Periodo de avaliacao: data_alvo >= 2024-01-01. Periodo de calibracao epidemica
  2022-2023: so descritivo.

  Teste: McNemar exato, pareado por semana (data_alvo), sobre acerto/erro da
  classificacao de cada modelo contra R_hoje e contra R_ano_passado, em h=4 e
  h=12, nos eventos E_100 e E_canal (canal C_log). Familia de 16 comparacoes,
  correcao de Holm.

Uso:  python3 rodar.py
"""

import dataclasses
import logging
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import scipy.stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend precisa ser fixado antes)


# ---------------------------------------------------------------------------
# CONFIGURACAO EXPLICITA
# ---------------------------------------------------------------------------

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PROJETO = PASTA_ANALISE.parent.parent
PASTA_SAIDAS = PASTA_ANALISE / "saidas"

CAMINHO_PREVISOES = (
    PASTA_PROJETO
    / "analises"
    / "2026-09-23_bateria_noturna"
    / "bloco_7_vetor_com_folha_20"
    / "saidas"
    / "previsoes_por_braco.csv"
)

CAMINHO_TABELA_FINAL = (
    PASTA_PROJETO
    / "modelagem_aedes"
    / "dados"
    / "entradas"
    / "tabela_modelagem"
    / "tabela_final.csv"
)

COLUNAS_TABELA_FINAL = [
    "data_inicio_semana_epidemi",
    "semana",
    "ano",
    "casos_confirmados",
]

BRACO_MODELO_ADOTADO = "referencia"
BRACO_MODELO_FOLHA20 = "HistGB_folha20_M1"
NOME_MODELO_ADOTADO = "M_adotado"
NOME_MODELO_FOLHA20 = "M_folha20"

MAPA_BRACO_PARA_MODELO = {
    BRACO_MODELO_ADOTADO: NOME_MODELO_ADOTADO,
    BRACO_MODELO_FOLHA20: NOME_MODELO_FOLHA20,
}

LIMITE_E100 = 100.0
ANO_MINIMO_CANAL = 2018
MINIMO_ANOS_CANAL = 3

INICIO_AVALIACAO = pd.Timestamp("2024-01-01")
FIM_AVALIACAO = pd.Timestamp("2100-01-01")  # sem teto: pega tudo que houver
INICIO_CALIBRACAO = pd.Timestamp("2022-01-01")
FIM_CALIBRACAO = pd.Timestamp("2023-12-31")

NOME_PERIODO_AVALIACAO = "avaliacao_2024_mais"
NOME_PERIODO_CALIBRACAO = "calibracao_2022_2023"

HORIZONTES_TODOS = (1, 4, 8, 12)
HORIZONTES_MCNEMAR = (4, 12)

NOME_EVENTO_100 = "E_100"
NOME_EVENTO_CANAL = "E_canal"

CANAL_LOG = "C_log"
CANAL_CONVENCIONAL = "C_conv"
CANAL_PERCENTIL75 = "C_p75"
CANAIS_TODOS = (CANAL_LOG, CANAL_CONVENCIONAL, CANAL_PERCENTIL75)

REGRA_M_ADOTADO = "M_adotado"
REGRA_M_FOLHA20 = "M_folha20"
REGRA_R_HOJE = "R_hoje"
REGRA_R_HOJE_CRESCENDO = "R_hoje_crescendo"
REGRA_R_ANO_PASSADO = "R_ano_passado"
REGRAS_TODAS = (
    REGRA_M_ADOTADO,
    REGRA_M_FOLHA20,
    REGRA_R_HOJE,
    REGRA_R_HOJE_CRESCENDO,
    REGRA_R_ANO_PASSADO,
)
REGRAS_BASE_PARA_MCNEMAR = (REGRA_R_HOJE, REGRA_R_ANO_PASSADO)
MODELOS_PARA_MCNEMAR = (REGRA_M_ADOTADO, REGRA_M_FOLHA20)

ALFA_HOLM = 0.05


@dataclasses.dataclass(frozen=True)
class ValoresEsperadosTrava:
    """Numeros que o cenario adotado (evento E_100) tem de reproduzir.

    Vieram do script de 13/09/2026 (medir_alarme.py), avaliacao 2024+.
    """

    h: int
    sensibilidade: float
    precisao: float
    falsos_por_ano: float


TRAVA_H4 = ValoresEsperadosTrava(h=4, sensibilidade=0.971, precisao=0.943, falsos_por_ano=0.7)
TRAVA_H12 = ValoresEsperadosTrava(h=12, sensibilidade=0.769, precisao=0.811, falsos_por_ano=2.3)
TOLERANCIA_TRAVA_PROPORCAO = 0.002
TOLERANCIA_TRAVA_FALSOS_POR_ANO = 0.05

# ---------------------------------------------------------------------------
# CONFIGURACAO NOVA — varredura do limiar de decisao (Parte A) e estagios (B)
# ---------------------------------------------------------------------------

NOME_EVENTO_140 = "E_140"
NOME_EVENTO_421 = "E_421"
NOME_EVENTO_702 = "E_702"

# Limiares fixos dos 4 estagios oficiais do plano municipal (piso de cada
# estagio, em casos confirmados/semana). E_100 e o corte legado de 13/09/2026,
# mantido para a trava; os outros 3 sao o Quadro 1 do plano.
LIMIARES_EVENTOS_CONSTANTES = {
    NOME_EVENTO_100: LIMITE_E100,
    NOME_EVENTO_140: 140.0,
    NOME_EVENTO_421: 421.0,
    NOME_EVENTO_702: 702.0,
}

EVENTO_CONFIRMATORIO = NOME_EVENTO_421
EVENTOS_DESCRITIVOS_ESTAGIOS = (NOME_EVENTO_100, NOME_EVENTO_140, NOME_EVENTO_702)

# Grade de limiares de DECISAO varrida na Parte A — parametro livre do
# alarme, independente do limiar do evento (que fica fixo em E_421=421).
GRADE_LIMIARES_DECISAO = (25, 50, 75, 100, 140, 200, 300, 421, 600, 702, 900, 1200)
LIMIAR_DECISAO_REFERENCIA_HOJE = 421.0  # a regra de hoje: D == limite do evento

MODELOS_PARA_VARREDURA = (REGRA_M_ADOTADO, REGRA_M_FOLHA20)

# Caminho da familia de McNemar ja aberta em 25/09/2026 (16 comparacoes), a
# qual a familia confirmatoria de E_421 (8 comparacoes novas) se soma para
# formar a familia de Holm de 24 comparacoes.
CAMINHO_MCNEMAR_25_09 = (
    PASTA_PROJETO
    / "analises"
    / "2026-09-25_alarme_contra_canal_endemico"
    / "saidas"
    / "mcnemar_holm.csv"
)

# Bloco-bootstrap da inflacao do p (Parte C).
COMPRIMENTOS_BLOCO_BOOTSTRAP = (4, 8, 13, 26)
N_REAMOSTRAGENS_BOOTSTRAP = 2000
SEMENTE_BOOTSTRAP = 20260926


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("alarme_contra_canal_endemico")


# ---------------------------------------------------------------------------
# CARGA DE DADOS
# ---------------------------------------------------------------------------


def carregar_serie_semanal(caminho_tabela_final: Path) -> pd.DataFrame:
    """Le a serie semanal de casos confirmados de Porto Alegre.

    Args:
        caminho_tabela_final: Caminho do `tabela_final.csv` do pipeline.

    Returns:
        DataFrame ordenado por data, com colunas `data`, `ano`, `semana` e
        `casos_confirmados` (float, com NaN nas semanas sem numero confirmado
        ainda, por exemplo antes de 18/02/2018 ou nas semanas mais recentes de
        2026 ainda nao fechadas).
    """
    dados_brutos = pd.read_csv(caminho_tabela_final, usecols=COLUNAS_TABELA_FINAL)
    dados_brutos["data"] = pd.to_datetime(dados_brutos["data_inicio_semana_epidemi"])

    serie_semanal = dados_brutos[["data", "ano", "semana", "casos_confirmados"]].copy()
    serie_semanal = serie_semanal.sort_values("data").reset_index(drop=True)

    duplicatas_ano_semana = serie_semanal.duplicated(subset=["ano", "semana"]).sum()
    if duplicatas_ano_semana > 0:
        raise ValueError(
            f"tabela_final.csv tem {duplicatas_ano_semana} pares (ano, semana) "
            "duplicados; o canal por semana epidemiologica exige unicidade."
        )

    log.info(
        "Serie semanal carregada: %d semanas, de %s a %s (%d com casos_confirmados nulo).",
        len(serie_semanal),
        serie_semanal["data"].min().date(),
        serie_semanal["data"].max().date(),
        serie_semanal["casos_confirmados"].isna().sum(),
    )
    return serie_semanal


def carregar_previsoes_dos_bracos(caminho_previsoes: Path) -> pd.DataFrame:
    """Le as previsoes do bloco 7 da bateria noturna e mantem so os 2 bracos usados.

    Args:
        caminho_previsoes: Caminho de `previsoes_por_braco.csv`.

    Returns:
        DataFrame com colunas `h`, `data_alvo`, `real`, `previsto`, `modelo`
        (`M_adotado` ou `M_folha20`), so com os bracos 'referencia' e
        'HistGB_folha20_M1'.
    """
    previsoes_brutas = pd.read_csv(caminho_previsoes)
    previsoes_brutas["data_alvo"] = pd.to_datetime(previsoes_brutas["data_alvo"])

    mascara_bracos_usados = previsoes_brutas["braco"].isin(MAPA_BRACO_PARA_MODELO.keys())
    previsoes_filtradas = previsoes_brutas[mascara_bracos_usados].copy()
    previsoes_filtradas["modelo"] = previsoes_filtradas["braco"].map(MAPA_BRACO_PARA_MODELO)

    if previsoes_filtradas["previsto"].isna().any() or previsoes_filtradas["real"].isna().any():
        raise ValueError("previsoes_por_braco.csv tem valores nulos em 'previsto' ou 'real'.")

    log.info(
        "Previsoes carregadas: %d linhas (%d por modelo), h de %d a %d, data_alvo de %s a %s.",
        len(previsoes_filtradas),
        previsoes_filtradas.groupby("modelo").size().min(),
        previsoes_filtradas["h"].min(),
        previsoes_filtradas["h"].max(),
        previsoes_filtradas["data_alvo"].min().date(),
        previsoes_filtradas["data_alvo"].max().date(),
    )
    return previsoes_filtradas


# ---------------------------------------------------------------------------
# CANAL ENDEMICO
# ---------------------------------------------------------------------------


def calcular_limite_canal_log(casos_anos_anteriores: np.ndarray) -> float:
    """Limite superior do canal em escala log (Singh et al. 2026).

    Formula: expm1(media + 2 desvios-padrao de log1p(casos)). O desvio-padrao
    usa ddof=1 (amostral), a convencao padrao do projeto para estatistica
    descritiva sobre poucos anos.
    """
    casos_em_log = np.log1p(casos_anos_anteriores)
    media_log = casos_em_log.mean()
    desvio_log = casos_em_log.std(ddof=1)
    limite = np.expm1(media_log + 2.0 * desvio_log)
    return float(limite)


def calcular_limite_canal_convencional(casos_anos_anteriores: np.ndarray) -> float:
    """Limite superior do canal convencional: media + 2 desvios-padrao (ddof=1)."""
    media = casos_anos_anteriores.mean()
    desvio = casos_anos_anteriores.std(ddof=1)
    limite = media + 2.0 * desvio
    return float(limite)


def calcular_limite_canal_percentil75(casos_anos_anteriores: np.ndarray) -> float:
    """Limite superior do canal por percentil 75 empirico (interpolacao linear).

    Simplificacao declarada na pre-declaracao: o sistema do CDC Dengue Branch
    usa binomial negativa; aqui o percentil e calculado direto sobre a amostra
    de anos anteriores.
    """
    limite = np.percentile(casos_anos_anteriores, 75)
    return float(limite)


def construir_canais_por_semana_epidemiologica(
    serie_semanal: pd.DataFrame,
    ano_minimo: int,
    minimo_anos: int,
) -> pd.DataFrame:
    """Calcula os 3 canais para toda semana epidemiologica (ano, semana) da serie.

    Para a semana `w` do ano `Y`, usa os casos confirmados da mesma semana `w`
    em todos os anos anteriores disponiveis, de `ano_minimo` ate `Y-1`,
    descartando anos com casos_confirmados nulo. Se sobrarem menos de
    `minimo_anos` anos, os 3 limites ficam NaN (semana sem canal definido).

    Args:
        serie_semanal: Saida de `carregar_serie_semanal`.
        ano_minimo: Primeiro ano que entra na base do canal (2018, pela
            adaptacao declarada: antes disso os casos sao proximos de zero e
            nao representam ausencia real de epidemia).
        minimo_anos: Numero minimo de anos anteriores validos para definir o
            canal.

    Returns:
        DataFrame indexado por (ano, semana) com `limite_c_log`,
        `limite_c_conv`, `limite_c_p75` e `n_anos_usados`.
    """
    linhas_do_canal: list[dict[str, float | int]] = []

    semanas_ano_disponiveis = serie_semanal[["ano", "semana", "casos_confirmados"]]

    for ano_semana, grupo_da_semana in semanas_ano_disponiveis.groupby("semana"):
        numero_da_semana = ano_semana
        grupo_ordenado = grupo_da_semana.sort_values("ano")

        for ano_alvo in grupo_ordenado["ano"].unique():
            mascara_anos_anteriores = (
                (grupo_ordenado["ano"] >= ano_minimo)
                & (grupo_ordenado["ano"] < ano_alvo)
                & (grupo_ordenado["casos_confirmados"].notna())
            )
            casos_anos_anteriores = grupo_ordenado.loc[
                mascara_anos_anteriores, "casos_confirmados"
            ].to_numpy()
            n_anos_usados = len(casos_anos_anteriores)

            if n_anos_usados < minimo_anos:
                limite_log = np.nan
                limite_conv = np.nan
                limite_p75 = np.nan
            else:
                limite_log = calcular_limite_canal_log(casos_anos_anteriores)
                limite_conv = calcular_limite_canal_convencional(casos_anos_anteriores)
                limite_p75 = calcular_limite_canal_percentil75(casos_anos_anteriores)

            linhas_do_canal.append({
                "ano": ano_alvo,
                "semana": numero_da_semana,
                "n_anos_usados": n_anos_usados,
                "limite_c_log": limite_log,
                "limite_c_conv": limite_conv,
                "limite_c_p75": limite_p75,
            })

    canais = pd.DataFrame(linhas_do_canal)
    canais = canais.set_index(["ano", "semana"]).sort_index()

    n_semanas_sem_canal = canais["limite_c_log"].isna().sum()
    log.info(
        "Canais calculados para %d semanas epidemiologicas (ano>=%d); "
        "%d ficaram sem canal por terem menos de %d anos anteriores validos.",
        len(canais),
        ano_minimo,
        n_semanas_sem_canal,
        minimo_anos,
    )
    if n_semanas_sem_canal > 0:
        semanas_sem_canal = canais[canais["limite_c_log"].isna()].index.tolist()
        log.info(
            "Semanas (ano, semana) sem canal definido (n_anos_usados < %d): %s",
            minimo_anos,
            semanas_sem_canal,
        )
    return canais


def montar_tabela_semanal_enriquecida(
    serie_semanal: pd.DataFrame,
    canais_por_semana: pd.DataFrame,
) -> pd.DataFrame:
    """Junta a serie de casos com os limites de canal, indexado pela data.

    Returns:
        DataFrame indexado por `data`, com `ano`, `semana`, `casos_confirmados`,
        `limite_c_log`, `limite_c_conv`, `limite_c_p75`, `n_anos_usados`.
    """
    serie_indexada = serie_semanal.set_index(["ano", "semana"])
    tabela_enriquecida = serie_indexada.join(canais_por_semana, how="left")
    tabela_enriquecida = tabela_enriquecida.reset_index().set_index("data").sort_index()
    return tabela_enriquecida


# ---------------------------------------------------------------------------
# MONTAGEM DA TABELA DE AVALIACAO (uma linha por h, data_alvo)
# ---------------------------------------------------------------------------


def buscar_valor_na_serie(
    tabela_semanal: pd.DataFrame,
    datas: pd.Series,
    coluna: str,
) -> pd.Series:
    """Busca o valor de `coluna` na `tabela_semanal`, para cada data de `datas`.

    Datas fora do indice da tabela semanal (fora do intervalo 2012-2026)
    retornam NaN, sem lancar excecao — a validade e checada explicitamente por
    quem chama, contando quantas buscas vieram vazias.
    """
    valores = tabela_semanal[coluna].reindex(datas.to_numpy())
    return pd.Series(valores.to_numpy(), index=datas.index)


def montar_tabela_de_avaliacao(
    previsoes: pd.DataFrame,
    tabela_semanal: pd.DataFrame,
) -> pd.DataFrame:
    """Monta uma linha por (h, data_alvo) com tudo que as 5 regras precisam.

    Colunas produzidas:
        h, data_alvo, real_alvo, ano_alvo,
        previsto_M_adotado, previsto_M_folha20,
        limite_c_log_alvo, limite_c_conv_alvo, limite_c_p75_alvo,
        data_origem, real_origem,
        limite_c_log_origem, limite_c_conv_origem, limite_c_p75_origem,
        real_origem_menos_1, real_ano_passado.

    `data_origem` = data_alvo - h semanas. `real_ano_passado` = real na data
    (data_alvo - 52 semanas), a mesma semana do ano anterior.
    """
    previsoes_pivotadas = previsoes.pivot_table(
        index=["h", "data_alvo"],
        columns="modelo",
        values="previsto",
        aggfunc="first",
    )
    previsoes_pivotadas.columns = [f"previsto_{nome_modelo}" for nome_modelo in previsoes_pivotadas.columns]
    previsoes_pivotadas = previsoes_pivotadas.reset_index()

    real_por_h_e_alvo = previsoes.groupby(["h", "data_alvo"])["real"].first().reset_index()
    real_por_h_e_alvo = real_por_h_e_alvo.rename(columns={"real": "real_alvo"})

    tabela = previsoes_pivotadas.merge(real_por_h_e_alvo, on=["h", "data_alvo"], how="inner")

    tabela["data_origem"] = tabela["data_alvo"] - pd.to_timedelta(tabela["h"] * 7, unit="D")
    tabela["data_origem_menos_1"] = tabela["data_origem"] - pd.Timedelta(days=7)
    tabela["data_ano_passado"] = tabela["data_alvo"] - pd.Timedelta(weeks=52)

    tabela["ano_alvo"] = buscar_valor_na_serie(tabela_semanal, tabela["data_alvo"], "ano")
    tabela["limite_c_log_alvo"] = buscar_valor_na_serie(tabela_semanal, tabela["data_alvo"], "limite_c_log")
    tabela["limite_c_conv_alvo"] = buscar_valor_na_serie(tabela_semanal, tabela["data_alvo"], "limite_c_conv")
    tabela["limite_c_p75_alvo"] = buscar_valor_na_serie(tabela_semanal, tabela["data_alvo"], "limite_c_p75")

    tabela["real_origem"] = buscar_valor_na_serie(tabela_semanal, tabela["data_origem"], "casos_confirmados")
    tabela["limite_c_log_origem"] = buscar_valor_na_serie(tabela_semanal, tabela["data_origem"], "limite_c_log")
    tabela["limite_c_conv_origem"] = buscar_valor_na_serie(tabela_semanal, tabela["data_origem"], "limite_c_conv")
    tabela["limite_c_p75_origem"] = buscar_valor_na_serie(tabela_semanal, tabela["data_origem"], "limite_c_p75")

    tabela["real_origem_menos_1"] = buscar_valor_na_serie(
        tabela_semanal, tabela["data_origem_menos_1"], "casos_confirmados"
    )
    tabela["real_ano_passado"] = buscar_valor_na_serie(
        tabela_semanal, tabela["data_ano_passado"], "casos_confirmados"
    )

    # Checagem de consistencia: o 'real_alvo' das previsoes tem de bater com o
    # casos_confirmados da tabela_final na mesma data (mesma fonte de verdade).
    real_alvo_pela_tabela = buscar_valor_na_serie(tabela_semanal, tabela["data_alvo"], "casos_confirmados")
    divergencia_real = (tabela["real_alvo"] - real_alvo_pela_tabela).abs()
    n_divergentes = int((divergencia_real > 1e-6).sum())
    if n_divergentes > 0:
        raise ValueError(
            f"{n_divergentes} linhas com 'real' das previsoes divergindo de "
            "casos_confirmados da tabela_final na mesma data_alvo."
        )

    n_origem_sem_real = int(tabela["real_origem"].isna().sum())
    n_origem_menos_1_sem_real = int(tabela["real_origem_menos_1"].isna().sum())
    n_ano_passado_sem_real = int(tabela["real_ano_passado"].isna().sum())
    log.info(
        "Tabela de avaliacao montada: %d linhas. Sem 'real' na origem: %d. "
        "Sem 'real' na origem-1: %d. Sem 'real' do ano passado: %d.",
        len(tabela),
        n_origem_sem_real,
        n_origem_menos_1_sem_real,
        n_ano_passado_sem_real,
    )
    return tabela


# ---------------------------------------------------------------------------
# EVENTOS E ALARMES
# ---------------------------------------------------------------------------


def obter_coluna_de_limite(canal: str) -> str:
    """Mapeia o nome do canal para o sufixo de coluna correspondente."""
    mapa_canal_para_coluna = {
        CANAL_LOG: "limite_c_log",
        CANAL_CONVENCIONAL: "limite_c_conv",
        CANAL_PERCENTIL75: "limite_c_p75",
    }
    if canal not in mapa_canal_para_coluna:
        raise ValueError(f"Canal desconhecido: {canal}")
    return mapa_canal_para_coluna[canal]


@dataclasses.dataclass(frozen=True)
class DefinicaoDeEvento:
    """Limite do alvo e limite da origem para um evento de 'semana de surto'.

    Para E_100 os dois limites sao a constante 100 e sempre validos. Para
    E_canal os limites vem do canal (log, convencional ou p75) calculado por
    semana epidemiologica, e podem ser NaN quando a semana nao tem anos
    anteriores suficientes.
    """

    limite_alvo: pd.Series
    limite_origem: pd.Series
    valido_alvo: pd.Series
    valido_origem: pd.Series


def montar_definicao_de_evento(tabela: pd.DataFrame, evento: str, canal: str | None) -> DefinicaoDeEvento:
    """Constroi os limites (alvo e origem) para o evento e canal pedidos.

    Para os eventos de limiar constante (E_100 e, a partir de 26/09/2026,
    E_140/E_421/E_702 — os 4 estagios do plano municipal), o limite e o mesmo
    numero para toda linha e sempre valido. So o evento E_canal depende da
    semana epidemiologica e pode ficar invalido (menos de 3 anos anteriores).
    """
    n_linhas = len(tabela)

    if evento in LIMIARES_EVENTOS_CONSTANTES:
        valor_constante = LIMIARES_EVENTOS_CONSTANTES[evento]
        limite_constante = pd.Series(np.full(n_linhas, valor_constante), index=tabela.index)
        validade_constante = pd.Series(np.full(n_linhas, True), index=tabela.index)
        return DefinicaoDeEvento(
            limite_alvo=limite_constante,
            limite_origem=limite_constante,
            valido_alvo=validade_constante,
            valido_origem=validade_constante,
        )

    if evento == NOME_EVENTO_CANAL:
        if canal is None:
            raise ValueError("Evento E_canal exige um canal (C_log, C_conv ou C_p75).")
        coluna_limite = obter_coluna_de_limite(canal)
        limite_alvo = tabela[f"{coluna_limite}_alvo"]
        limite_origem = tabela[f"{coluna_limite}_origem"]
        return DefinicaoDeEvento(
            limite_alvo=limite_alvo,
            limite_origem=limite_origem,
            valido_alvo=limite_alvo.notna(),
            valido_origem=limite_origem.notna(),
        )

    raise ValueError(f"Evento desconhecido: {evento}")


@dataclasses.dataclass(frozen=True)
class AlarmeDaRegra:
    """Alarme booleano de uma regra e a mascara de validade das linhas."""

    alarme: pd.Series
    valido: pd.Series


def calcular_alarmes_das_regras(
    tabela: pd.DataFrame,
    definicao_evento: DefinicaoDeEvento,
    limite_decisao: pd.Series | float | None = None,
) -> tuple[dict[str, AlarmeDaRegra], pd.Series]:
    """Calcula o alarme das 5 regras e a semana de surto (e_surto), por linha.

    A "semana de surto" (e_surto) e sempre `real_alvo > limite_alvo`: por isso
    toda regra exige `valido_alvo` (o limite do alvo precisa existir) para que
    a linha entre na conta. R_hoje e R_hoje_crescendo exigem tambem
    `valido_origem` (o limite da semana de origem). R_ano_passado exige que
    `real_ano_passado` nao seja nulo.

    Args:
        tabela: Tabela de avaliacao (uma linha por h, data_alvo).
        definicao_evento: Limites do EVENTO (o que o real precisa passar para
            ser "semana de surto"). Usado por `e_surto` e pelas 3 regras
            baseadas em valores reais (R_hoje, R_hoje_crescendo,
            R_ano_passado) — essas regras nao tem limiar de decisao proprio,
            porque decidem olhando o mesmo tipo de limite do evento.
        limite_decisao: Limiar de DECISAO dos dois modelos (M_adotado,
            M_folha20): o que a PREVISAO precisa passar para o alarme
            disparar. Parametro novo de 26/09/2026, separado do limiar do
            evento (achado que motivou esta rodada). Quando None (padrao,
            igual ao comportamento original de 25/09/2026), o limiar de
            decisao e o proprio `definicao_evento.limite_alvo` — a regra de
            hoje, em que decisao e evento sao colados.

    """
    limite_decisao_modelos = (
        definicao_evento.limite_alvo if limite_decisao is None else limite_decisao
    )

    e_surto = tabela["real_alvo"] > definicao_evento.limite_alvo

    alarme_m_adotado = tabela["previsto_M_adotado"] > limite_decisao_modelos
    valido_m_adotado = definicao_evento.valido_alvo

    alarme_m_folha20 = tabela["previsto_M_folha20"] > limite_decisao_modelos
    valido_m_folha20 = definicao_evento.valido_alvo

    alarme_r_hoje = tabela["real_origem"] > definicao_evento.limite_origem
    valido_r_hoje = definicao_evento.valido_alvo & definicao_evento.valido_origem & tabela["real_origem"].notna()

    origem_crescendo = tabela["real_origem"] > tabela["real_origem_menos_1"]
    alarme_r_hoje_crescendo = alarme_r_hoje & origem_crescendo
    valido_r_hoje_crescendo = valido_r_hoje & tabela["real_origem_menos_1"].notna()

    alarme_r_ano_passado = tabela["real_ano_passado"] > definicao_evento.limite_alvo
    valido_r_ano_passado = definicao_evento.valido_alvo & tabela["real_ano_passado"].notna()

    alarmes_por_regra = {
        REGRA_M_ADOTADO: AlarmeDaRegra(alarme=alarme_m_adotado, valido=valido_m_adotado),
        REGRA_M_FOLHA20: AlarmeDaRegra(alarme=alarme_m_folha20, valido=valido_m_folha20),
        REGRA_R_HOJE: AlarmeDaRegra(alarme=alarme_r_hoje, valido=valido_r_hoje),
        REGRA_R_HOJE_CRESCENDO: AlarmeDaRegra(alarme=alarme_r_hoje_crescendo, valido=valido_r_hoje_crescendo),
        REGRA_R_ANO_PASSADO: AlarmeDaRegra(alarme=alarme_r_ano_passado, valido=valido_r_ano_passado),
    }
    return alarmes_por_regra, e_surto


# ---------------------------------------------------------------------------
# METRICAS
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class MetricasDeAlarme:
    """Metricas descritivas de uma regra de alarme, para um recorte fixo."""

    n_semanas: int
    n_surto: int
    sensibilidade: float
    precisao: float
    especificidade: float
    falsos_por_ano: float
    youden: float


def calcular_metricas_de_alarme(
    e_surto: pd.Series,
    alarme: pd.Series,
    valido: pd.Series,
    anos: pd.Series,
) -> MetricasDeAlarme:
    """Calcula sensibilidade, precisao, especificidade, falsos/ano e Youden.

    So as linhas com `valido=True` entram na conta (limite do evento definido
    e, quando a regra precisa, valores de origem/ano-passado disponiveis).

    Fallbacks, decididos e registrados no log da execucao:
        - sem semana de surto no recorte -> sensibilidade NaN;
        - sem alarme algum no recorte -> precisao NaN (divisao por zero);
        - sem semana calma no recorte -> especificidade NaN;
        - sem ano no recorte -> falsos_por_ano NaN;
        - sensibilidade ou especificidade NaN -> Youden NaN.
    """
    e_surto_validado = e_surto[valido]
    alarme_validado = alarme[valido]
    anos_validados = anos[valido]

    n_semanas = int(valido.sum())
    n_surto = int(e_surto_validado.sum())
    n_calmas = n_semanas - n_surto

    n_alarmes = int(alarme_validado.sum())
    n_verdadeiros_positivos = int((e_surto_validado & alarme_validado).sum())
    n_falsos_positivos = int((~e_surto_validado & alarme_validado).sum())
    n_verdadeiros_negativos = n_calmas - n_falsos_positivos

    n_anos_no_recorte = int(anos_validados.nunique())

    sensibilidade = n_verdadeiros_positivos / n_surto if n_surto > 0 else np.nan
    precisao = n_verdadeiros_positivos / n_alarmes if n_alarmes > 0 else np.nan
    especificidade = n_verdadeiros_negativos / n_calmas if n_calmas > 0 else np.nan
    falsos_por_ano = n_falsos_positivos / n_anos_no_recorte if n_anos_no_recorte > 0 else np.nan

    if np.isnan(sensibilidade) or np.isnan(especificidade):
        youden = np.nan
    else:
        youden = sensibilidade + especificidade - 1.0

    return MetricasDeAlarme(
        n_semanas=n_semanas,
        n_surto=n_surto,
        sensibilidade=sensibilidade,
        precisao=precisao,
        especificidade=especificidade,
        falsos_por_ano=falsos_por_ano,
        youden=youden,
    )


def filtrar_por_periodo(tabela: pd.DataFrame, data_inicio: pd.Timestamp, data_fim: pd.Timestamp) -> pd.DataFrame:
    """Filtra a tabela de avaliacao por `data_alvo` dentro de [inicio, fim]."""
    mascara_periodo = (tabela["data_alvo"] >= data_inicio) & (tabela["data_alvo"] <= data_fim)
    return tabela[mascara_periodo]


@dataclasses.dataclass(frozen=True)
class ContagemDeBlocos:
    """Quantas semanas de surto existem no periodo, e em quantos blocos contiguos.

    Calculado direto sobre a serie REAL de casos confirmados por semana
    epidemiologica (independente de h e de modelo) — e uma propriedade do
    EVENTO, nao da previsao. Duas semanas de surto contam como o mesmo bloco
    quando sao semanas consecutivas na serie (sem exigencia de semanas calmas
    entre blocos: 26/09/2026 usa adjacencia estrita, e essa e a definicao que
    reproduz a ancora de C na pre-declaracao).
    """

    n_semanas_periodo: int
    n_surto: int
    n_blocos: int
    maior_bloco: int


def calcular_blocos_contiguos_por_evento(
    serie_semanal: pd.DataFrame,
    limite: float,
    data_inicio: pd.Timestamp,
    data_fim: pd.Timestamp,
) -> ContagemDeBlocos:
    """Conta semanas de surto e blocos contiguos, no periodo, para um limiar fixo.

    Usada pela Parte B para anexar `n_blocos_contiguos` as tabelas de metricas
    dos 4 estagios oficiais (E_100, E_140, E_421, E_702). So semanas com
    `casos_confirmados` nao nulo entram na conta — semanas em apuracao (corte
    de maturidade) nao contam nem como surto nem como bloco quebrado.

    Args:
        serie_semanal: Saida de `carregar_serie_semanal` (uma linha por data).
        limite: Limiar do evento (100, 140, 421 ou 702).
        data_inicio: Inicio do periodo (inclusive).
        data_fim: Fim do periodo (inclusive).

    Returns:
        `ContagemDeBlocos` com o total de semanas com dado, quantas sao de
        surto, em quantos blocos contiguos e o tamanho do maior bloco (0 se
        nao houver nenhuma semana de surto no periodo).
    """
    mascara_periodo = (
        (serie_semanal["data"] >= data_inicio)
        & (serie_semanal["data"] <= data_fim)
        & serie_semanal["casos_confirmados"].notna()
    )
    serie_do_periodo = serie_semanal[mascara_periodo].sort_values("data")

    indicador_surto = (serie_do_periodo["casos_confirmados"] > limite).to_numpy()

    tamanhos_dos_blocos: list[int] = []
    tamanho_do_bloco_atual = 0
    for semana_e_surto in indicador_surto:
        if semana_e_surto:
            tamanho_do_bloco_atual += 1
        else:
            if tamanho_do_bloco_atual > 0:
                tamanhos_dos_blocos.append(tamanho_do_bloco_atual)
            tamanho_do_bloco_atual = 0
    if tamanho_do_bloco_atual > 0:
        tamanhos_dos_blocos.append(tamanho_do_bloco_atual)

    return ContagemDeBlocos(
        n_semanas_periodo=len(serie_do_periodo),
        n_surto=int(indicador_surto.sum()),
        n_blocos=len(tamanhos_dos_blocos),
        maior_bloco=max(tamanhos_dos_blocos) if tamanhos_dos_blocos else 0,
    )


def construir_tabela_metricas_por_regra(tabela_avaliacao: pd.DataFrame) -> pd.DataFrame:
    """Monta metricas_por_regra.csv: uma linha por (evento, canal, regra, h, periodo)."""
    periodos = {
        NOME_PERIODO_AVALIACAO: (INICIO_AVALIACAO, FIM_AVALIACAO),
        NOME_PERIODO_CALIBRACAO: (INICIO_CALIBRACAO, FIM_CALIBRACAO),
    }

    combinacoes_de_evento: list[tuple[str, str | None]] = [(NOME_EVENTO_100, None)]
    for canal in CANAIS_TODOS:
        combinacoes_de_evento.append((NOME_EVENTO_CANAL, canal))

    linhas_de_resultado: list[dict[str, object]] = []

    for nome_periodo, (data_inicio, data_fim) in periodos.items():
        tabela_do_periodo = filtrar_por_periodo(tabela_avaliacao, data_inicio, data_fim)

        for h in HORIZONTES_TODOS:
            tabela_h = tabela_do_periodo[tabela_do_periodo["h"] == h]

            for evento, canal in combinacoes_de_evento:
                definicao_evento = montar_definicao_de_evento(tabela_h, evento, canal)
                alarmes_por_regra, e_surto = calcular_alarmes_das_regras(tabela_h, definicao_evento)

                for regra in REGRAS_TODAS:
                    alarme_da_regra = alarmes_por_regra[regra]
                    metricas = calcular_metricas_de_alarme(
                        e_surto=e_surto,
                        alarme=alarme_da_regra.alarme,
                        valido=alarme_da_regra.valido,
                        anos=tabela_h["ano_alvo"],
                    )
                    linhas_de_resultado.append({
                        "evento": evento,
                        "canal": canal if canal is not None else "-",
                        "regra": regra,
                        "h": h,
                        "periodo": nome_periodo,
                        "sensibilidade": metricas.sensibilidade,
                        "precisao": metricas.precisao,
                        "especificidade": metricas.especificidade,
                        "falsos_por_ano": metricas.falsos_por_ano,
                        "youden": metricas.youden,
                        "n_surto": metricas.n_surto,
                        "n_semanas": metricas.n_semanas,
                    })

    tabela_metricas = pd.DataFrame(linhas_de_resultado)
    return tabela_metricas


# ---------------------------------------------------------------------------
# TRAVA
# ---------------------------------------------------------------------------


def checar_trava(tabela_metricas: pd.DataFrame) -> bool:
    """Confere M_adotado/E_100/avaliacao contra os numeros de 13/09/2026.

    Levanta excecao com o detalhe da divergencia se a trava nao reproduzir.
    Retorna True se tudo bateu dentro da tolerancia.
    """
    trava_ok = True

    for esperado in (TRAVA_H4, TRAVA_H12):
        linha = tabela_metricas[
            (tabela_metricas["evento"] == NOME_EVENTO_100)
            & (tabela_metricas["regra"] == REGRA_M_ADOTADO)
            & (tabela_metricas["h"] == esperado.h)
            & (tabela_metricas["periodo"] == NOME_PERIODO_AVALIACAO)
        ]
        if len(linha) != 1:
            raise ValueError(f"Trava: nao encontrei exatamente 1 linha para h={esperado.h}.")

        sensibilidade_obtida = float(linha["sensibilidade"].iloc[0])
        precisao_obtida = float(linha["precisao"].iloc[0])
        falsos_por_ano_obtido = float(linha["falsos_por_ano"].iloc[0])

        diferenca_sensibilidade = abs(sensibilidade_obtida - esperado.sensibilidade)
        diferenca_precisao = abs(precisao_obtida - esperado.precisao)
        diferenca_falsos = abs(falsos_por_ano_obtido - esperado.falsos_por_ano)

        bateu = (
            diferenca_sensibilidade <= TOLERANCIA_TRAVA_PROPORCAO
            and diferenca_precisao <= TOLERANCIA_TRAVA_PROPORCAO
            and diferenca_falsos <= TOLERANCIA_TRAVA_FALSOS_POR_ANO
        )

        log.info(
            "TRAVA h=%d: obtido sensibilidade=%.4f (esperado %.3f, dif %.4f) | "
            "precisao=%.4f (esperado %.3f, dif %.4f) | falsos_por_ano=%.4f (esperado %.3f, dif %.4f) -> %s",
            esperado.h,
            sensibilidade_obtida,
            esperado.sensibilidade,
            diferenca_sensibilidade,
            precisao_obtida,
            esperado.precisao,
            diferenca_precisao,
            falsos_por_ano_obtido,
            esperado.falsos_por_ano,
            diferenca_falsos,
            "OK" if bateu else "FALHOU",
        )

        if not bateu:
            trava_ok = False

    return trava_ok


# ---------------------------------------------------------------------------
# MCNEMAR + HOLM
# ---------------------------------------------------------------------------


def calcular_mcnemar_exato(acertos_a: pd.Series, acertos_b: pd.Series) -> dict[str, float]:
    """McNemar exato pareado, sobre acerto/erro (True=acertou), via binomtest.

    Fallback declarado: se nao houver nenhum par discordante, o p-valor e
    fixado em 1.0 (nao ha evidencia de diferenca possivel de medir).
    """
    a_acerta_b_erra = int((acertos_a & ~acertos_b).sum())
    b_acerta_a_erra = int((~acertos_a & acertos_b).sum())
    n_discordantes = a_acerta_b_erra + b_acerta_a_erra

    if n_discordantes == 0:
        p_valor = 1.0
    else:
        n_menor = min(a_acerta_b_erra, b_acerta_a_erra)
        resultado_binomial = scipy.stats.binomtest(n_menor, n_discordantes, p=0.5, alternative="two-sided")
        p_valor = resultado_binomial.pvalue

    return {
        "n_pares": int(len(acertos_a)),
        "n_discordantes": n_discordantes,
        "n_a_acerta_b_erra": a_acerta_b_erra,
        "n_b_acerta_a_erra": b_acerta_a_erra,
        "p_valor": p_valor,
    }


def aplicar_correcao_holm(p_valores: list[float]) -> list[float]:
    """Correcao de Holm-Bonferroni (step-down), sobre uma familia de p-valores.

    Implementacao direta, sem depender de biblioteca de estatistica externa
    para a correcao (reimplementacao independente, conforme exigido pelas
    diretrizes do projeto para qualquer estatistica nova).
    """
    n_testes = len(p_valores)
    indices_ordenados = np.argsort(p_valores)

    p_ajustados = np.empty(n_testes, dtype=float)
    maior_ajustado_ate_agora = 0.0

    for posicao, indice_original in enumerate(indices_ordenados):
        multiplicador = n_testes - posicao
        p_ajustado_bruto = p_valores[indice_original] * multiplicador
        p_ajustado = max(p_ajustado_bruto, maior_ajustado_ate_agora)
        p_ajustado = min(p_ajustado, 1.0)
        p_ajustados[indice_original] = p_ajustado
        maior_ajustado_ate_agora = p_ajustado

    return p_ajustados.tolist()


def construir_tabela_mcnemar(tabela_avaliacao: pd.DataFrame) -> pd.DataFrame:
    """Monta a familia de 16 comparacoes de McNemar, com Holm aplicado no fim.

    Familia: 2 modelos x 2 regras-base x 2 horizontes x 2 eventos, todas no
    periodo de avaliacao (data_alvo >= 2024-01-01) — o periodo confirmatorio,
    nao a calibracao, que e so descritiva.
    """
    linhas_de_resultado: list[dict[str, object]] = []

    for evento, canal in ((NOME_EVENTO_100, None), (NOME_EVENTO_CANAL, CANAL_LOG)):
        for h in HORIZONTES_MCNEMAR:
            tabela_h = filtrar_por_periodo(tabela_avaliacao, INICIO_AVALIACAO, FIM_AVALIACAO)
            tabela_h = tabela_h[tabela_h["h"] == h]

            definicao_evento = montar_definicao_de_evento(tabela_h, evento, canal)
            alarmes_por_regra, e_surto = calcular_alarmes_das_regras(tabela_h, definicao_evento)

            for modelo in MODELOS_PARA_MCNEMAR:
                for regra_base in REGRAS_BASE_PARA_MCNEMAR:
                    alarme_modelo = alarmes_por_regra[modelo]
                    alarme_regra_base = alarmes_por_regra[regra_base]

                    mascara_ambos_validos = alarme_modelo.valido & alarme_regra_base.valido
                    e_surto_valido = e_surto[mascara_ambos_validos]
                    acertos_modelo = alarme_modelo.alarme[mascara_ambos_validos] == e_surto_valido
                    acertos_regra_base = alarme_regra_base.alarme[mascara_ambos_validos] == e_surto_valido

                    resultado_mcnemar = calcular_mcnemar_exato(acertos_modelo, acertos_regra_base)

                    linhas_de_resultado.append({
                        "evento": evento,
                        "canal": canal if canal is not None else "-",
                        "h": h,
                        "modelo": modelo,
                        "regra_base": regra_base,
                        "n_pares": resultado_mcnemar["n_pares"],
                        "n_discordantes": resultado_mcnemar["n_discordantes"],
                        "n_modelo_acerta_base_erra": resultado_mcnemar["n_a_acerta_b_erra"],
                        "n_base_acerta_modelo_erra": resultado_mcnemar["n_b_acerta_a_erra"],
                        "p_valor_bruto": resultado_mcnemar["p_valor"],
                    })

    tabela_mcnemar = pd.DataFrame(linhas_de_resultado)

    n_comparacoes = len(tabela_mcnemar)
    n_esperado = 2 * 2 * len(HORIZONTES_MCNEMAR) * 2
    if n_comparacoes != n_esperado:
        raise ValueError(
            f"Familia de McNemar tem {n_comparacoes} comparacoes, esperava {n_esperado}."
        )

    tabela_mcnemar["p_valor_holm"] = aplicar_correcao_holm(tabela_mcnemar["p_valor_bruto"].tolist())
    tabela_mcnemar["significativo_holm_005"] = tabela_mcnemar["p_valor_holm"] < ALFA_HOLM

    log.info(
        "McNemar: %d comparacoes na familia de Holm. Significativas (p_holm<0.05): %d.",
        n_comparacoes,
        int(tabela_mcnemar["significativo_holm_005"].sum()),
    )
    return tabela_mcnemar


# ---------------------------------------------------------------------------
# FIGURA
# ---------------------------------------------------------------------------


def gerar_figura_youden(tabela_metricas: pd.DataFrame, caminho_saida: Path) -> None:
    """Barras do indice de Youden por regra, eventos E_100/E_canal(C_log), h=4 e h=12.

    Usa sempre o periodo de avaliacao (o confirmatorio), pela mesma razao da
    familia de McNemar.
    """
    eventos_na_figura = [
        (NOME_EVENTO_100, "-", "E_100"),
        (NOME_EVENTO_CANAL, CANAL_LOG, "E_canal (C_log)"),
    ]

    figura, eixos = plt.subplots(1, 2, figsize=(11, 5), sharey=True)

    for indice_h, h in enumerate((4, 12)):
        eixo = eixos[indice_h]
        largura_barra = 0.35
        posicoes_regras = np.arange(len(REGRAS_TODAS))

        for indice_evento, (evento, canal, rotulo_evento) in enumerate(eventos_na_figura):
            mascara = (
                (tabela_metricas["h"] == h)
                & (tabela_metricas["evento"] == evento)
                & (tabela_metricas["canal"] == canal)
                & (tabela_metricas["periodo"] == NOME_PERIODO_AVALIACAO)
            )
            linhas_do_evento = tabela_metricas[mascara].set_index("regra").reindex(REGRAS_TODAS)
            valores_youden = linhas_do_evento["youden"].to_numpy()

            deslocamento = (indice_evento - 0.5) * largura_barra
            eixo.bar(
                posicoes_regras + deslocamento,
                valores_youden,
                width=largura_barra,
                label=rotulo_evento,
            )

        eixo.set_title(f"h = {h} semanas")
        eixo.set_xticks(posicoes_regras)
        eixo.set_xticklabels(REGRAS_TODAS, rotation=30, ha="right")
        eixo.axhline(0.0, color="black", linewidth=0.8)
        eixo.set_ylabel("Indice de Youden" if indice_h == 0 else "")
        eixo.legend(loc="upper right", fontsize=8)

    figura.suptitle("Youden por regra de alarme — periodo de avaliacao (2024+)")
    figura.tight_layout()
    figura.savefig(caminho_saida, dpi=150)
    plt.close(figura)
    log.info("Figura salva em %s", caminho_saida)


# ---------------------------------------------------------------------------
# PARTE A — VARREDURA DESCRITIVA DO LIMIAR DE DECISAO (evento fixo em E_421)
# ---------------------------------------------------------------------------


def construir_tabela_varredura_limiar_decisao(
    tabela_avaliacao: pd.DataFrame,
    serie_semanal: pd.DataFrame,
) -> pd.DataFrame:
    """Varre o limiar de DECISAO em `GRADE_LIMIARES_DECISAO`, evento fixo E_421.

    Descritiva, por pre-declaracao: nao escolhe o melhor D. Uma linha por
    (modelo, h, D), periodo de avaliacao (2024+) apenas — a varredura nao
    precisa do periodo de calibracao.
    """
    contagem_evento_421 = calcular_blocos_contiguos_por_evento(
        serie_semanal, LIMIARES_EVENTOS_CONSTANTES[NOME_EVENTO_421], INICIO_AVALIACAO, FIM_AVALIACAO
    )

    linhas_de_resultado: list[dict[str, object]] = []

    for h in HORIZONTES_TODOS:
        tabela_h = filtrar_por_periodo(tabela_avaliacao, INICIO_AVALIACAO, FIM_AVALIACAO)
        tabela_h = tabela_h[tabela_h["h"] == h]

        definicao_evento = montar_definicao_de_evento(tabela_h, NOME_EVENTO_421, None)

        for limiar_decisao in GRADE_LIMIARES_DECISAO:
            alarmes_por_regra, e_surto = calcular_alarmes_das_regras(
                tabela_h, definicao_evento, limite_decisao=float(limiar_decisao)
            )

            for modelo in MODELOS_PARA_VARREDURA:
                alarme_do_modelo = alarmes_por_regra[modelo]
                metricas = calcular_metricas_de_alarme(
                    e_surto=e_surto,
                    alarme=alarme_do_modelo.alarme,
                    valido=alarme_do_modelo.valido,
                    anos=tabela_h["ano_alvo"],
                )
                linhas_de_resultado.append({
                    "modelo": modelo,
                    "h": h,
                    "limiar_decisao": limiar_decisao,
                    "eh_regra_de_hoje": limiar_decisao == LIMIAR_DECISAO_REFERENCIA_HOJE,
                    "sensibilidade": metricas.sensibilidade,
                    "especificidade": metricas.especificidade,
                    "precisao": metricas.precisao,
                    "falsos_por_ano": metricas.falsos_por_ano,
                    "youden": metricas.youden,
                    "n_surto": metricas.n_surto,
                    "n_semanas": metricas.n_semanas,
                    "n_surto_periodo_total_421": contagem_evento_421.n_surto,
                    "n_blocos_contiguos_periodo_421": contagem_evento_421.n_blocos,
                })

    tabela_varredura = pd.DataFrame(linhas_de_resultado)
    return tabela_varredura


def verificar_previsao_youden_acima_do_evento(tabela_varredura: pd.DataFrame) -> pd.DataFrame:
    """Confere a previsao declarada: o D de melhor Youden deve ficar ACIMA de 421.

    Por (modelo, h), escolhe o D de maior Youden (ignorando NaN; em empate,
    fica com o menor D, decisao arbitraria mas registrada, ja que nao muda o
    veredito da previsao). Reporta CONFIRMOU ou FALHOU sem suavizar — a
    pre-declaracao proibe apresentar esse D como resultado, so como checagem
    da hipotese.
    """
    linhas_de_verificacao: list[dict[str, object]] = []

    for (modelo, h), tabela_do_grupo in tabela_varredura.groupby(["modelo", "h"]):
        tabela_valida = tabela_do_grupo[tabela_do_grupo["youden"].notna()]
        if len(tabela_valida) == 0:
            linhas_de_verificacao.append({
                "modelo": modelo,
                "h": h,
                "d_melhor_youden": np.nan,
                "melhor_youden": np.nan,
                "previsao_confirmada": None,
                "observacao": "sem nenhum Youden valido no recorte",
            })
            continue

        indice_do_maximo = tabela_valida["youden"].idxmax()
        linha_do_maximo = tabela_valida.loc[indice_do_maximo]
        d_melhor_youden = float(linha_do_maximo["limiar_decisao"])

        linhas_de_verificacao.append({
            "modelo": modelo,
            "h": h,
            "d_melhor_youden": d_melhor_youden,
            "melhor_youden": float(linha_do_maximo["youden"]),
            "previsao_confirmada": d_melhor_youden > LIMIAR_DECISAO_REFERENCIA_HOJE,
            "observacao": "",
        })

    tabela_verificacao = pd.DataFrame(linhas_de_verificacao)
    log.info(
        "PREVISAO DECLARADA (D de melhor Youden > 421): \n%s",
        tabela_verificacao.to_string(index=False),
    )
    return tabela_verificacao


def gerar_figura_varredura(tabela_varredura: pd.DataFrame, caminho_saida: Path) -> None:
    """Curva sensibilidade x falsos/ano, por horizonte, marcando D=421 (regra de hoje)."""
    figura, eixos = plt.subplots(2, 2, figsize=(11, 9), sharex=False, sharey=True)
    eixos_lineares = eixos.flatten()

    for indice_h, h in enumerate(HORIZONTES_TODOS):
        eixo = eixos_lineares[indice_h]

        for modelo in MODELOS_PARA_VARREDURA:
            mascara = (tabela_varredura["h"] == h) & (tabela_varredura["modelo"] == modelo)
            pontos_do_modelo = tabela_varredura[mascara].sort_values("limiar_decisao")

            eixo.plot(
                pontos_do_modelo["falsos_por_ano"],
                pontos_do_modelo["sensibilidade"],
                marker="o",
                markersize=4,
                label=modelo,
            )

            ponto_regra_de_hoje = pontos_do_modelo[pontos_do_modelo["eh_regra_de_hoje"]]
            if len(ponto_regra_de_hoje) == 1:
                eixo.scatter(
                    ponto_regra_de_hoje["falsos_por_ano"],
                    ponto_regra_de_hoje["sensibilidade"],
                    s=140,
                    facecolors="none",
                    edgecolors="black",
                    linewidths=1.8,
                    zorder=5,
                )

        eixo.set_title(f"h = {h} semanas")
        eixo.set_xlabel("Falsos por ano")
        if indice_h % 2 == 0:
            eixo.set_ylabel("Sensibilidade")
        eixo.set_ylim(-0.05, 1.05)
        eixo.legend(loc="lower right", fontsize=8)

    figura.suptitle(
        "Varredura do limiar de decisao — evento fixo E_421, periodo de avaliacao (2024+)\n"
        "circulo vazado = D=421 (a regra de hoje, decisao colada no evento)"
    )
    figura.tight_layout()
    figura.savefig(caminho_saida, dpi=150)
    plt.close(figura)
    log.info("Figura da varredura salva em %s", caminho_saida)


# ---------------------------------------------------------------------------
# PARTE B — OS ESTAGIOS OFICIAIS COMO EVENTO
# ---------------------------------------------------------------------------

EVENTOS_ESTAGIOS_TODOS = (NOME_EVENTO_100, NOME_EVENTO_140, NOME_EVENTO_421, NOME_EVENTO_702)


def construir_tabela_metricas_estagios(
    tabela_avaliacao: pd.DataFrame,
    serie_semanal: pd.DataFrame,
) -> pd.DataFrame:
    """Metricas por (evento, regra, h, periodo) para os 4 estagios oficiais.

    Mesmo desenho de `construir_tabela_metricas_por_regra`, mas so para os
    limiares constantes do plano municipal, e com 2 colunas novas ao lado de
    `n_surto`: `n_surto_periodo_total` e `n_blocos_contiguos_periodo` — a
    contagem sobre as 121 semanas reais do periodo (nao sobre o subconjunto
    valido por h/regra), a mesma usada na pre-declaracao (secao C).
    """
    periodos = {
        NOME_PERIODO_AVALIACAO: (INICIO_AVALIACAO, FIM_AVALIACAO),
        NOME_PERIODO_CALIBRACAO: (INICIO_CALIBRACAO, FIM_CALIBRACAO),
    }

    linhas_de_resultado: list[dict[str, object]] = []

    for nome_periodo, (data_inicio, data_fim) in periodos.items():
        tabela_do_periodo = filtrar_por_periodo(tabela_avaliacao, data_inicio, data_fim)

        for evento in EVENTOS_ESTAGIOS_TODOS:
            contagem_do_evento = calcular_blocos_contiguos_por_evento(
                serie_semanal, LIMIARES_EVENTOS_CONSTANTES[evento], data_inicio, data_fim
            )

            for h in HORIZONTES_TODOS:
                tabela_h = tabela_do_periodo[tabela_do_periodo["h"] == h]

                definicao_evento = montar_definicao_de_evento(tabela_h, evento, None)
                alarmes_por_regra, e_surto = calcular_alarmes_das_regras(tabela_h, definicao_evento)

                for regra in REGRAS_TODAS:
                    alarme_da_regra = alarmes_por_regra[regra]
                    metricas = calcular_metricas_de_alarme(
                        e_surto=e_surto,
                        alarme=alarme_da_regra.alarme,
                        valido=alarme_da_regra.valido,
                        anos=tabela_h["ano_alvo"],
                    )
                    linhas_de_resultado.append({
                        "evento": evento,
                        "regra": regra,
                        "h": h,
                        "periodo": nome_periodo,
                        "sensibilidade": metricas.sensibilidade,
                        "precisao": metricas.precisao,
                        "especificidade": metricas.especificidade,
                        "falsos_por_ano": metricas.falsos_por_ano,
                        "youden": metricas.youden,
                        "n_surto": metricas.n_surto,
                        "n_semanas": metricas.n_semanas,
                        "n_surto_periodo_total": contagem_do_evento.n_surto,
                        "n_blocos_contiguos_periodo": contagem_do_evento.n_blocos,
                        "maior_bloco_periodo": contagem_do_evento.maior_bloco,
                        "estatuto": (
                            "confirmatorio" if evento == EVENTO_CONFIRMATORIO else "descritivo"
                        ),
                    })

    tabela_metricas_estagios = pd.DataFrame(linhas_de_resultado)
    return tabela_metricas_estagios


@dataclasses.dataclass(frozen=True)
class ParDeAlarmesValidos:
    """Sequencia (ordenada por data_alvo) de acerto/erro de um modelo e uma regra-base."""

    data_alvo: pd.Series
    acertos_modelo: pd.Series
    acertos_base: pd.Series


def obter_par_de_alarmes_e421(
    tabela_avaliacao: pd.DataFrame,
    h: int,
    modelo: str,
    regra_base: str,
) -> ParDeAlarmesValidos:
    """Acerto/erro de `modelo` e `regra_base` no evento E_421, periodo de avaliacao.

    Usado tanto pelo McNemar confirmatorio (Parte B) quanto pelo
    bloco-bootstrap (Parte C) — a mesma comparacao pareada, ordenada por
    `data_alvo` para que os blocos do bootstrap sigam a ordem do calendario.
    """
    tabela_h = filtrar_por_periodo(tabela_avaliacao, INICIO_AVALIACAO, FIM_AVALIACAO)
    tabela_h = tabela_h[tabela_h["h"] == h]

    definicao_evento = montar_definicao_de_evento(tabela_h, NOME_EVENTO_421, None)
    alarmes_por_regra, e_surto = calcular_alarmes_das_regras(tabela_h, definicao_evento)

    alarme_modelo = alarmes_por_regra[modelo]
    alarme_base = alarmes_por_regra[regra_base]

    mascara_ambos_validos = alarme_modelo.valido & alarme_base.valido
    e_surto_valido = e_surto[mascara_ambos_validos]
    acertos_modelo = alarme_modelo.alarme[mascara_ambos_validos] == e_surto_valido
    acertos_base = alarme_base.alarme[mascara_ambos_validos] == e_surto_valido
    data_alvo_valida = tabela_h.loc[mascara_ambos_validos, "data_alvo"]

    ordem_temporal = data_alvo_valida.sort_values().index
    return ParDeAlarmesValidos(
        data_alvo=data_alvo_valida.loc[ordem_temporal].reset_index(drop=True),
        acertos_modelo=acertos_modelo.loc[ordem_temporal].reset_index(drop=True),
        acertos_base=acertos_base.loc[ordem_temporal].reset_index(drop=True),
    )


def construir_tabela_mcnemar_e421_e_familia_combinada(
    tabela_avaliacao: pd.DataFrame,
    caminho_familia_25_09: Path,
) -> pd.DataFrame:
    """McNemar confirmatorio de E_421 (8 testes), Holm sobre a familia de 25/09 + estes 8.

    A pre-declaracao (secao B) exige que a correcao de Holm cubra a familia
    JA aberta em 25/09/2026 (16 comparacoes: E_100 e E_canal(C_log), h=4/12,
    2 modelos x 2 regras-base) somada aos 8 testes novos de E_421 — nunca so
    os 8 novos isolados. A ordem da familia (25/09 primeiro, depois os 8
    novos) e preservada para que a leitura das colunas antigas nao mude.
    """
    familia_25_09 = pd.read_csv(caminho_familia_25_09)
    colunas_da_familia = [
        "evento", "canal", "h", "modelo", "regra_base",
        "n_pares", "n_discordantes",
        "n_modelo_acerta_base_erra", "n_base_acerta_modelo_erra",
        "p_valor_bruto",
    ]
    familia_25_09 = familia_25_09[colunas_da_familia].copy()
    familia_25_09["origem_familia"] = "25-09-2026"

    linhas_e421: list[dict[str, object]] = []
    for h in HORIZONTES_MCNEMAR:
        for modelo in MODELOS_PARA_MCNEMAR:
            for regra_base in REGRAS_BASE_PARA_MCNEMAR:
                par = obter_par_de_alarmes_e421(tabela_avaliacao, h, modelo, regra_base)
                resultado_mcnemar = calcular_mcnemar_exato(par.acertos_modelo, par.acertos_base)
                linhas_e421.append({
                    "evento": NOME_EVENTO_421,
                    "canal": "-",
                    "h": h,
                    "modelo": modelo,
                    "regra_base": regra_base,
                    "n_pares": resultado_mcnemar["n_pares"],
                    "n_discordantes": resultado_mcnemar["n_discordantes"],
                    "n_modelo_acerta_base_erra": resultado_mcnemar["n_a_acerta_b_erra"],
                    "n_base_acerta_modelo_erra": resultado_mcnemar["n_b_acerta_a_erra"],
                    "p_valor_bruto": resultado_mcnemar["p_valor"],
                    "origem_familia": "26-09-2026",
                })

    tabela_e421 = pd.DataFrame(linhas_e421)
    familia_combinada = pd.concat([familia_25_09, tabela_e421], ignore_index=True)

    n_esperado = 16 + 8
    if len(familia_combinada) != n_esperado:
        raise ValueError(
            f"Familia combinada tem {len(familia_combinada)} linhas, esperava {n_esperado} "
            f"({len(familia_25_09)} de 25/09 + {len(tabela_e421)} novas)."
        )

    familia_combinada["p_valor_holm"] = aplicar_correcao_holm(
        familia_combinada["p_valor_bruto"].tolist()
    )
    familia_combinada["significativo_holm_005"] = familia_combinada["p_valor_holm"] < ALFA_HOLM

    log.info(
        "Familia de Holm combinada: %d comparacoes (%d de 25/09 + %d de E_421 em 26/09). "
        "Significativas (p_holm<0.05): %d.",
        len(familia_combinada),
        len(familia_25_09),
        len(tabela_e421),
        int(familia_combinada["significativo_holm_005"].sum()),
    )
    return familia_combinada


def avaliar_criterio_de_ganho_e421(
    tabela_metricas_estagios: pd.DataFrame,
    tabela_mcnemar_combinada: pd.DataFrame,
) -> pd.DataFrame:
    """Aplica o criterio da pre-declaracao: ganho so vencendo R_ano_passado (Youden) com p_holm<0.05.

    Vencer so R_hoje nao conta — isso ja foi mostrado em 25/09 (secao B da
    pre-declaracao). Uma linha por (modelo, h).
    """
    mascara_mcnemar_e421 = (
        (tabela_mcnemar_combinada["evento"] == NOME_EVENTO_421)
        & (tabela_mcnemar_combinada["regra_base"] == REGRA_R_ANO_PASSADO)
    )
    mcnemar_e421_r_ano_passado = tabela_mcnemar_combinada[mascara_mcnemar_e421]

    mascara_metricas_e421 = (
        (tabela_metricas_estagios["evento"] == NOME_EVENTO_421)
        & (tabela_metricas_estagios["periodo"] == NOME_PERIODO_AVALIACAO)
    )
    metricas_e421 = tabela_metricas_estagios[mascara_metricas_e421].set_index(["regra", "h"])

    linhas_de_resultado: list[dict[str, object]] = []
    for h in HORIZONTES_MCNEMAR:
        for modelo in MODELOS_PARA_MCNEMAR:
            youden_modelo = float(metricas_e421.loc[(modelo, h), "youden"])
            youden_r_ano_passado = float(metricas_e421.loc[(REGRA_R_ANO_PASSADO, h), "youden"])

            linha_mcnemar = mcnemar_e421_r_ano_passado[
                (mcnemar_e421_r_ano_passado["modelo"] == modelo)
                & (mcnemar_e421_r_ano_passado["h"] == h)
            ]
            p_holm = float(linha_mcnemar["p_valor_holm"].iloc[0]) if len(linha_mcnemar) == 1 else np.nan

            vence_youden = youden_modelo > youden_r_ano_passado
            conta_como_ganho = bool(vence_youden and (p_holm < ALFA_HOLM))

            linhas_de_resultado.append({
                "modelo": modelo,
                "h": h,
                "youden_modelo": youden_modelo,
                "youden_r_ano_passado": youden_r_ano_passado,
                "vence_youden": vence_youden,
                "p_valor_holm_vs_r_ano_passado": p_holm,
                "conta_como_ganho_e421": conta_como_ganho,
            })

    tabela_criterio = pd.DataFrame(linhas_de_resultado)
    log.info("CRITERIO DE GANHO EM E_421 (vencer R_ano_passado em Youden, p_holm<0.05):\n%s",
              tabela_criterio.to_string(index=False))
    return tabela_criterio


# ---------------------------------------------------------------------------
# PARTE C — BLOCO-BOOTSTRAP DA INFLACAO DO P
# ---------------------------------------------------------------------------


def montar_serie_temporal_de_categorias(acertos_modelo: pd.Series, acertos_base: pd.Series) -> np.ndarray:
    """Categoria de cada SEMANA (nao so das discordantes), na ordem temporal recebida.

    +1: discordante, o modelo acerta e a base erra.
    -1: discordante, a base acerta e o modelo erra.
     0: concordante (os dois acertam ou os dois erram).

    Mantida a serie INTEIRA (nao so a subsequencia dos discordantes) porque o
    comprimento de bloco L, em semanas, so tem o significado declarado na
    pre-declaracao (4/8/13/26 semanas de calendario) se o bloco correr sobre o
    eixo do tempo real. Reduzir a serie so aos pares discordantes antes de
    reamostrar destruiria essa escala — um bloco de 13 "semanas discordantes"
    nao e um bloco de 13 semanas do calendario, porque os discordantes ja sao
    um subconjunto raro e disperso. As 39 semanas de surto do projeto formam
    2 blocos contiguos (ver pre-declaracao, secao 1): e essa proximidade no
    CALENDARIO que a reamostragem por bloco precisa preservar.
    """
    n_semanas = len(acertos_modelo)
    categorias = np.zeros(n_semanas, dtype=int)

    modelo_acerta_base_erra = (acertos_modelo & ~acertos_base).to_numpy()
    base_acerta_modelo_erra = (~acertos_modelo & acertos_base).to_numpy()

    categorias[modelo_acerta_base_erra] = 1
    categorias[base_acerta_modelo_erra] = -1
    return categorias


def reamostrar_bloco_movel_circular(
    sinais: np.ndarray,
    comprimento_bloco: int,
    gerador: np.random.Generator,
) -> np.ndarray:
    """Uma reamostragem por bloco movel CIRCULAR, do mesmo tamanho da serie original.

    Circular (com "quebra" voltando ao inicio) para que todo indice da serie
    tenha a mesma chance de comecar um bloco, inclusive perto do fim — a
    alternativa (bloco nao-circular) descartaria blocos que passassem do
    limite, enviesando a amostra contra os ultimos `comprimento_bloco - 1`
    pontos.
    """
    n_pontos = len(sinais)
    n_blocos_necessarios = int(np.ceil(n_pontos / comprimento_bloco))

    blocos_sorteados: list[np.ndarray] = []
    for _ in range(n_blocos_necessarios):
        inicio_do_bloco = int(gerador.integers(0, n_pontos))
        indices_do_bloco = [
            (inicio_do_bloco + deslocamento) % n_pontos for deslocamento in range(comprimento_bloco)
        ]
        blocos_sorteados.append(sinais[indices_do_bloco])

    serie_reamostrada = np.concatenate(blocos_sorteados)[:n_pontos]
    return serie_reamostrada


@dataclasses.dataclass(frozen=True)
class ResultadoBootstrapBloco:
    """Resultado do bloco-bootstrap para um teste e um comprimento de bloco."""

    n_semanas_total: int
    n_discordantes: int
    proporcao_positiva_observada: float
    erro_padrao_bootstrap: float
    n_reamostragens_validas: int
    p_bootstrap: float
    observacao: str


def calcular_p_bootstrap_bloco(
    categorias_semanais: np.ndarray,
    comprimento_bloco: int,
    n_reamostragens: int,
    gerador: np.random.Generator,
) -> ResultadoBootstrapBloco:
    """P-valor via bloco-bootstrap: reestima o erro padrao da proporcao sob dependencia.

    Metodo (descritivo, declarado na pre-declaracao como ordem de grandeza,
    nao substituto do p oficial):
      1. Reamostra a serie semanal INTEIRA (categorias +1/-1/0, ordenada no
         tempo) por bloco movel circular de `comprimento_bloco` semanas,
         `n_reamostragens` vezes — preservando a escala de calendario do
         bloco (ver docstring de `montar_serie_temporal_de_categorias`).
      2. Em cada reamostragem, recalcula a proporcao de sinais positivos
         SO entre as semanas que ficaram discordantes na propria
         reamostragem (uma reamostragem pode ter mais ou menos semanas
         discordantes que a serie original, porque blocos inteiros de
         semanas concordantes ou discordantes podem ser sorteados).
      3. O erro padrao bootstrap e o desvio-padrao (ddof=1) dessas
         proporcoes, so entre as reamostragens com pelo menos 1 semana
         discordante.
      4. O p-valor bootstrap vem de uma aproximacao normal bicaudal em torno
         de 0,5 (a hipotese nula do McNemar), usando esse erro padrao no
         lugar do erro padrao binomial iid (p(1-p)/n) implicito no teste
         exato original. Quando ha dependencia serial positiva (as semanas
         de surto formam blocos, nao estao espalhadas ao acaso), este erro
         padrao tende a ser MAIOR que o iid, e o p bootstrap, MAIOR que o
         nominal — a "inflacao" que a pre-declaracao pede para medir.

    Fallback declarado: sem semana discordante na serie original, erro
    padrao bootstrap igual a zero, ou menos de 2 reamostragens com alguma
    semana discordante (SE nao estimavel), o p-valor bootstrap fica NaN e a
    razao correspondente nao e calculavel; a `observacao` registra o motivo.
    """
    n_semanas_total = len(categorias_semanais)
    mascara_discordante_observada = categorias_semanais != 0
    n_discordantes_observado = int(mascara_discordante_observada.sum())

    if n_discordantes_observado == 0:
        return ResultadoBootstrapBloco(
            n_semanas_total=n_semanas_total,
            n_discordantes=0,
            proporcao_positiva_observada=np.nan,
            erro_padrao_bootstrap=np.nan,
            n_reamostragens_validas=0,
            p_bootstrap=np.nan,
            observacao="sem pares discordantes na serie original",
        )

    proporcao_positiva_observada = float(
        (categorias_semanais[mascara_discordante_observada] == 1).mean()
    )

    proporcoes_das_reamostragens_validas: list[float] = []
    for _ in range(n_reamostragens):
        reamostra = reamostrar_bloco_movel_circular(categorias_semanais, comprimento_bloco, gerador)
        mascara_discordante_reamostra = reamostra != 0
        n_discordantes_reamostra = int(mascara_discordante_reamostra.sum())
        if n_discordantes_reamostra == 0:
            continue
        proporcao_positiva_reamostra = float((reamostra[mascara_discordante_reamostra] == 1).mean())
        proporcoes_das_reamostragens_validas.append(proporcao_positiva_reamostra)

    n_reamostragens_validas = len(proporcoes_das_reamostragens_validas)

    if n_reamostragens_validas < 2:
        return ResultadoBootstrapBloco(
            n_semanas_total=n_semanas_total,
            n_discordantes=n_discordantes_observado,
            proporcao_positiva_observada=proporcao_positiva_observada,
            erro_padrao_bootstrap=np.nan,
            n_reamostragens_validas=n_reamostragens_validas,
            p_bootstrap=np.nan,
            observacao="menos de 2 reamostragens com alguma semana discordante",
        )

    erro_padrao_bootstrap = float(np.std(proporcoes_das_reamostragens_validas, ddof=1))

    if erro_padrao_bootstrap == 0.0:
        return ResultadoBootstrapBloco(
            n_semanas_total=n_semanas_total,
            n_discordantes=n_discordantes_observado,
            proporcao_positiva_observada=proporcao_positiva_observada,
            erro_padrao_bootstrap=0.0,
            n_reamostragens_validas=n_reamostragens_validas,
            p_bootstrap=np.nan,
            observacao="erro padrao bootstrap = 0 (sem variabilidade entre reamostragens)",
        )

    estatistica_z = (proporcao_positiva_observada - 0.5) / erro_padrao_bootstrap
    p_bootstrap = float(2.0 * (1.0 - scipy.stats.norm.cdf(abs(estatistica_z))))
    p_bootstrap = min(p_bootstrap, 1.0)

    observacao = (
        ""
        if n_reamostragens_validas == n_reamostragens
        else (
            f"{n_reamostragens - n_reamostragens_validas} de {n_reamostragens} reamostragens "
            "descartadas por nao terem nenhuma semana discordante"
        )
    )

    return ResultadoBootstrapBloco(
        n_semanas_total=n_semanas_total,
        n_discordantes=n_discordantes_observado,
        proporcao_positiva_observada=proporcao_positiva_observada,
        erro_padrao_bootstrap=erro_padrao_bootstrap,
        n_reamostragens_validas=n_reamostragens_validas,
        p_bootstrap=p_bootstrap,
        observacao=observacao,
    )


def construir_tabela_bootstrap_e421(tabela_avaliacao: pd.DataFrame) -> pd.DataFrame:
    """Bloco-bootstrap dos 8 testes de E_421, para os 4 comprimentos de bloco.

    Reusa exatamente os mesmos pares (modelo, regra_base, h) do McNemar
    confirmatorio da Parte B, para que a razao p_bootstrap/p_nominal seja
    sobre o MESMO teste, so recalculado.
    """
    gerador = np.random.default_rng(SEMENTE_BOOTSTRAP)
    linhas_de_resultado: list[dict[str, object]] = []

    for h in HORIZONTES_MCNEMAR:
        for modelo in MODELOS_PARA_MCNEMAR:
            for regra_base in REGRAS_BASE_PARA_MCNEMAR:
                par = obter_par_de_alarmes_e421(tabela_avaliacao, h, modelo, regra_base)
                resultado_nominal = calcular_mcnemar_exato(par.acertos_modelo, par.acertos_base)
                p_nominal = resultado_nominal["p_valor"]
                categorias_semanais = montar_serie_temporal_de_categorias(par.acertos_modelo, par.acertos_base)

                for comprimento_bloco in COMPRIMENTOS_BLOCO_BOOTSTRAP:
                    resultado_bootstrap = calcular_p_bootstrap_bloco(
                        categorias_semanais, comprimento_bloco, N_REAMOSTRAGENS_BOOTSTRAP, gerador
                    )
                    razao_inflacao = (
                        resultado_bootstrap.p_bootstrap / p_nominal
                        if (not np.isnan(resultado_bootstrap.p_bootstrap) and p_nominal > 0)
                        else np.nan
                    )
                    linhas_de_resultado.append({
                        "teste": f"E_421_h{h}_{modelo}_vs_{regra_base}",
                        "evento": NOME_EVENTO_421,
                        "h": h,
                        "modelo": modelo,
                        "regra_base": regra_base,
                        "comprimento_bloco": comprimento_bloco,
                        "n_semanas_total": resultado_bootstrap.n_semanas_total,
                        "n_discordantes": resultado_bootstrap.n_discordantes,
                        "p_nominal": p_nominal,
                        "erro_padrao_bootstrap": resultado_bootstrap.erro_padrao_bootstrap,
                        "n_reamostragens_validas": resultado_bootstrap.n_reamostragens_validas,
                        "p_bootstrap": resultado_bootstrap.p_bootstrap,
                        "razao_p_bootstrap_sobre_nominal": razao_inflacao,
                        "observacao": resultado_bootstrap.observacao,
                    })

    tabela_bootstrap = pd.DataFrame(linhas_de_resultado)
    return tabela_bootstrap


def registrar_teste_13_09_nao_localizado() -> dict[str, object]:
    """Documenta a busca pelas previsoes do teste de 13/09 (notificados, P90, h=12).

    Procurado e NAO encontrado. O teste (alvo notificados do InfoDengue,
    classificador LightGBM em cima do percentil 90, so-clima x clima+vetor)
    esta implementado em `modelagem_aedes/pipeline.py::rodar_cidade_surto_notificados`
    e so persiste em disco as CONTAGENS agregadas do McNemar (n, discordantes,
    p_bruto, p_holm — ver `modelagem_aedes/dados/saidas/resultados/
    surto_notificados_mcnemar.csv`, linha pctl=90/h=12: n=553, discordantes=30,
    p_bruto=0,0062, p_holm=0,0370). A funcao NUNCA salva a tabela `comparacao`
    por semana (acerto/erro por data_alvo de cada modelo) — ela e calculada em
    memoria e descartada apos as metricas agregadas. Sem essa sequencia por
    semana, o bloco-bootstrap (que precisa da ORDEM temporal dos pares
    discordantes) nao pode ser calculado sem re-treinar os 2 classificadores
    walk-forward — o que a pre-declaracao proibe ("nenhum modelo e treinado").

    Retorna um registro para o CSV de saida, com p_bootstrap NaN e o motivo
    explicito, em vez de forcar um numero.
    """
    return {
        "teste": "notificados_P90_h12_13-09-2026",
        "evento": "-",
        "h": 12,
        "modelo": "so-clima_vs_clima+vetor (LightGBM classificador)",
        "regra_base": "-",
        "comprimento_bloco": np.nan,
        "n_semanas_total": 553,
        "n_discordantes": 30,
        "p_nominal": 0.006169899320544161,
        "erro_padrao_bootstrap": np.nan,
        "n_reamostragens_validas": 0,
        "p_bootstrap": np.nan,
        "razao_p_bootstrap_sobre_nominal": np.nan,
        "observacao": (
            "NAO LOCALIZADO: previsoes por semana nao persistidas em disco "
            "(so as contagens agregadas do McNemar foram salvas); recalcular "
            "exigiria retreinar o classificador walk-forward, proibido pela "
            "pre-declaracao. Ver docstring de "
            "registrar_teste_13_09_nao_localizado."
        ),
    }


# ---------------------------------------------------------------------------
# ORQUESTRACAO
# ---------------------------------------------------------------------------


def main() -> None:
    log.info("Inicio da analise: alarme do modelo contra o canal endemico.")

    serie_semanal = carregar_serie_semanal(CAMINHO_TABELA_FINAL)
    canais_por_semana = construir_canais_por_semana_epidemiologica(
        serie_semanal, ANO_MINIMO_CANAL, MINIMO_ANOS_CANAL
    )
    tabela_semanal_enriquecida = montar_tabela_semanal_enriquecida(serie_semanal, canais_por_semana)

    previsoes = carregar_previsoes_dos_bracos(CAMINHO_PREVISOES)
    tabela_avaliacao = montar_tabela_de_avaliacao(previsoes, tabela_semanal_enriquecida)

    log.info(
        "Decisao registrada: semana 53 e tratada como qualquer outra semana "
        "epidemiologica — o canal so existe se houver >= %d anos anteriores "
        "com valor nao nulo NA MESMA semana 53 (ela so ocorre em alguns anos "
        "do calendario epidemiologico); quando faltam anos, a linha fica "
        "invalida para E_canal (todos os 3 canais) mas continua valendo para "
        "E_100, que nao depende do canal.",
        MINIMO_ANOS_CANAL,
    )
    log.info(
        "Decisao registrada: divisao por zero em precisao (sem alarmes), "
        "sensibilidade (sem semana de surto) e especificidade (sem semana "
        "calma) retornam NaN, nunca 0 ou erro — ver calcular_metricas_de_alarme.",
    )
    log.info(
        "Decisao registrada: desvio-padrao dos canais C_log e C_conv usa "
        "ddof=1 (amostral); percentil 75 usa interpolacao linear do NumPy "
        "(default), simplificacao ja declarada na pre-declaracao frente a "
        "binomial negativa do artigo original.",
    )

    PASTA_SAIDAS.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # PARTE D — TRAVA (roda primeiro, antes de qualquer resultado ser lido)
    # ------------------------------------------------------------------
    log.info("=" * 78)
    log.info("PARTE D — TRAVA (M_adotado, E_100, avaliacao 2024+)")
    log.info("=" * 78)

    tabela_metricas = construir_tabela_metricas_por_regra(tabela_avaliacao)
    trava_reproduziu = checar_trava(tabela_metricas)
    tabela_metricas.to_csv(PASTA_SAIDAS / "metricas_por_regra_e100_ecanal.csv", index=False)

    if not trava_reproduziu:
        log.error(
            "TRAVA FALHOU. Por instrucao da tarefa e da pre-declaracao, a "
            "rodada PARA aqui — nao le nem gera os resultados das Partes "
            "A, B e C. Investigar a causa antes de prosseguir."
        )
        log.info("Fim da analise (interrompida pela trava).")
        return

    log.info("TRAVA OK — reproduziu os numeros de 25/09/2026 dentro da tolerancia.")

    # ------------------------------------------------------------------
    # PARTE A — VARREDURA DESCRITIVA DO LIMIAR DE DECISAO (evento E_421)
    # ------------------------------------------------------------------
    log.info("=" * 78)
    log.info("PARTE A — varredura do limiar de decisao, evento fixo E_421")
    log.info("=" * 78)

    tabela_varredura = construir_tabela_varredura_limiar_decisao(tabela_avaliacao, serie_semanal)
    tabela_varredura.to_csv(PASTA_SAIDAS / "varredura_limiar_decisao.csv", index=False)

    tabela_verificacao_previsao = verificar_previsao_youden_acima_do_evento(tabela_varredura)
    tabela_verificacao_previsao.to_csv(PASTA_SAIDAS / "verificacao_previsao_youden.csv", index=False)

    gerar_figura_varredura(tabela_varredura, PASTA_SAIDAS / "figura_varredura_sensibilidade_falsos.png")

    # ------------------------------------------------------------------
    # PARTE B — OS ESTAGIOS OFICIAIS COMO EVENTO
    # ------------------------------------------------------------------
    log.info("=" * 78)
    log.info("PARTE B — estagios oficiais (E_100, E_140, E_421 confirmatorio, E_702)")
    log.info("=" * 78)

    tabela_metricas_estagios = construir_tabela_metricas_estagios(tabela_avaliacao, serie_semanal)
    tabela_metricas_estagios.to_csv(PASTA_SAIDAS / "metricas_estagios_oficiais.csv", index=False)

    tabela_mcnemar_combinada = construir_tabela_mcnemar_e421_e_familia_combinada(
        tabela_avaliacao, CAMINHO_MCNEMAR_25_09
    )
    tabela_mcnemar_combinada.to_csv(PASTA_SAIDAS / "mcnemar_holm_familia_combinada_24_testes.csv", index=False)

    tabela_criterio_e421 = avaliar_criterio_de_ganho_e421(tabela_metricas_estagios, tabela_mcnemar_combinada)
    tabela_criterio_e421.to_csv(PASTA_SAIDAS / "criterio_de_ganho_e421.csv", index=False)

    # ------------------------------------------------------------------
    # PARTE C — BLOCO-BOOTSTRAP DA INFLACAO DO P (roda depois de B)
    # ------------------------------------------------------------------
    log.info("=" * 78)
    log.info("PARTE C — bloco-bootstrap da inflacao do p (E_421 + tentativa do teste de 13/09)")
    log.info("=" * 78)

    tabela_bootstrap = construir_tabela_bootstrap_e421(tabela_avaliacao)
    linha_13_09 = registrar_teste_13_09_nao_localizado()
    tabela_bootstrap = pd.concat([tabela_bootstrap, pd.DataFrame([linha_13_09])], ignore_index=True)
    tabela_bootstrap.to_csv(PASTA_SAIDAS / "bootstrap_inflacao_p.csv", index=False)

    log.info(
        "Bootstrap: %d linhas (8 testes de E_421 x %d comprimentos de bloco = %d, "
        "+ 1 linha do teste de 13/09 NAO LOCALIZADO).",
        len(tabela_bootstrap),
        len(COMPRIMENTOS_BLOCO_BOOTSTRAP),
        8 * len(COMPRIMENTOS_BLOCO_BOOTSTRAP),
    )

    log.info("Arquivos gravados em %s", PASTA_SAIDAS)
    log.info("Fim da analise.")


if __name__ == "__main__":
    main()
