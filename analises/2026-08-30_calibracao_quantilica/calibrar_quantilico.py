"""

Calibracao quantilica do melhor modelo do projeto (HistGradientBoosting).

Pre-declarado em PRE_DECLARACAO.md antes de rodar.

Contexto: o cenario 1 subestima sistematicamente os picos de dengue, e a
subestimacao cresce com o horizonte. O teste de 30/08 apontou a regressao
quantilica como remedio, mas rodou em LightGBM - que e so o 3o melhor
algoritmo. Aqui o remedio e testado no HistGradientBoosting, que e o melhor
(R2 medio 0,779 contra 0,749).

O alpha e escolhido usando SO o periodo de calibracao (ate 31/12/2023); o
periodo de avaliacao (2024 em diante) nunca participa da escolha. Sem isso, o
alpha seria escolhido em cima do resultado que ele mesmo deve provar.

Uso:  python calibrar_quantilico.py

"""

import sys
import time
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from acesso import fontes
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from dominio.features import construir_alvo_horizonte

PASTA_SAIDAS = PASTA_ANALISE / "saidas"

HORIZONTES = (1, 4, 8, 12)
PASSO_TESTE = 1
LIMITE_PICO = 100
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")

# Hiperparametros identicos aos do projeto (config/experimentos/cidade_regressao_modelos.py).
HIPERPARAMETROS_BASE = {
    "max_iter": 250,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 5,
    "random_state": 42,
}

ALPHAS_TESTADOS = (0.70, 0.80, 0.85, 0.90)

# Guarda declarada: o alpha escolhido nao pode piorar o MAE global em mais que
# isto contra o padrao, senao trocariamos vies por erro.
PIORA_MAXIMA_ACEITA_NO_MAE = 0.20


def montar_dados_e_colunas() -> tuple[pd.DataFrame, list[str]]:
    """Reproduz o preparo do cenario 1 e devolve a tabela e as colunas do modelo."""
    config = CIDADE_REGRESSAO

    tabela = fontes.carregar_tabela_final()
    tabela = surto.aplicar_corte_maturidade(tabela, config.semanas_corte_maturidade)
    tabela = features.construir_features_temporais(tabela)

    colunas_nucleo, colunas_clima, _ = selecao_features.separar_grupos_de_features(
        tabela, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )
    ranking_clima = selecao_features.selecionar_clima_por_ganho(
        tabela, colunas_nucleo, colunas_clima, config.coluna_alvo,
        config.horizontes_selecao_clima, config.modelo_selecao_clima,
        config.fracao_treino_selecao,
    )
    return tabela, colunas_nucleo + ranking_clima.head(6).index.tolist()


def rodar_walk_forward(
    tabela: pd.DataFrame,
    colunas_modelo: list[str],
    horizonte: int,
    alpha: float | None,
) -> pd.DataFrame:
    """

    Walk-forward do HistGradientBoosting num horizonte.

    Args:
        tabela: Tabela semanal com as features prontas.
        colunas_modelo: Colunas de entrada.
        horizonte: Quantas semanas a frente prever.
        alpha: Quantil a estimar. Se None, usa o objetivo padrao (media).

    Returns:
        Uma linha por semana testada, com a data da semana-alvo, o valor real e
        o previsto (clipado em zero).

    """
    config = CIDADE_REGRESSAO

    dados = construir_alvo_horizonte(tabela, config.coluna_alvo, horizonte)
    colunas_usadas = colunas_modelo + ["alvo_sin", "alvo_cos"]

    validos = (
        dados.dropna(subset=colunas_usadas + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    parametros = dict(HIPERPARAMETROS_BASE)
    if alpha is None:
        parametros["loss"] = "squared_error"
    else:
        parametros["loss"] = "quantile"
        parametros["quantile"] = alpha

    linhas = []
    for indice_corte in range(config.minimo_semanas_treino, len(validos), PASSO_TESTE):
        treino = validos.iloc[:indice_corte]
        teste = validos.iloc[indice_corte:indice_corte + 1]

        modelo = HistGradientBoostingRegressor(**parametros)
        modelo.fit(treino[colunas_usadas], treino["y_h"])
        previsao = float(modelo.predict(teste[colunas_usadas])[0])

        # A data da SEMANA-ALVO, e nao a da origem: e ela que decide se o ponto
        # cai na calibracao ou na avaliacao.
        data_alvo = teste["data"].to_numpy()[0] + np.timedelta64(horizonte * 7, "D")

        linhas.append({
            "h": horizonte,
            "data_origem": teste["data"].to_numpy()[0],
            "data_alvo": data_alvo,
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": max(previsao, 0.0),
        })

    return pd.DataFrame(linhas)


def resumir_por_periodo(previsoes: pd.DataFrame) -> pd.DataFrame:
    """

    Resume vies do pico, MAE e R2 separando calibracao de avaliacao.

    O corte usa a data da SEMANA-ALVO: uma previsao feita em 2023 para uma
    semana de 2024 pertence a avaliacao, porque o que se julga e o acerto sobre
    aquela semana.

    """
    trabalho = previsoes.copy()
    trabalho["periodo"] = np.where(
        pd.to_datetime(trabalho["data_alvo"]) <= FIM_DA_CALIBRACAO, "calibracao", "avaliacao"
    )
    trabalho["erro"] = trabalho["pred"] - trabalho["real"]

    linhas = []
    for (variante, horizonte, periodo), grupo in trabalho.groupby(["variante", "h", "periodo"]):
        reais = grupo["real"].to_numpy()
        soma_total = float(((reais - reais.mean()) ** 2).sum())
        soma_residual = float((grupo["erro"].to_numpy() ** 2).sum())

        picos = grupo.loc[grupo["real"] > LIMITE_PICO]

        linhas.append({
            "variante": variante,
            "h": horizonte,
            "periodo": periodo,
            "n": len(grupo),
            "n_picos": len(picos),
            "MAE_global": grupo["erro"].abs().mean(),
            "R2_global": 1 - soma_residual / soma_total if soma_total > 0 else np.nan,
            "pico_real_medio": picos["real"].mean() if len(picos) else np.nan,
            "pico_previsto_medio": picos["pred"].mean() if len(picos) else np.nan,
            "pico_VIES": picos["erro"].mean() if len(picos) else np.nan,
        })

    return pd.DataFrame(linhas)


def escolher_alpha(resumo: pd.DataFrame) -> str:
    """

    Escolhe a variante pelo criterio pre-declarado, usando SO a calibracao.

    Criterio: menor |vies no pico| medio entre os horizontes, com a guarda de
    nao piorar o MAE global em mais que PIORA_MAXIMA_ACEITA_NO_MAE contra o
    padrao.

    """
    calibracao = resumo.loc[resumo["periodo"] == "calibracao"]

    vies_por_variante = calibracao.groupby("variante")["pico_VIES"].apply(
        lambda valores: valores.abs().mean()
    )
    mae_por_variante = calibracao.groupby("variante")["MAE_global"].mean()
    mae_do_padrao = mae_por_variante["padrao"]

    candidatas = []
    for variante in vies_por_variante.sort_values().index:
        if variante == "padrao":
            continue
        piora_no_mae = (mae_por_variante[variante] - mae_do_padrao) / mae_do_padrao
        aprovada = piora_no_mae <= PIORA_MAXIMA_ACEITA_NO_MAE
        candidatas.append((variante, vies_por_variante[variante], piora_no_mae, aprovada))

    print("\n--- escolha do alpha (SO com a calibracao) ---", flush=True)
    for variante, vies, piora, aprovada in candidatas:
        marca = "OK" if aprovada else "REJEITADA (piorou MAE demais)"
        print(f"  {variante:16s} |vies pico| medio={vies:7.1f} | "
              f"variacao do MAE={piora:+.1%} | {marca}", flush=True)

    for variante, _, _, aprovada in candidatas:
        if aprovada:
            return variante
    return "padrao"


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela, colunas_modelo = montar_dados_e_colunas()
    print(f"colunas do modelo: {len(colunas_modelo)}", flush=True)

    variantes = [("padrao", None)]
    for alpha in ALPHAS_TESTADOS:
        variantes.append((f"quantil_{alpha:.2f}", alpha))

    todas = []
    for rotulo, alpha in variantes:
        print(f"\n--- {rotulo} ---", flush=True)
        for horizonte in HORIZONTES:
            inicio_horizonte = time.time()
            previsoes = rodar_walk_forward(tabela, colunas_modelo, horizonte, alpha)
            previsoes["variante"] = rotulo
            todas.append(previsoes)
            print(f"  h={horizonte:2d}: {len(previsoes)} semanas "
                  f"({(time.time() - inicio_horizonte) / 60:.1f} min)", flush=True)

    previsoes_finais = pd.concat(todas, ignore_index=True)
    resumo = resumir_por_periodo(previsoes_finais)

    previsoes_finais.to_csv(PASTA_SAIDAS / "calibracao_previsoes.csv", index=False)
    resumo.to_csv(PASTA_SAIDAS / "calibracao_resumo.csv", index=False)

    variante_escolhida = escolher_alpha(resumo)
    print(f"\nALPHA ESCOLHIDO (pelo criterio pre-declarado): {variante_escolhida}", flush=True)

    for periodo in ("calibracao", "avaliacao"):
        print("\n" + "=" * 100, flush=True)
        print(f"VIES NO PICO — periodo de {periodo.upper()}", flush=True)
        print("=" * 100, flush=True)
        recorte = resumo.loc[resumo["periodo"] == periodo]
        print(recorte.pivot_table(index="h", columns="variante", values="pico_VIES")
              .round(1).to_string(), flush=True)

    print("\n=== R2 global no periodo de AVALIACAO ===", flush=True)
    avaliacao = resumo.loc[resumo["periodo"] == "avaliacao"]
    print(avaliacao.pivot_table(index="h", columns="variante", values="R2_global")
          .round(3).to_string(), flush=True)

    print("\n=== MAE global no periodo de AVALIACAO ===", flush=True)
    print(avaliacao.pivot_table(index="h", columns="variante", values="MAE_global")
          .round(1).to_string(), flush=True)

    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
