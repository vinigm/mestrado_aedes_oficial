"""Testes das familias F1 a F4 (pre-declaracao, secao 4 e Emenda 1). Nenhum modelo e treinado.

Le as previsoes da E2, o composto da E3 (N = 13), a regua sazonal (da tabela cortada) e o piso de ruido,
roda os 52 testes pareados (12 + 12 + 12 + 16) e grava `resultados/ciencia/estatistica/familias.csv`
com: familia, h, A, B, n, mae_A, mae_B, delta, ganho_pct, ic_inf, ic_sup, dm_hln, p_bruto, p_holm,
limiar_piso, variancia_fallback, veredito. Os vereditos saem so da regra (p de Holm < 0,05 E |delta| > 2x o piso).

Exige: travas da E2 aprovadas, `E3_composto/resumo.csv` pronto e a regua com o mesmo `real` da E2.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.testes_familias
"""

import sys

import pandas as pd

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
)
from aedes.familias import (
    HORIZONTES_TESTADOS,
    NOME_DA_REGUA_SAZONAL,
    NOME_DO_COMPOSTO,
    DefinicaoDoTeste,
    executar_familias,
    montar_definicoes_das_familias,
    nome_do_candidato,
)
from aedes.metricas import (
    COLUNA_DO_BRACO,
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_PREVISTO,
    COLUNA_DO_REAL,
    NOME_DO_BRACO_REGUA_SAZONAL,
    montar_previsoes_das_reguas,
    recortar_janela_de_avaliacao,
)
from experimentos.comum_ciencia import (
    PASTA_DA_CIENCIA,
    RegistradorDeLog,
    carregar_tabela_cortada,
)
from experimentos.e3_composto import (
    CAMINHO_DAS_PREVISOES as CAMINHO_DAS_PREVISOES_DA_E3,
    CAMINHO_DO_RESUMO as CAMINHO_DO_RESUMO_DA_E3,
    COLUNA_DA_FOLHA,
    COLUNA_DA_JANELA_N,
    JANELA_PRIMARIA,
    exigir_travas_da_e2_aprovadas,
    ler_previsoes_da_e2,
)

PASTA_DE_SAIDA = PASTA_DA_CIENCIA / "estatistica"
CAMINHO_DA_TABELA_DE_FAMILIAS = PASTA_DE_SAIDA / "familias.csv"
CAMINHO_DO_PISO = PASTA_DA_CIENCIA / "piso_de_ruido" / "piso.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "testes_familias.log")

COLUNAS_DAS_PREVISOES_DO_CANDIDATO = [COLUNA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
BRACO_DE_REFERENCIA_DA_GRADE = "completo"
FOLHA_DA_GRADE = 5
QUANTIDADE_ESPERADA_DE_TESTES = 52
TOLERANCIA_DO_REAL_DA_REGUA = 1e-9


def ler_piso_de_ruido() -> pd.DataFrame:
    """Le `piso_de_ruido/piso.csv` com precisao total dos floats."""
    return pd.read_csv(CAMINHO_DO_PISO, float_precision="round_trip")


def ler_composto_primario_na_janela() -> pd.DataFrame:
    """Previsoes do composto N = 13 na janela de avaliacao (a E3 precisa ter terminado, com `resumo.csv`).

    Raises:
        FileNotFoundError: Se a E3 nao estiver pronta.
    """
    if not CAMINHO_DO_RESUMO_DA_E3.exists():
        raise FileNotFoundError(f"E3 nao concluida: {CAMINHO_DO_RESUMO_DA_E3} ausente.")
    todos = pd.read_csv(
        CAMINHO_DAS_PREVISOES_DA_E3,
        parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
        float_precision="round_trip",
    )
    do_n_primario = todos.loc[todos[COLUNA_DA_JANELA_N] == JANELA_PRIMARIA]
    return recortar_janela_de_avaliacao(do_n_primario, CONFIGURACAO_AVALIACAO)


def montar_previsoes_da_regua_sazonal(previsoes_da_e2_na_janela: pd.DataFrame) -> pd.DataFrame:
    """Regua sazonal (casos 52 semanas antes, tabela cortada) na grade `(h, data_alvo)` do `completo` folha 5."""
    tabela_cortada = carregar_tabela_cortada()
    casos_por_data = tabela_cortada.set_index(CONFIGURACAO_DADOS.coluna_de_data)[CONFIGURACAO_DADOS.coluna_de_casos]

    e_da_grade = (previsoes_da_e2_na_janela[COLUNA_DO_BRACO] == BRACO_DE_REFERENCIA_DA_GRADE) & (
        previsoes_da_e2_na_janela[COLUNA_DA_FOLHA] == FOLHA_DA_GRADE
    )
    grade = previsoes_da_e2_na_janela.loc[e_da_grade]
    reguas = montar_previsoes_das_reguas(grade, casos_por_data)
    return reguas.loc[reguas[COLUNA_DO_BRACO] == NOME_DO_BRACO_REGUA_SAZONAL]


def conferir_real_da_regua_contra_a_e2(regua: pd.DataFrame, previsoes_da_e2_na_janela: pd.DataFrame) -> None:
    """Confere que o `real` da regua e o da E2 nas semanas em comum (mesma serie).

    Raises:
        ValueError: Se o `real` divergir ou nao houver semana em comum.
    """
    reais_da_e2 = previsoes_da_e2_na_janela[[COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO, COLUNA_DO_REAL]].drop_duplicates()
    cruzamento = regua[[COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO, COLUNA_DO_REAL]].merge(
        reais_da_e2, on=[COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO], how="inner", suffixes=("_regua", "_e2")
    )
    if len(cruzamento) == 0:
        raise ValueError("A regua e a E2 nao tem nenhuma semana em comum.")
    diferenca = (cruzamento[f"{COLUNA_DO_REAL}_regua"] - cruzamento[f"{COLUNA_DO_REAL}_e2"]).abs()
    if bool((diferenca > TOLERANCIA_DO_REAL_DA_REGUA).any()):
        raise ValueError("O `real` da regua difere do `real` da E2.")


def montar_previsoes_por_candidato(
    definicoes: list[DefinicaoDoTeste],
    previsoes_da_e2_na_janela: pd.DataFrame,
    composto_na_janela: pd.DataFrame,
    regua: pd.DataFrame,
) -> dict[tuple[str, int], pd.DataFrame]:
    """`(nome, h) -> previsoes` de todo candidato citado nas definicoes (E2 por braco e folha, composto, regua)."""
    previsoes_por_candidato: dict[tuple[str, int], pd.DataFrame] = {}
    nomes_citados: set[str] = set()
    for definicao in definicoes:
        nomes_citados.add(definicao.nome_a)
        nomes_citados.add(definicao.nome_b)

    nomes_da_e2: dict[str, tuple[str, int]] = {}
    for braco in pd.unique(previsoes_da_e2_na_janela[COLUNA_DO_BRACO]):
        for folha in pd.unique(previsoes_da_e2_na_janela[COLUNA_DA_FOLHA]):
            nomes_da_e2[nome_do_candidato(str(braco), int(folha))] = (str(braco), int(folha))

    for horizonte in HORIZONTES_TESTADOS:
        do_horizonte_da_e2 = previsoes_da_e2_na_janela.loc[previsoes_da_e2_na_janela[COLUNA_DO_HORIZONTE] == horizonte]
        for nome in sorted(nomes_citados):
            if nome in nomes_da_e2:
                braco, folha = nomes_da_e2[nome]
                e_do_braco = do_horizonte_da_e2[COLUNA_DO_BRACO] == braco
                e_da_folha = do_horizonte_da_e2[COLUNA_DA_FOLHA] == folha
                selecao = do_horizonte_da_e2.loc[e_do_braco & e_da_folha]
            elif nome == NOME_DO_COMPOSTO:
                selecao = composto_na_janela.loc[composto_na_janela[COLUNA_DO_HORIZONTE] == horizonte]
            elif nome == NOME_DA_REGUA_SAZONAL:
                selecao = regua.loc[regua[COLUNA_DO_HORIZONTE] == horizonte]
            else:
                raise KeyError(f"Candidato sem fonte de previsoes: {nome}")
            previsoes_por_candidato[(nome, horizonte)] = selecao[COLUNAS_DAS_PREVISOES_DO_CANDIDATO].copy()
    return previsoes_por_candidato


def main() -> int:
    """Roda as quatro familias e grava `familias.csv`.

    Returns:
        0 se terminou; uma excecao interrompe a etapa (nenhum resultado parcial e gravado).
    """
    exigir_travas_da_e2_aprovadas()
    previsoes_da_e2 = ler_previsoes_da_e2()
    previsoes_da_e2_na_janela = recortar_janela_de_avaliacao(previsoes_da_e2, CONFIGURACAO_AVALIACAO)
    composto_na_janela = ler_composto_primario_na_janela()
    regua = montar_previsoes_da_regua_sazonal(previsoes_da_e2_na_janela)
    conferir_real_da_regua_contra_a_e2(regua, previsoes_da_e2_na_janela)
    piso_de_ruido = ler_piso_de_ruido()
    REGISTRADOR.registrar(
        f"inicio: E2 na janela={len(previsoes_da_e2_na_janela)} linhas; composto N={JANELA_PRIMARIA} "
        f"na janela={len(composto_na_janela)}; regua={len(regua)}; piso={len(piso_de_ruido)} linhas"
    )

    definicoes = montar_definicoes_das_familias()
    if len(definicoes) != QUANTIDADE_ESPERADA_DE_TESTES:
        raise RuntimeError(f"{len(definicoes)} testes montados; esperado {QUANTIDADE_ESPERADA_DE_TESTES}.")

    previsoes_por_candidato = montar_previsoes_por_candidato(
        definicoes, previsoes_da_e2_na_janela, composto_na_janela, regua
    )
    tabela = executar_familias(definicoes, previsoes_por_candidato, piso_de_ruido)
    tabela.to_csv(CAMINHO_DA_TABELA_DE_FAMILIAS, index=False)

    contagem_por_familia = tabela.groupby("familia").size().to_dict()
    contagem_de_vereditos = tabela["veredito"].value_counts().to_dict()
    colunas_do_n = sorted(tabela["n"].unique().tolist())
    REGISTRADOR.registrar(
        f"fim: {len(tabela)} testes em {CAMINHO_DA_TABELA_DE_FAMILIAS.name}; por familia={contagem_por_familia}; "
        f"vereditos={contagem_de_vereditos}; valores de n={colunas_do_n}; "
        f"variancia_fallback={int(tabela['variancia_fallback'].sum())}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
