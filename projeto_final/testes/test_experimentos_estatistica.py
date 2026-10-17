"""Fiacao dos scripts E3, familias e E5, SEM treinar modelo e sem escrever no projeto.

Previsoes fabricadas em memoria; os zips DENGBR sao fabricados em `tmp_path`. A tabela certificada
(`dados/tabela_final.csv`) e apenas LIDA para conferir a regua sazonal.
"""

import json
import pathlib
import zipfile

import numpy as np
import pandas as pd
import pytest

import experimentos.e3_composto as e3
import experimentos.e5_alarme as e5
import experimentos.testes_familias as testes_familias
from aedes.bracos import NOMES_DOS_BRACOS
from aedes.composto import montar_composto
from aedes.configuracao import CONFIGURACAO_AVALIACAO, CONFIGURACAO_DADOS
from aedes.familias import NOME_DA_REGUA_SAZONAL, NOME_DO_COMPOSTO, montar_definicoes_das_familias
from aedes.metricas import recortar_janela_de_avaliacao
from experimentos.comum_ciencia import RegistradorDeLog

UMA_SEMANA = pd.Timedelta(weeks=1)
PRIMEIRO_DOMINGO_FABRICADO = pd.Timestamp("2021-01-03")
SEMANAS_FABRICADAS = 270


@pytest.fixture(autouse=True)
def redirecionar_os_logs_para_tmp(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Nenhum teste escreve nos logs reais de `resultados/ciencia/`."""
    monkeypatch.setattr(e3, "REGISTRADOR", RegistradorDeLog(tmp_path / "logs" / "E3_composto.log"))
    monkeypatch.setattr(e5, "REGISTRADOR", RegistradorDeLog(tmp_path / "logs" / "E5_alarme.log"))
    monkeypatch.setattr(testes_familias, "REGISTRADOR", RegistradorDeLog(tmp_path / "logs" / "testes_familias.log"))



def fabricar_previsoes_da_e2(semente: int = 8) -> pd.DataFrame:
    """Previsoes da E2 de mentira: 8 bracos x folhas 5 e 20 x 12 horizontes, 270 semanas-alvo cada."""
    gerador = np.random.default_rng(semente)
    datas = [PRIMEIRO_DOMINGO_FABRICADO + i * UMA_SEMANA for i in range(SEMANAS_FABRICADAS)]
    reais = gerador.uniform(0.0, 600.0, size=SEMANAS_FABRICADAS)
    tabelas = []
    for braco in NOMES_DOS_BRACOS:
        for folha in (5, 20):
            for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
                previstos = reais + gerador.normal(0.0, 40.0, size=SEMANAS_FABRICADAS)
                tabela = pd.DataFrame(
                    {
                        "braco": braco,
                        "folha": folha,
                        "h": horizonte,
                        "data_origem": [data - horizonte * UMA_SEMANA for data in datas],
                        "data_alvo": datas,
                        "real": reais,
                        "previsto": previstos,
                    }
                )
                tabelas.append(tabela)
    return pd.concat(tabelas, ignore_index=True)


# --------------------------------------------------------------------------------------
# E3
# --------------------------------------------------------------------------------------


def test_e3_monta_as_tres_janelas_nos_12_horizontes_e_resume_na_janela_de_avaliacao() -> None:
    previsoes = fabricar_previsoes_da_e2()
    compostos = e3.montar_todos_os_compostos(previsoes)
    assert list(compostos.columns) == list(e3.COLUNAS_DO_ARQUIVO_DE_PREVISOES)
    assert sorted(compostos["N"].unique()) == [8, 13, 26]
    assert sorted(compostos["h"].unique()) == list(range(1, 13))
    assert set(compostos["folha_escolhida"].unique()) <= {5, 20}

    resumo = e3.resumir_na_janela(compostos)
    assert list(resumo.columns) == list(e3.COLUNAS_DO_RESUMO)
    assert len(resumo) == 3 * 12
    datas_na_janela = recortar_janela_de_avaliacao(
        previsoes.loc[(previsoes["braco"] == "completo") & (previsoes["folha"] == 5) & (previsoes["h"] == 1)],
        CONFIGURACAO_AVALIACAO,
    )
    assert (resumo["n"] == len(datas_na_janela)).all()
    assert ((resumo["fracao_folha20"] >= 0.0) & (resumo["fracao_folha20"] <= 1.0)).all()


def test_e3_usa_o_completo_das_duas_folhas_e_nenhum_outro_braco() -> None:
    previsoes = fabricar_previsoes_da_e2()
    esperado = montar_composto(
        previsoes.loc[(previsoes["braco"] == "completo") & (previsoes["folha"] == 5) & (previsoes["h"] == 4)],
        previsoes.loc[(previsoes["braco"] == "completo") & (previsoes["folha"] == 20) & (previsoes["h"] == 4)],
        4,
        13,
    )
    compostos = e3.montar_todos_os_compostos(previsoes)
    do_n_e_h = compostos.loc[(compostos["N"] == 13) & (compostos["h"] == 4)].drop(columns=["N", "h"])
    pd.testing.assert_frame_equal(do_n_e_h.reset_index(drop=True), esperado.reset_index(drop=True))


def test_e3_exige_travas_da_e2_aprovadas(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    caminho_das_travas = tmp_path / "travas.json"
    monkeypatch.setattr(e3, "CAMINHO_DAS_TRAVAS_DA_E2", caminho_das_travas)
    with pytest.raises(FileNotFoundError):
        e3.exigir_travas_da_e2_aprovadas()
    caminho_das_travas.write_text(json.dumps({"todas_passaram": False}), encoding="utf-8")
    with pytest.raises(RuntimeError):
        e3.exigir_travas_da_e2_aprovadas()
    caminho_das_travas.write_text(json.dumps({"todas_passaram": True}), encoding="utf-8")
    e3.exigir_travas_da_e2_aprovadas()


# --------------------------------------------------------------------------------------
# Familias
# --------------------------------------------------------------------------------------


def test_testes_familias_monta_um_candidato_por_nome_e_horizonte_para_os_52_testes() -> None:
    previsoes = fabricar_previsoes_da_e2()
    na_janela = recortar_janela_de_avaliacao(previsoes, CONFIGURACAO_AVALIACAO)
    composto = e3.montar_todos_os_compostos(previsoes)
    composto_na_janela = recortar_janela_de_avaliacao(composto.loc[composto["N"] == 13], CONFIGURACAO_AVALIACAO)
    grade = na_janela.loc[(na_janela["braco"] == "completo") & (na_janela["folha"] == 5)]
    regua = grade[["h", "data_alvo", "real", "previsto"]].copy()
    regua["previsto"] = regua["real"]

    definicoes = montar_definicoes_das_familias()
    por_candidato = testes_familias.montar_previsoes_por_candidato(definicoes, na_janela, composto_na_janela, regua)
    for definicao in definicoes:
        assert (definicao.nome_a, definicao.horizonte) in por_candidato
        assert (definicao.nome_b, definicao.horizonte) in por_candidato
    do_f5 = por_candidato[("completo@f5", 8)]
    esperado = na_janela.loc[(na_janela["braco"] == "completo") & (na_janela["folha"] == 5) & (na_janela["h"] == 8)]
    assert list(do_f5["previsto"]) == list(esperado["previsto"])
    do_f20 = por_candidato[("completo@f20", 8)]
    esperado_20 = na_janela.loc[(na_janela["braco"] == "completo") & (na_janela["folha"] == 20) & (na_janela["h"] == 8)]
    assert list(do_f20["previsto"]) == list(esperado_20["previsto"])
    assert por_candidato[(NOME_DO_COMPOSTO, 4)]["data_alvo"].is_monotonic_increasing
    assert (NOME_DA_REGUA_SAZONAL, 12) in por_candidato


def test_testes_familias_rejeita_candidato_sem_fonte() -> None:
    from aedes.familias import DefinicaoDoTeste

    na_janela = recortar_janela_de_avaliacao(fabricar_previsoes_da_e2(), CONFIGURACAO_AVALIACAO)
    definicao = DefinicaoDoTeste("F1", 1, "braco_inexistente@f5", "completo@f5", (5,))
    with pytest.raises(KeyError):
        testes_familias.montar_previsoes_por_candidato([definicao], na_janela, na_janela, na_janela)


def test_regua_sazonal_e_o_caso_de_52_semanas_antes_na_tabela_cortada() -> None:
    """A regua da etapa devolve, para cada `data_alvo`, os casos 52 semanas antes (tabela cortada certificada)."""
    previsoes = fabricar_previsoes_da_e2()
    na_janela = recortar_janela_de_avaliacao(previsoes, CONFIGURACAO_AVALIACAO)
    regua = testes_familias.montar_previsoes_da_regua_sazonal(na_janela)
    assert set(regua["braco"]) == {"regua_sazonal"}
    tabela_cortada = testes_familias.carregar_tabela_cortada()
    casos_por_data = tabela_cortada.set_index(CONFIGURACAO_DADOS.coluna_de_data)[CONFIGURACAO_DADOS.coluna_de_casos]
    primeira_linha = regua.iloc[0]
    data_um_ano_antes = primeira_linha["data_alvo"] - 52 * UMA_SEMANA
    assert primeira_linha["previsto"] == casos_por_data.loc[data_um_ano_antes]
    assert primeira_linha["real"] == casos_por_data.loc[primeira_linha["data_alvo"]]


def test_conferencia_do_real_da_regua_reprova_quando_diverge() -> None:
    na_janela = recortar_janela_de_avaliacao(fabricar_previsoes_da_e2(), CONFIGURACAO_AVALIACAO)
    regua = na_janela.loc[(na_janela["braco"] == "completo") & (na_janela["folha"] == 5), ["h", "data_alvo", "real", "previsto"]].copy()
    testes_familias.conferir_real_da_regua_contra_a_e2(regua, na_janela)
    regua.iloc[3, regua.columns.get_loc("real")] += 1.0
    with pytest.raises(ValueError):
        testes_familias.conferir_real_da_regua_contra_a_e2(regua, na_janela)


# --------------------------------------------------------------------------------------
# E5
# --------------------------------------------------------------------------------------


def test_e5_tabela_do_alarme_tem_17_linhas_por_horizonte_e_o_mesmo_denominador_para_todos() -> None:
    previsoes = fabricar_previsoes_da_e2()
    na_janela = recortar_janela_de_avaliacao(previsoes, CONFIGURACAO_AVALIACAO)
    # um braco com semanas a mais (como os bracos sem vetor, 109 x 102): tira 5 semanas do `completo`
    semanas_do_completo = na_janela.loc[
        (na_janela["braco"] == "completo") & (na_janela["folha"] == 5) & (na_janela["h"] == 1), "data_alvo"
    ].tolist()
    semanas_retiradas = set(semanas_do_completo[:5])
    retirar = (na_janela["braco"] == "completo") & na_janela["data_alvo"].isin(semanas_retiradas)
    na_janela_com_buraco = na_janela.loc[~retirar]
    composto = e3.montar_todos_os_compostos(previsoes)
    composto_na_janela = recortar_janela_de_avaliacao(composto.loc[composto["N"] == 13], CONFIGURACAO_AVALIACAO)

    tabela = e5.montar_tabela_do_alarme(na_janela_com_buraco, composto_na_janela, 421.0)
    assert len(tabela) == 3 * (8 * 2 + 1)
    assert list(tabela.columns) == list(e5.COLUNAS_DO_ALARME)
    assert sorted(tabela["h"].unique()) == [1, 4, 8]
    # o denominador comum sao as semanas do `completo` folha 5 no h; todo candidato e medido nelas
    semanas_restantes = len(semanas_do_completo) - 5
    do_h1_sem_vetor = tabela.loc[(tabela["h"] == 1) & (tabela["braco"] == "sem_vetor") & (tabela["folha"] == 5)]
    assert int(do_h1_sem_vetor["n"].iloc[0]) == semanas_restantes
    do_h1_composto = tabela.loc[(tabela["h"] == 1) & (tabela["braco"] == NOME_DO_COMPOSTO)]
    assert int(do_h1_composto["n"].iloc[0]) == semanas_restantes
    assert (tabela["VP"] + tabela["FN"] + tabela["FP"] + tabela["VN"] == tabela["n"]).all()


def fabricar_zip_de_fichas(caminho_do_zip: pathlib.Path, linhas: list[str]) -> None:
    """Zip com um unico CSV no formato DENGBR (colunas extras incluidas)."""
    cabecalho = "NU_NOTIFIC,ID_MUNICIP,ID_MN_RESI,CLASSI_FIN,DT_SIN_PRI,DT_ENCERRA,OUTRA"
    conteudo = "\n".join([cabecalho, *linhas]) + "\n"
    with zipfile.ZipFile(caminho_do_zip, "w") as arquivo_zip:
        arquivo_zip.writestr("DENGBRXX.csv", conteudo)


def test_e5_le_zip_em_pedacos_e_soma_as_contagens(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    linhas = [
        "1,431490,431490,10,2018-02-01,2018-03-01,x",
        "2,431490,430000,11,2019-02-01,2019-03-01,x",
        "3,430000,431490,12,2020-02-01,2020-03-01,x",
        "4,431490,431490,5,2021-02-01,2021-03-01,x",
        "5,431490,431490,10,2024-02-01,2024-03-01,x",
        "6,431490,431490,10,2022-02-01,2022-03-01,x",
        "7,431490,431490,13,2022-02-01,2022-03-01,x",
    ]
    caminho = tmp_path / "DENGBRXX.csv.zip"
    fabricar_zip_de_fichas(caminho, linhas)
    monkeypatch.setattr(e5, "LINHAS_POR_PEDACO", 3)
    contagem, linhas_lidas = e5.contar_confirmados_de_um_zip(caminho)
    assert linhas_lidas == 7
    assert contagem.por_notificacao == 3  # fichas 1, 2 e 6
    assert contagem.por_residencia == 3  # fichas 1, 3 e 6


def test_e5_zip_com_mais_de_um_arquivo_e_rejeitado(tmp_path: pathlib.Path) -> None:
    caminho = tmp_path / "duplo.zip"
    with zipfile.ZipFile(caminho, "w") as arquivo_zip:
        arquivo_zip.writestr("a.csv", "x\n")
        arquivo_zip.writestr("b.csv", "y\n")
    with pytest.raises(ValueError):
        e5.contar_confirmados_de_um_zip(caminho)
