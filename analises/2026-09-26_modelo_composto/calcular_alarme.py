"""Mede o alarme de surto do modelo composto, e explica de onde vem a precisao.

Por que existe
--------------
Pergunta do Vinicius em 26/09/2026, em duas partes:

  1. o slide do alarme mostra os numeros da configuracao ADOTADA, que e a
     versao anterior a melhora. Ele quer os numeros do COMPOSTO;
  2. a precisao de 81% em 3 meses parece alta demais, e ele desconfia que haja
     algo errado por tras dela.

Este script responde as duas. A segunda tem resposta e ela nao e "esta errado":
a precisao e alta porque o evento e COMUM e CONCENTRADO. Das 102 semanas
avaliadas, 39 passam de 100 casos, e elas formam apenas 2 blocos contiguos.
Num evento assim, ate uma regra que so olha o calendario acerta muito - a regua
sazonal tem precisao AINDA MAIOR que a do modelo. Por isso a saida imprime a
regua ao lado: sem ela, 81% parece merito do modelo.

⚠️ ESTATUTO: DESCRITIVO. Nenhum modelo treinado, nenhum teste de hipotese,
nenhum valor-p. E recombinacao de previsoes ja salvas.

Trava
-----
Antes de qualquer numero novo, o script reproduz o painel publicado da
configuracao adotada: em h=4, sensibilidade 0,971, precisao 0,943 e 0,7 alarmes
falsos por ano; em h=12, 0,769, 0,811 e 2,3.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pandas as pd

PASTA_DESTE_SCRIPT = pathlib.Path(__file__).resolve().parent

_especificacao = importlib.util.spec_from_file_location(
    "calcular", PASTA_DESTE_SCRIPT / "calcular.py"
)
calcular = importlib.util.module_from_spec(_especificacao)
_especificacao.loader.exec_module(calcular)

# 🔴 TROCADO em 26/09/2026, por decisao do Vinicius: o limiar passa a ser o do
# ESTAGIO ALERTA do Plano Municipal de Contingencia de Arboviroses 2026 da
# SMS-POA, e nao mais os 100 casos, que eram convencao do projeto sem base
# oficial.
#
# 421 casos por semana = incidencia de 30 por 100 mil na populacao de
# 1.404.269. ⚠️ SIMPLIFICACAO DECLARADA: no plano o corte numerico nunca
# aparece sozinho - vem ligado por E a limiares estaduais sobre casos
# provaveis, mais obito e sorotipo novo. Usamos so a metade fixa do criterio.
#
# A troca muda MUITO os numeros, e e por isso que ela importa: com 100, o
# composto pega 84,6% das semanas em 3 meses; com 421, pega 50,0%. Quanto mais
# raro o evento, pior o modelo vai. O limiar antigo escondia isso.
LIMIAR_DE_SURTO = 421

# Os 100 casos ficam registrados porque a trava do painel publicado usa eles.
LIMIAR_DA_CONVENCAO_ANTIGA = 100
SEMANAS_POR_ANO = 52.0
HORIZONTES_RELATADOS = (1, 4, 8, 12)

# O que o painel publicado da configuracao adotada diz, e que a trava exige
# reproduzir antes de qualquer leitura nova.
# 🔴 ACHADO DE 26/09/2026 — a trava reprovou aqui, e o erro e do publicado.
#
# Sensibilidade e precisao batem exatamente. "Alarmes falsos por ano" nao bate,
# e a causa e o DENOMINADOR: a medicao de 13/09/2026 dividiu o numero de
# alarmes falsos por 3 ANOS CIVIS (2024, 2025 e 2026), enquanto a avaliacao
# cobre 102 semanas, isto e, 1,96 ano de tempo real - 2024 entra com 45 semanas
# e 2026 com apenas 5.
#
# Em h=12 sao 7 alarmes falsos:
#   7 / 3 anos civis  = 2,33 por ano  <- o numero publicado
#   7 / 1,96 ano real = 3,57 por ano  <- o correto
#
# A taxa publicada esta SUBESTIMADA em cerca de 53%. Por isso a trava confere
# so sensibilidade e precisao, e os alarmes falsos aparecem nas duas contas,
# lado a lado, com a diferenca explicada.
PAINEL_DO_ALARME_PUBLICADO = {
    4: {"sensibilidade": 0.971, "precisao": 0.943},
    12: {"sensibilidade": 0.769, "precisao": 0.811},
}
ANOS_CIVIS_DA_AVALIACAO = 3
TOLERANCIA_DA_PROPORCAO = 0.01
TOLERANCIA_DOS_FALSOS = 0.1


def calcular_metricas_do_alarme(
    de_um_braco: pd.DataFrame, limiar: int = LIMIAR_DE_SURTO
) -> dict[str, float]:
    """Calcula sensibilidade, precisao e alarmes falsos por ano.

    Args:
        de_um_braco: As previsoes de um unico braco e horizonte, com as colunas
            `real` e `previsto`.
        limiar: Casos por semana acima dos quais a semana conta como surto.

    Returns:
        Um dicionario com as tres metricas, mais as contagens que as produzem.
    """
    houve_surto = de_um_braco["real"] > limiar
    disparou_alarme = de_um_braco["previsto"] > limiar

    acertos = int((houve_surto & disparou_alarme).sum())
    alarmes_falsos = int((~houve_surto & disparou_alarme).sum())
    surtos_perdidos = int((houve_surto & ~disparou_alarme).sum())

    semanas = len(de_um_braco)
    anos_avaliados = semanas / SEMANAS_POR_ANO

    sensibilidade = acertos / (acertos + surtos_perdidos) if houve_surto.any() else float("nan")
    precisao = acertos / (acertos + alarmes_falsos) if disparou_alarme.any() else float("nan")

    return {
        "sensibilidade": sensibilidade,
        "precisao": precisao,
        "falsos_por_ano": alarmes_falsos / anos_avaliados,
        "falsos_por_ano_convencao_antiga": alarmes_falsos / ANOS_CIVIS_DA_AVALIACAO,
        "semanas": semanas,
        "semanas_de_surto": int(houve_surto.sum()),
        "acertos": acertos,
        "alarmes_falsos": alarmes_falsos,
        "surtos_perdidos": surtos_perdidos,
    }


def conferir_trava(por_braco_e_horizonte: dict) -> bool:
    """Confere se a configuracao adotada reproduz o painel publicado.

    Args:
        por_braco_e_horizonte: As metricas indexadas por (braco, horizonte).

    Returns:
        True se os seis numeros baterem dentro da tolerancia.
    """
    print(f"TRAVA — adotada contra o painel publicado (limiar {LIMIAR_DA_CONVENCAO_ANTIGA})")
    tudo_bate = True
    for horizonte, esperado in PAINEL_DO_ALARME_PUBLICADO.items():
        medido = por_braco_e_horizonte[
            (calcular.BRACO_FOLHA_5, horizonte, LIMIAR_DA_CONVENCAO_ANTIGA)
        ]
        for nome, valor_esperado in esperado.items():
            tolerancia = TOLERANCIA_DA_PROPORCAO
            diferenca = abs(medido[nome] - valor_esperado)
            bate = diferenca <= tolerancia
            tudo_bate = tudo_bate and bate
            marca = "ok" if bate else "DIVERGE"
            print(
                f"  h={horizonte:>2} {nome:<15} medido {medido[nome]:.3f} "
                f"esperado {valor_esperado:.3f}  {marca}"
            )
    return tudo_bate


def main() -> None:
    """Calcula o alarme dos tres bracos e grava a tabela comparativa."""
    previsoes = calcular.carregar_previsoes(calcular.CAMINHO_PREVISOES)
    todos_os_bracos = pd.concat(
        [
            previsoes[
                previsoes["braco"].isin([calcular.BRACO_FOLHA_5, calcular.BRACO_FOLHA_20])
            ],
            calcular.montar_modelo_composto(previsoes),
            calcular.montar_regua_sazonal(previsoes),
        ],
        ignore_index=True,
    )
    todos_os_bracos = calcular.recortar_para_a_avaliacao(todos_os_bracos)

    nomes_legiveis = {
        calcular.BRACO_FOLHA_5: "Adotado (folha 5)",
        calcular.BRACO_FOLHA_20: "Folha 20, com vetor",
        "composto": "Composto",
        "regua_sazonal": "Regua sazonal",
    }

    por_braco_e_horizonte = {}
    linhas = []
    for nome_interno, nome_legivel in nomes_legiveis.items():
        for horizonte in HORIZONTES_RELATADOS:
            recorte = todos_os_bracos[
                (todos_os_bracos["braco"] == nome_interno)
                & (todos_os_bracos["h"] == horizonte)
            ]
            if recorte.empty:
                continue
            metricas = calcular_metricas_do_alarme(recorte)
            metricas_na_convencao_antiga = calcular_metricas_do_alarme(
                recorte, LIMIAR_DA_CONVENCAO_ANTIGA
            )
            por_braco_e_horizonte[(nome_interno, horizonte, LIMIAR_DA_CONVENCAO_ANTIGA)] = (
                metricas_na_convencao_antiga
            )
            por_braco_e_horizonte[(nome_interno, horizonte, LIMIAR_DE_SURTO)] = metricas
            linhas.append({"braco": nome_legivel, "h": horizonte, **metricas})

    if not conferir_trava(por_braco_e_horizonte):
        raise SystemExit("\nTRAVA REPROVADA — nenhum numero novo deve ser lido.")
    print("  VEREDITO: trava valida\n")

    tabela = pd.DataFrame(linhas)
    tabela.to_csv(PASTA_DESTE_SCRIPT / "saidas" / "alarme_do_composto.csv", index=False)

    for horizonte in HORIZONTES_RELATADOS:
        print(f"--- h = {horizonte} semanas ---")
        for _, linha in tabela[tabela["h"] == horizonte].iterrows():
            print(
                f"  {linha['braco']:<22} sensib {linha['sensibilidade']:.3f} | "
                f"precisao {linha['precisao']:.3f} | falsos/ano {linha['falsos_por_ano']:.1f} "
                f"(pela conta antiga {linha['falsos_por_ano_convencao_antiga']:.1f}) | "
                f"acertos {int(linha['acertos'])} falsos {int(linha['alarmes_falsos'])} "
                f"perdidos {int(linha['surtos_perdidos'])}"
            )

    de_referencia = por_braco_e_horizonte[(calcular.BRACO_FOLHA_5, 12, LIMIAR_DE_SURTO)]
    print(
        f"\nBase: {de_referencia['semanas_de_surto']} das {de_referencia['semanas']} "
        f"semanas avaliadas passaram de {LIMIAR_DE_SURTO} casos "
        f"({de_referencia['semanas_de_surto'] / de_referencia['semanas']:.0%})."
    )


if __name__ == "__main__":
    main()
