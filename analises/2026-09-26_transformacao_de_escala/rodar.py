"""Transformação de escala do alvo — 26/09/2026.

Pré-declarado em PRE_DECLARACAO.md (leitura obrigatória, é o contrato desta
rodada). Testa se treinar o HistGB do cenário adotado numa escala transformada
do alvo (raiz quadrada ou log1p, em vez de casos brutos) conserta a faixa de
previsão nas semanas de epidemia sem destruir o erro pontual.

Dois braços novos, mais o controle B0 (não re-rodado, lido de
`../2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv`):

    T_raiz    alvo = sqrt(casos), previsão volta por elevar ao quadrado
    T_log     alvo = log1p(casos), previsão volta por expm1
    B0        casos brutos, sem transformação (controle, NÃO re-rodado)

Quantis: 0,05 · 0,10 · 0,25 · 0,50 · 0,75 · 0,90 · 0,95 (o conjunto do WIS),
mais 0,85 (só para a trava e para o MAE, que neste projeto sempre usa o
quantil 0,85 como previsão pontual — é o quantil do próprio cenário adotado,
config/experimentos/cidade_referencia.py). Horizontes 1, 4, 8, 12.
2 braços x 4 horizontes x 8 quantis = 64 células.

⚠️ NÃO altera nada do pipeline (`modelagem_aedes/`) nem o harness (só leitura).
NÃO roda preparar_dados.py, consolidar_sinan nem montar.py. NÃO toca no
datalake da secretaria. NÃO commita.

DESVIOS desta rodada em relação à letra da pré-declaração/brief, investigados
e reportados aqui (nunca corrigidos em silêncio — ver também README.md):

  1. O brief pede para conferir a trava do B0 "direto nas previsões salvas"
     de `previsoes_quantis.csv`. Esse arquivo só tem os 7 quantis do WIS
     (0,05 a 0,95) — o quantil 0,85 do B0 foi treinado na rodada de 26/09
     (`2026-09-26_wis_na_tabela_restaurada/rodar.py`), usado só para a
     própria trava daquela rodada, e NUNCA foi persistido em CSV (o script
     de origem descarta explicitamente esse quantil antes de salvar). Não dá
     para reler o que não foi salvo, e re-treinar o B0 é proibido aqui. A
     trava abaixo usa os números JÁ CERTIFICADOS no log daquela rodada
     (`2026-09-26_wis_na_tabela_restaurada/execucao.log`, linhas 67-71):
     MAE h=1 97,99 · h=4 219,67 · h=8 272,63 · h=12 278,82 — dentro da
     tolerância de 0,2 contra o painel publicado (98,0/219,7/272,6/278,7).
     Consequência: o MAE do B0 (usado no critério e no "total") vem desses
     números certificados, não de uma releitura de CSV nesta rodada.

  2. Sem o quantil 0,85 do B0 salvo, o MAE do B0 POR FAIXA (calmaria, subida,
     Mobilização, Alerta) não pode ser calculado sem re-rodar o B0. Reportado
     como indisponível no README, em vez de aproximar com outro quantil (o
     que trocaria a convenção de MAE do projeto em silêncio).

  3. A cobertura POR FAIXA (ic50/ic90) usa a MESMA metodologia de
     `../2026-09-26_calibracao_por_faixa/diagnosticar.py`: os 7 quantis do
     WIS, TODA a série de origens de `previsoes_quantis.csv` (2020-03-22 a
     2026-02-01), agrupando os 4 horizontes juntos por faixa — é assim que
     aquele script reproduz exatamente os números-âncora da pré-declaração
     (163 semanas, cobertura 90% = 17,8%, cobertura 50% = 8,0%, na faixa
     Alerta). Confirmado batendo exatamente com esses três números antes de
     aplicar o mesmo método aos braços novos.

  4. O MAE "no total" e o MAE do critério (h=12) usam a janela
     2024-01-01 a 2026-02-01 — a MESMA janela da trava e do painel publicado
     (harness.INICIO_DA_AVALIACAO até o fim natural dos dados). É uma janela
     DIFERENTE da usada na cobertura por faixa (item 3, série completa desde
     2020). As duas âncoras dadas no brief (278,8 de MAE e 17,8% de
     cobertura) vêm de janelas diferentes nos arquivos de origem — reproduzo
     cada uma na janela em que foi originalmente medida, não invento uma
     janela única que não bateria com nenhuma das duas.
"""

from __future__ import annotations

import concurrent.futures
import dataclasses
import os
import pathlib
import re
import sys
import time
from typing import Callable

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DA_BATERIA_NOTURNA = PASTA_DESTE_ARQUIVO.parent / "2026-09-23_bateria_noturna"
PASTA_DO_PIPELINE = PASTA_DESTE_ARQUIVO.parent.parent / "modelagem_aedes"

for pasta_a_incluir in (PASTA_DA_BATERIA_NOTURNA, PASTA_DO_PIPELINE):
    if str(pasta_a_incluir) not in sys.path:
        sys.path.insert(0, str(pasta_a_incluir))

import harness  # noqa: E402  (bateria de 23/09/2026 — só lido, nunca alterado)

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

PASTA_WIS_CERTIFICADA = PASTA_DESTE_ARQUIVO.parent / "2026-09-26_wis_na_tabela_restaurada"
CAMINHO_PREVISOES_B0 = PASTA_WIS_CERTIFICADA / "saidas" / "previsoes_quantis.csv"
CAMINHO_LOG_B0 = PASTA_WIS_CERTIFICADA / "execucao.log"

PASTA_CALIBRACAO_POR_FAIXA = PASTA_DESTE_ARQUIVO.parent / "2026-09-26_calibracao_por_faixa"
CAMINHO_COBERTURA_B0_POR_FAIXA = PASTA_CALIBRACAO_POR_FAIXA / "saidas" / "cobertura_por_faixa.csv"

# --- Configuração pré-declarada ---------------------------------------------

QUANTIS_WIS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
QUANTIL_MAE = 0.85  # quantil de referência do cenário adotado (ponto previsto)
TODOS_OS_QUANTIS = QUANTIS_WIS + (QUANTIL_MAE,)
HORIZONTES = (1, 4, 8, 12)
MAX_PROCESSOS_PARALELOS = 8

# Hiperparâmetros do "cenário adotado" (seção 3 da pré-declaração): HistGB,
# 250 iterações, taxa 0,05, 15 folhas, folha mínima 5. O quantil é inserido
# por combinação, em `treinar_uma_celula`.
PARAMETROS_CENARIO_ADOTADO = {
    "max_iter": 250,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 5,
    "random_state": 42,
    "loss": "quantile",
}

# Janela de avaliação do MAE — a mesma da trava e do painel publicado
# (harness.INICIO_DA_AVALIACAO até o fim natural dos dados). Ver desvio 4.
INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")
FIM_DA_AVALIACAO = pd.Timestamp("2026-02-01")

# Trava (seção 7 da pré-declaração) — ver desvio 1: os números do B0 vêm do
# log já certificado de 26/09/2026, não de um CSV que não guarda o quantil
# 0,85.
B0_MAE_CERTIFICADO = {1: 97.99, 4: 219.67, 8: 272.63, 12: 278.82}
PAINEL_PUBLICADO = harness.PAINEL_PUBLICADO  # {h: {"mae": ..., "r2": ...}}
TOLERANCIA_DA_TRAVA = 0.2

# Critério de decisão (seção 5 da pré-declaração).
B0_MAE_H12 = 278.8
TETO_MAE_H12 = 306.7  # +10% sobre 278,8
B0_COBERTURA_IC90_ALERTA = 0.178
COBERTURA_IC90_ALERTA_MINIMA = 0.50

# Faixas operacionais — IDÊNTICAS a
# ../2026-09-26_calibracao_por_faixa/diagnosticar.py, para os números serem
# comparáveis (ver desvio 3).
LIMITE_CALMARIA = 20
LIMITE_MOBILIZACAO = 140
LIMITE_ALERTA = 421
NOME_CALMARIA = "1. calmaria (0-20)"
NOME_SUBIDA = "2. subida (21-140)"
NOME_MOBILIZACAO = "3. Mobilizacao (141-421)"
NOME_ALERTA = "4. Alerta ou mais (>421)"

QUANTIL_INFERIOR_IC50 = 0.25
QUANTIL_SUPERIOR_IC50 = 0.75
QUANTIL_INFERIOR_IC90 = 0.05
QUANTIL_SUPERIOR_IC90 = 0.95


def classificar_faixa_de_casos(casos_reais: float) -> str:
    """Diz em que faixa operacional uma semana caiu, pelo número real de casos.

    Réplica exata de `diagnosticar.classificar_faixa_de_casos` (26/09/2026),
    para os números desta rodada serem comparáveis ao B0.

    Args:
        casos_reais: Casos confirmados observados naquela semana.

    Returns:
        O nome da faixa, prefixado por número para ordenar nas tabelas.
    """
    if casos_reais <= LIMITE_CALMARIA:
        return NOME_CALMARIA
    if casos_reais <= LIMITE_MOBILIZACAO:
        return NOME_SUBIDA
    if casos_reais <= LIMITE_ALERTA:
        return NOME_MOBILIZACAO
    return NOME_ALERTA


# --- Formulação do alvo: como o alvo é preparado e a previsão revertida ----


@dataclasses.dataclass(frozen=True)
class FormulacaoDoAlvo:
    """Como um braço transforma o alvo de treino e reverte a previsão.

    Attributes:
        nome: Identificador do braço nas saídas.
        preparar_alvo: Recebe a série de casos do treino (`y_h`) e devolve a
            série transformada que o modelo vê como alvo.
        inverter_escalar: Reverte uma única previsão transformada para casos.
            Usado no quantil 0,85 (sem reordenamento — origem de um quantil
            só).
        inverter_vetor: Reverte um array de previsões transformadas para
            casos, já rearranjadas isotonicamente. Usado no conjunto de 7
            quantis do WIS.
    """

    nome: str
    preparar_alvo: Callable[[pd.Series], pd.Series]
    inverter_escalar: Callable[[float], float]
    inverter_vetor: Callable[[np.ndarray], np.ndarray]


def preparar_alvo_raiz(casos_de_treino: pd.Series) -> pd.Series:
    """T_raiz: o modelo treina em sqrt(casos)."""
    return np.sqrt(casos_de_treino)


def inverter_previsao_raiz_escalar(previsao_transformada: float) -> float:
    """T_raiz: eleva ao quadrado. Previsão negativa na raiz vira 0 antes.

    A raiz de uma contagem nunca é negativa; um modelo treinado em sqrt(casos)
    que extrapola abaixo de 0 está fora do domínio da transformação. Sem esse
    corte, elevar um número negativo ao quadrado devolveria um valor positivo
    e quebraria a ordem entre quantis (ver `inverter_previsao_raiz_vetor`).
    """
    raiz_nao_negativa = max(0.0, previsao_transformada)
    return raiz_nao_negativa**2


def inverter_previsao_raiz_vetor(previsoes_transformadas: np.ndarray) -> np.ndarray:
    """T_raiz, vetorizado: mesmo corte em 0, depois eleva ao quadrado.

    O corte em 0 e o quadrado em [0, +inf) são as duas monótonas não
    decrescentes; aplicadas a uma sequência já ordenada (rearranjo isotônico
    em `reordenar_e_inverter_wis`), o resultado continua ordenado.
    """
    raizes_nao_negativas = np.clip(previsoes_transformadas, 0.0, None)
    return np.square(raizes_nao_negativas)


def preparar_alvo_log(casos_de_treino: pd.Series) -> pd.Series:
    """T_log: o modelo treina em log1p(casos)."""
    return np.log1p(casos_de_treino)


def inverter_previsao_log_escalar(previsao_transformada: float) -> float:
    """T_log: devolve expm1. Previsão negativa em casos vira 0."""
    previsao_em_casos = float(np.expm1(previsao_transformada))
    return max(0.0, previsao_em_casos)


def inverter_previsao_log_vetor(previsoes_transformadas: np.ndarray) -> np.ndarray:
    """T_log, vetorizado: expm1 seguido do mesmo corte em 0."""
    previsoes_em_casos = np.expm1(previsoes_transformadas)
    return np.clip(previsoes_em_casos, 0.0, None)


FORMULACAO_RAIZ = FormulacaoDoAlvo(
    "T_raiz", preparar_alvo_raiz, inverter_previsao_raiz_escalar, inverter_previsao_raiz_vetor
)
FORMULACAO_LOG = FormulacaoDoAlvo(
    "T_log", preparar_alvo_log, inverter_previsao_log_escalar, inverter_previsao_log_vetor
)
FORMULACOES_POR_NOME: dict[str, FormulacaoDoAlvo] = {
    "T_raiz": FORMULACAO_RAIZ,
    "T_log": FORMULACAO_LOG,
}


# --- Etapa 1: walk-forward customizado, com a formulação do alvo -----------


def rodar_walk_forward_transformado(
    tabela: pd.DataFrame,
    colunas_do_modelo: list[str],
    horizonte: int,
    formulacao: FormulacaoDoAlvo,
    quantil: float,
) -> pd.DataFrame:
    """Espelha harness.rodar_walk_forward, treinando na escala transformada.

    Mesmo corte de treino pela data da RESPOSTA
    (`corte_temporal.selecionar_treino_ja_respondido`), mesmo
    `minimo_semanas_treino`/`passo` do cenário adotado — a única diferença é
    que o alvo de treino passa por `formulacao.preparar_alvo` antes do `fit`,
    e a previsão bruta passa por `formulacao.inverter_escalar` depois do
    `predict`. As colunas de entrada (inclusive `alvo_sin`/`alvo_cos`)
    permanecem brutas: só o alvo é transformado.

    Args:
        tabela: Tabela do braço (mesmo corte de maturidade e features do
            cenário adotado — a transformação não muda features).
        colunas_do_modelo: Colunas de entrada do modelo, sem a sazonalidade.
        horizonte: h, quantas semanas à frente.
        formulacao: Como preparar o alvo e reverter a previsão deste braço.
        quantil: Nível do quantil treinado (0,05 a 0,95, ou 0,85 para o MAE).

    Returns:
        Uma linha por origem avaliada: h, data_alvo, real, previsto_bruto
        (na escala transformada, antes de reverter), previsto (em casos).
    """
    dados_do_horizonte = harness.construir_alvo_horizonte(
        tabela, harness.CIDADE_REFERENCIA.coluna_alvo, horizonte
    )
    features_com_sazonalidade = colunas_do_modelo + ["alvo_sin", "alvo_cos"]

    dados_validos = (
        dados_do_horizonte.dropna(subset=features_com_sazonalidade + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    parametros_do_quantil = dict(PARAMETROS_CENARIO_ADOTADO)
    parametros_do_quantil["quantile"] = quantil

    linhas: list[dict[str, object]] = []
    for indice_do_corte in range(
        harness.CIDADE_REFERENCIA.minimo_semanas_treino,
        len(dados_validos),
        harness.CIDADE_REFERENCIA.passo,
    ):
        teste = dados_validos.iloc[indice_do_corte : indice_do_corte + 1]
        data_do_teste = teste["data"].to_numpy()[0]

        treino = harness.corte_temporal.selecionar_treino_ja_respondido(
            dados_validos, data_do_teste, horizonte
        )

        alvo_de_treino_transformado = formulacao.preparar_alvo(treino["y_h"])

        modelo = HistGradientBoostingRegressor(**parametros_do_quantil)
        modelo.fit(treino[features_com_sazonalidade], alvo_de_treino_transformado)
        previsao_transformada = float(modelo.predict(teste[features_com_sazonalidade])[0])
        previsao_em_casos = formulacao.inverter_escalar(previsao_transformada)

        linhas.append(
            {
                "h": horizonte,
                "data_alvo": pd.Timestamp(data_do_teste) + pd.Timedelta(weeks=horizonte),
                "real": float(teste["y_h"].to_numpy()[0]),
                "previsto_transformado": previsao_transformada,
                "previsto": previsao_em_casos,
            }
        )

    return pd.DataFrame(linhas)


def treinar_uma_celula(nome_do_braco: str, horizonte: int, quantil: float) -> pd.DataFrame:
    """Treina uma das 64 células (braço, horizonte, quantil) num processo isolado.

    Recarrega a tabela e reconstrói as features do cenário adotado dentro do
    processo (~1-2s) em vez de serializar entre processos — mais simples e
    mais barato, mesmo padrão de `2026-09-26_wis_na_tabela_restaurada/rodar.py`.

    Args:
        nome_do_braco: "T_raiz" ou "T_log".
        horizonte: 1, 4, 8 ou 12.
        quantil: Um dos 8 quantis (7 do WIS + 0,85 do MAE).

    Returns:
        As previsões da célula, com as colunas `braco` e `quantil` marcadas.
    """
    formulacao = FORMULACOES_POR_NOME[nome_do_braco]

    tabela_bruta = harness.carregar_tabela_bruta()
    braco_de_referencia = harness.Braco("referencia")
    tabela, colunas_do_modelo, _ = harness.montar_features_do_braco(
        tabela_bruta, braco_de_referencia
    )

    previsoes = rodar_walk_forward_transformado(
        tabela, colunas_do_modelo, horizonte, formulacao, quantil
    )
    previsoes["braco"] = nome_do_braco
    previsoes["quantil"] = quantil
    return previsoes


def treinar_todas_as_celulas() -> pd.DataFrame:
    """Dispara as 64 combinações (2 braços x 4 horizontes x 8 quantis).

    Returns:
        Todas as previsões de todas as combinações, empilhadas.
    """
    combinacoes_pendentes = []
    for nome_do_braco in FORMULACOES_POR_NOME:
        for horizonte in HORIZONTES:
            for quantil in TODOS_OS_QUANTIS:
                combinacoes_pendentes.append((nome_do_braco, horizonte, quantil))

    print(
        f"Disparando {len(combinacoes_pendentes)} combinações "
        f"(até {MAX_PROCESSOS_PARALELOS} processos em paralelo)...",
        flush=True,
    )

    previsoes_de_todas = []
    inicio_geral = time.perf_counter()

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=MAX_PROCESSOS_PARALELOS
    ) as executor:
        tarefa_por_combinacao = {}
        for nome_do_braco, horizonte, quantil in combinacoes_pendentes:
            tarefa = executor.submit(treinar_uma_celula, nome_do_braco, horizonte, quantil)
            tarefa_por_combinacao[tarefa] = (nome_do_braco, horizonte, quantil)

        concluidas = 0
        for tarefa in concurrent.futures.as_completed(tarefa_por_combinacao):
            nome_do_braco, horizonte, quantil = tarefa_por_combinacao[tarefa]
            previsoes = tarefa.result()
            previsoes_de_todas.append(previsoes)
            concluidas += 1
            print(
                f"  [{concluidas:2d}/{len(combinacoes_pendentes)}] "
                f"{nome_do_braco:>7}  h={horizonte:2d}  q={quantil:.2f}  "
                f"{len(previsoes):3d} semanas  "
                f"({time.perf_counter() - inicio_geral:6.1f}s desde o início)",
                flush=True,
            )

    print(
        f"Treino completo em {(time.perf_counter() - inicio_geral) / 60:.1f} min.",
        flush=True,
    )
    return pd.concat(previsoes_de_todas, ignore_index=True)


# --- Etapa 2: trava, usando a evidência já certificada ----------------------


def conferir_trava() -> bool:
    """Confere o B0 (q0,85) contra o painel publicado, sem re-rodar o B0.

    Ver desvio 1 no cabeçalho do arquivo: os números do B0 vêm do log já
    certificado de `2026-09-26_wis_na_tabela_restaurada/execucao.log`,
    porque o quantil 0,85 nunca foi persistido em CSV. Este script também
    confirma que esse log existe e contém as linhas citadas, para não
    depender só de um número copiado à mão.

    Returns:
        True se os 4 horizontes baterem dentro da tolerância E o log citado
        contiver as mesmas linhas.
    """
    print("\nTRAVA — B0 (q0,85), evidência do log já certificado (ver desvio 1)")
    print(f"  janela: {INICIO_DA_AVALIACAO.date()} a {FIM_DA_AVALIACAO.date()}")

    tudo_bate = True
    for horizonte in HORIZONTES:
        mae_certificado = B0_MAE_CERTIFICADO[horizonte]
        mae_esperado = PAINEL_PUBLICADO[horizonte]["mae"]
        bate = abs(mae_certificado - mae_esperado) < TOLERANCIA_DA_TRAVA
        tudo_bate = tudo_bate and bate
        marca = "ok" if bate else "<<< DIVERGE"
        print(
            f"    h={horizonte:2d}  MAE certificado {mae_certificado:7.2f}  "
            f"(painel {mae_esperado:6.1f})  {marca}"
        )

    log_confirmado = _confirmar_log_de_origem()
    print(f"  log de origem ({CAMINHO_LOG_B0.name}) confere: {'sim' if log_confirmado else 'NAO'}")

    veredito = tudo_bate and log_confirmado
    print(f"  veredito: {'VALIDA' if veredito else 'INVALIDA'}")
    return veredito


def _confirmar_log_de_origem() -> bool:
    """Confirma que o log citado no desvio 1 realmente contém esses números.

    Não recalcula nada: só evita que a trava dependa de um número copiado à
    mão sem checagem contra o arquivo de onde ele veio.

    Returns:
        True se o log existir e contiver as 4 linhas de MAE citadas.
    """
    if not CAMINHO_LOG_B0.exists():
        return False

    texto_do_log = CAMINHO_LOG_B0.read_text(encoding="utf-8")
    padrao_da_linha = re.compile(
        r"h=\s*(\d+)\s+MAE\s+([\d.]+)\s+\(esperado ([\d.]+)\)"
    )

    maes_encontrados: dict[int, float] = {}
    for casamento in padrao_da_linha.finditer(texto_do_log):
        horizonte_do_log = int(casamento.group(1))
        mae_do_log = float(casamento.group(2))
        maes_encontrados[horizonte_do_log] = mae_do_log

    for horizonte, mae_esperado_aqui in B0_MAE_CERTIFICADO.items():
        mae_no_log = maes_encontrados.get(horizonte)
        if mae_no_log is None or abs(mae_no_log - mae_esperado_aqui) > 1e-6:
            return False

    return True


# --- Etapa 3: rearranjo isotônico dos 7 quantis do WIS, na escala transformada


def reordenar_e_inverter_wis(previsoes_wis: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rearranja os 7 quantis do WIS na escala transformada e reverte para casos.

    O rearranjo acontece ANTES da volta, na escala em que o modelo foi
    treinado — mesmo procedimento de
    `2026-09-26_wis_na_tabela_restaurada/rodar.py::ordenar_quantis_cruzados`,
    usado no B0. Como a volta (quadrado com corte em 0, ou expm1 com corte em
    0) é monótona não decrescente, uma sequência já ordenada continua
    ordenada depois de revertida — por isso o número de cruzamentos que
    sobra em casos, depois deste passo, tem que ser exatamente 0.

    Args:
        previsoes_wis: Só as linhas dos 7 quantis do WIS (sem o 0,85).

    Returns:
        As previsões com `previsto` final em casos, e uma tabela de
        diagnóstico de cruzamento por (braco, h).
    """
    ordenado = previsoes_wis.sort_values(
        ["braco", "h", "data_alvo", "quantil"]
    ).reset_index(drop=True)

    valores_transformados_reordenados = np.empty(len(ordenado), dtype=float)
    houve_cruzamento_bruto = np.zeros(len(ordenado), dtype=bool)

    origens = ordenado.groupby(["braco", "h", "data_alvo"], sort=False).indices

    total_de_origens = 0
    origens_com_cruzamento = 0
    for posicoes_da_origem in origens.values():
        total_de_origens += 1
        posicoes_em_ordem = np.sort(np.asarray(posicoes_da_origem))
        valores_brutos = ordenado.loc[posicoes_em_ordem, "previsto_transformado"].to_numpy()

        ja_estava_em_ordem = bool(np.all(np.diff(valores_brutos) >= 0))
        valores_transformados_reordenados[posicoes_em_ordem] = np.sort(valores_brutos)

        if not ja_estava_em_ordem:
            houve_cruzamento_bruto[posicoes_em_ordem] = True
            origens_com_cruzamento += 1

    ordenado["previsto_transformado_reordenado"] = valores_transformados_reordenados
    ordenado["cruzamento_bruto_corrigido"] = houve_cruzamento_bruto

    mascara_raiz = (ordenado["braco"] == "T_raiz").to_numpy()
    previsto_final = np.where(
        mascara_raiz,
        inverter_previsao_raiz_vetor(ordenado["previsto_transformado_reordenado"].to_numpy()),
        inverter_previsao_log_vetor(ordenado["previsto_transformado_reordenado"].to_numpy()),
    )
    ordenado["previsto"] = previsto_final

    cruzamentos_restantes = contar_cruzamentos_restantes(ordenado)

    resumo_por_braco_h = []
    for (braco, horizonte), dados_do_grupo in ordenado.groupby(["braco", "h"]):
        origens_do_grupo = dados_do_grupo.groupby("data_alvo")["cruzamento_bruto_corrigido"].any()
        resumo_por_braco_h.append(
            {
                "braco": braco,
                "h": horizonte,
                "origens": len(origens_do_grupo),
                "origens_com_cruzamento_bruto": int(origens_do_grupo.sum()),
                "taxa_cruzamento_bruto": float(origens_do_grupo.mean()),
                "cruzamentos_restantes_apos_volta": cruzamentos_restantes.get((braco, horizonte), 0),
            }
        )

    print(
        f"\nCruzamentos brutos (escala transformada, antes do rearranjo): "
        f"{origens_com_cruzamento} de {total_de_origens} origens "
        f"({100.0 * origens_com_cruzamento / total_de_origens:.1f}%)."
    )
    total_restantes = sum(cruzamentos_restantes.values())
    print(
        f"Cruzamentos restantes em CASOS, após rearranjo + volta monótona: "
        f"{total_restantes} (esperado: 0)."
    )

    return ordenado, pd.DataFrame(resumo_por_braco_h)


def contar_cruzamentos_restantes(previsoes_reordenadas: pd.DataFrame) -> dict[tuple[str, int], int]:
    """Conta, por (braco, h), quantas origens ficaram fora de ordem em CASOS.

    Serve de prova de que a volta da transformação preservou a ordem dos
    quantis (seção 3 da pré-declaração). Uma origem "fora de ordem" é aquela
    em que `previsto` (em casos) não é monótono não decrescente ao longo dos
    7 níveis de quantil.

    Args:
        previsoes_reordenadas: Saída de `reordenar_e_inverter_wis`, já com a
            coluna `previsto` em casos.

    Returns:
        Contagem de origens com cruzamento em casos, por (braco, h).
    """
    contagem: dict[tuple[str, int], int] = {}
    origens = previsoes_reordenadas.sort_values(
        ["braco", "h", "data_alvo", "quantil"]
    ).groupby(["braco", "h", "data_alvo"], sort=False)

    for (braco, horizonte, _data_alvo), dados_da_origem in origens:
        valores_em_casos = dados_da_origem["previsto"].to_numpy()
        se_esta_em_ordem = bool(np.all(np.diff(valores_em_casos) >= 0))
        if not se_esta_em_ordem:
            chave = (braco, horizonte)
            contagem[chave] = contagem.get(chave, 0) + 1

    return contagem


# --- Etapa 4: MAE (quantil 0,85), no total e por faixa -----------------------


def calcular_mae_por_h(previsoes_q085: pd.DataFrame) -> pd.DataFrame:
    """MAE por (braco, h), na janela de avaliação (ver desvio 4).

    Args:
        previsoes_q085: Previsões do quantil 0,85, já em casos.

    Returns:
        Uma linha por (braco, h), com o MAE e o número de semanas.
    """
    na_janela = previsoes_q085[
        (previsoes_q085["data_alvo"] >= INICIO_DA_AVALIACAO)
        & (previsoes_q085["data_alvo"] <= FIM_DA_AVALIACAO)
    ]

    linhas = []
    for (braco, horizonte), dados_do_grupo in na_janela.groupby(["braco", "h"]):
        erro_absoluto = (dados_do_grupo["real"] - dados_do_grupo["previsto"]).abs()
        linhas.append(
            {
                "braco": braco,
                "h": horizonte,
                "mae": float(erro_absoluto.mean()),
                "n_semanas": len(dados_do_grupo),
            }
        )
    return pd.DataFrame(linhas)


def calcular_mae_por_faixa(previsoes_q085: pd.DataFrame) -> pd.DataFrame:
    """MAE por (braco, h, faixa), na mesma janela de avaliação do MAE total.

    ⚠️ O B0 não entra aqui: seu quantil 0,85 não foi salvo (desvio 2). Só
    T_raiz e T_log aparecem nesta tabela.

    Args:
        previsoes_q085: Previsões do quantil 0,85 dos braços novos, em casos.

    Returns:
        Uma linha por (braco, h, faixa).
    """
    na_janela = previsoes_q085[
        (previsoes_q085["data_alvo"] >= INICIO_DA_AVALIACAO)
        & (previsoes_q085["data_alvo"] <= FIM_DA_AVALIACAO)
    ].copy()
    na_janela["faixa"] = na_janela["real"].apply(classificar_faixa_de_casos)

    linhas = []
    for (braco, horizonte, faixa), dados_do_grupo in na_janela.groupby(["braco", "h", "faixa"]):
        erro_absoluto = (dados_do_grupo["real"] - dados_do_grupo["previsto"]).abs()
        linhas.append(
            {
                "braco": braco,
                "h": horizonte,
                "faixa": faixa,
                "mae": float(erro_absoluto.mean()),
                "n_semanas": len(dados_do_grupo),
            }
        )
    return pd.DataFrame(linhas)


# --- Etapa 5: cobertura por faixa, mesma metodologia do B0 -------------------


def calcular_cobertura_por_faixa(previsoes_wis_finais: pd.DataFrame) -> pd.DataFrame:
    """Cobertura ic50/ic90 por (braco, faixa), série completa, h agrupados.

    Mesma metodologia de `diagnosticar.medir_cobertura_por_faixa` (ver
    desvio 3): usa TODA a série de origens (não só a janela de avaliação) e
    agrupa os 4 horizontes juntos dentro de cada faixa, porque é assim que
    os números-âncora do B0 (163 semanas, 17,8%, 8,0%) foram calculados.

    Args:
        previsoes_wis_finais: As previsões dos 7 quantis do WIS, já revertidas
            para casos (`reordenar_e_inverter_wis`).

    Returns:
        Uma linha por (braco, faixa), com semanas, cobertura_ic50 e
        cobertura_ic90.
    """
    com_faixa = previsoes_wis_finais.copy()
    com_faixa["faixa"] = com_faixa["real"].apply(classificar_faixa_de_casos)

    colunas_da_linha = ["braco", "h", "data_alvo", "faixa", "real"]
    em_formato_largo = com_faixa.pivot_table(
        index=colunas_da_linha, columns="quantil", values="previsto"
    ).reset_index()

    dentro_do_ic50 = (
        em_formato_largo["real"] >= em_formato_largo[QUANTIL_INFERIOR_IC50]
    ) & (em_formato_largo["real"] <= em_formato_largo[QUANTIL_SUPERIOR_IC50])
    dentro_do_ic90 = (
        em_formato_largo["real"] >= em_formato_largo[QUANTIL_INFERIOR_IC90]
    ) & (em_formato_largo["real"] <= em_formato_largo[QUANTIL_SUPERIOR_IC90])

    em_formato_largo["dentro_do_ic50"] = dentro_do_ic50
    em_formato_largo["dentro_do_ic90"] = dentro_do_ic90

    return em_formato_largo.groupby(["braco", "faixa"]).agg(
        semanas=("real", "size"),
        cobertura_ic50=("dentro_do_ic50", "mean"),
        cobertura_ic90=("dentro_do_ic90", "mean"),
    ).reset_index()


def carregar_cobertura_b0_por_faixa() -> pd.DataFrame:
    """Lê a cobertura por faixa já certificada do B0 (cenário adotado).

    Returns:
        A tabela de `../2026-09-26_calibracao_por_faixa/saidas/cobertura_por_faixa.csv`,
        filtrada ao modelo `cenario_adotado` (o B0 desta pré-declaração).
    """
    cobertura = pd.read_csv(CAMINHO_COBERTURA_B0_POR_FAIXA)
    return cobertura[cobertura["modelo"] == "cenario_adotado"].copy()


# --- Etapa 6: WIS por h e por faixa ------------------------------------------


INTERVALOS_DO_WIS = (
    {"alpha": 0.50, "quantil_inferior": 0.25, "quantil_superior": 0.75},
    {"alpha": 0.20, "quantil_inferior": 0.10, "quantil_superior": 0.90},
    {"alpha": 0.10, "quantil_inferior": 0.05, "quantil_superior": 0.95},
)


def calcular_intervalo_score(
    real: float, limite_inferior: float, limite_superior: float, alpha: float
) -> float:
    """O IS_alpha de um único intervalo (Bracher et al. 2021)."""
    largura_do_intervalo = limite_superior - limite_inferior

    penalidade_por_baixo = 0.0
    if real < limite_inferior:
        penalidade_por_baixo = (2.0 / alpha) * (limite_inferior - real)

    penalidade_por_cima = 0.0
    if real > limite_superior:
        penalidade_por_cima = (2.0 / alpha) * (real - limite_superior)

    return largura_do_intervalo + penalidade_por_baixo + penalidade_por_cima


def calcular_wis(real: float, previsto_por_quantil: dict[float, float]) -> float:
    """O Weighted Interval Score de uma origem (mediana + 3 intervalos)."""
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


def calcular_wis_por_h_e_faixa(previsoes_wis_finais: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """WIS médio por (braco, h) e por (braco, faixa), série completa.

    Args:
        previsoes_wis_finais: As previsões dos 7 quantis do WIS, em casos.

    Returns:
        Duas tabelas: WIS por (braco, h), e WIS por (braco, faixa) — faixa
        na mesma classificação e mesmo agrupamento de h da cobertura.
    """
    com_faixa = previsoes_wis_finais.copy()
    com_faixa["faixa"] = com_faixa["real"].apply(classificar_faixa_de_casos)

    linhas_de_origem = []
    agrupado = com_faixa.groupby(["braco", "h", "data_alvo", "faixa"], sort=False)
    for (braco, horizonte, _data_alvo, faixa), dados_da_origem in agrupado:
        previsto_por_quantil = dict(zip(dados_da_origem["quantil"], dados_da_origem["previsto"]))
        if len(previsto_por_quantil) != len(QUANTIS_WIS):
            continue
        real = float(dados_da_origem["real"].to_numpy()[0])
        linhas_de_origem.append(
            {
                "braco": braco,
                "h": horizonte,
                "faixa": faixa,
                "wis": calcular_wis(real, previsto_por_quantil),
            }
        )

    origens = pd.DataFrame(linhas_de_origem)
    wis_por_h = origens.groupby(["braco", "h"]).agg(
        wis_medio=("wis", "mean"), n=("wis", "size")
    ).reset_index()
    wis_por_faixa = origens.groupby(["braco", "faixa"]).agg(
        wis_medio=("wis", "mean"), n=("wis", "size")
    ).reset_index()
    return wis_por_h, wis_por_faixa


# --- Etapa 7: captura do pico -------------------------------------------------


def avaliar_captura_do_pico(previsoes_wis_finais: pd.DataFrame) -> pd.DataFrame:
    """Se o intervalo de 90% cobriu a semana de PICO de casos, por (braco, h).

    "Pico" é a origem com o maior valor real dentro daquele (braco, h) — a
    semana mais extrema que a rodada tenta cobrir.

    Args:
        previsoes_wis_finais: Previsões dos 7 quantis do WIS, em casos.

    Returns:
        Uma linha por (braco, h): valor do pico, limites do intervalo de
        90% previstos para aquela semana e se cobriu.
    """
    linhas = []
    for (braco, horizonte), dados_do_grupo in previsoes_wis_finais.groupby(["braco", "h"]):
        indice_do_pico = dados_do_grupo["real"].idxmax()
        data_alvo_do_pico = dados_do_grupo.loc[indice_do_pico, "data_alvo"]
        casos_no_pico = float(dados_do_grupo.loc[indice_do_pico, "real"])

        origem_do_pico = dados_do_grupo[dados_do_grupo["data_alvo"] == data_alvo_do_pico]
        previsto_por_quantil = dict(zip(origem_do_pico["quantil"], origem_do_pico["previsto"]))

        limite_inferior_90 = previsto_por_quantil[QUANTIL_INFERIOR_IC90]
        limite_superior_90 = previsto_por_quantil[QUANTIL_SUPERIOR_IC90]
        cobriu = bool(limite_inferior_90 <= casos_no_pico <= limite_superior_90)

        linhas.append(
            {
                "braco": braco,
                "h": horizonte,
                "data_alvo_do_pico": data_alvo_do_pico,
                "casos_no_pico": casos_no_pico,
                "ic90_inferior": limite_inferior_90,
                "ic90_superior": limite_superior_90,
                "cobriu_o_pico": cobriu,
            }
        )
    return pd.DataFrame(linhas)


# --- Etapa 8: veredito, critério duplo da seção 5 ----------------------------


def montar_veredito(mae_por_h: pd.DataFrame, cobertura_por_faixa: pd.DataFrame) -> pd.DataFrame:
    """Aplica o critério duplo da seção 5 aos dois braços.

    Um braço passa só se as DUAS condições valerem:
      1. cobertura ic90 na faixa Alerta >= 50% (B0 = 17,8%);
      2. MAE em h=12 <= 306,7 (B0 = 278,8 + 10%).

    Se só (1) valer, o veredito é reportado como NEGATIVO — nunca como
    parcial ou "quase lá" (proibido pela seção 5).

    Args:
        mae_por_h: Saída de `calcular_mae_por_h`.
        cobertura_por_faixa: Saída de `calcular_cobertura_por_faixa`.

    Returns:
        Uma linha por braço, com os dois critérios e o veredito final.
    """
    linhas = []
    for braco in FORMULACOES_POR_NOME:
        mae_h12 = mae_por_h[(mae_por_h["braco"] == braco) & (mae_por_h["h"] == 12)]["mae"].iloc[0]
        cobertura_alerta = cobertura_por_faixa[
            (cobertura_por_faixa["braco"] == braco) & (cobertura_por_faixa["faixa"] == NOME_ALERTA)
        ]["cobertura_ic90"].iloc[0]

        criterio_1_cobertura = cobertura_alerta >= COBERTURA_IC90_ALERTA_MINIMA
        criterio_2_mae = mae_h12 <= TETO_MAE_H12
        passou = criterio_1_cobertura and criterio_2_mae

        linhas.append(
            {
                "braco": braco,
                "cobertura_ic90_alerta": cobertura_alerta,
                "criterio_1_cobertura_ok": criterio_1_cobertura,
                "mae_h12": mae_h12,
                "criterio_2_mae_ok": criterio_2_mae,
                "veredito": "POSITIVO" if passou else "NEGATIVO",
            }
        )
    return pd.DataFrame(linhas)


# --- Orquestração -------------------------------------------------------------


def main() -> None:
    """Roda a rodada inteira: treino, trava, métricas, veredito."""
    print("=" * 78)
    print("TRANSFORMAÇÃO DE ESCALA — T_raiz e T_log, 26/09/2026")
    print("=" * 78, flush=True)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)

    if not conferir_trava():
        print(
            "\nBLOCO INVÁLIDO: a trava não bateu. Não sigo para o treino "
            "com uma referência que não reproduz o painel.",
            flush=True,
        )
        return

    previsoes_brutas = treinar_todas_as_celulas()
    previsoes_brutas.to_csv(PASTA_DE_SAIDAS / "previsoes_completas.csv", index=False)
    print(f"\nGravado: {PASTA_DE_SAIDAS / 'previsoes_completas.csv'}")

    previsoes_q085 = previsoes_brutas[previsoes_brutas["quantil"] == QUANTIL_MAE].copy()
    previsoes_wis = previsoes_brutas[previsoes_brutas["quantil"].isin(QUANTIS_WIS)].copy()

    previsoes_wis_finais, diagnostico_cruzamento = reordenar_e_inverter_wis(previsoes_wis)
    diagnostico_cruzamento.to_csv(PASTA_DE_SAIDAS / "diagnostico_cruzamento.csv", index=False)
    print(f"Gravado: {PASTA_DE_SAIDAS / 'diagnostico_cruzamento.csv'}")

    colunas_previsoes_finais = [
        "braco", "h", "data_alvo", "quantil", "real",
        "previsto_transformado", "previsto_transformado_reordenado",
        "cruzamento_bruto_corrigido", "previsto",
    ]
    previsoes_wis_finais[colunas_previsoes_finais].to_csv(
        PASTA_DE_SAIDAS / "previsoes_quantis_finais.csv", index=False
    )
    print(f"Gravado: {PASTA_DE_SAIDAS / 'previsoes_quantis_finais.csv'}")

    mae_por_h = calcular_mae_por_h(previsoes_q085)
    mae_por_faixa = calcular_mae_por_faixa(previsoes_q085)
    mae_por_h.to_csv(PASTA_DE_SAIDAS / "mae_por_h.csv", index=False)
    mae_por_faixa.to_csv(PASTA_DE_SAIDAS / "mae_por_faixa.csv", index=False)
    print(f"Gravado: {PASTA_DE_SAIDAS / 'mae_por_h.csv'} e mae_por_faixa.csv")
    print("\nMAE por (braço, h), janela 2024-01-01 a 2026-02-01:")
    print(mae_por_h.to_string(index=False))

    cobertura_por_faixa = calcular_cobertura_por_faixa(previsoes_wis_finais)
    cobertura_b0 = carregar_cobertura_b0_por_faixa()
    cobertura_b0_renomeada = cobertura_b0.rename(columns={"modelo": "braco"})
    cobertura_b0_renomeada["braco"] = "B0"
    cobertura_combinada = pd.concat(
        [cobertura_por_faixa, cobertura_b0_renomeada[["braco", "faixa", "semanas", "cobertura_ic50", "cobertura_ic90"]]],
        ignore_index=True,
    )
    cobertura_combinada.to_csv(PASTA_DE_SAIDAS / "cobertura_por_faixa.csv", index=False)
    print(f"\nGravado: {PASTA_DE_SAIDAS / 'cobertura_por_faixa.csv'}")
    print("\nCobertura por (braço, faixa), série completa, h agrupados:")
    print(cobertura_combinada.to_string(index=False))

    wis_por_h, wis_por_faixa = calcular_wis_por_h_e_faixa(previsoes_wis_finais)
    wis_por_h.to_csv(PASTA_DE_SAIDAS / "wis_por_h.csv", index=False)
    wis_por_faixa.to_csv(PASTA_DE_SAIDAS / "wis_por_faixa.csv", index=False)
    print(f"Gravado: {PASTA_DE_SAIDAS / 'wis_por_h.csv'} e wis_por_faixa.csv")

    captura_do_pico = avaliar_captura_do_pico(previsoes_wis_finais)
    captura_do_pico.to_csv(PASTA_DE_SAIDAS / "captura_do_pico.csv", index=False)
    print(f"Gravado: {PASTA_DE_SAIDAS / 'captura_do_pico.csv'}")
    print("\nCaptura do pico (IC 90%), por (braço, h):")
    print(captura_do_pico.to_string(index=False))

    veredito = montar_veredito(mae_por_h, cobertura_por_faixa)
    veredito.to_csv(PASTA_DE_SAIDAS / "veredito.csv", index=False)
    print(f"\nGravado: {PASTA_DE_SAIDAS / 'veredito.csv'}")
    print("\nVEREDITO — critério duplo da seção 5:")
    print(veredito.to_string(index=False))

    print("\nRODADA CONCLUÍDA.", flush=True)


if __name__ == "__main__":
    main()
