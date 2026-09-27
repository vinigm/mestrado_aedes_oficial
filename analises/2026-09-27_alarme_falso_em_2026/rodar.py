"""O modelo teria anunciado um surto na temporada de 2026, que nao veio?

Porto Alegre teve 12 casos confirmados no ano inteiro ate 26/04/2026. O modelo
aprendeu numa serie que so cresce — 5.583 casos em 2022, 24.793 em 2025 — e a
pergunta do Vinicius e se ele criou um vies de alta forte o bastante para
gritar surto num ano vazio.

⚠️ ESTATUTO: DESCRITIVO, E A PERGUNTA E BINARIA. Nao se mede erro, R2 nem
captura em 2026: prever 12 casos a partir de uma serie crescente e impossivel,
e o Vinicius ja tirou 2026 da avaliacao em 26/09/2026. O que se mede e se o
alarme tocou. Protocolo completo em PRE_DECLARACAO.md.

O obstaculo, e o contorno
-------------------------
O walk-forward do projeto para em 01/02/2026, e nao por falta de dado: os casos
existem ate 26/04/2026. O que trava e o corte de maturidade de 12 semanas, que
APAGA os casos das semanas recentes porque a confirmacao do SINAN atrasa.

Aqui o corte continua valendo para tudo que o modelo VE — features e treino —,
e a pergunta de cada previsao e feita numa semana dentro da maturidade. So o
GABARITO, o numero real com que a previsao e comparada, vem da tabela crua.

A diferenca em uma linha: o harness exige gabarito maduro para incluir um
corte; aqui a exigencia cai, porque o que interessa e o que o modelo DISSE, e
nao o quanto ele errou.
"""

from __future__ import annotations

import pathlib
import sys
import time

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DA_BATERIA = PASTA_DESTE_ARQUIVO.parent / "2026-09-23_bateria_noturna"
sys.path.insert(0, str(PASTA_DA_BATERIA))

import harness  # noqa: E402  (depende do sys.path ajustado acima)
from acesso import fontes  # noqa: E402
from config.experimentos.cidade_referencia import CIDADE_REFERENCIA  # noqa: E402
from config.modelo import EspecificacaoModelo  # noqa: E402
from dominio.features import construir_alvo_horizonte  # noqa: E402
from motor import corte_temporal  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

# A configuracao de folha minima 20, identica a referencia fora esse parametro.
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

# O composto usa a folha 5 ate 3 semanas e a folha 20 de 4 em diante.
ULTIMO_HORIZONTE_DA_FOLHA_5 = 3
HORIZONTES = (1, 4, 8, 12)

# Os tres limiares do Plano Municipal de Contingencia de Arboviroses 2026.
LIMIARES_DO_PLANO = {"Mobilizacao": 140, "Alerta": 421, "Emergencia": 702}

SEMANAS_DE_UM_ANO = 52
ANO_EM_TESTE = 2026


def carregar_gabarito_cru() -> pd.Series:
    """Le os casos reais sem o corte de maturidade, indexados por data.

    O corte apaga os casos das 12 semanas mais recentes, e e por isso que ele
    nao pode ser usado aqui: as semanas de fevereiro a abril de 2026 sao
    justamente as que interessam.

    Returns:
        Uma serie de casos confirmados por semana, com a data no indice.
    """
    tabela_crua = fontes.carregar_tabela_final()
    return tabela_crua.set_index("data")["casos"]


def escolher_modelo(horizonte: int) -> EspecificacaoModelo:
    """Diz qual configuracao o composto usa naquele horizonte.

    Args:
        horizonte: Quantas semanas a frente a previsao olha.

    Returns:
        A folha 5 ate 3 semanas, a folha 20 de 4 em diante.
    """
    if horizonte <= ULTIMO_HORIZONTE_DA_FOLHA_5:
        return CIDADE_REFERENCIA.modelo

    return HISTGB_FOLHA_20


def prever_um_horizonte(
    tabela: pd.DataFrame,
    colunas_do_modelo: list[str],
    horizonte: int,
    gabarito: pd.Series,
) -> pd.DataFrame:
    """Roda o walk-forward de um horizonte SEM exigir gabarito maduro.

    O treino de cada corte continua vindo so de semanas cuja resposta ja
    existia na data da pergunta — a regra de corte pela data da RESPOSTA nao e
    afrouxada. O que muda e que a semana de teste entra mesmo quando o gabarito
    dela foi apagado pelo corte de maturidade.

    Args:
        tabela: A tabela com features, ja com o corte de maturidade aplicado.
        colunas_do_modelo: As colunas que entram no modelo.
        horizonte: Quantas semanas a frente prever.
        gabarito: Os casos reais sem corte, para comparar depois.

    Returns:
        Uma linha por corte, com data-alvo, real e previsto.
    """
    especificacao = escolher_modelo(horizonte)
    dados_do_horizonte = construir_alvo_horizonte(
        tabela, CIDADE_REFERENCIA.coluna_alvo, horizonte
    )
    features_com_sazonalidade = colunas_do_modelo + ["alvo_sin", "alvo_cos"]

    # ⚠️ A diferenca para o harness: `y_h` sai do dropna. As semanas sem
    # gabarito maduro passam a entrar como teste, e nunca como treino — quem
    # garante isso e `selecionar_treino_ja_respondido`, que so devolve semanas
    # com resposta conhecida.
    dados_validos = (
        dados_do_horizonte.dropna(subset=features_com_sazonalidade)
        .sort_values("data")
        .reset_index(drop=True)
    )

    linhas = []
    for indice_do_corte in range(
        CIDADE_REFERENCIA.minimo_semanas_treino,
        len(dados_validos),
        CIDADE_REFERENCIA.passo,
    ):
        teste = dados_validos.iloc[indice_do_corte : indice_do_corte + 1]
        data_do_teste = teste["data"].to_numpy()[0]
        treino = corte_temporal.selecionar_treino_ja_respondido(
            dados_validos, data_do_teste, horizonte
        )
        treino = treino.dropna(subset=["y_h"])
        if treino.empty:
            continue

        modelo = especificacao.criar()
        modelo.fit(treino[features_com_sazonalidade], treino["y_h"])
        previsao = float(modelo.predict(teste[features_com_sazonalidade])[0])

        data_alvo = pd.Timestamp(data_do_teste) + pd.Timedelta(weeks=horizonte)
        linhas.append(
            {
                "h": horizonte,
                "data_alvo": data_alvo,
                "real": float(gabarito.get(data_alvo, float("nan"))),
                "previsto": previsao,
            }
        )

    return pd.DataFrame(linhas)


def montar_regua_sazonal(
    previsoes: pd.DataFrame, gabarito: pd.Series
) -> pd.DataFrame:
    """Monta a regua sazonal para as mesmas semanas-alvo.

    A regua responde "quantos casos houve nesta mesma semana do ano passado?".
    Em 2026 ela repete 2025, que teve 24.793 casos — e por isso ela entra aqui:
    e o pior caso possivel para uma regra que so olha o calendario.

    Args:
        previsoes: As previsoes do modelo, de onde saem as semanas-alvo.
        gabarito: Os casos reais sem corte de maturidade.

    Returns:
        A regua no mesmo formato das previsoes do modelo.
    """
    linhas = []
    for _, linha in previsoes.iterrows():
        do_ano_passado = linha["data_alvo"] - pd.Timedelta(weeks=SEMANAS_DE_UM_ANO)
        if do_ano_passado not in gabarito.index:
            continue
        linhas.append(
            {
                "h": linha["h"],
                "data_alvo": linha["data_alvo"],
                "real": linha["real"],
                "previsto": float(gabarito[do_ano_passado]),
            }
        )

    return pd.DataFrame(linhas)


def contar_alarmes(de_um_braco: pd.DataFrame) -> dict[str, int]:
    """Conta em quantas semanas o alarme teria tocado, em cada limiar.

    Args:
        de_um_braco: As previsoes de um braco num horizonte, ja recortadas ao
            ano em teste.

    Returns:
        Um dicionario de nome do estagio para numero de semanas com alarme.
    """
    contagem = {}
    for nome_do_estagio, limiar in LIMIARES_DO_PLANO.items():
        contagem[nome_do_estagio] = int((de_um_braco["previsto"] > limiar).sum())
    return contagem


def main() -> None:
    """Roda o composto e a regua, e conta os alarmes de 2026."""
    print("=" * 78)
    print("ALARME FALSO EM 2026 — a temporada que nao veio")
    print("=" * 78, flush=True)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    gabarito = carregar_gabarito_cru()

    tabela_bruta = harness.carregar_tabela_bruta()
    tabela, colunas_do_modelo, _ = harness.montar_features_do_braco(
        tabela_bruta, harness.Braco("A_referencia")
    )

    casos_de_2026 = gabarito[gabarito.index.year == ANO_EM_TESTE].dropna()
    print(
        f"  {ANO_EM_TESTE}: {len(casos_de_2026)} semanas com caso divulgado, "
        f"{casos_de_2026.sum():.0f} casos no total, "
        f"maior semana {casos_de_2026.max():.0f}",
        flush=True,
    )

    por_horizonte = []
    for horizonte in HORIZONTES:
        marca = time.perf_counter()
        previsoes = prever_um_horizonte(tabela, colunas_do_modelo, horizonte, gabarito)
        previsoes["braco"] = "composto"
        regua = montar_regua_sazonal(previsoes, gabarito)
        regua["braco"] = "regua_sazonal"
        por_horizonte.append(pd.concat([previsoes, regua], ignore_index=True))
        ultima = previsoes["data_alvo"].max()
        print(
            f"  h={horizonte:2d}  {len(previsoes):3d} semanas, ate "
            f"{ultima.date()}  {time.perf_counter() - marca:5.1f}s",
            flush=True,
        )

    todas = pd.concat(por_horizonte, ignore_index=True)
    todas.to_csv(PASTA_DE_SAIDAS / "previsoes_de_2026.csv", index=False)

    do_ano = todas[todas["data_alvo"].dt.year == ANO_EM_TESTE]
    print(f"\n  ALARMES EM {ANO_EM_TESTE}, por limiar do plano municipal")
    print(
        f"  {'braco':<14} {'h':>3} {'semanas':>8} {'maior previsto':>15} "
        f"{'Mobilizacao':>12} {'Alerta':>8} {'Emergencia':>11}"
    )
    linhas_do_resumo = []
    for nome_do_braco in ("composto", "regua_sazonal"):
        for horizonte in HORIZONTES:
            celula = do_ano[
                (do_ano["braco"] == nome_do_braco) & (do_ano["h"] == horizonte)
            ]
            if celula.empty:
                continue
            contagem = contar_alarmes(celula)
            print(
                f"  {nome_do_braco:<14} {horizonte:3d} {len(celula):8d} "
                f"{celula['previsto'].max():15.0f} "
                f"{contagem['Mobilizacao']:12d} {contagem['Alerta']:8d} "
                f"{contagem['Emergencia']:11d}"
            )
            linhas_do_resumo.append(
                {
                    "braco": nome_do_braco,
                    "h": horizonte,
                    "semanas": len(celula),
                    "maior_previsto": celula["previsto"].max(),
                    "maior_real": celula["real"].max(),
                    **contagem,
                }
            )

    pd.DataFrame(linhas_do_resumo).to_csv(
        PASTA_DE_SAIDAS / "alarmes_de_2026.csv", index=False
    )

    print(f"\n  SEMANA A SEMANA DE {ANO_EM_TESTE} — modelo composto")
    for horizonte in HORIZONTES:
        celula = do_ano[
            (do_ano["braco"] == "composto") & (do_ano["h"] == horizonte)
        ].sort_values("data_alvo")
        if celula.empty:
            continue
        print(f"    h={horizonte}:")
        for _, linha in celula.iterrows():
            marca_do_alarme = (
                "<<< ALARME" if linha["previsto"] > LIMIARES_DO_PLANO["Alerta"] else ""
            )
            print(
                f"      {linha['data_alvo'].date()}  real {linha['real']:5.0f}  "
                f"previsto {linha['previsto']:7.0f}  {marca_do_alarme}"
            )


if __name__ == "__main__":
    main()
