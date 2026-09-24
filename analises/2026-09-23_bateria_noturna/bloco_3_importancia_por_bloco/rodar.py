"""Bloco 3 — importancia por bloco, medida DENTRO do walk-forward.

A primeira medicao, de 23/09, usou um corte unico 80/20 e mostrou o vetor
crescendo com o horizonte. Mas o R2 base daquela medicao em h=12 foi 0,759,
contra 0,437 publicado: eram objetos diferentes, e o numero nao podia ir ao
painel ao lado do R2 do walk-forward.

Aqui a importancia sai do MESMO procedimento que gerou os numeros publicados.
Em cada corte do walk-forward o modelo e treinado uma vez e preve a semana de
teste de dois jeitos:

  - com as colunas reais;
  - com as colunas de UM bloco trocadas pelas de uma semana sorteada do
    proprio treino, repetido varias vezes.

A diferenca media de erro absoluto entre os dois e o quanto aquele bloco
carrega de informacao para aquela previsao. Somado sobre todos os cortes,
vira a importancia do bloco no horizonte.

Por que trocar o BLOCO inteiro, e nao coluna a coluna: as colunas de um bloco
sao a mesma serie deslocada, com correlacao media de 0,91 nos casos e 0,85 no
vetor. Trocar uma so deixa as irmas intactas socorrendo o modelo, e a
importancia de cada coluna sai perto de zero mesmo quando o bloco importa.

Protocolo em PRE_DECLARACAO.md.
"""

import pathlib
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA_DESTE_ARQUIVO.parent))

import harness  # noqa: E402
from config.experimentos.cidade_referencia import CIDADE_REFERENCIA  # noqa: E402
from dominio import selecao_features  # noqa: E402
from dominio.features import construir_alvo_horizonte  # noqa: E402
from motor import corte_temporal  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

# Quantas trocas por bloco em cada corte. Cada troca custa uma previsao de uma
# linha, que e barata perto do treino; 20 estabiliza a media sem pesar.
TROCAS_POR_BLOCO = 20
SEMENTE = 42

HORIZONTES = CIDADE_REFERENCIA.horizontes


def separar_blocos(colunas_do_modelo: list[str], tabela: pd.DataFrame) -> dict:
    """Diz a qual bloco pertence cada coluna que vai ao modelo.

    Args:
        colunas_do_modelo: As colunas do cenario adotado.
        tabela: A tabela com as features, usada para refazer a separacao.

    Returns:
        Um dicionario de nome do bloco para lista de colunas.
    """
    nucleo, _, vetor = selecao_features.separar_grupos_de_features(
        tabela,
        CIDADE_REFERENCIA.colunas_ignorar,
        CIDADE_REFERENCIA.padroes_vetor,
        CIDADE_REFERENCIA.padroes_clima,
    )
    colunas_nucleo = [c for c in colunas_do_modelo if c in nucleo]
    colunas_vetor = [c for c in colunas_do_modelo if c in vetor]
    colunas_clima = [
        c for c in colunas_do_modelo if c not in colunas_nucleo and c not in colunas_vetor
    ]

    return {"Nucleo": colunas_nucleo, "Clima": colunas_clima, "Vetor": colunas_vetor}


def medir_um_horizonte(tabela, colunas_do_modelo, blocos, horizonte, gerador):
    """Roda o walk-forward de um horizonte medindo a importancia de cada bloco.

    Returns:
        Uma linha por corte, com a previsao real e a previsao com cada bloco
        trocado, ja como media das trocas.
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

    linhas = []
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

        modelo = CIDADE_REFERENCIA.modelo.criar()
        modelo.fit(treino[features_com_sazonalidade], treino["y_h"])

        entrada_real = teste[features_com_sazonalidade]
        previsao_real = float(modelo.predict(entrada_real)[0])

        linha = {
            "h": horizonte,
            "data_alvo": pd.Timestamp(data_do_teste) + pd.Timedelta(weeks=horizonte),
            "real": float(teste["y_h"].to_numpy()[0]),
            "previsto": previsao_real,
        }

        # A troca sorteia semanas do TREINO, nunca do futuro: o que se quer
        # medir e o bloco carregando informacao irrelevante para esta semana,
        # e nao o bloco carregando informacao que o modelo nao podia ter.
        for nome_do_bloco, colunas_do_bloco in blocos.items():
            sorteio = gerador.integers(0, len(treino), size=TROCAS_POR_BLOCO)
            entradas_trocadas = pd.concat(
                [entrada_real] * TROCAS_POR_BLOCO, ignore_index=True
            )
            valores_sorteados = treino[colunas_do_bloco].to_numpy()[sorteio]
            entradas_trocadas[colunas_do_bloco] = valores_sorteados

            previsoes_trocadas = modelo.predict(entradas_trocadas)
            erro_medio_trocado = float(
                np.mean(np.abs(linha["real"] - previsoes_trocadas))
            )
            linha[f"erro_sem_{nome_do_bloco}"] = erro_medio_trocado

        linhas.append(linha)

    return pd.DataFrame(linhas)


def main() -> None:
    """Mede a importancia dos tres blocos nos 12 horizontes."""
    print("=" * 78)
    print("BLOCO 3 — importancia por bloco dentro do walk-forward")
    print("=" * 78, flush=True)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    tabela_bruta = harness.carregar_tabela_bruta()
    referencia = harness.Braco("A_referencia")
    tabela, colunas, _ = harness.montar_features_do_braco(tabela_bruta, referencia)
    blocos = separar_blocos(colunas, tabela)

    for nome, colunas_do_bloco in blocos.items():
        print(f"  {nome}: {len(colunas_do_bloco)} colunas", flush=True)

    gerador = np.random.default_rng(SEMENTE)
    resultados = []
    for horizonte in HORIZONTES:
        marca = time.perf_counter()
        resultado = medir_um_horizonte(tabela, colunas, blocos, horizonte, gerador)
        resultados.append(resultado)
        print(
            f"  h={horizonte:2d}  {len(resultado):3d} sem  "
            f"{time.perf_counter() - marca:5.1f}s",
            flush=True,
        )

    todos = pd.concat(resultados, ignore_index=True)
    todos["braco"] = "A_referencia"
    todos.to_csv(PASTA_DE_SAIDAS / "importancia_por_corte.csv", index=False)

    # A mesma trava dos outros blocos: se o erro sem troca nao reproduz o
    # painel, a importancia medida em cima dele nao vale.
    valido = harness.conferir_trava_de_validacao(todos, "A_referencia")
    if not valido:
        print("\n  BLOCO INVALIDO: a referencia nao reproduziu o painel.", flush=True)
        return

    avaliacao = todos[todos["data_alvo"] >= harness.INICIO_DA_AVALIACAO]
    print("\n  aumento do MAE quando o bloco e trocado, periodo de avaliacao")
    print(f"  {'h':>3} {'MAE real':>9} {'R2':>7} | {'Nucleo':>9} {'Clima':>9} {'Vetor':>9}")

    linhas_resumo = []
    for horizonte in HORIZONTES:
        celula = avaliacao[avaliacao["h"] == horizonte]
        mae_real = mean_absolute_error(celula["real"], celula["previsto"])
        r2_real = r2_score(celula["real"], celula["previsto"])
        linha = {"h": horizonte, "mae_real": mae_real, "r2_real": r2_real,
                 "semanas": len(celula)}
        texto = f"  {horizonte:3d} {mae_real:9.1f} {r2_real:7.3f} |"
        for nome in blocos:
            aumento = float(celula[f"erro_sem_{nome}"].mean() - mae_real)
            percentual = 100.0 * aumento / mae_real
            linha[f"aumento_mae_{nome}"] = aumento
            linha[f"aumento_pct_{nome}"] = percentual
            texto += f" {percentual:8.1f}%"
        print(texto)
        linhas_resumo.append(linha)

    pd.DataFrame(linhas_resumo).to_csv(
        PASTA_DE_SAIDAS / "importancia_por_horizonte.csv", index=False
    )


if __name__ == "__main__":
    main()
