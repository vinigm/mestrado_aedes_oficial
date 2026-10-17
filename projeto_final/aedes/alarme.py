"""E5: leitura de alarme no limiar convertido para a escala da notificacao (pre-declaracao, secao 7; descritiva).

Funcoes puras (nenhuma le ou grava arquivo; a leitura dos zips DENGBR fica em `experimentos/e5_alarme.py`).

Definicao de alarme: a do codigo antigo `analises/2026-09-26_modelo_composto/calcular_alarme.py`:
    - semana de surto (alerta REAL):   `real > limiar` (ESTRITO);
    - alarme (alerta PREVISTO):        `previsto > limiar` (ESTRITO);
    - conta SEMANAS (nao eventos);
    - sensibilidade = VP / (VP + FN), NaN se nao ha alerta real;
    - precisao = VP / (VP + FP), NaN se nao ha alarme;
    - alarmes falsos por ano = FP / anos da avaliacao (aqui 1,96, constante da especificacao).
"""

import dataclasses

import numpy as np
import pandas as pd

LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS = 421
ANOS_DA_AVALIACAO = 1.96
CODIGO_DE_PORTO_ALEGRE = "431490"
CLASSIFICACOES_CONFIRMADAS = ("10", "11", "12")
COLUNA_DE_NOTIFICACAO = "ID_MUNICIP"
COLUNA_DE_RESIDENCIA = "ID_MN_RESI"
COLUNA_DA_CLASSIFICACAO = "CLASSI_FIN"
COLUNA_DA_DATA_DE_SINTOMAS = "DT_SIN_PRI"
FORMATO_DA_DATA_DE_SINTOMAS = "%Y-%m-%d"


@dataclasses.dataclass(frozen=True)
class ContagemDeConfirmados:
    """Confirmados de Porto Alegre por municipio de notificacao e por municipio de residencia.

    Attributes:
        por_notificacao: Fichas confirmadas com `ID_MUNICIP` = Porto Alegre (numerador de `r`).
        por_residencia: Fichas confirmadas com `ID_MN_RESI` = Porto Alegre (denominador de `r`).
    """

    por_notificacao: int
    por_residencia: int


def contar_confirmados_de_porto_alegre(
    fichas: pd.DataFrame,
    ano_inicial_dos_sintomas: int,
    ano_final_dos_sintomas: int,
) -> ContagemDeConfirmados:
    """Conta as fichas confirmadas de Porto Alegre com `DT_SIN_PRI` entre dois anos (inclusive).

    Confirmada = `CLASSI_FIN` em 10, 11 ou 12. Um municipio so vale se o codigo for exatamente
    `431490`. Ficha sem `DT_SIN_PRI` valida (texto `AAAA-MM-DD`) nao entra em nenhuma contagem.
    Tudo e lido como texto (sem coercao de codigos).

    Args:
        fichas: Tabela com `ID_MUNICIP`, `ID_MN_RESI`, `CLASSI_FIN` e `DT_SIN_PRI` (texto).
        ano_inicial_dos_sintomas: Primeiro ano de `DT_SIN_PRI` aceito (2018).
        ano_final_dos_sintomas: Ultimo ano aceito (2023).

    Returns:
        A `ContagemDeConfirmados`.

    Raises:
        KeyError: Se faltar coluna.
    """
    colunas = [
        COLUNA_DE_NOTIFICACAO,
        COLUNA_DE_RESIDENCIA,
        COLUNA_DA_CLASSIFICACAO,
        COLUNA_DA_DATA_DE_SINTOMAS,
    ]
    ausentes = sorted(set(colunas) - set(fichas.columns))
    if ausentes:
        raise KeyError(f"Colunas ausentes nas fichas: {ausentes}")

    classificacao = fichas[COLUNA_DA_CLASSIFICACAO].astype(str).str.strip()
    esta_confirmada = classificacao.isin(CLASSIFICACOES_CONFIRMADAS)

    texto_da_data = fichas[COLUNA_DA_DATA_DE_SINTOMAS].astype(str).str.strip()
    data_dos_sintomas = pd.to_datetime(texto_da_data, format=FORMATO_DA_DATA_DE_SINTOMAS, errors="coerce")
    ano_dos_sintomas = data_dos_sintomas.dt.year
    no_periodo = (ano_dos_sintomas >= ano_inicial_dos_sintomas) & (ano_dos_sintomas <= ano_final_dos_sintomas)

    notificada_em_poa = fichas[COLUNA_DE_NOTIFICACAO].astype(str).str.strip() == CODIGO_DE_PORTO_ALEGRE
    residente_em_poa = fichas[COLUNA_DE_RESIDENCIA].astype(str).str.strip() == CODIGO_DE_PORTO_ALEGRE

    por_notificacao = int((esta_confirmada & no_periodo & notificada_em_poa).sum())
    por_residencia = int((esta_confirmada & no_periodo & residente_em_poa).sum())
    return ContagemDeConfirmados(por_notificacao=por_notificacao, por_residencia=por_residencia)


def calcular_razao_notificacao_residencia(por_notificacao: int, por_residencia: int) -> float:
    """`r` = confirmados por notificacao / confirmados por residencia.

    Raises:
        ValueError: Se o denominador for zero ou algum valor for negativo.
    """
    if por_notificacao < 0 or por_residencia <= 0:
        raise ValueError("por_notificacao deve ser >= 0 e por_residencia > 0.")
    return por_notificacao / por_residencia


def converter_limiar(limiar_na_escala_dos_casos: float, razao_notificacao_residencia: float) -> float:
    """`L = limiar x r`: leva o limiar da escala de residencia para a da notificacao."""
    if limiar_na_escala_dos_casos <= 0.0 or razao_notificacao_residencia <= 0.0:
        raise ValueError("limiar e razao devem ser positivos.")
    return limiar_na_escala_dos_casos * razao_notificacao_residencia


@dataclasses.dataclass(frozen=True)
class MetricasDoAlarme:
    """Contagens e metricas do alarme semanal.

    Attributes:
        n: Semanas avaliadas.
        semanas_de_surto: Semanas com `real > limiar`.
        verdadeiros_positivos: Surto e alarme.
        falsos_negativos: Surto sem alarme.
        falsos_positivos: Alarme sem surto.
        verdadeiros_negativos: Nem surto nem alarme.
        sensibilidade: VP / (VP + FN), NaN sem surto.
        precisao: VP / (VP + FP), NaN sem alarme.
        falsos_por_ano: FP / `ANOS_DA_AVALIACAO`.
    """

    n: int
    semanas_de_surto: int
    verdadeiros_positivos: int
    falsos_negativos: int
    falsos_positivos: int
    verdadeiros_negativos: int
    sensibilidade: float
    precisao: float
    falsos_por_ano: float


def calcular_metricas_do_alarme(
    valores_reais: np.ndarray,
    valores_previstos: np.ndarray,
    limiar: float,
    anos_da_avaliacao: float = ANOS_DA_AVALIACAO,
) -> MetricasDoAlarme:
    """Classifica cada semana (surto e alarme por `> limiar`) e calcula as metricas.

    Args:
        valores_reais: Casos observados por semana.
        valores_previstos: Previsoes pareadas por posicao.
        limiar: Casos por semana acima dos quais a semana conta como surto/alarme (estrito).
        anos_da_avaliacao: Denominador de `falsos_por_ano` (1,96).

    Returns:
        As `MetricasDoAlarme`.

    Raises:
        ValueError: Se os tamanhos diferirem, houver ausente ou infinito, ou `anos_da_avaliacao` <= 0.
    """
    reais = np.asarray(valores_reais, dtype=float)
    previstos = np.asarray(valores_previstos, dtype=float)
    if reais.ndim != 1 or reais.shape != previstos.shape:
        raise ValueError("valores_reais e valores_previstos devem ser 1-D e do mesmo tamanho.")
    if not (np.isfinite(reais).all() and np.isfinite(previstos).all()):
        raise ValueError("valores_reais e valores_previstos nao podem ter ausente ou infinito.")
    if anos_da_avaliacao <= 0.0:
        raise ValueError("anos_da_avaliacao deve ser > 0.")

    houve_surto = reais > limiar
    disparou_alarme = previstos > limiar

    verdadeiros_positivos = int((houve_surto & disparou_alarme).sum())
    falsos_negativos = int((houve_surto & ~disparou_alarme).sum())
    falsos_positivos = int((~houve_surto & disparou_alarme).sum())
    verdadeiros_negativos = int((~houve_surto & ~disparou_alarme).sum())

    if verdadeiros_positivos + falsos_negativos > 0:
        sensibilidade = verdadeiros_positivos / (verdadeiros_positivos + falsos_negativos)
    else:
        sensibilidade = float("nan")
    if verdadeiros_positivos + falsos_positivos > 0:
        precisao = verdadeiros_positivos / (verdadeiros_positivos + falsos_positivos)
    else:
        precisao = float("nan")

    return MetricasDoAlarme(
        n=len(reais),
        semanas_de_surto=int(houve_surto.sum()),
        verdadeiros_positivos=verdadeiros_positivos,
        falsos_negativos=falsos_negativos,
        falsos_positivos=falsos_positivos,
        verdadeiros_negativos=verdadeiros_negativos,
        sensibilidade=sensibilidade,
        precisao=precisao,
        falsos_por_ano=falsos_positivos / anos_da_avaliacao,
    )
