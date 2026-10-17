"""E5b: alarme das reguas (sazonal e persistencia), no mesmo limiar e nas mesmas semanas da E5 (DESCRITIVA).

A E5 (`e5_alarme.py`, certificada) mediu o alarme dos modelos; esta etapa mede o das duas reguas simples,
para a comparacao "modelo x regua" ter a mesma definicao de alarme nos dois lados. Nenhum modelo e treinado.

Passos:
    1. Le o limiar convertido `L` de `resultados/ciencia/E5_alarme/razao.json` (nao recalcula a razao; exige
       `ancora_ok` verdadeiro e `limiar_base` = 421) e exige as travas da E2 aprovadas, como a E5.
    2. Monta a MESMA grade de semanas da E5: as `data_alvo` do braco `completo` folha 5 na janela de
       avaliacao (07/01/2024 a 01/02/2026), em h = 1, 4 e 8 (102 semanas por horizonte).
    3. Aplica `montar_previsoes_das_reguas` (aedes/metricas.py) a essa grade, sobre a serie de casos
       da tabela certificada JA cortada pela maturidade (`aplicar_corte_de_maturidade`):
           - regua sazonal: casos da semana `data_alvo - 52 semanas`;
           - persistencia: casos da semana `data_alvo - h semanas` (a semana de origem).
    4. Mede o alarme com `calcular_metricas_do_alarme` (aedes/alarme.py): surto = `real > L`, alarme =
       `previsto > L`, ambos ESTRITOS, por semana; falsos por ano = FP / 1,96. Duas leituras do limiar:
       `L` convertido (~447,065) e 421 sem conversao.
    5. Confere as ANCORAS da E5 antes de gravar: n = 102 e semanas de surto 24, 27 e 28 em h = 1, 4 e 8
       (as semanas de surto dependem so do `real`, entao valem para as duas leituras do limiar).
       Se divergirem, a etapa PARA (codigo 1) e nao grava a tabela.

Grava em `resultados/ciencia/E5_alarme/`: `alarme_reguas.csv` (12 linhas = 2 reguas x 3 horizontes x 2 limiares;
mesmas colunas de `alarme.csv`, com `braco` = regua_sazonal ou persistencia e `folha` = "-") e `E5b_alarme_reguas.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`; leva segundos):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e5b_alarme_reguas
"""

import json
import sys

import pandas as pd

from aedes.alarme import LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
)
from aedes.metricas import (
    COLUNA_DO_BRACO,
    COLUNA_DO_HORIZONTE,
    NOME_DO_BRACO_PERSISTENCIA,
    NOME_DO_BRACO_REGUA_SAZONAL,
    montar_previsoes_das_reguas,
    recortar_janela_de_avaliacao,
)
from experimentos.comum_ciencia import RegistradorDeLog
from experimentos.e3_composto import COLUNA_DA_FOLHA, exigir_travas_da_e2_aprovadas, ler_previsoes_da_e2
from experimentos.e5_alarme import (
    CAMINHO_DA_RAZAO,
    COLUNAS_DO_ALARME,
    HORIZONTES_DO_ALARME,
    PASTA_DE_SAIDA,
    SEMANAS_ESPERADAS_NA_JANELA,
    montar_linha_do_alarme,
    semanas_do_completo_no_horizonte,
)
from experimentos.referencia import carregar_tabela_cortada

CAMINHO_DO_ALARME_DAS_REGUAS = PASTA_DE_SAIDA / "alarme_reguas.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E5b_alarme_reguas.log")

NOMES_DAS_REGUAS = (NOME_DO_BRACO_REGUA_SAZONAL, NOME_DO_BRACO_PERSISTENCIA)
FOLHA_DAS_REGUAS = "-"
SEMANAS_DE_SURTO_ESPERADAS_POR_HORIZONTE = {1: 24, 4: 27, 8: 28}
LINHAS_ESPERADAS_NA_TABELA = 2 * len(HORIZONTES_DO_ALARME) * 2


def ler_limiar_convertido() -> float:
    """Le `L` de `razao.json` da E5, sem recalcular a razao notificacao/residencia.

    Returns:
        O limiar na escala da notificacao (~447,065).

    Raises:
        FileNotFoundError: Se `razao.json` nao existir.
        RuntimeError: Se a ancora da E5 nao estava ok ou o limiar-base nao for 421.
    """
    if not CAMINHO_DA_RAZAO.exists():
        raise FileNotFoundError(f"razao.json da E5 ausente: {CAMINHO_DA_RAZAO}")
    with open(CAMINHO_DA_RAZAO, encoding="utf-8") as arquivo:
        razao = json.load(arquivo)
    if razao.get("ancora_ok") is not True:
        raise RuntimeError("razao.json da E5 sem ancora_ok verdadeiro; a E5b nao roda.")
    if razao.get("limiar_base") != LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS:
        raise RuntimeError(
            f"limiar_base de razao.json ({razao.get('limiar_base')}) difere de {LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS}."
        )
    return float(razao["L"])


def montar_a_grade_das_semanas_alvo(previsoes_na_janela: pd.DataFrame) -> pd.DataFrame:
    """Grade (h, data_alvo) da E5: as semanas do `completo` folha 5 na janela, em cada horizonte do alarme.

    Args:
        previsoes_na_janela: Previsoes da E2 ja recortadas na janela de avaliacao.

    Returns:
        DataFrame com `h` e `data_alvo`, uma linha por semana-alvo de cada horizonte (102 por horizonte).
    """
    tabelas_da_grade: list[pd.DataFrame] = []
    for horizonte in HORIZONTES_DO_ALARME:
        semanas_do_horizonte = semanas_do_completo_no_horizonte(previsoes_na_janela, horizonte)
        grade_do_horizonte = pd.DataFrame(
            {
                COLUNA_DO_HORIZONTE: horizonte,
                COLUNA_DATA_ALVO: semanas_do_horizonte,
            }
        )
        tabelas_da_grade.append(grade_do_horizonte)
    return pd.concat(tabelas_da_grade, ignore_index=True)


def montar_tabela_do_alarme_das_reguas(
    previsoes_das_reguas: pd.DataFrame,
    grade: pd.DataFrame,
    limiares: tuple[float, ...],
) -> pd.DataFrame:
    """Alarme de cada regua em cada horizonte e limiar, nas semanas da grade.

    Args:
        previsoes_das_reguas: Saida de `montar_previsoes_das_reguas` (h, data_alvo, real, previsto, braco).
        grade: Semanas-alvo por horizonte (`montar_a_grade_das_semanas_alvo`), o denominador comum.
        limiares: Limiares a medir, na ordem em que entram na tabela (convertido, depois 421).

    Returns:
        DataFrame com `COLUNAS_DO_ALARME`: limiar, depois horizonte, depois regua.
    """
    linhas: list[dict[str, object]] = []
    for limiar in limiares:
        for horizonte in HORIZONTES_DO_ALARME:
            e_do_horizonte_na_grade = grade[COLUNA_DO_HORIZONTE] == horizonte
            semanas_do_denominador = pd.DatetimeIndex(grade.loc[e_do_horizonte_na_grade, COLUNA_DATA_ALVO])
            for nome_da_regua in NOMES_DAS_REGUAS:
                e_da_regua = previsoes_das_reguas[COLUNA_DO_BRACO] == nome_da_regua
                e_do_horizonte = previsoes_das_reguas[COLUNA_DO_HORIZONTE] == horizonte
                do_candidato = previsoes_das_reguas.loc[e_da_regua & e_do_horizonte]
                linha = montar_linha_do_alarme(
                    nome_da_regua,
                    FOLHA_DAS_REGUAS,
                    horizonte,
                    limiar,
                    do_candidato,
                    semanas_do_denominador,
                )
                linhas.append(linha)
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_ALARME))


def conferir_ancoras(tabela_do_alarme: pd.DataFrame) -> list[str]:
    """Compara a tabela com as ancoras da E5 (n = 102; semanas de surto 24, 27 e 28 em h = 1, 4 e 8).

    Args:
        tabela_do_alarme: Saida de `montar_tabela_do_alarme_das_reguas`.

    Returns:
        Lista de divergencias, uma frase por divergencia; vazia se tudo bateu.
    """
    divergencias: list[str] = []
    if len(tabela_do_alarme) != LINHAS_ESPERADAS_NA_TABELA:
        divergencias.append(f"linhas={len(tabela_do_alarme)} (esperado {LINHAS_ESPERADAS_NA_TABELA})")
    for posicao in range(len(tabela_do_alarme)):
        linha = tabela_do_alarme.iloc[posicao]
        rotulo = f"{linha[COLUNA_DO_BRACO]} h={linha[COLUNA_DO_HORIZONTE]} limiar={linha['limiar']:.3f}"
        if linha["n"] != SEMANAS_ESPERADAS_NA_JANELA:
            divergencias.append(f"{rotulo}: n={linha['n']} (esperado {SEMANAS_ESPERADAS_NA_JANELA})")
        surtos_esperados = SEMANAS_DE_SURTO_ESPERADAS_POR_HORIZONTE[int(linha[COLUNA_DO_HORIZONTE])]
        if linha["semanas_de_surto"] != surtos_esperados:
            divergencias.append(f"{rotulo}: semanas_de_surto={linha['semanas_de_surto']} (esperado {surtos_esperados})")
    return divergencias


def registrar_resumo_da_tabela(tabela_do_alarme: pd.DataFrame) -> None:
    """Escreve no log uma linha por (limiar, regua, horizonte) com as contagens e as metricas do alarme."""
    for posicao in range(len(tabela_do_alarme)):
        linha = tabela_do_alarme.iloc[posicao]
        REGISTRADOR.registrar(
            f"limiar={linha['limiar']:.3f} {linha[COLUNA_DO_BRACO]} h={linha[COLUNA_DO_HORIZONTE]}: "
            f"n={linha['n']} surtos={linha['semanas_de_surto']} VP={linha['VP']} FN={linha['FN']} "
            f"FP={linha['FP']} sens={linha['sensibilidade']:.4f} prec={linha['precisao']:.4f} "
            f"falsos_por_ano={linha['falsos_por_ano']:.4f}"
        )


def main() -> int:
    """Mede o alarme das duas reguas, confere as ancoras da E5 e, se bateram, grava `alarme_reguas.csv`.

    Returns:
        0 se tudo passou; 1 se alguma ancora divergiu (nada e gravado alem do log).
    """
    exigir_travas_da_e2_aprovadas()
    limiar_convertido = ler_limiar_convertido()
    limiares = (limiar_convertido, float(LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS))
    REGISTRADOR.registrar(f"inicio E5b: L convertido={limiar_convertido:.6f}; sem conversao={limiares[1]:.1f}")

    tabela_cortada = carregar_tabela_cortada()
    casos_por_data = tabela_cortada.set_index(CONFIGURACAO_DADOS.coluna_de_data)[CONFIGURACAO_DADOS.coluna_de_casos]

    previsoes_na_janela = recortar_janela_de_avaliacao(ler_previsoes_da_e2(), CONFIGURACAO_AVALIACAO)
    grade = montar_a_grade_das_semanas_alvo(previsoes_na_janela)
    previsoes_das_reguas = montar_previsoes_das_reguas(grade, casos_por_data)
    REGISTRADOR.registrar(
        f"grade: {len(grade)} linhas (h x semana-alvo); previsoes das reguas: {len(previsoes_das_reguas)} linhas "
        f"(a regua sem previsao sai da conta)"
    )

    tabela_do_alarme = montar_tabela_do_alarme_das_reguas(previsoes_das_reguas, grade, limiares)
    registrar_resumo_da_tabela(tabela_do_alarme)

    divergencias = conferir_ancoras(tabela_do_alarme)
    if divergencias:
        for divergencia in divergencias:
            REGISTRADOR.registrar(f"ANCORA DIVERGE: {divergencia}")
        REGISTRADOR.registrar("alarme_reguas.csv NAO gravado; investigar antes de seguir.")
        return 1

    tabela_do_alarme.to_csv(CAMINHO_DO_ALARME_DAS_REGUAS, index=False)
    REGISTRADOR.registrar(
        f"fim E5b: {len(tabela_do_alarme)} linhas em {CAMINHO_DO_ALARME_DAS_REGUAS.name}; "
        f"ancoras da E5 conferidas (n={SEMANAS_ESPERADAS_NA_JANELA}; semanas de surto "
        f"{SEMANAS_DE_SURTO_ESPERADAS_POR_HORIZONTE})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
