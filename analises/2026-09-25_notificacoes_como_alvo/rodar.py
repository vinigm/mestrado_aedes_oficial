"""Rodada 'notificacoes como alvo' — protocolo em PRE_DECLARACAO.md.

Cinco bracos (T0, C0, N1, C2a, C2b), todos HistGB folha minima 20 (a
configuracao do bloco 7 da bateria noturna de 23/09/2026), horizontes 1, 4,
8 e 12, sobre a tabela desta analise (dados/tabela_cevs.csv), que troca a
coluna de casos da tabela_final oficial pela serie do CEVS.

Reaproveita o motor `harness.py` da bateria noturna (montagem de features,
walk-forward com corte pela data da resposta, comparacao pareada e Holm) SEM
alterar aquele arquivo. So o carregamento da tabela bruta e a troca do alvo
por braco sao feitos aqui, porque o harness sempre chama
`fontes.carregar_tabela_final()` (a tabela oficial).

⚠️ NAO altera nada em modelagem_aedes/. So le.
"""

import pathlib
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

PASTA_DESTA_ANALISE = pathlib.Path(__file__).resolve().parent
PASTA_DA_BATERIA_NOTURNA = PASTA_DESTA_ANALISE.parent / "2026-09-23_bateria_noturna"
sys.path.insert(0, str(PASTA_DA_BATERIA_NOTURNA))
sys.path.insert(0, str(PASTA_DESTA_ANALISE.parent.parent / "modelagem_aedes"))

import harness  # noqa: E402  (motor da bateria noturna, nao alterado)
from config.experimentos.cidade_referencia import CIDADE_REFERENCIA  # noqa: E402
from config.modelo import EspecificacaoModelo  # noqa: E402

CAMINHO_TABELA_DA_RODADA = PASTA_DESTA_ANALISE / "dados" / "tabela_cevs.csv"
PASTA_DE_SAIDAS = PASTA_DESTA_ANALISE / "saidas"

INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")
FIM_DO_RECORTE_2024_2025 = pd.Timestamp("2025-12-31")
NIVEL_DE_SIGNIFICANCIA = 0.05
JANELA_TAXA_DE_CONFIRMACAO_SEMANAS = 8

# Mesmo algoritmo do bloco 7: HistGB, folha minima 20, quantil 0,85.
HISTGB_FOLHA_20 = EspecificacaoModelo(
    nome="histgb_folha20",
    classe=HistGradientBoostingRegressor,
    parametros={
        "max_iter": 250,
        "learning_rate": 0.05,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 20,
        "random_state": 42,
        "loss": "quantile",
        "quantile": 0.85,
    },
)

# O braco de referencia do bloco 7 (HistGB_folha20_M1) precisa reproduzir
# estes quatro MAE — TRAVA 1 do protocolo desta rodada.
MAE_ESPERADO_BLOCO_7 = {1: 133.6, 4: 199.6, 8: 223.2, 12: 243.8}
TOLERANCIA_DE_MAE_TRAVA_1 = 0.2

HORIZONTES_DA_RODADA = (1, 4, 8, 12)

# Nomes das colunas extras que a rodada acrescenta a tabela (alem das ja
# existentes em tabela_cevs.csv). Sao reservadas: nunca disputam vaga de
# clima ou de nucleo, so entram no modelo quando o braco pede em
# `colunas_extras` (ver harness.montar_features_do_braco).
COLUNAS_NOTIFICACOES_COM_LAGS = (
    "notificacoes",
    "notificacoes_lag1",
    "notificacoes_lag2",
    "notificacoes_lag3",
    "notificacoes_lag4",
)
COLUNA_TAXA_DE_CONFIRMACAO = "taxa_confirmacao_8sem"

# ⚠️ 'cevs_confirmados' e 'cevs_notificacoes' (as series BRUTAS do CEVS, ja
# presentes em tabela_cevs.csv) tambem entram aqui. Sem isso, elas cairiam no
# grupo nucleo pela selecao automatica (nao batem nenhum padrao de vetor nem
# de clima) e vazariam para TODOS os bracos, inclusive C0 e T0 — o que
# destruiria a comparacao da familia K1 (C2a/C2b so podem ter a notificacao
# como entrada extra se C0 nao tiver, senao os dois braços comparados ja
# comecam com a mesma informacao).
COLUNAS_RESERVADAS_DA_RODADA = COLUNAS_NOTIFICACOES_COM_LAGS + (
    COLUNA_TAXA_DE_CONFIRMACAO,
    "cevs_confirmados",
    "cevs_notificacoes",
)


def carregar_tabela_da_rodada() -> pd.DataFrame:
    """Le a tabela_cevs.csv montada por `montar_tabela_cevs.py`."""
    return pd.read_csv(CAMINHO_TABELA_DA_RODADA, parse_dates=["data"])


def calcular_taxa_de_confirmacao(
    confirmados: pd.Series,
    notificacoes: pd.Series,
    janela_semanas: int,
) -> pd.Series:
    """Confirmados dividido por notificacoes numa janela movel de semanas.

    Quando a soma de notificacoes da janela e zero, o resultado dessa semana
    fica sem informacao (NaN) e depois recebe a ultima taxa valida conhecida
    (`ffill`) — regra do protocolo (PRE_DECLARACAO.md, secao 3): "repete a
    ultima taxa valida", o que so usa o passado e nunca olha a frente.

    Args:
        confirmados: Serie semanal de casos confirmados do CEVS.
        notificacoes: Serie semanal de notificacoes do CEVS.
        janela_semanas: Tamanho da janela movel, em semanas, terminando na
            propria semana de origem (inclusive).

    Returns:
        A taxa de confirmacao por semana, com a regra de repeticao aplicada.
    """
    confirmados_na_janela = confirmados.rolling(janela_semanas, min_periods=1).sum()
    notificacoes_na_janela = notificacoes.rolling(janela_semanas, min_periods=1).sum()

    taxa_bruta = confirmados_na_janela / notificacoes_na_janela
    denominador_e_zero = notificacoes_na_janela == 0
    taxa_com_denominador_zero_vazio = taxa_bruta.where(~denominador_e_zero)
    taxa_com_repeticao_do_passado = taxa_com_denominador_zero_vazio.ffill()
    return taxa_com_repeticao_do_passado


def construir_colunas_extras_da_rodada(tabela: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as colunas de notificacoes (com lags) e a taxa de confirmacao.

    Roda para TODOS os bracos (via `construir_extras` do harness), depois da
    tabela ja ter passado por `construir_features_temporais`. As colunas
    novas usam sempre as series BRUTAS do CEVS (`cevs_confirmados` e
    `cevs_notificacoes`), nunca a coluna 'casos' do braco — para que o
    resultado nao dependa de qual alvo aquele braco escolheu.

    Args:
        tabela: A tabela do braco, ja com as features temporais do pipeline.

    Returns:
        Uma COPIA da tabela com as colunas extras da rodada.
    """
    tabela_com_extras = tabela.copy()

    tabela_com_extras["notificacoes"] = tabela_com_extras["cevs_notificacoes"]
    for numero_de_semanas in (1, 2, 3, 4):
        nome_da_coluna_lag = f"notificacoes_lag{numero_de_semanas}"
        tabela_com_extras[nome_da_coluna_lag] = tabela_com_extras[
            "cevs_notificacoes"
        ].shift(numero_de_semanas)

    tabela_com_extras[COLUNA_TAXA_DE_CONFIRMACAO] = calcular_taxa_de_confirmacao(
        tabela_com_extras["cevs_confirmados"],
        tabela_com_extras["cevs_notificacoes"],
        JANELA_TAXA_DE_CONFIRMACAO_SEMANAS,
    )
    return tabela_com_extras


def preparar_tabela_bruta_do_braco(tabela_da_rodada: pd.DataFrame, alvo: str) -> pd.DataFrame:
    """Devolve uma copia da tabela com 'casos' trocado pela serie do braco.

    Args:
        tabela_da_rodada: A tabela_cevs.csv, com 'casos' (oficial),
            'cevs_confirmados' e 'cevs_notificacoes'.
        alvo: Qual coluna vira o novo 'casos' deste braco: 'casos' (mantem o
            oficial, braco T0), 'cevs_confirmados' (C0, C2a, C2b) ou
            'cevs_notificacoes' (N1).

    Returns:
        Uma COPIA da tabela, pronta para `harness.montar_features_do_braco`.
    """
    tabela_do_braco = tabela_da_rodada.copy()
    tabela_do_braco["casos"] = tabela_da_rodada[alvo]
    return tabela_do_braco


def rodar_braco(
    tabela_da_rodada: pd.DataFrame,
    nome_do_braco: str,
    alvo: str,
    colunas_extras: tuple[str, ...],
    descricao: str,
) -> tuple[pd.DataFrame, list[str]]:
    """Monta as features e roda o walk-forward de um braco em todos os horizontes.

    Returns:
        As previsoes do braco (uma linha por semana avaliada e horizonte) e
        a lista do clima escolhido (para a TRAVA 3, clima identico entre
        bracos).
    """
    tabela_bruta_do_braco = preparar_tabela_bruta_do_braco(tabela_da_rodada, alvo)

    braco_do_harness = harness.Braco(
        nome_do_braco,
        modelo=HISTGB_FOLHA_20,
        colunas_extras=colunas_extras,
        descricao=descricao,
    )

    tabela_com_features, colunas_do_modelo, clima_escolhido = (
        harness.montar_features_do_braco(
            tabela_bruta_do_braco,
            braco_do_harness,
            construir_extras=construir_colunas_extras_da_rodada,
            colunas_reservadas=COLUNAS_RESERVADAS_DA_RODADA,
        )
    )

    previsoes_do_braco = []
    for horizonte in HORIZONTES_DA_RODADA:
        marca = time.perf_counter()
        previsoes_do_horizonte = harness.rodar_walk_forward(
            tabela_com_features, colunas_do_modelo, horizonte, HISTGB_FOLHA_20
        )
        previsoes_do_horizonte["braco"] = nome_do_braco
        previsoes_do_braco.append(previsoes_do_horizonte)
        print(
            f"  [{nome_do_braco}] h={horizonte:2d}  "
            f"{len(previsoes_do_horizonte):3d} sem  "
            f"{time.perf_counter() - marca:5.1f}s",
            flush=True,
        )

    print(
        f"[{nome_do_braco}] {descricao} — {len(colunas_do_modelo)} features · "
        f"clima: {' | '.join(clima_escolhido)}",
        flush=True,
    )
    return pd.concat(previsoes_do_braco, ignore_index=True), clima_escolhido


def conferir_trava_1_reproduz_bloco_7(previsoes_t0: pd.DataFrame) -> bool:
    """TRAVA 1: o braco T0 tem de reproduzir o HistGB_folha20_M1 do bloco 7.

    Prova que o caminho do codigo (harness, features, walk-forward) esta
    correto antes de trocar a fonte dos casos pelo CEVS.
    """
    avaliacao = previsoes_t0[previsoes_t0["data_alvo"] >= INICIO_DA_AVALIACAO]
    fim_avaliacao_bloco_7 = pd.Timestamp("2026-02-28")
    avaliacao = avaliacao[avaliacao["data_alvo"] <= fim_avaliacao_bloco_7]

    print("\n  TRAVA 1 — T0 contra o bloco 7 (HistGB_folha20_M1)")
    tudo_bate = True
    for horizonte, mae_esperado in MAE_ESPERADO_BLOCO_7.items():
        do_horizonte = avaliacao[avaliacao["h"] == horizonte]
        mae_obtido = mean_absolute_error(do_horizonte["real"], do_horizonte["previsto"])
        bate = abs(mae_obtido - mae_esperado) < TOLERANCIA_DE_MAE_TRAVA_1
        tudo_bate = tudo_bate and bate
        marca = "ok" if bate else "<<< DIVERGE"
        print(
            f"    h={horizonte:2d}  esperado {mae_esperado:6.1f}  "
            f"obtido {mae_obtido:6.1f}  {marca}"
        )
    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}")
    return tudo_bate


def conferir_trava_3_clima_identico(clima_por_braco: dict[str, list[str]]) -> bool:
    """TRAVA 3: o clima escolhido tem de ser o mesmo em todos os bracos."""
    print("\n  TRAVA 3 — clima identico entre bracos")
    referencia = clima_por_braco["T0"]
    tudo_igual = True
    for nome_do_braco, clima in clima_por_braco.items():
        igual = clima == referencia
        tudo_igual = tudo_igual and igual
        marca = "ok" if igual else "<<< DIVERGE"
        print(f"    {nome_do_braco:>4}: {' | '.join(clima)}  {marca}")
    print(f"    veredito: {'VALIDO' if tudo_igual else 'INVALIDO'}")
    return tudo_igual


def calcular_regua_sazonal(previsoes: pd.DataFrame, alvo_valores: pd.Series, tabela: pd.DataFrame) -> pd.DataFrame:
    """A regua de cada alvo: o valor real da mesma semana do ano passado.

    Args:
        previsoes: As previsoes de um braco (colunas 'data_alvo', 'h').
        alvo_valores: A serie completa (indexada por data) do alvo desse
            braco, usada para buscar o valor de 52 semanas antes.
        tabela: A tabela com a coluna 'data', para mapear data_alvo -> valor.

    Returns:
        As previsoes com uma coluna nova, 'regua', com o real de 52 semanas
        antes da data_alvo (NaN se essa semana nao existir na tabela).
    """
    valor_por_data = pd.Series(alvo_valores.to_numpy(), index=tabela["data"].to_numpy())

    datas_da_regua = previsoes["data_alvo"] - pd.Timedelta(weeks=52)
    regua = datas_da_regua.map(valor_por_data)
    previsoes_com_regua = previsoes.copy()
    previsoes_com_regua["regua"] = regua.to_numpy()
    return previsoes_com_regua


RECORTES_DA_AVALIACAO = {
    "2024_2025": (pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31")),
    "2026": (pd.Timestamp("2026-01-01"), None),
    "tudo": (pd.Timestamp("2024-01-01"), None),
}

HORIZONTES_FAMILIA_K1 = (1, 4, 8, 12)
HORIZONTES_FAMILIA_K2 = (4, 8, 12)


def filtrar_por_recorte(
    previsoes: pd.DataFrame, inicio: pd.Timestamp, fim: pd.Timestamp | None
) -> pd.DataFrame:
    """Filtra previsoes por data_alvo dentro de um recorte de avaliacao."""
    dentro_do_recorte = previsoes["data_alvo"] >= inicio
    if fim is not None:
        dentro_do_recorte = dentro_do_recorte & (previsoes["data_alvo"] <= fim)
    return previsoes[dentro_do_recorte]


def calcular_metricas_descritivas_por_alvo(previsoes: pd.DataFrame) -> pd.DataFrame:
    """MAE, skill score contra a regua e leitura de pico/erro relativo em 2026.

    Uma linha por (braco, h, recorte). O skill score e 1 - MAE_modelo /
    MAE_regua, restrito as semanas em que a regua existe (a primeira
    temporada de cada alvo nao tem regua, por nao haver ano anterior na
    serie do CEVS). O erro relativo ao total e a "maior previsao x maior
    real" so sao calculados no recorte 2026 (secao 5 do protocolo); nos
    outros recortes ficam vazios (NaN), nao zero.
    """
    linhas_da_tabela = []
    for nome_do_braco in previsoes["braco"].unique():
        do_braco = previsoes[previsoes["braco"] == nome_do_braco]
        for horizonte in HORIZONTES_DA_RODADA:
            do_horizonte = do_braco[do_braco["h"] == horizonte]
            for nome_do_recorte, (inicio, fim) in RECORTES_DA_AVALIACAO.items():
                do_recorte = filtrar_por_recorte(do_horizonte, inicio, fim)
                if do_recorte.empty:
                    continue

                mae = mean_absolute_error(do_recorte["real"], do_recorte["previsto"])

                com_regua = do_recorte.dropna(subset=["regua"])
                skill_score = np.nan
                if not com_regua.empty:
                    mae_regua = mean_absolute_error(com_regua["real"], com_regua["regua"])
                    mae_modelo_no_mesmo_conjunto = mean_absolute_error(
                        com_regua["real"], com_regua["previsto"]
                    )
                    if mae_regua > 0:
                        skill_score = 1.0 - (mae_modelo_no_mesmo_conjunto / mae_regua)

                erro_relativo_ao_total = np.nan
                erro_relativo_da_regua = np.nan
                maior_previsto = np.nan
                maior_real = np.nan
                if nome_do_recorte == "2026":
                    soma_real = do_recorte["real"].sum()
                    if soma_real > 0:
                        erro_relativo_ao_total = (
                            (do_recorte["real"] - do_recorte["previsto"]).abs().sum()
                            / soma_real
                        )
                        if not com_regua.empty:
                            soma_real_com_regua = com_regua["real"].sum()
                            erro_relativo_da_regua = (
                                (com_regua["real"] - com_regua["regua"]).abs().sum()
                                / soma_real_com_regua
                            )
                    maior_previsto = do_recorte["previsto"].max()
                    maior_real = do_recorte["real"].max()

                linhas_da_tabela.append(
                    {
                        "braco": nome_do_braco,
                        "h": horizonte,
                        "recorte": nome_do_recorte,
                        "n": len(do_recorte),
                        "mae": mae,
                        "skill_score_vs_regua": skill_score,
                        "erro_relativo_ao_total_2026": erro_relativo_ao_total,
                        "erro_relativo_da_regua_2026": erro_relativo_da_regua,
                        "maior_previsto_2026": maior_previsto,
                        "maior_real_2026": maior_real,
                    }
                )
    return pd.DataFrame(linhas_da_tabela)


def calcular_familia_k1_notificacoes_ajudam_confirmados(
    previsoes: pd.DataFrame,
) -> pd.DataFrame:
    """K1: C2a e C2b contra C0, em h=1,4,8,12, recorte 'tudo'. Holm sobre 8."""
    inicio, fim = RECORTES_DA_AVALIACAO["tudo"]
    avaliacao_tudo = filtrar_por_recorte(previsoes, inicio, fim)

    comparacoes = []
    for braco_variante in ("C2a", "C2b"):
        for horizonte in HORIZONTES_FAMILIA_K1:
            comparacoes.append(
                harness.comparar_pareado(avaliacao_tudo, "C0", braco_variante, horizonte)
            )

    p_corrigidos = harness.corrigir_por_holm(comparacoes)

    linhas_da_tabela = []
    for comparacao in comparacoes:
        p_holm = p_corrigidos[f"{comparacao.braco}:{comparacao.horizonte}"]
        linhas_da_tabela.append(
            {
                "braco": comparacao.braco,
                "h": comparacao.horizonte,
                "mae_c0": comparacao.mae_referencia,
                "mae_variante": comparacao.mae_variante,
                "reducao_percentual": comparacao.reducao_percentual(),
                "p_bruto": comparacao.p_bruto,
                "p_holm": p_holm,
                "semanas_pareadas": comparacao.semanas_pareadas,
            }
        )
    return pd.DataFrame(linhas_da_tabela)


def calcular_familia_k2_modelo_bate_regua(previsoes: pd.DataFrame) -> pd.DataFrame:
    """K2: C0 e N1 contra a regua do proprio alvo, h=4,8,12. Holm sobre 6."""
    inicio, fim = RECORTES_DA_AVALIACAO["tudo"]
    avaliacao_tudo = filtrar_por_recorte(previsoes, inicio, fim)

    comparacoes = []
    for nome_do_braco in ("C0", "N1"):
        do_braco = avaliacao_tudo[avaliacao_tudo["braco"] == nome_do_braco]
        for horizonte in HORIZONTES_FAMILIA_K2:
            do_horizonte = do_braco[do_braco["h"] == horizonte].dropna(subset=["regua"])
            if do_horizonte.empty:
                raise ValueError(
                    f"Sem semanas com regua para {nome_do_braco} em h={horizonte}."
                )

            erro_do_modelo = (do_horizonte["real"] - do_horizonte["previsto"]).abs()
            erro_da_regua = (do_horizonte["real"] - do_horizonte["regua"]).abs()

            if np.allclose(erro_do_modelo, erro_da_regua):
                p_bruto = 1.0
            else:
                _, p_bruto = stats.wilcoxon(erro_do_modelo, erro_da_regua)

            comparacoes.append(
                harness.ComparacaoPareada(
                    braco=nome_do_braco,
                    horizonte=horizonte,
                    mae_referencia=mean_absolute_error(
                        do_horizonte["real"], do_horizonte["regua"]
                    ),
                    mae_variante=mean_absolute_error(
                        do_horizonte["real"], do_horizonte["previsto"]
                    ),
                    r2_referencia=np.nan,
                    r2_variante=np.nan,
                    semanas_pareadas=len(do_horizonte),
                    p_bruto=float(p_bruto),
                )
            )

    p_corrigidos = harness.corrigir_por_holm(comparacoes)

    linhas_da_tabela = []
    for comparacao in comparacoes:
        p_holm = p_corrigidos[f"{comparacao.braco}:{comparacao.horizonte}"]
        linhas_da_tabela.append(
            {
                "braco": comparacao.braco,
                "h": comparacao.horizonte,
                "mae_regua": comparacao.mae_referencia,
                "mae_modelo": comparacao.mae_variante,
                "reducao_percentual_vs_regua": comparacao.reducao_percentual(),
                "p_bruto": comparacao.p_bruto,
                "p_holm": p_holm,
                "semanas_pareadas": comparacao.semanas_pareadas,
            }
        )
    return pd.DataFrame(linhas_da_tabela)


def gerar_figura_2026(previsoes: pd.DataFrame) -> None:
    """Real x previsto em 2026 para N1 e C0, h=4 e h=12, com a regua."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    inicio, fim = RECORTES_DA_AVALIACAO["2026"]
    figura, eixos = plt.subplots(2, 2, figsize=(13, 8), sharex=False)

    combinacoes = (("C0", 4), ("N1", 4), ("C0", 12), ("N1", 12))
    for indice, (nome_do_braco, horizonte) in enumerate(combinacoes):
        eixo = eixos.flat[indice]
        do_braco = previsoes[
            (previsoes["braco"] == nome_do_braco) & (previsoes["h"] == horizonte)
        ]
        do_recorte = filtrar_por_recorte(do_braco, inicio, fim).sort_values("data_alvo")

        eixo.plot(do_recorte["data_alvo"], do_recorte["real"], "o-", label="real", color="#1f4e79")
        eixo.plot(
            do_recorte["data_alvo"], do_recorte["previsto"], "o-", label="previsto", color="#c0392b"
        )
        eixo.plot(
            do_recorte["data_alvo"],
            do_recorte["regua"],
            "--",
            label="regua (ano passado)",
            color="#7f8c8d",
        )
        eixo.set_title(f"{nome_do_braco} — h={horizonte}")
        eixo.tick_params(axis="x", rotation=45)
        eixo.legend(fontsize=8)

    figura.suptitle("2026: real x previsto x regua sazonal (C0 = confirmados · N1 = notificacoes)")
    figura.tight_layout()
    figura.savefig(PASTA_DE_SAIDAS / "figura_2026.png", dpi=130)
    plt.close(figura)


def imprimir_criterios_da_secao_6(
    familia_k1: pd.DataFrame, metricas: pd.DataFrame
) -> None:
    """Aplica os dois criterios pre-declarados na secao 6 e registra o veredito."""
    print("\n  CRITERIOS DA SECAO 6")

    k1_em_h12 = familia_k1[familia_k1["h"] == 12]
    notificacoes_ajudam_confirmados = False
    for _, linha in k1_em_h12.iterrows():
        passou = linha["mae_variante"] < linha["mae_c0"] and linha["p_holm"] < NIVEL_DE_SIGNIFICANCIA
        notificacoes_ajudam_confirmados = notificacoes_ajudam_confirmados or passou
        print(
            f"    K1 h=12 {linha['braco']}: MAE {linha['mae_variante']:.1f} contra "
            f"C0 {linha['mae_c0']:.1f}, p Holm {linha['p_holm']:.4f} "
            f"{'PASSOU' if passou else 'nao passou'}"
        )
    print(
        "    => 'as notificacoes ajudam os confirmados': "
        f"{'SIM' if notificacoes_ajudam_confirmados else 'NAO'}"
    )

    metricas_2026 = metricas[metricas["recorte"] == "2026"]
    linha_c0 = metricas_2026[metricas_2026["braco"] == "C0"]
    linha_n1 = metricas_2026[metricas_2026["braco"] == "N1"]
    if linha_c0.empty or linha_n1.empty:
        print("    => 'o modelo acompanha a transmissao': SEM DADOS SUFICIENTES EM 2026")
        return

    erro_n1 = linha_n1["erro_relativo_ao_total_2026"].mean()
    erro_c0 = linha_c0["erro_relativo_ao_total_2026"].mean()
    erro_regua_n1 = linha_n1["erro_relativo_da_regua_2026"].mean()
    acompanha_transmissao = erro_n1 < erro_c0 and erro_n1 < erro_regua_n1
    print(
        f"    N1 erro relativo 2026 {erro_n1:.3f} · C0 {erro_c0:.3f} · "
        f"regua de notificacoes {erro_regua_n1:.3f}"
    )
    print(
        "    => 'o modelo acompanha a transmissao' (descritivo, 1 temporada): "
        f"{'SIM' if acompanha_transmissao else 'NAO'}"
    )


def calcular_metricas_e_familias(previsoes: pd.DataFrame) -> None:
    """Gera metricas.csv, familia_k1.csv, familia_k2.csv e a figura de 2026."""
    metricas = calcular_metricas_descritivas_por_alvo(previsoes)
    metricas.to_csv(PASTA_DE_SAIDAS / "metricas.csv", index=False)

    familia_k1 = calcular_familia_k1_notificacoes_ajudam_confirmados(previsoes)
    familia_k1.to_csv(PASTA_DE_SAIDAS / "familia_k1.csv", index=False)
    print("\n  FAMILIA K1 — notificacoes ajudam os confirmados? (Holm sobre 8)")
    print(familia_k1.to_string(index=False))

    familia_k2 = calcular_familia_k2_modelo_bate_regua(previsoes)
    familia_k2.to_csv(PASTA_DE_SAIDAS / "familia_k2.csv", index=False)
    print("\n  FAMILIA K2 — modelo bate a regua do proprio alvo? (Holm sobre 6)")
    print(familia_k2.to_string(index=False))

    gerar_figura_2026(previsoes)

    imprimir_criterios_da_secao_6(familia_k1, metricas)


def main() -> None:
    print("=" * 78)
    print("NOTIFICACOES COMO ALVO — protocolo em PRE_DECLARACAO.md")
    print("=" * 78, flush=True)

    tabela_da_rodada = carregar_tabela_da_rodada()

    especificacao_dos_bracos = (
        ("T0", "casos", (), "confirmados da tabela oficial — trava"),
        ("C0", "cevs_confirmados", (), "confirmados do CEVS — base dos confirmados"),
        ("N1", "cevs_notificacoes", (), "notificacoes do CEVS"),
        (
            "C2a",
            "cevs_confirmados",
            COLUNAS_NOTIFICACOES_COM_LAGS,
            "confirmados do CEVS + notificacoes da origem e lags 1-4",
        ),
        (
            "C2b",
            "cevs_confirmados",
            (COLUNA_TAXA_DE_CONFIRMACAO,),
            "confirmados do CEVS + taxa de confirmacao de 8 semanas",
        ),
    )

    previsoes_de_todos_os_bracos = []
    clima_por_braco: dict[str, list[str]] = {}
    alvo_por_braco: dict[str, str] = {}

    for nome_do_braco, alvo, colunas_extras, descricao in especificacao_dos_bracos:
        inicio = time.perf_counter()
        previsoes_do_braco, clima_escolhido = rodar_braco(
            tabela_da_rodada, nome_do_braco, alvo, colunas_extras, descricao
        )
        previsoes_de_todos_os_bracos.append(previsoes_do_braco)
        clima_por_braco[nome_do_braco] = clima_escolhido
        alvo_por_braco[nome_do_braco] = alvo
        print(f"[{nome_do_braco}] {(time.perf_counter() - inicio) / 60:.1f} min\n", flush=True)

    todas_as_previsoes = pd.concat(previsoes_de_todos_os_bracos, ignore_index=True)

    # Regua de cada alvo: mesma semana do ano passado, na propria serie do
    # braco (T0 e C0/C2a/C2b usam confirmados; N1 usa notificacoes).
    previsoes_com_regua = []
    for nome_do_braco, alvo in alvo_por_braco.items():
        do_braco = todas_as_previsoes[todas_as_previsoes["braco"] == nome_do_braco]
        com_regua = calcular_regua_sazonal(
            do_braco, tabela_da_rodada[alvo], tabela_da_rodada
        )
        previsoes_com_regua.append(com_regua)
    todas_as_previsoes = pd.concat(previsoes_com_regua, ignore_index=True)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    todas_as_previsoes.to_csv(PASTA_DE_SAIDAS / "previsoes_por_braco.csv", index=False)

    valido_trava_1 = conferir_trava_1_reproduz_bloco_7(
        todas_as_previsoes[todas_as_previsoes["braco"] == "T0"]
    )
    valido_trava_3 = conferir_trava_3_clima_identico(clima_por_braco)

    if not valido_trava_1:
        print("\n  TRAVA 1 INVALIDA — parando antes de calcular metricas e Holm.", flush=True)
        return

    if not valido_trava_3:
        print(
            "\n  TRAVA 3 INVALIDA — clima difere entre bracos (investigado, nao forcado; "
            "ver decisoes no retorno). Prosseguindo com as metricas mesmo assim, "
            "porque o protocolo nao lista isso como bloqueante.",
            flush=True,
        )

    calcular_metricas_e_familias(todas_as_previsoes)
    print("\nFIM.", flush=True)


if __name__ == "__main__":
    main()
