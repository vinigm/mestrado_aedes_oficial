"""Braço SARIMA da bateria SARIMA+LASSO+ensemble — 25/09/2026.

Protocolo completo em PRE_DECLARACAO.md (leitura obrigatória, é o contrato desta
rodada). Este script roda só o braço `sarima_log`: a régua sazonal (diferença
sazonal de 52 semanas) mais uma correção autorregressiva curta (AR(2), sem
constante), em log1p(casos_confirmados).

Roda no venv isolado `~/.venvs/aedes_modelos_fundacao/` (Python 3.12,
statsmodels 0.15.0) — o Python do pipeline (3.14) não tem essa dependência
instalada.

⚠️ NÃO altera nada fora desta pasta. Lê `tabela_final.csv` só para as colunas
'data_inicio_semana_epidemi' e 'casos_confirmados', e o CSV de previsões do
braço `HistGB_folha20_M1` do bloco 7 só para descobrir os pares (h, data_alvo)
que a bateria inteira usa — nenhum dos dois é escrito.

Uso:

    python rodar_sarima.py --smoke        # todos os 4 horizontes, ultimas 5 origens
    python rodar_sarima.py --cronometro    # 1 celula completa (h=12, todas as origens)
    python rodar_sarima.py --rodar-tudo    # bateria completa, os 4 horizontes (NAO RODAR
                                            # nesta entrega — só smoke test e cronômetro)
"""

import argparse
import dataclasses
import pathlib
import time

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

# ============================================================================
# CAMINHOS
# ============================================================================

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DO_PROJETO = PASTA_DESTE_ARQUIVO.parent.parent

CAMINHO_TABELA_FINAL = (
    PASTA_DO_PROJETO / "modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv"
)
CAMINHO_PREVISOES_B0 = (
    PASTA_DO_PROJETO
    / "analises/2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/saidas/previsoes_por_braco.csv"
)
NOME_DO_BRACO_B0_NO_BLOCO_7 = "HistGB_folha20_M1"

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

# ============================================================================
# CONSTANTES DE NEGÓCIO (seção 2 da pré-declaração, braço sarima_log)
# ============================================================================

HORIZONTES_DA_BATERIA = (1, 4, 8, 12)
INICIO_DA_SERIE_DE_CASOS = pd.Timestamp("2018-02-18")
SEMANAS_DO_PASSO_SAZONAL = 52
PASSOS_DE_PREVISAO = 12

# z da normal padrão no quantil 0,85 (norm.ppf(0.85) = 1.03643...), fixado na
# pré-declaração para não depender de scipy.stats.norm dentro do laço.
Z_DO_QUANTIL_085 = 1.0364

QUANTIL_DE_REFERENCIA_BAIXO = "q050"
QUANTIL_DE_REFERENCIA_ALTO = "q085"

N_ORIGENS_DO_SMOKE = 5
HORIZONTE_DO_CRONOMETRO = 12

# Comprimento mínimo de histórico para tentar o ajuste: duas voltas do ciclo
# sazonal mais a ordem AR. Abaixo disso o SARIMAX(0,1,0,52) não tem graus de
# liberdade para estimar a diferença sazonal — tratado como falha de
# convergência, mesma regra e mesmo fallback da seção 2.
MINIMO_DE_SEMANAS_PARA_AJUSTAR = 2 * SEMANAS_DO_PASSO_SAZONAL + 2


@dataclasses.dataclass(frozen=True)
class ConfiguracaoSarima:
    """Os hiperparâmetros do braço `sarima_log`, fixados na seção 2 da pré-declaração.

    Attributes:
        ordem_ar: (p, d, q) da parte não sazonal — AR(2), sem diferenciação
            nem média móvel.
        ordem_sazonal: (P, D, Q, s) da parte sazonal — só a diferença sazonal
            de 52 semanas, sem AR nem MA sazonais.
        tendencia: 'n' — sem constante. É o que faz a correção autorregressiva
            desaparecer em horizontes longos e a previsão convergir para a
            régua sazonal pura.
        passos_de_previsao: Quantos passos a frente o `get_forecast` calcula
            de uma vez; o horizonte pedido é lido na posição `h - 1` do
            resultado.
        z_do_quantil_085: Escore z da normal padrão usado para construir o
            quantil 0,85 a partir de média e erro-padrão da previsão em log.
    """

    ordem_ar: tuple[int, int, int]
    ordem_sazonal: tuple[int, int, int, int]
    tendencia: str
    passos_de_previsao: int
    z_do_quantil_085: float


CONFIGURACAO_SARIMA = ConfiguracaoSarima(
    ordem_ar=(2, 0, 0),
    ordem_sazonal=(0, 1, 0, 52),
    tendencia="n",
    passos_de_previsao=PASSOS_DE_PREVISAO,
    z_do_quantil_085=Z_DO_QUANTIL_085,
)


@dataclasses.dataclass(frozen=True)
class ResultadoDoAjuste:
    """O que sai de uma tentativa de ajustar o SARIMAX numa origem.

    Attributes:
        convergiu: Se o otimizador convergiu (`mle_retvals['converged']`) e
            nenhuma exceção foi lançada durante o ajuste ou a previsão.
        media_da_previsao: Média da previsão em log1p(casos), uma por passo
            (tamanho `passos_de_previsao`). Vazio quando não convergiu.
        erro_padrao_da_previsao: Erro-padrão da previsão em log1p(casos), na
            mesma posição da média. Vazio quando não convergiu.
    """

    convergiu: bool
    media_da_previsao: np.ndarray
    erro_padrao_da_previsao: np.ndarray


# ============================================================================
# LEITURA
# ============================================================================


def carregar_serie_semanal_de_casos(caminho_tabela_final: pathlib.Path) -> pd.DataFrame:
    """Lê só as duas colunas que o braço `sarima_log` usa, em ordem cronológica.

    ⚠️ Não passa por `acesso.fontes.carregar_tabela_final` de propósito: a
    pré-declaração pede leitura direta do CSV, com os nomes de coluna originais
    ('data_inicio_semana_epidemi', 'casos_confirmados'), sem o corte de
    maturidade nem as demais transformações do pipeline de features.

    Args:
        caminho_tabela_final: Caminho do `tabela_final.csv`.

    Returns:
        Uma linha por semana, colunas 'data' e 'casos', em ordem cronológica.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        KeyError: Se as colunas esperadas não estiverem presentes.
    """
    if not caminho_tabela_final.exists():
        raise FileNotFoundError(f"Tabela final nao encontrada: {caminho_tabela_final}")

    tabela_bruta = pd.read_csv(
        caminho_tabela_final,
        parse_dates=["data_inicio_semana_epidemi"],
    )

    colunas_obrigatorias = {"data_inicio_semana_epidemi", "casos_confirmados"}
    colunas_ausentes = colunas_obrigatorias.difference(tabela_bruta.columns)
    if colunas_ausentes:
        raise KeyError(f"Colunas obrigatorias ausentes em tabela_final.csv: {sorted(colunas_ausentes)}")

    serie_semanal = tabela_bruta[["data_inicio_semana_epidemi", "casos_confirmados"]].rename(
        columns={"data_inicio_semana_epidemi": "data", "casos_confirmados": "casos"}
    )
    serie_semanal = serie_semanal.sort_values("data").reset_index(drop=True)
    return serie_semanal


def carregar_pares_h_data_alvo_do_b0(
    caminho_previsoes_b0: pathlib.Path, nome_do_braco: str
) -> pd.DataFrame:
    """Lê os pares (h, data_alvo) do braço B0, que fixam a grade de toda a bateria.

    Args:
        caminho_previsoes_b0: CSV de previsões do bloco 7 da bateria noturna.
        nome_do_braco: Nome do braço B0 dentro desse CSV
            ('HistGB_folha20_M1').

    Returns:
        Um par (h, data_alvo) por linha, sem repetição, ordenado por h e por
        data_alvo.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se o braço pedido não aparecer no arquivo.
    """
    if not caminho_previsoes_b0.exists():
        raise FileNotFoundError(f"Previsoes do B0 nao encontradas: {caminho_previsoes_b0}")

    previsoes_do_bloco_7 = pd.read_csv(caminho_previsoes_b0, parse_dates=["data_alvo"])
    previsoes_do_b0 = previsoes_do_bloco_7[previsoes_do_bloco_7["braco"] == nome_do_braco]

    if previsoes_do_b0.empty:
        bracos_disponiveis = sorted(previsoes_do_bloco_7["braco"].unique())
        raise ValueError(f"Braco '{nome_do_braco}' nao encontrado. Disponiveis: {bracos_disponiveis}")

    pares_h_data_alvo = (
        previsoes_do_b0[["h", "data_alvo"]]
        .drop_duplicates()
        .sort_values(["h", "data_alvo"])
        .reset_index(drop=True)
    )
    return pares_h_data_alvo


# ============================================================================
# CÁLCULO — UMA ORIGEM
# ============================================================================


def calcular_data_de_origem(data_alvo: pd.Timestamp, horizonte: int) -> pd.Timestamp:
    """origem = data_alvo − h semanas, regra fixada na seção 2 da pré-declaração."""
    return data_alvo - pd.Timedelta(weeks=horizonte)


def selecionar_contexto_ate_a_origem(
    serie_semanal_de_casos: pd.DataFrame,
    origem: pd.Timestamp,
    inicio_da_serie: pd.Timestamp,
) -> pd.DataFrame:
    """Recorta a série de 18/02/2018 até a origem, inclusive — nunca além dela.

    Args:
        serie_semanal_de_casos: Série completa, colunas 'data' e 'casos'.
        origem: Última data que o ajuste pode enxergar.
        inicio_da_serie: Início do recorte (18/02/2018, fixado na pré-declaração).

    Returns:
        O recorte, em ordem cronológica. Vazio se a origem for anterior ao
        início da série.
    """
    dentro_do_recorte = (serie_semanal_de_casos["data"] >= inicio_da_serie) & (
        serie_semanal_de_casos["data"] <= origem
    )
    return serie_semanal_de_casos.loc[dentro_do_recorte].reset_index(drop=True)


def ajustar_sarima_e_prever(
    casos_em_log1p: np.ndarray, configuracao: ConfiguracaoSarima
) -> ResultadoDoAjuste:
    """Ajusta o SARIMAX no contexto e prevê `passos_de_previsao` semanas à frente.

    Qualquer exceção do ajuste ou da previsão, e qualquer não-convergência
    reportada pelo otimizador (`mle_retvals['converged']`), viram
    `convergiu=False` — nunca deixam o laço da bateria parar no meio.

    Args:
        casos_em_log1p: A série de contexto, já em log1p(casos), em ordem
            cronológica.
        configuracao: Ordem AR, ordem sazonal, tendência e horizonte de
            previsão do braço `sarima_log`.

    Returns:
        O resultado do ajuste, com a bandeira de convergência.
    """
    try:
        modelo = SARIMAX(
            casos_em_log1p,
            order=configuracao.ordem_ar,
            seasonal_order=configuracao.ordem_sazonal,
            trend=configuracao.tendencia,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        resultado_do_ajuste = modelo.fit(disp=False)
        convergiu = bool(resultado_do_ajuste.mle_retvals.get("converged", True))

        previsao = resultado_do_ajuste.get_forecast(steps=configuracao.passos_de_previsao)
        media_da_previsao = np.asarray(previsao.predicted_mean)
        erro_padrao_da_previsao = np.asarray(previsao.se_mean)

    except Exception:  # noqa: BLE001 — qualquer falha de otimizacao vira fallback, por design.
        convergiu = False
        media_da_previsao = np.array([])
        erro_padrao_da_previsao = np.array([])

    if not convergiu:
        return ResultadoDoAjuste(False, np.array([]), np.array([]))

    return ResultadoDoAjuste(True, media_da_previsao, erro_padrao_da_previsao)


def calcular_previsao_da_regua_sazonal(
    serie_semanal_de_casos: pd.DataFrame, data_alvo: pd.Timestamp
) -> float:
    """O fallback de não-convergência: casos confirmados 52 semanas antes de data_alvo.

    Args:
        serie_semanal_de_casos: Série completa, colunas 'data' e 'casos'.
        data_alvo: A semana que o braço está tentando prever.

    Returns:
        O caso confirmado da semana correspondente um ano antes, ou NaN se
        essa semana não existir na série ou o valor lá for nulo.
    """
    semana_um_ano_antes = data_alvo - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)
    linha_correspondente = serie_semanal_de_casos.loc[
        serie_semanal_de_casos["data"] == semana_um_ano_antes, "casos"
    ]
    if linha_correspondente.empty:
        return np.nan
    return float(linha_correspondente.to_numpy()[0])


def montar_previsao_de_uma_origem(
    serie_semanal_de_casos: pd.DataFrame,
    horizonte: int,
    data_alvo: pd.Timestamp,
    configuracao: ConfiguracaoSarima,
) -> dict[str, object]:
    """Roda o braço `sarima_log` para um único par (h, data_alvo).

    Regras da seção 2 da pré-declaração:
        - ajusta em log1p(casos) de 18/02/2018 até a origem;
        - q050 = expm1(média); q085 = expm1(média + z·erro-padrão), no passo h;
        - previsão negativa vira 0;
        - falha de convergência (ou histórico curto demais) usa a régua
          sazonal para os dois quantis, e é contada.

    Args:
        serie_semanal_de_casos: Série completa, colunas 'data' e 'casos'.
        horizonte: h, em semanas.
        data_alvo: A semana-alvo deste par.
        configuracao: Hiperparâmetros do braço.

    Returns:
        Uma linha de resultado, pronta para compor o CSV de saída.
    """
    origem = calcular_data_de_origem(data_alvo, horizonte)
    contexto = selecionar_contexto_ate_a_origem(
        serie_semanal_de_casos, origem, INICIO_DA_SERIE_DE_CASOS
    )

    historico_suficiente = len(contexto) >= MINIMO_DE_SEMANAS_PARA_AJUSTAR
    if historico_suficiente:
        casos_em_log1p = np.log1p(contexto["casos"].to_numpy())
        resultado_do_ajuste = ajustar_sarima_e_prever(casos_em_log1p, configuracao)
    else:
        resultado_do_ajuste = ResultadoDoAjuste(False, np.array([]), np.array([]))

    if resultado_do_ajuste.convergiu:
        media_no_passo_h = resultado_do_ajuste.media_da_previsao[horizonte - 1]
        erro_padrao_no_passo_h = resultado_do_ajuste.erro_padrao_da_previsao[horizonte - 1]
        previsao_q050 = float(np.expm1(media_no_passo_h))
        previsao_q085 = float(
            np.expm1(media_no_passo_h + configuracao.z_do_quantil_085 * erro_padrao_no_passo_h)
        )
        usou_regua_de_fallback = False
    else:
        previsao_da_regua = calcular_previsao_da_regua_sazonal(serie_semanal_de_casos, data_alvo)
        previsao_q050 = previsao_da_regua
        previsao_q085 = previsao_da_regua
        usou_regua_de_fallback = True

    previsao_q050 = max(0.0, previsao_q050) if not np.isnan(previsao_q050) else previsao_q050
    previsao_q085 = max(0.0, previsao_q085) if not np.isnan(previsao_q085) else previsao_q085

    valor_real = serie_semanal_de_casos.loc[serie_semanal_de_casos["data"] == data_alvo, "casos"]

    return {
        "h": horizonte,
        "origem": origem,
        "data_alvo": data_alvo,
        # A última data REAL do contexto ajustado, e não a origem calculada:
        # só assim a trava 2 do combinador consegue pegar um contexto que
        # passe da origem (apontamento da revisão pré-rodada de 25/09/2026).
        "ultima_data_ajuste": contexto["data"].max(),
        "real": float(valor_real.to_numpy()[0]) if not valor_real.empty else np.nan,
        QUANTIL_DE_REFERENCIA_BAIXO: previsao_q050,
        QUANTIL_DE_REFERENCIA_ALTO: previsao_q085,
        "convergiu": resultado_do_ajuste.convergiu,
        "usou_regua_de_fallback": usou_regua_de_fallback,
    }


# ============================================================================
# CÁLCULO — UMA CÉLULA (todas as origens de um horizonte)
# ============================================================================


def rodar_celula_do_horizonte(
    serie_semanal_de_casos: pd.DataFrame,
    horizonte: int,
    pares_h_data_alvo: pd.DataFrame,
    configuracao: ConfiguracaoSarima,
    limite_de_ultimas_origens: int | None = None,
) -> pd.DataFrame:
    """Roda o braço `sarima_log` em todas as origens de um horizonte.

    Args:
        serie_semanal_de_casos: Série completa, colunas 'data' e 'casos'.
        horizonte: h, em semanas.
        pares_h_data_alvo: Grade (h, data_alvo) vinda do B0.
        configuracao: Hiperparâmetros do braço.
        limite_de_ultimas_origens: Quando preenchido, roda só as últimas N
            origens do horizonte (usado pelo `--smoke`).

    Returns:
        Uma linha por origem avaliada.
    """
    datas_alvo_do_horizonte = (
        pares_h_data_alvo.loc[pares_h_data_alvo["h"] == horizonte, "data_alvo"]
        .sort_values()
        .reset_index(drop=True)
    )

    if limite_de_ultimas_origens is not None:
        datas_alvo_do_horizonte = datas_alvo_do_horizonte.tail(limite_de_ultimas_origens)

    linhas_do_resultado: list[dict[str, object]] = []
    for data_alvo in datas_alvo_do_horizonte:
        linha = montar_previsao_de_uma_origem(
            serie_semanal_de_casos, horizonte, pd.Timestamp(data_alvo), configuracao
        )
        linhas_do_resultado.append(linha)

    return pd.DataFrame(linhas_do_resultado)


# ============================================================================
# SMOKE TEST
# ============================================================================


def rodar_smoke_test(serie_semanal_de_casos: pd.DataFrame, pares_h_data_alvo: pd.DataFrame) -> None:
    """--smoke: os 4 horizontes, últimas 5 origens de cada, previsões impressas."""
    for horizonte in HORIZONTES_DA_BATERIA:
        inicio = time.perf_counter()
        previsoes = rodar_celula_do_horizonte(
            serie_semanal_de_casos,
            horizonte,
            pares_h_data_alvo,
            CONFIGURACAO_SARIMA,
            limite_de_ultimas_origens=N_ORIGENS_DO_SMOKE,
        )
        duracao = time.perf_counter() - inicio
        print(f"\n[smoke] sarima_log  h={horizonte}", flush=True)
        print(previsoes.to_string(index=False), flush=True)
        print(f"[smoke] h={horizonte}  {duracao:.2f}s ({len(previsoes)} origens)", flush=True)

    print("\n[smoke] TODOS OS HORIZONTES RODARAM SEM ERRO.", flush=True)


# ============================================================================
# CRONÔMETRO
# ============================================================================


def cronometrar_celula_completa(
    serie_semanal_de_casos: pd.DataFrame, pares_h_data_alvo: pd.DataFrame, horizonte: int
) -> tuple[pd.DataFrame, float]:
    """Roda uma célula inteira (todas as origens do horizonte) e cronometra."""
    inicio = time.perf_counter()
    previsoes = rodar_celula_do_horizonte(
        serie_semanal_de_casos, horizonte, pares_h_data_alvo, CONFIGURACAO_SARIMA
    )
    duracao = time.perf_counter() - inicio
    return previsoes, duracao


# ============================================================================
# BATERIA COMPLETA (não executada nesta entrega — só implementada)
# ============================================================================


def rodar_bateria_completa(
    serie_semanal_de_casos: pd.DataFrame, pares_h_data_alvo: pd.DataFrame
) -> None:
    """Roda os 4 horizontes por completo e grava `saidas/previsoes_sarima.csv`.

    ⚠️ NÃO EXECUTADO nesta entrega — o brief pediu só smoke test e cronômetro.
    Ver `desvios_e_decisoes` no retorno estruturado da tarefa.
    """
    previsoes_de_todos_os_horizontes: list[pd.DataFrame] = []
    for horizonte in HORIZONTES_DA_BATERIA:
        marca = time.perf_counter()
        previsoes_do_horizonte = rodar_celula_do_horizonte(
            serie_semanal_de_casos, horizonte, pares_h_data_alvo, CONFIGURACAO_SARIMA
        )
        previsoes_de_todos_os_horizontes.append(previsoes_do_horizonte)
        n_fallback = int(previsoes_do_horizonte["usou_regua_de_fallback"].sum())
        print(
            f"[sarima_log] h={horizonte:2d}  {len(previsoes_do_horizonte):3d} origens  "
            f"{n_fallback} com fallback da regua  {time.perf_counter() - marca:6.1f}s",
            flush=True,
        )

    todas_as_previsoes = pd.concat(previsoes_de_todos_os_horizontes, ignore_index=True)
    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    todas_as_previsoes.to_csv(PASTA_DE_SAIDAS / "previsoes_sarima.csv", index=False)
    print(f"Gravado: previsoes_sarima.csv ({len(todas_as_previsoes)} linhas)", flush=True)


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--cronometro", action="store_true")
    parser.add_argument("--rodar-tudo", action="store_true", dest="rodar_tudo")
    argumentos = parser.parse_args()

    nenhuma_acao_pedida = not any([argumentos.smoke, argumentos.cronometro, argumentos.rodar_tudo])
    if nenhuma_acao_pedida:
        parser.print_help()
        return

    serie_semanal_de_casos = carregar_serie_semanal_de_casos(CAMINHO_TABELA_FINAL)
    pares_h_data_alvo = carregar_pares_h_data_alvo_do_b0(
        CAMINHO_PREVISOES_B0, NOME_DO_BRACO_B0_NO_BLOCO_7
    )

    if argumentos.smoke:
        rodar_smoke_test(serie_semanal_de_casos, pares_h_data_alvo)

    if argumentos.cronometro:
        previsoes, duracao = cronometrar_celula_completa(
            serie_semanal_de_casos, pares_h_data_alvo, HORIZONTE_DO_CRONOMETRO
        )
        PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
        previsoes.to_csv(PASTA_DE_SAIDAS / f"cronometro_sarima_h{HORIZONTE_DO_CRONOMETRO}.csv", index=False)
        n_fallback = int(previsoes["usou_regua_de_fallback"].sum())
        print(
            f"[cronometro] sarima_log h={HORIZONTE_DO_CRONOMETRO}, {len(previsoes)} origens, "
            f"{n_fallback} com fallback da regua: {duracao:.1f}s "
            f"({duracao / max(len(previsoes), 1):.3f}s/origem)"
        )

    if argumentos.rodar_tudo:
        rodar_bateria_completa(serie_semanal_de_casos, pares_h_data_alvo)


if __name__ == "__main__":
    main()
