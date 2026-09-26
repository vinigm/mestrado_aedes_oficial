"""Certificacao adversarial da reversao de 26/09/2026 (2026 fora da tabela).

Reusa harness.py de analises/2026-09-23_bateria_noturna (SO LEITURA, nao
alterado) para rodar o braco de referencia (Braco() vazio = HistGB quantil
0,85) sobre a tabela_final.csv restaurada e conferir a trava de validacao
contra o PAINEL_PUBLICADO.

NAO altera nenhum arquivo do pipeline. So le e escreve dentro desta pasta.
"""

import pathlib
import sys

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DA_BATERIA_23_09 = PASTA_DESTE_ARQUIVO.parent.parent / "2026-09-23_bateria_noturna"
sys.path.insert(0, str(PASTA_DA_BATERIA_23_09))

import harness  # noqa: E402  motor da bateria noturna de 23/09, so leitura.

HORIZONTES = (1, 4, 8, 12)
NOME_DO_BRACO = "referencia"


def main() -> None:
    tabela_bruta = harness.carregar_tabela_bruta()
    braco_referencia = harness.Braco(nome=NOME_DO_BRACO)

    tabela, colunas_do_modelo, clima_escolhido = harness.montar_features_do_braco(
        tabela_bruta, braco_referencia
    )
    print(f"Colunas do modelo (n={len(colunas_do_modelo)}): {colunas_do_modelo}")
    print(f"Clima escolhido: {clima_escolhido}")
    print(f"INICIO_DA_AVALIACAO usado pela trava: {harness.INICIO_DA_AVALIACAO.date()}")

    previsoes_por_horizonte = []
    for horizonte in HORIZONTES:
        previsoes = harness.rodar_walk_forward(
            tabela, colunas_do_modelo, horizonte, braco_referencia.modelo_efetivo()
        )
        previsoes["braco"] = NOME_DO_BRACO
        previsoes_por_horizonte.append(previsoes)
        print(f"  h={horizonte:2d}: {len(previsoes)} previsoes")

    todas_previsoes = harness.pd.concat(previsoes_por_horizonte, ignore_index=True)
    tudo_bate = harness.conferir_trava_de_validacao(todas_previsoes, NOME_DO_BRACO)

    saida = PASTA_DESTE_ARQUIVO / "resultado_trava.txt"
    saida.write_text(f"tudo_bate={tudo_bate}\n", encoding="utf-8")
    print(f"\nVEREDITO FINAL DA TRAVA: {'VALIDO' if tudo_bate else 'INVALIDO'}")


if __name__ == "__main__":
    main()
