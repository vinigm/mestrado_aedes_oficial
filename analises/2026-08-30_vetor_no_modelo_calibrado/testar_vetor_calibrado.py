"""

O vetor acrescenta informacao quando o modelo esta bem calibrado?

Pre-declarado em PRE_DECLARACAO.md antes de rodar.

Todos os testes anteriores do valor preditivo das armadilhas rodaram com a
perda padrao (erro quadratico), que hoje sabemos estar sistematicamente
enviesada para baixo nos picos. Se o modelo estava mal calibrado, aqueles
testes podem ter medido a limitacao do modelo, e nao a informacao do vetor.

Aqui o vetor e testado no HistGradientBoosting com quantil 0,85 - a
configuracao validada em 30/08 fora do periodo de calibracao - contra a mesma
configuracao sem o vetor.

Uso:  python testar_vetor_calibrado.py

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
from avaliacao import diebold_mariano
from avaliacao.correcao_multipla import corrigir_holm
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from dominio.features import construir_alvo_horizonte

PASTA_SAIDAS = PASTA_ANALISE / "saidas"

HORIZONTES = (1, 4, 8, 12)
PASSO_TESTE = 1
LIMITE_PICO = 100
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")
ALFA = 0.05

HIPERPARAMETROS_BASE = {
    "max_iter": 250,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 5,
    "random_state": 42,
}

# (rotulo, alpha do quantil ou None para a perda padrao)
PERDAS = (("padrao", None), ("quantil_0.85", 0.85))


def montar_dados_e_conjuntos() -> tuple[pd.DataFrame, list[str], list[str]]:
    """

    Reproduz o preparo do cenario 1 e devolve a tabela e os DOIS conjuntos.

    Returns:
        A tabela pronta, o conjunto M0 (nucleo + clima, sem vetor) e o conjunto
        M1 (M0 + as colunas do vetor).

    """
    config = CIDADE_REGRESSAO

    tabela = fontes.carregar_tabela_final()
    tabela = surto.aplicar_corte_maturidade(tabela, config.semanas_corte_maturidade)
    tabela = features.construir_features_temporais(tabela)

    colunas_nucleo, colunas_clima, colunas_vetor = selecao_features.separar_grupos_de_features(
        tabela, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )
    ranking_clima = selecao_features.selecionar_clima_por_ganho(
        tabela, colunas_nucleo, colunas_clima, config.coluna_alvo,
        config.horizontes_selecao_clima, config.modelo_selecao_clima,
        config.fracao_treino_selecao,
    )
    clima_enxuto = ranking_clima.head(6).index.tolist()

    conjunto_sem_vetor = colunas_nucleo + clima_enxuto
    conjunto_com_vetor = colunas_nucleo + clima_enxuto + colunas_vetor
    return tabela, conjunto_sem_vetor, conjunto_com_vetor


def rodar_walk_forward(
    tabela: pd.DataFrame,
    colunas_modelo: list[str],
    horizonte: int,
    alpha: float | None,
) -> pd.DataFrame:
    """Walk-forward do HistGradientBoosting, gravando previsao por semana."""
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

        data_alvo = teste["data"].to_numpy()[0] + np.timedelta64(horizonte * 7, "D")
        linhas.append({
            "h": horizonte,
            "data_alvo": data_alvo,
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": max(previsao, 0.0),
        })

    return pd.DataFrame(linhas)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela, sem_vetor, com_vetor = montar_dados_e_conjuntos()
    colunas_do_vetor = [coluna for coluna in com_vetor if coluna not in sem_vetor]
    print(f"M0 (sem vetor): {len(sem_vetor)} colunas", flush=True)
    print(f"M1 (com vetor): {len(com_vetor)} colunas", flush=True)
    print(f"colunas do vetor acrescentadas: {colunas_do_vetor}\n", flush=True)

    conjuntos = (("M0_sem_vetor", sem_vetor), ("M1_com_vetor", com_vetor))

    todas = []
    for rotulo_perda, alpha in PERDAS:
        for rotulo_conjunto, colunas in conjuntos:
            print(f"--- {rotulo_perda} | {rotulo_conjunto} ---", flush=True)
            for horizonte in HORIZONTES:
                inicio = time.time()
                previsoes = rodar_walk_forward(tabela, colunas, horizonte, alpha)
                previsoes["perda"] = rotulo_perda
                previsoes["conjunto"] = rotulo_conjunto
                todas.append(previsoes)
                print(f"  h={horizonte:2d}: {len(previsoes)} semanas "
                      f"({(time.time() - inicio) / 60:.1f} min)", flush=True)

    previsoes_finais = pd.concat(todas, ignore_index=True)
    previsoes_finais["periodo"] = np.where(
        pd.to_datetime(previsoes_finais["data_alvo"]) <= FIM_DA_CALIBRACAO,
        "calibracao", "avaliacao",
    )
    previsoes_finais.to_csv(PASTA_SAIDAS / "vetor_previsoes.csv", index=False)

    # --- Comparacao pareada M0 x M1, por perda e horizonte ---
    linhas_comparacao = []
    for rotulo_perda, _ in PERDAS:
        for horizonte in HORIZONTES:
            recorte = previsoes_finais.loc[
                (previsoes_finais["perda"] == rotulo_perda)
                & (previsoes_finais["h"] == horizonte)
                & (previsoes_finais["periodo"] == "avaliacao")
            ]
            sem = recorte.loc[recorte["conjunto"] == "M0_sem_vetor"].sort_values("data_alvo")
            com = recorte.loc[recorte["conjunto"] == "M1_com_vetor"].sort_values("data_alvo")

            pareado = sem.merge(com, on=["h", "data_alvo", "real"], suffixes=("_m0", "_m1"))

            erro_m0 = (pareado["pred_m0"] - pareado["real"]).to_numpy()
            erro_m1 = (pareado["pred_m1"] - pareado["real"]).to_numpy()

            mae_m0 = float(np.abs(erro_m0).mean())
            mae_m1 = float(np.abs(erro_m1).mean())

            resultado_dm = diebold_mariano.teste_diebold_mariano(
                erro_m0, erro_m1, horizonte, "absoluto"
            )

            picos = pareado.loc[pareado["real"] > LIMITE_PICO]

            linhas_comparacao.append({
                "perda": rotulo_perda,
                "h": horizonte,
                "n": len(pareado),
                "MAE_sem_vetor": mae_m0,
                "MAE_com_vetor": mae_m1,
                "ganho_MAE": mae_m0 - mae_m1,
                "vies_pico_sem_vetor": (picos["pred_m0"] - picos["real"]).mean() if len(picos) else np.nan,
                "vies_pico_com_vetor": (picos["pred_m1"] - picos["real"]).mean() if len(picos) else np.nan,
                "DM_estatistica": resultado_dm.estatistica,
                "DM_p_bruto": resultado_dm.valor_p,
            })

    comparacao = pd.DataFrame(linhas_comparacao)
    comparacao["DM_p_holm_8"] = corrigir_holm(comparacao["DM_p_bruto"].to_numpy())
    comparacao["significativo"] = comparacao["DM_p_holm_8"] < ALFA
    comparacao.to_csv(PASTA_SAIDAS / "vetor_comparacao.csv", index=False)

    print("\n" + "=" * 118, flush=True)
    print("O VETOR AJUDA? — periodo de AVALIACAO (2024+), M0 sem vetor x M1 com vetor", flush=True)
    print("=" * 118, flush=True)
    print(comparacao.round(4).to_string(index=False), flush=True)

    venceu = int((comparacao["ganho_MAE"] > 0).sum())
    sobreviveu = int(comparacao["significativo"].sum())
    print(f"\nM1 (com vetor) tem MAE menor em {venceu} de {len(comparacao)} comparacoes.", flush=True)
    print(f"Sobrevivem a Holm (8 comparacoes, alfa={ALFA}): {sobreviveu}", flush=True)

    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
