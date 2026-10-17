"""Testes de unidade de `aedes.dados` e `aedes.configuracao` com tabelas sinteticas.

Cada teste monta uma tabela pequena de domingos consecutivos (sem ler arquivo)
e confere um caso-limite do corte de maturidade ou da validacao.
"""

import dataclasses
import hashlib

import numpy as np
import pandas as pd
import pytest

from aedes.configuracao import CONFIGURACAO_DADOS, ConfiguracaoDados
from aedes.dados import (
    aplicar_corte_de_maturidade,
    montar_tabela_a_partir_dos_bytes,
    obter_ultima_semana_com_caso,
    validar_esquema,
    validar_impressao_digital,
)

PRIMEIRO_DOMINGO_SINTETICO = pd.Timestamp("2020-01-05")
COLUNA_DE_DATA = CONFIGURACAO_DADOS.coluna_de_data
COLUNA_DE_CASOS = CONFIGURACAO_DADOS.coluna_de_casos
COLUNA_EXTRA_DE_TEXTO = "fonte"
SHA256_QUALQUER = "0" * 64


def montar_configuracao_sintetica(
    semanas: int, semanas_corte_maturidade: int
) -> ConfiguracaoDados:
    """Configuracao para tabelas sinteticas: so muda forma, primeira data e corte."""
    colunas_da_tabela_sintetica = len(CONFIGURACAO_DADOS.colunas_obrigatorias) + 1
    return dataclasses.replace(
        CONFIGURACAO_DADOS,
        linhas_esperadas=semanas,
        colunas_esperadas=colunas_da_tabela_sintetica,
        primeira_data_da_grade=PRIMEIRO_DOMINGO_SINTETICO,
        semanas_corte_maturidade=semanas_corte_maturidade,
    )


def montar_tabela_sintetica(casos_por_semana: list[float]) -> pd.DataFrame:
    """Tabela de domingos consecutivos; `casos_por_semana` define os casos de cada semana."""
    semanas = len(casos_por_semana)
    datas = pd.date_range(PRIMEIRO_DOMINGO_SINTETICO, periods=semanas, freq="W-SUN")
    tabela = pd.DataFrame(
        {
            COLUNA_DE_DATA: datas,
            "semana": np.arange(1, semanas + 1),
            COLUNA_DE_CASOS: np.array(casos_por_semana, dtype="float64"),
            "temp_media": np.linspace(15.0, 25.0, semanas),
            "temp_max": np.linspace(20.0, 30.0, semanas),
            "umid_media": np.linspace(60.0, 80.0, semanas),
            "pressao_media": np.linspace(1010.0, 1020.0, semanas),
            "aedes_aegypti_por_armadilha": np.linspace(0.1, 0.9, semanas),
            COLUNA_EXTRA_DE_TEXTO: ["secretaria"] * semanas,
        }
    )
    return tabela


def semanas_com_caso_apos_corte(tabela_cortada: pd.DataFrame) -> list[int]:
    """Posicoes (0, 1, 2...) das semanas cujo caso sobrou nao ausente."""
    mascara_com_caso = tabela_cortada[COLUNA_DE_CASOS].notna().to_numpy()
    posicoes = np.flatnonzero(mascara_com_caso)
    return posicoes.tolist()


# --- Corte de maturidade: limites da regra -----------------------------------


def test_data_exatamente_no_limite_e_mantida_e_a_seguinte_e_apagada() -> None:
    """Ultima semana com caso = posicao 9; corte 3 -> limite = posicao 6 (mantida); 7 a 9 apagadas."""
    casos = [10.0] * 10 + [np.nan] * 5
    tabela = montar_tabela_sintetica(casos)
    configuracao = montar_configuracao_sintetica(semanas=15, semanas_corte_maturidade=3)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    assert semanas_com_caso_apos_corte(tabela_cortada) == [0, 1, 2, 3, 4, 5, 6]
    ultima_mantida = obter_ultima_semana_com_caso(tabela_cortada, configuracao)
    assert ultima_mantida == tabela[COLUNA_DE_DATA].iloc[6]


def test_ultimo_caso_mantido_cai_exatamente_na_semana_limite() -> None:
    """Casos nas posicoes 0 e 3, corte 3: limite = posicao 0, que e mantida; a posicao 3 e apagada."""
    casos = [5.0, np.nan, np.nan, 7.0, np.nan, np.nan]
    tabela = montar_tabela_sintetica(casos)
    configuracao = montar_configuracao_sintetica(semanas=6, semanas_corte_maturidade=3)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    assert semanas_com_caso_apos_corte(tabela_cortada) == [0]
    assert tabela_cortada[COLUNA_DE_CASOS].iloc[0] == 5.0
    ultima_mantida = obter_ultima_semana_com_caso(tabela_cortada, configuracao)
    assert ultima_mantida == PRIMEIRO_DOMINGO_SINTETICO


def test_serie_com_um_unico_caso_tem_esse_caso_apagado() -> None:
    """Um caso so: ele e a propria ultima semana com caso, logo fica acima do limite."""
    casos = [np.nan, np.nan, 4.0, np.nan]
    tabela = montar_tabela_sintetica(casos)
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    assert semanas_com_caso_apos_corte(tabela_cortada) == []


def test_contagem_parte_da_ultima_semana_com_caso_e_nao_do_fim_da_tabela() -> None:
    """Casos ate a posicao 5 e tabela ate a 14: o corte de 2 apaga as posicoes 4 e 5, nao as 13 e 14."""
    casos = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] + [np.nan] * 9
    tabela = montar_tabela_sintetica(casos)
    configuracao = montar_configuracao_sintetica(semanas=15, semanas_corte_maturidade=2)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    assert semanas_com_caso_apos_corte(tabela_cortada) == [0, 1, 2, 3]


def test_serie_sem_nenhum_caso_devolve_copia_igual_e_nao_levanta_erro() -> None:
    """Sem caso nenhum nao ha ultima semana: nada e apagado (como no codigo antigo)."""
    tabela = montar_tabela_sintetica([np.nan] * 6)
    configuracao = montar_configuracao_sintetica(semanas=6, semanas_corte_maturidade=3)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    pd.testing.assert_frame_equal(tabela_cortada, tabela)
    assert tabela_cortada is not tabela


def test_ultima_semana_com_caso_de_serie_sem_caso_levanta_erro_claro() -> None:
    """Pedir a ultima semana com caso de uma serie vazia de casos e erro, nao NaT."""
    tabela = montar_tabela_sintetica([np.nan] * 4)
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    with pytest.raises(ValueError, match="nenhuma semana com caso"):
        obter_ultima_semana_com_caso(tabela, configuracao)


def test_corte_zero_nao_apaga_nada() -> None:
    """semanas_corte_maturidade = 0 desliga o corte: a saida e igual a entrada."""
    casos = [1.0, 2.0, 3.0, 4.0, np.nan]
    tabela = montar_tabela_sintetica(casos)
    configuracao = montar_configuracao_sintetica(semanas=5, semanas_corte_maturidade=0)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    pd.testing.assert_frame_equal(tabela_cortada, tabela)
    assert semanas_com_caso_apos_corte(tabela_cortada) == [0, 1, 2, 3]


# --- Corte de maturidade: nulos, zeros e imutabilidade -----------------------


def test_nan_no_meio_da_serie_continua_nan_e_nunca_vira_zero() -> None:
    """Buraco de casos no meio fica NaN; zero verdadeiro fica zero; so o fim e apagado."""
    casos = [3.0, np.nan, 0.0, np.nan, 8.0, 9.0, 10.0, 11.0]
    tabela = montar_tabela_sintetica(casos)
    configuracao = montar_configuracao_sintetica(semanas=8, semanas_corte_maturidade=2)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    casos_cortados = tabela_cortada[COLUNA_DE_CASOS].to_numpy()
    assert casos_cortados[0] == 3.0
    assert np.isnan(casos_cortados[1])
    assert casos_cortados[2] == 0.0
    assert np.isnan(casos_cortados[3])
    assert casos_cortados[4] == 8.0
    assert casos_cortados[5] == 9.0
    assert np.isnan(casos_cortados[6])
    assert np.isnan(casos_cortados[7])
    quantidade_de_zeros = int((casos_cortados == 0.0).sum())
    assert quantidade_de_zeros == 1


def test_entrada_nao_e_modificada_e_a_saida_e_outro_objeto() -> None:
    """A funcao devolve DataFrame novo; alterar a saida nao toca a entrada."""
    casos = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    tabela = montar_tabela_sintetica(casos)
    copia_da_entrada = tabela.copy()
    configuracao = montar_configuracao_sintetica(semanas=6, semanas_corte_maturidade=2)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    pd.testing.assert_frame_equal(tabela, copia_da_entrada)
    assert tabela_cortada is not tabela

    tabela_cortada[COLUNA_DE_CASOS] = 999.0
    pd.testing.assert_frame_equal(tabela, copia_da_entrada)


def test_so_a_coluna_de_casos_muda_e_colunas_e_indice_ficam_iguais() -> None:
    """Ordem e nomes das colunas, indice e as demais colunas saem identicos a entrada."""
    casos = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    tabela = montar_tabela_sintetica(casos)
    configuracao = montar_configuracao_sintetica(semanas=6, semanas_corte_maturidade=2)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    assert list(tabela_cortada.columns) == list(tabela.columns)
    pd.testing.assert_index_equal(tabela_cortada.index, tabela.index)
    colunas_sem_casos = [nome for nome in tabela.columns if nome != COLUNA_DE_CASOS]
    pd.testing.assert_frame_equal(tabela_cortada[colunas_sem_casos], tabela[colunas_sem_casos])


def test_indice_nao_sequencial_e_preservado() -> None:
    """O corte alinha por indice: um indice embaralhado/nao sequencial sai igual e cortado certo."""
    casos = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    tabela = montar_tabela_sintetica(casos)
    tabela.index = pd.Index([50, 10, 40, 20, 30, 0])
    configuracao = montar_configuracao_sintetica(semanas=6, semanas_corte_maturidade=2)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    pd.testing.assert_index_equal(tabela_cortada.index, tabela.index)
    casos_cortados = tabela_cortada[COLUNA_DE_CASOS].to_numpy()
    assert casos_cortados[:4].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert np.isnan(casos_cortados[4:]).all()


def test_casos_inteiros_saem_como_float_com_nan() -> None:
    """Casos em int64 precisam virar float64 para guardar NaN; os valores mantidos nao mudam."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    tabela[COLUNA_DE_CASOS] = tabela[COLUNA_DE_CASOS].astype("int64")
    configuracao = montar_configuracao_sintetica(semanas=6, semanas_corte_maturidade=2)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    assert tabela_cortada[COLUNA_DE_CASOS].dtype == np.dtype("float64")
    assert tabela_cortada[COLUNA_DE_CASOS].iloc[:4].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert tabela[COLUNA_DE_CASOS].dtype == np.dtype("int64")


def test_corte_maior_que_a_serie_apaga_todos_os_casos() -> None:
    """Corte de 100 semanas numa serie de 6: o limite cai antes da grade, e toda data fica acima dele."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    configuracao = montar_configuracao_sintetica(semanas=6, semanas_corte_maturidade=100)

    tabela_cortada = aplicar_corte_de_maturidade(tabela, configuracao)

    assert semanas_com_caso_apos_corte(tabela_cortada) == []


def test_corte_sem_coluna_de_casos_levanta_keyerror_com_nome() -> None:
    """Faltar a coluna de casos e erro claro, nao um erro obscuro adiante."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0])
    tabela_sem_casos = tabela.drop(columns=[COLUNA_DE_CASOS])
    configuracao = montar_configuracao_sintetica(semanas=3, semanas_corte_maturidade=1)

    with pytest.raises(KeyError, match=COLUNA_DE_CASOS):
        aplicar_corte_de_maturidade(tabela_sem_casos, configuracao)


def test_corte_com_data_em_texto_levanta_valueerror() -> None:
    """Data em texto (nao convertida) compararia errado; a funcao recusa."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0])
    tabela[COLUNA_DE_DATA] = tabela[COLUNA_DE_DATA].dt.strftime("%Y-%m-%d")
    configuracao = montar_configuracao_sintetica(semanas=3, semanas_corte_maturidade=1)

    with pytest.raises(ValueError, match="deve ser de data"):
        aplicar_corte_de_maturidade(tabela, configuracao)


# --- Configuracao -------------------------------------------------------------


def test_configuracao_e_imutavel() -> None:
    """A configuracao padrao nao aceita alteracao de campo."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        CONFIGURACAO_DADOS.semanas_corte_maturidade = 0  # type: ignore[misc]


def test_configuracao_padrao_tem_as_ancoras_do_ciclo_1() -> None:
    """Valores padrao: 12 semanas de corte, 725 x 36, grade que comeca em 23/09/2012."""
    assert CONFIGURACAO_DADOS.semanas_corte_maturidade == 12
    assert CONFIGURACAO_DADOS.linhas_esperadas == 725
    assert CONFIGURACAO_DADOS.colunas_esperadas == 36
    assert CONFIGURACAO_DADOS.primeira_data_da_grade == pd.Timestamp("2012-09-23")
    assert CONFIGURACAO_DADOS.sha256_esperado_da_tabela.startswith("6f34b8549009c01b")


def test_configuracao_rejeita_corte_negativo() -> None:
    """Corte negativo nao faz sentido; falha na criacao da configuracao."""
    with pytest.raises(ValueError, match="semanas_corte_maturidade"):
        dataclasses.replace(CONFIGURACAO_DADOS, semanas_corte_maturidade=-1)


def test_configuracao_rejeita_hash_malformado() -> None:
    """Hash com tamanho errado ou caractere nao hexadecimal falha na criacao."""
    with pytest.raises(ValueError, match="64 caracteres"):
        dataclasses.replace(CONFIGURACAO_DADOS, sha256_esperado_da_tabela="abc")
    with pytest.raises(ValueError, match="64 caracteres"):
        dataclasses.replace(CONFIGURACAO_DADOS, sha256_esperado_da_tabela="z" * 64)


# --- Impressao digital --------------------------------------------------------


def test_hash_correto_passa_inclusive_em_maiusculas() -> None:
    """O sha256 do conteudo passa, escrito em minusculas ou maiusculas."""
    conteudo = b"semana,casos\n2020-01-05,1\n"
    sha256_do_conteudo = hashlib.sha256(conteudo).hexdigest()

    validar_impressao_digital(conteudo, sha256_do_conteudo)
    validar_impressao_digital(conteudo, sha256_do_conteudo.upper())


def test_hash_errado_levanta_erro_com_os_dois_hashes() -> None:
    """Hash diferente falha e a mensagem mostra o calculado e o esperado."""
    conteudo = b"semana,casos\n2020-01-05,1\n"
    sha256_do_conteudo = hashlib.sha256(conteudo).hexdigest()

    with pytest.raises(ValueError, match="diverge") as erro:
        validar_impressao_digital(conteudo, SHA256_QUALQUER)

    assert sha256_do_conteudo in str(erro.value)
    assert SHA256_QUALQUER in str(erro.value)


def test_um_byte_diferente_muda_o_hash_e_falha() -> None:
    """Conteudo adulterado em um byte e recusado contra o hash do original."""
    conteudo_original = b"semana,casos\n2020-01-05,1\n"
    sha256_do_original = hashlib.sha256(conteudo_original).hexdigest()
    conteudo_adulterado = b"semana,casos\n2020-01-05,2\n"

    with pytest.raises(ValueError, match="diverge"):
        validar_impressao_digital(conteudo_adulterado, sha256_do_original)


# --- Esquema -------------------------------------------------------------------


def test_tabela_sintetica_valida_passa() -> None:
    """Tabela correta (domingos consecutivos, colunas e tipos certos) nao levanta erro."""
    tabela = montar_tabela_sintetica([1.0, 2.0, np.nan, 4.0, 5.0])
    configuracao = montar_configuracao_sintetica(semanas=5, semanas_corte_maturidade=2)

    validar_esquema(tabela, configuracao)


def test_coluna_obrigatoria_faltando_falha_com_o_nome_da_coluna() -> None:
    """Sem `temp_media` a validacao levanta KeyError citando a coluna."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    tabela_sem_clima = tabela.drop(columns=["temp_media"])
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    with pytest.raises(KeyError, match="temp_media"):
        validar_esquema(tabela_sem_clima, configuracao)


def test_forma_diferente_da_esperada_falha() -> None:
    """Uma linha a menos que o esperado e erro, com a forma encontrada na mensagem."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    configuracao = montar_configuracao_sintetica(semanas=5, semanas_corte_maturidade=2)

    with pytest.raises(ValueError, match="forma"):
        validar_esquema(tabela, configuracao)


def test_data_que_nao_e_domingo_falha() -> None:
    """Uma data de sabado na grade falha, citando a data."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    sabado = pd.Timestamp("2020-01-18")
    tabela.loc[2, COLUNA_DE_DATA] = sabado
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    with pytest.raises(ValueError, match="nao sao domingo") as erro:
        validar_esquema(tabela, configuracao)

    assert "2020-01-18" in str(erro.value)


def test_buraco_na_grade_falha() -> None:
    """Faltar uma semana (salto de 14 dias) falha, mesmo com a contagem de linhas certa."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0, 5.0])
    datas_com_buraco = tabela[COLUNA_DE_DATA].copy()
    datas_com_buraco.iloc[3:] = datas_com_buraco.iloc[3:] + pd.Timedelta(weeks=1)
    tabela[COLUNA_DE_DATA] = datas_com_buraco
    configuracao = montar_configuracao_sintetica(semanas=5, semanas_corte_maturidade=2)

    with pytest.raises(ValueError, match="Buraco"):
        validar_esquema(tabela, configuracao)


def test_data_duplicada_falha() -> None:
    """Duas linhas na mesma semana falham antes de qualquer outra verificacao de grade."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    tabela.loc[3, COLUNA_DE_DATA] = tabela.loc[2, COLUNA_DE_DATA]
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    with pytest.raises(ValueError, match="duplicadas"):
        validar_esquema(tabela, configuracao)


def test_datas_fora_de_ordem_falham() -> None:
    """Linhas trocadas de lugar (sem duplicata) falham por ordem."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    datas_trocadas = tabela[COLUNA_DE_DATA].to_numpy().copy()
    datas_trocadas[[1, 2]] = datas_trocadas[[2, 1]]
    tabela[COLUNA_DE_DATA] = datas_trocadas
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    with pytest.raises(ValueError, match="ordem crescente"):
        validar_esquema(tabela, configuracao)


def test_grade_que_comeca_em_outra_data_falha() -> None:
    """Grade correta, mas deslocada uma semana em relacao a data inicial esperada, falha."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    tabela[COLUNA_DE_DATA] = tabela[COLUNA_DE_DATA] + pd.Timedelta(weeks=1)
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    with pytest.raises(ValueError, match="A grade comeca em"):
        validar_esquema(tabela, configuracao)


def test_data_ausente_ou_em_texto_falha() -> None:
    """Data em texto e data ausente (NaT) sao recusadas com mensagem propria."""
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    tabela_em_texto = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    tabela_em_texto[COLUNA_DE_DATA] = tabela_em_texto[COLUNA_DE_DATA].dt.strftime("%Y-%m-%d")
    with pytest.raises(ValueError, match="deve ser de data"):
        validar_esquema(tabela_em_texto, configuracao)

    tabela_com_nat = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    tabela_com_nat.loc[1, COLUNA_DE_DATA] = pd.NaT
    with pytest.raises(ValueError, match="ausentes"):
        validar_esquema(tabela_com_nat, configuracao)


def test_coluna_obrigatoria_em_texto_falha() -> None:
    """Uma coluna numerica obrigatoria lida como texto e recusada."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0, 4.0])
    tabela["umid_media"] = ["60", "65", "70", "75"]
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    with pytest.raises(ValueError, match="umid_media"):
        validar_esquema(tabela, configuracao)


def test_casos_infinitos_ou_negativos_falham() -> None:
    """Casos com infinito ou valor negativo sao recusados; ausente (NaN) e aceito."""
    configuracao = montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=2)

    tabela_com_infinito = montar_tabela_sintetica([1.0, np.inf, 3.0, 4.0])
    with pytest.raises(ValueError, match="infinito"):
        validar_esquema(tabela_com_infinito, configuracao)

    tabela_com_negativo = montar_tabela_sintetica([1.0, -2.0, 3.0, 4.0])
    with pytest.raises(ValueError, match="negativo"):
        validar_esquema(tabela_com_negativo, configuracao)

    tabela_com_ausente = montar_tabela_sintetica([1.0, np.nan, 3.0, 4.0])
    validar_esquema(tabela_com_ausente, configuracao)


# --- Carga a partir de bytes ----------------------------------------------------


def montar_csv_sintetico_em_bytes(tabela: pd.DataFrame) -> bytes:
    """Serializa uma tabela sintetica como o CSV da tabela_final (datas AAAA-MM-DD)."""
    texto_csv = tabela.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d")
    return texto_csv.encode("utf-8")


def test_montar_tabela_a_partir_dos_bytes_valida_e_converte_a_data() -> None:
    """Com hash certo, devolve a tabela com a data ja em formato de data."""
    tabela = montar_tabela_sintetica([1.0, 2.0, np.nan, 4.0, 5.0])
    conteudo = montar_csv_sintetico_em_bytes(tabela)
    configuracao_base = montar_configuracao_sintetica(semanas=5, semanas_corte_maturidade=2)
    configuracao = dataclasses.replace(
        configuracao_base, sha256_esperado_da_tabela=hashlib.sha256(conteudo).hexdigest()
    )

    tabela_lida = montar_tabela_a_partir_dos_bytes(conteudo, configuracao)

    assert pd.api.types.is_datetime64_any_dtype(tabela_lida[COLUNA_DE_DATA])
    assert list(tabela_lida.columns) == list(tabela.columns)
    assert tabela_lida[COLUNA_DE_DATA].iloc[0] == PRIMEIRO_DOMINGO_SINTETICO
    assert tabela_lida[COLUNA_DE_CASOS].isna().tolist() == [False, False, True, False, False]


def test_montar_tabela_a_partir_dos_bytes_com_hash_errado_falha_antes_de_ler() -> None:
    """Hash errado para na carga, sem chegar ao esquema."""
    tabela = montar_tabela_sintetica([1.0, 2.0, 3.0])
    conteudo = montar_csv_sintetico_em_bytes(tabela)
    configuracao_base = montar_configuracao_sintetica(semanas=3, semanas_corte_maturidade=1)
    configuracao = dataclasses.replace(
        configuracao_base, sha256_esperado_da_tabela=SHA256_QUALQUER
    )

    with pytest.raises(ValueError, match="Impressao digital"):
        montar_tabela_a_partir_dos_bytes(conteudo, configuracao)


# --- Carga: o esquema é conferido mesmo quando o hash bate (lacuna apontada na certificação do ciclo 1) ------------


def test_carga_com_hash_valido_e_esquema_ruim_falha() -> None:
    """Um CSV com hash correto, mas com uma semana fora do domingo, não pode passar pela carga."""
    tabela = montar_tabela_sintetica([0.0, 1.0, 2.0, 3.0])
    tabela.loc[2, COLUNA_DE_DATA] = tabela.loc[2, COLUNA_DE_DATA] + pd.Timedelta(days=1)
    conteudo_em_bytes = tabela.to_csv(index=False).encode("utf-8")
    configuracao = dataclasses.replace(
        montar_configuracao_sintetica(semanas=4, semanas_corte_maturidade=0),
        sha256_esperado_da_tabela=hashlib.sha256(conteudo_em_bytes).hexdigest(),
    )
    with pytest.raises(ValueError):
        montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, configuracao)
