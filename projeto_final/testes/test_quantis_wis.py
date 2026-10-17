"""Testes da E7: ordenacao dos quantis, WIS, cobertura, regua climatologica, composto e a familia F5.

Blocos:
    1. `ordenar_quantis_cruzados`: casos pequenos (ordem ja correta, um cruzamento, empate, varias origens,
       entrada embaralhada, origem incompleta, NaN) e DIFERENCIAL com os 2.318 origens que o antigo ordenou;
    2. WIS e escore de intervalo: conta a mao (dentro, acima, abaixo, nos limites), diferencial contra a
       formula ESCALAR do antigo (transcrita) em entradas aleatorias, e diferencial contra a tabela
       `wis_e_cobertura.csv` salva pelo antigo, recalculada a partir das previsoes salvas;
    3. regua climatologica: exemplos a mao (anos, minimo de 3, ano minimo 2018, NaN, semana certa) e
       diferencial contra a regua salva pelo antigo (WIS 292,684 e n = 96 em h = 1);
    4. composto de quantis, resumo por janela e a comparacao pareada (igual a `estatistica.comparar_pareado`
       quando a perda e o erro absoluto) e a familia F5.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest

from aedes.configuracao import CONFIGURACAO_DADOS
from aedes.dados import montar_tabela_a_partir_dos_bytes
from aedes.estatistica import comparar_pareado, corrigir_por_holm
from aedes.quantis import (
    QUANTIS_DO_WIS,
    contar_origens_com_cruzamento,
    ordenar_quantis_cruzados,
)
from aedes.wis import (
    INTERVALOS_DO_WIS,
    NOME_DA_REGUA_CLIMATOLOGICA,
    calcular_cobertura,
    calcular_escore_de_intervalo,
    calcular_escores_por_origem,
    calcular_quantis_da_regua,
    calcular_wis,
    comparar_wis_pareado,
    executar_familia_f5,
    montar_historico_da_regua,
    montar_quantis_do_composto,
    montar_regua_climatologica,
    parear_escores_por_data_alvo,
    recortar_por_data_alvo,
    resumir_escores_por_janela,
)

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
PASTA_DOS_GABARITOS = PASTA_DO_PROJETO / "testes" / "referencia_antiga"

NOME_DO_MODELO_ANTIGO_PARA_A_FOLHA = {"cenario_adotado": 5, "histgb_folha20": 20}
INICIO_DA_JANELA_ANTIGA = pd.Timestamp("2024-01-01")
FIM_DA_JANELA_ANTIGA = pd.Timestamp("2025-12-31")


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------


def montar_origem(
    valores_por_quantil: list[float],
    data: str = "2024-01-07",
    folha: int = 5,
    horizonte: int = 1,
    real: float = 10.0,
) -> pd.DataFrame:
    """Uma origem: 7 linhas (uma por quantil) com os valores dados na ordem dos niveis."""
    return pd.DataFrame(
        {
            "folha": folha,
            "h": horizonte,
            "data_alvo": pd.Timestamp(data),
            "quantil": list(QUANTIS_DO_WIS),
            "real": real,
            "previsto": valores_por_quantil,
        }
    )


@pytest.fixture(scope="module")
def previsoes_quantis_do_antigo() -> pd.DataFrame:
    """As previsoes dos 7 quantis salvas pela rodada de 26/09 (brutas, ordenadas e a marca de cruzamento)."""
    caminho = PASTA_DOS_GABARITOS / "e7_previsoes_quantis.csv"
    return pd.read_csv(caminho, parse_dates=["data_alvo"], float_precision="round_trip")


@pytest.fixture(scope="module")
def tabela_crua() -> pd.DataFrame:
    """A tabela certificada SEM o corte de maturidade (a regua climatologica a usa assim)."""
    return montar_tabela_a_partir_dos_bytes(CAMINHO_TABELA.read_bytes(), CONFIGURACAO_DADOS)


def converter_o_formato_do_antigo(previsoes_do_antigo: pd.DataFrame) -> pd.DataFrame:
    """Do formato do antigo (`modelo`, `previsto_bruto`) para o de `ordenar_quantis_cruzados` (`folha`, `previsto`)."""
    entrada = previsoes_do_antigo[["modelo", "h", "data_alvo", "quantil", "real", "previsto_bruto"]].copy()
    entrada["folha"] = entrada["modelo"].map(NOME_DO_MODELO_ANTIGO_PARA_A_FOLHA)
    entrada = entrada.rename(columns={"previsto_bruto": "previsto"})
    return entrada[["folha", "h", "data_alvo", "quantil", "real", "previsto"]]


# ---------------------------------------------------------------------------
# 1. Ordenacao dos quantis
# ---------------------------------------------------------------------------


def test_origem_ja_em_ordem_nao_muda_e_nao_e_marcada() -> None:
    """Quantis crescentes: `previsto == previsto_bruto` e `cruzamento_corrigido` falso nas 7 linhas."""
    entrada = montar_origem([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    saida = ordenar_quantis_cruzados(entrada)
    assert list(saida["previsto"]) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    assert list(saida["previsto_bruto"]) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    assert not saida["cruzamento_corrigido"].any()


def test_um_cruzamento_e_corrigido_ordenando_e_marca_a_origem_inteira() -> None:
    """q25 = 9 > q50 = 4: os 7 valores sao ordenados e atribuidos aos niveis em ordem; as 7 linhas ficam marcadas."""
    entrada = montar_origem([1.0, 2.0, 9.0, 4.0, 5.0, 6.0, 7.0])
    saida = ordenar_quantis_cruzados(entrada)
    assert list(saida["previsto"]) == [1.0, 2.0, 4.0, 5.0, 6.0, 7.0, 9.0]
    assert list(saida["previsto_bruto"]) == [1.0, 2.0, 9.0, 4.0, 5.0, 6.0, 7.0]
    assert saida["cruzamento_corrigido"].all()


def test_valores_iguais_entre_niveis_vizinhos_nao_sao_cruzamento() -> None:
    """Empate (`diff == 0`) esta em ordem: sem marca (caso comum com previsao truncada ou quantis baixos iguais)."""
    entrada = montar_origem([0.0, 0.0, 0.0, 1.0, 1.0, 5.0, 5.0])
    saida = ordenar_quantis_cruzados(entrada)
    assert not saida["cruzamento_corrigido"].any()
    assert list(saida["previsto"]) == list(saida["previsto_bruto"])


def test_o_valor_mais_baixo_no_nivel_mais_alto_vai_para_o_nivel_mais_baixo() -> None:
    """Ordem totalmente invertida: o rearranjo inverte de volta (7 6 5 4 3 2 1 -> 1 2 3 4 5 6 7)."""
    saida = ordenar_quantis_cruzados(montar_origem([7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]))
    assert list(saida["previsto"]) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    assert saida["cruzamento_corrigido"].all()


def test_varias_origens_sao_tratadas_separadamente_e_a_entrada_embaralhada_nao_importa() -> None:
    """Duas origens (uma cruzada, outra nao) com as linhas embaralhadas: a saida vem ordenada por (folha, h, data, quantil)."""
    origem_a = montar_origem([1.0, 2.0, 9.0, 4.0, 5.0, 6.0, 7.0], data="2024-01-14")
    origem_b = montar_origem([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], data="2024-01-07")
    entrada = pd.concat([origem_a, origem_b], ignore_index=True).sample(frac=1.0, random_state=3)
    saida = ordenar_quantis_cruzados(entrada)
    assert list(saida["data_alvo"].dt.strftime("%Y-%m-%d")) == ["2024-01-07"] * 7 + ["2024-01-14"] * 7
    assert list(saida["quantil"]) == list(QUANTIS_DO_WIS) * 2
    assert not saida["cruzamento_corrigido"].iloc[:7].any()
    assert saida["cruzamento_corrigido"].iloc[7:].all()
    assert list(saida["previsto"].iloc[7:]) == [1.0, 2.0, 4.0, 5.0, 6.0, 7.0, 9.0]


def test_a_ordenacao_nao_modifica_a_entrada_e_mantem_as_colunas_extras() -> None:
    """A entrada fica intacta; `real` acompanha a origem."""
    entrada = montar_origem([1.0, 2.0, 9.0, 4.0, 5.0, 6.0, 7.0], real=33.0)
    copia = entrada.copy()
    saida = ordenar_quantis_cruzados(entrada)
    pd.testing.assert_frame_equal(entrada, copia, check_exact=True)
    assert (saida["real"] == 33.0).all()


def test_origem_incompleta_ou_com_nivel_a_mais_e_erro() -> None:
    """Falta um nivel (6 linhas) ou o nivel nao e um dos 7: ValueError claro."""
    incompleta = montar_origem([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]).iloc[:6]
    with pytest.raises(ValueError):
        ordenar_quantis_cruzados(incompleta)
    com_nivel_errado = montar_origem([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    com_nivel_errado.loc[3, "quantil"] = 0.55
    with pytest.raises(ValueError, match="niveis"):
        ordenar_quantis_cruzados(com_nivel_errado)


def test_duas_origens_de_tamanho_diferente_uma_com_nivel_faltando_e_outra_completa_e_erro() -> None:
    """14 linhas, mas uma origem tem 8 niveis e a outra 6: os blocos de 7 misturam origens e o erro e levantado."""
    origem_a = montar_origem([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], data="2024-01-07")
    origem_b = montar_origem([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], data="2024-01-14")
    # Move uma linha da origem B para a origem A: 8 na A, 6 na B.
    origem_b.loc[origem_b.index[0], "data_alvo"] = pd.Timestamp("2024-01-07")
    entrada = pd.concat([origem_a, origem_b], ignore_index=True)
    with pytest.raises(ValueError):
        ordenar_quantis_cruzados(entrada)


def test_previsto_ausente_ou_infinito_e_erro() -> None:
    """NaN ou infinito no `previsto`: ValueError (nao ordena lixo)."""
    com_nan = montar_origem([1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0])
    with pytest.raises(ValueError, match="ausente ou infinito"):
        ordenar_quantis_cruzados(com_nan)
    com_infinito = montar_origem([1.0, 2.0, np.inf, 4.0, 5.0, 6.0, 7.0])
    with pytest.raises(ValueError, match="ausente ou infinito"):
        ordenar_quantis_cruzados(com_infinito)


def test_coluna_ausente_levanta_keyerror() -> None:
    """Sem `folha`: KeyError."""
    entrada = montar_origem([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]).drop(columns=["folha"])
    with pytest.raises(KeyError, match="folha"):
        ordenar_quantis_cruzados(entrada)


def test_a_contagem_de_cruzamentos_e_por_folha_e_horizonte() -> None:
    """3 origens na folha 5 / h 1 (1 cruzada) e 1 na folha 20 / h 4 (nenhuma)."""
    origens = [
        montar_origem([1, 2, 3, 4, 5, 6, 7], data="2024-01-07"),
        montar_origem([1, 2, 9, 4, 5, 6, 7], data="2024-01-14"),
        montar_origem([1, 2, 3, 4, 5, 6, 7], data="2024-01-21"),
        montar_origem([1, 2, 3, 4, 5, 6, 7], data="2024-01-07", folha=20, horizonte=4),
    ]
    ordenado = ordenar_quantis_cruzados(pd.concat(origens, ignore_index=True))
    contagem = contar_origens_com_cruzamento(ordenado)
    primeira = contagem.loc[(contagem["folha"] == 5) & (contagem["h"] == 1)].iloc[0]
    assert (primeira["origens"], primeira["com_cruzamento"]) == (3, 1)
    assert primeira["fracao"] == pytest.approx(1 / 3)
    segunda = contagem.loc[(contagem["folha"] == 20) & (contagem["h"] == 4)].iloc[0]
    assert (segunda["origens"], segunda["com_cruzamento"]) == (1, 0)


def test_a_ordenacao_reproduz_a_do_antigo_nas_2318_origens(previsoes_quantis_do_antigo: pd.DataFrame) -> None:
    """DIFERENCIAL: aplicada aos valores brutos do antigo, devolve os mesmos `previsto` e a mesma marca; 1.784 de 2.318 origens."""
    entrada = converter_o_formato_do_antigo(previsoes_quantis_do_antigo)
    saida = ordenar_quantis_cruzados(entrada)

    antigo = previsoes_quantis_do_antigo.copy()
    antigo["folha"] = antigo["modelo"].map(NOME_DO_MODELO_ANTIGO_PARA_A_FOLHA)
    antigo = antigo.sort_values(["folha", "h", "data_alvo", "quantil"]).reset_index(drop=True)

    assert len(saida) == len(antigo) == 2318 * 7
    np.testing.assert_array_equal(saida["previsto"].to_numpy(), antigo["previsto"].to_numpy())
    np.testing.assert_array_equal(saida["cruzamento_corrigido"].to_numpy(), antigo["cruzamento_corrigido"].to_numpy())

    contagem = contar_origens_com_cruzamento(saida)
    assert int(contagem["origens"].sum()) == 2318
    assert int(contagem["com_cruzamento"].sum()) == 1784


# ---------------------------------------------------------------------------
# 2. WIS e escore de intervalo
# ---------------------------------------------------------------------------

# Quantis de uma origem de exemplo: q05 2, q10 4, q25 6, q50 8, q75 12, q90 14, q95 18.
QUANTIS_DO_EXEMPLO = np.array([[2.0, 4.0, 6.0, 8.0, 12.0, 14.0, 18.0]])


def test_o_escore_de_intervalo_dentro_e_a_largura() -> None:
    """Real dentro de [6, 12]: IS_0,5 = 12 - 6 = 6, sem penalidade."""
    escore = calcular_escore_de_intervalo(np.array([10.0]), np.array([6.0]), np.array([12.0]), 0.5)
    assert escore[0] == 6.0


def test_o_escore_de_intervalo_acima_soma_a_penalidade_2_sobre_alpha_vezes_o_excesso() -> None:
    """Real 20 acima de u = 12: 6 + (2/0,5) * (20 - 12) = 6 + 32 = 38."""
    escore = calcular_escore_de_intervalo(np.array([20.0]), np.array([6.0]), np.array([12.0]), 0.5)
    assert escore[0] == 38.0


def test_o_escore_de_intervalo_abaixo_soma_a_penalidade_2_sobre_alpha_vezes_a_falta() -> None:
    """Real 0 abaixo de l = 6: 6 + (2/0,5) * (6 - 0) = 30."""
    escore = calcular_escore_de_intervalo(np.array([0.0]), np.array([6.0]), np.array([12.0]), 0.5)
    assert escore[0] == 30.0


def test_o_escore_de_intervalo_nos_limites_nao_tem_penalidade() -> None:
    """Real exatamente em l ou em u: `y < l` e `y > u` sao estritos, penalidade zero."""
    escore_no_inferior = calcular_escore_de_intervalo(np.array([6.0]), np.array([6.0]), np.array([12.0]), 0.5)
    escore_no_superior = calcular_escore_de_intervalo(np.array([12.0]), np.array([6.0]), np.array([12.0]), 0.5)
    assert escore_no_inferior[0] == 6.0
    assert escore_no_superior[0] == 6.0


def test_o_escore_de_intervalo_imediatamente_fora_do_limite_ja_penaliza() -> None:
    """Real 12 + 1e-9 acima de u: penalidade = (2/0,5) * 1e-9 (continuo no limite)."""
    escore = calcular_escore_de_intervalo(np.array([12.0 + 1e-9]), np.array([6.0]), np.array([12.0]), 0.5)
    assert escore[0] == pytest.approx(6.0 + 4.0 * 1e-9, rel=1e-6)


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.5, 1.5])
def test_alpha_fora_de_0_1_e_erro(alpha: float) -> None:
    """alpha precisa estar em (0, 1) aberto."""
    with pytest.raises(ValueError, match="alpha"):
        calcular_escore_de_intervalo(np.array([1.0]), np.array([0.0]), np.array([2.0]), alpha)


def test_o_wis_do_exemplo_com_real_dentro_e_4_3_sobre_3_5() -> None:
    """y = 10: |y - mediana| = 2; IS_50 = 6, IS_80 = 10, IS_90 = 16 -> (0,5*2 + 0,25*6 + 0,1*10 + 0,05*16)/3,5 = 4,3/3,5."""
    wis = calcular_wis(np.array([10.0]), QUANTIS_DO_EXEMPLO)
    assert wis[0] == pytest.approx(4.3 / 3.5, rel=1e-14)


def test_o_wis_do_exemplo_com_real_acima_de_todos_os_intervalos() -> None:
    """y = 20: IS_50 = 6 + 4*8 = 38; IS_80 = 10 + 10*6 = 70; IS_90 = 16 + 20*2 = 56 -> (6 + 9,5 + 7 + 2,8)/3,5 = 25,3/3,5."""
    wis = calcular_wis(np.array([20.0]), QUANTIS_DO_EXEMPLO)
    assert wis[0] == pytest.approx(25.3 / 3.5, rel=1e-14)


def test_o_wis_do_exemplo_com_real_abaixo_de_todos_os_intervalos() -> None:
    """y = 0: IS_50 = 6 + 4*6 = 30; IS_80 = 10 + 10*4 = 50; IS_90 = 16 + 20*2 = 56 -> (4 + 7,5 + 5 + 2,8)/3,5 = 19,3/3,5."""
    wis = calcular_wis(np.array([0.0]), QUANTIS_DO_EXEMPLO)
    assert wis[0] == pytest.approx(19.3 / 3.5, rel=1e-14)


def test_o_wis_com_previsao_perfeita_e_so_a_largura_dos_intervalos() -> None:
    """Real = mediana, dentro de tudo: WIS = (0,25*IS_50 + 0,1*IS_80 + 0,05*IS_90)/3,5 sem termo da mediana."""
    wis = calcular_wis(np.array([8.0]), QUANTIS_DO_EXEMPLO)
    assert wis[0] == pytest.approx((0.25 * 6.0 + 0.1 * 10.0 + 0.05 * 16.0) / 3.5, rel=1e-14)


def test_o_wis_e_vetorizado_por_origem_e_nao_mistura_as_origens() -> None:
    """Tres origens de uma vez == tres chamadas separadas, na ordem."""
    reais = np.array([10.0, 20.0, 0.0])
    quantis = np.vstack([QUANTIS_DO_EXEMPLO, QUANTIS_DO_EXEMPLO, QUANTIS_DO_EXEMPLO])
    juntos = calcular_wis(reais, quantis)
    separados = [calcular_wis(reais[[i]], quantis[[i]])[0] for i in range(3)]
    np.testing.assert_array_equal(juntos, np.array(separados))


def test_wis_com_matriz_do_formato_errado_e_erro() -> None:
    """Matriz com 6 colunas ou numero de linhas diferente do de reais: ValueError."""
    with pytest.raises(ValueError, match="quantis_previstos"):
        calcular_wis(np.array([1.0]), QUANTIS_DO_EXEMPLO[:, :6])
    with pytest.raises(ValueError, match="quantis_previstos"):
        calcular_wis(np.array([1.0, 2.0]), QUANTIS_DO_EXEMPLO)


def wis_antigo_escalar(real: float, quantis_por_nivel: dict[float, float]) -> float:
    """O `calcular_wis` do antigo (`analises/2026-09-26_wis_na_tabela_restaurada/rodar.py`), transcrito sem mudanca."""
    mediana_prevista = quantis_por_nivel[0.50]
    termo_da_mediana = 0.5 * abs(real - mediana_prevista)
    soma_dos_intervalos = 0.0
    for alpha, nivel_inferior, nivel_superior in ((0.50, 0.25, 0.75), (0.20, 0.10, 0.90), (0.10, 0.05, 0.95)):
        limite_inferior = quantis_por_nivel[nivel_inferior]
        limite_superior = quantis_por_nivel[nivel_superior]
        largura = limite_superior - limite_inferior
        penalidade_por_baixo = 0.0
        if real < limite_inferior:
            penalidade_por_baixo = (2.0 / alpha) * (limite_inferior - real)
        penalidade_por_cima = 0.0
        if real > limite_superior:
            penalidade_por_cima = (2.0 / alpha) * (real - limite_superior)
        escore = largura + penalidade_por_baixo + penalidade_por_cima
        soma_dos_intervalos += (alpha / 2.0) * escore
    return (termo_da_mediana + soma_dos_intervalos) / (3 + 0.5)


def test_o_wis_vetorizado_e_igual_ao_escalar_do_antigo_em_entradas_aleatorias() -> None:
    """DIFERENCIAL: 500 origens aleatorias (reais dentro e fora dos intervalos), diferenca < 1e-12 relativa."""
    gerador = np.random.default_rng(7)
    quantidade = 500
    quantis = np.sort(gerador.uniform(0.0, 300.0, size=(quantidade, 7)), axis=1)
    reais = gerador.uniform(-20.0, 350.0, size=quantidade)
    vetorizado = calcular_wis(reais, quantis)
    for posicao in range(quantidade):
        por_nivel = dict(zip(QUANTIS_DO_WIS, quantis[posicao]))
        esperado = wis_antigo_escalar(float(reais[posicao]), por_nivel)
        assert vetorizado[posicao] == pytest.approx(esperado, rel=1e-12, abs=1e-12)


def test_a_cobertura_inclui_os_limites_e_exclui_o_que_esta_fora() -> None:
    """`l <= y <= u`: em l e em u cobre; epsilon fora nao cobre. Tres intervalos (50, 80 e 90%)."""
    quantis = np.vstack([QUANTIS_DO_EXEMPLO] * 5)
    reais = np.array([6.0, 12.0, 6.0 - 1e-9, 12.0 + 1e-9, 9.0])
    intervalo_de_50 = INTERVALOS_DO_WIS[0]
    cobertura = calcular_cobertura(reais, quantis, intervalo_de_50)
    assert list(cobertura) == [True, True, False, False, True]
    intervalo_de_90 = INTERVALOS_DO_WIS[2]
    assert list(calcular_cobertura(np.array([2.0, 18.0, 1.9, 18.1]), np.vstack([QUANTIS_DO_EXEMPLO] * 4), intervalo_de_90)) == [
        True,
        True,
        False,
        False,
    ]


def test_os_tres_intervalos_do_wis_sao_50_80_e_90_com_alpha_e_niveis_corretos() -> None:
    """alpha = 1 - cobertura; niveis = alpha/2 e 1 - alpha/2; na ordem 50, 80, 90."""
    coberturas = [intervalo.cobertura_nominal for intervalo in INTERVALOS_DO_WIS]
    assert coberturas == [0.50, 0.80, 0.90]
    for intervalo in INTERVALOS_DO_WIS:
        assert intervalo.alpha == pytest.approx(1.0 - intervalo.cobertura_nominal)
        assert intervalo.quantil_inferior == pytest.approx(intervalo.alpha / 2.0)
        assert intervalo.quantil_superior == pytest.approx(1.0 - intervalo.alpha / 2.0)


def montar_escores_do_antigo_por_modelo_e_horizonte(previsoes_do_antigo: pd.DataFrame) -> pd.DataFrame:
    """Escores por origem das previsoes JA ORDENADAS salvas pelo antigo, nos formatos do pacote."""
    escores: list[pd.DataFrame] = []
    for (modelo, horizonte), grupo in previsoes_do_antigo.groupby(["modelo", "h"], sort=False):
        matriz = grupo.pivot(index="data_alvo", columns="quantil", values="previsto").sort_index()
        reais = grupo.drop_duplicates("data_alvo").set_index("data_alvo")["real"].sort_index()
        escores.append(
            calcular_escores_por_origem(
                str(modelo), int(horizonte), pd.Series(matriz.index), reais.reindex(matriz.index), matriz.to_numpy()
            )
        )
    return pd.concat(escores, ignore_index=True)


def test_o_wis_e_a_cobertura_recalculados_das_previsoes_do_antigo_reproduzem_a_tabela_do_antigo(
    previsoes_quantis_do_antigo: pd.DataFrame,
) -> None:
    """DIFERENCIAL: WIS medio, cobertura 50/90 e n de `wis_e_cobertura.csv` (2024-2025) == recalculo nosso, 1e-9."""
    escores = montar_escores_do_antigo_por_modelo_e_horizonte(previsoes_quantis_do_antigo)
    resumo = resumir_escores_por_janela(escores, {"antiga": (INICIO_DA_JANELA_ANTIGA, FIM_DA_JANELA_ANTIGA)})

    tabela_antiga = pd.read_csv(PASTA_DOS_GABARITOS / "e7_wis_e_cobertura.csv")
    antiga_de_2024_2025 = tabela_antiga.loc[
        (tabela_antiga["recorte"] == "2024-2025") & (tabela_antiga["modelo"] != "regua_climatologica")
    ]
    assert len(antiga_de_2024_2025) == 8
    for _, linha_antiga in antiga_de_2024_2025.iterrows():
        escolha = (resumo["modelo"] == linha_antiga["modelo"]) & (resumo["h"] == linha_antiga["h"])
        linha_nova = resumo.loc[escolha].iloc[0]
        assert linha_nova["n"] == linha_antiga["n"]
        assert linha_nova["wis_medio"] == pytest.approx(linha_antiga["wis_medio"], abs=1e-9)
        assert linha_nova["cobertura_50"] == pytest.approx(linha_antiga["cobertura_50"], abs=1e-12)
        assert linha_nova["cobertura_90"] == pytest.approx(linha_antiga["cobertura_90"], abs=1e-12)


def test_as_ancoras_do_wis_da_predeclaracao_saem_das_previsoes_do_antigo(
    previsoes_quantis_do_antigo: pd.DataFrame,
) -> None:
    """Ancoras de 12/10: adotado (folha 5) 101,9 / 215,4 / 288,6 / 300,7 e folha 20 121,3 / 199,0 / 259,0 / 278,6, n = 97."""
    escores = montar_escores_do_antigo_por_modelo_e_horizonte(previsoes_quantis_do_antigo)
    resumo = resumir_escores_por_janela(escores, {"antiga": (INICIO_DA_JANELA_ANTIGA, FIM_DA_JANELA_ANTIGA)})
    esperado = {
        ("cenario_adotado", 1): 101.9,
        ("cenario_adotado", 4): 215.4,
        ("cenario_adotado", 8): 288.6,
        ("cenario_adotado", 12): 300.7,
        ("histgb_folha20", 1): 121.3,
        ("histgb_folha20", 4): 199.0,
        ("histgb_folha20", 8): 259.0,
        ("histgb_folha20", 12): 278.6,
    }
    for (modelo, horizonte), wis_esperado in esperado.items():
        linha = resumo.loc[(resumo["modelo"] == modelo) & (resumo["h"] == horizonte)].iloc[0]
        assert round(float(linha["wis_medio"]), 1) == wis_esperado
        assert linha["n"] == 97


# ---------------------------------------------------------------------------
# 3. Regua climatologica
# ---------------------------------------------------------------------------


def montar_historico_sintetico(casos_por_ano: dict[int, float], semana: int = 10) -> pd.DataFrame:
    """Uma linha por ano na semana dada; a data e o dia 5/mar do ano (so precisa ser unica)."""
    linhas = []
    for ano, casos in casos_por_ano.items():
        linhas.append({"data": pd.Timestamp(f"{ano}-03-05"), "ano": ano, "semana": semana, "casos": casos})
    return pd.DataFrame(linhas)


def test_a_regua_usa_os_quantis_dos_casos_da_mesma_semana_dos_anos_anteriores() -> None:
    """Anos 2018-2021 = 10, 20, 30, 40; alvo em 2022: quantis lineares do np.quantile calculados a mao."""
    historico = montar_historico_sintetico({2018: 10.0, 2019: 20.0, 2020: 30.0, 2021: 40.0, 2022: 999.0})
    quantis = calcular_quantis_da_regua(historico, pd.Timestamp("2022-03-05"))
    assert quantis is not None
    esperado = [11.5, 13.0, 17.5, 25.0, 32.5, 37.0, 38.5]
    np.testing.assert_allclose(quantis, esperado, rtol=1e-14)


def test_a_regua_exige_no_minimo_3_anos_com_dado() -> None:
    """2 anos: sem regua (None); exatamente 3: com regua (limite inclusivo)."""
    com_dois = montar_historico_sintetico({2018: 10.0, 2019: 20.0, 2020: 0.0})
    assert calcular_quantis_da_regua(com_dois, pd.Timestamp("2020-03-05")) is None
    com_tres = montar_historico_sintetico({2018: 10.0, 2019: 20.0, 2020: 30.0, 2021: 0.0})
    assert calcular_quantis_da_regua(com_tres, pd.Timestamp("2021-03-05")) is not None


def test_a_regua_nao_usa_anos_antes_de_2018() -> None:
    """2017 fica de fora: com 2017, 2018, 2019 e alvo em 2020 sobram so 2 anos -> None."""
    historico = montar_historico_sintetico({2017: 500.0, 2018: 10.0, 2019: 20.0, 2020: 0.0})
    assert calcular_quantis_da_regua(historico, pd.Timestamp("2020-03-05")) is None


def test_a_regua_nao_usa_o_ano_da_semana_alvo_nem_anos_posteriores() -> None:
    """Anos iguais ou posteriores ao do alvo nunca entram (a regua e feita so com o passado)."""
    historico = montar_historico_sintetico({2018: 10.0, 2019: 20.0, 2020: 30.0, 2021: 1e6, 2022: 1e6})
    quantis = calcular_quantis_da_regua(historico, pd.Timestamp("2021-03-05"))
    assert quantis is not None
    assert quantis[-1] < 100.0  # nenhum dos 1e6 entrou


def test_a_regua_descarta_semanas_sem_caso_antes_de_contar_os_anos() -> None:
    """Um ano com casos ausentes (NaN) nao conta: 4 anos com 1 NaN = 3 validos (ok); com 2 NaN sobram 2 (None)."""
    com_um_nan = montar_historico_sintetico({2018: 10.0, 2019: np.nan, 2020: 30.0, 2021: 40.0, 2022: 0.0})
    quantis = calcular_quantis_da_regua(com_um_nan, pd.Timestamp("2022-03-05"))
    assert quantis is not None
    np.testing.assert_allclose(quantis[3], 30.0)  # mediana de 10, 30, 40
    com_dois_nan = montar_historico_sintetico({2018: 10.0, 2019: np.nan, 2020: np.nan, 2021: 40.0, 2022: 0.0})
    assert calcular_quantis_da_regua(com_dois_nan, pd.Timestamp("2022-03-05")) is None


def test_a_regua_so_olha_a_mesma_semana_epidemiologica() -> None:
    """Casos de outras semanas dos mesmos anos nao entram."""
    mesma_semana = montar_historico_sintetico({2018: 10.0, 2019: 20.0, 2020: 30.0, 2021: 0.0}, semana=10)
    outra_semana = montar_historico_sintetico({2018: 1e6, 2019: 1e6, 2020: 1e6}, semana=11)
    outra_semana["data"] = outra_semana["data"] + pd.Timedelta(days=7)
    historico = pd.concat([mesma_semana, outra_semana], ignore_index=True)
    quantis = calcular_quantis_da_regua(historico, pd.Timestamp("2021-03-05"))
    assert quantis is not None
    assert quantis[-1] < 100.0


def test_data_alvo_fora_da_tabela_nao_tem_regua() -> None:
    """Data que nao esta no historico: None (nao chuta)."""
    historico = montar_historico_sintetico({2018: 10.0, 2019: 20.0, 2020: 30.0, 2021: 0.0})
    assert calcular_quantis_da_regua(historico, pd.Timestamp("2030-01-06")) is None


def test_a_regua_por_datas_devolve_so_as_datas_com_historico_ordenadas_e_as_colunas_dos_7_niveis() -> None:
    """Quatro datas pedidas (fora de ordem e com repeticao): so as 2 com historico, em ordem crescente."""
    historico = montar_historico_sintetico({2018: 10.0, 2019: 20.0, 2020: 30.0, 2021: 40.0, 2022: 0.0, 2023: 0.0})
    datas_pedidas = pd.Series(
        pd.to_datetime(["2023-03-05", "2019-03-05", "2022-03-05", "2022-03-05"])
    )
    regua = montar_regua_climatologica(historico, datas_pedidas)
    assert list(regua.index) == [pd.Timestamp("2022-03-05"), pd.Timestamp("2023-03-05")]
    assert list(regua.columns) == list(QUANTIS_DO_WIS)


def test_a_regua_das_semanas_do_antigo_reproduz_o_wis_e_a_cobertura_da_tabela_do_antigo(
    tabela_crua: pd.DataFrame, previsoes_quantis_do_antigo: pd.DataFrame
) -> None:
    """DIFERENCIAL: regua com a tabela crua, 2024-2025, h = 1: n = 96, WIS 292,6843 e cobertura 17,7% / 39,6% (26/09)."""
    historico = montar_historico_da_regua(tabela_crua, CONFIGURACAO_DADOS)
    do_antigo_h1 = previsoes_quantis_do_antigo.loc[
        (previsoes_quantis_do_antigo["modelo"] == "cenario_adotado") & (previsoes_quantis_do_antigo["h"] == 1)
    ]
    datas = pd.Series(sorted(do_antigo_h1["data_alvo"].unique()))
    reais = do_antigo_h1.drop_duplicates("data_alvo").set_index("data_alvo")["real"].sort_index()

    regua = montar_regua_climatologica(historico, datas)
    escores = calcular_escores_por_origem(
        NOME_DA_REGUA_CLIMATOLOGICA, 1, pd.Series(regua.index), reais.reindex(regua.index), regua.to_numpy()
    )
    resumo = resumir_escores_por_janela(escores, {"antiga": (INICIO_DA_JANELA_ANTIGA, FIM_DA_JANELA_ANTIGA)})
    linha = resumo.iloc[0]
    assert linha["n"] == 96
    assert linha["wis_medio"] == pytest.approx(292.6843005952381, abs=1e-9)
    assert linha["cobertura_50"] == pytest.approx(0.17708333333333334, abs=1e-12)
    assert linha["cobertura_90"] == pytest.approx(0.3958333333333333, abs=1e-12)


def test_a_regua_com_a_tabela_cortada_ou_crua_e_a_mesma_na_janela_de_avaliacao(tabela_crua: pd.DataFrame) -> None:
    """O corte de maturidade so apaga casos de 2026; para alvos ate 01/02/2026 a regua so usa anos < 2026: nao muda."""
    from aedes.dados import aplicar_corte_de_maturidade

    cortada = aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)
    datas = pd.Series(pd.date_range("2024-01-07", "2026-02-01", freq="7D"))
    regua_da_crua = montar_regua_climatologica(montar_historico_da_regua(tabela_crua, CONFIGURACAO_DADOS), datas)
    regua_da_cortada = montar_regua_climatologica(montar_historico_da_regua(cortada, CONFIGURACAO_DADOS), datas)
    pd.testing.assert_frame_equal(regua_da_crua, regua_da_cortada, check_exact=True)


# ---------------------------------------------------------------------------
# 4. Composto, resumo por janela, comparacao pareada e a familia F5
# ---------------------------------------------------------------------------


def test_o_composto_pega_o_conjunto_de_quantis_da_folha_escolhida_em_cada_semana() -> None:
    """Semana 1: folha 5; semana 2: folha 20; o conjunto de 7 quantis vem inteiro da folha escolhida."""
    datas = pd.to_datetime(["2024-01-07", "2024-01-14"])
    quantis_5 = pd.DataFrame(np.arange(14.0).reshape(2, 7), index=datas, columns=list(QUANTIS_DO_WIS))
    quantis_20 = pd.DataFrame(100.0 + np.arange(14.0).reshape(2, 7), index=datas, columns=list(QUANTIS_DO_WIS))
    escolha = pd.Series([5, 20], index=datas)
    composto = montar_quantis_do_composto(quantis_5, quantis_20, escolha)
    np.testing.assert_array_equal(composto.iloc[0].to_numpy(), quantis_5.iloc[0].to_numpy())
    np.testing.assert_array_equal(composto.iloc[1].to_numpy(), quantis_20.iloc[1].to_numpy())


def test_o_composto_so_cobre_as_datas_da_escolha_e_valida_a_entrada() -> None:
    """Data da escolha sem quantis numa folha, folha diferente de 5 e 20, ou niveis diferentes: ValueError."""
    datas = pd.to_datetime(["2024-01-07", "2024-01-14"])
    quantis = pd.DataFrame(np.zeros((2, 7)), index=datas, columns=list(QUANTIS_DO_WIS))
    with pytest.raises(ValueError, match="sem quantis"):
        montar_quantis_do_composto(quantis, quantis, pd.Series([5, 5], index=pd.to_datetime(["2024-01-07", "2030-01-06"])))
    with pytest.raises(ValueError, match="5 ou 20"):
        montar_quantis_do_composto(quantis, quantis, pd.Series([5, 7], index=datas))
    com_outros_niveis = quantis.copy()
    com_outros_niveis.columns = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    with pytest.raises(ValueError, match="niveis"):
        montar_quantis_do_composto(quantis, com_outros_niveis, pd.Series([5, 5], index=datas))


def montar_escores_sinteticos(modelo: str, horizonte: int, wis: list[float], inicio: str = "2024-01-07") -> pd.DataFrame:
    """Escores por origem de um modelo com WIS dados (real = 10 em todas), em semanas consecutivas."""
    datas = pd.date_range(inicio, periods=len(wis), freq="7D")
    return pd.DataFrame(
        {
            "modelo": modelo,
            "h": horizonte,
            "data_alvo": datas,
            "real": 10.0,
            "wis": wis,
            "cobertura_50": True,
            "cobertura_80": True,
            "cobertura_90": True,
        }
    )


def test_o_resumo_por_janela_inclui_os_limites_e_conta_o_n_de_cada_modelo() -> None:
    """Janela [2024-01-14, 2024-01-28]: entram as datas 14, 21 e 28 (limites incluidos); WIS medio = (2+3+4)/3."""
    escores = montar_escores_sinteticos("folha5", 1, [1.0, 2.0, 3.0, 4.0, 5.0])
    janela = (pd.Timestamp("2024-01-14"), pd.Timestamp("2024-01-28"))
    resumo = resumir_escores_por_janela(escores, {"j": janela})
    assert resumo["n"].iloc[0] == 3
    assert resumo["wis_medio"].iloc[0] == 3.0
    assert resumo["janela"].iloc[0] == "j"
    assert resumo["cobertura_80"].iloc[0] == 1.0


def test_o_resumo_por_janela_com_duas_janelas_gera_uma_linha_por_modelo_horizonte_e_janela() -> None:
    """2 modelos x 1 horizonte x 2 janelas = 4 linhas."""
    escores = pd.concat(
        [montar_escores_sinteticos("folha5", 1, [1.0, 2.0, 3.0]), montar_escores_sinteticos("folha20", 1, [2.0, 3.0, 4.0])]
    )
    janelas = {
        "a": (pd.Timestamp("2024-01-07"), pd.Timestamp("2024-01-14")),
        "b": (pd.Timestamp("2024-01-07"), pd.Timestamp("2024-01-21")),
    }
    assert len(resumir_escores_por_janela(escores, janelas)) == 4


def test_recortar_por_data_alvo_tem_limites_incluidos() -> None:
    """Primeira e ultima datas fazem parte; um dia antes e um dia depois ficam de fora."""
    escores = montar_escores_sinteticos("folha5", 1, [1.0, 2.0, 3.0, 4.0])
    recorte = recortar_por_data_alvo(escores, pd.Timestamp("2024-01-14"), pd.Timestamp("2024-01-21"))
    assert list(recorte["wis"]) == [2.0, 3.0]


def test_o_pareamento_so_mantem_as_datas_em_comum_ordenadas() -> None:
    """A tem 4 semanas e B tem as 3 ultimas: n = 3, ordenado por data, WIS de cada lado nas colunas certas."""
    escores_a = montar_escores_sinteticos("a", 1, [1.0, 2.0, 3.0, 4.0])
    escores_b = montar_escores_sinteticos("b", 1, [30.0, 40.0, 50.0], inicio="2024-01-14")
    pareado = parear_escores_por_data_alvo(escores_a.sample(frac=1.0, random_state=1), escores_b)
    assert list(pareado["wis_a"]) == [2.0, 3.0, 4.0]
    assert list(pareado["wis_b"]) == [30.0, 40.0, 50.0]


def test_o_pareamento_rejeita_data_repetida_real_diferente_e_falta_de_intersecao() -> None:
    """Tres erros de entrada, tres ValueError."""
    escores_a = montar_escores_sinteticos("a", 1, [1.0, 2.0])
    escores_b = montar_escores_sinteticos("b", 1, [3.0, 4.0])
    with pytest.raises(ValueError, match="repetida"):
        parear_escores_por_data_alvo(pd.concat([escores_a, escores_a.iloc[:1]]), escores_b)
    com_real_diferente = escores_b.copy()
    com_real_diferente["real"] = 11.0
    with pytest.raises(ValueError, match="real"):
        parear_escores_por_data_alvo(escores_a, com_real_diferente)
    sem_intersecao = montar_escores_sinteticos("b", 1, [3.0, 4.0], inicio="2030-01-06")
    with pytest.raises(ValueError, match="Nenhuma"):
        parear_escores_por_data_alvo(escores_a, sem_intersecao)


def test_a_comparacao_de_wis_e_igual_a_comparacao_certificada_quando_a_perda_e_o_erro_absoluto() -> None:
    """Se `wis` = |real - previsto|, `comparar_wis_pareado` == `estatistica.comparar_pareado`: n, medias, delta, ganho, IC, DM e p."""
    gerador = np.random.default_rng(11)
    quantidade = 60
    datas = pd.date_range("2024-01-07", periods=quantidade, freq="7D")
    reais = gerador.uniform(0.0, 200.0, size=quantidade)
    previsto_a = reais + gerador.normal(scale=20.0, size=quantidade)
    previsto_b = reais + gerador.normal(scale=35.0, size=quantidade)
    horizonte = 4

    previsoes_a = pd.DataFrame({"data_alvo": datas, "real": reais, "previsto": previsto_a})
    previsoes_b = pd.DataFrame({"data_alvo": datas, "real": reais, "previsto": previsto_b})
    certificada = comparar_pareado(previsoes_a, previsoes_b, horizonte)

    escores_a = pd.DataFrame({"data_alvo": datas, "real": reais, "wis": np.abs(reais - previsto_a)})
    escores_b = pd.DataFrame({"data_alvo": datas, "real": reais, "wis": np.abs(reais - previsto_b)})
    nova = comparar_wis_pareado(escores_a, escores_b, horizonte)

    assert nova.n == certificada.n
    assert nova.wis_a == certificada.mae_a
    assert nova.wis_b == certificada.mae_b
    assert nova.delta == certificada.delta
    assert nova.ganho_pct == certificada.ganho_pct
    assert (nova.ic_inf, nova.ic_sup) == (certificada.ic_inf, certificada.ic_sup)
    assert nova.dm_hln == certificada.dm_hln
    assert nova.p_bruto == certificada.p_bruto


def test_o_sinal_do_delta_e_positivo_quando_o_candidato_tem_wis_menor() -> None:
    """A com WIS menor que B: delta > 0 e ganho > 0; trocar A e B inverte o sinal do delta."""
    datas = pd.date_range("2024-01-07", periods=40, freq="7D")
    gerador = np.random.default_rng(5)
    wis_b = 100.0 + gerador.normal(scale=5.0, size=40)
    wis_a = wis_b - 20.0
    escores_a = pd.DataFrame({"data_alvo": datas, "real": 1.0, "wis": wis_a})
    escores_b = pd.DataFrame({"data_alvo": datas, "real": 1.0, "wis": wis_b})
    a_contra_b = comparar_wis_pareado(escores_a, escores_b, 4)
    b_contra_a = comparar_wis_pareado(escores_b, escores_a, 4)
    assert a_contra_b.delta > 0.0
    assert a_contra_b.ganho_pct > 0.0
    assert a_contra_b.delta == pytest.approx(-b_contra_a.delta)
    assert a_contra_b.ic_inf > 0.0


def test_escores_identicos_dao_delta_zero_e_dm_indefinido_com_p_1() -> None:
    """Perda constante nula: variancia nao positiva mesmo com Bartlett -> DM indefinido, p = 1,0, `variancia_fallback`."""
    escores = montar_escores_sinteticos("a", 1, [5.0] * 30)
    outros = montar_escores_sinteticos("b", 1, [5.0] * 30)
    comparacao = comparar_wis_pareado(escores, outros, 4)
    assert comparacao.delta == 0.0
    assert comparacao.p_bruto == 1.0
    assert comparacao.variancia_fallback is True


def montar_escores_da_familia(
    candidato_vence_a_regua: dict[str, bool],
) -> dict[tuple[str, int], pd.DataFrame]:
    """Escores de 3 candidatos e da regua em h = 1, 4, 8 e 12 (40 semanas): candidato 'vence' = WIS 50 abaixo da regua."""
    gerador = np.random.default_rng(21)
    datas = pd.date_range("2024-01-07", periods=40, freq="7D")
    escores: dict[tuple[str, int], pd.DataFrame] = {}
    for horizonte in (1, 4, 8, 12):
        wis_da_regua = 200.0 + gerador.normal(scale=10.0, size=40)
        escores[(NOME_DA_REGUA_CLIMATOLOGICA, horizonte)] = pd.DataFrame(
            {"modelo": NOME_DA_REGUA_CLIMATOLOGICA, "h": horizonte, "data_alvo": datas, "real": 1.0, "wis": wis_da_regua}
        )
        for nome, vence in candidato_vence_a_regua.items():
            deslocamento = -50.0 if vence else 0.0
            wis_do_candidato = wis_da_regua + deslocamento + gerador.normal(scale=2.0, size=40)
            escores[(nome, horizonte)] = pd.DataFrame(
                {"modelo": nome, "h": horizonte, "data_alvo": datas, "real": 1.0, "wis": wis_do_candidato}
            )
    return escores


def test_a_familia_f5_tem_12_testes_holm_sobre_todos_e_veredito_sem_piso() -> None:
    """3 candidatos x 4 horizontes = 12; p de Holm = `corrigir_por_holm` dos 12 p brutos; quem vence a regua com folga e 'A melhor'."""
    escores = montar_escores_da_familia({"folha5": True, "folha20": False, "composto_N13": True})
    tabela = executar_familia_f5(escores, ("folha5", "folha20", "composto_N13"), (1, 4, 8, 12))
    assert len(tabela) == 12
    assert list(tabela["A"].iloc[:4]) == ["folha5"] * 4
    assert list(tabela["h"].iloc[:4]) == [1, 4, 8, 12]
    assert (tabela["B"] == NOME_DA_REGUA_CLIMATOLOGICA).all()
    assert (tabela["familia"] == "F5").all()
    np.testing.assert_allclose(tabela["p_holm"].to_numpy(), corrigir_por_holm(tabela["p_bruto"].to_numpy()), rtol=1e-14)

    das_vencedoras = tabela.loc[tabela["A"].isin(["folha5", "composto_N13"])]
    assert (das_vencedoras["veredito"] == "A melhor").all()
    assert (das_vencedoras["delta"] > 0).all()
    da_neutra = tabela.loc[tabela["A"] == "folha20"]
    assert (da_neutra["veredito"] == "sem evidencia").all()


def test_a_familia_f5_marca_a_pior_quando_o_candidato_tem_wis_maior_que_a_regua() -> None:
    """Candidato 100 acima da regua em todos os horizontes: veredito 'A pior' (delta < 0 e Holm < 0,05)."""
    escores = montar_escores_da_familia({"folha5": False})
    pior = {}
    for chave, tabela in escores.items():
        copia = tabela.copy()
        if chave[0] == "folha5":
            copia["wis"] = copia["wis"] + 100.0
        pior[chave] = copia
    tabela = executar_familia_f5(pior, ("folha5",), (1, 4, 8, 12))
    assert (tabela["veredito"] == "A pior").all()


def test_a_familia_f5_sem_a_regua_em_algum_horizonte_levanta_keyerror() -> None:
    """Falta a regua em h = 12: KeyError (nao testa com informacao faltando)."""
    escores = montar_escores_da_familia({"folha5": True})
    del escores[(NOME_DA_REGUA_CLIMATOLOGICA, 12)]
    with pytest.raises(KeyError):
        executar_familia_f5(escores, ("folha5",), (1, 4, 8, 12))
