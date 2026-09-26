"""Mede um modelo composto: folha minima 5 no horizonte curto, folha 20 no longo.

Por que existe
--------------
Pergunta do Vinicius em 26/09/2026. Duas configuracoes do mesmo algoritmo tem
forcas opostas, medidas na bateria de 23-24/09/2026:

  - a **folha 5**, que e o cenario adotado, erra menos ate 3 semanas a frente;
  - a **folha 20** erra menos de 4 semanas em diante, e e a unica das duas que
    extrai ganho das colunas do vetor em horizonte longo.

A pergunta: e se cada horizonte usasse a configuracao que vai melhor nele?

⚠️ ESTATUTO: DESCRITIVO E POSTERIOR AOS FATOS
---------------------------------------------
Este script NAO testa hipotese, NAO calcula valor-p e NAO abre familia de
correcao multipla. Ele recombina previsoes ja salvas.

O ponto de corte entre as duas configuracoes foi escolhido OLHANDO o periodo de
avaliacao. Isso e contaminacao: o mesmo periodo que serve de juiz nao pode
escolher o competidor. Por isso o resultado aqui vale como **ilustracao do que
um composto renderia**, e NAO como configuracao adotavel. Adotar exige
pre-declarar o criterio antes e re-rodar o grid.

Entrada
-------
`../2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/saidas/
previsoes_por_braco.csv`, com os bracos `referencia` (folha 5, com vetor) e
`HistGB_folha20_M1` (folha 20, com vetor), nos 12 horizontes.

A regua sazonal e calculada aqui, do proprio arquivo: a previsao para uma
semana e o numero real de casos 52 semanas antes.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

# O corte entre as duas configuracoes. Ate 3 semanas a folha 5 vai melhor; de 4
# em diante, a folha 20. ⚠️ Este numero foi lido da avaliacao, e e justamente
# o que torna o resultado contaminado (ver o cabecalho).
ULTIMO_HORIZONTE_DA_FOLHA_5 = 3

BRACO_FOLHA_5 = "referencia"
BRACO_FOLHA_20 = "HistGB_folha20_M1"

# Limiar de surto usado na captura do pico. E convencao do projeto, nao criterio
# oficial: o Plano Municipal de Contingencia usa 140, 421 e 702.
LIMIAR_DE_SURTO = 100

# Semanas entre uma temporada e a seguinte, para a regua sazonal.
SEMANAS_DE_UM_ANO = 52

# ⚠️ O arquivo de previsoes cobre de 2020 em diante, mas o painel do projeto e
# medido SO na janela de avaliacao. Sem este filtro o erro de h=1 da 48,5 em vez
# dos 98,0 publicados, porque 2020-2023 sao anos quase sem casos e puxam a media
# para baixo. INICIO_DA_AVALIACAO e o mesmo de `harness.py`.
INICIO_DA_AVALIACAO = "2024-01-01"

HORIZONTES_RELATADOS = (1, 4, 8, 12)

PASTA_DESTE_SCRIPT = pathlib.Path(__file__).resolve().parent
CAMINHO_PREVISOES = (
    PASTA_DESTE_SCRIPT.parent
    / "2026-09-23_bateria_noturna"
    / "bloco_7_vetor_com_folha_20"
    / "saidas"
    / "previsoes_por_braco.csv"
)
PASTA_SAIDAS = PASTA_DESTE_SCRIPT / "saidas"


def carregar_previsoes(caminho: pathlib.Path) -> pd.DataFrame:
    """Le as previsoes dos dois bracos e converte a data-alvo.

    Args:
        caminho: Caminho de `previsoes_por_braco.csv`.

    Returns:
        A tabela com `data_alvo` ja como data.
    """
    previsoes = pd.read_csv(caminho)
    previsoes["data_alvo"] = pd.to_datetime(previsoes["data_alvo"])
    return previsoes


def recortar_para_a_avaliacao(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Mantem so as semanas da janela de avaliacao do projeto.

    Args:
        previsoes: A tabela completa, que comeca em 2020.

    Returns:
        So as linhas com data-alvo a partir de `INICIO_DA_AVALIACAO`.
    """
    return previsoes[previsoes["data_alvo"] >= INICIO_DA_AVALIACAO]


def montar_regua_sazonal(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Monta a previsao da regua sazonal para as mesmas semanas avaliadas.

    A regua responde "quantos casos houve nesta mesma semana do ano passado?".
    Ela nao usa mosquito nem clima: so o proprio historico de casos.

    Args:
        previsoes: A tabela de previsoes, de onde saem as semanas e os reais.

    Returns:
        Uma tabela com as colunas `h`, `data_alvo`, `real`, `previsto` e
        `braco`, no mesmo formato dos demais bracos.
    """
    de_um_braco = previsoes[previsoes["braco"] == BRACO_FOLHA_5]
    casos_reais_por_semana = (
        de_um_braco.drop_duplicates("data_alvo").set_index("data_alvo")["real"]
    )

    linhas_da_regua = []
    for horizonte in sorted(previsoes["h"].unique()):
        do_horizonte = previsoes[
            (previsoes["h"] == horizonte) & (previsoes["braco"] == BRACO_FOLHA_5)
        ]
        for _, linha in do_horizonte.iterrows():
            semana_do_ano_anterior = linha["data_alvo"] - pd.Timedelta(
                weeks=SEMANAS_DE_UM_ANO
            )
            if semana_do_ano_anterior not in casos_reais_por_semana.index:
                continue
            linhas_da_regua.append(
                {
                    "h": horizonte,
                    "data_alvo": linha["data_alvo"],
                    "real": linha["real"],
                    "previsto": casos_reais_por_semana[semana_do_ano_anterior],
                    "braco": "regua_sazonal",
                }
            )
    return pd.DataFrame(linhas_da_regua)


def montar_modelo_composto(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Monta o braco composto, trocando de configuracao conforme o horizonte.

    Args:
        previsoes: A tabela com os dois bracos.

    Returns:
        A tabela do composto, no mesmo formato dos demais bracos.
    """
    curto = previsoes[
        (previsoes["braco"] == BRACO_FOLHA_5)
        & (previsoes["h"] <= ULTIMO_HORIZONTE_DA_FOLHA_5)
    ]
    longo = previsoes[
        (previsoes["braco"] == BRACO_FOLHA_20)
        & (previsoes["h"] > ULTIMO_HORIZONTE_DA_FOLHA_5)
    ]
    composto = pd.concat([curto, longo], ignore_index=True).copy()
    composto["braco"] = "composto"
    return composto


def calcular_metricas(de_um_braco: pd.DataFrame) -> dict[str, float]:
    """Calcula as tres metricas do painel para um braco, num horizonte.

    Args:
        de_um_braco: As previsoes de um unico braco e horizonte.

    Returns:
        Um dicionario com o erro absoluto medio, o coeficiente de determinacao
        e a captura do pico.
    """
    real = de_um_braco["real"].to_numpy()
    previsto = de_um_braco["previsto"].to_numpy()

    erro_absoluto_medio = float(np.abs(real - previsto).mean())

    soma_dos_quadrados_do_erro = float(((real - previsto) ** 2).sum())
    soma_dos_quadrados_total = float(((real - real.mean()) ** 2).sum())
    coeficiente_de_determinacao = 1.0 - soma_dos_quadrados_do_erro / soma_dos_quadrados_total

    semanas_de_surto = de_um_braco[de_um_braco["real"] > LIMIAR_DE_SURTO]
    if semanas_de_surto.empty:
        captura_do_pico = float("nan")
    else:
        captura_do_pico = float(
            semanas_de_surto["previsto"].mean() / semanas_de_surto["real"].mean()
        )

    return {
        "mae": erro_absoluto_medio,
        "r2": coeficiente_de_determinacao,
        "captura_do_pico": captura_do_pico,
        "n": len(de_um_braco),
    }


def main() -> None:
    """Calcula o painel dos quatro bracos e grava a tabela comparativa."""
    PASTA_SAIDAS.mkdir(exist_ok=True)
    previsoes = carregar_previsoes(CAMINHO_PREVISOES)

    todos_os_bracos = pd.concat(
        [
            previsoes[previsoes["braco"].isin([BRACO_FOLHA_5, BRACO_FOLHA_20])],
            montar_modelo_composto(previsoes),
            # A regua e montada ANTES do recorte, porque ela precisa olhar 52
            # semanas para tras: recortar primeiro deixaria 2024 sem referencia.
            montar_regua_sazonal(previsoes),
        ],
        ignore_index=True,
    )
    todos_os_bracos = recortar_para_a_avaliacao(todos_os_bracos)

    nomes_legiveis = {
        BRACO_FOLHA_5: "Adotado (folha 5)",
        BRACO_FOLHA_20: "Folha 20, com vetor",
        "composto": "Composto",
        "regua_sazonal": "Regua sazonal",
    }

    linhas_do_painel = []
    for nome_interno, nome_legivel in nomes_legiveis.items():
        for horizonte in HORIZONTES_RELATADOS:
            recorte = todos_os_bracos[
                (todos_os_bracos["braco"] == nome_interno)
                & (todos_os_bracos["h"] == horizonte)
            ]
            if recorte.empty:
                continue
            metricas = calcular_metricas(recorte)
            linhas_do_painel.append({"braco": nome_legivel, "h": horizonte, **metricas})

    painel = pd.DataFrame(linhas_do_painel)
    painel.to_csv(PASTA_SAIDAS / "painel_do_composto.csv", index=False)

    print(f"Previsoes lidas de {CAMINHO_PREVISOES.name}")
    print(f"Corte do composto: folha 5 ate h={ULTIMO_HORIZONTE_DA_FOLHA_5}, folha 20 depois\n")
    for horizonte in HORIZONTES_RELATADOS:
        print(f"--- h = {horizonte} semanas ---")
        do_horizonte = painel[painel["h"] == horizonte]
        for _, linha in do_horizonte.iterrows():
            print(
                f"  {linha['braco']:<22} MAE {linha['mae']:7.1f} | "
                f"R2 {linha['r2']:6.3f} | captura {linha['captura_do_pico']:.3f} | "
                f"n {int(linha['n'])}"
            )


if __name__ == "__main__":
    main()
