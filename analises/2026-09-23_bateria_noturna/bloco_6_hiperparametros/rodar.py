"""Bloco 6 — busca de hiperparametros do HistGB, escolha pela calibracao.

Os hiperparametros do cenario adotado nunca foram buscados. O grid de 30/08
variou algoritmo, funcao de perda e presenca do vetor; max_iter, learning
rate, tamanho da arvore e folha minima vieram fixos, herdados do cenario 1.

⚠️ O risco desta busca, e como o desenho o trava. Com cerca de 400 semanas,
varrer muitas configuracoes acha alguma "melhor" por sorte. Por isso:

  - a escolha usa SO o periodo de calibracao (data_alvo < 2024), o mesmo
    criterio do grid de 30/08;
  - so a vencedora vai para a avaliacao, num unico teste pareado contra a
    referencia. A avaliacao julga, nao escolhe.

Protocolo em PRE_DECLARACAO.md.
"""

import dataclasses
import datetime
import pathlib
import sys
import time

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA_DESTE_ARQUIVO.parent))

import harness  # noqa: E402
from config.modelo import EspecificacaoModelo  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"
ARQUIVO_DE_PREVISOES = PASTA_DE_SAIDAS / "previsoes_por_configuracao.csv"

# Os horizontes de decisao do projeto. Rodar os 12 triplicaria o custo sem
# mudar a escolha, que e feita pela media destes quatro.
HORIZONTES = (1, 4, 8, 12)
QUANTIL = 0.85

# Nenhuma configuracao nova comeca depois deste horario. O Vinicius sai as
# 06:00; o que tiver rodado ate aqui e analisado, e a pre-declaracao preve
# isso.
LIMITE_PARA_COMECAR = datetime.time(5, 0)

# learning_rate e max_iter andam juntos: taxa menor pede mais arvores.
RITMOS = ((0.05, 250), (0.03, 400), (0.10, 150))
TAMANHOS_DE_ARVORE = (15, 7, 31)
FOLHAS_MINIMAS = (5, 20)


@dataclasses.dataclass(frozen=True)
class Configuracao:
    """Uma combinacao de hiperparametros do HistGB.

    Attributes:
        nome: Identificador curto, legivel nas saidas.
        learning_rate: Passo de cada arvore.
        max_iter: Quantas arvores.
        max_leaf_nodes: Tamanho maximo de cada arvore.
        min_samples_leaf: Menor numero de semanas numa folha.
    """

    nome: str
    learning_rate: float
    max_iter: int
    max_leaf_nodes: int
    min_samples_leaf: int

    def especificacao(self) -> EspecificacaoModelo:
        """A ficha do modelo com estes hiperparametros e o quantil fixo."""
        return EspecificacaoModelo(
            nome=f"histgb_{self.nome}",
            classe=HistGradientBoostingRegressor,
            parametros={
                "max_iter": self.max_iter,
                "learning_rate": self.learning_rate,
                "max_leaf_nodes": self.max_leaf_nodes,
                "min_samples_leaf": self.min_samples_leaf,
                "random_state": 42,
                "loss": "quantile",
                "quantile": QUANTIL,
            },
        )


def montar_grade() -> list[Configuracao]:
    """Monta as 18 configuracoes, com a referencia em primeiro lugar.

    A referencia vai primeiro porque sem ela nao ha validacao nem comparacao:
    se a busca for interrompida pelo horario-limite, ela ja rodou.
    """
    grade = []
    for learning_rate, max_iter in RITMOS:
        for max_leaf_nodes in TAMANHOS_DE_ARVORE:
            for min_samples_leaf in FOLHAS_MINIMAS:
                nome = (
                    f"lr{learning_rate}_it{max_iter}_"
                    f"folhas{max_leaf_nodes}_min{min_samples_leaf}"
                )
                grade.append(
                    Configuracao(nome, learning_rate, max_iter, max_leaf_nodes,
                                 min_samples_leaf)
                )
    return grade


NOME_DA_REFERENCIA = "lr0.05_it250_folhas15_min5"


def rodar_configuracao(tabela, colunas, configuracao) -> pd.DataFrame:
    """Walk-forward dos quatro horizontes para uma configuracao."""
    especificacao = configuracao.especificacao()
    partes = []
    for horizonte in HORIZONTES:
        previsoes = harness.rodar_walk_forward(tabela, colunas, horizonte, especificacao)
        previsoes["braco"] = configuracao.nome
        partes.append(previsoes)

    return pd.concat(partes, ignore_index=True)


def mae_medio_na_calibracao(previsoes: pd.DataFrame, nome: str) -> float:
    """MAE medio dos quatro horizontes, so com data_alvo antes de 2024.

    E o criterio de escolha pre-declarado, o mesmo do grid de 30/08.
    """
    da_configuracao = previsoes[
        (previsoes["braco"] == nome)
        & (previsoes["data_alvo"] < harness.INICIO_DA_AVALIACAO)
    ]
    maes = []
    for horizonte in HORIZONTES:
        celula = da_configuracao[da_configuracao["h"] == horizonte]
        maes.append(mean_absolute_error(celula["real"], celula["previsto"]))

    return sum(maes) / len(maes)


def main() -> None:
    """Roda a grade, escolhe pela calibracao e testa a vencedora uma vez."""
    print("=" * 78)
    print("BLOCO 6 — hiperparametros do HistGB, escolha pela calibracao")
    print("=" * 78, flush=True)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    tabela_bruta = harness.carregar_tabela_bruta()
    tabela, colunas, _ = harness.montar_features_do_braco(
        tabela_bruta, harness.Braco("referencia")
    )

    grade = montar_grade()
    assert grade[0].nome == NOME_DA_REFERENCIA, "a referencia tem de rodar primeiro"

    todas = []
    interrompido = False
    for posicao, configuracao in enumerate(grade, start=1):
        agora = datetime.datetime.now().time()
        if posicao > 1 and agora >= LIMITE_PARA_COMECAR:
            print(f"\n  horario-limite atingido: {len(todas)} de {len(grade)} rodaram.")
            interrompido = True
            break

        marca = time.perf_counter()
        previsoes = rodar_configuracao(tabela, colunas, configuracao)
        todas.append(previsoes)
        # Grava a cada configuracao: se algo cair no meio, o que rodou fica.
        pd.concat(todas, ignore_index=True).to_csv(ARQUIVO_DE_PREVISOES, index=False)
        print(
            f"  [{posicao:2d}/{len(grade)}] {configuracao.nome:32s} "
            f"{(time.perf_counter() - marca) / 60:4.1f} min",
            flush=True,
        )

    previsoes = pd.concat(todas, ignore_index=True)

    valido = harness.conferir_trava_de_validacao(previsoes, NOME_DA_REFERENCIA)
    if not valido:
        print("\n  BLOCO INVALIDO: a referencia nao reproduziu o painel.", flush=True)
        return

    ranking = []
    for nome in previsoes["braco"].unique():
        ranking.append(
            {"configuracao": nome, "mae_calibracao": mae_medio_na_calibracao(previsoes, nome)}
        )
    ranking = pd.DataFrame(ranking).sort_values("mae_calibracao").reset_index(drop=True)
    ranking.to_csv(PASTA_DE_SAIDAS / "ranking_calibracao.csv", index=False)

    print("\n  ranking pela calibracao (criterio de escolha):")
    for posicao, linha in ranking.iterrows():
        marca = "  <= referencia" if linha["configuracao"] == NOME_DA_REFERENCIA else ""
        print(f"    {posicao + 1:2d}. {linha['configuracao']:32s} "
              f"MAE {linha['mae_calibracao']:7.2f}{marca}")

    vencedora = ranking.iloc[0]["configuracao"]
    print(f"\n  vencedora: {vencedora}"
          f"{'  (grade interrompida pelo horario)' if interrompido else ''}")

    if vencedora == NOME_DA_REFERENCIA:
        print("  A referencia venceu a propria busca. Nada a testar na avaliacao.")
        return

    print("\n  TESTE UNICO na avaliacao: vencedora contra referencia")
    harness.relatar_comparacoes(
        previsoes[previsoes["braco"].isin([NOME_DA_REFERENCIA, vencedora])],
        braco_referencia=NOME_DA_REFERENCIA,
        horizontes_da_familia=HORIZONTES,
        horizontes_de_decisao=(8, 12),
        pasta_de_saidas=PASTA_DE_SAIDAS,
    )


if __name__ == "__main__":
    main()
