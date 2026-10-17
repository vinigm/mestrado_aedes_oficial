"""E5c: alarme em h = 12 (emenda 4 da pre-declaracao, aprovada pelo Vinicius em 12/10/2026; DESCRITIVA).

Estende a E5 (`e5_alarme.py`) e a E5b (`e5b_alarme_reguas.py`), ambas certificadas e intocadas, ao horizonte
de 12 semanas, para a Tabela 3 ficar completa (h = 1, 4, 8 e 12). Mesma grade, mesma definicao de alarme
(`real > L` e `previsto > L`, estritos, por semana), mesmo `L` de `razao.json` (~447,065) e tambem 421.

Candidatos (5): `completo` folha 5, `completo` folha 20 (previsoes da E2), composto N = 13 (E3),
regua sazonal e persistencia (`montar_previsoes_das_reguas`). Nenhum modelo e treinado.

Grade: as 102 `data_alvo` do `completo` folha 5 em h = 12 na janela de avaliacao (07/01/2024 a 01/02/2026).
Ancora: n = 102 em todas as linhas e o mesmo numero de semanas de surto em todos os candidatos de um limiar.
Se divergir, a etapa PARA (codigo 1) e nao grava a tabela.

Grava em `resultados/ciencia/E5_alarme/`: `alarme_h12.csv` (10 linhas = 5 candidatos x 2 limiares; colunas de
`alarme.csv`) e `E5c_alarme_h12.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`; leva segundos):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e5c_alarme_h12
"""

import sys

import pandas as pd

from aedes.alarme import LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
)
from aedes.familias import NOME_DO_COMPOSTO
from aedes.metricas import (
    COLUNA_DO_BRACO,
    COLUNA_DO_HORIZONTE,
    montar_previsoes_das_reguas,
    recortar_janela_de_avaliacao,
)
from experimentos.comum_ciencia import RegistradorDeLog
from experimentos.e3_composto import COLUNA_DA_FOLHA, exigir_travas_da_e2_aprovadas, ler_previsoes_da_e2
from experimentos.e5_alarme import (
    BRACO_DA_GRADE,
    COLUNAS_DO_ALARME,
    FOLHA_DA_GRADE,
    NOME_DA_FOLHA_DO_COMPOSTO,
    PASTA_DE_SAIDA,
    SEMANAS_ESPERADAS_NA_JANELA,
    ler_composto_primario_na_janela,
    montar_linha_do_alarme,
    semanas_do_completo_no_horizonte,
)
from experimentos.e5b_alarme_reguas import (
    FOLHA_DAS_REGUAS,
    NOMES_DAS_REGUAS,
    ler_limiar_convertido,
)
from experimentos.referencia import carregar_tabela_cortada

CAMINHO_DO_ALARME_H12 = PASTA_DE_SAIDA / "alarme_h12.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E5c_alarme_h12.log")

HORIZONTE_DA_EMENDA = 12
FOLHAS_DO_COMPLETO = (5, 20)
CANDIDATOS_ESPERADOS = 5
LINHAS_ESPERADAS_NA_TABELA = CANDIDATOS_ESPERADOS * 2


def montar_tabela_dos_modelos(
    previsoes_na_janela: pd.DataFrame,
    composto_na_janela: pd.DataFrame,
    semanas_do_denominador: pd.DatetimeIndex,
    limiar: float,
) -> list[dict[str, object]]:
    """Linhas de alarme do `completo` (folhas 5 e 20) e do composto N=13 em h = 12, para um limiar."""
    linhas: list[dict[str, object]] = []
    for folha in FOLHAS_DO_COMPLETO:
        e_do_braco = previsoes_na_janela[COLUNA_DO_BRACO] == BRACO_DA_GRADE
        e_da_folha = previsoes_na_janela[COLUNA_DA_FOLHA] == folha
        e_do_horizonte = previsoes_na_janela[COLUNA_DO_HORIZONTE] == HORIZONTE_DA_EMENDA
        do_candidato = previsoes_na_janela.loc[e_do_braco & e_da_folha & e_do_horizonte]
        linhas.append(
            montar_linha_do_alarme(
                BRACO_DA_GRADE, folha, HORIZONTE_DA_EMENDA, limiar, do_candidato, semanas_do_denominador
            )
        )
    e_do_horizonte_do_composto = composto_na_janela[COLUNA_DO_HORIZONTE] == HORIZONTE_DA_EMENDA
    do_composto = composto_na_janela.loc[e_do_horizonte_do_composto]
    linhas.append(
        montar_linha_do_alarme(
            NOME_DO_COMPOSTO,
            NOME_DA_FOLHA_DO_COMPOSTO,
            HORIZONTE_DA_EMENDA,
            limiar,
            do_composto,
            semanas_do_denominador,
        )
    )
    return linhas


def montar_tabela_das_reguas(
    previsoes_das_reguas: pd.DataFrame,
    semanas_do_denominador: pd.DatetimeIndex,
    limiar: float,
) -> list[dict[str, object]]:
    """Linhas de alarme da regua sazonal e da persistencia em h = 12, para um limiar."""
    linhas: list[dict[str, object]] = []
    for nome_da_regua in NOMES_DAS_REGUAS:
        e_da_regua = previsoes_das_reguas[COLUNA_DO_BRACO] == nome_da_regua
        e_do_horizonte = previsoes_das_reguas[COLUNA_DO_HORIZONTE] == HORIZONTE_DA_EMENDA
        do_candidato = previsoes_das_reguas.loc[e_da_regua & e_do_horizonte]
        linhas.append(
            montar_linha_do_alarme(
                nome_da_regua, FOLHA_DAS_REGUAS, HORIZONTE_DA_EMENDA, limiar, do_candidato, semanas_do_denominador
            )
        )
    return linhas


def conferir_ancoras(tabela_do_alarme: pd.DataFrame) -> list[str]:
    """Confere n = 102 e a igualdade das semanas de surto entre candidatos do mesmo limiar.

    Returns:
        Divergencias (uma frase cada); vazia se tudo bateu.
    """
    divergencias: list[str] = []
    if len(tabela_do_alarme) != LINHAS_ESPERADAS_NA_TABELA:
        divergencias.append(f"linhas={len(tabela_do_alarme)} (esperado {LINHAS_ESPERADAS_NA_TABELA})")
    for posicao in range(len(tabela_do_alarme)):
        linha = tabela_do_alarme.iloc[posicao]
        if linha["n"] != SEMANAS_ESPERADAS_NA_JANELA:
            divergencias.append(f"{linha[COLUNA_DO_BRACO]} limiar={linha['limiar']:.3f}: n={linha['n']}")
    for limiar, do_limiar in tabela_do_alarme.groupby("limiar"):
        surtos_distintos = sorted(do_limiar["semanas_de_surto"].unique().tolist())
        if len(surtos_distintos) != 1:
            divergencias.append(f"limiar={limiar:.3f}: semanas_de_surto diferem entre candidatos: {surtos_distintos}")
    return divergencias


def main() -> int:
    """Mede o alarme em h = 12 dos 5 candidatos, confere as ancoras e grava `alarme_h12.csv`.

    Returns:
        0 se tudo passou; 1 se alguma ancora divergiu (nada e gravado alem do log).
    """
    exigir_travas_da_e2_aprovadas()
    limiar_convertido = ler_limiar_convertido()
    limiares = (limiar_convertido, float(LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS))
    REGISTRADOR.registrar(f"inicio E5c (h={HORIZONTE_DA_EMENDA}): L convertido={limiar_convertido:.6f}; sem conversao={limiares[1]:.1f}")

    previsoes_na_janela = recortar_janela_de_avaliacao(ler_previsoes_da_e2(), CONFIGURACAO_AVALIACAO)
    composto_na_janela = ler_composto_primario_na_janela()
    semanas_do_denominador = semanas_do_completo_no_horizonte(previsoes_na_janela, HORIZONTE_DA_EMENDA)

    tabela_cortada = carregar_tabela_cortada()
    casos_por_data = tabela_cortada.set_index(CONFIGURACAO_DADOS.coluna_de_data)[CONFIGURACAO_DADOS.coluna_de_casos]
    grade = pd.DataFrame(
        {
            COLUNA_DO_HORIZONTE: HORIZONTE_DA_EMENDA,
            COLUNA_DATA_ALVO: semanas_do_denominador,
        }
    )
    previsoes_das_reguas = montar_previsoes_das_reguas(grade, casos_por_data)
    REGISTRADOR.registrar(
        f"grade: {len(grade)} semanas-alvo; previsoes das reguas: {len(previsoes_das_reguas)} linhas"
    )

    linhas: list[dict[str, object]] = []
    for limiar in limiares:
        linhas.extend(montar_tabela_dos_modelos(previsoes_na_janela, composto_na_janela, semanas_do_denominador, limiar))
        linhas.extend(montar_tabela_das_reguas(previsoes_das_reguas, semanas_do_denominador, limiar))
    tabela_do_alarme = pd.DataFrame(linhas, columns=list(COLUNAS_DO_ALARME))

    for posicao in range(len(tabela_do_alarme)):
        linha = tabela_do_alarme.iloc[posicao]
        REGISTRADOR.registrar(
            f"limiar={linha['limiar']:.3f} {linha[COLUNA_DO_BRACO]} folha={linha[COLUNA_DA_FOLHA]} h={linha[COLUNA_DO_HORIZONTE]}: "
            f"n={linha['n']} surtos={linha['semanas_de_surto']} VP={linha['VP']} FN={linha['FN']} "
            f"FP={linha['FP']} VN={linha['VN']} sens={linha['sensibilidade']:.4f} prec={linha['precisao']:.4f} "
            f"falsos_por_ano={linha['falsos_por_ano']:.4f}"
        )

    divergencias = conferir_ancoras(tabela_do_alarme)
    if divergencias:
        for divergencia in divergencias:
            REGISTRADOR.registrar(f"ANCORA DIVERGE: {divergencia}")
        REGISTRADOR.registrar("alarme_h12.csv NAO gravado; investigar antes de seguir.")
        return 1

    tabela_do_alarme.to_csv(CAMINHO_DO_ALARME_H12, index=False)
    REGISTRADOR.registrar(f"fim E5c: {len(tabela_do_alarme)} linhas em {CAMINHO_DO_ALARME_H12.name}; ancoras conferidas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
