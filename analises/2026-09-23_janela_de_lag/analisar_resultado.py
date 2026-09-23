"""Lê as previsões dos três braços contra o critério pré-declarado.

O critério está fixado em PRE_DECLARACAO.md §5 e não pode ser alterado aqui:
uma variante só entra na referência se reduzir o MAE em h=8 E h=12, com p de
Holm abaixo de 0,05 nos dois.

A comparação é pareada por `data_alvo`, conforme a regra do projeto. Comparar
médias de conjuntos diferentes de semanas não vale, porque a diferença
misturaria o efeito da variante com o efeito de avaliar semanas diferentes.

Uso:
    python3 analisar_resultado.py
"""

import dataclasses
import pathlib

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, r2_score

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")
BRACO_DE_REFERENCIA = "A_referencia"

# Os horizontes que entram na família de correção múltipla.
HORIZONTES_DA_FAMILIA = (1, 4, 8, 12)

# Os horizontes em que o critério pré-declarado decide.
HORIZONTES_DE_DECISAO = (8, 12)

NIVEL_DE_SIGNIFICANCIA = 0.05


@dataclasses.dataclass(frozen=True)
class ComparacaoPareada:
    """O resultado de comparar uma variante com a referência num horizonte.

    Attributes:
        braco: Nome da variante.
        horizonte: Quantas semanas à frente.
        mae_referencia: MAE da referência nas semanas pareadas.
        mae_variante: MAE da variante nas mesmas semanas.
        r2_variante: R² da variante, descritivo.
        semanas_pareadas: Quantas semanas entraram na comparação.
        p_bruto: p do Wilcoxon pareado, antes da correção.
    """

    braco: str
    horizonte: int
    mae_referencia: float
    mae_variante: float
    r2_variante: float
    semanas_pareadas: int
    p_bruto: float

    def reducao_percentual(self) -> float:
        """Quanto a variante reduziu o MAE. Negativo significa que piorou."""
        return 100.0 * (self.mae_referencia - self.mae_variante) / self.mae_referencia


def comparar_um_horizonte(
    previsoes: pd.DataFrame, braco: str, horizonte: int
) -> ComparacaoPareada:
    """Compara uma variante com a referência, semana a semana.

    O pareamento é feito por `data_alvo`: só entram as semanas que os dois
    braços previram. Braços com janela de lag maior perdem semanas no início
    da série, então os conjuntos não são idênticos e a interseção é o que
    torna a comparação honesta.

    Args:
        previsoes: Todas as previsões, de todos os braços.
        braco: A variante a comparar.
        horizonte: O horizonte a comparar.

    Returns:
        O resultado da comparação naquele horizonte.

    Raises:
        ValueError: Se não sobrar nenhuma semana em comum.
    """
    do_horizonte = previsoes[previsoes["h"] == horizonte]

    da_referencia = do_horizonte[do_horizonte["braco"] == BRACO_DE_REFERENCIA]
    da_variante = do_horizonte[do_horizonte["braco"] == braco]

    pareado = da_referencia.merge(
        da_variante, on="data_alvo", suffixes=("_ref", "_var")
    )

    if pareado.empty:
        raise ValueError(
            f"Nenhuma semana em comum entre {BRACO_DE_REFERENCIA} e {braco} "
            f"em h={horizonte}."
        )

    erro_da_referencia = np.abs(pareado["real_ref"] - pareado["previsto_ref"])
    erro_da_variante = np.abs(pareado["real_var"] - pareado["previsto_var"])

    # O Wilcoxon exige que haja diferença; se os dois braços derem exatamente
    # a mesma previsão em toda semana, não há o que testar.
    if np.allclose(erro_da_referencia, erro_da_variante):
        p_bruto = 1.0
    else:
        _, p_bruto = stats.wilcoxon(erro_da_referencia, erro_da_variante)

    return ComparacaoPareada(
        braco=braco,
        horizonte=horizonte,
        mae_referencia=mean_absolute_error(
            pareado["real_ref"], pareado["previsto_ref"]
        ),
        mae_variante=mean_absolute_error(
            pareado["real_var"], pareado["previsto_var"]
        ),
        r2_variante=r2_score(pareado["real_var"], pareado["previsto_var"]),
        semanas_pareadas=len(pareado),
        p_bruto=float(p_bruto),
    )


def corrigir_por_holm(comparacoes: list[ComparacaoPareada]) -> dict[str, float]:
    """Aplica a correção de Holm sobre a família inteira de comparações.

    Holm ordena os p do menor para o maior e exige que o i-ésimo sobreviva a
    um limiar que vai afrouxando. É mais poderoso que Bonferroni e continua
    controlando a chance de um falso positivo em qualquer lugar da família.

    Args:
        comparacoes: Todas as comparações da família, sem exceção. Deixar uma
            de fora inflaria a significância das que ficaram.

    Returns:
        O p corrigido de cada comparação, indexado por "braco:horizonte".
    """
    ordenadas = sorted(comparacoes, key=lambda item: item.p_bruto)
    quantidade = len(ordenadas)

    p_corrigidos: dict[str, float] = {}
    maior_p_ate_agora = 0.0

    for posicao, comparacao in enumerate(ordenadas):
        multiplicador = quantidade - posicao
        p_ajustado = min(1.0, comparacao.p_bruto * multiplicador)
        # Holm é monótono: um p corrigido nunca pode ficar abaixo do anterior.
        maior_p_ate_agora = max(maior_p_ate_agora, p_ajustado)
        chave = f"{comparacao.braco}:{comparacao.horizonte}"
        p_corrigidos[chave] = maior_p_ate_agora

    return p_corrigidos


def main() -> None:
    """Imprime a tabela de resultados e o veredito pelo critério declarado."""
    previsoes = pd.read_csv(
        PASTA_DE_SAIDAS / "previsoes_por_braco.csv", parse_dates=["data_alvo"]
    )
    avaliacao = previsoes[previsoes["data_alvo"] >= INICIO_DA_AVALIACAO]

    variantes = [
        nome for nome in avaliacao["braco"].unique() if nome != BRACO_DE_REFERENCIA
    ]

    comparacoes = []
    for braco in sorted(variantes):
        for horizonte in HORIZONTES_DA_FAMILIA:
            comparacoes.append(comparar_um_horizonte(avaliacao, braco, horizonte))

    p_corrigidos = corrigir_por_holm(comparacoes)

    print(f"Família de correção: {len(comparacoes)} comparações, método de Holm")
    print(f"Período de avaliação: data_alvo >= {INICIO_DA_AVALIACAO.date()}\n")
    print(
        f"{'braço':>15} {'h':>3} {'MAE ref':>9} {'MAE var':>9} "
        f"{'redução':>9} {'R² var':>8} {'p bruto':>9} {'p Holm':>8} {'n':>4}"
    )
    print("-" * 88)

    for comparacao in comparacoes:
        chave = f"{comparacao.braco}:{comparacao.horizonte}"
        p_holm = p_corrigidos[chave]
        sobrevive = "*" if p_holm < NIVEL_DE_SIGNIFICANCIA else " "
        print(
            f"{comparacao.braco:>15} {comparacao.horizonte:3d} "
            f"{comparacao.mae_referencia:9.1f} {comparacao.mae_variante:9.1f} "
            f"{comparacao.reducao_percentual():8.2f}% {comparacao.r2_variante:8.3f} "
            f"{comparacao.p_bruto:9.4f} {p_holm:8.4f}{sobrevive} "
            f"{comparacao.semanas_pareadas:4d}"
        )

    print("\nVEREDITO pelo critério pré-declarado (§5):")
    for braco in sorted(variantes):
        aprovacoes = []
        for horizonte in HORIZONTES_DE_DECISAO:
            do_braco = [
                item
                for item in comparacoes
                if item.braco == braco and item.horizonte == horizonte
            ]
            comparacao = do_braco[0]
            p_holm = p_corrigidos[f"{braco}:{horizonte}"]
            reduziu = comparacao.mae_variante < comparacao.mae_referencia
            significativo = p_holm < NIVEL_DE_SIGNIFICANCIA
            aprovacoes.append(reduziu and significativo)

        if all(aprovacoes):
            veredito = "ENTRA na referência"
        else:
            veredito = "NÃO entra"
        print(f"  {braco:>15}: {veredito}")


if __name__ == "__main__":
    main()
