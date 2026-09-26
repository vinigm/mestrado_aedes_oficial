"""Rodada B da segunda bateria noturna — varios quantis e o WIS.

Pre-declarado em analises/2026-09-25_segunda_bateria_noturna/PRE_DECLARACAO.md,
secao B, com as emendas de 25/09/2026 23h30 e 23h50 (limiares do plano
municipal e travas recalculadas na tabela atualizada).

O QUE ESTE SCRIPT FAZ

  1. Treina o cenario adotado (HistGB folha minima 5) e o HistGB folha minima
     20, nos dois casos COM vetor (M1), em 7 quantis (0,05 a 0,95) e 4
     horizontes (1, 4, 8 e 12 semanas), pelo mesmo walk-forward do harness da
     bateria de 23/09 — so trocando o parametro `quantile` do HistGB.
  2. Confere a TRAVA do cenario adotado contra os numeros da tabela nova
     (adendo de CERTIFICACAO.md) antes de olhar qualquer resultado novo.
  3. Ordena quantis cruzados (rearranjo isotonico) e conta quantas origens
     precisaram disso.
  4. Calcula o WIS (Bracher et al. 2021) e a cobertura dos intervalos de 50%
     e 90%, para os dois modelos e para a regua climatologica (quantis da
     mesma semana epidemiologica nos anos anteriores, desde 2018, minimo 3
     anos).
  5. Testa WIS do modelo contra WIS da regua em h=4 e h=12, nos dois modelos,
     Wilcoxon pareado, Holm sobre a familia de 4 — separadamente nos recortes
     2024-2025, 2026 e "tudo" (ver decisao registrada abaixo).

NAO ALTERA o harness nem qualquer outro arquivo do projeto: so le
`analises/2026-09-23_bateria_noturna/harness.py` e a tabela oficial.

DECISOES NAO COBERTAS PELA PRE-DECLARACAO, registradas aqui por serem
usadas no calculo (ver tambem o retorno da tarefa):

  - "HistGB folha 20" na secao B usa a variante COM vetor (M1) do bloco 7,
    a mesma que decidiu a rodada confirmatoria de 25/09 — nao a M0.
  - Recorte "tudo" = a uniao dos outros dois recortes (2024-01-01 a
    2026-04-19), e nao a serie inteira desde 2012: olhar 2018-2023 misturaria
    semanas de calibracao do grid de 30/08 com semanas de avaliacao, o que a
    regra do projeto (harness.INICIO_DA_AVALIACAO) sempre evitou.
  - Familia de Holm = 4 comparacoes (2 modelos x 2 horizontes) DENTRO de cada
    recorte, aplicada 3 vezes (uma por recorte) — nao uma familia global de
    12. Cada recorte e uma pergunta diferente (temporada atipica de 2026 x
    janela normal), en tao nao faz sentido diluir a correcao de uma no ruido
    da outra.
  - Quantis calculados por interpolacao linear (`numpy.quantile` padrao), na
    regua e no rearranjo isotonico dos quantis cruzados do modelo.
"""

import concurrent.futures
import dataclasses
import os
import pathlib
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DA_BATERIA_ANTERIOR = PASTA_DESTE_ARQUIVO.parent.parent / "2026-09-23_bateria_noturna"
PASTA_DO_PIPELINE = PASTA_DESTE_ARQUIVO.parent.parent.parent / "modelagem_aedes"

for pasta_a_incluir in (PASTA_DA_BATERIA_ANTERIOR, PASTA_DO_PIPELINE):
    if str(pasta_a_incluir) not in sys.path:
        sys.path.insert(0, str(pasta_a_incluir))

import harness  # noqa: E402  (bateria de 23/09/2026 — so lido, nunca alterado)
from config.modelo import EspecificacaoModelo  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

# --- Configuracao pre-declarada -------------------------------------------

QUANTIS_DECLARADOS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
HORIZONTES_DECLARADOS = (1, 4, 8, 12)
HORIZONTES_DE_TESTE = (4, 12)
MAX_PROCESSOS_PARALELOS = 8

# Emenda de 26/09/2026, 01h20: a lista de quantis da secao B nunca incluiu o
# 0,85, que e o quantil que a trava confere (`conferir_trava`, abaixo). Sem
# ele, o filtro `quantil == 0.85` sempre voltava vazio e a trava falhava por
# falta de dado, nao por divergencia real. O 0,85 e treinado SO para o
# cenario adotado (unico modelo que a trava olha) e SO para checar a trava —
# ele e descartado antes da etapa 3 (`ordenar_quantis_cruzados`) para que o
# WIS continue calculado com exatamente os 7 niveis declarados.
QUANTIL_DA_TRAVA = 0.85

INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")
FIM_RECORTE_2024_2025 = pd.Timestamp("2025-12-31")
INICIO_RECORTE_2026 = pd.Timestamp("2026-01-01")
FIM_RECORTE_2026 = pd.Timestamp("2026-04-19")

FIM_DA_TRAVA = pd.Timestamp("2026-02-01")
TRAVA_ESPERADA_MAE = {1: 97.4, 12: 280.0}
TOLERANCIA_DA_TRAVA = 0.2

ANO_MINIMO_CLIMATOLOGIA = 2018
MINIMO_ANOS_CLIMATOLOGIA = 3
NIVEL_DE_SIGNIFICANCIA = 0.05

NOME_DA_REGUA = "regua_climatologica"


@dataclasses.dataclass(frozen=True)
class FamiliaDeModelo:
    """Um dos dois algoritmos da rodada B, com os hiperparametros fixos.

    Attributes:
        nome: Identificador usado em todas as saidas.
        parametros_base: Hiperparametros do HistGB, sem o quantil — o quantil
            e inserido por `criar_especificacao_do_quantil`.
    """

    nome: str
    parametros_base: dict


FAMILIA_CENARIO_ADOTADO = FamiliaDeModelo(
    nome="cenario_adotado",
    parametros_base={
        "max_iter": 250,
        "learning_rate": 0.05,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 5,
        "random_state": 42,
        "loss": "quantile",
    },
)

FAMILIA_HISTGB_FOLHA20 = FamiliaDeModelo(
    nome="histgb_folha20",
    parametros_base={
        "max_iter": 250,
        "learning_rate": 0.05,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 20,
        "random_state": 42,
        "loss": "quantile",
    },
)

FAMILIAS_DE_MODELO = (FAMILIA_CENARIO_ADOTADO, FAMILIA_HISTGB_FOLHA20)


# --- Etapa 1: treino dos 7 quantis, nos 4 horizontes, nas 2 familias -------


def criar_especificacao_do_quantil(
    familia: FamiliaDeModelo,
    quantil: float,
) -> EspecificacaoModelo:
    """Monta a ficha do HistGB de uma familia, fixado num quantil.

    Args:
        familia: Qual das duas familias (cenario adotado ou folha 20).
        quantil: O nivel do quantil que a perda `loss="quantile"` mira.

    Returns:
        A ficha pronta para `especificacao.criar()`.
    """
    parametros_do_quantil = dict(familia.parametros_base)
    parametros_do_quantil["quantile"] = quantil

    return EspecificacaoModelo(
        nome=f"{familia.nome}_q{quantil}",
        classe=HistGradientBoostingRegressor,
        parametros=parametros_do_quantil,
    )


def rodar_uma_combinacao(
    nome_da_familia: str,
    parametros_base: dict,
    horizonte: int,
    quantil: float,
) -> pd.DataFrame:
    """Roda o walk-forward de uma combinacao (familia, horizonte, quantil).

    Cada chamada roda num processo separado (ver `main`). As features do
    braco de referencia (corte de maturidade, defasagens, vetor) NAO dependem
    do algoritmo nem do quantil — sao reconstruidas aqui (~1,2s) em vez de
    serializadas entre processos, o que e mais barato e mais simples.

    Args:
        nome_da_familia: "cenario_adotado" ou "histgb_folha20".
        parametros_base: Hiperparametros do HistGB da familia, sem o quantil.
        horizonte: Semanas a frente (1, 4, 8 ou 12).
        quantil: Nivel do quantil treinado (0,05 a 0,95).

    Returns:
        Uma linha por semana avaliada: h, data_alvo, real, previsto, modelo,
        quantil.
    """
    familia = FamiliaDeModelo(nome=nome_da_familia, parametros_base=parametros_base)
    especificacao = criar_especificacao_do_quantil(familia, quantil)

    tabela_bruta = harness.carregar_tabela_bruta()
    braco_de_referencia = harness.Braco("referencia")
    tabela, colunas_do_modelo, _ = harness.montar_features_do_braco(
        tabela_bruta, braco_de_referencia
    )

    previsoes = harness.rodar_walk_forward(
        tabela, colunas_do_modelo, horizonte, especificacao
    )
    previsoes["modelo"] = nome_da_familia
    previsoes["quantil"] = quantil
    return previsoes


def treinar_todas_as_combinacoes() -> pd.DataFrame:
    """Dispara os 60 treinos: 56 da secao B, mais 4 so para a trava.

    Os 56 sao 2 familias x 4 horizontes x 7 quantis declarados (WIS). Os 4
    extras sao o cenario adotado, nos 4 horizontes, no quantil 0,85 (emenda
    de 26/09/2026, 01h20) — usados so pela trava em `conferir_trava`, nunca
    pelo WIS.

    Ate `MAX_PROCESSOS_PARALELOS` processos em paralelo, cada um com 1
    thread (`OMP_NUM_THREADS=1`, ja fixado no topo do arquivo antes de
    importar numpy/sklearn).

    Returns:
        Todas as previsoes de todas as combinacoes (incluindo as 4 do
        quantil da trava), empilhadas.
    """
    combinacoes_pendentes = []
    for familia in FAMILIAS_DE_MODELO:
        for horizonte in HORIZONTES_DECLARADOS:
            for quantil in QUANTIS_DECLARADOS:
                combinacoes_pendentes.append((familia, horizonte, quantil))

    for horizonte in HORIZONTES_DECLARADOS:
        combinacoes_pendentes.append(
            (FAMILIA_CENARIO_ADOTADO, horizonte, QUANTIL_DA_TRAVA)
        )

    print(
        f"Disparando {len(combinacoes_pendentes)} combinacoes "
        f"(ate {MAX_PROCESSOS_PARALELOS} processos em paralelo)...",
        flush=True,
    )

    previsoes_de_todas = []
    inicio_geral = time.perf_counter()

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=MAX_PROCESSOS_PARALELOS
    ) as executor:
        tarefa_por_combinacao = {}
        for familia, horizonte, quantil in combinacoes_pendentes:
            tarefa = executor.submit(
                rodar_uma_combinacao,
                familia.nome,
                familia.parametros_base,
                horizonte,
                quantil,
            )
            tarefa_por_combinacao[tarefa] = (familia.nome, horizonte, quantil)

        concluidas = 0
        for tarefa in concurrent.futures.as_completed(tarefa_por_combinacao):
            nome_familia, horizonte, quantil = tarefa_por_combinacao[tarefa]
            previsoes = tarefa.result()
            previsoes_de_todas.append(previsoes)
            concluidas += 1
            print(
                f"  [{concluidas:2d}/{len(combinacoes_pendentes)}] "
                f"{nome_familia:>15}  h={horizonte:2d}  q={quantil:.2f}  "
                f"{len(previsoes):3d} semanas  "
                f"({time.perf_counter() - inicio_geral:6.1f}s desde o inicio)",
                flush=True,
            )

    print(
        f"Treino completo em {(time.perf_counter() - inicio_geral) / 60:.1f} min.",
        flush=True,
    )
    return pd.concat(previsoes_de_todas, ignore_index=True)


# --- Etapa 2: a trava contra a tabela atualizada ---------------------------


def conferir_trava(previsoes: pd.DataFrame) -> tuple[bool, pd.DataFrame]:
    """Confere o cenario adotado (q0,85) contra as ancoras da tabela nova.

    A janela e a mesma do adendo de CERTIFICACAO.md: `data_alvo` entre
    2024-01-01 e 2026-02-01, as MESMAS semanas usadas antes da atualizacao —
    isola o efeito da tabela nova do efeito de estender o recorte ate
    2026-04-19.

    Args:
        previsoes: Todas as previsoes treinadas (as 60 combinacoes, incluindo
            o quantil 0,85 usado so aqui).

    Returns:
        Se a trava bateu, e uma tabela com o MAE dos 4 horizontes na mesma
        janela (h=1 e h=12 sao a trava; h=4 e h=8 so sao registrados).
    """
    cenario_q85 = previsoes[
        (previsoes["modelo"] == "cenario_adotado") & (previsoes["quantil"] == 0.85)
    ]
    na_janela_da_trava = cenario_q85[
        (cenario_q85["data_alvo"] >= INICIO_DA_AVALIACAO)
        & (cenario_q85["data_alvo"] <= FIM_DA_TRAVA)
    ]

    print("\nTRAVA — cenario adotado (q0,85) contra a tabela atualizada")
    print(f"  janela: {INICIO_DA_AVALIACAO.date()} a {FIM_DA_TRAVA.date()}")

    linhas_do_registro = []
    trava_bateu = True
    for horizonte in HORIZONTES_DECLARADOS:
        do_horizonte = na_janela_da_trava[na_janela_da_trava["h"] == horizonte]
        erro_absoluto = np.abs(do_horizonte["real"] - do_horizonte["previsto"])
        mae_medido = float(erro_absoluto.mean())

        esperado = TRAVA_ESPERADA_MAE.get(horizonte)
        if esperado is None:
            marca = "(so registrado)"
        else:
            bate = abs(mae_medido - esperado) < TOLERANCIA_DA_TRAVA
            trava_bateu = trava_bateu and bate
            marca = "ok" if bate else "<<< DIVERGE"

        print(
            f"    h={horizonte:2d}  MAE {mae_medido:7.2f}  "
            f"(esperado {esperado if esperado is not None else '—'})  "
            f"n={len(do_horizonte):3d}  {marca}"
        )
        linhas_do_registro.append(
            {
                "h": horizonte,
                "mae_medido": mae_medido,
                "mae_esperado": esperado,
                "n_semanas": len(do_horizonte),
            }
        )

    print(f"  veredito: {'VALIDA' if trava_bateu else 'FALHOU'}")
    return trava_bateu, pd.DataFrame(linhas_do_registro)


def investigar_falha_da_trava(previsoes: pd.DataFrame) -> None:
    """Imprime diagnostico quando a trava falha, para investigar, nao forcar.

    Confere tambem contra a checagem embutida do proprio harness (que usa a
    janela desde 2024-01-01 sem teto e o painel de 23/09), para saber se o
    problema e a tabela nova, a janela cortada ou o arranjo deste script.
    """
    print("\n  INVESTIGACAO DA FALHA DA TRAVA")
    cenario_q85 = previsoes[
        (previsoes["modelo"] == "cenario_adotado") & (previsoes["quantil"] == 0.85)
    ].copy()
    cenario_q85["braco"] = "referencia"

    print("  Checagem embutida do harness (desde 2024-01-01, sem teto, painel de 23/09):")
    harness.conferir_trava_de_validacao(cenario_q85, "referencia")

    maior_data_alvo_por_horizonte = (
        cenario_q85.groupby("h")["data_alvo"].max().sort_index()
    )
    print("  Maior data_alvo alcancada, por horizonte:")
    print(maior_data_alvo_por_horizonte.to_string())


# --- Etapa 3: quantis cruzados, ordenados -----------------------------------


def ordenar_quantis_cruzados(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Rearranja os quantis de cada origem em ordem crescente e conta quantos cruzaram.

    Cada origem (mesmo modelo, horizonte e data_alvo) tem 7 previsoes
    independentes, uma por quantil treinado separadamente — nada garante que
    saiam em ordem crescente. O rearranjo isotonico (ordenar os 7 valores e
    devolve-los na ordem dos niveis) e o jeito padrao de consertar isso sem
    inventar um numero nao previsto pelo modelo.

    Args:
        previsoes: Uma linha por (modelo, h, data_alvo, quantil).

    Returns:
        A mesma tabela, com `previsto_bruto` (o valor original) preservado e
        `previsto` sobrescrito pelo valor rearranjado, mais a coluna booleana
        `cruzamento_corrigido`.
    """
    previsoes_ordenadas = previsoes.sort_values(
        ["modelo", "h", "data_alvo", "quantil"]
    ).reset_index(drop=True)
    previsoes_ordenadas["previsto_bruto"] = previsoes_ordenadas["previsto"]

    valores_finais = np.empty(len(previsoes_ordenadas), dtype=float)
    houve_cruzamento = np.zeros(len(previsoes_ordenadas), dtype=bool)

    origens = previsoes_ordenadas.groupby(
        ["modelo", "h", "data_alvo"], sort=False
    ).indices

    total_de_origens = 0
    origens_com_cruzamento = 0
    for posicoes_da_origem in origens.values():
        total_de_origens += 1
        posicoes_em_ordem = np.sort(np.asarray(posicoes_da_origem))
        valores_brutos = previsoes_ordenadas.loc[posicoes_em_ordem, "previsto_bruto"].to_numpy()

        ja_estava_em_ordem = bool(np.all(np.diff(valores_brutos) >= 0))
        valores_rearranjados = np.sort(valores_brutos)

        valores_finais[posicoes_em_ordem] = valores_rearranjados
        if not ja_estava_em_ordem:
            houve_cruzamento[posicoes_em_ordem] = True
            origens_com_cruzamento += 1

    previsoes_ordenadas["previsto"] = valores_finais
    previsoes_ordenadas["cruzamento_corrigido"] = houve_cruzamento

    percentual_com_cruzamento = 100.0 * origens_com_cruzamento / total_de_origens
    print(
        f"\nQuantis cruzados: {origens_com_cruzamento} de {total_de_origens} origens "
        f"({percentual_com_cruzamento:.1f}%) precisaram de rearranjo isotonico."
    )
    for chave_grupo, dados_do_grupo in previsoes_ordenadas.groupby(["modelo", "h"]):
        origens_do_grupo = dados_do_grupo.groupby("data_alvo")["cruzamento_corrigido"].any()
        print(
            f"    {chave_grupo[0]:>15}  h={chave_grupo[1]:2d}  "
            f"{int(origens_do_grupo.sum()):3d}/{len(origens_do_grupo):3d} origens com cruzamento"
        )

    return previsoes_ordenadas


# --- Etapa 4: a regua climatologica ----------------------------------------


def montar_historico_por_semana_epidemiologica(tabela_bruta: pd.DataFrame) -> pd.DataFrame:
    """Recorta so as colunas que a regua climatologica precisa.

    Args:
        tabela_bruta: A tabela semanal completa, sem corte de maturidade —
            a regua usa os casos ja maturados de anos passados, entao o
            corte do walk-forward (que so protege o TREINO do modelo) nao
            se aplica aqui.

    Returns:
        Uma linha por semana, com ano, semana epidemiologica e casos.
    """
    return tabela_bruta[["data", "ano", "semana", "casos"]].copy()


def calcular_previsao_da_regua(
    historico: pd.DataFrame,
    data_alvo: pd.Timestamp,
) -> dict[float, float] | None:
    """Os 7 quantis da regua climatologica para a semana de `data_alvo`.

    Usa os casos da MESMA semana epidemiologica em anos anteriores, a partir
    de 2018, exigindo pelo menos 3 anos com dado. "Anterior" e em relacao ao
    ano de `data_alvo` — anos iguais ou posteriores nunca entram, mesmo que a
    tabela ja os contenha, porque a regua tem que ser uma previsao de
    verdade, feita so com o passado.

    Args:
        historico: Saida de `montar_historico_por_semana_epidemiologica`.
        data_alvo: A data da semana que esta sendo avaliada.

    Returns:
        Um dicionario quantil -> valor previsto, ou None se houver menos de
        `MINIMO_ANOS_CLIMATOLOGIA` anos com dado para aquela semana.
    """
    linha_da_data_alvo = historico[historico["data"] == data_alvo]
    if linha_da_data_alvo.empty:
        return None

    semana_epidemiologica = int(linha_da_data_alvo["semana"].to_numpy()[0])
    ano_da_data_alvo = int(linha_da_data_alvo["ano"].to_numpy()[0])

    candidatos = historico[
        (historico["semana"] == semana_epidemiologica)
        & (historico["ano"] >= ANO_MINIMO_CLIMATOLOGIA)
        & (historico["ano"] < ano_da_data_alvo)
    ]
    casos_dos_anos_anteriores = candidatos["casos"].dropna()

    if len(casos_dos_anos_anteriores) == 0:
        return None
    anos_com_dado = candidatos.loc[casos_dos_anos_anteriores.index, "ano"].nunique()
    if anos_com_dado < MINIMO_ANOS_CLIMATOLOGIA:
        return None

    valores_dos_quantis = np.quantile(
        casos_dos_anos_anteriores.to_numpy(), QUANTIS_DECLARADOS
    )
    return dict(zip(QUANTIS_DECLARADOS, valores_dos_quantis))


def montar_previsoes_da_regua(
    tabela_bruta: pd.DataFrame,
    datas_alvo_a_cobrir: pd.Series,
) -> pd.DataFrame:
    """Roda a regua climatologica para cada data_alvo que os modelos previram.

    Args:
        tabela_bruta: A tabela semanal completa (ver
            `montar_historico_por_semana_epidemiologica`).
        datas_alvo_a_cobrir: As datas_alvo distintas presentes nas previsoes
            dos modelos.

    Returns:
        Uma linha por (data_alvo, quantil), so para as datas com pelo menos
        `MINIMO_ANOS_CLIMATOLOGIA` anos de historico.
    """
    historico = montar_historico_por_semana_epidemiologica(tabela_bruta)

    linhas_da_regua = []
    datas_sem_historico_suficiente = 0
    for data_alvo in sorted(datas_alvo_a_cobrir.unique()):
        quantis_previstos = calcular_previsao_da_regua(historico, pd.Timestamp(data_alvo))
        if quantis_previstos is None:
            datas_sem_historico_suficiente += 1
            continue

        for quantil, valor_previsto in quantis_previstos.items():
            linhas_da_regua.append(
                {
                    "data_alvo": pd.Timestamp(data_alvo),
                    "quantil": quantil,
                    "previsto": valor_previsto,
                }
            )

    print(
        f"\nRegua climatologica: {len(datas_alvo_a_cobrir.unique()) - datas_sem_historico_suficiente} "
        f"de {len(datas_alvo_a_cobrir.unique())} datas-alvo com historico suficiente "
        f"(>= {MINIMO_ANOS_CLIMATOLOGIA} anos desde {ANO_MINIMO_CLIMATOLOGIA})."
    )
    return pd.DataFrame(linhas_da_regua)


# --- Etapa 5: WIS e cobertura -----------------------------------------------


def calcular_intervalo_score(
    real: float,
    limite_inferior: float,
    limite_superior: float,
    alpha: float,
) -> float:
    """O IS_alpha de um unico intervalo, na formula de Bracher et al. 2021.

    IS_alpha = (u - l) + (2/alpha)(l - y) * 1[y < l] + (2/alpha)(y - u) * 1[y > u]

    Args:
        real: O valor observado.
        limite_inferior: O quantil inferior do intervalo (ex.: q0,25 no 50%).
        limite_superior: O quantil superior do intervalo (ex.: q0,75 no 50%).
        alpha: 1 menos a cobertura nominal do intervalo (0,5 no intervalo de
            50%, 0,1 no de 90%).

    Returns:
        O escore do intervalo — largura mais penalidade se `real` ficar fora.
    """
    largura_do_intervalo = limite_superior - limite_inferior

    penalidade_por_baixo = 0.0
    if real < limite_inferior:
        penalidade_por_baixo = (2.0 / alpha) * (limite_inferior - real)

    penalidade_por_cima = 0.0
    if real > limite_superior:
        penalidade_por_cima = (2.0 / alpha) * (real - limite_superior)

    return largura_do_intervalo + penalidade_por_baixo + penalidade_por_cima


# Os tres intervalos declarados na secao B, com o alpha de cada um (1 menos a
# cobertura nominal).
INTERVALOS_DO_WIS = (
    {"cobertura": 0.50, "alpha": 0.50, "quantil_inferior": 0.25, "quantil_superior": 0.75},
    {"cobertura": 0.80, "alpha": 0.20, "quantil_inferior": 0.10, "quantil_superior": 0.90},
    {"cobertura": 0.90, "alpha": 0.10, "quantil_inferior": 0.05, "quantil_superior": 0.95},
)


def calcular_wis(real: float, previsto_por_quantil: dict[float, float]) -> float:
    """O Weighted Interval Score de uma origem, com a mediana e 3 intervalos.

    WIS = [ (1/2)|y - mediana| + soma_k (alpha_k/2) IS_alpha_k ] / (K + 1/2)

    Args:
        real: O valor observado.
        previsto_por_quantil: Os 7 quantis previstos para esta origem — tem
            que conter, no minimo, a mediana e os 6 quantis dos 3 intervalos.

    Returns:
        O WIS da origem (quanto menor, melhor).
    """
    mediana_prevista = previsto_por_quantil[0.50]
    termo_da_mediana = 0.5 * abs(real - mediana_prevista)

    soma_dos_intervalos = 0.0
    for intervalo in INTERVALOS_DO_WIS:
        limite_inferior = previsto_por_quantil[intervalo["quantil_inferior"]]
        limite_superior = previsto_por_quantil[intervalo["quantil_superior"]]
        escore_do_intervalo = calcular_intervalo_score(
            real, limite_inferior, limite_superior, intervalo["alpha"]
        )
        soma_dos_intervalos += (intervalo["alpha"] / 2.0) * escore_do_intervalo

    quantidade_de_intervalos = len(INTERVALOS_DO_WIS)
    return (termo_da_mediana + soma_dos_intervalos) / (quantidade_de_intervalos + 0.5)


def calcular_cobertura(
    real: float,
    previsto_por_quantil: dict[float, float],
    quantil_inferior: float,
    quantil_superior: float,
) -> bool:
    """Se `real` caiu dentro do intervalo [quantil_inferior, quantil_superior]."""
    limite_inferior = previsto_por_quantil[quantil_inferior]
    limite_superior = previsto_por_quantil[quantil_superior]
    return bool(limite_inferior <= real <= limite_superior)


def montar_tabela_de_origens(
    previsoes_em_colunas: pd.DataFrame,
) -> pd.DataFrame:
    """Pivota quantil->coluna e calcula WIS e cobertura, uma linha por origem.

    Args:
        previsoes_em_colunas: Colunas modelo, h, data_alvo, real, quantil,
            previsto — uma linha por quantil.

    Returns:
        Uma linha por (modelo, h, data_alvo), com wis, cobertura_50 e
        cobertura_90.
    """
    linhas_de_origem = []

    agrupado = previsoes_em_colunas.groupby(["modelo", "h", "data_alvo"], sort=False)
    for (modelo, horizonte, data_alvo), dados_da_origem in agrupado:
        previsto_por_quantil = dict(
            zip(dados_da_origem["quantil"], dados_da_origem["previsto"])
        )
        if len(previsto_por_quantil) != len(QUANTIS_DECLARADOS):
            continue

        real = float(dados_da_origem["real"].to_numpy()[0])

        wis_da_origem = calcular_wis(real, previsto_por_quantil)
        cobertura_50 = calcular_cobertura(real, previsto_por_quantil, 0.25, 0.75)
        cobertura_90 = calcular_cobertura(real, previsto_por_quantil, 0.05, 0.95)

        linhas_de_origem.append(
            {
                "modelo": modelo,
                "h": horizonte,
                "data_alvo": data_alvo,
                "real": real,
                "wis": wis_da_origem,
                "cobertura_50": cobertura_50,
                "cobertura_90": cobertura_90,
            }
        )

    return pd.DataFrame(linhas_de_origem)


def marcar_recorte(data_alvo: pd.Series) -> pd.Series:
    """Classifica cada data_alvo em '2024-2025', '2026' ou fora dos recortes.

    Args:
        data_alvo: A serie de datas-alvo a classificar.

    Returns:
        Uma serie categorica com "2024-2025", "2026" ou None.
    """
    dentro_de_2024_2025 = (data_alvo >= INICIO_DA_AVALIACAO) & (
        data_alvo <= FIM_RECORTE_2024_2025
    )
    dentro_de_2026 = (data_alvo >= INICIO_RECORTE_2026) & (data_alvo <= FIM_RECORTE_2026)

    condicoes = [dentro_de_2024_2025, dentro_de_2026]
    resultados = ["2024-2025", "2026"]
    return pd.Series(
        np.select(condicoes, resultados, default=None), index=data_alvo.index
    )


def montar_wis_e_cobertura(origens: pd.DataFrame) -> pd.DataFrame:
    """Agrega WIS medio e cobertura por modelo, horizonte e recorte.

    Args:
        origens: Saida de `montar_tabela_de_origens`, com a coluna `recorte`
            ja preenchida (ver `marcar_recorte`) e um recorte extra "tudo".

    Returns:
        Uma linha por (modelo, h, recorte).
    """
    linhas_do_resumo = []
    for (modelo, horizonte, recorte), dados_do_grupo in origens.groupby(
        ["modelo", "h", "recorte"], sort=False
    ):
        linhas_do_resumo.append(
            {
                "modelo": modelo,
                "h": horizonte,
                "recorte": recorte,
                "wis_medio": float(dados_do_grupo["wis"].mean()),
                "cobertura_50": float(dados_do_grupo["cobertura_50"].mean()),
                "cobertura_90": float(dados_do_grupo["cobertura_90"].mean()),
                "n": len(dados_do_grupo),
            }
        )
    return pd.DataFrame(linhas_do_resumo)


# --- Etapa 6: o teste pareado, WIS modelo x WIS regua -----------------------


def comparar_wis_pareado(
    origens_do_modelo: pd.DataFrame,
    origens_da_regua: pd.DataFrame,
    modelo: str,
    horizonte: int,
    recorte: str,
) -> dict:
    """Wilcoxon pareado entre o WIS do modelo e o WIS da regua, por data_alvo.

    Args:
        origens_do_modelo: Todas as origens de todos os modelos.
        origens_da_regua: Todas as origens da regua (um wis por data_alvo,
            sem depender de h).
        modelo: Qual modelo comparar.
        horizonte: 4 ou 12.
        recorte: "2024-2025", "2026" ou "tudo".

    Returns:
        Um dicionario com os campos da linha de `familia_b.csv`.

    Raises:
        ValueError: Se nao sobrar nenhuma data_alvo em comum entre modelo e
            regua no recorte.
    """
    do_modelo = origens_do_modelo[
        (origens_do_modelo["modelo"] == modelo)
        & (origens_do_modelo["h"] == horizonte)
        & (origens_do_modelo["recorte"] == recorte)
    ]
    da_regua = origens_da_regua[origens_da_regua["recorte"] == recorte]

    pareado = do_modelo.merge(
        da_regua, on="data_alvo", suffixes=("_modelo", "_regua")
    )
    if pareado.empty:
        raise ValueError(
            f"Nenhuma data_alvo em comum entre {modelo} e a regua "
            f"em h={horizonte}, recorte {recorte}."
        )

    wis_do_modelo = pareado["wis_modelo"].to_numpy()
    wis_da_regua = pareado["wis_regua"].to_numpy()

    if np.allclose(wis_do_modelo, wis_da_regua):
        estatistica, p_bruto = np.nan, 1.0
    else:
        estatistica, p_bruto = stats.wilcoxon(wis_do_modelo, wis_da_regua)

    return {
        "recorte": recorte,
        "modelo": modelo,
        "h": horizonte,
        "n_pares": len(pareado),
        "wis_medio_modelo": float(np.mean(wis_do_modelo)),
        "wis_medio_regua": float(np.mean(wis_da_regua)),
        "diferenca_media": float(np.mean(wis_do_modelo - wis_da_regua)),
        "estatistica_wilcoxon": float(estatistica) if estatistica == estatistica else None,
        "p_bruto": float(p_bruto),
    }


def aplicar_holm_por_recorte(comparacoes: pd.DataFrame) -> pd.DataFrame:
    """Corrige por Holm dentro de cada recorte (familia de 4: 2 modelos x 2 h).

    Ver a decisao registrada no topo do arquivo sobre por que a familia e por
    recorte, e nao global.

    Args:
        comparacoes: Uma linha por (recorte, modelo, h), com `p_bruto`.

    Returns:
        A mesma tabela, com a coluna `p_holm` e `significativo` adicionadas.
    """
    comparacoes_com_holm = comparacoes.copy()
    comparacoes_com_holm["p_holm"] = np.nan

    for recorte, indices_do_recorte in comparacoes_com_holm.groupby("recorte").groups.items():
        bloco_do_recorte = comparacoes_com_holm.loc[indices_do_recorte].sort_values("p_bruto")
        quantidade_no_bloco = len(bloco_do_recorte)

        maior_p_ate_agora = 0.0
        for posicao, (indice_da_linha, linha) in enumerate(bloco_do_recorte.iterrows()):
            p_ajustado = min(1.0, linha["p_bruto"] * (quantidade_no_bloco - posicao))
            maior_p_ate_agora = max(maior_p_ate_agora, p_ajustado)
            comparacoes_com_holm.loc[indice_da_linha, "p_holm"] = maior_p_ate_agora

    comparacoes_com_holm["significativo"] = (
        comparacoes_com_holm["p_holm"] < NIVEL_DE_SIGNIFICANCIA
    )
    return comparacoes_com_holm


# --- Etapa 7: a figura -------------------------------------------------------


def desenhar_figura_de_intervalos(
    previsoes_finais: pd.DataFrame,
    previsoes_da_regua: pd.DataFrame,
    tabela_bruta: pd.DataFrame,
    caminho_da_figura: pathlib.Path,
) -> None:
    """Grafico de intervalos em 2026: cenario adotado, folha 20 e a regua.

    Um painel por horizonte de decisao (4 e 12 semanas), com a mediana e a
    banda de 90% do cenario adotado e da regua climatologica, a mediana do
    HistGB folha 20 e os casos observados.

    Args:
        previsoes_finais: As previsoes dos modelos, ja com quantis
            rearranjados (`ordenar_quantis_cruzados`).
        previsoes_da_regua: As previsoes da regua (uma linha por
            data_alvo/quantil).
        tabela_bruta: A tabela semanal completa, para o eixo dos casos
            observados.
        caminho_da_figura: Onde salvar o PNG.
    """
    figura, eixos = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

    for eixo, horizonte in zip(eixos, HORIZONTES_DE_TESTE):
        do_horizonte_2026 = previsoes_finais[
            (previsoes_finais["h"] == horizonte)
            & (previsoes_finais["data_alvo"] >= INICIO_RECORTE_2026)
            & (previsoes_finais["data_alvo"] <= FIM_RECORTE_2026)
        ]

        for modelo, cor, estilo_da_linha in (
            ("cenario_adotado", "tab:blue", "-"),
            ("histgb_folha20", "tab:orange", "--"),
        ):
            do_modelo = do_horizonte_2026[do_horizonte_2026["modelo"] == modelo].pivot(
                index="data_alvo", columns="quantil", values="previsto"
            )
            if do_modelo.empty:
                continue

            eixo.plot(
                do_modelo.index, do_modelo[0.50], estilo_da_linha, color=cor,
                label=f"{modelo} (mediana)", linewidth=1.6,
            )
            if modelo == "cenario_adotado":
                eixo.fill_between(
                    do_modelo.index, do_modelo[0.05], do_modelo[0.95],
                    color=cor, alpha=0.15, label=f"{modelo} (90%)",
                )

        regua_2026 = previsoes_da_regua[
            (previsoes_da_regua["data_alvo"] >= INICIO_RECORTE_2026)
            & (previsoes_da_regua["data_alvo"] <= FIM_RECORTE_2026)
        ].pivot(index="data_alvo", columns="quantil", values="previsto")
        if not regua_2026.empty:
            eixo.plot(
                regua_2026.index, regua_2026[0.50], ":", color="tab:green",
                label="regua climatologica (mediana)", linewidth=1.6,
            )
            eixo.fill_between(
                regua_2026.index, regua_2026[0.05], regua_2026[0.95],
                color="tab:green", alpha=0.12, label="regua climatologica (90%)",
            )

        observados_2026 = tabela_bruta[
            (tabela_bruta["data"] >= INICIO_RECORTE_2026)
            & (tabela_bruta["data"] <= FIM_RECORTE_2026)
        ]
        eixo.plot(
            observados_2026["data"], observados_2026["casos"], "o", color="black",
            markersize=4, label="casos observados",
        )

        eixo.set_title(f"h = {horizonte} semanas")
        eixo.set_ylabel("casos confirmados")
        eixo.grid(alpha=0.3)

    eixos[0].legend(loc="upper left", fontsize=8, ncol=2)
    eixos[-1].set_xlabel("data-alvo")
    figura.suptitle(
        "Cenario adotado x HistGB folha 20 x regua climatologica — recorte 2026"
    )
    figura.tight_layout()
    figura.savefig(caminho_da_figura, dpi=150)
    plt.close(figura)


# --- Orquestracao -----------------------------------------------------------


def main() -> None:
    """Roda a rodada B inteira, do treino ate as saidas."""
    print("=" * 78)
    print("RODADA B — quantis multiplos e WIS (segunda bateria noturna)")
    print("=" * 78, flush=True)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)

    previsoes_brutas = treinar_todas_as_combinacoes()

    trava_bateu, registro_da_trava = conferir_trava(previsoes_brutas)
    if not trava_bateu:
        investigar_falha_da_trava(previsoes_brutas)
        print(
            "\nBLOCO INVALIDO: a trava nao bateu. Nao vou seguir para o WIS "
            "com um arranjo que nao reproduz o painel. Ver a investigacao acima.",
            flush=True,
        )
        registro_da_trava.to_csv(PASTA_DE_SAIDAS / "trava_h4_h8.csv", index=False)
        return

    # O quantil 0,85 (QUANTIL_DA_TRAVA) so serve para `conferir_trava`, acima.
    # A partir daqui a secao B segue com exatamente os 7 quantis declarados,
    # como pre-declarado (emenda de 26/09/2026, 01h20).
    previsoes_dos_quantis_declarados = previsoes_brutas[
        previsoes_brutas["quantil"].isin(QUANTIS_DECLARADOS)
    ].copy()

    previsoes_finais = ordenar_quantis_cruzados(previsoes_dos_quantis_declarados)
    previsoes_finais.to_csv(PASTA_DE_SAIDAS / "previsoes_quantis.csv", index=False)
    print(f"\nGravado: {PASTA_DE_SAIDAS / 'previsoes_quantis.csv'}")

    tabela_bruta = harness.carregar_tabela_bruta()
    previsoes_da_regua = montar_previsoes_da_regua(
        tabela_bruta, previsoes_finais["data_alvo"]
    )

    origens_do_modelo = montar_tabela_de_origens(previsoes_finais)
    origens_da_regua_por_h = []
    for horizonte in HORIZONTES_DECLARADOS:
        real_por_data = (
            previsoes_finais[previsoes_finais["h"] == horizonte][["data_alvo", "real"]]
            .drop_duplicates("data_alvo")
        )
        regua_com_real = previsoes_da_regua.merge(real_por_data, on="data_alvo")
        regua_com_real["modelo"] = NOME_DA_REGUA
        regua_com_real["h"] = horizonte
        origens_da_regua_por_h.append(montar_tabela_de_origens(regua_com_real))
    origens_da_regua = pd.concat(origens_da_regua_por_h, ignore_index=True)

    origens_do_modelo["recorte"] = marcar_recorte(origens_do_modelo["data_alvo"])
    origens_da_regua["recorte"] = marcar_recorte(origens_da_regua["data_alvo"])

    origens_todos_2024_2026 = pd.concat(
        [origens_do_modelo, origens_da_regua], ignore_index=True
    )
    origens_tudo = origens_todos_2024_2026[
        origens_todos_2024_2026["recorte"].isin(["2024-2025", "2026"])
    ].copy()
    origens_tudo["recorte"] = "tudo"
    origens_com_recortes = pd.concat(
        [origens_todos_2024_2026.dropna(subset=["recorte"]), origens_tudo],
        ignore_index=True,
    )

    tabela_wis_e_cobertura = montar_wis_e_cobertura(origens_com_recortes)
    tabela_wis_e_cobertura.to_csv(PASTA_DE_SAIDAS / "wis_e_cobertura.csv", index=False)
    print(f"Gravado: {PASTA_DE_SAIDAS / 'wis_e_cobertura.csv'}")
    print("\nWIS medio e cobertura, por modelo/h/recorte:")
    print(tabela_wis_e_cobertura.to_string(index=False))

    origens_modelo_com_recorte = origens_com_recortes[
        origens_com_recortes["modelo"] != NOME_DA_REGUA
    ].dropna(subset=["recorte"])
    origens_regua_com_recorte = origens_com_recortes[
        origens_com_recortes["modelo"] == NOME_DA_REGUA
    ].dropna(subset=["recorte"])

    comparacoes_da_familia_b = []
    for recorte in ("2024-2025", "2026", "tudo"):
        for modelo in ("cenario_adotado", "histgb_folha20"):
            for horizonte in HORIZONTES_DE_TESTE:
                comparacoes_da_familia_b.append(
                    comparar_wis_pareado(
                        origens_modelo_com_recorte,
                        origens_regua_com_recorte[
                            origens_regua_com_recorte["h"] == horizonte
                        ],
                        modelo,
                        horizonte,
                        recorte,
                    )
                )

    tabela_familia_b = aplicar_holm_por_recorte(pd.DataFrame(comparacoes_da_familia_b))
    tabela_familia_b.to_csv(PASTA_DE_SAIDAS / "familia_b.csv", index=False)
    print(f"\nGravado: {PASTA_DE_SAIDAS / 'familia_b.csv'}")
    print("\nWIS modelo x WIS regua climatologica, Wilcoxon pareado, Holm por recorte:")
    print(tabela_familia_b.to_string(index=False))

    caminho_da_figura = PASTA_DE_SAIDAS / "figura_intervalos_2026.png"
    desenhar_figura_de_intervalos(
        previsoes_finais, previsoes_da_regua, tabela_bruta, caminho_da_figura
    )
    print(f"\nGravado: {caminho_da_figura}")

    print("\nRODADA B CONCLUIDA.", flush=True)


if __name__ == "__main__":
    main()
