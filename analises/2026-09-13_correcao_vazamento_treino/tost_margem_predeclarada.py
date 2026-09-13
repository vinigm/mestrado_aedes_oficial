"""

Recalcula o TOST de equivalencia clima x vetor com a margem que a
PRE_DECLARACAO de 29/08 fixou, e nao com a que o codigo usou.

O QUE ACONTECEU

  A pre-declaracao de 29/08 (secao "Margem de equivalencia", linha 123) diz:
  "TOST em +-5%, +-10% e +-15% do MAE da PERSISTENCIA". O codigo calculou a
  margem como fracao do MAE do SO_CLIMA. Sao bases diferentes, e em horizonte
  curto a diferenca e grande: em h=1, notificados, a margem usada foi 27,5
  casos contra os 6,8 que a pre-declaracao mandava - regua 4x mais larga.

  A margem pre-declarada e a que vale. Este script mede a diferenca.

  Nao roda modelo nenhum: le as previsoes ja salvas e refaz so a estatistica.

Uso:  python tost_margem_predeclarada.py [pasta_com_as_previsoes]
      (sem argumento, usa as previsoes de 29/08; com a rodada corrigida,
       aponte para a pasta desta analise)

"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PASTA_ANALISE = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA_ANALISE))

from rodada_2_corrigida import (
    HORIZONTES,
    MARGENS_TOST_FRACAO_MAE_CLIMA,
    calcular_mae,
    testar_tost_equivalencia,
)

VERSOES = {"puro": ("SO_CLIMA_PURO", "SO_VETOR_PURO"),
           "com_ar": ("SO_CLIMA_AR", "SO_VETOR_AR")}


def carregar(pasta: Path, alvo: str, nome: str, horizonte: int) -> pd.DataFrame:
    """Le um CSV de previsoes de uma combinacao (alvo, conjunto, horizonte)."""
    caminho = pasta / f"rodada_2_{alvo}_previsoes_{nome}_h{horizonte}.csv"
    return pd.read_csv(caminho, parse_dates=["data"])


def avaliar(pasta: Path, alvo: str) -> pd.DataFrame:
    """

    Refaz o TOST de cada combinacao com as duas bases de margem.

    Returns:
        Uma linha por (versao, horizonte) com os MAEs, as duas margens e o
        veredito de equivalencia sob cada uma.

    """
    linhas = []
    for versao, (nome_clima, nome_vetor) in VERSOES.items():
        for horizonte in HORIZONTES:
            clima = carregar(pasta, alvo, nome_clima, horizonte)
            vetor = carregar(pasta, alvo, nome_vetor, horizonte)
            persistencia = pd.read_csv(
                pasta / f"rodada_2_{alvo}_previsoes_persistencia_h{horizonte}.csv",
                parse_dates=["data"],
            )

            pareado = (
                clima.merge(vetor, on=["data", "h", "real"], suffixes=("_clima", "_vetor"))
                .merge(persistencia[["data", "h", "pred"]].rename(
                    columns={"pred": "pred_persistencia"}), on=["data", "h"])
            )
            erro_clima = (pareado["real"] - pareado["pred_clima"]).abs().to_numpy()
            erro_vetor = (pareado["real"] - pareado["pred_vetor"]).abs().to_numpy()
            erro_persistencia = (
                pareado["real"] - pareado["pred_persistencia"]
            ).abs().to_numpy()

            mae_clima = calcular_mae(erro_clima)
            mae_persistencia = calcular_mae(erro_persistencia)
            diferenca = erro_vetor - erro_clima

            linha = {"versao": versao, "h": horizonte, "n": len(pareado),
                     "MAE_clima": mae_clima, "MAE_vetor": calcular_mae(erro_vetor),
                     "MAE_persistencia": mae_persistencia,
                     "delta_MAE": calcular_mae(erro_vetor) - mae_clima}
            for fracao in MARGENS_TOST_FRACAO_MAE_CLIMA:
                rotulo = f"{int(fracao * 100)}pct"
                for base, mae_base in (("clima", mae_clima), ("persist", mae_persistencia)):
                    resultado = testar_tost_equivalencia(
                        diferenca, horizonte, fracao * mae_base
                    )
                    linha[f"margem_{rotulo}_{base}"] = fracao * mae_base
                    linha[f"equiv_{rotulo}_{base}"] = resultado.equivalente_a_5pct
            linhas.append(linha)
    return pd.DataFrame(linhas)


def main() -> None:
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        PASTA_ANALISE.parent / "2026-08-29_rodadas_notificados_zonas" / "saidas"
    )
    print(f"previsoes lidas de: {pasta}\n")
    pd.set_option("display.width", 220)

    for alvo in ("confirmados", "notificados"):
        try:
            resultado = avaliar(pasta, alvo)
        except FileNotFoundError as erro:
            print(f"=== {alvo.upper()}: sem arquivos ({erro.filename}) ===\n")
            continue

        colunas = ["versao", "h", "n", "MAE_clima", "MAE_vetor", "MAE_persistencia",
                   "delta_MAE", "margem_15pct_clima", "equiv_15pct_clima",
                   "margem_15pct_persist", "equiv_15pct_persist"]
        print(f"=== {alvo.upper()} ===")
        print(resultado[colunas].round(2).to_string(index=False))
        fecha_clima = int(resultado["equiv_15pct_clima"].sum())
        fecha_persist = int(resultado["equiv_15pct_persist"].sum())
        print(f"  a +-15%: fecha {fecha_clima} de 8 com a margem do CLIMA (o que o codigo fez) | "
              f"{fecha_persist} de 8 com a margem da PERSISTENCIA (o que foi pre-declarado)\n")


if __name__ == "__main__":
    main()
