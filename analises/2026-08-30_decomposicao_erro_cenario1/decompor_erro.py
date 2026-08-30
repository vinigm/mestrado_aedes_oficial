"""

Decompoe o erro do cenario 1 (previsao do numero de casos) por faixa de casos.

Motivo: o R2 do cenario e alto, mas a serie de POA e extremamente desigual -
61% das semanas tem 0 a 5 casos e algumas passam de 2.000. Num cenario assim o
R2 e dominado pelos picos, e um modelo pode ter R2 alto so por acertar o
formato geral da curva. A pergunta que o R2 NAO responde e a que importa para
vigilancia: o modelo enxerga o pico chegando, ou ele so acerta o "esta calmo"?

Este script replica o protocolo do experimento cidade_regressao usando as
FUNCOES DO PROPRIO PACOTE (nao uma copia), com a unica diferenca de guardar as
previsoes semana a semana em vez de descarta-las depois de calcular o MAE.

Uso:  python decompor_erro.py

"""

import sys
import time
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import numpy as np
import pandas as pd

from acesso import fontes
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from motor.walk_forward_regressao import executar_walk_forward_regressao

PASTA_SAIDAS = PASTA_ANALISE / "saidas"

HORIZONTES_ANALISADOS = (1, 4, 8, 12)

# Faixas de casos, escolhidas pela operacao e nao pelos dados: "entressafra" e
# semana em que nao ha o que alarmar; "pico" e o patamar em que a rede de
# saude sente. Os cortes sao declarados aqui para nao serem ajustados depois de
# ver o resultado.
LIMITE_ENTRESSAFRA = 5
LIMITE_PICO = 100


def classificar_faixa(casos_reais: float) -> str:
    """Rotula a semana pela intensidade real de casos naquela semana-alvo."""
    if casos_reais <= LIMITE_ENTRESSAFRA:
        return f"1_entressafra (<={LIMITE_ENTRESSAFRA})"
    if casos_reais <= LIMITE_PICO:
        return f"2_intermediaria ({LIMITE_ENTRESSAFRA}-{LIMITE_PICO})"
    return f"3_pico (>{LIMITE_PICO})"


def gerar_previsoes() -> pd.DataFrame:
    """

    Reproduz o cenario 1 e devolve as previsoes semana a semana.

    Usa a MESMA config, a MESMA selecao de clima e o MESMO motor do
    experimento oficial - o que muda e so guardar o que o experimento joga
    fora.

    """
    config = CIDADE_REGRESSAO

    tabela = fontes.carregar_tabela_final()
    tabela = surto.aplicar_corte_maturidade(tabela, config.semanas_corte_maturidade)
    tabela = features.construir_features_temporais(tabela)

    colunas_nucleo, colunas_clima, colunas_vetor = selecao_features.separar_grupos_de_features(
        tabela, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )
    ranking_clima = selecao_features.selecionar_clima_por_ganho(
        tabela, colunas_nucleo, colunas_clima, config.coluna_alvo,
        config.horizontes_selecao_clima, config.modelo_selecao_clima,
        config.fracao_treino_selecao,
    )

    # Fica so no k=6, que e o conjunto que o experimento reporta como M0_clima6
    # e M1_clima6_vetor - suficiente para a decomposicao e metade do custo.
    clima_enxuto = ranking_clima.head(6).index.tolist()
    print(f"clima selecionado (k=6): {clima_enxuto}", flush=True)

    conjuntos = {
        "M0_clima6": colunas_nucleo + clima_enxuto,
        "M1_clima6_vetor": colunas_nucleo + clima_enxuto + colunas_vetor,
    }

    previsoes_por_conjunto = []
    for nome_conjunto, colunas in conjuntos.items():
        print(f"rodando {nome_conjunto} ({len(colunas)} colunas)...", flush=True)
        previsoes = executar_walk_forward_regressao(
            tabela, colunas, config.coluna_alvo, HORIZONTES_ANALISADOS,
            config.modelo, config.minimo_semanas_treino, config.passo,
        )
        previsoes["conjunto"] = nome_conjunto
        previsoes_por_conjunto.append(previsoes)

    return pd.concat(previsoes_por_conjunto, ignore_index=True)


def decompor(previsoes: pd.DataFrame) -> pd.DataFrame:
    """

    Resume erro e vies por faixa de intensidade, horizonte e conjunto.

    O vies (previsto menos real) e a coluna que responde a pergunta de alarme:
    vies muito negativo no pico significa que o modelo SUBESTIMA a epidemia -
    e um modelo que subestima pico nao serve para alarmar, por melhor que seja
    o R2.

    """
    trabalho = previsoes.copy()
    trabalho["faixa"] = trabalho["real"].apply(classificar_faixa)
    trabalho["erro"] = trabalho["pred"] - trabalho["real"]

    linhas = []
    for (conjunto, horizonte, faixa), grupo in trabalho.groupby(["conjunto", "h", "faixa"]):
        media_real = grupo["real"].mean()
        erro_absoluto_medio = grupo["erro"].abs().mean()

        linhas.append({
            "conjunto": conjunto,
            "h": horizonte,
            "faixa": faixa,
            "n_semanas": len(grupo),
            "casos_reais_medio": media_real,
            "casos_previstos_medio": grupo["pred"].mean(),
            "MAE": erro_absoluto_medio,
            "vies_medio": grupo["erro"].mean(),
            "MAE_relativo": erro_absoluto_medio / media_real if media_real > 0 else np.nan,
        })

    return pd.DataFrame(linhas).sort_values(["conjunto", "h", "faixa"])


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    previsoes = gerar_previsoes()
    previsoes.to_csv(PASTA_SAIDAS / "previsoes_por_semana.csv", index=False)

    decomposicao = decompor(previsoes)
    decomposicao.to_csv(PASTA_SAIDAS / "decomposicao_erro_por_faixa.csv", index=False)

    print("\n" + "=" * 104, flush=True)
    print("ERRO DECOMPOSTO POR FAIXA DE INTENSIDADE (conjunto M0_clima6, so clima)", flush=True)
    print("=" * 104, flush=True)
    so_clima = decomposicao.loc[decomposicao["conjunto"] == "M0_clima6"]
    print(so_clima.drop(columns="conjunto").round(2).to_string(index=False), flush=True)

    print("\n" + "=" * 104, flush=True)
    print("O MESMO, COM O VETOR (M1_clima6_vetor)", flush=True)
    print("=" * 104, flush=True)
    com_vetor = decomposicao.loc[decomposicao["conjunto"] == "M1_clima6_vetor"]
    print(com_vetor.drop(columns="conjunto").round(2).to_string(index=False), flush=True)

    print(f"\ntempo total: {(time.time() - momento_inicial) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
