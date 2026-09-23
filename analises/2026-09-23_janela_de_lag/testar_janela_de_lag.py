"""Estender a janela de lag ajuda o horizonte longo?

O modelo prevê até 12 semanas à frente e olha no máximo 4 semanas para trás.
Este script mede se cobrir o vão de 5 a 12 semanas melhora a previsão.

O protocolo está fixado em PRE_DECLARACAO.md, escrito antes desta execução.
Nada aqui decide nada: o script mede, grava e imprime. A leitura contra o
critério pré-declarado acontece depois, em analisar_resultado.py.

Uso:
    python3 testar_janela_de_lag.py
"""

import dataclasses
import pathlib
import sys
import time

import pandas as pd

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DO_PIPELINE = PASTA_DESTE_ARQUIVO.parent.parent / "modelagem_aedes"
sys.path.insert(0, str(PASTA_DO_PIPELINE))

from acesso import fontes  # noqa: E402  (depende do sys.path ajustado acima)
from config.experimentos.cidade_referencia import CIDADE_REFERENCIA  # noqa: E402
from dominio import features, selecao_features, surto  # noqa: E402
from dominio.features import construir_alvo_horizonte  # noqa: E402
from motor import corte_temporal  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

# Onde começa o período que julga o resultado. A escolha da configuração
# aconteceu na calibração, que termina antes disso.
INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")


@dataclasses.dataclass(frozen=True)
class BracoDoTeste:
    """Uma variante da janela de lag a ser medida.

    Attributes:
        nome: Identificador do braço nas saídas.
        lags_em_semanas: Quais defasagens cada coluna elegível recebe.
    """

    nome: str
    lags_em_semanas: list[int]


BRACOS = (
    BracoDoTeste("A_referencia", [1, 2, 3, 4]),
    BracoDoTeste("B_lags_ate_8", [1, 2, 3, 4, 6, 8]),
    BracoDoTeste("C_lags_ate_12", [1, 2, 3, 4, 6, 8, 10, 12]),
)


def montar_tabela_do_braco(
    tabela_base: pd.DataFrame, braco: BracoDoTeste
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Constrói as features do braço e escolhe as colunas de clima dele.

    ⚠️ A lista de defasagens vive numa constante de módulo que
    `construir_features_temporais` lê por dentro, então ela é trocada aqui
    antes da chamada. Duplicar a construção de features neste script evitaria
    o remendo, mas criaria uma segunda implementação que envelheceria em
    silêncio quando o pipeline mudasse — o que é pior.

    A seleção de clima roda com o mesmo procedimento nos três braços. Como o
    conjunto candidato cresce junto com as defasagens, cada braço pode escolher
    colunas diferentes. É limitação declarada na pré-declaração, não descuido.

    Args:
        tabela_base: A tabela semanal já com o corte de maturidade aplicado.
        braco: A variante a montar.

    Returns:
        A tabela com as features do braço, a lista de colunas que vão ao modelo
        e a lista das colunas de clima escolhidas.
    """
    features.LAGS_SEMANAS = braco.lags_em_semanas
    tabela_com_features = features.construir_features_temporais(tabela_base)

    colunas_nucleo, colunas_clima, colunas_vetor = (
        selecao_features.separar_grupos_de_features(
            tabela_com_features,
            CIDADE_REFERENCIA.colunas_ignorar,
            CIDADE_REFERENCIA.padroes_vetor,
            CIDADE_REFERENCIA.padroes_clima,
        )
    )

    ranking_de_clima = selecao_features.selecionar_clima_por_ganho(
        tabela_com_features,
        colunas_nucleo,
        colunas_clima,
        CIDADE_REFERENCIA.coluna_alvo,
        CIDADE_REFERENCIA.horizontes_selecao_clima,
        CIDADE_REFERENCIA.modelo_selecao_clima,
        CIDADE_REFERENCIA.fracao_treino_selecao,
    )
    quantas_de_clima = CIDADE_REFERENCIA.valores_k[0]
    clima_escolhido = ranking_de_clima.head(quantas_de_clima).index.tolist()

    colunas_do_modelo = colunas_nucleo + clima_escolhido + colunas_vetor

    return tabela_com_features, colunas_do_modelo, clima_escolhido


def rodar_walk_forward_com_data(
    tabela: pd.DataFrame, colunas_do_modelo: list[str], horizonte: int
) -> pd.DataFrame:
    """Roda o walk-forward de um horizonte, guardando a data de cada previsão.

    Espelha `motor.walk_forward_regressao.executar_walk_forward_regressao`,
    incluindo o corte de treino pela data da RESPOSTA. A única diferença é que
    aqui a `data_alvo` volta na saída: sem ela não dá para parear a comparação
    entre braços, e a regra do projeto é que comparação não pareada não vale.

    Args:
        tabela: A tabela com as features do braço.
        colunas_do_modelo: As colunas de entrada, sem a sazonalidade do alvo.
        horizonte: Quantas semanas à frente prever.

    Returns:
        Uma linha por semana avaliada, com h, data_alvo, real e previsto.
    """
    dados_do_horizonte = construir_alvo_horizonte(
        tabela, CIDADE_REFERENCIA.coluna_alvo, horizonte
    )
    features_com_sazonalidade = colunas_do_modelo + ["alvo_sin", "alvo_cos"]

    dados_validos = (
        dados_do_horizonte.dropna(subset=features_com_sazonalidade + ["y_h"])
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

        modelo = CIDADE_REFERENCIA.modelo.criar()
        modelo.fit(treino[features_com_sazonalidade], treino["y_h"])
        previsao = float(modelo.predict(teste[features_com_sazonalidade])[0])

        linhas.append(
            {
                "h": horizonte,
                "data_alvo": pd.Timestamp(data_do_teste)
                + pd.Timedelta(weeks=horizonte),
                "real": float(teste["y_h"].to_numpy()[0]),
                "previsto": previsao,
            }
        )

    return pd.DataFrame(linhas)


def main() -> None:
    """Roda os três braços e grava uma previsão por linha."""
    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela_base = surto.aplicar_corte_maturidade(
        fontes.carregar_tabela_final(), CIDADE_REFERENCIA.semanas_corte_maturidade
    )
    print(
        f"referência: {CIDADE_REFERENCIA.modelo.nome} · "
        f"quantil {CIDADE_REFERENCIA.modelo.parametros['quantile']} · "
        f"passo {CIDADE_REFERENCIA.passo}",
        flush=True,
    )

    previsoes_de_todos = []
    clima_por_braco = []

    for braco in BRACOS:
        inicio_do_braco = time.perf_counter()
        tabela, colunas, clima_escolhido = montar_tabela_do_braco(tabela_base, braco)

        print(
            f"\n[{braco.nome}] lags {braco.lags_em_semanas} · "
            f"{len(colunas)} features · clima: {clima_escolhido}",
            flush=True,
        )
        clima_por_braco.append(
            {
                "braco": braco.nome,
                "lags": str(braco.lags_em_semanas),
                "n_features": len(colunas),
                "clima_escolhido": " | ".join(clima_escolhido),
            }
        )

        for horizonte in CIDADE_REFERENCIA.horizontes:
            inicio_do_horizonte = time.perf_counter()
            previsoes = rodar_walk_forward_com_data(tabela, colunas, horizonte)
            previsoes["braco"] = braco.nome
            previsoes_de_todos.append(previsoes)
            print(
                f"  h={horizonte:2d}  {len(previsoes):3d} semanas  "
                f"{time.perf_counter() - inicio_do_horizonte:5.1f}s",
                flush=True,
            )

        print(
            f"[{braco.nome}] concluído em "
            f"{(time.perf_counter() - inicio_do_braco) / 60:.1f} min",
            flush=True,
        )

    todas_as_previsoes = pd.concat(previsoes_de_todos, ignore_index=True)
    caminho_previsoes = PASTA_DE_SAIDAS / "previsoes_por_braco.csv"
    todas_as_previsoes.to_csv(caminho_previsoes, index=False)

    caminho_clima = PASTA_DE_SAIDAS / "clima_escolhido_por_braco.csv"
    pd.DataFrame(clima_por_braco).to_csv(caminho_clima, index=False)

    print(f"\ngravado: {caminho_previsoes.name} ({len(todas_as_previsoes)} linhas)")
    print(f"gravado: {caminho_clima.name}")


if __name__ == "__main__":
    main()
