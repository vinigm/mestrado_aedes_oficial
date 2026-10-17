"""Testes da fiacao dos scripts da ciencia (E1, E2, E4 e piso de ruido), SEM treinar nenhum modelo.

Os scripts fazem tres coisas alem de treinar: gravar parciais, juntar e conferir travas. Aqui os
parciais sao FABRICADOS a partir da referencia certificada (`resultados/referencia/previsoes.csv`) e do
gabarito antigo (`testes/referencia_antiga/`), em pastas temporarias, e se confere:
    - as ancoras do orquestrador (n e MAE da janela e da calibracao);
    - que as travas passam quando as previsoes sao iguais ao gabarito e REPROVAM quando uma celula muda
      1e-3, quando falta uma linha, ou quando o braco antigo nao bate;
    - que, com trava reprovada, a etapa para e nao grava o resultado descritivo;
    - a regra de 2% do quantil na juncao da E1, a exigencia da E2 pronta na E4 e o piso do ruido.

Nenhum arquivo do projeto e escrito: tudo vai para `tmp_path`.
"""

import json
import pathlib
import time

import numpy as np
import pandas as pd
import pytest

import experimentos.e1_quantil as e1
import experimentos.e2_ablacao as e2
import experimentos.e4_corte as e4
import experimentos.piso_de_ruido as piso_de_ruido
from aedes.bracos import NOMES_DOS_BRACOS
from aedes.comparacoes import calcular_mae_na_janela
from aedes.configuracao import (
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.bracos import montar_matriz_do_braco
from aedes.perturbacao import alinhar_matriz_do_gabarito
from experimentos.comum_ciencia import (
    CAMINHO_DA_REFERENCIA,
    RegistradorDeLog,
    ler_gabarito_por_braco_antigo,
    ler_matriz_do_gabarito_csv,
    ler_previsoes_da_referencia,
)

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
HORIZONTES = CONFIGURACAO_AVALIACAO.horizontes
UMA_SEMANA = pd.Timedelta(weeks=1)

# Ancoras calculadas pelo orquestrador a partir de `resultados/referencia/previsoes.csv`.
MAE_DA_JANELA_FOLHA_5 = {1: 97.987, 4: 219.669, 8: 272.627, 12: 278.818}
MAE_DA_JANELA_FOLHA_20 = {1: 133.626, 4: 199.635, 8: 223.183, 12: 243.765}
MAE_DA_CALIBRACAO_FOLHA_5 = {1: 22.337, 4: 45.786, 8: 48.167, 12: 51.799}
N_DA_CALIBRACAO = {1: 193, 4: 190, 8: 186, 12: 182}
N_DA_JANELA = 102
TOLERANCIA_DA_ANCORA = 5e-4

# Ancoras do gabarito antigo `HistGB_folha20_M0` (sem vetor, folha 20).
LINHAS_DO_GABARITO_SEM_VETOR = 3618
N_DA_JANELA_SEM_VETOR = 109
MAE_DA_JANELA_SEM_VETOR_FOLHA_20 = {1: 138.678, 4: 214.741, 8: 231.119, 12: 261.180}


@pytest.fixture(scope="module")
def referencia() -> pd.DataFrame:
    """As previsoes certificadas do ciclo 3 (folha 5 = `referencia`, folha 20 = `HistGB_folha20_M1`)."""
    return ler_previsoes_da_referencia()


@pytest.fixture(scope="module")
def gabarito_antigo() -> pd.DataFrame:
    """As previsoes por braco do codigo antigo (sem `data_origem`)."""
    return ler_gabarito_por_braco_antigo()


def previsoes_da_referencia_por_folha(referencia: pd.DataFrame, folha: int) -> pd.DataFrame:
    """Linhas da referencia de uma folha."""
    nome_do_braco = {5: "referencia", 20: "HistGB_folha20_M1"}[folha]
    return referencia.loc[referencia["braco"] == nome_do_braco]


def previsoes_do_gabarito_sem_vetor(gabarito_antigo: pd.DataFrame) -> pd.DataFrame:
    """Linhas do gabarito `HistGB_folha20_M0`, com `data_origem` reconstruida (`data_alvo - h semanas`)."""
    do_braco = gabarito_antigo.loc[gabarito_antigo["braco"] == "HistGB_folha20_M0"].copy()
    do_braco["data_origem"] = do_braco["data_alvo"] - do_braco["h"] * UMA_SEMANA
    return do_braco


def montar_previsoes_da_e2_fabricadas(referencia: pd.DataFrame, gabarito_antigo: pd.DataFrame) -> pd.DataFrame:
    """Previsoes da E2 com `completo` = referencia, `sem_vetor` folha 20 = gabarito antigo e os outros bracos = referencia."""
    pedacos: list[pd.DataFrame] = []
    sem_vetor_antigo = previsoes_do_gabarito_sem_vetor(gabarito_antigo)
    for nome_do_braco in NOMES_DOS_BRACOS:
        for folha in (5, 20):
            if nome_do_braco == "sem_vetor" and folha == 20:
                origem = sem_vetor_antigo
            else:
                origem = previsoes_da_referencia_por_folha(referencia, folha)
            pedaco = origem[["h", "data_origem", "data_alvo", "real", "previsto"]].copy()
            pedaco.insert(0, "folha", folha)
            pedaco.insert(0, "braco", nome_do_braco)
            pedacos.append(pedaco)
    return pd.concat(pedacos, ignore_index=True)[list(e2.COLUNAS_DO_ARQUIVO_DE_PREVISOES)]


# ---------------------------------------------------------------------------
# Ancoras da referencia (garantem que os dados-base dos testes sao os do orquestrador)
# ---------------------------------------------------------------------------


def test_ancoras_da_referencia_na_janela_e_na_calibracao(referencia: pd.DataFrame) -> None:
    """n = 102 na janela; MAE da janela das duas folhas; n e MAE da calibracao da folha 5."""
    for folha, mae_esperado_por_horizonte in ((5, MAE_DA_JANELA_FOLHA_5), (20, MAE_DA_JANELA_FOLHA_20)):
        da_folha = previsoes_da_referencia_por_folha(referencia, folha)
        for horizonte, mae_esperado in mae_esperado_por_horizonte.items():
            do_horizonte = da_folha.loc[da_folha["h"] == horizonte]
            quantidade, mae = calcular_mae_na_janela(do_horizonte, CONFIGURACAO_AVALIACAO)
            assert quantidade == N_DA_JANELA
            assert mae == pytest.approx(mae_esperado, abs=TOLERANCIA_DA_ANCORA)

    da_folha_5 = previsoes_da_referencia_por_folha(referencia, 5)
    for horizonte, mae_esperado in MAE_DA_CALIBRACAO_FOLHA_5.items():
        do_horizonte = da_folha_5.loc[da_folha_5["h"] == horizonte]
        na_calibracao = do_horizonte.loc[do_horizonte["data_alvo"] <= CONFIGURACAO_AVALIACAO.fim_da_calibracao]
        assert len(na_calibracao) == N_DA_CALIBRACAO[horizonte]
        mae = float(np.mean(np.abs(na_calibracao["real"] - na_calibracao["previsto"])))
        assert mae == pytest.approx(mae_esperado, abs=TOLERANCIA_DA_ANCORA)


def test_ancoras_do_gabarito_antigo_sem_vetor(gabarito_antigo: pd.DataFrame) -> None:
    """3618 previsoes; n = 109 na janela; MAE da janela em h = 1, 4, 8, 12."""
    sem_vetor = previsoes_do_gabarito_sem_vetor(gabarito_antigo)
    assert len(sem_vetor) == LINHAS_DO_GABARITO_SEM_VETOR
    for horizonte, mae_esperado in MAE_DA_JANELA_SEM_VETOR_FOLHA_20.items():
        do_horizonte = sem_vetor.loc[sem_vetor["h"] == horizonte]
        quantidade, mae = calcular_mae_na_janela(do_horizonte, CONFIGURACAO_AVALIACAO)
        assert quantidade == N_DA_JANELA_SEM_VETOR
        assert mae == pytest.approx(mae_esperado, abs=TOLERANCIA_DA_ANCORA)


# ---------------------------------------------------------------------------
# E2: travas
# ---------------------------------------------------------------------------


def test_e2_travas_passam_quando_as_previsoes_sao_as_da_referencia_e_do_gabarito(
    referencia: pd.DataFrame,
    gabarito_antigo: pd.DataFrame,
) -> None:
    """Trava 1 (completo f5 e f20 x referencia) e trava 2 (sem_vetor f20 x HistGB_folha20_M0, 3618 linhas)."""
    previsoes = montar_previsoes_da_e2_fabricadas(referencia, gabarito_antigo)
    travas = e2.avaliar_travas(previsoes, escopo="teste")

    assert travas["todas_passaram"] is True
    assert travas["trava_1_completo_folha5"]["linhas_em_comum"] == 3474
    assert travas["trava_1_completo_folha20"]["linhas_em_comum"] == 3474
    assert travas["trava_2_sem_vetor_folha20"]["linhas_em_comum"] == LINHAS_DO_GABARITO_SEM_VETOR
    assert travas["trava_2_sem_vetor_folha20"]["passou"] is True


def test_e2_trava_2_reprova_se_uma_previsao_do_sem_vetor_muda_1e_3(
    referencia: pd.DataFrame,
    gabarito_antigo: pd.DataFrame,
) -> None:
    """Uma celula do `sem_vetor` folha 20 com +1e-3: so a trava 2 reprova; `todas_passaram` falso."""
    previsoes = montar_previsoes_da_e2_fabricadas(referencia, gabarito_antigo)
    da_trava_2 = (previsoes["braco"] == "sem_vetor") & (previsoes["folha"] == 20)
    primeira_linha = previsoes.index[da_trava_2][100]
    previsoes.loc[primeira_linha, "previsto"] += 1e-3

    travas = e2.avaliar_travas(previsoes, escopo="teste")
    assert travas["trava_2_sem_vetor_folha20"]["passou"] is False
    assert travas["trava_1_completo_folha5"]["passou"] is True
    assert travas["trava_1_completo_folha20"]["passou"] is True
    assert travas["todas_passaram"] is False


def test_e2_trava_1_reprova_se_o_completo_perde_uma_linha(
    referencia: pd.DataFrame,
    gabarito_antigo: pd.DataFrame,
) -> None:
    """Sem uma linha do `completo` folha 20: conjunto de chaves diferente, trava 1 (folha 20) reprova."""
    previsoes = montar_previsoes_da_e2_fabricadas(referencia, gabarito_antigo)
    do_completo_folha_20 = (previsoes["braco"] == "completo") & (previsoes["folha"] == 20)
    linha_a_remover = previsoes.index[do_completo_folha_20][7]
    previsoes = previsoes.drop(index=linha_a_remover)

    travas = e2.avaliar_travas(previsoes, escopo="teste")
    assert travas["trava_1_completo_folha20"]["passou"] is False
    assert travas["trava_1_completo_folha20"]["linhas_so_no_gabarito"] == 1
    assert travas["todas_passaram"] is False


# ---------------------------------------------------------------------------
# E2: juncao com parciais fabricados
# ---------------------------------------------------------------------------


@pytest.fixture
def e2_com_pastas_temporarias(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Aponta os caminhos de saida da E2 para `tmp_path` (nada do projeto e escrito)."""
    pasta_de_saida = tmp_path / "E2_ablacao"
    monkeypatch.setattr(e2, "PASTA_DE_SAIDA", pasta_de_saida)
    monkeypatch.setattr(e2, "PASTA_DOS_PARCIAIS", pasta_de_saida / "parciais")
    monkeypatch.setattr(e2, "CAMINHO_DAS_PREVISOES", pasta_de_saida / "previsoes.csv")
    monkeypatch.setattr(e2, "CAMINHO_DO_MAE", pasta_de_saida / "mae_descritivo.csv")
    monkeypatch.setattr(e2, "CAMINHO_DAS_TRAVAS", pasta_de_saida / "travas.json")
    monkeypatch.setattr(e2, "REGISTRADOR", RegistradorDeLog(pasta_de_saida / "E2_ablacao.log"))
    return pasta_de_saida


def gravar_parciais_da_e2(previsoes: pd.DataFrame, bracos: tuple[str, ...], folhas: tuple[int, ...]) -> None:
    """Grava, no formato do script, os parciais de (braco, folha, h) a partir de uma tabela de previsoes."""
    e2.PASTA_DOS_PARCIAIS.mkdir(parents=True, exist_ok=True)
    for nome_do_braco in bracos:
        for folha in folhas:
            for horizonte in HORIZONTES:
                do_braco = previsoes["braco"] == nome_do_braco
                da_folha = previsoes["folha"] == folha
                do_horizonte = previsoes["h"] == horizonte
                parcial = previsoes.loc[do_braco & da_folha & do_horizonte]
                parcial.to_csv(e2.caminho_do_parcial(nome_do_braco, folha, horizonte), index=False)


def test_e2_juntar_e_medir_com_parciais_iguais_ao_gabarito_grava_o_mae_com_as_ancoras(
    e2_com_pastas_temporarias: pathlib.Path,
    referencia: pd.DataFrame,
    gabarito_antigo: pd.DataFrame,
) -> None:
    """192 parciais fabricados: codigo de saida 0, `travas.json` aprovado e `mae_descritivo.csv` com as ancoras."""
    previsoes = montar_previsoes_da_e2_fabricadas(referencia, gabarito_antigo)
    gravar_parciais_da_e2(previsoes, NOMES_DOS_BRACOS, (5, 20))
    assert e2.listar_parciais_faltantes(NOMES_DOS_BRACOS, (5, 20)) == []

    codigo_de_saida = e2.juntar_e_medir(time.perf_counter())
    assert codigo_de_saida == 0

    with open(e2.CAMINHO_DAS_TRAVAS, encoding="utf-8") as arquivo:
        travas = json.load(arquivo)
    assert travas["todas_passaram"] is True
    assert travas["escopo"] == "etapa_completa"

    previsoes_juntas = pd.read_csv(e2.CAMINHO_DAS_PREVISOES)
    assert list(previsoes_juntas.columns) == [
        "braco", "folha", "h", "data_origem", "data_alvo", "real", "previsto",
    ]
    assert len(previsoes_juntas) == len(previsoes)
    assert list(pd.unique(previsoes_juntas["braco"])) == list(NOMES_DOS_BRACOS)

    mae_descritivo = pd.read_csv(e2.CAMINHO_DO_MAE)
    assert list(mae_descritivo.columns) == ["braco", "folha", "h", "n_janela", "mae"]
    assert len(mae_descritivo) == 8 * 2 * 12

    completo_folha_5_h1 = mae_descritivo.loc[
        (mae_descritivo["braco"] == "completo") & (mae_descritivo["folha"] == 5) & (mae_descritivo["h"] == 1)
    ].iloc[0]
    assert completo_folha_5_h1["n_janela"] == N_DA_JANELA
    assert completo_folha_5_h1["mae"] == pytest.approx(MAE_DA_JANELA_FOLHA_5[1], abs=TOLERANCIA_DA_ANCORA)

    sem_vetor_folha_20_h12 = mae_descritivo.loc[
        (mae_descritivo["braco"] == "sem_vetor") & (mae_descritivo["folha"] == 20) & (mae_descritivo["h"] == 12)
    ].iloc[0]
    assert sem_vetor_folha_20_h12["n_janela"] == N_DA_JANELA_SEM_VETOR
    assert sem_vetor_folha_20_h12["mae"] == pytest.approx(
        MAE_DA_JANELA_SEM_VETOR_FOLHA_20[12], abs=TOLERANCIA_DA_ANCORA
    )


def test_e2_com_trava_reprovada_a_etapa_para_e_nao_grava_o_mae(
    e2_com_pastas_temporarias: pathlib.Path,
    referencia: pd.DataFrame,
    gabarito_antigo: pd.DataFrame,
) -> None:
    """Uma previsao do `completo` folha 5 muda 1e-3: saida 1, `travas.json` reprovado, SEM `mae_descritivo.csv`."""
    previsoes = montar_previsoes_da_e2_fabricadas(referencia, gabarito_antigo)
    do_completo_folha_5_h3 = (previsoes["braco"] == "completo") & (previsoes["folha"] == 5) & (previsoes["h"] == 3)
    previsoes.loc[previsoes.index[do_completo_folha_5_h3][50], "previsto"] += 1e-3
    gravar_parciais_da_e2(previsoes, NOMES_DOS_BRACOS, (5, 20))

    codigo_de_saida = e2.juntar_e_medir(time.perf_counter())
    assert codigo_de_saida == 1

    with open(e2.CAMINHO_DAS_TRAVAS, encoding="utf-8") as arquivo:
        travas = json.load(arquivo)
    assert travas["todas_passaram"] is False
    assert travas["trava_1_completo_folha5"]["passou"] is False
    assert e2.CAMINHO_DAS_PREVISOES.exists()
    assert not e2.CAMINHO_DO_MAE.exists()


def test_e2_so_travas_exige_os_parciais_e_depois_confere(
    e2_com_pastas_temporarias: pathlib.Path,
    referencia: pd.DataFrame,
    gabarito_antigo: pd.DataFrame,
) -> None:
    """`--so-travas`: sem parciais devolve 2; com `completo` (f5, f20) e `sem_vetor` f20 prontos, devolve 0."""
    assert e2.checar_travas_antecipadas() == 2

    previsoes = montar_previsoes_da_e2_fabricadas(referencia, gabarito_antigo)
    gravar_parciais_da_e2(previsoes, ("completo",), (5, 20))
    assert e2.checar_travas_antecipadas() == 2

    gravar_parciais_da_e2(previsoes, ("sem_vetor",), (20,))
    assert e2.checar_travas_antecipadas() == 0
    with open(e2.CAMINHO_DAS_TRAVAS, encoding="utf-8") as arquivo:
        travas = json.load(arquivo)
    assert travas["escopo"] == "so_travas"
    assert travas["todas_passaram"] is True


def test_e2_juntar_sem_todos_os_parciais_levanta_erro_claro(e2_com_pastas_temporarias: pathlib.Path) -> None:
    """Nenhum parcial: FileNotFoundError citando a quantidade."""
    with pytest.raises(FileNotFoundError, match="192"):
        e2.juntar_parciais(NOMES_DOS_BRACOS, (5, 20))


# ---------------------------------------------------------------------------
# E1
# ---------------------------------------------------------------------------


def test_e1_sufixo_e_caminho_do_parcial() -> None:
    """0,85 vira `085`; 0,7 vira `070` (arredondamento, nao truncamento)."""
    assert [e1.sufixo_do_quantil(quantil) for quantil in e1.QUANTIS_CANDIDATOS] == ["050", "070", "080", "085", "090"]
    assert e1.caminho_do_parcial(0.85, 4).name == "previsoes_q085_h04.csv"


def previsoes_da_calibracao_da_e1(referencia: pd.DataFrame, quantil: float, mistura_com_o_real: float) -> pd.DataFrame:
    """Previsoes da E1 de um quantil: a referencia da folha 5 na calibracao, com o previsto puxado para o real.

    `mistura_com_o_real` = 0 devolve a referencia; 0,5 leva o previsto a meio caminho do real (MAE menor).
    """
    da_folha_5 = previsoes_da_referencia_por_folha(referencia, 5)
    dos_horizontes = da_folha_5["h"].isin(e1.HORIZONTES_DA_E1)
    na_calibracao = da_folha_5["data_alvo"] <= CONFIGURACAO_AVALIACAO.fim_da_calibracao
    pedaco = da_folha_5.loc[dos_horizontes & na_calibracao].copy()
    pedaco["previsto"] = (1.0 - mistura_com_o_real) * pedaco["previsto"] + mistura_com_o_real * pedaco["real"]
    pedaco.insert(0, "quantil", quantil)
    return pedaco[list(e1.COLUNAS_DO_ARQUIVO_DE_PREVISOES)]


def test_e1_metricas_da_calibracao_reproduzem_as_ancoras(referencia: pd.DataFrame) -> None:
    """n = 193/190/186/182; MAE 22,337/45,786/48,167/51,799 (media 42,022) no quantil 0,85; cobertura em [0, 1]."""
    previsoes = pd.concat(
        [previsoes_da_calibracao_da_e1(referencia, quantil, 0.0) for quantil in e1.QUANTIS_CANDIDATOS],
        ignore_index=True,
    )
    metricas = e1.calcular_metricas_da_calibracao(previsoes)
    assert list(metricas.columns) == ["quantil", "h", "n", "mae", "cobertura"]
    assert len(metricas) == 20

    do_quantil_de_referencia = metricas.loc[metricas["quantil"] == 0.85].set_index("h")
    for horizonte in e1.HORIZONTES_DA_E1:
        assert do_quantil_de_referencia.loc[horizonte, "n"] == N_DA_CALIBRACAO[horizonte]
        assert do_quantil_de_referencia.loc[horizonte, "mae"] == pytest.approx(
            MAE_DA_CALIBRACAO_FOLHA_5[horizonte], abs=TOLERANCIA_DA_ANCORA
        )
    assert float(do_quantil_de_referencia["mae"].mean()) == pytest.approx(42.022, abs=TOLERANCIA_DA_ANCORA)
    assert metricas["cobertura"].between(0.0, 1.0).all()


def test_e1_trava_3_passa_com_a_referencia_e_reprova_com_uma_celula_alterada(referencia: pd.DataFrame) -> None:
    """O quantil 0,85 igual a referencia na calibracao passa; +1e-3 em uma previsao reprova."""
    previsoes = previsoes_da_calibracao_da_e1(referencia, 0.85, 0.0)
    trava_3 = e1.conferir_trava_3(previsoes)
    assert trava_3["passou"] is True
    assert trava_3["linhas_em_comum"] == sum(N_DA_CALIBRACAO.values())

    alterada = previsoes.copy()
    alterada.loc[alterada.index[30], "previsto"] += 1e-3
    assert e1.conferir_trava_3(alterada)["passou"] is False


@pytest.fixture
def e1_com_pastas_temporarias(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Aponta os caminhos de saida da E1 para `tmp_path`."""
    pasta_de_saida = tmp_path / "E1_quantil"
    monkeypatch.setattr(e1, "PASTA_DE_SAIDA", pasta_de_saida)
    monkeypatch.setattr(e1, "PASTA_DOS_PARCIAIS", pasta_de_saida / "parciais")
    monkeypatch.setattr(e1, "CAMINHO_DAS_PREVISOES", pasta_de_saida / "previsoes.csv")
    monkeypatch.setattr(e1, "CAMINHO_DAS_METRICAS", pasta_de_saida / "metricas.csv")
    monkeypatch.setattr(e1, "CAMINHO_DA_DECISAO", pasta_de_saida / "decisao.json")
    monkeypatch.setattr(e1, "REGISTRADOR", RegistradorDeLog(pasta_de_saida / "E1_quantil.log"))
    return pasta_de_saida


def gravar_parciais_da_e1(referencia: pd.DataFrame, mistura_por_quantil: dict[float, float]) -> None:
    """Grava os 20 parciais da E1, com a mistura com o real indicada por quantil."""
    e1.PASTA_DOS_PARCIAIS.mkdir(parents=True, exist_ok=True)
    for quantil in e1.QUANTIS_CANDIDATOS:
        previsoes = previsoes_da_calibracao_da_e1(referencia, quantil, mistura_por_quantil[quantil])
        for horizonte in e1.HORIZONTES_DA_E1:
            parcial = previsoes.loc[previsoes["h"] == horizonte]
            parcial.to_csv(e1.caminho_do_parcial(quantil, horizonte), index=False)


def test_e1_decisao_mantem_o_085_quando_nenhum_candidato_o_supera_por_2_por_cento(
    e1_com_pastas_temporarias: pathlib.Path,
    referencia: pd.DataFrame,
) -> None:
    """Todos os quantis iguais a referencia: ganho zero, escolhido 0,85, `quantil_mudou` falso, `metricas.csv` gravado."""
    gravar_parciais_da_e1(referencia, {quantil: 0.0 for quantil in e1.QUANTIS_CANDIDATOS})
    assert e1.juntar_e_decidir(time.perf_counter()) == 0

    with open(e1.CAMINHO_DA_DECISAO, encoding="utf-8") as arquivo:
        decisao = json.load(arquivo)
    assert decisao["quantil_escolhido"] == 0.85
    assert decisao["quantil_mudou"] is False
    assert decisao["ganho_relativo"] == 0.0
    assert decisao["trava_3"]["passou"] is True
    assert decisao["n_por_horizonte"] == {"1": 193, "4": 190, "8": 186, "12": 182}
    assert decisao["mae_medio_por_quantil"]["0.85"] == pytest.approx(42.022, abs=TOLERANCIA_DA_ANCORA)
    assert e1.CAMINHO_DAS_METRICAS.exists()


def test_e1_decisao_troca_o_quantil_quando_outro_supera_o_085_por_2_por_cento_ou_mais(
    e1_com_pastas_temporarias: pathlib.Path,
    referencia: pd.DataFrame,
) -> None:
    """O quantil 0,70 com o previsto puxado 50% para o real tem MAE bem menor que o 0,85: troca."""
    misturas = {quantil: 0.0 for quantil in e1.QUANTIS_CANDIDATOS}
    misturas[0.70] = 0.5
    gravar_parciais_da_e1(referencia, misturas)
    assert e1.juntar_e_decidir(time.perf_counter()) == 0

    with open(e1.CAMINHO_DA_DECISAO, encoding="utf-8") as arquivo:
        decisao = json.load(arquivo)
    assert decisao["melhor_quantil"] == 0.70
    assert decisao["quantil_escolhido"] == 0.70
    assert decisao["quantil_mudou"] is True
    assert decisao["ganho_relativo"] > 0.02


def test_e1_com_trava_3_reprovada_a_etapa_para_sem_metricas_nem_decisao(
    e1_com_pastas_temporarias: pathlib.Path,
    referencia: pd.DataFrame,
) -> None:
    """O 0,85 diverge da referencia: saida 1, `decisao.json` so com a trava, SEM `metricas.csv`."""
    misturas = {quantil: 0.0 for quantil in e1.QUANTIS_CANDIDATOS}
    misturas[0.85] = 0.01
    gravar_parciais_da_e1(referencia, misturas)
    assert e1.juntar_e_decidir(time.perf_counter()) == 1

    with open(e1.CAMINHO_DA_DECISAO, encoding="utf-8") as arquivo:
        decisao = json.load(arquivo)
    assert decisao["decisao"] is None
    assert decisao["trava_3"]["passou"] is False
    assert not e1.CAMINHO_DAS_METRICAS.exists()


# ---------------------------------------------------------------------------
# E4
# ---------------------------------------------------------------------------


@pytest.fixture
def e4_com_pastas_temporarias(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Aponta os caminhos de saida da E4 e os de entrada da E2 para `tmp_path`."""
    pasta_da_e2 = tmp_path / "E2_ablacao"
    pasta_de_saida = tmp_path / "E4_corte"
    monkeypatch.setattr(e4, "PASTA_DE_SAIDA", pasta_de_saida)
    monkeypatch.setattr(e4, "PASTA_DOS_PARCIAIS", pasta_de_saida / "parciais")
    monkeypatch.setattr(e4, "CAMINHO_DAS_PREVISOES", pasta_de_saida / "previsoes.csv")
    monkeypatch.setattr(e4, "CAMINHO_DA_COMPARACAO", pasta_de_saida / "comparacao.csv")
    monkeypatch.setattr(e4, "REGISTRADOR", RegistradorDeLog(pasta_de_saida / "E4_corte.log"))
    monkeypatch.setattr(e4, "PASTA_DA_E2", pasta_da_e2)
    monkeypatch.setattr(e4, "CAMINHO_DAS_PREVISOES_DA_E2", pasta_da_e2 / "previsoes.csv")
    monkeypatch.setattr(e4, "CAMINHO_DAS_TRAVAS_DA_E2", pasta_da_e2 / "travas.json")
    return tmp_path


def gravar_e2_fabricada(pasta_da_e2: pathlib.Path, previsoes: pd.DataFrame, travas: dict[str, object]) -> None:
    """Grava `previsoes.csv` e `travas.json` da E2 fabricada."""
    pasta_da_e2.mkdir(parents=True, exist_ok=True)
    previsoes.to_csv(pasta_da_e2 / "previsoes.csv", index=False)
    with open(pasta_da_e2 / "travas.json", "w", encoding="utf-8") as arquivo:
        json.dump(travas, arquivo)


def test_e4_exige_a_e2_pronta_e_com_as_travas_aprovadas(
    e4_com_pastas_temporarias: pathlib.Path,
    referencia: pd.DataFrame,
    gabarito_antigo: pd.DataFrame,
) -> None:
    """Sem arquivos: FileNotFoundError. Travas reprovadas ou so antecipadas: RuntimeError. Aprovadas: passa."""
    pasta_da_e2 = e4_com_pastas_temporarias / "E2_ablacao"
    with pytest.raises(FileNotFoundError, match="E2 pronta"):
        e4.exigir_a_e2_pronta()

    previsoes_da_e2 = montar_previsoes_da_e2_fabricadas(referencia, gabarito_antigo)
    gravar_e2_fabricada(pasta_da_e2, previsoes_da_e2, {"escopo": "etapa_completa", "todas_passaram": False})
    with pytest.raises(RuntimeError, match="travas"):
        e4.exigir_a_e2_pronta()

    gravar_e2_fabricada(pasta_da_e2, previsoes_da_e2, {"escopo": "so_travas", "todas_passaram": True})
    with pytest.raises(RuntimeError, match="travas"):
        e4.exigir_a_e2_pronta()

    gravar_e2_fabricada(pasta_da_e2, previsoes_da_e2, {"escopo": "etapa_completa", "todas_passaram": True})
    e4.exigir_a_e2_pronta()


def test_e4_juntar_e_comparar_com_parciais_fabricados(
    e4_com_pastas_temporarias: pathlib.Path,
    referencia: pd.DataFrame,
    gabarito_antigo: pd.DataFrame,
) -> None:
    """Corte pela pergunta = resposta em h = 1 (variacao 0) e +1 caso de previsto nos demais: `comparacao.csv` coerente."""
    pasta_da_e2 = e4_com_pastas_temporarias / "E2_ablacao"
    previsoes_da_e2 = montar_previsoes_da_e2_fabricadas(referencia, gabarito_antigo)
    gravar_e2_fabricada(pasta_da_e2, previsoes_da_e2, {"escopo": "etapa_completa", "todas_passaram": True})

    e4.PASTA_DOS_PARCIAIS.mkdir(parents=True, exist_ok=True)
    for nome_do_braco in e4.BRACOS_DA_E4:
        for horizonte in HORIZONTES:
            do_braco = previsoes_da_e2["braco"] == nome_do_braco
            da_folha_5 = previsoes_da_e2["folha"] == 5
            do_horizonte = previsoes_da_e2["h"] == horizonte
            parcial = previsoes_da_e2.loc[do_braco & da_folha_5 & do_horizonte].copy()
            if horizonte > 1:
                parcial["previsto"] = parcial["previsto"] + 1.0
            parcial["corte"] = "pergunta"
            parcial.to_csv(e4.caminho_do_parcial(nome_do_braco, horizonte), index=False)
    assert e4.listar_parciais_faltantes() == []

    e4.juntar_e_comparar(time.perf_counter())

    comparacao = pd.read_csv(e4.CAMINHO_DA_COMPARACAO)
    assert list(comparacao.columns) == [
        "braco", "h", "n", "mae_corte_resposta", "mae_corte_pergunta", "variacao_pct",
        "r2_corte_resposta", "r2_corte_pergunta",
    ]
    assert len(comparacao) == 2 * 12
    assert (comparacao["n"] == N_DA_JANELA).all()

    completo_h1 = comparacao.loc[(comparacao["braco"] == "completo") & (comparacao["h"] == 1)].iloc[0]
    assert completo_h1["variacao_pct"] == 0.0
    assert completo_h1["mae_corte_resposta"] == pytest.approx(MAE_DA_JANELA_FOLHA_5[1], abs=TOLERANCIA_DA_ANCORA)

    completo_h12 = comparacao.loc[(comparacao["braco"] == "completo") & (comparacao["h"] == 12)].iloc[0]
    assert completo_h12["mae_corte_resposta"] == pytest.approx(MAE_DA_JANELA_FOLHA_5[12], abs=TOLERANCIA_DA_ANCORA)
    assert completo_h12["mae_corte_pergunta"] != completo_h12["mae_corte_resposta"]
    assert e4.CAMINHO_DAS_PREVISOES.exists()


# ---------------------------------------------------------------------------
# Piso de ruido
# ---------------------------------------------------------------------------


def test_piso_mae_da_referencia_reproduz_as_ancoras() -> None:
    """MAE da janela (n = 102) das duas folhas em h = 1, 4, 8, 12."""
    mae_da_referencia = piso_de_ruido.calcular_mae_da_referencia().set_index(["folha", "h"])
    assert len(mae_da_referencia) == 8
    for horizonte in (1, 4, 8, 12):
        assert mae_da_referencia.loc[(5, horizonte), "n"] == N_DA_JANELA
        assert mae_da_referencia.loc[(5, horizonte), "mae"] == pytest.approx(
            MAE_DA_JANELA_FOLHA_5[horizonte], abs=TOLERANCIA_DA_ANCORA
        )
        assert mae_da_referencia.loc[(20, horizonte), "mae"] == pytest.approx(
            MAE_DA_JANELA_FOLHA_20[horizonte], abs=TOLERANCIA_DA_ANCORA
        )


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


def test_piso_perturbacao_csv_e_a_matriz_do_gabarito_alinhada(tabela_cortada: pd.DataFrame) -> None:
    """`csv` devolve, igual, o resultado de `alinhar_matriz_do_gabarito` (e nao depende da opcao de zeros)."""
    matriz_do_pacote = montar_matriz_do_braco(tabela_cortada, 4, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    esperada = alinhar_matriz_do_gabarito(matriz_do_pacote, ler_matriz_do_gabarito_csv(4))
    for opcao in (piso_de_ruido.OPCAO_PERTURBAR_ZEROS, piso_de_ruido.OPCAO_MANTER_ZEROS):
        obtida = piso_de_ruido.montar_matriz_perturbada(tabela_cortada, 4, "csv", opcao)
        pd.testing.assert_frame_equal(obtida, esperada, check_exact=True)


def test_piso_opcao_de_zeros_decide_se_os_zeros_exatos_das_sementes_mudam(tabela_cortada: pd.DataFrame) -> None:
    """`casos_mm4` tem zeros exatos: `perturbar` (padrao) os troca por +-5e-324; `manter` os preserva."""
    matriz_do_pacote = montar_matriz_do_braco(tabela_cortada, 4, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    zeros_originais = int((matriz_do_pacote["casos_mm4"] == 0.0).sum())
    assert zeros_originais > 0

    perturbada = piso_de_ruido.montar_matriz_perturbada(tabela_cortada, 4, "s1", piso_de_ruido.OPCAO_PERTURBAR_ZEROS)
    assert int((perturbada["casos_mm4"] == 0.0).sum()) == 0

    com_zeros_mantidos = piso_de_ruido.montar_matriz_perturbada(tabela_cortada, 4, "s1", piso_de_ruido.OPCAO_MANTER_ZEROS)
    assert int((com_zeros_mantidos["casos_mm4"] == 0.0).sum()) == zeros_originais


def test_piso_perturbacao_desconhecida_e_rejeitada(tabela_cortada: pd.DataFrame) -> None:
    """Nome fora de csv, s1..s4 levanta ValueError."""
    with pytest.raises(ValueError, match="Perturbacao desconhecida"):
        piso_de_ruido.montar_matriz_perturbada(tabela_cortada, 4, "s5", piso_de_ruido.OPCAO_PERTURBAR_ZEROS)


def test_piso_definir_pastas_separa_a_variante_com_zeros_mantidos() -> None:
    """Padrao grava em `piso_de_ruido/`; `manter` grava em outra pasta, para nao misturar."""
    pasta_padrao, _ = piso_de_ruido.definir_pastas(piso_de_ruido.OPCAO_PERTURBAR_ZEROS)
    pasta_zeros_mantidos, _ = piso_de_ruido.definir_pastas(piso_de_ruido.OPCAO_MANTER_ZEROS)
    assert pasta_padrao.name == "piso_de_ruido"
    assert pasta_zeros_mantidos.name == "piso_de_ruido_zeros_mantidos"


def gravar_parciais_do_piso(pasta_de_saida: pathlib.Path, referencia: pd.DataFrame) -> dict[str, float]:
    """Grava os 40 parciais do piso: referencia com um deslocamento de previsto por perturbacao.

    `csv` = referencia exata (delta zero); `s1` a `s4` somam deslocamentos 0,1; 0,5; 0,2; 0,3 a TODAS as previsoes.
    Devolve os deslocamentos usados.
    """
    deslocamentos = {"csv": 0.0, "s1": 0.1, "s2": 0.5, "s3": 0.2, "s4": 0.3}
    for perturbacao, deslocamento in deslocamentos.items():
        for folha in (5, 20):
            da_folha = previsoes_da_referencia_por_folha(referencia, folha)
            for horizonte in piso_de_ruido.HORIZONTES_DO_PISO:
                parcial = da_folha.loc[da_folha["h"] == horizonte][
                    ["h", "data_origem", "data_alvo", "real", "previsto"]
                ].copy()
                parcial["previsto"] = parcial["previsto"] + deslocamento
                parcial.insert(0, "folha", folha)
                parcial.insert(0, "perturbacao", perturbacao)
                caminho = piso_de_ruido.caminho_do_parcial(pasta_de_saida, perturbacao, folha, horizonte)
                caminho.parent.mkdir(parents=True, exist_ok=True)
                parcial.to_csv(caminho, index=False)
    return deslocamentos


def test_piso_juntar_e_medir_com_parciais_fabricados(tmp_path: pathlib.Path, referencia: pd.DataFrame) -> None:
    """40 parciais: delta do `csv` = 0 (identico a referencia); piso = o maior delta; n = 102 em toda celula."""
    pasta_de_saida = tmp_path / "piso_de_ruido"
    registrador = RegistradorDeLog(pasta_de_saida / "piso_de_ruido.log")
    gravar_parciais_do_piso(pasta_de_saida, referencia)
    assert piso_de_ruido.listar_parciais_faltantes(pasta_de_saida) == []

    piso_de_ruido.juntar_e_medir(pasta_de_saida, registrador, time.perf_counter())

    deltas = pd.read_csv(pasta_de_saida / "mae_por_perturbacao.csv")
    assert list(deltas.columns) == ["perturbacao", "folha", "h", "n", "mae", "mae_referencia", "delta"]
    assert len(deltas) == 5 * 2 * 4
    assert (deltas["n"] == N_DA_JANELA).all()
    delta_do_csv = deltas.loc[deltas["perturbacao"] == "csv", "delta"]
    assert (delta_do_csv == 0.0).all()
    assert (deltas.loc[deltas["perturbacao"] != "csv", "delta"] > 0.0).all()

    piso = pd.read_csv(pasta_de_saida / "piso.csv")
    assert len(piso) == 2 * 4
    maior_delta_por_celula = deltas.groupby(["folha", "h"])["delta"].max().reset_index()
    cruzado = piso.merge(maior_delta_por_celula, on=["folha", "h"])
    assert np.allclose(cruzado["piso_de_ruido"], cruzado["delta"], rtol=0.0, atol=1e-12)
    assert np.allclose(piso["duas_vezes_o_piso"], 2.0 * piso["piso_de_ruido"], rtol=0.0, atol=1e-12)
    assert (pasta_de_saida / "previsoes.csv").exists()


def test_piso_rejeita_perturbacao_medida_em_numero_diferente_de_semanas(referencia: pd.DataFrame) -> None:
    """Se uma perturbacao tem n diferente do da referencia (102), a juncao levanta ValueError."""
    mae_da_referencia = piso_de_ruido.calcular_mae_da_referencia()
    linhas = []
    for folha in (5, 20):
        for horizonte in (1, 4, 8, 12):
            linhas.append({"perturbacao": "s1", "folha": folha, "h": horizonte, "n": 102, "mae": 1.0})
    mae_por_perturbacao = pd.DataFrame(linhas)
    piso_de_ruido.conferir_mesmas_semanas_da_referencia(mae_por_perturbacao, mae_da_referencia)

    mae_por_perturbacao.loc[3, "n"] = 101
    with pytest.raises(ValueError, match="n diferente"):
        piso_de_ruido.conferir_mesmas_semanas_da_referencia(mae_por_perturbacao, mae_da_referencia)


def test_a_referencia_certificada_existe_e_nao_foi_alterada_por_estes_testes() -> None:
    """Os testes so LEEM `resultados/referencia/previsoes.csv`; confere que ele esta la, com 6.948 linhas (2 x 3474)."""
    assert CAMINHO_DA_REFERENCIA.exists()
    assert len(ler_previsoes_da_referencia()) == 2 * 3474
