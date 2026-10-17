"""Testes da fiacao dos scripts E6a, E6b, E6c e E7, SEM treinar nenhum modelo da etapa.

Os scripts fazem tres coisas alem de treinar: gravar parciais, juntar e conferir travas. Aqui os parciais sao
FABRICADOS a partir da referencia certificada (`resultados/referencia/previsoes.csv`) e das previsoes salvas pelo
antigo (`testes/referencia_antiga/`), em pastas temporarias, e se confere:
    - E6a: o script roda de ponta a ponta (segundos) e grava os ganhos e o resumo, em pasta temporaria;
    - E6b/E6c/E7: nomes e fatiamento dos parciais; a juncao com a trava aprovada grava as saidas; a trava REPROVA
      quando uma celula muda 1e-3 (e a etapa para, sem gravar o ranking ou o WIS); a fase 2 da E6c decide a troca;
    - as ancoras do ranking da E6b reconhecem o ranking calculado das previsoes do antigo.

Nenhum arquivo do projeto e escrito: tudo vai para `tmp_path`.
"""

import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd
import pytest

import experimentos.e6a_clima as e6a
import experimentos.e6b_grade30 as e6b
import experimentos.e6c_grade18 as e6c
import experimentos.e7_wis as e7
from aedes.configuracao import CONFIGURACAO_AVALIACAO
from aedes.grade import (
    ALGORITMO_HISTGB,
    CONJUNTO_M1,
    ConfiguracaoDaGrade,
    construir_ranking_da_grade,
    montar_as_30_configuracoes,
    resumir_previsoes_da_grade,
)
from aedes.hiperparametros import NOME_DA_REFERENCIA, montar_a_grade_de_18, montar_ranking_da_fase_1
from aedes.quantis import QUANTIS_DO_WIS
from experimentos.comum_reproducao import RegistradorDeLog, ler_previsoes_da_referencia

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
PASTA_DOS_GABARITOS = PASTA_DO_PROJETO / "testes" / "referencia_antiga"
HORIZONTES_DA_BUSCA = (1, 4, 8, 12)
NOME_DA_VENCEDORA_ANTIGA = "lr0.03_it400_folhas15_min5"


@pytest.fixture(scope="module")
def referencia() -> pd.DataFrame:
    """As previsoes certificadas do ciclo 3 (folha 5 = `referencia`, folha 20 = `HistGB_folha20_M1`)."""
    return ler_previsoes_da_referencia()


def da_referencia(referencia: pd.DataFrame, folha: int, horizonte: int) -> pd.DataFrame:
    """Linhas da referencia de uma folha e um horizonte, so com as colunas dos parciais."""
    nome_do_braco = {5: "referencia", 20: "HistGB_folha20_M1"}[folha]
    do_braco = referencia["braco"] == nome_do_braco
    do_horizonte = referencia["h"] == horizonte
    return referencia.loc[do_braco & do_horizonte, ["h", "data_origem", "data_alvo", "real", "previsto"]].copy()


# ---------------------------------------------------------------------------
# E6a
# ---------------------------------------------------------------------------


def test_e6a_roda_de_ponta_a_ponta_em_pasta_temporaria(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """3 variantes: grava `ganho_<variante>.csv` (42 candidatas) e `resumo.json`; devolve 0; nada vai para `resultados/`."""
    pasta_de_saida = tmp_path / "e6a"
    monkeypatch.setattr(sys, "argv", ["e6a_clima", "--saida", str(pasta_de_saida)])
    assert e6a.main() == 0

    for nome_da_variante in e6a.VARIANTES:
        ganhos = pd.read_csv(pasta_de_saida / f"ganho_{nome_da_variante}.csv")
        assert len(ganhos) == 42
        assert list(ganhos["posicao"]) == list(range(1, 43))
        assert ganhos["ganho_total"].is_monotonic_decreasing
        assert list(ganhos.columns) == ["posicao", "candidata", "ganho_h1", "ganho_h4", "ganho_h8", "ganho_total"]

    with open(pasta_de_saida / "resumo.json", encoding="utf-8") as arquivo:
        resumo = json.load(arquivo)
    assert list(resumo["variantes"]) == list(e6a.VARIANTES)
    for variante in resumo["variantes"].values():
        assert len(variante["escolhidas"]) == 6
        assert set(variante["margem_entre_a_6a_e_a_7a"]) >= {"ultima_escolhida", "proxima", "diferenca"}
        assert variante["linhas_de_treino_por_horizonte"]["1"] == int(variante["linhas_validas_por_horizonte"]["1"] * 0.6)
    assert (pasta_de_saida / "E6a_clima.log").exists()


def test_o_clima_do_artigo_tem_6_nomes_na_ordem_do_ranking_antigo() -> None:
    """A lista de comparacao vem do pacote (`CONFIGURACAO_VARIAVEIS`), nao escrita a mao no script."""
    assert e6a.listar_o_clima_do_artigo() == [
        "temp_media_lag4",
        "umid_media",
        "temp_media_lag3",
        "temp_max",
        "pressao_media_lag3",
        "pressao_media_lag4",
    ]


# ---------------------------------------------------------------------------
# E6b
# ---------------------------------------------------------------------------


@pytest.fixture
def e6b_com_pastas_temporarias(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Aponta os caminhos de saida da E6b para `tmp_path`."""
    pasta_de_saida = tmp_path / "E6b_grade30"
    monkeypatch.setattr(e6b, "PASTA_DE_SAIDA", pasta_de_saida)
    monkeypatch.setattr(e6b, "PASTA_DOS_PARCIAIS", pasta_de_saida / "parciais")
    monkeypatch.setattr(e6b, "CAMINHO_DAS_PREVISOES", pasta_de_saida / "previsoes.csv")
    monkeypatch.setattr(e6b, "CAMINHO_DO_RESUMO", pasta_de_saida / "resumo.csv")
    monkeypatch.setattr(e6b, "CAMINHO_DO_RANKING", pasta_de_saida / "ranking.csv")
    monkeypatch.setattr(e6b, "CAMINHO_DA_COMPARACAO", pasta_de_saida / "comparacao_com_gabarito.csv")
    monkeypatch.setattr(e6b, "CAMINHO_DAS_ANCORAS", pasta_de_saida / "ancoras.json")
    monkeypatch.setattr(e6b, "CAMINHO_DA_TRAVA", pasta_de_saida / "trava.json")
    monkeypatch.setattr(e6b, "REGISTRADOR", RegistradorDeLog(pasta_de_saida / "E6b_grade30.log"))
    return pasta_de_saida


def gravar_parciais_da_e6b(referencia: pd.DataFrame, mudar_uma_celula_da_trava: bool) -> None:
    """Grava os 120 parciais: a celula de referencia = referencia TRUNCADA em zero; as demais = referencia deslocada.

    Cada configuracao recebe um deslocamento proprio (`indice * 0,5`), so para o ranking ter uma ordem.
    """
    e6b.PASTA_DOS_PARCIAIS.mkdir(parents=True, exist_ok=True)
    for indice, configuracao in enumerate(montar_as_30_configuracoes()):
        for horizonte in HORIZONTES_DA_BUSCA:
            parcial = da_referencia(referencia, 5, horizonte)
            parcial["previsto"] = np.maximum(parcial["previsto"], 0.0)
            e_a_celula_da_trava = (
                configuracao.algoritmo == ALGORITMO_HISTGB
                and configuracao.quantil == 0.85
                and configuracao.conjunto == CONJUNTO_M1
            )
            if not e_a_celula_da_trava:
                parcial["previsto"] = parcial["previsto"] + indice * 0.5
            elif mudar_uma_celula_da_trava and horizonte == 4:
                parcial.loc[parcial.index[50], "previsto"] += 1e-3
            parcial.insert(0, "conjunto", configuracao.conjunto)
            parcial.insert(0, "perda", configuracao.rotulo_da_perda())
            parcial.insert(0, "algoritmo", configuracao.algoritmo)
            parcial.to_csv(e6b.caminho_do_parcial(configuracao, horizonte), index=False)


def test_e6b_o_nome_do_parcial_e_a_selecao_de_fatias(e6b_com_pastas_temporarias: pathlib.Path) -> None:
    """Nome `previsoes_<algoritmo>_<perda>_<conjunto>_h<hh>.csv`; as fatias filtram algoritmo, perda e conjunto."""
    configuracao = ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1)
    assert e6b.caminho_do_parcial(configuracao, 4).name == "previsoes_hist_gradient_boosting_quantil_0.85_M1_com_vetor_h04.csv"
    todas = e6b.selecionar_configuracoes(None, None, None)
    assert len(todas) == 30
    so_a_referencia = e6b.selecionar_configuracoes([ALGORITMO_HISTGB], ["quantil_0.85"], [CONJUNTO_M1])
    assert [c.rotulo() for c in so_a_referencia] == ["hist_gradient_boosting|quantil_0.85|M1_com_vetor"]
    so_a_perda_padrao = e6b.selecionar_configuracoes(None, ["padrao"], None)
    assert len(so_a_perda_padrao) == 6
    assert len(e6b.listar_parciais_faltantes(todas)) == 120


def test_e6b_juntar_e_medir_com_trava_aprovada_grava_resumo_ranking_comparacao_e_ancoras(
    e6b_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """120 parciais fabricados: saida 0, trava aprovada, resumo de 240 linhas, ranking de 30 e comparacao de 120 celulas."""
    gravar_parciais_da_e6b(referencia, mudar_uma_celula_da_trava=False)
    assert e6b.listar_parciais_faltantes(montar_as_30_configuracoes()) == []

    assert e6b.juntar_e_medir(montar_as_30_configuracoes(), time.perf_counter()) == 0

    with open(e6b.CAMINHO_DA_TRAVA, encoding="utf-8") as arquivo:
        trava = json.load(arquivo)["trava"]
    assert trava["passou"] is True
    linhas_da_referencia_nos_4_horizontes = int(
        ((referencia["braco"] == "referencia") & referencia["h"].isin(HORIZONTES_DA_BUSCA)).sum()
    )
    assert trava["linhas_em_comum"] == linhas_da_referencia_nos_4_horizontes

    assert len(pd.read_csv(e6b.CAMINHO_DO_RESUMO)) == 240
    ranking = pd.read_csv(e6b.CAMINHO_DO_RANKING)
    assert len(ranking) == 30
    assert ranking["pos"].tolist() == list(range(1, 31))
    comparacao = pd.read_csv(e6b.CAMINHO_DA_COMPARACAO)
    assert len(comparacao) == 120
    with open(e6b.CAMINHO_DAS_ANCORAS, encoding="utf-8") as arquivo:
        ancoras = json.load(arquivo)
    assert len(ancoras["ancoras_do_ranking"]) == 7
    assert set(ancoras["diferenca_maxima_contra_o_gabarito_por_algoritmo"]) == {
        "hist_gradient_boosting",
        "gradient_boosting",
        "lightgbm",
    }


def test_e6b_a_trava_reprova_se_uma_previsao_da_celula_de_referencia_muda_1e_3_e_a_etapa_para(
    e6b_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """Uma previsao da celula HistGB q0,85 M1 (h = 4) com +1e-3: saida 1, `trava.json` reprovado, SEM resumo nem ranking."""
    gravar_parciais_da_e6b(referencia, mudar_uma_celula_da_trava=True)

    assert e6b.juntar_e_medir(montar_as_30_configuracoes(), time.perf_counter()) == 1

    with open(e6b.CAMINHO_DA_TRAVA, encoding="utf-8") as arquivo:
        trava = json.load(arquivo)["trava"]
    assert trava["passou"] is False
    assert trava["diferenca_maxima_do_previsto"] == pytest.approx(1e-3, rel=1e-6)
    assert e6b.CAMINHO_DAS_PREVISOES.exists()
    assert not e6b.CAMINHO_DO_RESUMO.exists()
    assert not e6b.CAMINHO_DO_RANKING.exists()
    assert not e6b.CAMINHO_DAS_ANCORAS.exists()


def test_e6b_so_trava_confere_so_os_4_parciais_da_celula(
    e6b_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """Sem os parciais: saida 1. Com so os 4 da celula de referencia: saida 0."""
    assert e6b.conferir_so_a_trava() == 1
    gravar_parciais_da_e6b(referencia, mudar_uma_celula_da_trava=False)
    for configuracao in montar_as_30_configuracoes():
        e_a_celula = (
            configuracao.algoritmo == ALGORITMO_HISTGB and configuracao.quantil == 0.85 and configuracao.conjunto == CONJUNTO_M1
        )
        if not e_a_celula:
            for horizonte in HORIZONTES_DA_BUSCA:
                e6b.caminho_do_parcial(configuracao, horizonte).unlink()
    assert e6b.conferir_so_a_trava() == 0


def previsoes_do_antigo_no_formato_da_e6b() -> pd.DataFrame:
    """As 35.490 previsoes salvas pelo antigo, com `previsto` e `data_origem` (= `data_alvo - h semanas`)."""
    tabelas = []
    for sufixo in ("parciais", "padrao", "restante"):
        caminho = PASTA_DOS_GABARITOS / f"e6b_corrigido_previsoes_{sufixo}.csv"
        tabelas.append(pd.read_csv(caminho, parse_dates=["data_alvo"], float_precision="round_trip"))
    juntas = pd.concat(tabelas, ignore_index=True).rename(columns={"pred": "previsto"})
    juntas["data_origem"] = juntas["data_alvo"] - juntas["h"] * pd.Timedelta(weeks=1)
    return juntas[["algoritmo", "perda", "conjunto", "h", "data_origem", "data_alvo", "real", "previsto"]]


def test_e6b_as_ancoras_reconhecem_o_ranking_das_previsoes_do_antigo() -> None:
    """As 7 ancoras (MAE e posicao) batem quando o ranking vem das previsoes salvas pelo antigo."""
    antigo = previsoes_do_antigo_no_formato_da_e6b()
    ranking = construir_ranking_da_grade(resumir_previsoes_da_grade(antigo, CONFIGURACAO_AVALIACAO.fim_da_calibracao))
    entradas = e6b.conferir_ancoras_do_ranking(ranking)
    assert len(entradas) == 7
    for entrada in entradas:
        assert entrada["bate_o_mae"] is True, entrada
        assert entrada["bate_a_posicao"] is True, entrada


def test_e6b_as_ancoras_reprovam_um_ranking_diferente() -> None:
    """Somando 5 casos ao previsto de TODAS as celulas do antigo, o MAE do 1o muda e a ancora de 42,02 deixa de bater."""
    antigo = previsoes_do_antigo_no_formato_da_e6b()
    antigo["previsto"] = antigo["previsto"] + 5.0
    ranking = construir_ranking_da_grade(resumir_previsoes_da_grade(antigo, CONFIGURACAO_AVALIACAO.fim_da_calibracao))
    entradas = e6b.conferir_ancoras_do_ranking(ranking)
    assert any(entrada["bate_o_mae"] is False for entrada in entradas)


def test_e6b_a_comparacao_com_o_gabarito_do_antigo_da_zero_para_as_proprias_previsoes_do_antigo() -> None:
    """As previsoes do antigo comparadas com elas mesmas: 120 celulas, diferenca maxima 0, todas dentro da tolerancia."""
    antigo = previsoes_do_antigo_no_formato_da_e6b()
    comparacao = e6b.comparar_com_o_gabarito_antigo(antigo)
    assert len(comparacao) == 120
    assert (comparacao["diferenca_maxima_do_previsto"] == 0.0).all()
    assert comparacao["dentro_da_tolerancia"].all()
    assert (comparacao["linhas_so_nas_novas"] == 0).all()
    assert (comparacao["linhas_so_no_gabarito"] == 0).all()


def test_e6b_a_comparacao_com_o_gabarito_do_antigo_detecta_uma_celula_mudada() -> None:
    """+1e-3 em uma previsao do LightGBM: so essa celula sai da tolerancia e a diferenca maxima e 1e-3."""
    antigo = previsoes_do_antigo_no_formato_da_e6b()
    e_do_lightgbm = (antigo["algoritmo"] == "lightgbm") & (antigo["h"] == 8)
    linha = antigo.index[e_do_lightgbm][10]
    antigo.loc[linha, "previsto"] += 1e-3
    comparacao = e6b.comparar_com_o_gabarito_antigo(antigo)
    assert int((~comparacao["dentro_da_tolerancia"]).sum()) == 1
    assert comparacao["diferenca_maxima_do_previsto"].max() == pytest.approx(1e-3, rel=1e-6)


# ---------------------------------------------------------------------------
# E6c
# ---------------------------------------------------------------------------


@pytest.fixture
def e6c_com_pastas_temporarias(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Aponta os caminhos de saida da E6c para `tmp_path`."""
    pasta_de_saida = tmp_path / "E6c_grade18"
    monkeypatch.setattr(e6c, "PASTA_DE_SAIDA", pasta_de_saida)
    monkeypatch.setattr(e6c, "PASTA_DOS_PARCIAIS_DA_FASE_1", pasta_de_saida / "parciais")
    monkeypatch.setattr(e6c, "PASTA_DOS_PARCIAIS_DA_FASE_2", pasta_de_saida / "parciais_fase2")
    monkeypatch.setattr(e6c, "CAMINHO_DAS_PREVISOES_DA_FASE_1", pasta_de_saida / "previsoes_fase1.csv")
    monkeypatch.setattr(e6c, "CAMINHO_DO_RANKING", pasta_de_saida / "ranking.csv")
    monkeypatch.setattr(e6c, "CAMINHO_DA_TRAVA", pasta_de_saida / "trava.json")
    monkeypatch.setattr(e6c, "CAMINHO_DAS_ANCORAS", pasta_de_saida / "ancoras.json")
    monkeypatch.setattr(e6c, "CAMINHO_DA_DECISAO", pasta_de_saida / "decisao.json")
    monkeypatch.setattr(e6c, "CAMINHO_DA_FASE_2", pasta_de_saida / "fase2.csv")
    monkeypatch.setattr(e6c, "REGISTRADOR", RegistradorDeLog(pasta_de_saida / "E6c_grade18.log"))
    return pasta_de_saida


def gravar_parciais_da_fase_1(referencia: pd.DataFrame, mudar_uma_celula_da_referencia: bool) -> dict[str, float]:
    """Grava os 72 parciais da fase 1: so as semanas da calibracao; a referencia = certificada; as outras deslocadas.

    Returns:
        O deslocamento de cada configuracao (a referencia tem 0), para o teste saber quem deve vencer.
    """
    e6c.PASTA_DOS_PARCIAIS_DA_FASE_1.mkdir(parents=True, exist_ok=True)
    deslocamentos: dict[str, float] = {}
    for indice, configuracao in enumerate(montar_a_grade_de_18()):
        deslocamento = 0.0 if configuracao.nome == NOME_DA_REFERENCIA else 0.4 * indice
        deslocamentos[configuracao.nome] = deslocamento
        for horizonte in HORIZONTES_DA_BUSCA:
            parcial = da_referencia(referencia, 5, horizonte)
            parcial = parcial.loc[parcial["data_alvo"] <= CONFIGURACAO_AVALIACAO.fim_da_calibracao].copy()
            parcial["previsto"] = parcial["previsto"] + deslocamento
            if mudar_uma_celula_da_referencia and configuracao.nome == NOME_DA_REFERENCIA and horizonte == 8:
                parcial.loc[parcial.index[20], "previsto"] += 1e-3
            parcial.insert(0, "configuracao", configuracao.nome)
            parcial.to_csv(e6c.caminho_do_parcial_da_fase_1(configuracao.nome, horizonte), index=False)
    return deslocamentos


def test_e6c_nome_dos_parciais_e_contagem_da_fase_1(e6c_com_pastas_temporarias: pathlib.Path) -> None:
    """Fase 1: `fase1_<configuracao>_h<hh>.csv`; sao 72; fase 2: `<configuracao>_h<hh>.csv` em outra pasta."""
    assert e6c.caminho_do_parcial_da_fase_1(NOME_DA_REFERENCIA, 4).name == "fase1_lr0.05_it250_folhas15_min5_h04.csv"
    assert e6c.caminho_do_parcial_da_fase_2(NOME_DA_REFERENCIA, 4).parent.name == "parciais_fase2"
    assert len(e6c.listar_parciais_faltantes_da_fase_1()) == 72
    assert e6c.encontrar_configuracao(NOME_DA_VENCEDORA_ANTIGA).folha_minima == 5
    with pytest.raises(ValueError):
        e6c.encontrar_configuracao("lr9_it9_folhas9_min9")


def test_e6c_juntar_e_decidir_a_fase_1_com_trava_aprovada(
    e6c_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """72 parciais: a trava passa; a vencedora e a de menor MAE de calibracao (a referencia e a unica sem deslocamento)."""
    gravar_parciais_da_fase_1(referencia, mudar_uma_celula_da_referencia=False)
    assert e6c.juntar_e_decidir_a_fase_1(time.perf_counter()) == 0

    with open(e6c.CAMINHO_DA_TRAVA, encoding="utf-8") as arquivo:
        assert json.load(arquivo)["trava_1"]["passou"] is True
    ranking = pd.read_csv(e6c.CAMINHO_DO_RANKING)
    assert len(ranking) == 18
    assert ranking["pos"].tolist() == list(range(1, 19))
    assert ranking["mae_calibracao"].is_monotonic_increasing

    with open(e6c.CAMINHO_DA_DECISAO, encoding="utf-8") as arquivo:
        decisao = json.load(arquivo)
    assert decisao["vencedora_da_fase_1"] == ranking["configuracao"].iloc[0]
    assert decisao["troca_a_referencia"] is False
    assert "NAO muda" in decisao["nota"]
    with open(e6c.CAMINHO_DAS_ANCORAS, encoding="utf-8") as arquivo:
        ancoras = json.load(arquivo)
    assert ancoras["posicao_da_referencia_medida"] == int(
        ranking.loc[ranking["configuracao"] == NOME_DA_REFERENCIA, "pos"].iloc[0]
    )


def test_e6c_a_trava_1_reprova_se_a_referencia_muda_1e_3_e_a_etapa_para(
    e6c_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """+1e-3 numa previsao da referencia (h = 8): saida 1, sem ranking nem decisao."""
    gravar_parciais_da_fase_1(referencia, mudar_uma_celula_da_referencia=True)
    assert e6c.juntar_e_decidir_a_fase_1(time.perf_counter()) == 1
    with open(e6c.CAMINHO_DA_TRAVA, encoding="utf-8") as arquivo:
        assert json.load(arquivo)["trava_1"]["passou"] is False
    assert not e6c.CAMINHO_DO_RANKING.exists()
    assert not e6c.CAMINHO_DA_DECISAO.exists()


def test_e6c_a_fase_2_exige_a_fase_1_decidida(e6c_com_pastas_temporarias: pathlib.Path) -> None:
    """Sem `decisao.json`, `rodar_a_fase_2` levanta FileNotFoundError (nao roda nada)."""
    with pytest.raises(FileNotFoundError, match="decisao.json"):
        e6c.rodar_a_fase_2((1,), refazer=False)


def test_e6c_se_a_referencia_venceu_nao_ha_fase_2(e6c_com_pastas_temporarias: pathlib.Path) -> None:
    """Vencedora = referencia: a fase 2 devolve 0 sem treinar e sem gravar `fase2.csv`."""
    e6c_com_pastas_temporarias.mkdir(parents=True, exist_ok=True)
    e6c.CAMINHO_DA_DECISAO.write_text(json.dumps({"vencedora_da_fase_1": NOME_DA_REFERENCIA}), encoding="utf-8")
    assert e6c.rodar_a_fase_2(HORIZONTES_DA_BUSCA, refazer=False) == 0
    assert not e6c.CAMINHO_DA_FASE_2.exists()


def gravar_parciais_da_fase_2(referencia: pd.DataFrame, vencedora: str, fator_da_vencedora: float) -> None:
    """Parciais da fase 2: referencia = certificada (todas as origens); vencedora = previsto * fator."""
    e6c.PASTA_DOS_PARCIAIS_DA_FASE_2.mkdir(parents=True, exist_ok=True)
    for horizonte in HORIZONTES_DA_BUSCA:
        da_ref = da_referencia(referencia, 5, horizonte)
        da_ref.insert(0, "configuracao", NOME_DA_REFERENCIA)
        da_ref.to_csv(e6c.caminho_do_parcial_da_fase_2(NOME_DA_REFERENCIA, horizonte), index=False)
        da_vencedora = da_referencia(referencia, 5, horizonte)
        da_vencedora["previsto"] = da_vencedora["real"] + (da_vencedora["previsto"] - da_vencedora["real"]) * fator_da_vencedora
        da_vencedora.insert(0, "configuracao", vencedora)
        da_vencedora.to_csv(e6c.caminho_do_parcial_da_fase_2(vencedora, horizonte), index=False)


def preparar_a_fase_2(
    referencia: pd.DataFrame, fator_da_vencedora: float, nome_da_vencedora: str
) -> None:
    """Escreve o `trava.json` (com a trava 1) e a `decisao.json` da fase 1 e os 8 parciais da fase 2."""
    e6c.CAMINHO_DA_TRAVA.parent.mkdir(parents=True, exist_ok=True)
    e6c.CAMINHO_DA_TRAVA.write_text(json.dumps({"trava_1": {"passou": True}}), encoding="utf-8")
    e6c.CAMINHO_DA_DECISAO.write_text(
        json.dumps({"vencedora_da_fase_1": nome_da_vencedora, "nota": "x"}), encoding="utf-8"
    )
    gravar_parciais_da_fase_2(referencia, nome_da_vencedora, fator_da_vencedora)


def test_e6c_fase_2_a_vencedora_com_erro_metade_em_todos_os_horizontes_troca_a_referencia(
    e6c_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """Vencedora com o erro da referencia pela metade em todas as semanas: MAE cai em h = 8 e 12 e Holm < 0,05 -> troca (documentada)."""
    preparar_a_fase_2(referencia, 0.5, NOME_DA_VENCEDORA_ANTIGA)
    assert e6c.rodar_a_fase_2(HORIZONTES_DA_BUSCA, refazer=False) == 0

    fase_2 = pd.read_csv(e6c.CAMINHO_DA_FASE_2)
    assert list(fase_2["horizonte"]) == list(HORIZONTES_DA_BUSCA)
    assert (fase_2["n_pares"] == 102).all()
    assert (fase_2["reducao_percentual"] > 30.0).all()
    assert (fase_2["p_holm"] < 0.05).all()
    with open(e6c.CAMINHO_DA_DECISAO, encoding="utf-8") as arquivo:
        decisao = json.load(arquivo)
    assert decisao["fase_2"] == "realizada"
    assert decisao["troca_a_referencia"] is True
    assert "NAO muda" in decisao["nota"]
    with open(e6c.CAMINHO_DA_TRAVA, encoding="utf-8") as arquivo:
        trava = json.load(arquivo)
    assert trava["trava_2"]["passou"] is True


def test_e6c_fase_2_a_vencedora_identica_a_referencia_nao_troca(
    e6c_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """Vencedora com as mesmas previsoes (fator 1): p = 1,0 em todos os horizontes, nao troca."""
    preparar_a_fase_2(referencia, 1.0, NOME_DA_VENCEDORA_ANTIGA)
    assert e6c.rodar_a_fase_2(HORIZONTES_DA_BUSCA, refazer=False) == 0
    fase_2 = pd.read_csv(e6c.CAMINHO_DA_FASE_2)
    assert (fase_2["p_bruto"] == 1.0).all()
    with open(e6c.CAMINHO_DA_DECISAO, encoding="utf-8") as arquivo:
        assert json.load(arquivo)["troca_a_referencia"] is False


def test_e6c_a_trava_2_reprova_se_a_referencia_da_fase_2_nao_e_a_certificada(
    e6c_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """Uma previsao da referencia (h = 12) +1e-3: saida 1 e `fase2.csv` nao e gerado."""
    preparar_a_fase_2(referencia, 0.5, NOME_DA_VENCEDORA_ANTIGA)
    caminho = e6c.caminho_do_parcial_da_fase_2(NOME_DA_REFERENCIA, 12)
    parcial = pd.read_csv(caminho)
    parcial.loc[parcial.index[30], "previsto"] += 1e-3
    parcial.to_csv(caminho, index=False)

    assert e6c.rodar_a_fase_2(HORIZONTES_DA_BUSCA, refazer=False) == 1
    assert not e6c.CAMINHO_DA_FASE_2.exists()


def test_e6c_as_ancoras_da_fase_1_batem_com_o_ranking_das_previsoes_do_antigo() -> None:
    """O ranking calculado das previsoes do antigo (calibracao) satisfaz todas as ancoras da E6c."""
    antigo = pd.read_csv(
        PASTA_DOS_GABARITOS / "e6c_previsoes_por_configuracao.csv", parse_dates=["data_alvo"], float_precision="round_trip"
    )
    na_calibracao = antigo.loc[antigo["data_alvo"] <= CONFIGURACAO_AVALIACAO.fim_da_calibracao]
    maes: dict[str, float] = {}
    for configuracao in montar_a_grade_de_18():
        da_configuracao = na_calibracao.loc[na_calibracao["braco"] == configuracao.nome]
        erros = (da_configuracao["real"] - da_configuracao["previsto"]).abs()
        por_horizonte = erros.groupby(da_configuracao["h"]).mean()
        maes[configuracao.nome] = float(por_horizonte.mean())
    ancoras = e6c.conferir_ancoras_da_fase_1(montar_ranking_da_fase_1(maes))
    assert ancoras["primeiro_e_o_esperado"] is True
    assert ancoras["bate_o_mae_do_1o"] is True
    assert ancoras["bate_o_mae_da_referencia"] is True
    assert ancoras["posicao_da_referencia_medida"] == 4
    assert ancoras["folha_minima_20_do_10o_ao_18o"] is True
    assert ancoras["folha_minima_20_na_faixa_54_68_a_55_69"] is True
    assert ancoras["maior_diferenca_de_mae_para_o_ranking_antigo"] < 1e-9


# ---------------------------------------------------------------------------
# E7
# ---------------------------------------------------------------------------


@pytest.fixture
def e7_com_pastas_temporarias(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Aponta os caminhos de saida da E7 para `tmp_path`."""
    pasta_de_saida = tmp_path / "wis"
    monkeypatch.setattr(e7, "PASTA_DE_SAIDA", pasta_de_saida)
    monkeypatch.setattr(e7, "PASTA_DOS_PARCIAIS", pasta_de_saida / "parciais")
    monkeypatch.setattr(e7, "CAMINHO_DA_TRAVA", pasta_de_saida / "trava.json")
    monkeypatch.setattr(e7, "CAMINHO_DAS_PREVISOES_DOS_QUANTIS", pasta_de_saida / "previsoes_quantis.csv")
    monkeypatch.setattr(e7, "CAMINHO_DOS_QUANTIS_DO_COMPOSTO", pasta_de_saida / "previsoes_quantis_composto.csv")
    monkeypatch.setattr(e7, "CAMINHO_DOS_CRUZAMENTOS", pasta_de_saida / "cruzamentos.csv")
    monkeypatch.setattr(e7, "CAMINHO_DA_REGUA", pasta_de_saida / "regua_climatologica.csv")
    monkeypatch.setattr(e7, "CAMINHO_DOS_ESCORES", pasta_de_saida / "wis_por_origem.csv")
    monkeypatch.setattr(e7, "CAMINHO_DO_RESUMO", pasta_de_saida / "wis_resumo.csv")
    monkeypatch.setattr(e7, "CAMINHO_DA_FAMILIA_F5", pasta_de_saida / "familia_F5.csv")
    monkeypatch.setattr(e7, "CAMINHO_DAS_ANCORAS", pasta_de_saida / "ancoras.json")
    monkeypatch.setattr(e7, "REGISTRADOR", RegistradorDeLog(pasta_de_saida / "E7_wis.log"))
    return pasta_de_saida


def gravar_parciais_da_e7(referencia: pd.DataFrame, mudar_uma_celula_da_trava: bool, cruzar_uma_celula: bool) -> None:
    """Grava as 176 celulas: previsto do quantil q = referencia + 10 * (q - 0,85) (crescente em q); q0,85 = referencia exata.

    Com `cruzar_uma_celula`, a celula (folha 5, q0,25, h = 1) recebe +1000: o q0,25 passa dos quantis acima em todas as origens.
    """
    e7.PASTA_DOS_PARCIAIS.mkdir(parents=True, exist_ok=True)
    for celula in e7.montar_todas_as_celulas():
        parcial = da_referencia(referencia, celula.folha, celula.horizonte)
        parcial["previsto"] = parcial["previsto"] + 10.0 * (celula.quantil - 0.85)
        if cruzar_uma_celula and (celula.folha, celula.quantil, celula.horizonte) == (5, 0.25, 1):
            parcial["previsto"] = parcial["previsto"] + 1000.0
        if mudar_uma_celula_da_trava and (celula.folha, celula.quantil, celula.horizonte) == (20, 0.85, 8):
            parcial.loc[parcial.index[40], "previsto"] += 1e-3
        parcial.insert(0, "quantil", celula.quantil)
        parcial.insert(0, "folha", celula.folha)
        parcial.to_csv(e7.caminho_do_parcial(celula), index=False)


def verificar_que_o_composto_usa_a_escolha_da_e3_com_n_13(quantis_das_folhas: pd.DataFrame) -> None:
    """Em cada semana do horizonte 1, o composto grava os quantis da folha que a E3 (N = 13) escolheu.

    Lido de `resultados/ciencia/E3_composto/previsoes.csv` (so leitura) e comparado, quantil a quantil, com os
    quantis ORDENADOS da folha escolhida (as duas folhas fabricadas diferem, entao a escolha errada aparece).
    """
    e3 = pd.read_csv(e7.CAMINHO_DAS_ESCOLHAS_DO_COMPOSTO_DA_E3, parse_dates=["data_origem", "data_alvo"])
    escolhas = e3.loc[(e3["N"] == 13) & (e3["h"] == 1), ["data_alvo", "folha_escolhida"]]
    composto = pd.read_csv(e7.CAMINHO_DOS_QUANTIS_DO_COMPOSTO, parse_dates=["data_alvo"])
    composto_h1 = composto.loc[composto["h"] == 1]
    das_folhas_h1 = quantis_das_folhas.copy()
    das_folhas_h1["data_alvo"] = pd.to_datetime(das_folhas_h1["data_alvo"])
    das_folhas_h1 = das_folhas_h1.loc[das_folhas_h1["h"] == 1]
    for folha in (5, 20):
        datas_da_folha = escolhas.loc[escolhas["folha_escolhida"] == folha, "data_alvo"]
        assert len(datas_da_folha) > 0
        do_composto = composto_h1.loc[composto_h1["data_alvo"].isin(datas_da_folha)].sort_values(["data_alvo", "quantil"])
        da_folha = das_folhas_h1.loc[
            (das_folhas_h1["folha"] == folha) & das_folhas_h1["data_alvo"].isin(datas_da_folha)
        ].sort_values(["data_alvo", "quantil"])
        assert len(do_composto) == len(da_folha) == 7 * len(datas_da_folha)
        np.testing.assert_array_equal(do_composto["previsto"].to_numpy(), da_folha["previsto"].to_numpy())


def test_e7_as_176_celulas_e_o_nome_dos_parciais(e7_com_pastas_temporarias: pathlib.Path) -> None:
    """168 do WIS (2 x 7 x 12) + 8 da trava (q0,85 em h = 1, 4, 8, 12 nas 2 folhas); nome `previsoes_folha<f>_q<nnn>_h<hh>.csv`."""
    celulas = e7.montar_todas_as_celulas()
    assert len(celulas) == 176 == e7.TOTAL_DE_CELULAS
    assert len(set(celulas)) == 176
    da_trava = [celula for celula in celulas if celula.quantil == 0.85]
    assert len(da_trava) == 8
    assert sorted({celula.horizonte for celula in da_trava}) == [1, 4, 8, 12]
    assert e7.caminho_do_parcial(e7.CelulaDoWis(5, 0.05, 1)).name == "previsoes_folha5_q005_h01.csv"
    assert e7.caminho_do_parcial(e7.CelulaDoWis(20, 0.85, 12)).name == "previsoes_folha20_q085_h12.csv"
    assert e7.sufixo_do_quantil(0.10) == "010"
    assert e7.sufixo_do_quantil(0.95) == "095"


def test_e7_a_selecao_de_fatias(e7_com_pastas_temporarias: pathlib.Path) -> None:
    """`--quantis 0.85` pega so as 8 celulas da trava; q0,85 em h = 2 nao existe; fatia de 1 folha x 2 quantis x 3 h = 6."""
    assert len(e7.selecionar_celulas(None, [0.85], None)) == 8
    assert e7.selecionar_celulas(None, [0.85], [2]) == []
    assert len(e7.selecionar_celulas([5], [0.05, 0.10], [1, 2, 3])) == 6
    assert len(e7.selecionar_celulas(None, None, None)) == 176


def test_e7_juntar_e_medir_com_trava_aprovada_grava_quantis_wis_e_familia_f5(
    e7_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """176 parciais fabricados: saida 0; quantis ordenados (so 1 celula cruzada); WIS por origem e resumo; F5 com 12 testes."""
    gravar_parciais_da_e7(referencia, mudar_uma_celula_da_trava=False, cruzar_uma_celula=True)
    assert e7.listar_parciais_faltantes(e7.montar_todas_as_celulas()) == []

    assert e7.juntar_e_medir(time.perf_counter()) == 0

    with open(e7.CAMINHO_DA_TRAVA, encoding="utf-8") as arquivo:
        assert json.load(arquivo)["trava"]["passou"] is True

    quantis = pd.read_csv(e7.CAMINHO_DAS_PREVISOES_DOS_QUANTIS)
    assert set(quantis["quantil"].round(2)) == {round(q, 2) for q in QUANTIS_DO_WIS}
    assert (quantis["quantil"].round(2) != 0.85).all()
    assert len(quantis) % 7 == 0

    cruzamentos = pd.read_csv(e7.CAMINHO_DOS_CRUZAMENTOS)
    assert len(cruzamentos) == 24  # 2 folhas x 12 horizontes
    cruzada = cruzamentos.loc[(cruzamentos["folha"] == 5) & (cruzamentos["h"] == 1)].iloc[0]
    assert cruzada["fracao"] == 1.0
    assert int(cruzamentos["com_cruzamento"].sum()) == int(cruzada["com_cruzamento"])

    escores = pd.read_csv(e7.CAMINHO_DOS_ESCORES)
    assert set(escores["modelo"]) == {"folha5", "folha20", "composto_N13", "regua_climatologica"}
    assert set(escores["h"]) == set(range(1, 13))
    assert (escores["wis"] >= 0).all()

    resumo = pd.read_csv(e7.CAMINHO_DO_RESUMO)
    assert set(resumo["janela"]) == {e7.NOME_DA_JANELA_PADRAO, e7.NOME_DA_JANELA_ANTIGA}
    da_janela_padrao = resumo.loc[(resumo["janela"] == e7.NOME_DA_JANELA_PADRAO) & (resumo["modelo"] != "regua_climatologica")]
    assert (da_janela_padrao["n"] == 102).all()
    assert len(da_janela_padrao) == 3 * 12

    na_janela_antiga = resumo.loc[(resumo["janela"] == e7.NOME_DA_JANELA_ANTIGA) & (resumo["modelo"].isin(["folha5", "folha20"]))]
    na_janela_antiga_nos_4_horizontes = na_janela_antiga.loc[na_janela_antiga["h"].isin([1, 4, 8, 12])]
    assert (na_janela_antiga_nos_4_horizontes["n"] == 97).all()  # n da rodada de 26/09 (2024-2025)

    verificar_que_o_composto_usa_a_escolha_da_e3_com_n_13(quantis)

    familia = pd.read_csv(e7.CAMINHO_DA_FAMILIA_F5)
    assert len(familia) == 12
    assert sorted(set(familia["A"])) == ["composto_N13", "folha20", "folha5"]
    assert sorted(set(familia["h"])) == [1, 4, 8, 12]

    with open(e7.CAMINHO_DAS_ANCORAS, encoding="utf-8") as arquivo:
        ancoras = json.load(arquivo)
    assert ancoras["n_de_102_semanas_por_horizonte_nos_3_modelos"] is True
    assert len(ancoras["wis_da_janela_antiga_contra_26_09"]) == 12
    assert ancoras["previsoes_dos_7_quantis_contra_a_rodada_de_26_09"]["linhas_em_comum"] > 0


def test_e7_a_trava_reprova_se_uma_previsao_do_q085_da_folha_20_muda_1e_3_e_a_etapa_para(
    e7_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """+1e-3 em (folha 20, q0,85, h = 8): saida 1, `trava.json` reprovado e NADA do WIS e gravado."""
    gravar_parciais_da_e7(referencia, mudar_uma_celula_da_trava=True, cruzar_uma_celula=False)
    assert e7.juntar_e_medir(time.perf_counter()) == 1
    with open(e7.CAMINHO_DA_TRAVA, encoding="utf-8") as arquivo:
        trava = json.load(arquivo)["trava"]
    assert trava["passou"] is False
    assert trava["por_folha"]["folha5"]["passou"] is True
    assert trava["por_folha"]["folha20"]["passou"] is False
    assert not e7.CAMINHO_DAS_PREVISOES_DOS_QUANTIS.exists()
    assert not e7.CAMINHO_DO_RESUMO.exists()
    assert not e7.CAMINHO_DA_FAMILIA_F5.exists()


def test_e7_so_trava_exige_as_8_celulas_e_confere(
    e7_com_pastas_temporarias: pathlib.Path, referencia: pd.DataFrame
) -> None:
    """Sem parciais: saida 1. Com os 8 do q0,85 corretos: saida 0."""
    assert e7.conferir_so_a_trava() == 1
    gravar_parciais_da_e7(referencia, mudar_uma_celula_da_trava=False, cruzar_uma_celula=False)
    for celula in e7.montar_todas_as_celulas():
        if celula.quantil != 0.85:
            e7.caminho_do_parcial(celula).unlink()
    assert e7.conferir_so_a_trava() == 0


def test_e7_as_ancoras_do_wis_antigo_estao_completas() -> None:
    """12 ancoras (folha 5, folha 20 e regua em 4 horizontes) como na pre-declaracao."""
    assert len(e7.ANCORAS_DO_WIS_NA_JANELA_ANTIGA) == 12
    assert e7.ANCORAS_DO_WIS_NA_JANELA_ANTIGA[("folha5", 1)] == 101.9
    assert e7.ANCORAS_DO_WIS_NA_JANELA_ANTIGA[("regua_climatologica", 12)] == 324.2
