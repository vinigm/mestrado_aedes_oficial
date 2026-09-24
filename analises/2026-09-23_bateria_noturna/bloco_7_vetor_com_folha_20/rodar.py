"""Bloco 7 — o vetor no HistGB com folha minima 20.

Teste de mecanismo, exploratorio. Protocolo em PRE_DECLARACAO.md.

O bloco 5 achou o vetor ajudando o LightGBM em 3 meses e nao o HistGB. O
bloco 6 sugeriu que o que separa os dois e a folha minima: 20 no LightGBM,
5 no HistGB. Se for isso, o vetor deve ajudar o HistGB com folha minima 20.
"""

import pathlib
import sys

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA_DESTE_ARQUIVO.parent))

import harness  # noqa: E402
from config.modelo import EspecificacaoModelo  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"
ARQUIVO_DO_BLOCO_6 = (
    PASTA_DESTE_ARQUIVO.parent / "bloco_6_hiperparametros" / "saidas"
    / "previsoes_por_configuracao.csv"
)
NOME_NO_BLOCO_6 = "lr0.05_it250_folhas15_min20"

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

BRACOS = (
    harness.Braco("referencia", descricao="cenario adotado, folha minima 5"),
    harness.Braco("HistGB_folha20_M1", modelo=HISTGB_FOLHA_20, descricao="folha 20, com vetor"),
    harness.Braco(
        "HistGB_folha20_M0",
        modelo=HISTGB_FOLHA_20,
        sem_vetor=True,
        descricao="folha 20, sem vetor",
    ),
)


def conferir_contra_o_bloco_6(previsoes: pd.DataFrame) -> bool:
    """O HistGB com folha 20 e deterministico: tem de repetir o bloco 6."""
    anterior = pd.read_csv(ARQUIVO_DO_BLOCO_6, parse_dates=["data_alvo"])
    anterior = anterior[anterior["braco"] == NOME_NO_BLOCO_6]
    atual = previsoes[previsoes["braco"] == "HistGB_folha20_M1"]

    print("\n  TRAVA 2 — folha 20 com vetor contra o bloco 6")
    tudo_bate = True
    for horizonte in (1, 4, 8, 12):
        a = anterior[anterior["h"] == horizonte]
        b = atual[atual["h"] == horizonte]
        mae_a = mean_absolute_error(a["real"], a["previsto"])
        mae_b = mean_absolute_error(b["real"], b["previsto"])
        bate = abs(mae_a - mae_b) < 0.01 and len(a) == len(b)
        tudo_bate = tudo_bate and bate
        print(f"    h={horizonte:2d}  bloco 6 {mae_a:8.2f}  agora {mae_b:8.2f}  {'ok' if bate else '<<< DIVERGE'}")

    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}")
    return tudo_bate


def main() -> None:
    """Roda os tres bracos, confere as duas travas e compara M0 com M1."""
    print("=" * 78)
    print("BLOCO 7 — o vetor no HistGB com folha minima 20")
    print("=" * 78, flush=True)

    previsoes = harness.executar_bateria(BRACOS, PASTA_DE_SAIDAS)

    valido = harness.conferir_trava_de_validacao(previsoes, "referencia")
    valido = conferir_contra_o_bloco_6(previsoes) and valido
    if not valido:
        print("\n  BLOCO INVALIDO.", flush=True)
        return

    so_folha_20 = previsoes[previsoes["braco"].isin(["HistGB_folha20_M1", "HistGB_folha20_M0"])]
    harness.relatar_comparacoes(
        so_folha_20,
        braco_referencia="HistGB_folha20_M1",
        horizontes_da_familia=(1, 4, 8, 12),
        horizontes_de_decisao=(12,),
        pasta_de_saidas=PASTA_DE_SAIDAS,
    )


if __name__ == "__main__":
    main()
