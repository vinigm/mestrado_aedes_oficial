"""Rodada D da segunda bateria noturna — calibracao conformal do quantil, sem treino.

Protocolo pre-declarado em `../PRE_DECLARACAO.md`, secao D. Este script NAO treina
nenhum modelo: le as previsoes ja geradas pela rodada A
(`../A_resultados_em_2026/saidas/previsoes_por_braco.csv`) para os dois bracos
q=0,85 do cenario adotado (HistGB folha 5, com vetor) e do HistGB folha 20 com
vetor, e aplica uma correcao conformal por origem sobre a previsao ja feita.

Correcao conformal por origem (pre-declaracao, secao D):
  Em cada linha (braco, h, data_alvo), a "origem" e a semana em que a previsao
  foi de fato emitida: origem = data_alvo - h semanas. A correcao soma ao
  `previsto` o quantil 0,85 empirico dos residuos (real - previsto) de TODOS os
  pares do MESMO braco e do MESMO h que ja tinham `data_alvo` respondida na
  origem (data_alvo_do_par <= origem), restritos a data_alvo_do_par >=
  2022-01-01. Com menos de 26 pares nessa janela, a linha fica sem correcao
  (previsto_corrigido = previsto).

⚠️ NAO altera `harness.py`, a rodada A nem nenhuma outra analise. So le. Grava
so dentro desta pasta (`saidas/`).
"""

import dataclasses
import logging
import pathlib

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# CAMINHOS
# ---------------------------------------------------------------------------

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"
CAMINHO_PREVISOES_DA_RODADA_A = (
    PASTA_DESTE_ARQUIVO.parent / "A_resultados_em_2026" / "saidas" / "previsoes_por_braco.csv"
)

# ---------------------------------------------------------------------------
# OS DOIS BRACOS DESTA RODADA (nomes identicos aos gravados pela rodada A)
# ---------------------------------------------------------------------------

NOME_CENARIO_ADOTADO = "HistGB_M1"
NOME_HISTGB_FOLHA20_M1 = "HistGB_folha20_M1"
BRACOS_DA_RODADA_D = (NOME_CENARIO_ADOTADO, NOME_HISTGB_FOLHA20_M1)

QUANTIL_DE_REFERENCIA = 0.85

# ---------------------------------------------------------------------------
# CORRECAO CONFORMAL POR ORIGEM
# ---------------------------------------------------------------------------

INICIO_DA_JANELA_DE_RESIDUOS = pd.Timestamp("2022-01-01")
MINIMO_DE_PARES_PARA_CORRIGIR = 26


def calcular_origem(data_alvo: pd.Series, horizonte: pd.Series) -> pd.Series:
    """Semana em que a previsao foi de fato emitida.

    A rodada A grava `data_alvo = data_do_teste + h semanas` (`harness.py`,
    `rodar_walk_forward`). A origem desfaz essa soma.

    Args:
        data_alvo: Semana que a previsao tenta acertar.
        horizonte: Quantas semanas a frente da origem essa previsao mira.

    Returns:
        A semana em que o modelo tinha, de fato, os dados para prever.
    """
    semanas_de_distancia = horizonte.apply(lambda h: pd.Timedelta(weeks=int(h)))
    return data_alvo - semanas_de_distancia


@dataclasses.dataclass(frozen=True)
class ResultadoDaCorrecao:
    """Resultado da correcao conformal de uma unica linha de previsao.

    Attributes:
        previsto_corrigido: `previsto` somado ao quantil 0,85 empirico dos
            residuos do pool, ou o proprio `previsto` quando o pool for
            pequeno demais.
        n_pares_no_pool: Quantos pares entraram no calculo do quantil.
        correcao_foi_aplicada: Se o pool teve pares suficientes.
        quantil_de_residuo_somado: O valor somado a `previsto` (0,0 quando a
            correcao nao foi aplicada, para deixar a soma sempre explicita).
    """

    previsto_corrigido: float
    n_pares_no_pool: int
    correcao_foi_aplicada: bool
    quantil_de_residuo_somado: float


def corrigir_uma_previsao(
    previsto_da_linha: float,
    origem_da_linha: pd.Timestamp,
    residuos_do_grupo: np.ndarray,
    datas_alvo_do_grupo: np.ndarray,
) -> ResultadoDaCorrecao:
    """Aplica a correcao conformal a uma previsao, usando so o que ja era sabido na origem.

    Args:
        previsto_da_linha: Previsao original (q0,85) desta linha.
        origem_da_linha: Semana em que esta previsao foi emitida.
        residuos_do_grupo: `real - previsto` de todas as linhas do MESMO braco
            e do MESMO horizonte (antes de qualquer filtro de data).
        datas_alvo_do_grupo: `data_alvo` alinhado posicionalmente com
            `residuos_do_grupo`.

    Returns:
        O resultado da correcao desta linha.
    """
    ja_respondido_na_origem = datas_alvo_do_grupo <= origem_da_linha
    dentro_da_janela_de_residuos = datas_alvo_do_grupo >= INICIO_DA_JANELA_DE_RESIDUOS
    mascara_do_pool = ja_respondido_na_origem & dentro_da_janela_de_residuos

    residuos_do_pool = residuos_do_grupo[mascara_do_pool]
    n_pares_no_pool = int(mascara_do_pool.sum())

    if n_pares_no_pool < MINIMO_DE_PARES_PARA_CORRIGIR:
        return ResultadoDaCorrecao(
            previsto_corrigido=previsto_da_linha,
            n_pares_no_pool=n_pares_no_pool,
            correcao_foi_aplicada=False,
            quantil_de_residuo_somado=0.0,
        )

    quantil_de_residuo = float(np.quantile(residuos_do_pool, QUANTIL_DE_REFERENCIA))
    return ResultadoDaCorrecao(
        previsto_corrigido=previsto_da_linha + quantil_de_residuo,
        n_pares_no_pool=n_pares_no_pool,
        correcao_foi_aplicada=True,
        quantil_de_residuo_somado=quantil_de_residuo,
    )


def calibrar_um_grupo(previsoes_do_grupo: pd.DataFrame) -> pd.DataFrame:
    """Aplica a correcao conformal a todas as linhas de um (braco, h).

    Args:
        previsoes_do_grupo: Linhas de um unico braco e um unico horizonte,
            com as colunas `data_alvo`, `real`, `previsto`, `origem`.

    Returns:
        `previsoes_do_grupo` acrescida de `previsto_corrigido`,
        `n_pares_no_pool`, `correcao_foi_aplicada` e `quantil_de_residuo_somado`.
    """
    residuos_do_grupo = (previsoes_do_grupo["real"] - previsoes_do_grupo["previsto"]).to_numpy()
    datas_alvo_do_grupo = previsoes_do_grupo["data_alvo"].to_numpy()

    resultados_da_linha = []
    for _, linha in previsoes_do_grupo.iterrows():
        resultado = corrigir_uma_previsao(
            previsto_da_linha=linha["previsto"],
            origem_da_linha=linha["origem"],
            residuos_do_grupo=residuos_do_grupo,
            datas_alvo_do_grupo=datas_alvo_do_grupo,
        )
        resultados_da_linha.append(resultado)

    previsoes_calibradas = previsoes_do_grupo.copy()
    previsoes_calibradas["previsto_corrigido"] = [r.previsto_corrigido for r in resultados_da_linha]
    previsoes_calibradas["n_pares_no_pool"] = [r.n_pares_no_pool for r in resultados_da_linha]
    previsoes_calibradas["correcao_foi_aplicada"] = [
        r.correcao_foi_aplicada for r in resultados_da_linha
    ]
    previsoes_calibradas["quantil_de_residuo_somado"] = [
        r.quantil_de_residuo_somado for r in resultados_da_linha
    ]
    return previsoes_calibradas


def montar_previsoes_calibradas(previsoes_dos_dois_bracos: pd.DataFrame) -> pd.DataFrame:
    """Aplica a correcao conformal a cada (braco, h) de forma independente.

    Args:
        previsoes_dos_dois_bracos: Previsoes de `NOME_CENARIO_ADOTADO` e de
            `NOME_HISTGB_FOLHA20_M1`, com `origem` ja calculada.

    Returns:
        Uma linha por previsao original, com as colunas de correcao
        acrescentadas. Linhas com `real` ou `previsto` vazios sao mantidas,
        sem entrar no pool de residuos de ninguem (NaN nunca e "menor ou
        igual" a uma data, entao a mascara as exclui automaticamente).
    """
    grupos_calibrados = []
    combinacoes_de_braco_e_h = previsoes_dos_dois_bracos[["braco", "h"]].drop_duplicates()

    for _, combinacao in combinacoes_de_braco_e_h.iterrows():
        do_grupo = previsoes_dos_dois_bracos[
            (previsoes_dos_dois_bracos["braco"] == combinacao["braco"])
            & (previsoes_dos_dois_bracos["h"] == combinacao["h"])
        ]
        grupos_calibrados.append(calibrar_um_grupo(do_grupo))

    return pd.concat(grupos_calibrados, ignore_index=True)


# ---------------------------------------------------------------------------
# RECORTES TEMPORAIS — identicos aos da rodada A (mesma pre-declaracao comum)
# ---------------------------------------------------------------------------

INICIO_RECORTE_2024_2025 = pd.Timestamp("2024-01-01")
FIM_RECORTE_2024_2025 = pd.Timestamp("2025-12-31")
INICIO_RECORTE_2026 = pd.Timestamp("2026-01-01")
FIM_RECORTE_2026 = pd.Timestamp("2026-04-19")

NOME_RECORTE_2024_2025 = "2024-2025"
NOME_RECORTE_2026 = "2026"
NOME_RECORTE_TUDO = "tudo"
NOMES_DOS_RECORTES = (NOME_RECORTE_2024_2025, NOME_RECORTE_2026, NOME_RECORTE_TUDO)


def selecionar_recorte(medicoes: pd.DataFrame, nome_do_recorte: str) -> pd.DataFrame:
    """Filtra as medicoes pelo recorte temporal pedido. Copia de `A/rodar.py`.

    Args:
        medicoes: DataFrame com a coluna `data_alvo`.
        nome_do_recorte: Um de "2024-2025", "2026" ou "tudo".

    Returns:
        As linhas de `medicoes` dentro do recorte.

    Raises:
        ValueError: Se o nome do recorte nao for reconhecido.
    """
    if nome_do_recorte == NOME_RECORTE_2024_2025:
        dentro_do_inicio = medicoes["data_alvo"] >= INICIO_RECORTE_2024_2025
        dentro_do_fim = medicoes["data_alvo"] <= FIM_RECORTE_2024_2025
        return medicoes[dentro_do_inicio & dentro_do_fim]

    if nome_do_recorte == NOME_RECORTE_2026:
        dentro_do_inicio = medicoes["data_alvo"] >= INICIO_RECORTE_2026
        dentro_do_fim = medicoes["data_alvo"] <= FIM_RECORTE_2026
        return medicoes[dentro_do_inicio & dentro_do_fim]

    if nome_do_recorte == NOME_RECORTE_TUDO:
        return medicoes

    raise ValueError(f"Recorte desconhecido: {nome_do_recorte}")


# ---------------------------------------------------------------------------
# METRICAS — cobertura, perda quantilica 0,85, MAE, alarmes falsos
# ---------------------------------------------------------------------------

LIMIARES_DE_ALARME = (100.0, 140.0)
HORIZONTES_DA_RODADA_D = (1, 4, 8, 12)


def calcular_perda_quantilica(valores_reais: np.ndarray, previsoes: np.ndarray) -> np.ndarray:
    """Perda pinball do quantil 0,85, uma linha por par (real, previsto).

    L(y, q) = 0,85 * (y - q), se y >= q
    L(y, q) = 0,15 * (q - y), se y <  q

    Args:
        valores_reais: Casos confirmados observados.
        previsoes: Previsao q0,85 (original ou corrigida).

    Returns:
        A perda de cada par, na mesma ordem de entrada.
    """
    residuo = valores_reais - previsoes
    mascara_real_maior_ou_igual = residuo >= 0

    perda = np.where(
        mascara_real_maior_ou_igual,
        QUANTIL_DE_REFERENCIA * residuo,
        (QUANTIL_DE_REFERENCIA - 1.0) * residuo,
    )
    return perda


def montar_metricas_de_uma_versao(
    previsoes_validas: pd.DataFrame, coluna_da_previsao: str, versao: str
) -> list[dict[str, object]]:
    """Cobertura, perda quantilica, MAE e alarmes falsos de uma versao da previsao.

    Args:
        previsoes_validas: Linhas com `real` e a coluna de previsao nao vazios.
        coluna_da_previsao: "previsto" (original) ou "previsto_corrigido".
        versao: Rotulo gravado na tabela ("original" ou "corrigida").

    Returns:
        Uma linha por (braco, h, recorte), com as quatro metricas.
    """
    linhas_da_tabela = []

    for nome_do_braco in BRACOS_DA_RODADA_D:
        do_braco = previsoes_validas[previsoes_validas["braco"] == nome_do_braco]

        for horizonte in HORIZONTES_DA_RODADA_D:
            do_horizonte = do_braco[do_braco["h"] == horizonte]

            for nome_do_recorte in NOMES_DOS_RECORTES:
                do_recorte = selecionar_recorte(do_horizonte, nome_do_recorte)

                if len(do_recorte) == 0:
                    linhas_da_tabela.append(
                        {
                            "braco": nome_do_braco,
                            "h": horizonte,
                            "recorte": nome_do_recorte,
                            "versao": versao,
                            "n_semanas": 0,
                            "cobertura": np.nan,
                            "perda_quantilica_085": np.nan,
                            "mae": np.nan,
                            "n_alarmes_falsos_limiar_100": np.nan,
                            "n_alarmes_falsos_limiar_140": np.nan,
                        }
                    )
                    continue

                valores_reais = do_recorte["real"].to_numpy()
                valores_previstos = do_recorte[coluna_da_previsao].to_numpy()

                cobertura = float(np.mean(valores_reais <= valores_previstos))
                perda_quantilica = float(
                    np.mean(calcular_perda_quantilica(valores_reais, valores_previstos))
                )
                mae = float(np.mean(np.abs(valores_reais - valores_previstos)))

                linha_de_metricas = {
                    "braco": nome_do_braco,
                    "h": horizonte,
                    "recorte": nome_do_recorte,
                    "versao": versao,
                    "n_semanas": len(do_recorte),
                    "cobertura": cobertura,
                    "perda_quantilica_085": perda_quantilica,
                    "mae": mae,
                }

                for limiar in LIMIARES_DE_ALARME:
                    alarme_emitido = valores_previstos > limiar
                    surto_real = valores_reais > limiar
                    n_alarmes_falsos = int((alarme_emitido & ~surto_real).sum())
                    linha_de_metricas[f"n_alarmes_falsos_limiar_{int(limiar)}"] = n_alarmes_falsos

                linhas_da_tabela.append(linha_de_metricas)

    return linhas_da_tabela


def montar_tabela_de_metricas(previsoes_calibradas: pd.DataFrame) -> pd.DataFrame:
    """Metricas da previsao original e da corrigida, lado a lado por linha.

    Args:
        previsoes_calibradas: Saida de `montar_previsoes_calibradas`.

    Returns:
        Uma linha por (braco, h, recorte, versao), com cobertura, perda
        quantilica 0,85, MAE e alarmes falsos nos limiares 100 e 140.
    """
    previsoes_validas = previsoes_calibradas.dropna(subset=["real", "previsto"])

    linhas_originais = montar_metricas_de_uma_versao(previsoes_validas, "previsto", "original")
    linhas_corrigidas = montar_metricas_de_uma_versao(
        previsoes_validas, "previsto_corrigido", "corrigida"
    )

    return pd.DataFrame(linhas_originais + linhas_corrigidas)


# ---------------------------------------------------------------------------
# FAMILIA D — perda quantilica corrigida x original, Wilcoxon + Holm sobre 4
#   (2 bracos x horizontes 4 e 12), com Holm calculado por recorte.
#
# Decisao registrada no retorno estruturado: a pre-declaracao pede "familia de
# 4" sem amarrar a um recorte especifico. Sigo o padrao da rodada A
# (`montar_familia_a1`): cada recorte recebe a SUA PROPRIA correcao de Holm
# sobre as suas 4 comparacoes, sem misturar entre recortes.
# ---------------------------------------------------------------------------

HORIZONTES_DA_FAMILIA_D = (4, 12)


def corrigir_por_holm(p_brutos: list[float]) -> list[float]:
    """Correcao de Holm sobre uma familia de p-valores. Copia de `A/rodar.py`.

    Args:
        p_brutos: Todos os p-valores da familia, na ordem original.

    Returns:
        Os p-valores corrigidos, na MESMA ordem de `p_brutos`.
    """
    quantidade_de_testes = len(p_brutos)
    indices_ordenados_por_p = sorted(range(quantidade_de_testes), key=lambda i: p_brutos[i])

    p_corrigidos_na_ordem_original = [0.0] * quantidade_de_testes
    maior_p_ate_agora = 0.0

    for posicao, indice_original in enumerate(indices_ordenados_por_p):
        p_ajustado = min(1.0, p_brutos[indice_original] * (quantidade_de_testes - posicao))
        maior_p_ate_agora = max(maior_p_ate_agora, p_ajustado)
        p_corrigidos_na_ordem_original[indice_original] = maior_p_ate_agora

    return p_corrigidos_na_ordem_original


def comparar_perda_corrigida_x_original(
    previsoes_validas: pd.DataFrame, nome_do_braco: str, horizonte: int
) -> dict[str, object]:
    """Compara a perda quantilica corrigida com a original, pareada linha a linha.

    O pareamento e trivial aqui (nao precisa de merge por `data_alvo`): a
    corrigida e a original vem da MESMA linha de previsao, so muda a coluna.

    Args:
        previsoes_validas: Previsoes de um unico (braco, recorte), com `real`,
            `previsto` e `previsto_corrigido` nao vazios.
        nome_do_braco: Braco desta comparacao.
        horizonte: Horizonte h desta comparacao.

    Returns:
        Dicionario com as perdas medias dos dois lados, a reducao percentual
        da correcao, o p bruto de Wilcoxon e o n de semanas usadas.
    """
    do_horizonte = previsoes_validas[previsoes_validas["h"] == horizonte]

    if do_horizonte.empty:
        return {
            "braco": nome_do_braco,
            "horizonte": horizonte,
            "perda_original": np.nan,
            "perda_corrigida": np.nan,
            "reducao_percentual_da_correcao": np.nan,
            "p_bruto": np.nan,
            "n_semanas": 0,
        }

    valores_reais = do_horizonte["real"].to_numpy()
    perda_original = calcular_perda_quantilica(valores_reais, do_horizonte["previsto"].to_numpy())
    perda_corrigida = calcular_perda_quantilica(
        valores_reais, do_horizonte["previsto_corrigido"].to_numpy()
    )

    if np.allclose(perda_original, perda_corrigida):
        p_bruto = 1.0
    else:
        _, p_bruto = stats.wilcoxon(perda_corrigida, perda_original)

    media_perda_original = float(np.mean(perda_original))
    media_perda_corrigida = float(np.mean(perda_corrigida))
    reducao_percentual = (
        100.0 * (media_perda_original - media_perda_corrigida) / media_perda_original
    )

    return {
        "braco": nome_do_braco,
        "horizonte": horizonte,
        "perda_original": media_perda_original,
        "perda_corrigida": media_perda_corrigida,
        "reducao_percentual_da_correcao": reducao_percentual,
        "p_bruto": float(p_bruto),
        "n_semanas": len(do_horizonte),
    }


def montar_familia_d(previsoes_calibradas: pd.DataFrame) -> pd.DataFrame:
    """Familia D inteira: 2 bracos x h(4,12), Holm por recorte.

    Args:
        previsoes_calibradas: Saida de `montar_previsoes_calibradas`.

    Returns:
        Uma linha por (braco, horizonte, recorte), com p_holm e o veredito de
        significancia a 5%.
    """
    previsoes_validas = previsoes_calibradas.dropna(subset=["real", "previsto", "previsto_corrigido"])

    linhas_de_todos_os_recortes = []

    for nome_do_recorte in NOMES_DOS_RECORTES:
        do_recorte = selecionar_recorte(previsoes_validas, nome_do_recorte)

        comparacoes_do_recorte = []
        for nome_do_braco in BRACOS_DA_RODADA_D:
            do_braco = do_recorte[do_recorte["braco"] == nome_do_braco]
            for horizonte in HORIZONTES_DA_FAMILIA_D:
                comparacoes_do_recorte.append(
                    comparar_perda_corrigida_x_original(do_braco, nome_do_braco, horizonte)
                )

        p_brutos = [c["p_bruto"] for c in comparacoes_do_recorte]
        p_holm = corrigir_por_holm(p_brutos)

        for comparacao, p_holm_da_linha in zip(comparacoes_do_recorte, p_holm):
            linha = dict(comparacao)
            linha["recorte"] = nome_do_recorte
            linha["p_holm"] = p_holm_da_linha
            linha["significativo_5pct"] = p_holm_da_linha < 0.05
            linhas_de_todos_os_recortes.append(linha)

    return pd.DataFrame(linhas_de_todos_os_recortes)


# ---------------------------------------------------------------------------
# ORQUESTRACAO
# ---------------------------------------------------------------------------


def main() -> None:
    """Le as previsoes da rodada A, calibra por origem e grava as 3 saidas."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    log = logging.getLogger(__name__)

    print("=" * 78)
    print("RODADA D — segunda bateria noturna: calibracao do quantil, sem treino")
    print("=" * 78, flush=True)

    if not CAMINHO_PREVISOES_DA_RODADA_A.exists():
        raise FileNotFoundError(
            "Previsoes da rodada A ainda nao existem em "
            f"{CAMINHO_PREVISOES_DA_RODADA_A}. A rodada D depende da A ja concluida."
        )

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)

    todas_as_previsoes = pd.read_csv(CAMINHO_PREVISOES_DA_RODADA_A, parse_dates=["data_alvo"])
    log.info("Previsoes da rodada A lidas: %d linhas, %d bracos.", len(todas_as_previsoes), todas_as_previsoes["braco"].nunique())

    previsoes_dos_dois_bracos = todas_as_previsoes[
        todas_as_previsoes["braco"].isin(BRACOS_DA_RODADA_D)
    ].copy()
    previsoes_dos_dois_bracos["origem"] = calcular_origem(
        previsoes_dos_dois_bracos["data_alvo"], previsoes_dos_dois_bracos["h"]
    )
    log.info("Linhas dos 2 bracos da rodada D: %d.", len(previsoes_dos_dois_bracos))

    previsoes_calibradas = montar_previsoes_calibradas(previsoes_dos_dois_bracos)
    previsoes_calibradas.to_csv(PASTA_DE_SAIDAS / "previsoes_calibradas.csv", index=False)
    log.info(
        "Correcao aplicada em %d de %d linhas (o resto tinha pool < %d pares).",
        int(previsoes_calibradas["correcao_foi_aplicada"].sum()),
        len(previsoes_calibradas),
        MINIMO_DE_PARES_PARA_CORRIGIR,
    )

    metricas = montar_tabela_de_metricas(previsoes_calibradas)
    metricas.to_csv(PASTA_DE_SAIDAS / "metricas.csv", index=False)

    familia_d = montar_familia_d(previsoes_calibradas)
    familia_d.to_csv(PASTA_DE_SAIDAS / "familia_d.csv", index=False)

    print("\nFAMILIA D (recorte tudo):")
    print(familia_d[familia_d["recorte"] == NOME_RECORTE_TUDO].to_string(index=False))

    print("\nCONCLUIDO.")


if __name__ == "__main__":
    main()
