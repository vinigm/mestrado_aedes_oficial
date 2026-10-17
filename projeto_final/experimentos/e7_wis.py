"""E7: WIS, a metrica secundaria (pre-declaracao de 12/10/2026, secao 5).

Um HistGB por quantil (0,05 / 0,10 / 0,25 / 0,50 / 0,75 / 0,90 / 0,95), nas
configuracoes de FOLHA 5 e FOLHA 20 (as da referencia, trocando so o quantil),
em h = 1 a 12, walk-forward completo, M1 (`completo`), sem truncar em zero:
2 x 7 x 12 = 168 celulas. Mais 8 celulas SO PARA A TRAVA: quantil 0,85 nas duas
folhas em h = 1, 4, 8 e 12.

TRAVA (antes de ler qualquer resultado): o quantil 0,85 desta etapa reproduz
`resultados/referencia/previsoes.csv` (folha 5 = braco `referencia`, folha 20 =
braco `HistGB_folha20_M1`), em todas as origens dos 4 horizontes, diferenca < 1e-9.
Se falhar, a etapa PARA (codigo de saida 1): grava `trava.json` e nada mais.

DEPOIS DA TRAVA: ordena os 7 quantis de cada origem (cruzamentos corrigidos), monta o
composto (em cada semana, o conjunto de quantis da folha que o composto da E3 escolheu,
N = 13, `resultados/ciencia/E3_composto/previsoes.csv`), a regua climatologica (quantis da
mesma semana epidemiologica em anos >= 2018 anteriores ao ano-alvo, minimo 3 anos) e calcula
WIS e cobertura (50, 80 e 90%) por origem. Janelas: a PADRAO (07/01/2024 a 01/02/2026,
102 semanas por horizonte) e a ANTIGA (2024-2025, para comparar com a rodada de 26/09).
Familia F5 (12 testes, Holm): folha 5, folha 20 e composto, cada um contra a regua climatologica,
em h = 1, 4, 8 e 12; Diebold-Mariano HLN sobre a diferenca semanal de WIS, IC 95% por bootstrap
de blocos (8 semanas, 2.000 reamostras, semente 42); sem piso de ruido.

Grava em `resultados/wis/`:
    - `parciais/previsoes_folha<f>_q<nnn>_h<hh>.csv`: um por celula;
    - `trava.json`;
    - `previsoes_quantis.csv` (7 quantis, ordenados, com `previsto_bruto` e `cruzamento_corrigido`),
      `previsoes_quantis_composto.csv`, `cruzamentos.csv`, `regua_climatologica.csv`;
    - `wis_por_origem.csv`, `wis_resumo.csv` (modelo x h x janela: n, WIS medio, cobertura 50/80/90),
      `familia_F5.csv`, `ancoras.json`;
    - `E7_wis.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`)

    # a trava primeiro (8 celulas):
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.e7_wis \\
        --quantis 0.85 > /dev/null 2>&1 &
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e7_wis --so-trava

    # fatias do WIS, em segundo plano (um processo por fatia):
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.e7_wis \\
        --folhas 5 --quantis 0.05 0.1 --horizontes 1 2 3 > /dev/null 2>&1 &

    # juntar (exige as 176 celulas):
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e7_wis --so-juntar

Parciais existentes sao pulados; `--refazer` forca. Ao terminar uma fatia, se as 176 celulas
existem, o proprio script junta e mede.
"""

import argparse
import dataclasses
import pathlib
import sys
import time

import numpy as np
import pandas as pd

from aedes.bracos import montar_matriz_do_braco
from aedes.comparacoes import comparar_previsoes_com_gabarito
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
    FOLHA_20,
    ConfiguracaoModelo,
)
from aedes.dados import montar_tabela_a_partir_dos_bytes
from aedes.metricas import COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE, COLUNA_DO_PREVISTO, COLUNA_DO_REAL
from aedes.quantis import (
    COLUNA_DA_FOLHA,
    COLUNA_DO_PREVISTO_BRUTO,
    COLUNA_DO_QUANTIL,
    HORIZONTES_DA_TRAVA,
    QUANTIL_DA_TRAVA,
    QUANTIS_DO_WIS,
    contar_origens_com_cruzamento,
    ordenar_quantis_cruzados,
)
from aedes.walk_forward import COLUNAS_DAS_PREVISOES, executar_walk_forward
from aedes.wis import (
    COLUNA_DO_MODELO,
    COLUNAS_DOS_ESCORES,
    NOME_DA_REGUA_CLIMATOLOGICA,
    NOME_DO_MODELO_COMPOSTO,
    NOME_DO_MODELO_FOLHA_5,
    NOME_DO_MODELO_FOLHA_20,
    calcular_escores_por_origem,
    executar_familia_f5,
    montar_historico_da_regua,
    montar_quantis_do_composto,
    montar_regua_climatologica,
    recortar_por_data_alvo,
    resumir_escores_por_janela,
)
from experimentos.comum_reproducao import (
    CAMINHO_DAS_ESCOLHAS_DO_COMPOSTO_DA_E3,
    CAMINHO_DO_GABARITO_DO_WIS,
    CAMINHO_DO_GABARITO_DOS_QUANTIS,
    NOME_DA_REFERENCIA_FOLHA_5,
    NOME_DA_REFERENCIA_FOLHA_20,
    PASTA_DO_PROJETO,
    PASTA_DO_WIS,
    TOLERANCIA_DAS_TRAVAS,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_json_de_forma_atomica,
    gravar_parcial,
    ler_csv_de_previsoes,
    ler_parciais_com_datas,
    ler_previsoes_da_referencia,
    validar_horizontes,
)

PASTA_DE_SAIDA = PASTA_DO_WIS
PASTA_DOS_PARCIAIS = PASTA_DE_SAIDA / "parciais"
CAMINHO_DA_TRAVA = PASTA_DE_SAIDA / "trava.json"
CAMINHO_DAS_PREVISOES_DOS_QUANTIS = PASTA_DE_SAIDA / "previsoes_quantis.csv"
CAMINHO_DOS_QUANTIS_DO_COMPOSTO = PASTA_DE_SAIDA / "previsoes_quantis_composto.csv"
CAMINHO_DOS_CRUZAMENTOS = PASTA_DE_SAIDA / "cruzamentos.csv"
CAMINHO_DA_REGUA = PASTA_DE_SAIDA / "regua_climatologica.csv"
CAMINHO_DOS_ESCORES = PASTA_DE_SAIDA / "wis_por_origem.csv"
CAMINHO_DO_RESUMO = PASTA_DE_SAIDA / "wis_resumo.csv"
CAMINHO_DA_FAMILIA_F5 = PASTA_DE_SAIDA / "familia_F5.csv"
CAMINHO_DAS_ANCORAS = PASTA_DE_SAIDA / "ancoras.json"
CAMINHO_DA_TABELA_CRUA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E7_wis.log")

FOLHAS_DO_WIS = (5, 20)
HORIZONTES_DO_WIS = CONFIGURACAO_AVALIACAO.horizontes
HORIZONTES_DA_FAMILIA_F5 = (1, 4, 8, 12)
MODELOS_POR_FOLHA: dict[int, ConfiguracaoModelo] = {5: FOLHA_5, 20: FOLHA_20}
NOME_DO_MODELO_POR_FOLHA = {5: NOME_DO_MODELO_FOLHA_5, 20: NOME_DO_MODELO_FOLHA_20}
NOME_DA_REFERENCIA_POR_FOLHA = {5: NOME_DA_REFERENCIA_FOLHA_5, 20: NOME_DA_REFERENCIA_FOLHA_20}
# Nomes dos modelos na rodada de 26/09 (`previsoes_quantis.csv` antigo).
NOME_ANTIGO_POR_FOLHA = {5: "cenario_adotado", 20: "histgb_folha20"}
NOME_ANTIGO_DA_REGUA = "regua_climatologica"
QUANTIS_DE_TODAS_AS_CELULAS = (*QUANTIS_DO_WIS, QUANTIL_DA_TRAVA)
JANELA_DE_N_N13_DO_COMPOSTO = 13
TOTAL_DE_CELULAS = len(FOLHAS_DO_WIS) * len(QUANTIS_DO_WIS) * len(HORIZONTES_DO_WIS) + len(FOLHAS_DO_WIS) * len(
    HORIZONTES_DA_TRAVA
)
SEMANAS_ESPERADAS_NA_JANELA_PADRAO = 102
TOLERANCIA_DA_ANCORA_DO_WIS = 0.05
CHAVE_DA_TRAVA = [COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]

NOME_DA_JANELA_PADRAO = "padrao_2024-01-07_a_2026-02-01"
NOME_DA_JANELA_ANTIGA = "antiga_2024-2025"
JANELAS_DO_WIS: dict[str, tuple[pd.Timestamp, pd.Timestamp]] = {
    NOME_DA_JANELA_PADRAO: (
        CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada,
        CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada,
    ),
    NOME_DA_JANELA_ANTIGA: (pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31")),
}

# Ancoras da rodada de 26/09 (janela antiga, n = 97): WIS medio por modelo e horizonte (pre-declaracao, secao 5).
ANCORAS_DO_WIS_NA_JANELA_ANTIGA: dict[tuple[str, int], float] = {
    (NOME_DO_MODELO_FOLHA_5, 1): 101.9,
    (NOME_DO_MODELO_FOLHA_5, 4): 215.4,
    (NOME_DO_MODELO_FOLHA_5, 8): 288.6,
    (NOME_DO_MODELO_FOLHA_5, 12): 300.7,
    (NOME_DO_MODELO_FOLHA_20, 1): 121.3,
    (NOME_DO_MODELO_FOLHA_20, 4): 199.0,
    (NOME_DO_MODELO_FOLHA_20, 8): 259.0,
    (NOME_DO_MODELO_FOLHA_20, 12): 278.6,
    (NOME_DA_REGUA_CLIMATOLOGICA, 1): 292.7,
    (NOME_DA_REGUA_CLIMATOLOGICA, 4): 313.5,
    (NOME_DA_REGUA_CLIMATOLOGICA, 8): 322.2,
    (NOME_DA_REGUA_CLIMATOLOGICA, 12): 324.2,
}


@dataclasses.dataclass(frozen=True)
class CelulaDoWis:
    """Uma celula: uma folha, um quantil e um horizonte."""

    folha: int
    quantil: float
    horizonte: int


def sufixo_do_quantil(quantil: float) -> str:
    """Quantil em tres digitos para nome de arquivo: 0,05 vira `005`; 0,85 vira `085`."""
    return f"{round(quantil * 100):03d}"


def caminho_do_parcial(celula: CelulaDoWis) -> pathlib.Path:
    """Caminho do parcial de uma celula."""
    nome = f"previsoes_folha{celula.folha}_q{sufixo_do_quantil(celula.quantil)}_h{celula.horizonte:02d}.csv"
    return PASTA_DOS_PARCIAIS / nome


def montar_todas_as_celulas() -> list[CelulaDoWis]:
    """As 176 celulas: 168 do WIS (folha, quantil, h) mais 8 da trava (q0,85 em h = 1, 4, 8, 12), nessa ordem por folha."""
    celulas: list[CelulaDoWis] = []
    for folha in FOLHAS_DO_WIS:
        for quantil in QUANTIS_DO_WIS:
            for horizonte in HORIZONTES_DO_WIS:
                celulas.append(CelulaDoWis(folha, quantil, horizonte))
        for horizonte in HORIZONTES_DA_TRAVA:
            celulas.append(CelulaDoWis(folha, QUANTIL_DA_TRAVA, horizonte))
    return celulas


def selecionar_celulas(
    folhas: list[int] | None,
    quantis: list[float] | None,
    horizontes: list[int] | None,
) -> list[CelulaDoWis]:
    """Filtra as 176 celulas pelas folhas, quantis e horizontes pedidos (`None` = todos)."""
    selecionadas: list[CelulaDoWis] = []
    for celula in montar_todas_as_celulas():
        if folhas is not None and celula.folha not in folhas:
            continue
        if quantis is not None and celula.quantil not in quantis:
            continue
        if horizontes is not None and celula.horizonte not in horizontes:
            continue
        selecionadas.append(celula)
    return selecionadas


def rodar_um_pedaco(celula: CelulaDoWis, tabela_cortada: pd.DataFrame) -> pd.DataFrame:
    """Walk-forward completo de uma celula (braco `completo`, sem truncar em zero)."""
    configuracao_do_modelo = dataclasses.replace(
        MODELOS_POR_FOLHA[celula.folha],
        nome=f"histgb_folha{celula.folha}_q{sufixo_do_quantil(celula.quantil)}",
        quantil=celula.quantil,
    )
    matriz = montar_matriz_do_braco(
        tabela_cortada, celula.horizonte, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    inicio = time.perf_counter()
    previsoes = executar_walk_forward(matriz, celula.horizonte, configuracao_do_modelo, CONFIGURACAO_AVALIACAO)
    segundos = time.perf_counter() - inicio

    previsoes.insert(0, COLUNA_DO_QUANTIL, celula.quantil)
    previsoes.insert(0, COLUNA_DA_FOLHA, celula.folha)
    previsoes = previsoes[[COLUNA_DA_FOLHA, COLUNA_DO_QUANTIL, *COLUNAS_DAS_PREVISOES]]
    REGISTRADOR.registrar(
        f"pedaco folha={celula.folha} q={celula.quantil:.2f} h={celula.horizonte:2d} "
        f"linhas_da_matriz={len(matriz)} previsoes={len(previsoes)} tempo={segundos:.1f}s"
    )
    return previsoes


def listar_parciais_faltantes(celulas: list[CelulaDoWis]) -> list[pathlib.Path]:
    """Parciais que ainda nao existem entre os das celulas dadas."""
    faltantes: list[pathlib.Path] = []
    for celula in celulas:
        caminho = caminho_do_parcial(celula)
        if not caminho.exists():
            faltantes.append(caminho)
    return faltantes


def juntar_parciais(celulas: list[CelulaDoWis]) -> pd.DataFrame:
    """Junta os parciais das celulas dadas, na ordem recebida.

    Raises:
        FileNotFoundError: Se algum parcial nao existir.
    """
    faltantes = listar_parciais_faltantes(celulas)
    if faltantes:
        nomes = ", ".join(caminho.name for caminho in faltantes[:3])
        raise FileNotFoundError(f"{len(faltantes)} parcial(is) ausente(s), ex.: {nomes}")
    tabelas: list[pd.DataFrame] = []
    for celula in celulas:
        tabelas.append(ler_parciais_com_datas(caminho_do_parcial(celula)))
    return pd.concat(tabelas, ignore_index=True)


def conferir_trava(previsoes_do_quantil_da_trava: pd.DataFrame) -> dict[str, object]:
    """Trava: o quantil 0,85 reproduz a referencia certificada das duas folhas, diferenca < 1e-9 em todas as origens.

    Args:
        previsoes_do_quantil_da_trava: Linhas com `quantil == 0,85` das duas folhas, nos 4 horizontes.

    Returns:
        `{"passou": bool, "por_folha": {...}}` com o resultado da comparacao de cada folha.
    """
    referencia = ler_previsoes_da_referencia()
    resultado_por_folha: dict[str, object] = {}
    todas_passaram = True
    for folha in FOLHAS_DO_WIS:
        da_folha = previsoes_do_quantil_da_trava.loc[previsoes_do_quantil_da_trava[COLUNA_DA_FOLHA] == folha]
        e_do_braco = referencia[COLUNA_DO_BRACO] == NOME_DA_REFERENCIA_POR_FOLHA[folha]
        e_dos_horizontes = referencia[COLUNA_DO_HORIZONTE].isin(HORIZONTES_DA_TRAVA)
        da_referencia = referencia.loc[e_do_braco & e_dos_horizontes]
        resultado = comparar_previsoes_com_gabarito(da_folha, da_referencia, CHAVE_DA_TRAVA, TOLERANCIA_DAS_TRAVAS)
        conteudo = dataclasses.asdict(resultado)
        conteudo["gabarito"] = (
            f"resultados/referencia/previsoes.csv, braco {NOME_DA_REFERENCIA_POR_FOLHA[folha]}, "
            f"h em {list(HORIZONTES_DA_TRAVA)}"
        )
        resultado_por_folha[f"folha{folha}"] = conteudo
        todas_passaram = todas_passaram and resultado.passou
    return {"passou": bool(todas_passaram), "por_folha": resultado_por_folha}


def extrair_quantis_da_folha_e_horizonte(
    previsoes_ordenadas: pd.DataFrame,
    folha: int,
    horizonte: int,
) -> tuple[pd.Series, pd.DataFrame]:
    """Reais e quantis ordenados de uma folha em um horizonte, indexados por `data_alvo`.

    Returns:
        `reais` (Series) e `quantis` (DataFrame com uma coluna por nivel, na ordem de `QUANTIS_DO_WIS`).

    Raises:
        ValueError: Se os niveis das colunas nao forem os 7 do WIS.
    """
    e_da_folha = previsoes_ordenadas[COLUNA_DA_FOLHA] == folha
    e_do_horizonte = previsoes_ordenadas[COLUNA_DO_HORIZONTE] == horizonte
    da_origem = previsoes_ordenadas.loc[e_da_folha & e_do_horizonte]
    quantis = da_origem.pivot(index=COLUNA_DATA_ALVO, columns=COLUNA_DO_QUANTIL, values=COLUNA_DO_PREVISTO)
    if list(quantis.columns) != list(QUANTIS_DO_WIS):
        raise ValueError(f"Niveis inesperados na folha {folha}, h {horizonte}: {list(quantis.columns)}")
    quantis = quantis.sort_index()
    reais = da_origem.drop_duplicates(COLUNA_DATA_ALVO).set_index(COLUNA_DATA_ALVO)[COLUNA_DO_REAL].sort_index()
    return reais, quantis


def ler_as_escolhas_do_composto() -> pd.DataFrame:
    """Escolhas do composto da E3 com N = 13: `h`, `data_alvo`, `folha_escolhida` de todas as origens.

    Raises:
        FileNotFoundError: Se a E3 nao estiver pronta.
    """
    previsoes_do_composto = ler_csv_de_previsoes(
        CAMINHO_DAS_ESCOLHAS_DO_COMPOSTO_DA_E3, [COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO]
    )
    e_da_janela_primaria = previsoes_do_composto["N"] == JANELA_DE_N_N13_DO_COMPOSTO
    return previsoes_do_composto.loc[e_da_janela_primaria, [COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO, "folha_escolhida"]]


def extrair_a_escolha_do_horizonte(escolhas_do_composto: pd.DataFrame, horizonte: int) -> pd.Series:
    """Folha escolhida pelo composto (5 ou 20) em cada semana-alvo do horizonte, indexada por `data_alvo`."""
    do_horizonte = escolhas_do_composto.loc[escolhas_do_composto[COLUNA_DO_HORIZONTE] == horizonte]
    return do_horizonte.set_index(COLUNA_DATA_ALVO)["folha_escolhida"].sort_index()


def empilhar_quantis_em_formato_longo(
    nome_do_modelo: str,
    horizonte: int,
    quantis: pd.DataFrame,
) -> pd.DataFrame:
    """Transforma a matriz de quantis (data_alvo x nivel) em linhas `modelo`, `h`, `data_alvo`, `quantil`, `previsto`."""
    longo = quantis.stack().reset_index()
    longo.columns = [COLUNA_DATA_ALVO, COLUNA_DO_QUANTIL, COLUNA_DO_PREVISTO]
    longo.insert(0, COLUNA_DO_HORIZONTE, horizonte)
    longo.insert(0, COLUNA_DO_MODELO, nome_do_modelo)
    return longo


def comparar_com_as_previsoes_antigas(previsoes_ordenadas: pd.DataFrame) -> dict[str, object]:
    """As previsoes dos 7 quantis (valores brutos, antes de ordenar) contra as salvas pela rodada de 26/09.

    A rodada antiga so tem h = 1, 4, 8 e 12. Casa por (modelo, h, quantil, data_alvo). Divergencia e relatada.
    """
    antigas = ler_csv_de_previsoes(CAMINHO_DO_GABARITO_DOS_QUANTIS, [COLUNA_DATA_ALVO])
    novas = previsoes_ordenadas[
        [COLUNA_DA_FOLHA, COLUNA_DO_HORIZONTE, COLUNA_DO_QUANTIL, COLUNA_DATA_ALVO, COLUNA_DO_PREVISTO_BRUTO]
    ].copy()
    nome_antigo_por_linha: list[str] = []
    for folha in novas[COLUNA_DA_FOLHA]:
        nome_antigo_por_linha.append(NOME_ANTIGO_POR_FOLHA[int(folha)])
    novas[COLUNA_DO_MODELO] = nome_antigo_por_linha

    antigas_na_chave = antigas[
        [COLUNA_DO_MODELO, COLUNA_DO_HORIZONTE, COLUNA_DO_QUANTIL, COLUNA_DATA_ALVO, COLUNA_DO_PREVISTO_BRUTO]
    ]
    chave = [COLUNA_DO_MODELO, COLUNA_DO_HORIZONTE, COLUNA_DO_QUANTIL, COLUNA_DATA_ALVO]
    cruzamento = novas.merge(antigas_na_chave, on=chave, how="outer", suffixes=("_novo", "_antigo"), indicator=True)
    em_comum = cruzamento.loc[cruzamento["_merge"] == "both"]
    so_nas_novas_dos_horizontes_antigos = cruzamento.loc[
        (cruzamento["_merge"] == "left_only") & (cruzamento[COLUNA_DO_HORIZONTE].isin(HORIZONTES_DA_TRAVA))
    ]
    so_nas_antigas = cruzamento.loc[cruzamento["_merge"] == "right_only"]
    diferencas = (em_comum[f"{COLUNA_DO_PREVISTO_BRUTO}_novo"] - em_comum[f"{COLUNA_DO_PREVISTO_BRUTO}_antigo"]).abs()
    return {
        "linhas_em_comum": int(len(em_comum)),
        "linhas_so_nas_novas_nos_horizontes_antigos": int(len(so_nas_novas_dos_horizontes_antigos)),
        "linhas_so_nas_antigas": int(len(so_nas_antigas)),
        "diferenca_maxima_do_previsto_bruto": float(diferencas.max()) if len(diferencas) > 0 else float("nan"),
        "linhas_com_diferenca_acima_de_1e-9": int((diferencas >= TOLERANCIA_DAS_TRAVAS).sum()),
    }


def comparar_o_resumo_com_a_rodada_antiga(resumo: pd.DataFrame) -> list[dict[str, object]]:
    """WIS medio e `n` da janela ANTIGA (2024-2025) contra a tabela salva em 26/09 e contra as ancoras da pre-declaracao."""
    antigo = ler_csv_de_previsoes(CAMINHO_DO_GABARITO_DO_WIS, [])
    antigo_de_2024_2025 = antigo.loc[antigo["recorte"] == "2024-2025"]
    nome_novo_por_antigo = {
        "cenario_adotado": NOME_DO_MODELO_FOLHA_5,
        "histgb_folha20": NOME_DO_MODELO_FOLHA_20,
        NOME_ANTIGO_DA_REGUA: NOME_DA_REGUA_CLIMATOLOGICA,
    }
    resumo_da_janela_antiga = resumo.loc[resumo["janela"] == NOME_DA_JANELA_ANTIGA]

    entradas: list[dict[str, object]] = []
    for _, linha_antiga in antigo_de_2024_2025.iterrows():
        nome_novo = nome_novo_por_antigo[str(linha_antiga["modelo"])]
        horizonte = int(linha_antiga["h"])
        e_o_modelo = resumo_da_janela_antiga[COLUNA_DO_MODELO] == nome_novo
        e_o_horizonte = resumo_da_janela_antiga[COLUNA_DO_HORIZONTE] == horizonte
        linha_nova = resumo_da_janela_antiga.loc[e_o_modelo & e_o_horizonte]
        if len(linha_nova) != 1:
            continue
        wis_novo = float(linha_nova["wis_medio"].iloc[0])
        wis_antigo = float(linha_antiga["wis_medio"])
        ancora_da_predeclaracao = ANCORAS_DO_WIS_NA_JANELA_ANTIGA.get((nome_novo, horizonte))
        entradas.append(
            {
                "modelo": nome_novo,
                "h": horizonte,
                "n_novo": int(linha_nova["n"].iloc[0]),
                "n_antigo": int(linha_antiga["n"]),
                "wis_novo": wis_novo,
                "wis_antigo_26_09": wis_antigo,
                "diferenca_absoluta": abs(wis_novo - wis_antigo),
                "ancora_da_predeclaracao": ancora_da_predeclaracao,
                "bate_a_ancora": (
                    None if ancora_da_predeclaracao is None
                    else bool(abs(wis_novo - ancora_da_predeclaracao) < TOLERANCIA_DA_ANCORA_DO_WIS)
                ),
                "cobertura_50_novo": float(linha_nova["cobertura_50"].iloc[0]),
                "cobertura_50_antigo": float(linha_antiga["cobertura_50"]),
                "cobertura_90_novo": float(linha_nova["cobertura_90"].iloc[0]),
                "cobertura_90_antigo": float(linha_antiga["cobertura_90"]),
            }
        )
    return entradas


def montar_os_escores_de_todos_os_modelos(
    previsoes_ordenadas: pd.DataFrame,
    historico_da_regua: pd.DataFrame,
    escolhas_do_composto: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """WIS e cobertura por origem das duas folhas, do composto e da regua, em h = 1 a 12.

    Args:
        previsoes_ordenadas: Quantis das duas folhas, ja ordenados.
        historico_da_regua: Saida de `montar_historico_da_regua`.
        escolhas_do_composto: Saida de `ler_as_escolhas_do_composto`.

    Returns:
        Os escores empilhados, os quantis do composto (formato longo) e os da regua (formato longo).
    """
    escores_por_modelo: list[pd.DataFrame] = []
    quantis_do_composto_em_longo: list[pd.DataFrame] = []
    quantis_da_regua_em_longo: list[pd.DataFrame] = []

    for horizonte in HORIZONTES_DO_WIS:
        reais_da_folha_5, quantis_da_folha_5 = extrair_quantis_da_folha_e_horizonte(previsoes_ordenadas, 5, horizonte)
        reais_da_folha_20, quantis_da_folha_20 = extrair_quantis_da_folha_e_horizonte(previsoes_ordenadas, 20, horizonte)

        for nome_do_modelo, reais, quantis in (
            (NOME_DO_MODELO_FOLHA_5, reais_da_folha_5, quantis_da_folha_5),
            (NOME_DO_MODELO_FOLHA_20, reais_da_folha_20, quantis_da_folha_20),
        ):
            escores_por_modelo.append(
                calcular_escores_por_origem(
                    nome_do_modelo,
                    horizonte,
                    pd.Series(quantis.index),
                    reais.reindex(quantis.index),
                    quantis.to_numpy(dtype=float),
                )
            )

        escolha_do_composto = extrair_a_escolha_do_horizonte(escolhas_do_composto, horizonte)
        quantis_do_composto = montar_quantis_do_composto(quantis_da_folha_5, quantis_da_folha_20, escolha_do_composto)
        escores_por_modelo.append(
            calcular_escores_por_origem(
                NOME_DO_MODELO_COMPOSTO,
                horizonte,
                pd.Series(quantis_do_composto.index),
                reais_da_folha_5.reindex(quantis_do_composto.index),
                quantis_do_composto.to_numpy(dtype=float),
            )
        )
        quantis_do_composto_em_longo.append(
            empilhar_quantis_em_formato_longo(NOME_DO_MODELO_COMPOSTO, horizonte, quantis_do_composto)
        )

        regua = montar_regua_climatologica(historico_da_regua, pd.Series(quantis_da_folha_5.index))
        reais_da_regua = reais_da_folha_5.reindex(regua.index)
        escores_por_modelo.append(
            calcular_escores_por_origem(
                NOME_DA_REGUA_CLIMATOLOGICA,
                horizonte,
                pd.Series(regua.index),
                reais_da_regua,
                regua.to_numpy(dtype=float),
            )
        )
        quantis_da_regua_em_longo.append(
            empilhar_quantis_em_formato_longo(NOME_DA_REGUA_CLIMATOLOGICA, horizonte, regua)
        )

    escores = pd.concat(escores_por_modelo, ignore_index=True)[list(COLUNAS_DOS_ESCORES)]
    return escores, pd.concat(quantis_do_composto_em_longo, ignore_index=True), pd.concat(
        quantis_da_regua_em_longo, ignore_index=True
    )


def montar_os_escores_da_janela_padrao(escores: pd.DataFrame) -> dict[tuple[str, int], pd.DataFrame]:
    """Escores da janela padrao, por (modelo, h), para a familia F5."""
    primeira_data, ultima_data = JANELAS_DO_WIS[NOME_DA_JANELA_PADRAO]
    na_janela = recortar_por_data_alvo(escores, primeira_data, ultima_data)
    por_modelo_e_horizonte: dict[tuple[str, int], pd.DataFrame] = {}
    for chave, grupo in na_janela.groupby([COLUNA_DO_MODELO, COLUNA_DO_HORIZONTE], sort=False):
        nome_do_modelo, horizonte = chave
        por_modelo_e_horizonte[(str(nome_do_modelo), int(horizonte))] = grupo
    return por_modelo_e_horizonte


def juntar_e_medir(inicio_da_rodada: float) -> int:
    """Junta as 176 celulas, confere a trava e (so se passar) ordena os quantis, calcula WIS e roda a familia F5.

    Returns:
        0 se a trava passou; 1 se falhou.
    """
    todas_as_celulas = montar_todas_as_celulas()
    previsoes_brutas = juntar_parciais(todas_as_celulas)

    e_do_quantil_da_trava = np.isclose(previsoes_brutas[COLUNA_DO_QUANTIL], QUANTIL_DA_TRAVA, rtol=0.0, atol=1e-12)
    trava = conferir_trava(previsoes_brutas.loc[e_do_quantil_da_trava])
    gravar_json_de_forma_atomica({"trava": trava}, CAMINHO_DA_TRAVA)
    if not trava["passou"]:
        REGISTRADOR.registrar(
            "TRAVA FALHOU: a etapa para. trava.json gravado para diagnostico; "
            "nenhum resultado foi gerado e nenhum deve ser lido."
        )
        return 1

    previsoes_dos_7_quantis = previsoes_brutas.loc[~e_do_quantil_da_trava]
    previsoes_ordenadas = ordenar_quantis_cruzados(previsoes_dos_7_quantis)
    previsoes_ordenadas.to_csv(CAMINHO_DAS_PREVISOES_DOS_QUANTIS, index=False)
    contagem_de_cruzamentos = contar_origens_com_cruzamento(previsoes_ordenadas)
    contagem_de_cruzamentos.to_csv(CAMINHO_DOS_CRUZAMENTOS, index=False)

    conteudo_da_tabela_crua = CAMINHO_DA_TABELA_CRUA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_da_tabela_crua, CONFIGURACAO_DADOS)
    historico_da_regua = montar_historico_da_regua(tabela_crua, CONFIGURACAO_DADOS)

    escolhas_do_composto = ler_as_escolhas_do_composto()
    escores, quantis_do_composto, quantis_da_regua = montar_os_escores_de_todos_os_modelos(
        previsoes_ordenadas, historico_da_regua, escolhas_do_composto
    )
    escores.to_csv(CAMINHO_DOS_ESCORES, index=False)
    quantis_do_composto.to_csv(CAMINHO_DOS_QUANTIS_DO_COMPOSTO, index=False)
    quantis_da_regua.to_csv(CAMINHO_DA_REGUA, index=False)

    resumo = resumir_escores_por_janela(escores, JANELAS_DO_WIS)
    resumo.to_csv(CAMINHO_DO_RESUMO, index=False)

    escores_da_janela_padrao = montar_os_escores_da_janela_padrao(escores)
    familia_f5 = executar_familia_f5(
        escores_da_janela_padrao,
        (NOME_DO_MODELO_FOLHA_5, NOME_DO_MODELO_FOLHA_20, NOME_DO_MODELO_COMPOSTO),
        HORIZONTES_DA_FAMILIA_F5,
    )
    familia_f5.to_csv(CAMINHO_DA_FAMILIA_F5, index=False)

    resumo_da_janela_padrao = resumo.loc[resumo["janela"] == NOME_DA_JANELA_PADRAO]
    modelos_com_102 = resumo_da_janela_padrao.loc[
        resumo_da_janela_padrao[COLUNA_DO_MODELO].isin([NOME_DO_MODELO_FOLHA_5, NOME_DO_MODELO_FOLHA_20, NOME_DO_MODELO_COMPOSTO])
    ]
    n_confere = bool((modelos_com_102["n"] == SEMANAS_ESPERADAS_NA_JANELA_PADRAO).all())
    n_da_regua_por_horizonte: dict[str, int] = {}
    resumo_da_regua = resumo_da_janela_padrao.loc[resumo_da_janela_padrao[COLUNA_DO_MODELO] == NOME_DA_REGUA_CLIMATOLOGICA]
    for _, linha_da_regua in resumo_da_regua.iterrows():
        n_da_regua_por_horizonte[str(int(linha_da_regua["h"]))] = int(linha_da_regua["n"])
    gravar_json_de_forma_atomica(
        {
            "n_de_102_semanas_por_horizonte_nos_3_modelos": n_confere,
            "n_da_regua_por_horizonte_na_janela_padrao": n_da_regua_por_horizonte,
            "previsoes_dos_7_quantis_contra_a_rodada_de_26_09": comparar_com_as_previsoes_antigas(previsoes_ordenadas),
            "wis_da_janela_antiga_contra_26_09": comparar_o_resumo_com_a_rodada_antiga(resumo),
            "origens_com_cruzamento": contagem_de_cruzamentos.to_dict(orient="records"),
        },
        CAMINHO_DAS_ANCORAS,
    )

    segundos = time.perf_counter() - inicio_da_rodada
    REGISTRADOR.registrar(
        f"juncao: {len(previsoes_brutas)} previsoes brutas; trava OK; {len(escores)} escores por origem; "
        f"{len(familia_f5)} testes da F5; tempo deste processo={segundos:.1f}s"
    )
    return 0


def ler_argumentos() -> argparse.Namespace:
    """Le as fatias (`--folhas`, `--quantis`, `--horizontes`) e `--refazer`, `--so-juntar`, `--so-trava`."""
    leitor = argparse.ArgumentParser(description="E7: WIS, um HistGB por quantil, em pedacos.")
    leitor.add_argument("--folhas", type=int, nargs="+", choices=FOLHAS_DO_WIS, default=None)
    leitor.add_argument("--quantis", type=float, nargs="+", default=None,
                        help="Quantis a rodar (os 7 do WIS e 0.85, que so existe para a trava).")
    leitor.add_argument("--horizontes", type=int, nargs="+", default=None)
    leitor.add_argument("--refazer", action="store_true", help="Recalcula parciais que ja existem.")
    leitor.add_argument("--so-juntar", action="store_true", help="Nao treina nada: junta as 176 celulas e mede.")
    leitor.add_argument("--so-trava", action="store_true", help="Nao treina nada: confere a trava nas 8 celulas do q0,85.")
    argumentos = leitor.parse_args()
    if argumentos.quantis is not None:
        quantis_invalidos = [q for q in argumentos.quantis if q not in QUANTIS_DE_TODAS_AS_CELULAS]
        if quantis_invalidos:
            leitor.error(f"quantis fora de {list(QUANTIS_DE_TODAS_AS_CELULAS)}: {quantis_invalidos}")
    if argumentos.horizontes is not None:
        try:
            validar_horizontes(argumentos.horizontes)
        except ValueError as erro:
            leitor.error(str(erro))
    return argumentos


def conferir_so_a_trava() -> int:
    """`--so-trava`: junta as 8 celulas do quantil 0,85 e confere a trava (grava so `trava.json`).

    Returns:
        0 se passou; 1 se falhou ou faltar parcial.
    """
    celulas_da_trava = selecionar_celulas(None, [QUANTIL_DA_TRAVA], None)
    faltantes = listar_parciais_faltantes(celulas_da_trava)
    if faltantes:
        REGISTRADOR.registrar(f"--so-trava: faltam {len(faltantes)} de {len(celulas_da_trava)} parciais do q0,85.")
        return 1
    previsoes = juntar_parciais(celulas_da_trava)
    trava = conferir_trava(previsoes)
    gravar_json_de_forma_atomica({"trava": trava}, CAMINHO_DA_TRAVA)
    REGISTRADOR.registrar(f"--so-trava: passou={trava['passou']}")
    if trava["passou"]:
        return 0
    return 1


def main() -> int:
    """Roda as fatias pedidas e, se as 176 celulas existirem, junta, confere a trava e mede."""
    inicio_da_rodada = time.perf_counter()
    argumentos = ler_argumentos()

    if argumentos.so_trava:
        return conferir_so_a_trava()

    if not argumentos.so_juntar:
        celulas = selecionar_celulas(argumentos.folhas, argumentos.quantis, argumentos.horizontes)
        if len(celulas) == 0:
            REGISTRADOR.registrar("Nenhuma celula na fatia pedida (o q0,85 so existe em h = 1, 4, 8 e 12).")
            return 1
        tabela_cortada = carregar_tabela_cortada()
        REGISTRADOR.registrar(f"inicio: {len(celulas)} celula(s) pedida(s)")
        for celula in celulas:
            caminho = caminho_do_parcial(celula)
            if caminho.exists() and not argumentos.refazer:
                REGISTRADOR.registrar(f"pulado (parcial ja existe): {caminho.name}")
                continue
            previsoes = rodar_um_pedaco(celula, tabela_cortada)
            gravar_parcial(previsoes, caminho)

    faltantes = listar_parciais_faltantes(montar_todas_as_celulas())
    if faltantes:
        REGISTRADOR.registrar(f"fim do pedaco: faltam {len(faltantes)} de {TOTAL_DE_CELULAS} parciais; juncao adiada.")
        return 0
    return juntar_e_medir(inicio_da_rodada)


if __name__ == "__main__":
    sys.exit(main())
