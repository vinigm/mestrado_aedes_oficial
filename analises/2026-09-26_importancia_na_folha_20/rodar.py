"""Importancia por bloco na configuracao de folha minima 20.

O que este script responde
--------------------------
O bloco 3 da bateria de 23/09/2026 mediu quanto o modelo ADOTADO (folha minima
5) se apoia em cada bloco de colunas, trocando o bloco inteiro por semanas
sorteadas do proprio treino. O vetor domina de h=4 a h=11.

Falta a mesma medicao na configuracao de folha minima 20 — a unica das duas em
que o vetor REDUZ o erro na ablacao (+12,3% em 3 meses, bloco 7). Este script
repete o procedimento do bloco 3 mudando UM parametro: `min_samples_leaf`, de
5 para 20.

⚠️ ESTATUTO: DESCRITIVO. Nao testa hipotese, nao calcula valor-p, nao abre
familia de correcao multipla e nao autoriza trocar a configuracao adotada.
Protocolo completo em PRE_DECLARACAO.md.

Por que o procedimento e copiado e nao importado
------------------------------------------------
O laco de medicao e transcrito do bloco 3 em vez de importado porque a
comparacao entre as duas configuracoes so vale se o procedimento for
identico ate a ordem de consumo do gerador aleatorio. Transcrever deixa as duas
versoes lado a lado e auditaveis; importar esconderia uma divergencia futura no
bloco 3 dentro deste resultado.

⚠️ A ordem de consumo do gerador e parte do contrato: mesmo horizonte, mesmo
corte, mesma ordem dos blocos (Nucleo, Clima, Vetor) e mesmo numero de trocas.
Como os tamanhos de treino nao dependem do modelo, as semanas sorteadas aqui
sao as MESMAS do bloco 3, e as duas medicoes ficam pareadas no sorteio.
"""

from __future__ import annotations

import pathlib
import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DA_BATERIA = PASTA_DESTE_ARQUIVO.parent / "2026-09-23_bateria_noturna"
sys.path.insert(0, str(PASTA_DA_BATERIA))

import harness  # noqa: E402  (depende do sys.path ajustado acima)
from config.experimentos.cidade_referencia import CIDADE_REFERENCIA  # noqa: E402
from config.modelo import EspecificacaoModelo  # noqa: E402
from dominio import selecao_features  # noqa: E402
from dominio.features import construir_alvo_horizonte  # noqa: E402
from motor import corte_temporal  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

CAMINHO_DA_FOLHA_5 = (
    PASTA_DA_BATERIA
    / "bloco_3_importancia_por_bloco"
    / "saidas"
    / "importancia_por_horizonte.csv"
)
CAMINHO_DAS_PREVISOES_DO_BLOCO_7 = (
    PASTA_DA_BATERIA
    / "bloco_7_vetor_com_folha_20"
    / "saidas"
    / "previsoes_por_braco.csv"
)
NOME_DO_BRACO_NO_BLOCO_7 = "HistGB_folha20_M1"

# Quantas trocas por bloco em cada corte, e a semente. Os dois valores sao os
# do bloco 3 e NAO podem mudar: alterar qualquer um deles quebra o pareamento
# do sorteio entre as duas configuracoes.
TROCAS_POR_BLOCO = 20
SEMENTE = 42

HORIZONTES = CIDADE_REFERENCIA.horizontes

# A ordem desta tupla e a ordem de consumo do gerador aleatorio. E a mesma do
# dicionario do bloco 3, e trocar a ordem trocaria as semanas sorteadas.
NOMES_DOS_BLOCOS = ("Nucleo", "Clima", "Vetor")

# A configuracao medida aqui. Identica a referencia (cidade_referencia.py),
# com `min_samples_leaf` em 20 no lugar de 5. Copiada do bloco 7, que e de onde
# vem a ancora da trava.
HISTGB_FOLHA_20 = EspecificacaoModelo(
    nome="histgb_folha20",
    classe=HistGradientBoostingRegressor,
    parametros={
        "max_iter": 250,
        "learning_rate": 0.05,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 20,
        "random_state": 42,
        "loss": "quantile",
        "quantile": 0.85,
    },
)

# O que a previsao SEM troca tem de reproduzir para o resultado valer. Sao os
# numeros do braco HistGB_folha20_M1 do bloco 7, recalculados do CSV em
# 26/09/2026 no periodo de avaliacao (n=102 em cada horizonte).
#
# 🔴 A trava tambem prova que a tabela de dados continua a de 23/09/2026: a
# reversao de 2026, feita em 26/09, tinha de devolver a base ao estado
# anterior. Se ela nao tiver devolvido, os MAE divergem e o script para.
ANCORAS_DA_FOLHA_20 = {
    1: {"mae": 133.6259, "r2": 0.8335, "semanas": 102},
    4: {"mae": 199.6352, "r2": 0.7167, "semanas": 102},
    8: {"mae": 223.1827, "r2": 0.5761, "semanas": 102},
    12: {"mae": 243.7645, "r2": 0.5577, "semanas": 102},
}
TOLERANCIA_DE_MAE = 0.2
TOLERANCIA_DE_R2 = 0.003


def separar_blocos(
    colunas_do_modelo: list[str], tabela: pd.DataFrame
) -> dict[str, list[str]]:
    """Diz a qual bloco pertence cada coluna que vai ao modelo.

    A separacao usa os mesmos padroes de nome da configuracao de referencia. O
    clima e definido por exclusao — tudo que nao e nucleo nem vetor —, que e
    como o bloco 3 fez.

    Args:
        colunas_do_modelo: As colunas que efetivamente entram no modelo, na
            ordem em que o harness as devolveu.
        tabela: A tabela ja com features, usada para refazer a separacao.

    Returns:
        Um dicionario de nome do bloco para a lista de colunas dele, com as
        chaves na ordem de `NOMES_DOS_BLOCOS`.
    """
    colunas_de_nucleo_do_pipeline, _, colunas_de_vetor_do_pipeline = (
        selecao_features.separar_grupos_de_features(
            tabela,
            CIDADE_REFERENCIA.colunas_ignorar,
            CIDADE_REFERENCIA.padroes_vetor,
            CIDADE_REFERENCIA.padroes_clima,
        )
    )

    colunas_do_nucleo: list[str] = []
    colunas_do_vetor: list[str] = []
    colunas_do_clima: list[str] = []

    for nome_da_coluna in colunas_do_modelo:
        if nome_da_coluna in colunas_de_nucleo_do_pipeline:
            colunas_do_nucleo.append(nome_da_coluna)
        elif nome_da_coluna in colunas_de_vetor_do_pipeline:
            colunas_do_vetor.append(nome_da_coluna)
        else:
            colunas_do_clima.append(nome_da_coluna)

    return {
        "Nucleo": colunas_do_nucleo,
        "Clima": colunas_do_clima,
        "Vetor": colunas_do_vetor,
    }


def medir_um_horizonte(
    tabela: pd.DataFrame,
    colunas_do_modelo: list[str],
    blocos: dict[str, list[str]],
    horizonte: int,
    gerador: np.random.Generator,
) -> pd.DataFrame:
    """Roda o walk-forward de um horizonte medindo a importancia de cada bloco.

    Em cada corte o modelo e treinado uma vez, com as semanas cuja resposta ja
    existia na data da pergunta, e preve a semana de teste de dois jeitos: com
    as colunas reais e com as colunas de um bloco trocadas.

    O sorteio da troca vem do TREINO, nunca do futuro: o que se quer medir e o
    bloco carregando informacao irrelevante para aquela semana, e nao o bloco
    carregando informacao que o modelo nao podia ter.

    Args:
        tabela: A tabela ja com features, antes do alvo do horizonte.
        colunas_do_modelo: As colunas que entram no modelo.
        blocos: O mapa de bloco para colunas, na ordem de consumo do gerador.
        horizonte: Quantas semanas a frente prever.
        gerador: O gerador aleatorio, consumido em ordem. ⚠️ E mutavel e
            compartilhado entre os horizontes: a ordem das chamadas faz parte
            do contrato desta medicao.

    Returns:
        Uma linha por corte, com o valor real, a previsao sem troca e o erro
        medio com cada bloco trocado.
    """
    dados_do_horizonte = construir_alvo_horizonte(
        tabela, CIDADE_REFERENCIA.coluna_alvo, horizonte
    )
    features_com_sazonalidade = colunas_do_modelo + ["alvo_sin", "alvo_cos"]
    dados_validos = (
        dados_do_horizonte.dropna(subset=features_com_sazonalidade + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    linhas_dos_cortes = []
    for indice_do_corte in range(
        CIDADE_REFERENCIA.minimo_semanas_treino,
        len(dados_validos),
        CIDADE_REFERENCIA.passo,
    ):
        teste = dados_validos.iloc[indice_do_corte : indice_do_corte + 1]
        data_do_teste = teste["data"].to_numpy()[0]
        treino = corte_temporal.selecionar_treino_ja_respondido(
            dados_validos, data_do_teste, horizonte
        )

        modelo = HISTGB_FOLHA_20.criar()
        modelo.fit(treino[features_com_sazonalidade], treino["y_h"])

        entrada_real = teste[features_com_sazonalidade]
        previsao_real = float(modelo.predict(entrada_real)[0])
        valor_real = float(teste["y_h"].to_numpy()[0])

        linha_do_corte = {
            "h": horizonte,
            "data_alvo": pd.Timestamp(data_do_teste) + pd.Timedelta(weeks=horizonte),
            "real": valor_real,
            "previsto": previsao_real,
        }

        for nome_do_bloco in NOMES_DOS_BLOCOS:
            colunas_do_bloco = blocos[nome_do_bloco]
            semanas_sorteadas = gerador.integers(
                0, len(treino), size=TROCAS_POR_BLOCO
            )
            entradas_trocadas = pd.concat(
                [entrada_real] * TROCAS_POR_BLOCO, ignore_index=True
            )
            valores_sorteados = treino[colunas_do_bloco].to_numpy()[semanas_sorteadas]
            entradas_trocadas[colunas_do_bloco] = valores_sorteados

            previsoes_trocadas = modelo.predict(entradas_trocadas)
            erro_medio_trocado = float(
                np.mean(np.abs(valor_real - previsoes_trocadas))
            )
            linha_do_corte[f"erro_sem_{nome_do_bloco}"] = erro_medio_trocado

        linhas_dos_cortes.append(linha_do_corte)

    return pd.DataFrame(linhas_dos_cortes)


def conferir_trava_da_folha_20(previsoes: pd.DataFrame) -> bool:
    """Diz se a previsao sem troca reproduz o braco de folha 20 do bloco 7.

    O HistGB com semente fixa e deterministico, entao a reproducao tem de ser
    exata dentro da tolerancia do harness. Uma divergencia aqui significa que
    o modelo, o laco de walk-forward ou a tabela de dados mudaram.

    Args:
        previsoes: As previsoes de todos os horizontes, com `data_alvo`,
            `real` e `previsto`.

    Returns:
        True se os quatro horizontes baterem em MAE, R2 e numero de semanas.
    """
    avaliacao = previsoes[previsoes["data_alvo"] >= harness.INICIO_DA_AVALIACAO]

    print("\n  TRAVA — folha 20 contra o bloco 7 (periodo de avaliacao)")
    tudo_bate = True
    for horizonte, esperado in ANCORAS_DA_FOLHA_20.items():
        celula = avaliacao[avaliacao["h"] == horizonte]
        if celula.empty:
            print(f"    h={horizonte:2d}  SEM DADOS")
            tudo_bate = False
            continue

        mae_medido = mean_absolute_error(celula["real"], celula["previsto"])
        r2_medido = r2_score(celula["real"], celula["previsto"])
        semanas_medidas = len(celula)

        bate = (
            abs(mae_medido - esperado["mae"]) < TOLERANCIA_DE_MAE
            and abs(r2_medido - esperado["r2"]) < TOLERANCIA_DE_R2
            and semanas_medidas == esperado["semanas"]
        )
        tudo_bate = tudo_bate and bate
        marca = "ok" if bate else "<<< DIVERGE"
        print(
            f"    h={horizonte:2d}  n {semanas_medidas:3d}  "
            f"MAE {mae_medido:8.3f} (bloco 7 {esperado['mae']:8.3f})  "
            f"R2 {r2_medido:6.3f} (bloco 7 {esperado['r2']:5.3f})  {marca}"
        )

    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}")
    return tudo_bate


def resumir_por_horizonte(
    previsoes: pd.DataFrame, blocos: dict[str, list[str]]
) -> pd.DataFrame:
    """Condensa os cortes num resumo por horizonte, no periodo de avaliacao.

    Args:
        previsoes: Uma linha por corte, com o erro de cada bloco trocado.
        blocos: O mapa de bloco para colunas, so para saber os nomes.

    Returns:
        Uma linha por horizonte, com o MAE e o R2 sem troca e o aumento do erro
        de cada bloco, em casos e em percentual do proprio MAE.
    """
    avaliacao = previsoes[previsoes["data_alvo"] >= harness.INICIO_DA_AVALIACAO]

    linhas_do_resumo = []
    for horizonte in HORIZONTES:
        celula = avaliacao[avaliacao["h"] == horizonte]
        mae_sem_troca = mean_absolute_error(celula["real"], celula["previsto"])
        r2_sem_troca = r2_score(celula["real"], celula["previsto"])

        linha_do_horizonte = {
            "h": horizonte,
            "mae_real": mae_sem_troca,
            "r2_real": r2_sem_troca,
            "semanas": len(celula),
        }
        for nome_do_bloco in blocos:
            erro_medio_trocado = float(celula[f"erro_sem_{nome_do_bloco}"].mean())
            aumento_em_casos = erro_medio_trocado - mae_sem_troca
            aumento_percentual = 100.0 * aumento_em_casos / mae_sem_troca
            linha_do_horizonte[f"aumento_mae_{nome_do_bloco}"] = aumento_em_casos
            linha_do_horizonte[f"aumento_pct_{nome_do_bloco}"] = aumento_percentual

        linhas_do_resumo.append(linha_do_horizonte)

    return pd.DataFrame(linhas_do_resumo)


def comparar_com_a_folha_5(resumo_da_folha_20: pd.DataFrame) -> pd.DataFrame:
    """Poe a importancia do vetor nas duas configuracoes lado a lado.

    Args:
        resumo_da_folha_20: O resumo por horizonte medido neste script.

    Returns:
        Uma linha por horizonte, com a importancia de cada bloco nas duas
        configuracoes e a diferenca em pontos percentuais no vetor.

    Raises:
        FileNotFoundError: Se o resumo do bloco 3 nao estiver em disco.
    """
    if not CAMINHO_DA_FOLHA_5.exists():
        raise FileNotFoundError(
            f"O resumo da folha 5 nao esta em {CAMINHO_DA_FOLHA_5}. "
            "Ele e a saida do bloco 3 da bateria de 23/09/2026."
        )

    resumo_da_folha_5 = pd.read_csv(CAMINHO_DA_FOLHA_5)

    linhas_da_comparacao = []
    for horizonte in HORIZONTES:
        da_folha_5 = resumo_da_folha_5[resumo_da_folha_5["h"] == horizonte].iloc[0]
        da_folha_20 = resumo_da_folha_20[
            resumo_da_folha_20["h"] == horizonte
        ].iloc[0]

        vetor_na_folha_5 = float(da_folha_5["aumento_pct_Vetor"])
        vetor_na_folha_20 = float(da_folha_20["aumento_pct_Vetor"])

        linhas_da_comparacao.append(
            {
                "h": horizonte,
                "mae_folha_5": float(da_folha_5["mae_real"]),
                "mae_folha_20": float(da_folha_20["mae_real"]),
                "nucleo_folha_5": float(da_folha_5["aumento_pct_Nucleo"]),
                "nucleo_folha_20": float(da_folha_20["aumento_pct_Nucleo"]),
                "clima_folha_5": float(da_folha_5["aumento_pct_Clima"]),
                "clima_folha_20": float(da_folha_20["aumento_pct_Clima"]),
                "vetor_folha_5": vetor_na_folha_5,
                "vetor_folha_20": vetor_na_folha_20,
                "diferenca_do_vetor_pp": vetor_na_folha_20 - vetor_na_folha_5,
            }
        )

    return pd.DataFrame(linhas_da_comparacao)


def main() -> None:
    """Mede a importancia dos tres blocos na folha 20 e compara com a folha 5."""
    print("=" * 78)
    print("IMPORTANCIA POR BLOCO — configuracao de folha minima 20")
    print("=" * 78, flush=True)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela_bruta = harness.carregar_tabela_bruta()
    braco_de_referencia = harness.Braco("A_referencia")
    tabela, colunas_do_modelo, _ = harness.montar_features_do_braco(
        tabela_bruta, braco_de_referencia
    )
    blocos = separar_blocos(colunas_do_modelo, tabela)

    for nome_do_bloco in NOMES_DOS_BLOCOS:
        print(f"  {nome_do_bloco}: {len(blocos[nome_do_bloco])} colunas", flush=True)

    gerador = np.random.default_rng(SEMENTE)
    previsoes_por_horizonte = []
    for horizonte in HORIZONTES:
        marca_de_tempo = time.perf_counter()
        previsoes_do_horizonte = medir_um_horizonte(
            tabela, colunas_do_modelo, blocos, horizonte, gerador
        )
        previsoes_por_horizonte.append(previsoes_do_horizonte)
        print(
            f"  h={horizonte:2d}  {len(previsoes_do_horizonte):3d} sem  "
            f"{time.perf_counter() - marca_de_tempo:5.1f}s",
            flush=True,
        )

    todas_as_previsoes = pd.concat(previsoes_por_horizonte, ignore_index=True)
    todas_as_previsoes["braco"] = NOME_DO_BRACO_NO_BLOCO_7
    todas_as_previsoes.to_csv(
        PASTA_DE_SAIDAS / "importancia_por_corte.csv", index=False
    )

    if not conferir_trava_da_folha_20(todas_as_previsoes):
        print(
            "\n  BLOCO INVALIDO: a folha 20 nao reproduziu o bloco 7. "
            "Nenhum numero novo deve ser lido.",
            flush=True,
        )
        return

    resumo = resumir_por_horizonte(todas_as_previsoes, blocos)
    resumo.to_csv(PASTA_DE_SAIDAS / "importancia_por_horizonte.csv", index=False)

    print("\n  aumento do MAE quando o bloco e trocado, periodo de avaliacao")
    print(f"  {'h':>3} {'MAE real':>9} {'R2':>7} | {'Nucleo':>9} {'Clima':>9} {'Vetor':>9}")
    for _, linha in resumo.iterrows():
        texto_da_linha = (
            f"  {int(linha['h']):3d} {linha['mae_real']:9.1f} {linha['r2_real']:7.3f} |"
        )
        for nome_do_bloco in NOMES_DOS_BLOCOS:
            texto_da_linha += f" {linha[f'aumento_pct_{nome_do_bloco}']:8.1f}%"
        print(texto_da_linha)

    comparacao = comparar_com_a_folha_5(resumo)
    comparacao.to_csv(PASTA_DE_SAIDAS / "folha_5_contra_folha_20.csv", index=False)

    print("\n  IMPORTANCIA DO VETOR — folha 5 contra folha 20")
    print(f"  {'h':>3} {'folha 5':>9} {'folha 20':>9} {'diferenca':>11}")
    for _, linha in comparacao.iterrows():
        print(
            f"  {int(linha['h']):3d} {linha['vetor_folha_5']:8.1f}% "
            f"{linha['vetor_folha_20']:8.1f}% "
            f"{linha['diferenca_do_vetor_pp']:+10.1f} pp"
        )


if __name__ == "__main__":
    main()
