"""

Teste decisivo: confirmados x notificados sobre EXATAMENTE as mesmas semanas.

Pre-declarado em PRE_DECLARACAO.md (30/08/2026) antes de rodar.

O que este script existe para resolver: em 29/08 os dois alvos deram respostas
opostas sobre o vetor ajudar a detectar surto. Mas os dois experimentos
diferiam em DUAS coisas ao mesmo tempo - o alvo e a janela. E a janela importa
porque de 2012 a 2018 a densidade do vetor usa denominador aproximado (a
Secretaria nao registrava se a vistoria acontecia). O experimento de
notificados tinha 45,8% da amostra assim; o de confirmados, quase nada.

Aqui os dois alvos rodam sobre a MESMA grade de semanas, com o vetor de
qualidade homogenea. Sobra uma unica diferenca: o alvo.

O motor e o do proprio pacote (importado, nao copiado), para que o resultado
seja comparavel com a producao linha a linha.

Uso:  python teste_decisivo_alvos.py

"""

import sys
import time
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import pandas as pd
from lightgbm import LGBMClassifier

from avaliacao import mcnemar
from avaliacao.correcao_multipla import corrigir_holm
from avaliacao.metricas import calcular_metricas_classificacao
from config import settings
from config.modelo import EspecificacaoModelo
from dominio import features, surto
from motor.walk_forward import executar_walk_forward_surto

PASTA_SAIDAS = PASTA_ANALISE / "saidas"

# Identicos ao experimento de producao - se algo aqui divergir, o resultado
# deixa de ser comparavel com o de 29/08.
HORIZONTES = (4, 8, 12)
PERCENTIS = (90, 95)
SEMANAS_CORTE_MATURIDADE = 12
ALFA = 0.05

PREFIXOS_CLIMA = (
    "temp_media_lag",
    "precip_total_mm_lag",
    "orvalho_media_lag",
    "umid_media_lag",
    "pressao_media_lag",
)
PREFIXOS_AUTORREGRESSIVO = ("casos_lag", "casos_mm")
PREFIXOS_VETOR = ("aedes_aegypti_por_armadilha_lag", "vetor_mm")

ESPECIFICACAO_MODELO = EspecificacaoModelo(
    nome="lightgbm",
    classe=LGBMClassifier,
    parametros={
        "n_estimators": 250,
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_child_samples": 5,
        "class_weight": "balanced",
        "verbose": -1,
        "n_jobs": 1,
    },
)


def carregar_com_os_dois_alvos() -> pd.DataFrame:
    """

    Abre a tabela_final com as duas series de casos lado a lado.

    Returns:
        A tabela semanal com 'casos_confirmados' (SINAN) e 'casos_notificados'
        (InfoDengue), casadas pela data de inicio da semana.

    """
    tabela = pd.read_csv(
        settings.CAMINHO_TABELA_FINAL, parse_dates=["data_inicio_semana_epidemi"]
    ).rename(columns={"data_inicio_semana_epidemi": "data"})

    infodengue = pd.read_csv(settings.CAMINHO_INFODENGUE, parse_dates=["data_iniSE"])
    notificados = infodengue[["data_iniSE", "casos"]].rename(
        columns={"data_iniSE": "data", "casos": "casos_notificados"}
    )

    tabela = tabela.merge(notificados, on="data", how="left")
    return tabela.sort_values("data").reset_index(drop=True)


def recortar_janela_comum(tabela: pd.DataFrame) -> pd.DataFrame:
    """

    Fica so com as semanas que atendem aos TRES criterios pre-declarados.

    Os criterios: denominador do vetor exato (nao aproximado), casos
    confirmados presentes e casos notificados presentes. Recortar antes de
    montar as features e proposital - assim os lags dos dois bracos enxergam
    exatamente o mesmo passado.

    """
    denominador_exato = tabela["denominador_aproximado"] == 0
    tem_confirmados = tabela["casos_confirmados"].notna()
    tem_notificados = tabela["casos_notificados"].notna()

    janela_comum = tabela.loc[denominador_exato & tem_confirmados & tem_notificados]
    return janela_comum.sort_values("data").reset_index(drop=True)


def preparar_braco(janela: pd.DataFrame, coluna_do_alvo: str) -> pd.DataFrame:
    """

    Monta um braco do teste: escolhe o alvo, aplica o corte de maturidade e
    cria as features temporais.

    A coluna do alvo escolhido vira 'casos' (o nome que o motor espera) e a
    outra serie e REMOVIDA - deixar as duas na tabela seria vazamento, porque
    uma e quase funcao da outra na mesma semana.

    """
    braco = janela.copy()
    braco["casos"] = braco[coluna_do_alvo]
    braco = braco.drop(columns=["casos_confirmados", "casos_notificados"])

    braco = surto.aplicar_corte_maturidade(braco, SEMANAS_CORTE_MATURIDADE)
    return features.construir_features_temporais(braco)


def rodar_braco(braco: pd.DataFrame, nome_alvo: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """

    Roda as 6 comparacoes de um alvo: so-clima contra clima+vetor.

    Returns:
        As metricas por modelo e a tabela de McNemar daquele braco.

    """
    colunas_clima = features.selecionar_colunas_por_prefixo(braco, PREFIXOS_CLIMA)
    colunas_autorregressivas = features.selecionar_colunas_por_prefixo(
        braco, PREFIXOS_AUTORREGRESSIVO
    )
    colunas_vetor = features.selecionar_colunas_por_prefixo(braco, PREFIXOS_VETOR)

    features_so_clima = colunas_autorregressivas + colunas_clima + ["sem_sin", "sem_cos"]
    features_clima_vetor = (
        colunas_autorregressivas + colunas_clima + colunas_vetor + ["sem_sin", "sem_cos"]
    )

    linhas_metricas = []
    linhas_mcnemar = []

    for percentil in PERCENTIS:
        for horizonte in HORIZONTES:
            resultado_clima = executar_walk_forward_surto(
                braco, features_so_clima, "fonte", horizonte, percentil, ESPECIFICACAO_MODELO,
            )
            resultado_vetor = executar_walk_forward_surto(
                braco, features_clima_vetor, "fonte", horizonte, percentil, ESPECIFICACAO_MODELO,
            )
            comparacao = resultado_clima.merge(
                resultado_vetor, on=["h", "data", "real"], suffixes=("_c", "_v")
            )

            for nome_modelo, sufixo in [("so-clima", "_c"), ("clima+vetor", "_v")]:
                metricas = calcular_metricas_classificacao(
                    comparacao["real"], comparacao[f"pred{sufixo}"], comparacao[f"prob{sufixo}"]
                )
                metricas.update(
                    {"alvo": nome_alvo, "pctl": percentil, "h": horizonte, "modelo": nome_modelo}
                )
                linhas_metricas.append(metricas)

            resultado_mcnemar = mcnemar.teste_mcnemar(
                (comparacao["pred_c"] == comparacao["real"]).to_numpy(),
                (comparacao["pred_v"] == comparacao["real"]).to_numpy(),
            )
            linhas_mcnemar.append(
                {
                    "alvo": nome_alvo,
                    "pctl": percentil,
                    "h": horizonte,
                    "n": len(comparacao),
                    "n_pos": int(comparacao["real"].sum()),
                    "clima_certo_vetor_errado": resultado_mcnemar.n_a_certo_b_errado,
                    "vetor_certo_clima_errado": resultado_mcnemar.n_a_errado_b_certo,
                    "discordantes": (
                        resultado_mcnemar.n_a_certo_b_errado + resultado_mcnemar.n_a_errado_b_certo
                    ),
                    "p_bruto": resultado_mcnemar.valor_p,
                }
            )
            print(
                f"  [{nome_alvo}] P{percentil} h={horizonte:2d}: n={len(comparacao):3d} "
                f"pos={int(comparacao['real'].sum()):3d} | "
                f"clima>vetor={resultado_mcnemar.n_a_certo_b_errado} "
                f"vetor>clima={resultado_mcnemar.n_a_errado_b_certo} "
                f"p={resultado_mcnemar.valor_p:.5f}",
                flush=True,
            )

    return pd.DataFrame(linhas_metricas), pd.DataFrame(linhas_mcnemar)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela = carregar_com_os_dois_alvos()
    janela = recortar_janela_comum(tabela)

    print(f"tabela completa: {len(tabela)} semanas", flush=True)
    print(f"JANELA COMUM (denominador exato + os dois alvos presentes): {len(janela)} semanas",
          flush=True)
    print(f"  de {janela['data'].min().date()} a {janela['data'].max().date()}", flush=True)
    print(f"  denominador aproximado na janela: "
          f"{int((janela['denominador_aproximado'] == 1).sum())} semanas (tem que ser 0)\n",
          flush=True)

    metricas_por_braco = []
    mcnemar_por_braco = []

    for coluna_do_alvo, nome_alvo in (
        ("casos_confirmados", "confirmados"),
        ("casos_notificados", "notificados"),
    ):
        print(f"--- braco: {nome_alvo} ---", flush=True)
        braco = preparar_braco(janela, coluna_do_alvo)
        metricas, resultado_mcnemar = rodar_braco(braco, nome_alvo)

        resultado_mcnemar["p_holm_6_dentro_do_braco"] = corrigir_holm(
            resultado_mcnemar["p_bruto"].to_numpy()
        )
        metricas_por_braco.append(metricas)
        mcnemar_por_braco.append(resultado_mcnemar)
        print("", flush=True)

    metricas_finais = pd.concat(metricas_por_braco, ignore_index=True)
    mcnemar_final = pd.concat(mcnemar_por_braco, ignore_index=True)

    # Holm sobre as 12: a pergunta e a mesma nos dois bracos, entao o conjunto
    # pre-declarado de comparacoes e o conjunto inteiro.
    mcnemar_final["p_holm_12_no_conjunto"] = corrigir_holm(
        mcnemar_final["p_bruto"].to_numpy()
    )
    mcnemar_final["significativo_holm_12"] = mcnemar_final["p_holm_12_no_conjunto"] < ALFA

    metricas_finais.to_csv(PASTA_SAIDAS / "teste_decisivo_metricas.csv", index=False)
    mcnemar_final.to_csv(PASTA_SAIDAS / "teste_decisivo_mcnemar.csv", index=False)

    print("=" * 100, flush=True)
    print("RESULTADO — os dois alvos sobre EXATAMENTE as mesmas semanas", flush=True)
    print("=" * 100, flush=True)
    colunas_exibidas = [
        "alvo", "pctl", "h", "n", "n_pos",
        "clima_certo_vetor_errado", "vetor_certo_clima_errado", "discordantes",
        "p_bruto", "p_holm_6_dentro_do_braco", "p_holm_12_no_conjunto", "significativo_holm_12",
    ]
    print(mcnemar_final[colunas_exibidas].round(5).to_string(index=False), flush=True)

    for nome_alvo, grupo in mcnemar_final.groupby("alvo"):
        vetor_favorecido = int(
            (grupo["vetor_certo_clima_errado"] > grupo["clima_certo_vetor_errado"]).sum()
        )
        sobrevivem = int(grupo["significativo_holm_12"].sum())
        print(f"\n{nome_alvo}: vetor favorecido em {vetor_favorecido} de 6 comparacoes | "
              f"{sobrevivem} sobrevivem a Holm(12)", flush=True)

    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
