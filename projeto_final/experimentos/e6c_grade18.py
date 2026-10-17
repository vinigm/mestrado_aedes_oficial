"""E6c: reproducao da busca de 18 hiperparametros do HistGB (pre-declaracao de 12/10/2026, secao 4).

Quantil 0,85, M1, `random_state` 42, SEM truncar em zero. Ver `aedes/hiperparametros.py`.

FASE 1 (escolha, so calibracao): 18 configuracoes x h em {1, 4, 8, 12} = 72 celulas.
A matriz de cada horizonte e cortada em `data_alvo <= 31/12/2023` ANTES do laco
(da as mesmas previsoes, bit a bit, que rodar tudo e filtrar; provado em
`testes/test_walk_forward_com_corte.py`): a avaliacao NAO e vista na escolha,
por construcao. Criterio: menor MAE medio de calibracao nos 4 horizontes.

FASE 2 (um teste, na avaliacao): so se a vencedora da fase 1 NAO for a
referencia. Roda a vencedora e a referencia na matriz INTEIRA (4 horizontes) e
aplica Wilcoxon pareado por `data_alvo`, Holm em 4 testes, e a regra de troca
(reduzir o MAE em h = 8 E h = 12 com p de Holm < 0,05). Chame com `--fase2`.

TRAVAS (antes de ler qualquer resultado):
    1. a referencia da grade, na calibracao, reproduz `resultados/referencia/previsoes.csv`
       (braco `referencia`, `data_alvo <= 2023-12-31`) com diferenca < 1e-9;
    2. (fase 2) a referencia na matriz inteira reproduz a referencia certificada, < 1e-9.
Trava reprovada = a etapa para (codigo de saida 1) e nenhum resultado e gravado alem do diagnostico.

ANCORAS (investigar e reportar, nunca forcar): 1o lugar 0,03 x 400, 15 folhas, folha minima 5
com 41,66; a referencia em 4o com 42,02; folha minima 20 do 10o ao 18o, entre 54,68 e 55,69;
fase 2: -7,5%, +3,3%, +0,1% e +0,2% de reducao, p de Holm 1,0, n = 102.

Grava em `resultados/reproducao_selecao/E6c_grade18/`:
    - `parciais/fase1_<configuracao>_h<hh>.csv` e `parciais_fase2/<configuracao>_h<hh>.csv`;
    - `previsoes_fase1.csv`, `ranking.csv`, `trava.json`, `ancoras.json`, `decisao.json`;
    - `fase2.csv` (so se houver fase 2);
    - `E6c_grade18.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`)

    # uma fatia da fase 1, em segundo plano:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.e6c_grade18 \\
        --configuracoes lr0.05_it250_folhas15_min5 lr0.03_it400_folhas15_min5 > /dev/null 2>&1 &

    # juntar a fase 1 (exige os 72 parciais), conferir a trava e decidir a vencedora:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e6c_grade18 --so-juntar

    # fase 2 (exige `ranking.csv`; roda as celulas que faltam da vencedora e da referencia):
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e6c_grade18 --fase2 --horizontes 1 4

Parciais existentes sao pulados; `--refazer` forca. Ao terminar uma fatia da fase 1, se os 72
parciais existem, o proprio script junta e decide.
"""

import argparse
import dataclasses
import json
import pathlib
import sys
import time

import pandas as pd

from aedes.bracos import montar_matriz_do_braco
from aedes.comparacoes import comparar_previsoes_com_gabarito
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
)
from aedes.hiperparametros import (
    COLUNA_DA_CONFIGURACAO,
    COLUNA_DO_MAE_DE_CALIBRACAO,
    HORIZONTES_DA_BUSCA,
    NOME_DA_REFERENCIA,
    ConfiguracaoDeHiperparametros,
    calcular_mae_medio_de_calibracao,
    comparar_vencedora_com_referencia,
    decidir_a_fase_2,
    montar_a_grade_de_18,
    montar_ranking_da_fase_1,
)
from aedes.metricas import COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE, recortar_janela_de_avaliacao
from aedes.walk_forward import executar_walk_forward
from aedes.walk_forward_com_corte import recortar_matriz_ate_a_data_alvo
from experimentos.comum_reproducao import (
    CAMINHO_DAS_COMPARACOES_ANTIGAS_DA_GRADE_DE_18,
    CAMINHO_DO_RANKING_ANTIGO_DA_GRADE_DE_18,
    NOME_DA_REFERENCIA_FOLHA_5,
    PASTA_DA_REPRODUCAO,
    TOLERANCIA_DAS_TRAVAS,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_json_de_forma_atomica,
    gravar_parcial,
    ler_csv_de_previsoes,
    ler_parciais_com_datas,
    ler_previsoes_da_referencia,
)

PASTA_DE_SAIDA = PASTA_DA_REPRODUCAO / "E6c_grade18"
PASTA_DOS_PARCIAIS_DA_FASE_1 = PASTA_DE_SAIDA / "parciais"
PASTA_DOS_PARCIAIS_DA_FASE_2 = PASTA_DE_SAIDA / "parciais_fase2"
CAMINHO_DAS_PREVISOES_DA_FASE_1 = PASTA_DE_SAIDA / "previsoes_fase1.csv"
CAMINHO_DO_RANKING = PASTA_DE_SAIDA / "ranking.csv"
CAMINHO_DA_TRAVA = PASTA_DE_SAIDA / "trava.json"
CAMINHO_DAS_ANCORAS = PASTA_DE_SAIDA / "ancoras.json"
CAMINHO_DA_DECISAO = PASTA_DE_SAIDA / "decisao.json"
CAMINHO_DA_FASE_2 = PASTA_DE_SAIDA / "fase2.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E6c_grade18.log")

TOTAL_DE_CELULAS_DA_FASE_1 = 72
CHAVE_DA_TRAVA = [COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]
COLUNA_DA_CONFIGURACAO_NAS_PREVISOES = "configuracao"
TOLERANCIA_DA_ANCORA = 0.005
CONFIGURACAO_DA_VENCEDORA_ANTIGA = "lr0.03_it400_folhas15_min5"
MAE_ANCORA_DA_VENCEDORA = 41.66
MAE_ANCORA_DA_REFERENCIA = 42.02
POSICAO_ANCORA_DA_REFERENCIA = 4
POSICOES_DA_FOLHA_MINIMA_20 = (10, 18)
FAIXA_DE_MAE_DA_FOLHA_MINIMA_20 = (54.68, 55.69)


def encontrar_configuracao(nome: str) -> ConfiguracaoDeHiperparametros:
    """Configuracao da grade pelo nome.

    Raises:
        ValueError: Se o nome nao for das 18.
    """
    for configuracao in montar_a_grade_de_18():
        if configuracao.nome == nome:
            return configuracao
    raise ValueError(f"Configuracao desconhecida: {nome!r}.")


def caminho_do_parcial_da_fase_1(nome_da_configuracao: str, horizonte: int) -> pathlib.Path:
    """Caminho do parcial da fase 1 (matriz cortada na calibracao)."""
    return PASTA_DOS_PARCIAIS_DA_FASE_1 / f"fase1_{nome_da_configuracao}_h{horizonte:02d}.csv"


def caminho_do_parcial_da_fase_2(nome_da_configuracao: str, horizonte: int) -> pathlib.Path:
    """Caminho do parcial da fase 2 (matriz inteira)."""
    return PASTA_DOS_PARCIAIS_DA_FASE_2 / f"{nome_da_configuracao}_h{horizonte:02d}.csv"


def rodar_um_pedaco(
    configuracao: ConfiguracaoDeHiperparametros,
    horizonte: int,
    tabela_cortada: pd.DataFrame,
    so_a_calibracao: bool,
) -> pd.DataFrame:
    """Walk-forward do M1 de uma configuracao e um horizonte, sem truncar em zero.

    Args:
        configuracao: As 4 hiperparametros da combinacao.
        horizonte: h.
        tabela_cortada: Tabela certificada com o corte de maturidade.
        so_a_calibracao: Se verdadeiro, a matriz e cortada em `data_alvo <= 31/12/2023` antes do laco (fase 1).

    Returns:
        Previsoes com a coluna `configuracao`.
    """
    matriz = montar_matriz_do_braco(tabela_cortada, horizonte, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    if so_a_calibracao:
        matriz = recortar_matriz_ate_a_data_alvo(matriz, CONFIGURACAO_AVALIACAO.fim_da_calibracao)
    configuracao_do_modelo = configuracao.para_configuracao_do_modelo()

    inicio = time.perf_counter()
    previsoes = executar_walk_forward(matriz, horizonte, configuracao_do_modelo, CONFIGURACAO_AVALIACAO)
    segundos = time.perf_counter() - inicio

    previsoes.insert(0, COLUNA_DA_CONFIGURACAO_NAS_PREVISOES, configuracao.nome)
    nome_da_fase = "fase1" if so_a_calibracao else "fase2"
    REGISTRADOR.registrar(
        f"pedaco {nome_da_fase} {configuracao.nome} h={horizonte:2d} linhas_da_matriz={len(matriz)} "
        f"previsoes={len(previsoes)} tempo={segundos:.1f}s"
    )
    return previsoes


def listar_parciais_faltantes_da_fase_1() -> list[pathlib.Path]:
    """Parciais da fase 1 que ainda nao existem entre os 72 esperados (18 configuracoes x 4 horizontes)."""
    faltantes: list[pathlib.Path] = []
    for configuracao in montar_a_grade_de_18():
        for horizonte in HORIZONTES_DA_BUSCA:
            caminho = caminho_do_parcial_da_fase_1(configuracao.nome, horizonte)
            if not caminho.exists():
                faltantes.append(caminho)
    return faltantes


def juntar_parciais_da_fase_1() -> pd.DataFrame:
    """Junta os 72 parciais na ordem da grade e dos horizontes.

    Raises:
        FileNotFoundError: Se algum parcial nao existir.
    """
    faltantes = listar_parciais_faltantes_da_fase_1()
    if faltantes:
        nomes = ", ".join(caminho.name for caminho in faltantes[:3])
        raise FileNotFoundError(f"{len(faltantes)} parcial(is) ausente(s), ex.: {nomes}")
    tabelas: list[pd.DataFrame] = []
    for configuracao in montar_a_grade_de_18():
        for horizonte in HORIZONTES_DA_BUSCA:
            tabelas.append(ler_parciais_com_datas(caminho_do_parcial_da_fase_1(configuracao.nome, horizonte)))
    return pd.concat(tabelas, ignore_index=True)


def ler_a_referencia_certificada_da_folha_5() -> pd.DataFrame:
    """As previsoes certificadas do braco `referencia` (folha 5) nos 4 horizontes da busca."""
    referencia = ler_previsoes_da_referencia()
    da_folha_5 = referencia[COLUNA_DO_BRACO] == NOME_DA_REFERENCIA_FOLHA_5
    dos_horizontes = referencia[COLUNA_DO_HORIZONTE].isin(HORIZONTES_DA_BUSCA)
    return referencia.loc[da_folha_5 & dos_horizontes]


def conferir_trava_da_calibracao(previsoes_da_fase_1: pd.DataFrame) -> dict[str, object]:
    """Trava 1: a referencia da grade reproduz a referencia certificada na calibracao, diferenca < 1e-9."""
    e_a_referencia = previsoes_da_fase_1[COLUNA_DA_CONFIGURACAO_NAS_PREVISOES] == NOME_DA_REFERENCIA
    da_referencia = previsoes_da_fase_1.loc[e_a_referencia]
    certificada = ler_a_referencia_certificada_da_folha_5()
    na_calibracao = certificada[COLUNA_DATA_ALVO] <= CONFIGURACAO_AVALIACAO.fim_da_calibracao
    certificada_na_calibracao = certificada.loc[na_calibracao]

    resultado = comparar_previsoes_com_gabarito(
        da_referencia, certificada_na_calibracao, CHAVE_DA_TRAVA, TOLERANCIA_DAS_TRAVAS
    )
    conteudo = dataclasses.asdict(resultado)
    conteudo["gabarito"] = (
        f"resultados/referencia/previsoes.csv, braco {NOME_DA_REFERENCIA_FOLHA_5}, "
        f"h em {list(HORIZONTES_DA_BUSCA)}, data_alvo <= {CONFIGURACAO_AVALIACAO.fim_da_calibracao.date()}"
    )
    return conteudo


def calcular_os_maes_de_calibracao(previsoes_da_fase_1: pd.DataFrame) -> dict[str, float]:
    """MAE medio de calibracao de cada configuracao, na ordem da grade."""
    maes: dict[str, float] = {}
    for configuracao in montar_a_grade_de_18():
        e_da_configuracao = previsoes_da_fase_1[COLUNA_DA_CONFIGURACAO_NAS_PREVISOES] == configuracao.nome
        maes[configuracao.nome] = calcular_mae_medio_de_calibracao(previsoes_da_fase_1.loc[e_da_configuracao])
    return maes


def conferir_ancoras_da_fase_1(ranking: pd.DataFrame) -> dict[str, object]:
    """Compara o ranking da fase 1 com as ancoras da pre-declaracao e com o ranking salvo pelo antigo.

    Divergencia nao para a etapa: e relatada (investigar, nunca forcar).
    """
    mae_por_nome = dict(zip(ranking[COLUNA_DA_CONFIGURACAO], ranking[COLUNA_DO_MAE_DE_CALIBRACAO]))
    posicao_por_nome = dict(zip(ranking[COLUNA_DA_CONFIGURACAO], ranking["pos"]))

    antigo = ler_csv_de_previsoes(CAMINHO_DO_RANKING_ANTIGO_DA_GRADE_DE_18, [])
    mae_antigo_por_nome = dict(zip(antigo["configuracao"], antigo["mae_calibracao"]))
    maior_diferenca_para_o_antigo = 0.0
    for nome, mae_antigo in mae_antigo_por_nome.items():
        diferenca = abs(mae_por_nome[nome] - mae_antigo)
        maior_diferenca_para_o_antigo = max(maior_diferenca_para_o_antigo, diferenca)

    maes_da_folha_minima_20: list[float] = []
    posicoes_da_folha_minima_20: list[int] = []
    for configuracao in montar_a_grade_de_18():
        if configuracao.folha_minima == 20:
            maes_da_folha_minima_20.append(float(mae_por_nome[configuracao.nome]))
            posicoes_da_folha_minima_20.append(int(posicao_por_nome[configuracao.nome]))

    primeiro = str(ranking[COLUNA_DA_CONFIGURACAO].iloc[0])
    mae_da_vencedora = float(mae_por_nome[CONFIGURACAO_DA_VENCEDORA_ANTIGA])
    mae_da_referencia = float(mae_por_nome[NOME_DA_REFERENCIA])
    folha_20_em_10_a_18 = (
        min(posicoes_da_folha_minima_20) == POSICOES_DA_FOLHA_MINIMA_20[0]
        and max(posicoes_da_folha_minima_20) == POSICOES_DA_FOLHA_MINIMA_20[1]
    )
    faixa_inferior, faixa_superior = FAIXA_DE_MAE_DA_FOLHA_MINIMA_20
    folha_20_na_faixa = (
        min(maes_da_folha_minima_20) > faixa_inferior - TOLERANCIA_DA_ANCORA
        and max(maes_da_folha_minima_20) < faixa_superior + TOLERANCIA_DA_ANCORA
    )
    return {
        "primeiro_colocado": primeiro,
        "primeiro_e_o_esperado": primeiro == CONFIGURACAO_DA_VENCEDORA_ANTIGA,
        "mae_do_esperado_1o_medido": mae_da_vencedora,
        "mae_do_esperado_1o_ancora": MAE_ANCORA_DA_VENCEDORA,
        "bate_o_mae_do_1o": abs(mae_da_vencedora - MAE_ANCORA_DA_VENCEDORA) < TOLERANCIA_DA_ANCORA,
        "mae_da_referencia_medido": mae_da_referencia,
        "mae_da_referencia_ancora": MAE_ANCORA_DA_REFERENCIA,
        "bate_o_mae_da_referencia": abs(mae_da_referencia - MAE_ANCORA_DA_REFERENCIA) < TOLERANCIA_DA_ANCORA,
        "posicao_da_referencia_medida": int(posicao_por_nome[NOME_DA_REFERENCIA]),
        "posicao_da_referencia_ancora": POSICAO_ANCORA_DA_REFERENCIA,
        "folha_minima_20_posicoes": sorted(posicoes_da_folha_minima_20),
        "folha_minima_20_do_10o_ao_18o": bool(folha_20_em_10_a_18),
        "folha_minima_20_mae_minimo": min(maes_da_folha_minima_20),
        "folha_minima_20_mae_maximo": max(maes_da_folha_minima_20),
        "folha_minima_20_na_faixa_54_68_a_55_69": bool(folha_20_na_faixa),
        "maior_diferenca_de_mae_para_o_ranking_antigo": maior_diferenca_para_o_antigo,
    }


def juntar_e_decidir_a_fase_1(inicio_da_rodada: float) -> int:
    """Junta os 72 parciais, confere a trava 1 e (so se passar) grava ranking, ancoras e decisao da fase 1.

    Returns:
        0 se a trava passou; 1 se falhou.
    """
    previsoes = juntar_parciais_da_fase_1()
    previsoes.to_csv(CAMINHO_DAS_PREVISOES_DA_FASE_1, index=False)

    trava = conferir_trava_da_calibracao(previsoes)
    gravar_json_de_forma_atomica({"trava_1": trava}, CAMINHO_DA_TRAVA)
    if not trava["passou"]:
        REGISTRADOR.registrar(
            "TRAVA 1 FALHOU: a etapa para. previsoes_fase1.csv e trava.json gravados para diagnostico; "
            "ranking NAO foi gerado e nenhum resultado deve ser lido."
        )
        return 1

    maes = calcular_os_maes_de_calibracao(previsoes)
    ranking = montar_ranking_da_fase_1(maes)
    ranking.to_csv(CAMINHO_DO_RANKING, index=False)
    ancoras = conferir_ancoras_da_fase_1(ranking)
    gravar_json_de_forma_atomica(ancoras, CAMINHO_DAS_ANCORAS)

    vencedora = str(ranking[COLUNA_DA_CONFIGURACAO].iloc[0])
    e_a_propria_referencia = vencedora == NOME_DA_REFERENCIA
    decisao = {
        "criterio": "menor MAE medio de calibracao (data_alvo <= 2023-12-31) nos horizontes 1, 4, 8 e 12",
        "vencedora_da_fase_1": vencedora,
        "mae_da_vencedora": float(ranking[COLUNA_DO_MAE_DE_CALIBRACAO].iloc[0]),
        "mae_da_referencia": float(maes[NOME_DA_REFERENCIA]),
        "a_referencia_venceu_a_propria_busca": e_a_propria_referencia,
        "fase_2": (
            "nao ha teste: a referencia venceu a propria busca"
            if e_a_propria_referencia
            else "pendente: rodar `--fase2` (vencedora x referencia na avaliacao)"
        ),
        "troca_a_referencia": False,
        "nota": "o modelo de referencia do artigo NAO muda por esta etapa (regra do Vinicius, 12/10/2026)",
    }
    gravar_json_de_forma_atomica(decisao, CAMINHO_DA_DECISAO)

    segundos = time.perf_counter() - inicio_da_rodada
    REGISTRADOR.registrar(
        f"juncao da fase 1: {len(previsoes)} previsoes; trava 1 OK; vencedora={vencedora} "
        f"(mae_cal={decisao['mae_da_vencedora']:.4f}; referencia={decisao['mae_da_referencia']:.4f}); "
        f"tempo deste processo={segundos:.1f}s"
    )
    return 0


def ler_a_vencedora_da_fase_1() -> str:
    """Nome da vencedora gravado em `decisao.json`.

    Raises:
        FileNotFoundError: Se a fase 1 ainda nao foi juntada e decidida.
    """
    if not CAMINHO_DA_DECISAO.exists():
        raise FileNotFoundError(f"decisao.json ausente: junte e decida a fase 1 antes ({CAMINHO_DA_DECISAO}).")
    with open(CAMINHO_DA_DECISAO, encoding="utf-8") as arquivo:
        decisao = json.load(arquivo)
    return str(decisao["vencedora_da_fase_1"])


def listar_parciais_faltantes_da_fase_2(nomes: list[str]) -> list[pathlib.Path]:
    """Parciais da fase 2 que faltam para as configuracoes dadas (4 horizontes cada)."""
    faltantes: list[pathlib.Path] = []
    for nome in nomes:
        for horizonte in HORIZONTES_DA_BUSCA:
            caminho = caminho_do_parcial_da_fase_2(nome, horizonte)
            if not caminho.exists():
                faltantes.append(caminho)
    return faltantes


def conferir_trava_da_fase_2(previsoes_da_referencia: pd.DataFrame) -> dict[str, object]:
    """Trava 2: a referencia na matriz inteira reproduz a referencia certificada, diferenca < 1e-9."""
    certificada = ler_a_referencia_certificada_da_folha_5()
    resultado = comparar_previsoes_com_gabarito(
        previsoes_da_referencia, certificada, CHAVE_DA_TRAVA, TOLERANCIA_DAS_TRAVAS
    )
    conteudo = dataclasses.asdict(resultado)
    conteudo["gabarito"] = (
        f"resultados/referencia/previsoes.csv, braco {NOME_DA_REFERENCIA_FOLHA_5}, h em {list(HORIZONTES_DA_BUSCA)}, "
        "todas as origens"
    )
    return conteudo


def ler_as_comparacoes_antigas_da_fase_2(vencedora: str) -> dict[int, tuple[float, float]]:
    """Reducao percentual e p de Holm da fase 2 antiga, por horizonte, SE a vencedora for a mesma de antes.

    Returns:
        `h -> (reducao_percentual, p_holm)`; vazio se a vencedora de agora for outra configuracao.
    """
    if vencedora != CONFIGURACAO_DA_VENCEDORA_ANTIGA:
        return {}
    antigas = ler_csv_de_previsoes(CAMINHO_DAS_COMPARACOES_ANTIGAS_DA_GRADE_DE_18, [])
    da_vencedora = antigas.loc[antigas["braco"] == vencedora]
    por_horizonte: dict[int, tuple[float, float]] = {}
    for _, linha in da_vencedora.iterrows():
        por_horizonte[int(linha["h"])] = (float(linha["reducao_percentual"]), float(linha["p_holm"]))
    return por_horizonte


def juntar_e_decidir_a_fase_2(vencedora: str) -> int:
    """Com os parciais da fase 2 completos: confere a trava 2, compara na janela de avaliacao e decide a troca.

    Returns:
        0 se a trava passou; 1 se falhou.
    """
    tabelas_da_referencia: list[pd.DataFrame] = []
    tabelas_da_vencedora: list[pd.DataFrame] = []
    for horizonte in HORIZONTES_DA_BUSCA:
        tabelas_da_referencia.append(ler_parciais_com_datas(caminho_do_parcial_da_fase_2(NOME_DA_REFERENCIA, horizonte)))
        tabelas_da_vencedora.append(ler_parciais_com_datas(caminho_do_parcial_da_fase_2(vencedora, horizonte)))
    previsoes_da_referencia = pd.concat(tabelas_da_referencia, ignore_index=True)
    previsoes_da_vencedora = pd.concat(tabelas_da_vencedora, ignore_index=True)

    trava = conferir_trava_da_fase_2(previsoes_da_referencia)
    with open(CAMINHO_DA_TRAVA, encoding="utf-8") as arquivo:
        conteudo_da_trava = json.load(arquivo)
    conteudo_da_trava["trava_2"] = trava
    gravar_json_de_forma_atomica(conteudo_da_trava, CAMINHO_DA_TRAVA)
    if not trava["passou"]:
        REGISTRADOR.registrar("TRAVA 2 FALHOU: a fase 2 para; fase2.csv NAO foi gerado e nenhum resultado deve ser lido.")
        return 1

    na_janela_da_referencia = recortar_janela_de_avaliacao(previsoes_da_referencia, CONFIGURACAO_AVALIACAO)
    na_janela_da_vencedora = recortar_janela_de_avaliacao(previsoes_da_vencedora, CONFIGURACAO_AVALIACAO)
    comparacoes = []
    for horizonte in HORIZONTES_DA_BUSCA:
        comparacoes.append(
            comparar_vencedora_com_referencia(na_janela_da_referencia, na_janela_da_vencedora, horizonte)
        )
    decisao_da_fase_2 = decidir_a_fase_2(comparacoes)

    comparacoes_antigas = ler_as_comparacoes_antigas_da_fase_2(vencedora)
    linhas: list[dict[str, object]] = []
    for comparacao, p_holm in zip(decisao_da_fase_2.comparacoes, decisao_da_fase_2.p_holm):
        linha = dataclasses.asdict(comparacao)
        linha["p_holm"] = p_holm
        linha["reducao_percentual_antiga"] = comparacoes_antigas.get(comparacao.horizonte, (float("nan"), float("nan")))[0]
        linha["p_holm_antigo"] = comparacoes_antigas.get(comparacao.horizonte, (float("nan"), float("nan")))[1]
        linhas.append(linha)
    tabela_da_fase_2 = pd.DataFrame(linhas)
    tabela_da_fase_2.insert(0, "vencedora", vencedora)
    tabela_da_fase_2.to_csv(CAMINHO_DA_FASE_2, index=False)

    with open(CAMINHO_DA_DECISAO, encoding="utf-8") as arquivo:
        decisao = json.load(arquivo)
    decisao["fase_2"] = "realizada"
    decisao["troca_a_referencia"] = bool(decisao_da_fase_2.troca_a_referencia)
    decisao["regra"] = "reduzir o MAE em h=8 E h=12 com p de Holm < 0,05 nos dois"
    decisao["nota"] = (
        "mesmo que `troca_a_referencia` seja verdadeiro, o modelo de referencia do artigo NAO muda "
        "(regra do Vinicius, 12/10/2026): a decisao e documentada e fica para depois"
    )
    gravar_json_de_forma_atomica(decisao, CAMINHO_DA_DECISAO)
    REGISTRADOR.registrar(
        f"fase 2: vencedora={vencedora}; troca_a_referencia={decisao_da_fase_2.troca_a_referencia}; "
        f"p_holm={[round(p, 4) for p in decisao_da_fase_2.p_holm]}"
    )
    return 0


def rodar_a_fase_2(horizontes: tuple[int, ...], refazer: bool) -> int:
    """Roda as celulas que faltam da vencedora e da referencia na matriz inteira e, completas, decide.

    Returns:
        0 ao terminar (inclusive quando a referencia venceu e nao ha teste, ou quando a juncao fica adiada); 1 se uma trava falhar.
    """
    vencedora = ler_a_vencedora_da_fase_1()
    if vencedora == NOME_DA_REFERENCIA:
        REGISTRADOR.registrar("fase 2: a referencia venceu a propria busca; nao ha teste.")
        return 0

    nomes = [NOME_DA_REFERENCIA, vencedora]
    tabela_cortada = carregar_tabela_cortada()
    REGISTRADOR.registrar(f"inicio da fase 2: {nomes}, horizontes={list(horizontes)}")
    for nome in nomes:
        configuracao = encontrar_configuracao(nome)
        for horizonte in horizontes:
            caminho = caminho_do_parcial_da_fase_2(nome, horizonte)
            if caminho.exists() and not refazer:
                REGISTRADOR.registrar(f"pulado (parcial ja existe): {caminho.name}")
                continue
            previsoes = rodar_um_pedaco(configuracao, horizonte, tabela_cortada, so_a_calibracao=False)
            gravar_parcial(previsoes, caminho)

    faltantes = listar_parciais_faltantes_da_fase_2(nomes)
    if faltantes:
        REGISTRADOR.registrar(f"fim do pedaco da fase 2: faltam {len(faltantes)} de 8 parciais; juncao adiada.")
        return 0
    return juntar_e_decidir_a_fase_2(vencedora)


def ler_argumentos() -> argparse.Namespace:
    """Le `--configuracoes`, `--horizontes`, `--refazer`, `--so-juntar` e `--fase2`."""
    nomes_da_grade = [configuracao.nome for configuracao in montar_a_grade_de_18()]
    leitor = argparse.ArgumentParser(description="E6c: busca de 18 hiperparametros do HistGB, em pedacos.")
    leitor.add_argument("--configuracoes", nargs="+", choices=nomes_da_grade, default=None)
    leitor.add_argument("--horizontes", nargs="+", type=int, choices=HORIZONTES_DA_BUSCA, default=None)
    leitor.add_argument("--refazer", action="store_true", help="Recalcula parciais que ja existem.")
    leitor.add_argument("--so-juntar", action="store_true", help="Nao treina nada: junta os 72 parciais da fase 1 e decide.")
    leitor.add_argument("--fase2", action="store_true", help="Fase 2: vencedora x referencia na avaliacao (exige a fase 1 decidida).")
    return leitor.parse_args()


def main() -> int:
    """Roda as fatias pedidas da fase 1 (ou a fase 2) e, se os 72 parciais existirem, junta e decide."""
    inicio_da_rodada = time.perf_counter()
    argumentos = ler_argumentos()
    horizontes = tuple(argumentos.horizontes) if argumentos.horizontes else HORIZONTES_DA_BUSCA

    if argumentos.fase2:
        return rodar_a_fase_2(horizontes, argumentos.refazer)

    if not argumentos.so_juntar:
        grade = montar_a_grade_de_18()
        if argumentos.configuracoes is not None:
            grade = [configuracao for configuracao in grade if configuracao.nome in argumentos.configuracoes]
        tabela_cortada = carregar_tabela_cortada()
        REGISTRADOR.registrar(f"inicio da fase 1: {len(grade)} configuracao(oes), horizontes={list(horizontes)}")
        for configuracao in grade:
            for horizonte in horizontes:
                caminho = caminho_do_parcial_da_fase_1(configuracao.nome, horizonte)
                if caminho.exists() and not argumentos.refazer:
                    REGISTRADOR.registrar(f"pulado (parcial ja existe): {caminho.name}")
                    continue
                previsoes = rodar_um_pedaco(configuracao, horizonte, tabela_cortada, so_a_calibracao=True)
                gravar_parcial(previsoes, caminho)

    faltantes = listar_parciais_faltantes_da_fase_1()
    if faltantes:
        REGISTRADOR.registrar(
            f"fim do pedaco: faltam {len(faltantes)} de {TOTAL_DE_CELULAS_DA_FASE_1} parciais; juncao adiada."
        )
        return 0
    return juntar_e_decidir_a_fase_1(inicio_da_rodada)


if __name__ == "__main__":
    sys.exit(main())
