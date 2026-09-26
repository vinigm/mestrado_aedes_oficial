"""Busca aleatoria de hiperparametros, pre-declarada e julgada em 2026.

Protocolo: PRE_DECLARACAO.md (secoes 3 a 6), incluindo a emenda de 25/09/2026
23h50 (travas recalculadas na tabela nova, recorte 2026 ate 19/04/2026).

Reusa o motor da bateria noturna de 23/09/2026 (`harness.py`) so por leitura:
nao altera nada la. Tambem NAO altera o pipeline (`modelagem_aedes/`).

Decisao de escopo computacional (declarada aqui, nao na pre-declaracao, por
custo de CPU medido empiricamente ANTES de rodar: um unico walk-forward de
295 semanas com o modelo de referencia levou ~115s de parede em uma so
chamada de teste): as 120 configuracoes sorteadas da secao 3 rodam walk-
forward SO nos dois horizontes que a nota da secao 4 usa (h=4 e h=12, "1 mes
e 3 meses"). Os quatro horizontes completos (1/4/8/12) exigidos pela secao 5
rodam para as VENCEDORAS e os CONTROLES (no maximo 6 configuracoes de
modelo), nao para as 120 candidatas. Rodar as 120 nos 4 horizontes custaria
da ordem de 120 * 4 * 140s / 8 processos ~= 6h de parede; assim, a fase de
triagem fica em ~120 * 2 * 140s / 8 processos ~= 70 min, e a fase final em
minutos. Reportado como desvio no retorno estruturado, nao decidido em
silencio.
"""

import dataclasses
import json
import multiprocessing
import pathlib
import sys
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DA_BATERIA_NOTURNA = PASTA_DESTE_ARQUIVO.parent / "2026-09-23_bateria_noturna"
PASTA_DO_PIPELINE = PASTA_DESTE_ARQUIVO.parent.parent / "modelagem_aedes"
sys.path.insert(0, str(PASTA_DA_BATERIA_NOTURNA))
sys.path.insert(0, str(PASTA_DO_PIPELINE))

import harness  # noqa: E402  (depende do sys.path ajustado acima)
from config.experimentos.cidade_referencia import CIDADE_REFERENCIA  # noqa: E402
from config.modelo import EspecificacaoModelo  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"
PASTA_DE_PARCIAIS = PASTA_DE_SAIDAS / "parciais"
PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
PASTA_DE_PARCIAIS.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CONSTANTES DO PROTOCOLO (PRE_DECLARACAO.md, secoes 3 a 6, + emenda)
# ============================================================================

SEMENTE_DO_SORTEIO = 20260925
QUANTIL_DE_REFERENCIA = 0.85
N_SORTEIOS_POR_FAMILIA = 60

HORIZONTES_DA_TRIAGEM = (4, 12)
HORIZONTES_COMPLETOS = (1, 4, 8, 12)
HORIZONTES_DE_DECISAO_JULGAMENTO = (4, 12)

INICIO_JANELA_NOTA = pd.Timestamp("2022-01-01")
FIM_JANELA_NOTA = pd.Timestamp("2025-12-31")

INICIO_2026 = pd.Timestamp("2026-01-01")
FIM_2026 = pd.Timestamp("2026-04-19")

INICIO_DESCRITIVO_2024_2025 = pd.Timestamp("2024-01-01")
FIM_DESCRITIVO_2024_2025 = pd.Timestamp("2025-12-31")

# Emenda de 25/09/2026, 23h50: trava recalculada na tabela atualizada, so ate
# a data que os numeros publicados cobriam (fev/2026), nao ate 19/04/2026.
FIM_TRAVA_CENARIO_ADOTADO = pd.Timestamp("2026-02-01")
TRAVA_MAE_CENARIO_ADOTADO = {1: 97.4, 12: 280.0}
TOLERANCIA_DA_TRAVA = 0.2

LIMIAR_ALARME_FALSO = 100.0
NIVEL_DE_SIGNIFICANCIA = 0.05

NOME_CENARIO_ADOTADO = "cenario_adotado"
NOME_HISTGB_FOLHA20 = "HistGB_folha20"
NOME_REGUA_SAZONAL = "regua_sazonal"
NOME_HB_BEST = "HB_best"
NOME_LGB_BEST = "LGB_best"
NOME_LGB_LINEAR = "LGB_linear"
NOME_MONO = "MONO"

BRACOS_JULGADOS = (NOME_HB_BEST, NOME_LGB_BEST, NOME_LGB_LINEAR, NOME_MONO)
CONTROLES = (NOME_CENARIO_ADOTADO, NOME_HISTGB_FOLHA20, NOME_REGUA_SAZONAL)

SEMANAS_DO_PASSO_SAZONAL = 52


# ============================================================================
# SORTEIO DAS 120 CONFIGURACOES (secao 3)
# ============================================================================


def sortear_configuracoes_histgb(rng: np.random.Generator, quantidade: int) -> list[dict]:
    """Sorteia hiperparametros do HistGB conforme as faixas da secao 3.

    Args:
        rng: Gerador de numeros aleatorios ja semeado.
        quantidade: Quantos sorteios fazer.

    Returns:
        Uma lista de dicionarios, um por configuracao sorteada.
    """
    opcoes_de_profundidade_maxima = [None, 3, 4, 6, 8]

    configuracoes_sorteadas: list[dict] = []
    for indice_do_sorteio in range(quantidade):
        log_learning_rate = rng.uniform(np.log(0.01), np.log(0.2))
        learning_rate = float(np.exp(log_learning_rate))

        max_iter = int(rng.integers(100, 601))
        max_leaf_nodes = int(rng.integers(4, 64))
        min_samples_leaf = int(rng.integers(5, 61))

        l2_regularization_e_zero = rng.random() < 0.2
        if l2_regularization_e_zero:
            l2_regularization = 0.0
        else:
            log_l2 = rng.uniform(np.log(0.001), np.log(10.0))
            l2_regularization = float(np.exp(log_l2))

        max_features = float(rng.uniform(0.4, 1.0))

        indice_da_profundidade = int(rng.integers(0, len(opcoes_de_profundidade_maxima)))
        max_depth = opcoes_de_profundidade_maxima[indice_da_profundidade]

        configuracoes_sorteadas.append(
            {
                "config_id": f"histgb_{indice_do_sorteio:03d}",
                "familia": "histgb",
                "learning_rate": learning_rate,
                "max_iter": max_iter,
                "max_leaf_nodes": max_leaf_nodes,
                "min_samples_leaf": min_samples_leaf,
                "l2_regularization": l2_regularization,
                "max_features": max_features,
                "max_depth": max_depth,
                "n_arvores": max_iter,
            }
        )

    return configuracoes_sorteadas


def sortear_configuracoes_lightgbm(rng: np.random.Generator, quantidade: int) -> list[dict]:
    """Sorteia hiperparametros do LightGBM conforme as faixas da secao 3.

    Args:
        rng: Gerador de numeros aleatorios ja semeado (o MESMO do HistGB, na
            sequencia: primeiro os 60 sorteios do HistGB, depois estes).
        quantidade: Quantos sorteios fazer.

    Returns:
        Uma lista de dicionarios, um por configuracao sorteada.
    """
    configuracoes_sorteadas: list[dict] = []
    for indice_do_sorteio in range(quantidade):
        log_learning_rate = rng.uniform(np.log(0.01), np.log(0.2))
        learning_rate = float(np.exp(log_learning_rate))

        n_estimators = int(rng.integers(100, 601))
        num_leaves = int(rng.integers(4, 64))
        min_child_samples = int(rng.integers(5, 61))

        reg_lambda_e_zero = rng.random() < 0.2
        if reg_lambda_e_zero:
            reg_lambda = 0.0
        else:
            log_reg_lambda = rng.uniform(np.log(0.001), np.log(10.0))
            reg_lambda = float(np.exp(log_reg_lambda))

        colsample_bytree = float(rng.uniform(0.4, 1.0))
        subsample = float(rng.uniform(0.5, 1.0))
        extra_trees = bool(rng.integers(0, 2))

        configuracoes_sorteadas.append(
            {
                "config_id": f"lightgbm_{indice_do_sorteio:03d}",
                "familia": "lightgbm",
                "learning_rate": learning_rate,
                "n_estimators": n_estimators,
                "num_leaves": num_leaves,
                "min_child_samples": min_child_samples,
                "reg_lambda": reg_lambda,
                "colsample_bytree": colsample_bytree,
                "subsample": subsample,
                "extra_trees": extra_trees,
                "n_arvores": n_estimators,
            }
        )

    return configuracoes_sorteadas


# ============================================================================
# CONSTRUCAO DAS FICHAS DE MODELO (EspecificacaoModelo) A PARTIR DE UM CONFIG
# ============================================================================


def converter_para_inteiro(valor: object) -> int:
    """Converte um hiperparametro inteiro que pode ter virado float no caminho.

    ⚠️ Uma linha de configuracao passa por merges de pandas (notas + config)
    e por `.iloc[...].to_dict()`. Quando uma linha mistura colunas int e
    float, o pandas devolve a linha inteira num tipo numerico comum (float) —
    por isso `n_estimators=555` chega aqui como `555.0`, e o LightGBM rejeita
    isso (exige int exato). Converter explicitamente evita esse erro
    silencioso de tipo.
    """
    return int(round(float(valor)))


def converter_para_inteiro_ou_none(valor: object) -> int | None:
    """Como `converter_para_inteiro`, mas preservando o fallback None.

    `max_depth` pode ser `None` (sem limite). Depois de passar pelas mesmas
    conversoes de pandas descritas em `converter_para_inteiro`, o `None`
    tende a chegar como `NaN` (float) — o fallback original tem que ser
    reconhecido nesse formato tambem, e nao seria pego por um `is None` puro.
    """
    if valor is None:
        return None
    if isinstance(valor, float) and np.isnan(valor):
        return None
    return converter_para_inteiro(valor)


def construir_especificacao_histgb(config: dict) -> EspecificacaoModelo:
    """Monta a ficha do HistGB a partir de uma linha sorteada ou fixa."""
    parametros = {
        "learning_rate": float(config["learning_rate"]),
        "max_iter": converter_para_inteiro(config["max_iter"]),
        "max_leaf_nodes": converter_para_inteiro(config["max_leaf_nodes"]),
        "min_samples_leaf": converter_para_inteiro(config["min_samples_leaf"]),
        # .get(..., default) com os defaults do proprio sklearn: o config do
        # cenario adotado (config_cenario_adotado, vindo direto de
        # CIDADE_REFERENCIA.modelo.parametros) nao define estes tres — o
        # experimento sempre usou o default do HistGradientBoostingRegressor
        # pra eles, e reproduzir isso aqui evita um KeyError E preserva o
        # comportamento real do cenario adotado.
        "l2_regularization": float(config.get("l2_regularization", 0.0)),
        "max_features": float(config.get("max_features", 1.0)),
        "max_depth": converter_para_inteiro_ou_none(config.get("max_depth")),
        "random_state": 42,
        "loss": "quantile",
        "quantile": QUANTIL_DE_REFERENCIA,
    }
    if config.get("monotonic_cst") is not None:
        parametros["monotonic_cst"] = config["monotonic_cst"]

    return EspecificacaoModelo(
        nome=config["config_id"], classe=HistGradientBoostingRegressor, parametros=parametros
    )


def construir_especificacao_lightgbm(config: dict) -> EspecificacaoModelo:
    """Monta a ficha do LightGBM a partir de uma linha sorteada ou fixa."""
    parametros = {
        "learning_rate": float(config["learning_rate"]),
        "n_estimators": converter_para_inteiro(config["n_estimators"]),
        "num_leaves": converter_para_inteiro(config["num_leaves"]),
        "min_child_samples": converter_para_inteiro(config["min_child_samples"]),
        "reg_lambda": float(config["reg_lambda"]),
        "colsample_bytree": float(config["colsample_bytree"]),
        "subsample": float(config["subsample"]),
        "subsample_freq": 1,
        "extra_trees": bool(config["extra_trees"]),
        "random_state": 42,
        "n_jobs": 1,
        "verbose": -1,
        "objective": "quantile",
        "alpha": QUANTIL_DE_REFERENCIA,
    }
    if config.get("linear_tree"):
        parametros["linear_tree"] = True
        parametros["linear_lambda"] = float(config["linear_lambda"])
    if config.get("monotone_constraints") is not None:
        parametros["monotone_constraints"] = config["monotone_constraints"]

    return EspecificacaoModelo(
        nome=config["config_id"], classe=LGBMRegressor, parametros=parametros
    )


def construir_especificacao_do_config(config: dict) -> EspecificacaoModelo:
    """Despacha para o construtor certo conforme a familia do config.

    Nomeada em vez de lambda, por causa da regra de sintaxe do padrao de
    codigo do projeto (secao 3.1 de PADRAO-CODIGO-PYTHON.md).
    """
    if config["familia"] in ("histgb", "histgb_folha20", "mono_histgb"):
        return construir_especificacao_histgb(config)
    if config["familia"] in ("lightgbm", "lgb_linear", "mono_lightgbm"):
        return construir_especificacao_lightgbm(config)
    raise ValueError(f"Familia de modelo desconhecida: {config['familia']}")


# ============================================================================
# EXECUCAO PARALELA (fork; TABELA_GLOBAL/COLUNAS_GLOBAL ja calculados no pai)
# ============================================================================

TABELA_GLOBAL: pd.DataFrame | None = None
COLUNAS_GLOBAL: list[str] | None = None


def rodar_uma_configuracao(tarefa: dict) -> str:
    """Roda o walk-forward de uma configuracao nos horizontes pedidos.

    Roda em processo filho (fork): usa TABELA_GLOBAL e COLUNAS_GLOBAL, ja
    calculados no processo pai ANTES do fork, para nao repetir a engenharia
    de features (que envolve um ajuste de modelo por horizonte de selecao de
    clima) uma vez por configuracao.

    Args:
        tarefa: dicionario com "config" (a linha da configuracao) e
            "horizontes" (quais h rodar para esta configuracao).

    Returns:
        O config_id da configuracao rodada (para acompanhamento no log).
    """
    config = tarefa["config"]
    horizontes = tarefa["horizontes"]
    especificacao = construir_especificacao_do_config(config)

    previsoes_da_configuracao = []
    for horizonte in horizontes:
        inicio = time.perf_counter()
        previsoes = harness.rodar_walk_forward(
            TABELA_GLOBAL, COLUNAS_GLOBAL, horizonte, especificacao
        )
        previsoes["config_id"] = config["config_id"]
        previsoes["familia"] = config["familia"]
        previsoes_da_configuracao.append(previsoes)
        duracao = time.perf_counter() - inicio
        print(
            f"  [{config['config_id']}] h={horizonte:2d}  {len(previsoes):3d} sem  "
            f"{duracao:6.1f}s",
            flush=True,
        )

    resultado_da_configuracao = pd.concat(previsoes_da_configuracao, ignore_index=True)
    caminho_parcial = PASTA_DE_PARCIAIS / f"{config['config_id']}.csv"
    resultado_da_configuracao.to_csv(caminho_parcial, index=False)
    return config["config_id"]


def rodar_lote_em_paralelo(
    configuracoes: list[dict], horizontes: tuple[int, ...], n_processos: int = 8
) -> pd.DataFrame:
    """Roda um lote de configuracoes em paralelo, gravando cada uma ao terminar.

    Args:
        configuracoes: As configuracoes a rodar.
        horizontes: Os horizontes a rodar para TODAS as configuracoes deste
            lote.
        n_processos: Quantos processos usar em paralelo.

    Returns:
        Todas as previsoes do lote, empilhadas num DataFrame so.
    """
    tarefas = []
    for config in configuracoes:
        tarefas.append({"config": config, "horizontes": horizontes})

    contexto_fork = multiprocessing.get_context("fork")
    with contexto_fork.Pool(processes=n_processos) as piscina_de_processos:
        config_ids_concluidos = piscina_de_processos.map(rodar_uma_configuracao, tarefas)

    print(
        f"Lote concluido: {len(config_ids_concluidos)} configuracoes, "
        f"horizontes {horizontes}.",
        flush=True,
    )

    previsoes_do_lote = []
    for config in configuracoes:
        caminho_parcial = PASTA_DE_PARCIAIS / f"{config['config_id']}.csv"
        previsoes_do_lote.append(
            pd.read_csv(caminho_parcial, parse_dates=["data_alvo"])
        )

    return pd.concat(previsoes_do_lote, ignore_index=True)


# ============================================================================
# NOTA DA SECAO 4 (SO 2022-01-01 a 2025-12-31, h=4 e h=12)
# ============================================================================


def calcular_notas(previsoes_da_triagem: pd.DataFrame) -> pd.DataFrame:
    """Calcula a nota de cada configuracao: media do MAE em h=4 e h=12.

    So usa pares com 2022-01-01 <= data_alvo <= 2025-12-31 (secao 4). Prova,
    por construcao, que 2026 nunca entra: filtra por FIM_JANELA_NOTA antes de
    qualquer calculo.

    Args:
        previsoes_da_triagem: Previsoes das 120 configuracoes, h em
            HORIZONTES_DA_TRIAGEM.

    Returns:
        Uma linha por config_id, com mae_h4, mae_h12, nota e n de cada h.
    """
    dentro_da_janela = (
        (previsoes_da_triagem["data_alvo"] >= INICIO_JANELA_NOTA)
        & (previsoes_da_triagem["data_alvo"] <= FIM_JANELA_NOTA)
    )
    pares_da_nota = previsoes_da_triagem[dentro_da_janela]

    maior_data_alvo_usada = pares_da_nota["data_alvo"].max()
    print(
        f"PROVA: maior data_alvo usada na nota = {maior_data_alvo_usada.date()} "
        f"(tem que ser <= {FIM_JANELA_NOTA.date()}; 2026 NAO entra).",
        flush=True,
    )

    linhas_de_nota = []
    for config_id, grupo_da_configuracao in pares_da_nota.groupby("config_id"):
        grupo_h4 = grupo_da_configuracao[grupo_da_configuracao["h"] == 4]
        grupo_h12 = grupo_da_configuracao[grupo_da_configuracao["h"] == 12]

        mae_h4 = mean_absolute_error(grupo_h4["real"], grupo_h4["previsto"])
        mae_h12 = mean_absolute_error(grupo_h12["real"], grupo_h12["previsto"])
        nota = float(np.mean([mae_h4, mae_h12]))

        linhas_de_nota.append(
            {
                "config_id": config_id,
                "mae_h4": mae_h4,
                "mae_h12": mae_h12,
                "nota": nota,
                "n_h4": len(grupo_h4),
                "n_h12": len(grupo_h12),
            }
        )

    return pd.DataFrame(linhas_de_nota)


CAMPOS_DE_PONTUACAO = (
    "mae_h4",
    "mae_h12",
    "nota",
    "n_h4",
    "n_h12",
    "nota_arredondada",
)


def remover_campos_de_pontuacao(config: dict) -> dict:
    """Devolve uma copia do config sem os campos de nota/selecao.

    ⚠️ Uma vencedora (saida de `escolher_vencedora_da_familia`) carrega, alem
    dos hiperparametros, os campos da propria selecao (nota, mae_h4, mae_h12,
    ...). Copiar essa dict direto para montar um NOVO candidato (LGB_linear,
    MONO) e depois colocar esse candidato numa tabela que sera mesclada com
    uma nota NOVA faz o pandas colidir nomes de coluna ("nota_x"/"nota_y") e
    a coluna "nota" desaparece silenciosamente do merge seguinte. Por isso
    esses campos sao removidos ANTES de reusar o dict como base de um novo
    candidato.
    """
    config_limpo = dict(config)
    for campo in CAMPOS_DE_PONTUACAO:
        config_limpo.pop(campo, None)
    return config_limpo


def escolher_vencedora_da_familia(
    notas: pd.DataFrame, configuracoes: pd.DataFrame, familia: str
) -> dict:
    """Escolhe a configuracao de menor nota numa familia, com desempate.

    Empate ate a primeira casa decimal da nota: vence a de menos arvores
    (secao 4 da pre-declaracao).

    Args:
        notas: Saida de calcular_notas.
        configuracoes: A tabela de configuracoes sorteadas (para achar o
            numero de arvores de cada uma).
        familia: "histgb" ou "lightgbm".

    Returns:
        A linha completa (config + nota) da vencedora, como dicionario.
    """
    configuracoes_da_familia = configuracoes[configuracoes["familia"] == familia]
    tabela_unida = notas.merge(configuracoes_da_familia, on="config_id")
    tabela_unida["nota_arredondada"] = tabela_unida["nota"].round(1)

    tabela_ordenada = tabela_unida.sort_values(["nota_arredondada", "n_arvores"])
    linha_vencedora = tabela_ordenada.iloc[0]
    return linha_vencedora.to_dict()


# ============================================================================
# BRACO LGB_linear
# ============================================================================


def testar_compatibilidade_monotone_constraints_lightgbm_quantile() -> bool:
    """Testa se o LightGBM instalado aceita monotone_constraints com objective=quantile.

    Achado empirico (LightGBM 4.6.0, 25/09/2026): NAO aceita — erro fatal
    "Cannot use monotone_constraints in quantile objective, please disable
    it.". Testado aqui, e nao assumido, porque a versao instalada pode mudar.
    """
    dados_de_teste_x = np.random.RandomState(0).rand(50, 3)
    dados_de_teste_y = np.random.RandomState(1).rand(50)
    try:
        modelo_de_teste = LGBMRegressor(
            n_estimators=10,
            objective="quantile",
            alpha=QUANTIL_DE_REFERENCIA,
            monotone_constraints=[1, 0, -1],
            verbose=-1,
            n_jobs=1,
            random_state=42,
        )
        modelo_de_teste.fit(dados_de_teste_x, dados_de_teste_y)
        return True
    except Exception as erro:
        print(
            f"MONO (base LightGBM): monotone_constraints + objective=quantile FALHOU: {erro!r}",
            flush=True,
        )
        return False


def testar_compatibilidade_linear_tree_com_quantile() -> bool:
    """Testa, empiricamente, se o LightGBM aceita linear_tree com objetivo quantile.

    Nao assume nada da versao instalada: treina um modelo minusculo e devolve
    se o ajuste terminou sem excecao.
    """
    dados_de_teste_x = np.random.RandomState(0).rand(50, 3)
    dados_de_teste_y = np.random.RandomState(1).rand(50)
    try:
        modelo_de_teste = LGBMRegressor(
            n_estimators=10,
            objective="quantile",
            alpha=QUANTIL_DE_REFERENCIA,
            linear_tree=True,
            linear_lambda=1.0,
            verbose=-1,
            n_jobs=1,
            random_state=42,
        )
        modelo_de_teste.fit(dados_de_teste_x, dados_de_teste_y)
        return True
    except Exception as erro:
        print(f"LGB_linear: linear_tree + objective=quantile FALHOU: {erro!r}", flush=True)
        return False


# ============================================================================
# BRACO MONO
# ============================================================================


def eh_coluna_de_casos_ou_vetor(nome_da_coluna: str) -> bool:
    """Diz se uma coluna e de casos (nucleo) ou do vetor, para a restricao MONO."""
    eh_de_casos = "casos" in nome_da_coluna
    eh_de_vetor = any(padrao in nome_da_coluna for padrao in CIDADE_REFERENCIA.padroes_vetor)
    return eh_de_casos or eh_de_vetor


def construir_vetor_monotonico(colunas_do_modelo: list[str]) -> list[int]:
    """Monta o vetor de restricao monotonica, na ordem que o harness usa.

    A ordem de features passada ao modelo e colunas_do_modelo + ["alvo_sin",
    "alvo_cos"] (ver harness.rodar_walk_forward). As duas ultimas (a
    sazonalidade do ALVO futuro) nao sao de casos nem de vetor, entao ficam
    sem restricao (0), como pede a secao 3: "sem restricao no resto".

    Args:
        colunas_do_modelo: As 20 colunas do cenario adotado, na ordem em que
            entram no modelo.

    Returns:
        Uma lista de -1/0/1, um valor por feature, na ordem
        colunas_do_modelo + [alvo_sin, alvo_cos].
    """
    vetor_de_restricoes = []
    for nome_da_coluna in colunas_do_modelo:
        if eh_coluna_de_casos_ou_vetor(nome_da_coluna):
            vetor_de_restricoes.append(1)
        else:
            vetor_de_restricoes.append(0)

    vetor_de_restricoes.append(0)  # alvo_sin
    vetor_de_restricoes.append(0)  # alvo_cos
    return vetor_de_restricoes


# ============================================================================
# REGRA SAZONAL (controle "regua")
# ============================================================================


def carregar_serie_semanal_de_casos(tabela_bruta: pd.DataFrame) -> dict[pd.Timestamp, float]:
    """Indexa casos_confirmados por data, para a regua sazonal andar por data."""
    return dict(zip(tabela_bruta["data"], tabela_bruta["casos"]))


def calcular_previsoes_da_regua_sazonal(
    pares_h_data_alvo: pd.DataFrame, casos_por_data: dict[pd.Timestamp, float]
) -> pd.DataFrame:
    """Repete o caso de exatamente 52 semanas antes da data_alvo.

    Mesma regra usada em analises/2026-09-25_regua_regras_simples/
    calcular_regua.py (calcular_regra_sazonal), reimplementada aqui em vez de
    importada porque aquele script nao expoe uma API de modulo estavel — so
    um main() de script.

    Args:
        pares_h_data_alvo: Colunas h e data_alvo, uma linha por par unico.
        casos_por_data: Serie semanal de casos indexada por data.

    Returns:
        DataFrame com h, data_alvo, real e previsto (podendo ser NaN).
    """
    linhas_da_regua = []
    for _, par in pares_h_data_alvo.iterrows():
        horizonte = int(par["h"])
        data_alvo = par["data_alvo"]
        semana_um_ano_antes = data_alvo - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)

        linhas_da_regua.append(
            {
                "h": horizonte,
                "data_alvo": data_alvo,
                "real": casos_por_data.get(data_alvo, np.nan),
                "previsto": casos_por_data.get(semana_um_ano_antes, np.nan),
                "config_id": NOME_REGUA_SAZONAL,
                "familia": "regra",
            }
        )

    return pd.DataFrame(linhas_da_regua)


# ============================================================================
# TRAVA DE VALIDACAO (emenda de 25/09/2026, 23h50)
# ============================================================================


def conferir_trava_do_cenario_adotado(previsoes_do_cenario_adotado: pd.DataFrame) -> bool:
    """Confere a trava recalculada: h=1 MAE 97,4 e h=12 MAE 280,0, ate fev/2026.

    Registra tambem h=4 e h=8 (sem tolerancia definida, so para o relatorio),
    como pede o brief.

    Returns:
        True se h=1 e h=12 baterem dentro da tolerancia de 0,2.
    """
    ate_fevereiro_2026 = previsoes_do_cenario_adotado[
        previsoes_do_cenario_adotado["data_alvo"] <= FIM_TRAVA_CENARIO_ADOTADO
    ]

    print("\n  TRAVA DO CENARIO ADOTADO (tabela nova, ate 01/02/2026)", flush=True)
    tudo_bate = True
    maes_por_horizonte = {}
    for horizonte in HORIZONTES_COMPLETOS:
        celula = ate_fevereiro_2026[ate_fevereiro_2026["h"] == horizonte]
        mae = mean_absolute_error(celula["real"], celula["previsto"])
        maes_por_horizonte[horizonte] = float(mae)

        if horizonte in TRAVA_MAE_CENARIO_ADOTADO:
            esperado = TRAVA_MAE_CENARIO_ADOTADO[horizonte]
            bate = abs(mae - esperado) < TOLERANCIA_DA_TRAVA
            tudo_bate = tudo_bate and bate
            marca = "ok" if bate else "<<< DIVERGE"
            print(f"    h={horizonte:2d}  MAE {mae:7.2f} (trava {esperado:6.1f})  {marca}  n={len(celula)}")
        else:
            print(f"    h={horizonte:2d}  MAE {mae:7.2f}  (sem trava — registrado)  n={len(celula)}")

    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}", flush=True)

    with open(PASTA_DE_SAIDAS / "trava_cenario_adotado.json", "w", encoding="utf-8") as arquivo:
        json.dump(
            {
                "maes_ate_fev_2026": maes_por_horizonte,
                "trava_h1_h12": TRAVA_MAE_CENARIO_ADOTADO,
                "tolerancia": TOLERANCIA_DA_TRAVA,
                "valido": tudo_bate,
            },
            arquivo,
            indent=2,
        )

    return tudo_bate


# ============================================================================
# METRICAS DE JULGAMENTO (secao 5)
# ============================================================================


def calcular_perda_quantilica(valores_reais: np.ndarray, valores_previstos: np.ndarray) -> float:
    """Perda quantilica pinball no quantil 0,85 (mesma formula do cenario adotado)."""
    diferenca = valores_reais - valores_previstos
    termos = np.maximum(
        QUANTIL_DE_REFERENCIA * diferenca, (QUANTIL_DE_REFERENCIA - 1.0) * diferenca
    )
    return float(np.mean(termos))


def calcular_cobertura(valores_reais: np.ndarray, valores_previstos: np.ndarray) -> float:
    """Fracao de semanas em que o real ficou no ou abaixo do previsto (q0,85)."""
    return float(np.mean(valores_reais <= valores_previstos))


def montar_julgamento_2026(previsoes_completas: pd.DataFrame) -> pd.DataFrame:
    """MAE, alarmes falsos (limiar 100) e teto (maior previsto x maior real), 2026.

    Args:
        previsoes_completas: Previsoes de todos os bracos julgados e
            controles, horizontes completos, com coluna "entidade".

    Returns:
        Uma linha por (entidade, h), com as metricas da secao 5.
    """
    em_2026 = previsoes_completas[
        (previsoes_completas["data_alvo"] >= INICIO_2026)
        & (previsoes_completas["data_alvo"] <= FIM_2026)
    ]

    linhas_do_julgamento = []
    for entidade in sorted(em_2026["entidade"].unique()):
        da_entidade = em_2026[em_2026["entidade"] == entidade]
        for horizonte in HORIZONTES_COMPLETOS:
            do_horizonte = da_entidade[da_entidade["h"] == horizonte]
            if len(do_horizonte) == 0:
                continue

            valores_reais = do_horizonte["real"].to_numpy()
            valores_previstos = do_horizonte["previsto"].to_numpy()

            mae = float(mean_absolute_error(valores_reais, valores_previstos))
            alarmes_falsos = int(
                np.sum((valores_previstos > LIMIAR_ALARME_FALSO) & (valores_reais <= LIMIAR_ALARME_FALSO))
            )

            linhas_do_julgamento.append(
                {
                    "entidade": entidade,
                    "h": horizonte,
                    "n": len(do_horizonte),
                    "mae_2026": mae,
                    "alarmes_falsos_2026": alarmes_falsos,
                    "maior_previsto_2026": float(np.max(valores_previstos)),
                    "maior_real_2026": float(np.max(valores_reais)),
                }
            )

    return pd.DataFrame(linhas_do_julgamento)


def montar_descritivo_2024_2025(previsoes_completas: pd.DataFrame) -> pd.DataFrame:
    """MAE, perda quantilica e cobertura em 2024-2025 (ja usado na escolha)."""
    no_periodo = previsoes_completas[
        (previsoes_completas["data_alvo"] >= INICIO_DESCRITIVO_2024_2025)
        & (previsoes_completas["data_alvo"] <= FIM_DESCRITIVO_2024_2025)
    ]

    linhas_do_descritivo = []
    for entidade in sorted(no_periodo["entidade"].unique()):
        da_entidade = no_periodo[no_periodo["entidade"] == entidade]
        for horizonte in HORIZONTES_COMPLETOS:
            do_horizonte = da_entidade[da_entidade["h"] == horizonte]
            if len(do_horizonte) == 0:
                continue

            valores_reais = do_horizonte["real"].to_numpy()
            valores_previstos = do_horizonte["previsto"].to_numpy()

            linhas_do_descritivo.append(
                {
                    "entidade": entidade,
                    "h": horizonte,
                    "n": len(do_horizonte),
                    "mae_2024_2025": float(mean_absolute_error(valores_reais, valores_previstos)),
                    "perda_quantilica_2024_2025": calcular_perda_quantilica(
                        valores_reais, valores_previstos
                    ),
                    "cobertura_2024_2025": calcular_cobertura(valores_reais, valores_previstos),
                }
            )

    return pd.DataFrame(linhas_do_descritivo)


def montar_holm_2026(previsoes_completas: pd.DataFrame, bracos_presentes: list[str]) -> pd.DataFrame:
    """Wilcoxon pareado de cada braco julgado contra o cenario adotado, em 2026.

    Familia: bracos_presentes x horizontes de decisao (h=4 e h=12) = ate 8
    comparacoes. Holm sobre a familia inteira.
    """
    em_2026 = previsoes_completas[
        (previsoes_completas["data_alvo"] >= INICIO_2026)
        & (previsoes_completas["data_alvo"] <= FIM_2026)
    ].rename(columns={"entidade": "braco"})

    comparacoes = []
    for braco in bracos_presentes:
        for horizonte in HORIZONTES_DE_DECISAO_JULGAMENTO:
            try:
                comparacoes.append(
                    harness.comparar_pareado(em_2026, NOME_CENARIO_ADOTADO, braco, horizonte)
                )
            except ValueError as erro:
                # Defensivo: no protocolo pre-declarado (passo=1, corte 2026
                # ate 19/04) isto nao deveria acontecer — todos os bracos
                # rodam sobre a MESMA tabela de features, entao tem o mesmo
                # conjunto de datas por horizonte. Se acontecer mesmo assim,
                # a comparacao fica de fora da familia de Holm e o motivo vai
                # pro log, em vez de derrubar a rodada inteira.
                print(f"  AVISO: sem semanas pareadas para {braco} em h={horizonte}: {erro}", flush=True)

    p_corrigidos = harness.corrigir_por_holm(comparacoes)

    linhas_holm = []
    for comparacao in comparacoes:
        chave = f"{comparacao.braco}:{comparacao.horizonte}"
        linhas_holm.append(
            {
                "braco": comparacao.braco,
                "h": comparacao.horizonte,
                "mae_cenario_adotado": comparacao.mae_referencia,
                "mae_braco": comparacao.mae_variante,
                "reducao_percentual": comparacao.reducao_percentual(),
                "n_pareado": comparacao.semanas_pareadas,
                "p_bruto": comparacao.p_bruto,
                "p_holm": p_corrigidos[chave],
                "significativo_5pct": p_corrigidos[chave] < NIVEL_DE_SIGNIFICANCIA,
            }
        )

    return pd.DataFrame(linhas_holm)


# ============================================================================
# FIGURA
# ============================================================================


def gerar_figura_2026(previsoes_completas: pd.DataFrame, julgamento: pd.DataFrame) -> None:
    """Gera a figura de 2026: MAE por horizonte e serie real x previsto em h=12."""
    figura, eixos = plt.subplots(1, 2, figsize=(13, 5))

    eixo_mae = eixos[0]
    for entidade in sorted(julgamento["entidade"].unique()):
        da_entidade = julgamento[julgamento["entidade"] == entidade].sort_values("h")
        eixo_mae.plot(da_entidade["h"], da_entidade["mae_2026"], marker="o", label=entidade)
    eixo_mae.set_xlabel("horizonte (semanas)")
    eixo_mae.set_ylabel("MAE em 2026 (jan-19/abr)")
    eixo_mae.set_title("MAE por horizonte, 2026")
    eixo_mae.legend(fontsize=7)
    eixo_mae.grid(alpha=0.3)

    eixo_serie = eixos[1]
    em_2026_h12 = previsoes_completas[
        (previsoes_completas["h"] == 12)
        & (previsoes_completas["data_alvo"] >= INICIO_2026)
        & (previsoes_completas["data_alvo"] <= FIM_2026)
    ]
    plotado_o_real = False
    for entidade in sorted(em_2026_h12["entidade"].unique()):
        da_entidade = em_2026_h12[em_2026_h12["entidade"] == entidade].sort_values("data_alvo")
        if not plotado_o_real:
            eixo_serie.plot(
                da_entidade["data_alvo"], da_entidade["real"], color="black", linewidth=2, label="real"
            )
            plotado_o_real = True
        eixo_serie.plot(da_entidade["data_alvo"], da_entidade["previsto"], marker=".", label=entidade)
    eixo_serie.set_title("h=12: previsto x real, 2026")
    eixo_serie.legend(fontsize=7)
    eixo_serie.grid(alpha=0.3)
    figura.autofmt_xdate()

    figura.tight_layout()
    figura.savefig(PASTA_DE_SAIDAS / "figura_2026.png", dpi=130)
    plt.close(figura)


# ============================================================================
# ORQUESTRACAO
# ============================================================================


def main() -> None:
    """Roda a busca inteira: sorteio, triagem, bracos, controles e julgamento."""
    inicio_geral = time.perf_counter()
    print("=" * 78)
    print("BUSCA DE HIPERPARAMETROS — pre-declarada, julgada em 2026")
    print("=" * 78, flush=True)

    global TABELA_GLOBAL, COLUNAS_GLOBAL

    tabela_bruta = harness.carregar_tabela_bruta()
    TABELA_GLOBAL, COLUNAS_GLOBAL, clima_escolhido = harness.montar_features_do_braco(
        tabela_bruta, harness.Braco("referencia")
    )
    print(f"colunas do modelo ({len(COLUNAS_GLOBAL)}): {COLUNAS_GLOBAL}")
    print(f"clima escolhido: {clima_escolhido}", flush=True)

    if len(COLUNAS_GLOBAL) != 20:
        raise ValueError(
            f"Esperava 20 colunas do cenario adotado, vieram {len(COLUNAS_GLOBAL)}."
        )

    # ------------------------------------------------------------------
    # 1) SORTEIO (secao 3) — gravado ANTES de qualquer walk-forward.
    # ------------------------------------------------------------------
    rng = np.random.default_rng(SEMENTE_DO_SORTEIO)
    configuracoes_histgb = sortear_configuracoes_histgb(rng, N_SORTEIOS_POR_FAMILIA)
    configuracoes_lightgbm = sortear_configuracoes_lightgbm(rng, N_SORTEIOS_POR_FAMILIA)
    todas_as_configuracoes = configuracoes_histgb + configuracoes_lightgbm

    tabela_de_configuracoes = pd.DataFrame(todas_as_configuracoes)
    tabela_de_configuracoes.to_csv(PASTA_DE_SAIDAS / "configuracoes_sorteadas.csv", index=False)
    print(
        f"\nSorteio gravado: {len(configuracoes_histgb)} HistGB + "
        f"{len(configuracoes_lightgbm)} LightGBM = {len(todas_as_configuracoes)} configs, "
        f"semente {SEMENTE_DO_SORTEIO}.",
        flush=True,
    )

    # ------------------------------------------------------------------
    # 2) TRIAGEM: walk-forward de cada uma das 120 nos horizontes da nota.
    # ------------------------------------------------------------------
    print(
        f"\nTriagem: {len(todas_as_configuracoes)} configs x horizontes "
        f"{HORIZONTES_DA_TRIAGEM} (h=4 e h=12 — o par que a nota da secao 4 usa).",
        flush=True,
    )
    previsoes_da_triagem = rodar_lote_em_paralelo(
        todas_as_configuracoes, HORIZONTES_DA_TRIAGEM, n_processos=8
    )

    notas = calcular_notas(previsoes_da_triagem)
    notas.to_csv(PASTA_DE_SAIDAS / "notas_2022_2025.csv", index=False)

    vencedora_histgb = escolher_vencedora_da_familia(notas, tabela_de_configuracoes, "histgb")
    vencedora_lightgbm = escolher_vencedora_da_familia(notas, tabela_de_configuracoes, "lightgbm")
    print(
        f"\nHB_best  = {vencedora_histgb['config_id']}  nota={vencedora_histgb['nota']:.2f}  "
        f"arvores={vencedora_histgb['n_arvores']}",
        flush=True,
    )
    print(
        f"LGB_best = {vencedora_lightgbm['config_id']}  nota={vencedora_lightgbm['nota']:.2f}  "
        f"arvores={vencedora_lightgbm['n_arvores']}",
        flush=True,
    )

    # ------------------------------------------------------------------
    # 3) BRACO LGB_linear (sobre a vencedora do LightGBM).
    # ------------------------------------------------------------------
    linear_tree_e_compativel = testar_compatibilidade_linear_tree_com_quantile()
    lgb_linear_impossivel = not linear_tree_e_compativel
    config_lgb_linear_vencedora = None

    if linear_tree_e_compativel:
        candidatos_lgb_linear = []
        for lambda_linear in (0.1, 1.0, 10.0):
            candidato = remover_campos_de_pontuacao(vencedora_lightgbm)
            candidato["config_id"] = f"lgb_linear_lambda{lambda_linear}"
            candidato["familia"] = "lgb_linear"
            candidato["linear_tree"] = True
            candidato["linear_lambda"] = lambda_linear
            candidatos_lgb_linear.append(candidato)

        print(f"\nLGB_linear: testando 3 candidatos de linear_lambda.", flush=True)
        previsoes_lgb_linear_triagem = rodar_lote_em_paralelo(
            candidatos_lgb_linear, HORIZONTES_DA_TRIAGEM, n_processos=3
        )
        notas_lgb_linear = calcular_notas(previsoes_lgb_linear_triagem)
        tabela_candidatos_lgb_linear = pd.DataFrame(candidatos_lgb_linear)
        tabela_candidatos_lgb_linear["n_arvores"] = tabela_candidatos_lgb_linear["n_estimators"]

        vencedora_lgb_linear = escolher_vencedora_da_familia(
            notas_lgb_linear, tabela_candidatos_lgb_linear, "lgb_linear"
        )
        config_lgb_linear_vencedora = vencedora_lgb_linear
        print(
            f"LGB_linear vencedora = {vencedora_lgb_linear['config_id']}  "
            f"nota={vencedora_lgb_linear['nota']:.2f}",
            flush=True,
        )
    else:
        print("\nLGB_linear: IMPOSSIVEL (linear_tree nao roda com objective=quantile).", flush=True)

    # ------------------------------------------------------------------
    # 4) BRACO MONO (sobre a vencedora GERAL, HistGB ou LightGBM).
    # ------------------------------------------------------------------
    if vencedora_histgb["nota"] <= vencedora_lightgbm["nota"]:
        vencedora_geral = vencedora_histgb
        familia_mono = "mono_histgb"
    else:
        vencedora_geral = vencedora_lightgbm
        familia_mono = "mono_lightgbm"

    vetor_monotonico = construir_vetor_monotonico(COLUNAS_GLOBAL)
    mono_impossivel = False
    config_mono = remover_campos_de_pontuacao(vencedora_geral)
    config_mono["config_id"] = NOME_MONO
    config_mono["familia"] = familia_mono
    if familia_mono == "mono_histgb":
        config_mono["monotonic_cst"] = vetor_monotonico
    else:
        # Achado empirico (ver testar_compatibilidade_monotone_constraints_
        # lightgbm_quantile): o LightGBM 4.6.0 rejeita monotone_constraints
        # junto de objective=quantile. A secao 3 pede o braco "sem trocar a
        # perda" quando a combinacao falha — mesma regra do LGB_linear.
        mono_impossivel = not testar_compatibilidade_monotone_constraints_lightgbm_quantile()
        config_mono["monotone_constraints"] = vetor_monotonico

    if mono_impossivel:
        print(
            f"\nMONO: IMPOSSIVEL — base {vencedora_geral['config_id']} e LightGBM, e "
            "monotone_constraints nao roda com objective=quantile nesta versao.",
            flush=True,
        )
    else:
        print(
            f"\nMONO: baseada em {vencedora_geral['config_id']} ({familia_mono}), "
            f"restricao em {sum(1 for v in vetor_monotonico if v == 1)} de "
            f"{len(vetor_monotonico)} features.",
            flush=True,
        )

    # ------------------------------------------------------------------
    # 5) VENCEDORAS + CONTROLES, horizontes completos (secao 5).
    # ------------------------------------------------------------------
    config_hb_best_completo = dict(vencedora_histgb)
    config_hb_best_completo["config_id"] = NOME_HB_BEST

    config_lgb_best_completo = dict(vencedora_lightgbm)
    config_lgb_best_completo["config_id"] = NOME_LGB_BEST

    config_cenario_adotado = dict(CIDADE_REFERENCIA.modelo.parametros)
    config_cenario_adotado["config_id"] = NOME_CENARIO_ADOTADO
    config_cenario_adotado["familia"] = "histgb"

    config_histgb_folha20 = {
        "config_id": NOME_HISTGB_FOLHA20,
        "familia": "histgb",
        "learning_rate": 0.05,
        "max_iter": 250,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 20,
        "l2_regularization": 0.0,
        "max_features": 1.0,
        "max_depth": None,
    }

    configuracoes_finais = [
        config_hb_best_completo,
        config_lgb_best_completo,
        config_cenario_adotado,
        config_histgb_folha20,
    ]
    if not mono_impossivel:
        configuracoes_finais.append(config_mono)
    if config_lgb_linear_vencedora is not None:
        config_lgb_linear_completo = dict(config_lgb_linear_vencedora)
        config_lgb_linear_completo["config_id"] = NOME_LGB_LINEAR
        configuracoes_finais.append(config_lgb_linear_completo)

    print(
        f"\nRodada final: {len(configuracoes_finais)} configuracoes de modelo x "
        f"horizontes {HORIZONTES_COMPLETOS}.",
        flush=True,
    )
    previsoes_finais = rodar_lote_em_paralelo(
        configuracoes_finais, HORIZONTES_COMPLETOS, n_processos=6
    )
    previsoes_finais = previsoes_finais.rename(columns={"config_id": "entidade"})

    # Regua sazonal: mesma grade (h, data_alvo) do cenario adotado.
    casos_por_data = carregar_serie_semanal_de_casos(tabela_bruta)
    grade_do_cenario_adotado = previsoes_finais[
        previsoes_finais["entidade"] == NOME_CENARIO_ADOTADO
    ][["h", "data_alvo"]].drop_duplicates()
    previsoes_da_regua = calcular_previsoes_da_regua_sazonal(grade_do_cenario_adotado, casos_por_data)
    previsoes_da_regua = previsoes_da_regua.rename(columns={"config_id": "entidade"})
    previsoes_da_regua = previsoes_da_regua.dropna(subset=["real", "previsto"])

    previsoes_completas = pd.concat([previsoes_finais, previsoes_da_regua], ignore_index=True)
    previsoes_completas.to_csv(
        PASTA_DE_SAIDAS / "previsoes_vencedoras_e_controles.csv", index=False
    )

    # ------------------------------------------------------------------
    # 6) TRAVA (emenda 25/09/2026).
    # ------------------------------------------------------------------
    previsoes_do_cenario_adotado = previsoes_completas[
        previsoes_completas["entidade"] == NOME_CENARIO_ADOTADO
    ]
    trava_valida = conferir_trava_do_cenario_adotado(previsoes_do_cenario_adotado)
    if not trava_valida:
        print("\n  TRAVA INVALIDA — INVESTIGAR ANTES DE LER O RESTO. Nao forcar.", flush=True)

    # ------------------------------------------------------------------
    # 7) JULGAMENTO EM 2026 + DESCRITIVO 2024-2025 + HOLM.
    # ------------------------------------------------------------------
    julgamento = montar_julgamento_2026(previsoes_completas)
    julgamento.to_csv(PASTA_DE_SAIDAS / "julgamento_2026.csv", index=False)

    descritivo = montar_descritivo_2024_2025(previsoes_completas)
    descritivo.to_csv(PASTA_DE_SAIDAS / "descritivo_2024_2025.csv", index=False)

    bracos_presentes_no_julgamento = [
        nome for nome in BRACOS_JULGADOS if nome in previsoes_completas["entidade"].unique()
    ]
    holm = montar_holm_2026(previsoes_completas, bracos_presentes_no_julgamento)
    holm.to_csv(PASTA_DE_SAIDAS / "holm_2026.csv", index=False)

    gerar_figura_2026(previsoes_completas, julgamento)

    vencedoras = {
        "HB_best": {
            k: v for k, v in vencedora_histgb.items() if k not in ("nota_arredondada",)
        },
        "LGB_best": {
            k: v for k, v in vencedora_lightgbm.items() if k not in ("nota_arredondada",)
        },
        "LGB_linear": {
            "impossivel": lgb_linear_impossivel,
            "vencedora": config_lgb_linear_vencedora,
        },
        "MONO": {
            "impossivel": mono_impossivel,
            "baseada_em": vencedora_geral["config_id"],
            "familia": familia_mono,
            "vetor_monotonico": vetor_monotonico,
            "colunas_do_modelo": COLUNAS_GLOBAL,
        },
        "trava_valida": trava_valida,
    }
    with open(PASTA_DE_SAIDAS / "vencedoras.json", "w", encoding="utf-8") as arquivo:
        json.dump(vencedoras, arquivo, indent=2, default=str)

    duracao_total_minutos = (time.perf_counter() - inicio_geral) / 60
    print(f"\nCONCLUIDO em {duracao_total_minutos:.1f} min.", flush=True)


if __name__ == "__main__":
    main()
