"""Bloco 5 — os tres algoritmos com perda quantilica, com e sem vetor.

Duas perguntas no mesmo desenho:

  1. O HistGB continua sendo o melhor algoritmo DEPOIS da correcao do
     vazamento? Hoje essa escolha se apoia no grid de 30/08, que rodou
     contaminado. So tres algoritmos implementam perda quantilica, entao so
     eles podem rodar o cenario adotado: HistGB, GradientBoosting e LightGBM.

  2. O resultado de que o vetor nao melhora a previsao depende do algoritmo?
     Se os tres concordarem, o achado e robusto. Se um discordar, e isso que
     importa.

Hiperparametros identicos aos do grid de 30/08, quantil 0,85 nos tres.
Protocolo em PRE_DECLARACAO.md.
"""

import pathlib
import sys

from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA_DESTE_ARQUIVO.parent))

import harness  # noqa: E402
from config.modelo import EspecificacaoModelo  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

QUANTIL = 0.85

GRADIENT_BOOSTING_QUANTIL = EspecificacaoModelo(
    nome="gradient_boosting_quantil",
    classe=GradientBoostingRegressor,
    parametros={
        "n_estimators": 250,
        "learning_rate": 0.05,
        "max_depth": 3,
        "min_samples_leaf": 5,
        "random_state": 42,
        "loss": "quantile",
        "alpha": QUANTIL,
    },
)

LIGHTGBM_QUANTIL = EspecificacaoModelo(
    nome="lightgbm_quantil",
    classe=LGBMRegressor,
    parametros={
        "n_estimators": 300,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 20,
        "verbose": -1,
        "n_jobs": -1,
        "random_state": 42,
        "objective": "quantile",
        "alpha": QUANTIL,
    },
)

BRACOS = (
    harness.Braco("HistGB_M1", descricao="referencia: HistGB com vetor"),
    harness.Braco("HistGB_M0", sem_vetor=True, descricao="HistGB sem vetor"),
    harness.Braco(
        "GradBoost_M1", modelo=GRADIENT_BOOSTING_QUANTIL, descricao="GradBoost com vetor"
    ),
    harness.Braco(
        "GradBoost_M0",
        modelo=GRADIENT_BOOSTING_QUANTIL,
        sem_vetor=True,
        descricao="GradBoost sem vetor",
    ),
    harness.Braco("LightGBM_M1", modelo=LIGHTGBM_QUANTIL, descricao="LightGBM com vetor"),
    harness.Braco(
        "LightGBM_M0",
        modelo=LIGHTGBM_QUANTIL,
        sem_vetor=True,
        descricao="LightGBM sem vetor",
    ),
)

# Os pares de cada pergunta. A primeira compara algoritmos contra o HistGB;
# a segunda mede o vetor DENTRO de cada algoritmo, sempre M0 contra M1.
PARES_DE_ALGORITMO = (("HistGB_M1", "GradBoost_M1"), ("HistGB_M1", "LightGBM_M1"))
PARES_DE_VETOR = (
    ("HistGB_M1", "HistGB_M0"),
    ("GradBoost_M1", "GradBoost_M0"),
    ("LightGBM_M1", "LightGBM_M0"),
)
HORIZONTES = (1, 4, 8, 12)


def comparar_familia(previsoes, pares, titulo, arquivo_de_saida):
    """Compara uma familia de pares e aplica Holm sobre ela inteira.

    Cada pergunta e uma familia separada, com a sua propria correcao: sao
    hipoteses distintas, declaradas antes, e juntar as duas afrouxaria a
    exigencia sobre cada uma sem motivo.

    Args:
        previsoes: Todas as previsoes da bateria.
        pares: Tuplas (controle, variante).
        titulo: Nome da pergunta, para o relatorio.
        arquivo_de_saida: Onde gravar o CSV.
    """
    import pandas as pd

    avaliacao = previsoes[previsoes["data_alvo"] >= harness.INICIO_DA_AVALIACAO]

    comparacoes = []
    controles = {}
    for controle, variante in pares:
        for horizonte in HORIZONTES:
            comparacao = harness.comparar_pareado(
                avaliacao, controle, variante, horizonte
            )
            comparacoes.append(comparacao)
            controles[f"{variante}:{horizonte}"] = controle

    p_corrigidos = harness.corrigir_por_holm(comparacoes)

    print(f"\n  {titulo} — {len(comparacoes)} comparacoes, Holm")
    print(
        f"  {'controle':>13} {'variante':>13} {'h':>3} {'MAE ctrl':>9} "
        f"{'MAE var':>9} {'red':>8} {'p Holm':>8}"
    )
    linhas = []
    for comparacao in comparacoes:
        chave = f"{comparacao.braco}:{comparacao.horizonte}"
        p_holm = p_corrigidos[chave]
        marca = "*" if p_holm < harness.NIVEL_DE_SIGNIFICANCIA else " "
        print(
            f"  {controles[chave]:>13} {comparacao.braco:>13} {comparacao.horizonte:3d} "
            f"{comparacao.mae_referencia:9.1f} {comparacao.mae_variante:9.1f} "
            f"{comparacao.reducao_percentual():7.2f}% {p_holm:8.4f}{marca}"
        )
        linhas.append(
            {
                "controle": controles[chave],
                "variante": comparacao.braco,
                "h": comparacao.horizonte,
                "mae_controle": comparacao.mae_referencia,
                "mae_variante": comparacao.mae_variante,
                "reducao_percentual": comparacao.reducao_percentual(),
                "r2_controle": comparacao.r2_referencia,
                "r2_variante": comparacao.r2_variante,
                "p_bruto": comparacao.p_bruto,
                "p_holm": p_holm,
                "semanas_pareadas": comparacao.semanas_pareadas,
            }
        )

    pd.DataFrame(linhas).to_csv(PASTA_DE_SAIDAS / arquivo_de_saida, index=False)


def main() -> None:
    """Roda os seis bracos, valida a referencia e compara as duas familias."""
    print("=" * 78)
    print("BLOCO 5 — tres algoritmos com quantil 0,85, com e sem vetor")
    print("=" * 78, flush=True)

    previsoes = harness.executar_bateria(BRACOS, PASTA_DE_SAIDAS)
    valido = harness.conferir_trava_de_validacao(previsoes, "HistGB_M1")
    if not valido:
        print("\n  BLOCO INVALIDO: a referencia nao reproduziu o painel.", flush=True)
        return

    comparar_familia(
        previsoes,
        PARES_DE_ALGORITMO,
        "PERGUNTA 1: outro algoritmo bate o HistGB?",
        "comparacoes_algoritmo.csv",
    )
    comparar_familia(
        previsoes,
        PARES_DE_VETOR,
        "PERGUNTA 2: tirar o vetor muda o erro? (variante = SEM vetor)",
        "comparacoes_vetor.csv",
    )


if __name__ == "__main__":
    main()
