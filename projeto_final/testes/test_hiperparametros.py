"""Testes da E6c: a grade de 18 hiperparametros do HistGB, o criterio da fase 1 e o teste da fase 2.

Tres blocos:
    1. a grade (18, referencia primeiro, nomes do antigo) e a conversao para o `ConfiguracaoModelo` do pacote;
    2. o criterio da fase 1 e a regra de troca da fase 2, em casos pequenos com conta a mao;
    3. DIFERENCIAIS SEM MODELO, sobre as previsoes que o antigo salvou (`e6c_previsoes_por_configuracao.csv`):
       o MAE medio de calibracao das 18 configuracoes e IGUAL ao `ranking_calibracao.csv` do antigo, e a
       comparacao da fase 2 (vencedora x referencia) reproduz `comparacoes.csv` (reducao percentual e p bruto
       e p de Holm, n = 102).
"""

import dataclasses
import pathlib

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingRegressor

from aedes.configuracao import CONFIGURACAO_AVALIACAO, FOLHA_5
from aedes.hiperparametros import (
    NOME_DA_REFERENCIA,
    ComparacaoDaFase2,
    calcular_mae_medio_de_calibracao,
    comparar_vencedora_com_referencia,
    decidir_a_fase_2,
    montar_a_grade_de_18,
    montar_nome_da_configuracao,
    montar_ranking_da_fase_1,
)
from aedes.metricas import recortar_janela_de_avaliacao

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
PASTA_DOS_GABARITOS = PASTA_DO_PROJETO / "testes" / "referencia_antiga"
HORIZONTES = (1, 4, 8, 12)
NOME_DA_VENCEDORA_ANTIGA = "lr0.03_it400_folhas15_min5"


@pytest.fixture(scope="module")
def previsoes_do_antigo() -> pd.DataFrame:
    """As previsoes das 18 configuracoes salvas pelo antigo (coluna `braco` = nome da configuracao)."""
    caminho = PASTA_DOS_GABARITOS / "e6c_previsoes_por_configuracao.csv"
    return pd.read_csv(caminho, parse_dates=["data_alvo"], float_precision="round_trip")


# ---------------------------------------------------------------------------
# 1. A grade
# ---------------------------------------------------------------------------


def test_a_grade_tem_18_configuracoes_unicas_e_a_referencia_vem_primeiro() -> None:
    """3 ritmos x 3 tamanhos de arvore x 2 folhas minimas; a referencia (0,05 x 250, 15, 5) e a primeira."""
    grade = montar_a_grade_de_18()
    assert len(grade) == 18
    nomes = [configuracao.nome for configuracao in grade]
    assert len(set(nomes)) == 18
    assert nomes[0] == NOME_DA_REFERENCIA == "lr0.05_it250_folhas15_min5"


def test_a_grade_cobre_exatamente_as_combinacoes_declaradas() -> None:
    """Ritmos {0,05x250, 0,03x400, 0,10x150}, folhas {15, 7, 31}, folha minima {5, 20}: todas as 18 aparecem."""
    combinacoes_esperadas = set()
    for taxa, iteracoes in ((0.05, 250), (0.03, 400), (0.10, 150)):
        for folhas in (15, 7, 31):
            for folha_minima in (5, 20):
                combinacoes_esperadas.add((taxa, iteracoes, folhas, folha_minima))
    combinacoes_da_grade = set()
    for configuracao in montar_a_grade_de_18():
        combinacoes_da_grade.add(
            (
                configuracao.taxa_de_aprendizado,
                configuracao.numero_de_iteracoes,
                configuracao.maximo_de_folhas,
                configuracao.folha_minima,
            )
        )
    assert combinacoes_da_grade == combinacoes_esperadas


def test_o_nome_da_configuracao_segue_o_formato_do_antigo() -> None:
    """`lr0.1` para a taxa 0,10 (o antigo formatava o float cru), `it150`, `folhas7`, `min20`."""
    assert montar_nome_da_configuracao(0.10, 150, 7, 20) == "lr0.1_it150_folhas7_min20"
    assert montar_nome_da_configuracao(0.03, 400, 15, 5) == "lr0.03_it400_folhas15_min5"


def test_a_configuracao_do_modelo_troca_so_os_quatro_hiperparametros_da_folha_5() -> None:
    """Quantil 0,85, semente 42 e todos os demais campos ficam os da `FOLHA_5`."""
    configuracao = montar_a_grade_de_18()[0]
    assert configuracao.para_configuracao_do_modelo().parametros_do_sklearn() == FOLHA_5.parametros_do_sklearn()

    outra = [c for c in montar_a_grade_de_18() if c.nome == "lr0.1_it150_folhas31_min20"][0]
    modelo = outra.para_configuracao_do_modelo()
    esperado = dataclasses.replace(
        FOLHA_5,
        nome="histgb_lr0.1_it150_folhas31_min20",
        taxa_de_aprendizado=0.10,
        numero_de_iteracoes=150,
        maximo_de_folhas=31,
        folha_minima=20,
    )
    assert modelo == esperado
    assert modelo.quantil == 0.85
    assert modelo.semente_aleatoria == 42


def test_a_configuracao_do_modelo_tem_os_parametros_do_construtor_do_antigo() -> None:
    """Antigo: 7 parametros (max_iter, learning_rate, max_leaf_nodes, min_samples_leaf, random_state, loss, quantile)."""
    antigo = HistGradientBoostingRegressor(
        max_iter=400,
        learning_rate=0.03,
        max_leaf_nodes=7,
        min_samples_leaf=20,
        random_state=42,
        loss="quantile",
        quantile=0.85,
    )
    configuracao = [c for c in montar_a_grade_de_18() if c.nome == "lr0.03_it400_folhas7_min20"][0]
    do_pacote = HistGradientBoostingRegressor(**configuracao.para_configuracao_do_modelo().parametros_do_sklearn())
    assert do_pacote.get_params() == antigo.get_params()


# ---------------------------------------------------------------------------
# 2. Criterio da fase 1 e regra de troca da fase 2
# ---------------------------------------------------------------------------


def test_o_mae_medio_de_calibracao_da_peso_igual_a_cada_horizonte() -> None:
    """h=1: erros 2 e 4 (MAE 3); h=4: erro 9 (MAE 9) -> media dos MAE = 6 (e nao a media de todos os erros, 5)."""
    previsoes = pd.DataFrame(
        {
            "h": [1, 1, 4],
            "real": [10.0, 10.0, 50.0],
            "previsto": [12.0, 6.0, 41.0],
        }
    )
    assert calcular_mae_medio_de_calibracao(previsoes, horizontes=(1, 4)) == 6.0


def test_o_mae_medio_exige_previsao_em_todos_os_horizontes() -> None:
    """Horizonte sem nenhuma previsao: ValueError (nao ignora em silencio)."""
    previsoes = pd.DataFrame({"h": [1], "real": [1.0], "previsto": [2.0]})
    with pytest.raises(ValueError, match="horizonte 4"):
        calcular_mae_medio_de_calibracao(previsoes, horizontes=(1, 4))


def test_o_ranking_da_fase_1_ordena_e_numera_com_desempate_estavel() -> None:
    """Menor MAE primeiro; empate exato mantem a ordem da grade (entrada); `pos` comeca em 1."""
    ranking = montar_ranking_da_fase_1({"b": 5.0, "a": 3.0, "c": 5.0, "d": 4.0})
    assert list(ranking["configuracao"]) == ["a", "d", "b", "c"]
    assert list(ranking["pos"]) == [1, 2, 3, 4]


def test_o_ranking_da_fase_1_vazio_e_erro() -> None:
    """Sem configuracoes, ValueError."""
    with pytest.raises(ValueError):
        montar_ranking_da_fase_1({})


def montar_comparacao(horizonte: int, mae_referencia: float, mae_vencedora: float, p_bruto: float) -> ComparacaoDaFase2:
    """Comparacao sintetica de um horizonte para testar a regra de troca."""
    return ComparacaoDaFase2(
        horizonte=horizonte,
        n_pares=102,
        mae_referencia=mae_referencia,
        mae_vencedora=mae_vencedora,
        reducao_percentual=100.0 * (mae_referencia - mae_vencedora) / mae_referencia,
        r2_referencia=0.5,
        r2_vencedora=0.5,
        p_bruto=p_bruto,
    )


def test_a_vencedora_so_entra_se_reduzir_o_mae_em_h8_e_h12_com_holm_abaixo_de_0_05() -> None:
    """Quatro p brutos 0,001, 0,002, 0,003, 0,004 -> Holm 0,004, 0,006, 0,006, 0,004: troca se h = 8 e 12 reduzem."""
    comparacoes = [
        montar_comparacao(1, 100.0, 110.0, 0.004),
        montar_comparacao(4, 100.0, 90.0, 0.003),
        montar_comparacao(8, 100.0, 80.0, 0.001),
        montar_comparacao(12, 100.0, 70.0, 0.002),
    ]
    decisao = decidir_a_fase_2(comparacoes)
    assert decisao.p_holm[2] == pytest.approx(0.004)  # 4 * 0,001
    assert decisao.p_holm[3] == pytest.approx(0.006)  # 3 * 0,002
    assert decisao.troca_a_referencia is True


def test_nao_troca_se_a_vencedora_piora_em_h12_mesmo_com_p_baixo() -> None:
    """Em h = 12 o MAE da vencedora e MAIOR: `reduziu` falso, nao troca."""
    comparacoes = [
        montar_comparacao(1, 100.0, 90.0, 0.5),
        montar_comparacao(4, 100.0, 90.0, 0.5),
        montar_comparacao(8, 100.0, 80.0, 0.001),
        montar_comparacao(12, 100.0, 101.0, 0.001),
    ]
    assert decidir_a_fase_2(comparacoes).troca_a_referencia is False


def test_nao_troca_se_so_um_dos_horizontes_de_decisao_e_significativo() -> None:
    """h = 8 passa e h = 12 nao passa em Holm: E logico, nao troca."""
    comparacoes = [
        montar_comparacao(1, 100.0, 100.0, 1.0),
        montar_comparacao(4, 100.0, 100.0, 1.0),
        montar_comparacao(8, 100.0, 80.0, 0.001),
        montar_comparacao(12, 100.0, 80.0, 0.30),
    ]
    assert decidir_a_fase_2(comparacoes).troca_a_referencia is False


def test_p_de_holm_exatamente_0_05_nao_troca() -> None:
    """Limite estrito (`< 0,05`): com 4 testes, p bruto 0,0125 em todos da Holm 0,05 -> nao passa."""
    comparacoes = [montar_comparacao(horizonte, 100.0, 80.0, 0.0125) for horizonte in HORIZONTES]
    decisao = decidir_a_fase_2(comparacoes)
    assert decisao.p_holm[2] == pytest.approx(0.05)
    assert decisao.troca_a_referencia is False


def test_a_regra_de_troca_exige_a_comparacao_dos_horizontes_de_decisao() -> None:
    """Sem h = 12 na lista de comparacoes, ValueError (nao decide com informacao faltando)."""
    comparacoes = [montar_comparacao(8, 100.0, 80.0, 0.001)]
    with pytest.raises(ValueError, match="12"):
        decidir_a_fase_2(comparacoes)


def montar_previsoes_para_a_comparacao(erros: list[float], horizonte: int) -> pd.DataFrame:
    """Previsoes de um modelo com `real` 100 e `previsto` = 100 - erro, em semanas consecutivas de 2024."""
    datas = pd.date_range("2024-01-07", periods=len(erros), freq="7D")
    return pd.DataFrame(
        {
            "h": horizonte,
            "data_alvo": datas,
            "real": 100.0,
            "previsto": 100.0 - np.asarray(erros, dtype=float),
        }
    )


def test_erros_identicos_da_p_igual_a_1_sem_chamar_o_wilcoxon() -> None:
    """Regra do antigo: se os vetores de erro sao `allclose`, p = 1,0 (o Wilcoxon exigiria diferencas)."""
    referencia = montar_previsoes_para_a_comparacao([1.0, 2.0, 3.0, 4.0], 8)
    vencedora = montar_previsoes_para_a_comparacao([1.0, 2.0, 3.0, 4.0], 8)
    comparacao = comparar_vencedora_com_referencia(referencia, vencedora, 8)
    assert comparacao.p_bruto == 1.0
    assert comparacao.reducao_percentual == 0.0
    assert comparacao.n_pares == 4


def test_so_as_semanas_em_comum_entram_na_comparacao_pareada() -> None:
    """A vencedora tem uma semana a menos: n_pares = 3, e o MAE de cada lado e calculado so nessas 3."""
    referencia = montar_previsoes_para_a_comparacao([10.0, 20.0, 30.0, 40.0], 12)
    vencedora = montar_previsoes_para_a_comparacao([5.0, 10.0, 15.0, 20.0], 12).iloc[:3]
    comparacao = comparar_vencedora_com_referencia(referencia, vencedora, 12)
    assert comparacao.n_pares == 3
    assert comparacao.mae_referencia == 20.0
    assert comparacao.mae_vencedora == 10.0
    assert comparacao.reducao_percentual == 50.0


def test_a_comparacao_ignora_outros_horizontes_e_rejeita_data_repetida() -> None:
    """Filtra pelo horizonte pedido; data_alvo repetida em um lado e erro."""
    referencia = pd.concat(
        [montar_previsoes_para_a_comparacao([1.0, 2.0], 8), montar_previsoes_para_a_comparacao([100.0, 200.0], 12)]
    )
    vencedora = pd.concat(
        [montar_previsoes_para_a_comparacao([1.0, 2.0], 8), montar_previsoes_para_a_comparacao([50.0, 60.0], 12)]
    )
    assert comparar_vencedora_com_referencia(referencia, vencedora, 8).mae_referencia == 1.5
    repetida = pd.concat([vencedora, vencedora.iloc[:1]])
    with pytest.raises(ValueError, match="repetida"):
        comparar_vencedora_com_referencia(referencia, repetida, 8)


def test_nenhuma_semana_em_comum_e_erro() -> None:
    """Sem intersecao de `data_alvo`, ValueError."""
    referencia = montar_previsoes_para_a_comparacao([1.0, 2.0], 8)
    vencedora = montar_previsoes_para_a_comparacao([1.0, 2.0], 8)
    vencedora["data_alvo"] = vencedora["data_alvo"] + pd.Timedelta(weeks=100)
    with pytest.raises(ValueError, match="Nenhuma semana em comum"):
        comparar_vencedora_com_referencia(referencia, vencedora, 8)


# ---------------------------------------------------------------------------
# 3. Diferenciais sem modelo sobre as previsoes salvas pelo antigo
# ---------------------------------------------------------------------------


def test_o_mae_medio_de_calibracao_das_18_reproduz_o_ranking_do_antigo(previsoes_do_antigo: pd.DataFrame) -> None:
    """Para cada configuracao: MAE medio dos 4 horizontes com `data_alvo <= 2023-12-31` == `ranking_calibracao.csv`, < 1e-9."""
    ranking_antigo = pd.read_csv(PASTA_DOS_GABARITOS / "e6c_ranking_calibracao.csv")
    mae_antigo_por_nome = dict(zip(ranking_antigo["configuracao"], ranking_antigo["mae_calibracao"]))
    assert len(mae_antigo_por_nome) == 18

    fim_da_calibracao = CONFIGURACAO_AVALIACAO.fim_da_calibracao
    maes_novos: dict[str, float] = {}
    for configuracao in montar_a_grade_de_18():
        da_configuracao = previsoes_do_antigo.loc[previsoes_do_antigo["braco"] == configuracao.nome]
        na_calibracao = da_configuracao.loc[da_configuracao["data_alvo"] <= fim_da_calibracao]
        maes_novos[configuracao.nome] = calcular_mae_medio_de_calibracao(na_calibracao)
        assert maes_novos[configuracao.nome] == pytest.approx(mae_antigo_por_nome[configuracao.nome], abs=1e-9)

    ranking_novo = montar_ranking_da_fase_1(maes_novos)
    assert ranking_novo["configuracao"].iloc[0] == NOME_DA_VENCEDORA_ANTIGA
    assert round(float(ranking_novo["mae_calibracao"].iloc[0]), 2) == 41.66
    posicao_da_referencia = int(ranking_novo.loc[ranking_novo["configuracao"] == NOME_DA_REFERENCIA, "pos"].iloc[0])
    assert posicao_da_referencia == 4
    assert round(maes_novos[NOME_DA_REFERENCIA], 2) == 42.02


def test_as_9_configuracoes_de_folha_minima_20_ficam_do_10o_ao_18o_lugar_entre_54_68_e_55_69(
    previsoes_do_antigo: pd.DataFrame,
) -> None:
    """Ancora da pre-declaracao: folha minima 20 = posicoes 10 a 18, MAE de calibracao entre 54,68 e 55,69."""
    fim_da_calibracao = CONFIGURACAO_AVALIACAO.fim_da_calibracao
    maes: dict[str, float] = {}
    for configuracao in montar_a_grade_de_18():
        da_configuracao = previsoes_do_antigo.loc[previsoes_do_antigo["braco"] == configuracao.nome]
        na_calibracao = da_configuracao.loc[da_configuracao["data_alvo"] <= fim_da_calibracao]
        maes[configuracao.nome] = calcular_mae_medio_de_calibracao(na_calibracao)
    ranking = montar_ranking_da_fase_1(maes)
    nomes_da_folha_20 = [c.nome for c in montar_a_grade_de_18() if c.folha_minima == 20]
    da_folha_20 = ranking.loc[ranking["configuracao"].isin(nomes_da_folha_20)]
    assert sorted(da_folha_20["pos"]) == list(range(10, 19))
    assert round(float(da_folha_20["mae_calibracao"].min()), 2) == 54.68
    assert round(float(da_folha_20["mae_calibracao"].max()), 2) == 55.69


def test_a_fase_2_da_vencedora_antiga_reproduz_as_comparacoes_salvas_pelo_antigo(
    previsoes_do_antigo: pd.DataFrame,
) -> None:
    """Wilcoxon + Holm sobre as previsoes do antigo: reducao percentual, p bruto e p de Holm == `comparacoes.csv`, n = 102."""
    comparacoes_antigas = pd.read_csv(PASTA_DOS_GABARITOS / "e6c_comparacoes.csv")
    previsoes_na_janela = recortar_janela_de_avaliacao(previsoes_do_antigo, CONFIGURACAO_AVALIACAO)
    da_referencia = previsoes_na_janela.loc[previsoes_na_janela["braco"] == NOME_DA_REFERENCIA]
    da_vencedora = previsoes_na_janela.loc[previsoes_na_janela["braco"] == NOME_DA_VENCEDORA_ANTIGA]

    comparacoes_novas = []
    for horizonte in HORIZONTES:
        comparacoes_novas.append(comparar_vencedora_com_referencia(da_referencia, da_vencedora, horizonte))
    decisao = decidir_a_fase_2(comparacoes_novas)

    for comparacao, p_holm in zip(decisao.comparacoes, decisao.p_holm):
        antiga = comparacoes_antigas.loc[comparacoes_antigas["h"] == comparacao.horizonte].iloc[0]
        assert comparacao.n_pares == int(antiga["semanas_pareadas"]) == 102
        assert comparacao.mae_referencia == pytest.approx(antiga["mae_referencia"], abs=1e-9)
        assert comparacao.mae_vencedora == pytest.approx(antiga["mae_variante"], abs=1e-9)
        assert comparacao.reducao_percentual == pytest.approx(antiga["reducao_percentual"], abs=1e-9)
        assert comparacao.r2_referencia == pytest.approx(antiga["r2_referencia"], abs=1e-9)
        assert comparacao.r2_vencedora == pytest.approx(antiga["r2_variante"], abs=1e-9)
        assert comparacao.p_bruto == pytest.approx(antiga["p_bruto"], abs=1e-9)
        assert p_holm == pytest.approx(antiga["p_holm"], abs=1e-9)
    assert decisao.troca_a_referencia is False
