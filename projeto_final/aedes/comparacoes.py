"""Comparacoes descritivas das etapas E1, E2, E4 e do piso de ruido (sem nenhum teste estatistico).

Funcoes puras: recebem DataFrames de previsoes e devolvem numeros, tabelas ou
decisoes de regra. Nenhuma le ou grava arquivo. Aqui NAO ha Diebold-Mariano,
Holm nem bootstrap: so MAE, R2, cobertura e diferencas, que e o que a rodada de
execucao pede; os testes entram em outra etapa.

O que ha:
    - `comparar_previsoes_com_gabarito`: a TRAVA (previsoes novas = gabarito,
      diferenca < tolerancia, mesmo conjunto de linhas);
    - `calcular_cobertura`: fracao de semanas em que o real passou do previsto (E1);
    - `decidir_quantil`: a regra de 2% da pre-declaracao 3 (E1);
    - `comparar_cortes`: MAE e R2 do corte pela resposta e pela pergunta (E4);
    - `calcular_mae_na_janela`: MAE e n na janela de avaliacao;
    - `calcular_deltas_e_piso_de_ruido`: |MAE perturbada - MAE referencia| e o
      maior delta por folha e horizonte (pre-declaracao 8b).
"""

import dataclasses

import numpy as np
import pandas as pd

from aedes.configuracao import COLUNA_DATA_ALVO, ConfiguracaoAvaliacao
from aedes.metricas import (
    COLUNA_DO_BRACO,
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_PREVISTO,
    COLUNA_DO_REAL,
    erro_absoluto_medio,
    r_quadrado,
    recortar_janela_de_avaliacao,
)


@dataclasses.dataclass(frozen=True)
class ResultadoDaTrava:
    """Resultado da comparacao das previsoes novas com o gabarito.

    Attributes:
        linhas_novas: Quantas linhas as previsoes novas tem.
        linhas_do_gabarito: Quantas linhas o gabarito tem.
        linhas_em_comum: Quantas chaves aparecem nos dois lados.
        linhas_so_nas_novas: Chaves que so as previsoes novas tem.
        linhas_so_no_gabarito: Chaves que so o gabarito tem.
        diferenca_maxima_do_previsto: Maior |previsto novo - previsto do gabarito|
            nas linhas em comum (NaN se nao houver nenhuma).
        diferenca_maxima_do_real: Idem para a coluna `real`.
        tolerancia: Limite estrito usado (a diferenca tem de ser MENOR).
        passou: Verdadeiro se os conjuntos sao iguais, ha linhas e as duas
            diferencas maximas sao menores que a tolerancia.
    """

    linhas_novas: int
    linhas_do_gabarito: int
    linhas_em_comum: int
    linhas_so_nas_novas: int
    linhas_so_no_gabarito: int
    diferenca_maxima_do_previsto: float
    diferenca_maxima_do_real: float
    tolerancia: float
    passou: bool


def comparar_previsoes_com_gabarito(
    previsoes_novas: pd.DataFrame,
    previsoes_do_gabarito: pd.DataFrame,
    colunas_da_chave: list[str],
    tolerancia: float,
) -> ResultadoDaTrava:
    """Compara previsoes novas e gabarito casando pelas colunas da chave (por exemplo `h`, `data_alvo`).

    Casa por CHAVE, nunca por posicao: o gabarito do braco antigo nao tem
    `data_origem`, e a ordem das linhas pode diferir. Passa so se o conjunto de
    chaves e o mesmo nos dois lados e as diferencas de `previsto` e de `real`
    sao menores que a tolerancia.

    Args:
        previsoes_novas: Precisa de `colunas_da_chave`, `real` e `previsto`.
        previsoes_do_gabarito: Idem.
        colunas_da_chave: Colunas que identificam a linha de forma unica.
        tolerancia: Limite estrito da diferenca (por exemplo 1e-9).

    Returns:
        O `ResultadoDaTrava`.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se a tolerancia nao for positiva ou se a chave se repetir
            em algum dos lados.
    """
    if tolerancia <= 0.0:
        raise ValueError(f"tolerancia deve ser > 0, recebido {tolerancia!r}.")

    colunas_necessarias = [*colunas_da_chave, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
    for nome_do_lado, tabela in (("novas", previsoes_novas), ("gabarito", previsoes_do_gabarito)):
        colunas_ausentes = sorted(set(colunas_necessarias) - set(tabela.columns))
        if colunas_ausentes:
            raise KeyError(f"Colunas ausentes nas previsoes ({nome_do_lado}): {colunas_ausentes}")
        if tabela.duplicated(subset=colunas_da_chave).any():
            raise ValueError(f"Chave repetida nas previsoes ({nome_do_lado}): {colunas_da_chave}.")

    novas = previsoes_novas[colunas_necessarias].rename(
        columns={COLUNA_DO_REAL: "real_novo", COLUNA_DO_PREVISTO: "previsto_novo"}
    )
    gabarito = previsoes_do_gabarito[colunas_necessarias].rename(
        columns={COLUNA_DO_REAL: "real_gabarito", COLUNA_DO_PREVISTO: "previsto_gabarito"}
    )
    cruzamento = novas.merge(gabarito, on=colunas_da_chave, how="outer", indicator=True)

    em_comum = cruzamento.loc[cruzamento["_merge"] == "both"]
    so_nas_novas = int((cruzamento["_merge"] == "left_only").sum())
    so_no_gabarito = int((cruzamento["_merge"] == "right_only").sum())

    if len(em_comum) == 0:
        diferenca_do_previsto = float("nan")
        diferenca_do_real = float("nan")
    else:
        diferencas_do_previsto = (em_comum["previsto_novo"] - em_comum["previsto_gabarito"]).abs()
        diferencas_do_real = (em_comum["real_novo"] - em_comum["real_gabarito"]).abs()
        diferenca_do_previsto = float(diferencas_do_previsto.max())
        diferenca_do_real = float(diferencas_do_real.max())

    previsto_dentro_da_tolerancia = diferenca_do_previsto < tolerancia
    real_dentro_da_tolerancia = diferenca_do_real < tolerancia
    conjuntos_iguais = so_nas_novas == 0 and so_no_gabarito == 0
    passou = bool(conjuntos_iguais and previsto_dentro_da_tolerancia and real_dentro_da_tolerancia)

    return ResultadoDaTrava(
        linhas_novas=len(previsoes_novas),
        linhas_do_gabarito=len(previsoes_do_gabarito),
        linhas_em_comum=len(em_comum),
        linhas_so_nas_novas=so_nas_novas,
        linhas_so_no_gabarito=so_no_gabarito,
        diferenca_maxima_do_previsto=diferenca_do_previsto,
        diferenca_maxima_do_real=diferenca_do_real,
        tolerancia=tolerancia,
        passou=passou,
    )


def calcular_cobertura(
    valores_reais: pd.Series | np.ndarray,
    valores_previstos: pd.Series | np.ndarray,
) -> float:
    """Fracao das semanas em que o real ficou ACIMA do previsto (`real > previsto`).

    Num quantil `q` bem calibrado, o real passa do previsto em cerca de `1 - q`
    das semanas; e uma leitura descritiva (E1), nao um criterio de decisao.

    Args:
        valores_reais: Casos observados.
        valores_previstos: Previsoes, pareadas por posicao.

    Returns:
        A fracao em [0, 1]; NaN se nao houver nenhum par.

    Raises:
        ValueError: Se os tamanhos diferirem ou houver ausente ou infinito.
    """
    reais = np.asarray(valores_reais, dtype=float)
    previstos = np.asarray(valores_previstos, dtype=float)
    if reais.ndim != 1 or previstos.ndim != 1 or len(reais) != len(previstos):
        raise ValueError("valores_reais e valores_previstos devem ser 1-D e do mesmo tamanho.")
    if not (np.isfinite(reais).all() and np.isfinite(previstos).all()):
        raise ValueError("valores_reais e valores_previstos nao podem ter ausente ou infinito.")
    if len(reais) == 0:
        return float("nan")
    real_acima_do_previsto = reais > previstos
    return float(np.mean(real_acima_do_previsto))


@dataclasses.dataclass(frozen=True)
class DecisaoDoQuantil:
    """Resultado da regra de desempate da E1 (pre-declaracao, secao 3).

    Attributes:
        mae_medio_por_quantil: MAE medio (media dos horizontes) de cada candidato.
        quantil_de_referencia: O quantil em uso (0,85).
        melhor_quantil: Quantil de menor MAE medio (a referencia vence empate).
        mae_do_melhor: MAE medio do melhor.
        mae_da_referencia: MAE medio do quantil de referencia.
        ganho_relativo: `(MAE_ref - MAE_melhor) / MAE_ref`; zero se o melhor e a referencia.
        ganho_minimo_para_trocar: Limite da regra (0,02).
        quantil_escolhido: A referencia se `ganho_relativo < ganho_minimo`; senao o melhor.
    """

    mae_medio_por_quantil: dict[float, float]
    quantil_de_referencia: float
    melhor_quantil: float
    mae_do_melhor: float
    mae_da_referencia: float
    ganho_relativo: float
    ganho_minimo_para_trocar: float
    quantil_escolhido: float


def decidir_quantil(
    mae_medio_por_quantil: dict[float, float],
    quantil_de_referencia: float,
    ganho_minimo_para_trocar: float,
) -> DecisaoDoQuantil:
    """Aplica a regra pre-declarada: o quantil de referencia fica, a menos que outro o supere por >= 2%.

    O ganho relativo e `(MAE_ref - MAE_melhor) / MAE_ref`. Troca-se so se o
    ganho for MAIOR OU IGUAL ao limite; abaixo dele (inclusive ganho zero,
    quando a referencia ja e a melhor) o quantil de referencia continua. Em
    empate exato de MAE, a referencia e preferida a qualquer outro.

    Args:
        mae_medio_por_quantil: MAE medio por candidato; deve conter a referencia.
        quantil_de_referencia: Quantil em uso (0,85).
        ganho_minimo_para_trocar: Ganho relativo minimo para trocar (0,02).

    Returns:
        A `DecisaoDoQuantil`.

    Raises:
        ValueError: Se a referencia nao estiver nos candidatos, se algum MAE
            nao for finito e positivo, ou se o limite nao estiver em [0, 1).
    """
    if quantil_de_referencia not in mae_medio_por_quantil:
        raise ValueError(f"O quantil de referencia {quantil_de_referencia} nao esta entre os candidatos.")
    if not 0.0 <= ganho_minimo_para_trocar < 1.0:
        raise ValueError(f"ganho_minimo_para_trocar deve estar em [0, 1), recebido {ganho_minimo_para_trocar!r}.")
    for quantil, mae_medio in mae_medio_por_quantil.items():
        if not np.isfinite(mae_medio) or mae_medio <= 0.0:
            raise ValueError(f"MAE medio invalido para o quantil {quantil}: {mae_medio!r}.")

    mae_da_referencia = mae_medio_por_quantil[quantil_de_referencia]
    melhor_quantil = quantil_de_referencia
    mae_do_melhor = mae_da_referencia
    for quantil in sorted(mae_medio_por_quantil):
        mae_do_candidato = mae_medio_por_quantil[quantil]
        if mae_do_candidato < mae_do_melhor:
            melhor_quantil = quantil
            mae_do_melhor = mae_do_candidato

    ganho_relativo = (mae_da_referencia - mae_do_melhor) / mae_da_referencia
    if ganho_relativo >= ganho_minimo_para_trocar and melhor_quantil != quantil_de_referencia:
        quantil_escolhido = melhor_quantil
    else:
        quantil_escolhido = quantil_de_referencia

    return DecisaoDoQuantil(
        mae_medio_por_quantil=dict(mae_medio_por_quantil),
        quantil_de_referencia=quantil_de_referencia,
        melhor_quantil=melhor_quantil,
        mae_do_melhor=mae_do_melhor,
        mae_da_referencia=mae_da_referencia,
        ganho_relativo=ganho_relativo,
        ganho_minimo_para_trocar=ganho_minimo_para_trocar,
        quantil_escolhido=quantil_escolhido,
    )


def calcular_mae_na_janela(
    previsoes: pd.DataFrame,
    configuracao_avaliacao: ConfiguracaoAvaliacao,
) -> tuple[int, float]:
    """Numero de semanas e MAE das previsoes dentro da janela de avaliacao (por `data_alvo`).

    Args:
        previsoes: DataFrame com `data_alvo`, `real` e `previsto`, de um so braco e horizonte.
        configuracao_avaliacao: Define a janela (07/01/2024 a 01/02/2026).

    Returns:
        `(n, mae)`; o MAE e NaN se a janela ficar vazia.
    """
    previsoes_na_janela = recortar_janela_de_avaliacao(previsoes, configuracao_avaliacao)
    mae = erro_absoluto_medio(previsoes_na_janela[COLUNA_DO_REAL], previsoes_na_janela[COLUNA_DO_PREVISTO])
    return len(previsoes_na_janela), mae


COLUNAS_DA_COMPARACAO_DE_CORTES = (
    COLUNA_DO_BRACO,
    COLUNA_DO_HORIZONTE,
    "n",
    "mae_corte_resposta",
    "mae_corte_pergunta",
    "variacao_pct",
    "r2_corte_resposta",
    "r2_corte_pergunta",
)


def comparar_cortes(
    previsoes_corte_resposta: pd.DataFrame,
    previsoes_corte_pergunta: pd.DataFrame,
    configuracao_avaliacao: ConfiguracaoAvaliacao,
) -> pd.DataFrame:
    """E4: MAE e R2, por braco e horizonte, com o corte pela resposta e pelo corte pela pergunta.

    As duas tabelas sao recortadas na janela de avaliacao e cruzadas por
    (braco, h, data_alvo): so as semanas presentes nos dois lados entram, e a
    funcao EXIGE que sejam as mesmas (o corte so muda o treino, nao as
    origens). `variacao_pct = 100 * (MAE_pergunta - MAE_resposta) / MAE_resposta`
    (negativo = o corte ingenuo parece melhor, que e o efeito do vazamento).

    Args:
        previsoes_corte_resposta: `braco`, `h`, `data_alvo`, `real`, `previsto`.
        previsoes_corte_pergunta: Mesmas colunas.
        configuracao_avaliacao: Define a janela.

    Returns:
        DataFrame com `braco`, `h`, `n`, `mae_corte_resposta`,
        `mae_corte_pergunta`, `variacao_pct`, `r2_corte_resposta`,
        `r2_corte_pergunta`, ordenado por braco (ordem de aparicao) e `h`.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se as semanas dos dois lados nao forem as mesmas, se o
            `real` diferir entre os lados, ou se o MAE do corte pela resposta for zero.
    """
    chave = [COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]
    colunas_necessarias = [*chave, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
    for nome_do_lado, tabela in (("resposta", previsoes_corte_resposta), ("pergunta", previsoes_corte_pergunta)):
        colunas_ausentes = sorted(set(colunas_necessarias) - set(tabela.columns))
        if colunas_ausentes:
            raise KeyError(f"Colunas ausentes nas previsoes do corte pela {nome_do_lado}: {colunas_ausentes}")

    na_janela_da_resposta = recortar_janela_de_avaliacao(previsoes_corte_resposta, configuracao_avaliacao)
    na_janela_da_pergunta = recortar_janela_de_avaliacao(previsoes_corte_pergunta, configuracao_avaliacao)
    do_lado_da_resposta = na_janela_da_resposta[colunas_necessarias].rename(
        columns={COLUNA_DO_REAL: "real_resposta", COLUNA_DO_PREVISTO: "previsto_resposta"}
    )
    do_lado_da_pergunta = na_janela_da_pergunta[colunas_necessarias].rename(
        columns={COLUNA_DO_REAL: "real_pergunta", COLUNA_DO_PREVISTO: "previsto_pergunta"}
    )
    cruzamento = do_lado_da_resposta.merge(do_lado_da_pergunta, on=chave, how="outer", indicator=True)

    quantidade_de_semanas_soltas = int((cruzamento["_merge"] != "both").sum())
    if quantidade_de_semanas_soltas > 0:
        raise ValueError(
            f"{quantidade_de_semanas_soltas} semana(s) (braco, h, data_alvo) aparecem so em um dos cortes; "
            "a comparacao exige as mesmas semanas nos dois lados."
        )
    diferenca_do_real = (cruzamento["real_resposta"] - cruzamento["real_pergunta"]).abs()
    if bool((diferenca_do_real > 0.0).any()):
        raise ValueError("A coluna `real` difere entre os dois cortes; as tabelas nao sao da mesma serie.")

    linhas: list[dict[str, object]] = []
    for nome_do_braco in pd.unique(cruzamento[COLUNA_DO_BRACO]):
        do_braco = cruzamento.loc[cruzamento[COLUNA_DO_BRACO] == nome_do_braco]
        for horizonte in sorted(pd.unique(do_braco[COLUNA_DO_HORIZONTE])):
            do_horizonte = do_braco.loc[do_braco[COLUNA_DO_HORIZONTE] == horizonte]
            valores_reais = do_horizonte["real_resposta"]
            previsto_pela_resposta = do_horizonte["previsto_resposta"]
            previsto_pela_pergunta = do_horizonte["previsto_pergunta"]
            mae_pela_resposta = erro_absoluto_medio(valores_reais, previsto_pela_resposta)
            mae_pela_pergunta = erro_absoluto_medio(valores_reais, previsto_pela_pergunta)
            if mae_pela_resposta == 0.0:
                raise ValueError(f"MAE zero no corte pela resposta (braco {nome_do_braco}, h {horizonte}).")
            variacao_percentual = 100.0 * (mae_pela_pergunta - mae_pela_resposta) / mae_pela_resposta
            linhas.append(
                {
                    COLUNA_DO_BRACO: nome_do_braco,
                    COLUNA_DO_HORIZONTE: int(horizonte),
                    "n": len(do_horizonte),
                    "mae_corte_resposta": mae_pela_resposta,
                    "mae_corte_pergunta": mae_pela_pergunta,
                    "variacao_pct": variacao_percentual,
                    "r2_corte_resposta": r_quadrado(valores_reais, previsto_pela_resposta),
                    "r2_corte_pergunta": r_quadrado(valores_reais, previsto_pela_pergunta),
                }
            )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DA_COMPARACAO_DE_CORTES))


COLUNAS_DOS_DELTAS_DO_PISO = ("perturbacao", "folha", COLUNA_DO_HORIZONTE, "n", "mae", "mae_referencia", "delta")
COLUNAS_DO_PISO = ("folha", COLUNA_DO_HORIZONTE, "piso_de_ruido", "perturbacao_do_maximo", "duas_vezes_o_piso")


def calcular_deltas_e_piso_de_ruido(
    mae_por_perturbacao: pd.DataFrame,
    mae_de_referencia: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Piso de ruido: para cada folha e horizonte, o maior |MAE(perturbada) - MAE(referencia)|.

    Args:
        mae_por_perturbacao: `perturbacao`, `folha`, `h`, `n`, `mae` (uma linha
            por perturbacao, folha e horizonte, MAE na janela de avaliacao).
        mae_de_referencia: `folha`, `h`, `mae` da referencia certificada
            (sem perturbacao), na mesma janela.

    Returns:
        `(deltas, piso)`. `deltas` tem `perturbacao`, `folha`, `h`, `n`, `mae`,
        `mae_referencia`, `delta` (o valor ABSOLUTO). `piso` tem `folha`, `h`,
        `piso_de_ruido` (o maior delta), `perturbacao_do_maximo` e
        `duas_vezes_o_piso` (o limite da regra de leitura da pre-declaracao).

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se alguma (folha, h) de `mae_por_perturbacao` nao tiver referencia.
    """
    colunas_das_perturbacoes = ["perturbacao", "folha", COLUNA_DO_HORIZONTE, "n", "mae"]
    colunas_da_referencia = ["folha", COLUNA_DO_HORIZONTE, "mae"]
    colunas_ausentes_nas_perturbacoes = sorted(set(colunas_das_perturbacoes) - set(mae_por_perturbacao.columns))
    if colunas_ausentes_nas_perturbacoes:
        raise KeyError(f"Colunas ausentes em mae_por_perturbacao: {colunas_ausentes_nas_perturbacoes}")
    colunas_ausentes_na_referencia = sorted(set(colunas_da_referencia) - set(mae_de_referencia.columns))
    if colunas_ausentes_na_referencia:
        raise KeyError(f"Colunas ausentes em mae_de_referencia: {colunas_ausentes_na_referencia}")

    referencia = mae_de_referencia[colunas_da_referencia].rename(columns={"mae": "mae_referencia"})
    cruzamento = mae_por_perturbacao[colunas_das_perturbacoes].merge(
        referencia, on=["folha", COLUNA_DO_HORIZONTE], how="left"
    )
    if cruzamento["mae_referencia"].isna().any():
        raise ValueError("Ha (folha, h) sem MAE de referencia correspondente.")

    cruzamento["delta"] = (cruzamento["mae"] - cruzamento["mae_referencia"]).abs()
    deltas = cruzamento[list(COLUNAS_DOS_DELTAS_DO_PISO)].copy()

    linhas_do_piso: list[dict[str, object]] = []
    for folha in sorted(pd.unique(deltas["folha"])):
        da_folha = deltas.loc[deltas["folha"] == folha]
        for horizonte in sorted(pd.unique(da_folha[COLUNA_DO_HORIZONTE])):
            do_horizonte = da_folha.loc[da_folha[COLUNA_DO_HORIZONTE] == horizonte]
            posicao_do_maximo = do_horizonte["delta"].to_numpy().argmax()
            piso = float(do_horizonte["delta"].to_numpy()[posicao_do_maximo])
            perturbacao_do_maximo = str(do_horizonte["perturbacao"].to_numpy()[posicao_do_maximo])
            linhas_do_piso.append(
                {
                    "folha": int(folha),
                    COLUNA_DO_HORIZONTE: int(horizonte),
                    "piso_de_ruido": piso,
                    "perturbacao_do_maximo": perturbacao_do_maximo,
                    "duas_vezes_o_piso": 2.0 * piso,
                }
            )
    piso_por_folha_e_horizonte = pd.DataFrame(linhas_do_piso, columns=list(COLUNAS_DO_PISO))
    return deltas, piso_por_folha_e_horizonte
