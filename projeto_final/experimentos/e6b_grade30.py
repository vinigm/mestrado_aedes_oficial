"""E6b: reproducao da grade de 30 configuracoes (pre-declaracao de 12/10/2026, secao 3).

3 algoritmos x 5 perdas x M0/M1 x h em {1, 4, 8, 12} = 120 walk-forwards
completos (todas as origens, nao so a janela), corte do treino pela RESPOSTA,
retreino semanal e PREVISAO TRUNCADA EM ZERO, como a grade antiga corrigida
(`analises/2026-09-13_correcao_vazamento_treino/`). Ver `aedes/grade.py`.

CRITERIO (o do antigo): menor MAE medio das semanas-alvo ate 31/12/2023
(calibracao), media dos horizontes 1, 4, 8 e 12.

TRAVA (antes de ler qualquer resultado): a celula HistGB, quantil 0,85, M1
reproduz `resultados/referencia/previsoes.csv` (braco `referencia`), TRUNCADA em
zero tambem, com diferenca < 1e-9 nos 4 horizontes. Se falhar, a etapa PARA:
grava `previsoes.csv` e `trava.json` para diagnostico, NAO grava ranking e sai
com codigo 1.

ANCORAS (investigar e reportar, nunca forcar), MAE medio de calibracao:
    1o HistGB q0,85 M1 42,02 | 2o HistGB q0,80 M0 42,52 | 3o HistGB q0,80 M1 42,71 |
    4o GBR q0,80 M1 42,71 | HistGB padrao M1 46,17 | LightGBM padrao M1 47,00 |
    30o LightGBM q0,90 M1 58,45.
As previsoes sao comparadas com as salvas pelo antigo
(`testes/referencia_antiga/e6b_corrigido_previsoes_*.csv`): tolerancia < 1e-9
para HistGB e GBR; para o LightGBM relata-se a diferenca maxima.

Grava em `resultados/reproducao_selecao/E6b_grade30/`:
    - `parciais/previsoes_<algoritmo>_<perda>_<conjunto>_h<hh>.csv`: um por celula;
    - `previsoes.csv`, `resumo.csv` (MAE, R2, n por configuracao, h e periodo),
      `ranking.csv`, `comparacao_com_gabarito.csv`, `ancoras.json`, `trava.json`;
    - `E6b_grade30.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`)

    # uma fatia, em segundo plano, com log; um processo por fatia:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.e6b_grade30 \\
        --algoritmos hist_gradient_boosting --perdas quantil_0.85 --conjuntos M1_com_vetor > /dev/null 2>&1 &

    # conferir so a trava (exige os 4 parciais da celula de referencia):
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e6b_grade30 --so-trava

    # juntar (exige os 120 parciais):
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e6b_grade30 --so-juntar

Parciais que ja existem sao pulados; `--refazer` forca o recalculo. Ao terminar
uma fatia, se os 120 parciais existem, o proprio script junta e mede. Sem
`OMP_NUM_THREADS=1` cada celula leva ~5x mais; o resultado e o mesmo.
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
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
)
from aedes.grade import (
    ALGORITMO_GBR,
    ALGORITMO_HISTGB,
    ALGORITMO_LIGHTGBM,
    ALGORITMOS_DA_GRADE,
    BRACO_DO_PACOTE_POR_CONJUNTO,
    COLUNA_DA_PERDA,
    COLUNA_DO_ALGORITMO,
    COLUNA_DO_CONJUNTO,
    COLUNAS_DAS_PREVISOES_DA_GRADE,
    CONJUNTO_M0,
    CONJUNTO_M1,
    CONJUNTOS_DA_GRADE,
    HORIZONTES_DA_GRADE,
    ROTULO_DA_PERDA_PADRAO,
    ConfiguracaoDaGrade,
    construir_ranking_da_grade,
    executar_walk_forward_da_grade,
    montar_as_30_configuracoes,
    resumir_previsoes_da_grade,
)
from aedes.metricas import COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE
from aedes.walk_forward import COLUNA_DO_PREVISTO
from experimentos.comum_reproducao import (
    CAMINHOS_DOS_GABARITOS_DA_GRADE_DE_30,
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

PASTA_DE_SAIDA = PASTA_DA_REPRODUCAO / "E6b_grade30"
PASTA_DOS_PARCIAIS = PASTA_DE_SAIDA / "parciais"
CAMINHO_DAS_PREVISOES = PASTA_DE_SAIDA / "previsoes.csv"
CAMINHO_DO_RESUMO = PASTA_DE_SAIDA / "resumo.csv"
CAMINHO_DO_RANKING = PASTA_DE_SAIDA / "ranking.csv"
CAMINHO_DA_COMPARACAO = PASTA_DE_SAIDA / "comparacao_com_gabarito.csv"
CAMINHO_DAS_ANCORAS = PASTA_DE_SAIDA / "ancoras.json"
CAMINHO_DA_TRAVA = PASTA_DE_SAIDA / "trava.json"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E6b_grade30.log")

TOTAL_DE_CELULAS = 120
CHAVE_DA_TRAVA = [COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]
CHAVE_DA_COMPARACAO = [*[COLUNA_DO_ALGORITMO, COLUNA_DA_PERDA, COLUNA_DO_CONJUNTO], COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]
TOLERANCIA_DA_ANCORA_DO_RANKING = 0.005
TOLERANCIA_DO_GABARITO_HISTGB_E_GBR = 1e-9
COLUNAS_DA_COMPARACAO_COM_GABARITO = (
    COLUNA_DO_ALGORITMO,
    COLUNA_DA_PERDA,
    COLUNA_DO_CONJUNTO,
    COLUNA_DO_HORIZONTE,
    "linhas_novas",
    "linhas_do_gabarito",
    "linhas_so_nas_novas",
    "linhas_so_no_gabarito",
    "diferenca_maxima_do_previsto",
    "dentro_da_tolerancia",
)

# Configuracao da trava: a referencia do artigo dentro da grade.
CONFIGURACAO_DA_TRAVA = ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1)


@dataclasses.dataclass(frozen=True)
class AncoraDoRanking:
    """Um numero do ranking que a pre-declaracao fixou.

    Attributes:
        posicao: Posicao esperada, ou `None` quando so o MAE e ancora.
        algoritmo: Algoritmo.
        perda: Rotulo da perda (`padrao`, `quantil_0.85`).
        conjunto: `M0_sem_vetor` ou `M1_com_vetor`.
        mae_de_calibracao: MAE medio de calibracao esperado (duas casas).
    """

    posicao: int | None
    algoritmo: str
    perda: str
    conjunto: str
    mae_de_calibracao: float


ANCORAS_DO_RANKING = (
    AncoraDoRanking(1, ALGORITMO_HISTGB, "quantil_0.85", CONJUNTO_M1, 42.02),
    AncoraDoRanking(2, ALGORITMO_HISTGB, "quantil_0.80", CONJUNTO_M0, 42.52),
    AncoraDoRanking(3, ALGORITMO_HISTGB, "quantil_0.80", CONJUNTO_M1, 42.71),
    AncoraDoRanking(4, ALGORITMO_GBR, "quantil_0.80", CONJUNTO_M1, 42.71),
    AncoraDoRanking(None, ALGORITMO_HISTGB, ROTULO_DA_PERDA_PADRAO, CONJUNTO_M1, 46.17),
    AncoraDoRanking(None, ALGORITMO_LIGHTGBM, ROTULO_DA_PERDA_PADRAO, CONJUNTO_M1, 47.00),
    AncoraDoRanking(30, ALGORITMO_LIGHTGBM, "quantil_0.90", CONJUNTO_M1, 58.45),
)


def caminho_do_parcial(configuracao: ConfiguracaoDaGrade, horizonte: int) -> pathlib.Path:
    """Caminho do parcial de uma celula (configuracao e horizonte)."""
    nome = (
        f"previsoes_{configuracao.algoritmo}_{configuracao.rotulo_da_perda()}_"
        f"{configuracao.conjunto}_h{horizonte:02d}.csv"
    )
    return PASTA_DOS_PARCIAIS / nome


def selecionar_configuracoes(
    algoritmos: list[str] | None,
    perdas: list[str] | None,
    conjuntos: list[str] | None,
) -> list[ConfiguracaoDaGrade]:
    """Filtra as 30 configuracoes pelos algoritmos, rotulos de perda e conjuntos pedidos (`None` = todos)."""
    selecionadas: list[ConfiguracaoDaGrade] = []
    for configuracao in montar_as_30_configuracoes():
        if algoritmos is not None and configuracao.algoritmo not in algoritmos:
            continue
        if perdas is not None and configuracao.rotulo_da_perda() not in perdas:
            continue
        if conjuntos is not None and configuracao.conjunto not in conjuntos:
            continue
        selecionadas.append(configuracao)
    return selecionadas


def rodar_um_pedaco(
    configuracao: ConfiguracaoDaGrade,
    horizonte: int,
    tabela_cortada: pd.DataFrame,
) -> pd.DataFrame:
    """Walk-forward completo de uma celula, com previsao truncada em zero; devolve as previsoes com as chaves."""
    nome_do_braco = BRACO_DO_PACOTE_POR_CONJUNTO[configuracao.conjunto]
    matriz = montar_matriz_do_braco(
        tabela_cortada, horizonte, nome_do_braco, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    inicio = time.perf_counter()
    previsoes = executar_walk_forward_da_grade(
        matriz, horizonte, configuracao, CONFIGURACAO_AVALIACAO, truncar_em_zero=True
    )
    segundos = time.perf_counter() - inicio

    previsoes.insert(0, COLUNA_DO_CONJUNTO, configuracao.conjunto)
    previsoes.insert(0, COLUNA_DA_PERDA, configuracao.rotulo_da_perda())
    previsoes.insert(0, COLUNA_DO_ALGORITMO, configuracao.algoritmo)
    previsoes = previsoes[list(COLUNAS_DAS_PREVISOES_DA_GRADE)]
    REGISTRADOR.registrar(
        f"pedaco {configuracao.rotulo()} h={horizonte:2d} linhas_da_matriz={len(matriz)} "
        f"previsoes={len(previsoes)} tempo={segundos:.1f}s"
    )
    return previsoes


def listar_parciais_faltantes(configuracoes: list[ConfiguracaoDaGrade]) -> list[pathlib.Path]:
    """Parciais que ainda nao existem entre os esperados (configuracoes x 4 horizontes)."""
    faltantes: list[pathlib.Path] = []
    for configuracao in configuracoes:
        for horizonte in HORIZONTES_DA_GRADE:
            caminho = caminho_do_parcial(configuracao, horizonte)
            if not caminho.exists():
                faltantes.append(caminho)
    return faltantes


def juntar_parciais(configuracoes: list[ConfiguracaoDaGrade]) -> pd.DataFrame:
    """Junta os parciais na ordem configuracao (a da grade) e horizonte.

    Raises:
        FileNotFoundError: Se algum parcial nao existir.
    """
    faltantes = listar_parciais_faltantes(configuracoes)
    if faltantes:
        nomes = ", ".join(caminho.name for caminho in faltantes[:3])
        raise FileNotFoundError(f"{len(faltantes)} parcial(is) ausente(s), ex.: {nomes}")

    tabelas: list[pd.DataFrame] = []
    for configuracao in configuracoes:
        for horizonte in HORIZONTES_DA_GRADE:
            tabelas.append(ler_parciais_com_datas(caminho_do_parcial(configuracao, horizonte)))
    return pd.concat(tabelas, ignore_index=True)[list(COLUNAS_DAS_PREVISOES_DA_GRADE)]


def conferir_trava(previsoes: pd.DataFrame) -> dict[str, object]:
    """Trava: HistGB q0,85 M1 reproduz a referencia truncada em zero, nas mesmas (h, data_alvo), diferenca < 1e-9.

    Args:
        previsoes: Previsoes da grade (precisa conter a celula de referencia).

    Returns:
        O resultado da comparacao (dicionario) com `passou`.
    """
    e_da_celula = (
        (previsoes[COLUNA_DO_ALGORITMO] == CONFIGURACAO_DA_TRAVA.algoritmo)
        & (previsoes[COLUNA_DA_PERDA] == CONFIGURACAO_DA_TRAVA.rotulo_da_perda())
        & (previsoes[COLUNA_DO_CONJUNTO] == CONFIGURACAO_DA_TRAVA.conjunto)
    )
    da_grade = previsoes.loc[e_da_celula]

    referencia = ler_previsoes_da_referencia()
    da_folha_5 = referencia[COLUNA_DO_BRACO] == NOME_DA_REFERENCIA_FOLHA_5
    dos_horizontes_da_grade = referencia[COLUNA_DO_HORIZONTE].isin(HORIZONTES_DA_GRADE)
    referencia_dos_horizontes = referencia.loc[da_folha_5 & dos_horizontes_da_grade].copy()
    # A grade trunca a previsao em zero; a referencia nao truncava. Compara-se truncando a referencia.
    referencia_dos_horizontes[COLUNA_DO_PREVISTO] = np.maximum(referencia_dos_horizontes[COLUNA_DO_PREVISTO], 0.0)

    resultado = comparar_previsoes_com_gabarito(da_grade, referencia_dos_horizontes, CHAVE_DA_TRAVA, TOLERANCIA_DAS_TRAVAS)
    conteudo = dataclasses.asdict(resultado)
    conteudo["gabarito"] = (
        f"resultados/referencia/previsoes.csv, braco {NOME_DA_REFERENCIA_FOLHA_5}, "
        f"h em {list(HORIZONTES_DA_GRADE)}, previsao truncada em zero dos dois lados"
    )
    return conteudo


def ler_o_gabarito_antigo_da_grade() -> pd.DataFrame:
    """Une os tres CSV de previsoes salvos pelo antigo (`pred` renomeado para `previsto`), com precisao total."""
    tabelas: list[pd.DataFrame] = []
    for caminho in CAMINHOS_DOS_GABARITOS_DA_GRADE_DE_30:
        tabela = ler_csv_de_previsoes(caminho, [COLUNA_DATA_ALVO])
        tabelas.append(tabela)
    juntas = pd.concat(tabelas, ignore_index=True)
    return juntas.rename(columns={"pred": COLUNA_DO_PREVISTO})


def comparar_com_o_gabarito_antigo(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Por configuracao e horizonte: as previsoes novas contra as salvas pelo antigo (diferenca maxima).

    Casa por (h, data_alvo). A tolerancia estrita (< 1e-9) vale para HistGB e GBR; para o LightGBM
    a coluna `dentro_da_tolerancia` usa a mesma tolerancia e o valor da diferenca e o que se relata.

    Args:
        previsoes: Previsoes novas da grade (120 celulas).

    Returns:
        DataFrame com `COLUNAS_DA_COMPARACAO_COM_GABARITO`, uma linha por celula.
    """
    gabarito = ler_o_gabarito_antigo_da_grade()
    linhas: list[dict[str, object]] = []
    for configuracao in montar_as_30_configuracoes():
        e_da_configuracao_novas = (
            (previsoes[COLUNA_DO_ALGORITMO] == configuracao.algoritmo)
            & (previsoes[COLUNA_DA_PERDA] == configuracao.rotulo_da_perda())
            & (previsoes[COLUNA_DO_CONJUNTO] == configuracao.conjunto)
        )
        e_da_configuracao_antiga = (
            (gabarito[COLUNA_DO_ALGORITMO] == configuracao.algoritmo)
            & (gabarito[COLUNA_DA_PERDA] == configuracao.rotulo_da_perda())
            & (gabarito[COLUNA_DO_CONJUNTO] == configuracao.conjunto)
        )
        novas_da_configuracao = previsoes.loc[e_da_configuracao_novas]
        antigas_da_configuracao = gabarito.loc[e_da_configuracao_antiga]
        for horizonte in HORIZONTES_DA_GRADE:
            novas = novas_da_configuracao.loc[novas_da_configuracao[COLUNA_DO_HORIZONTE] == horizonte]
            antigas = antigas_da_configuracao.loc[antigas_da_configuracao[COLUNA_DO_HORIZONTE] == horizonte]
            resultado = comparar_previsoes_com_gabarito(novas, antigas, CHAVE_DA_TRAVA, TOLERANCIA_DAS_TRAVAS)
            linhas.append(
                {
                    COLUNA_DO_ALGORITMO: configuracao.algoritmo,
                    COLUNA_DA_PERDA: configuracao.rotulo_da_perda(),
                    COLUNA_DO_CONJUNTO: configuracao.conjunto,
                    COLUNA_DO_HORIZONTE: horizonte,
                    "linhas_novas": resultado.linhas_novas,
                    "linhas_do_gabarito": resultado.linhas_do_gabarito,
                    "linhas_so_nas_novas": resultado.linhas_so_nas_novas,
                    "linhas_so_no_gabarito": resultado.linhas_so_no_gabarito,
                    "diferenca_maxima_do_previsto": resultado.diferenca_maxima_do_previsto,
                    "dentro_da_tolerancia": resultado.passou,
                }
            )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DA_COMPARACAO_COM_GABARITO))


def conferir_ancoras_do_ranking(ranking: pd.DataFrame) -> list[dict[str, object]]:
    """Compara o MAE de calibracao (e a posicao, quando fixada) com as ancoras da pre-declaracao.

    Divergencia nao para a etapa: o resultado e relatado (investigar, nunca forcar).

    Args:
        ranking: Saida de `construir_ranking_da_grade`.

    Returns:
        Uma entrada por ancora, com o esperado, o medido e `bate_o_mae` / `bate_a_posicao`.
    """
    entradas: list[dict[str, object]] = []
    for ancora in ANCORAS_DO_RANKING:
        e_da_ancora = (
            (ranking[COLUNA_DO_ALGORITMO] == ancora.algoritmo)
            & (ranking[COLUNA_DA_PERDA] == ancora.perda)
            & (ranking[COLUNA_DO_CONJUNTO] == ancora.conjunto)
        )
        linha = ranking.loc[e_da_ancora]
        mae_medido = float(linha["mae_cal"].iloc[0])
        posicao_medida = int(linha["pos"].iloc[0])
        bate_o_mae = abs(mae_medido - ancora.mae_de_calibracao) < TOLERANCIA_DA_ANCORA_DO_RANKING
        bate_a_posicao = ancora.posicao is None or ancora.posicao == posicao_medida
        entradas.append(
            {
                "algoritmo": ancora.algoritmo,
                "perda": ancora.perda,
                "conjunto": ancora.conjunto,
                "posicao_esperada": ancora.posicao,
                "posicao_medida": posicao_medida,
                "mae_esperado": ancora.mae_de_calibracao,
                "mae_medido": mae_medido,
                "bate_o_mae": bool(bate_o_mae),
                "bate_a_posicao": bool(bate_a_posicao),
            }
        )
    return entradas


def juntar_e_medir(configuracoes: list[ConfiguracaoDaGrade], inicio_da_rodada: float) -> int:
    """Junta os 120 parciais, confere a trava e (so se passar) grava resumo, ranking, comparacao e ancoras.

    Returns:
        0 se a trava passou; 1 se falhou.
    """
    previsoes = juntar_parciais(configuracoes)
    previsoes.to_csv(CAMINHO_DAS_PREVISOES, index=False)

    trava = conferir_trava(previsoes)
    gravar_json_de_forma_atomica({"trava": trava}, CAMINHO_DA_TRAVA)
    if not trava["passou"]:
        REGISTRADOR.registrar(
            "TRAVA FALHOU: a etapa para. previsoes.csv e trava.json gravados para diagnostico; "
            "resumo, ranking e ancoras NAO foram gerados e nenhum resultado deve ser lido."
        )
        return 1

    resumo = resumir_previsoes_da_grade(previsoes, CONFIGURACAO_AVALIACAO.fim_da_calibracao)
    resumo.to_csv(CAMINHO_DO_RESUMO, index=False)
    ranking = construir_ranking_da_grade(resumo)
    ranking.to_csv(CAMINHO_DO_RANKING, index=False)

    comparacao = comparar_com_o_gabarito_antigo(previsoes)
    comparacao.to_csv(CAMINHO_DA_COMPARACAO, index=False)

    ancoras = conferir_ancoras_do_ranking(ranking)
    diferenca_por_algoritmo: dict[str, float] = {}
    for algoritmo in ALGORITMOS_DA_GRADE:
        do_algoritmo = comparacao.loc[comparacao[COLUNA_DO_ALGORITMO] == algoritmo]
        diferenca_por_algoritmo[algoritmo] = float(do_algoritmo["diferenca_maxima_do_previsto"].max())
    gravar_json_de_forma_atomica(
        {
            "ancoras_do_ranking": ancoras,
            "todas_as_ancoras_batem": all(entrada["bate_o_mae"] and entrada["bate_a_posicao"] for entrada in ancoras),
            "diferenca_maxima_contra_o_gabarito_por_algoritmo": diferenca_por_algoritmo,
            "celulas_fora_da_tolerancia_do_gabarito": int((~comparacao["dentro_da_tolerancia"]).sum()),
        },
        CAMINHO_DAS_ANCORAS,
    )

    segundos = time.perf_counter() - inicio_da_rodada
    REGISTRADOR.registrar(
        f"juncao: {len(previsoes)} previsoes; trava OK; ranking: 1o={ranking.loc[0, COLUNA_DO_ALGORITMO]} "
        f"{ranking.loc[0, COLUNA_DA_PERDA]} {ranking.loc[0, COLUNA_DO_CONJUNTO]} mae_cal={ranking.loc[0, 'mae_cal']:.4f}; "
        f"tempo deste processo={segundos:.1f}s"
    )
    return 0


def ler_argumentos() -> argparse.Namespace:
    """Le as fatias (`--algoritmos`, `--perdas`, `--conjuntos`, `--horizontes`) e `--refazer`, `--so-juntar`, `--so-trava`."""
    rotulos_das_perdas = [ROTULO_DA_PERDA_PADRAO]
    for configuracao in montar_as_30_configuracoes():
        if configuracao.rotulo_da_perda() not in rotulos_das_perdas:
            rotulos_das_perdas.append(configuracao.rotulo_da_perda())

    leitor = argparse.ArgumentParser(description="E6b: grade de 30 configuracoes, em pedacos.")
    leitor.add_argument("--algoritmos", nargs="+", choices=ALGORITMOS_DA_GRADE, default=None)
    leitor.add_argument("--perdas", nargs="+", choices=rotulos_das_perdas, default=None)
    leitor.add_argument("--conjuntos", nargs="+", choices=CONJUNTOS_DA_GRADE, default=None)
    leitor.add_argument("--horizontes", nargs="+", type=int, choices=HORIZONTES_DA_GRADE, default=None)
    leitor.add_argument("--refazer", action="store_true", help="Recalcula parciais que ja existem.")
    leitor.add_argument("--so-juntar", action="store_true", help="Nao treina nada: junta os 120 parciais e mede.")
    leitor.add_argument("--so-trava", action="store_true", help="Nao treina nada: confere a trava nos 4 parciais da celula.")
    return leitor.parse_args()


def conferir_so_a_trava() -> int:
    """`--so-trava`: junta os 4 parciais da celula de referencia e confere a trava (nada e gravado alem de `trava.json`).

    Returns:
        0 se passou; 1 se falhou ou faltar parcial.
    """
    configuracoes = [CONFIGURACAO_DA_TRAVA]
    faltantes = listar_parciais_faltantes(configuracoes)
    if faltantes:
        REGISTRADOR.registrar(f"--so-trava: faltam {len(faltantes)} parcial(is) da celula de referencia.")
        return 1
    previsoes = juntar_parciais(configuracoes)
    trava = conferir_trava(previsoes)
    gravar_json_de_forma_atomica({"trava": trava}, CAMINHO_DA_TRAVA)
    REGISTRADOR.registrar(
        f"--so-trava: passou={trava['passou']} diferenca_maxima_do_previsto={trava['diferenca_maxima_do_previsto']}"
    )
    if trava["passou"]:
        return 0
    return 1


def main() -> int:
    """Roda as fatias pedidas e, se os 120 parciais existirem, junta, confere a trava e mede."""
    inicio_da_rodada = time.perf_counter()
    argumentos = ler_argumentos()

    if argumentos.so_trava:
        return conferir_so_a_trava()

    todas_as_configuracoes = montar_as_30_configuracoes()
    if not argumentos.so_juntar:
        configuracoes = selecionar_configuracoes(argumentos.algoritmos, argumentos.perdas, argumentos.conjuntos)
        horizontes = tuple(argumentos.horizontes) if argumentos.horizontes else HORIZONTES_DA_GRADE
        tabela_cortada = carregar_tabela_cortada()
        REGISTRADOR.registrar(f"inicio: {len(configuracoes)} configuracao(oes), horizontes={list(horizontes)}")
        for configuracao in configuracoes:
            for horizonte in horizontes:
                caminho = caminho_do_parcial(configuracao, horizonte)
                if caminho.exists() and not argumentos.refazer:
                    REGISTRADOR.registrar(f"pulado (parcial ja existe): {caminho.name}")
                    continue
                previsoes = rodar_um_pedaco(configuracao, horizonte, tabela_cortada)
                gravar_parcial(previsoes, caminho)

    faltantes = listar_parciais_faltantes(todas_as_configuracoes)
    if faltantes:
        REGISTRADOR.registrar(f"fim do pedaco: faltam {len(faltantes)} de {TOTAL_DE_CELULAS} parciais; juncao adiada.")
        return 0
    return juntar_e_medir(todas_as_configuracoes, inicio_da_rodada)


if __name__ == "__main__":
    sys.exit(main())
