"""Figura headline: sem ENSO + alvo com corte de maturidade -> o vetor carrega o horizonte longo.

Le a tabela de metricas por horizonte dos modelos de clima maduro (M0 so-clima
sem ENSO x M1 clima+vetor) e monta uma figura de dois paineis:

  - Painel esquerdo: R2 x horizonte de previsao, uma curva por conjunto, com a
    faixa de horizonte longo (semanas 5,5 a 12,5) destacada e uma anotacao de
    leitura operacional.
  - Painel direito: lift marginal do vetor (reducao percentual do MAE de M1 em
    relacao a M0), em barras verdes (lift positivo) ou vermelhas (lift <= 0).

A figura e salva como lift_maturidade.png no diretorio de trabalho atual.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------------------------- config
# Marcador de diretorio que identifica a raiz do projeto (permite rodar o
# script de qualquer subpasta).
MARCADOR_RAIZ = "Raspagem"

# Nome do arquivo de metricas por horizonte lido como entrada.
NOME_ARQUIVO_METRICAS = "clima_enxuto_maturidade_resultados.csv"

# Nome do arquivo PNG gerado (gravado no diretorio de trabalho atual).
NOME_ARQUIVO_FIGURA = "lift_maturidade.png"

# Rotulos dos conjuntos (colunas do pivot) usados nos calculos e nas curvas.
CONJUNTO_SO_CLIMA = "M0_clima6"
CONJUNTO_CLIMA_VETOR = "M1_clima6_vetor"

# Faixa de horizonte longo (semanas a frente) destacada nos dois paineis.
INICIO_FAIXA_HORIZONTE_LONGO = 5.5
FIM_FAIXA_HORIZONTE_LONGO = 12.5

# Aparencia da figura.
TAMANHO_FIGURA = (13, 4.5)
COR_SO_CLIMA = "tab:blue"
COR_CLIMA_VETOR = "tab:green"
COR_LIFT_POSITIVO = "tab:green"
COR_LIFT_NAO_POSITIVO = "tab:red"
ALPHA_FAIXA_HORIZONTE = 0.08
ALPHA_GRADE = 0.3
FONTE_LEGENDA = 9
FONTE_ANOTACAO = 9
POSICAO_ANOTACAO = (10, 0.62)
TEXTO_ANOTACAO = "1,5–3 meses:\nclima sozinho ~0,08\nvetor segura ~0,35"
RESOLUCAO_DPI = 110

# Fator para converter a reducao proporcional de MAE em porcentagem.
PERCENTUAL = 100


def encontrar_raiz_do_projeto(marcador_de_diretorio: str = MARCADOR_RAIZ) -> Path:
    """Sobe a partir do diretorio atual ate achar a raiz do projeto.

    A raiz e identificada pela presenca de um subdiretorio marcador (por padrao
    'Raspagem'), o que torna o script executavel de qualquer subpasta.

    Args:
        marcador_de_diretorio: Nome do subdiretorio que identifica a raiz.

    Returns:
        Caminho da raiz do projeto.

    Raises:
        FileNotFoundError: Se nenhum diretorio ancestral contiver o marcador.
    """
    diretorio_atual = Path.cwd()
    for diretorio_candidato in [diretorio_atual, *diretorio_atual.parents]:
        if (diretorio_candidato / marcador_de_diretorio).is_dir():
            return diretorio_candidato
    raise FileNotFoundError("raiz nao encontrada")


def carregar_metricas() -> pd.DataFrame:
    """Le a tabela de metricas por horizonte dos modelos de clima maduro.

    Returns:
        DataFrame com as colunas 'conjunto', 'h', 'n', 'MAE' e 'R2'.
    """
    raiz_do_projeto = encontrar_raiz_do_projeto()
    diretorio_tabela = raiz_do_projeto / "Bases de dados" / "tabela_modelagem"
    caminho_metricas = diretorio_tabela / NOME_ARQUIVO_METRICAS
    return pd.read_csv(caminho_metricas)


def pivotar_por_horizonte(metricas: pd.DataFrame, metrica: str) -> pd.DataFrame:
    """Reorganiza uma metrica em formato largo: horizonte nas linhas, conjunto nas colunas.

    Args:
        metricas: Tabela longa com colunas 'h', 'conjunto' e a metrica desejada.
        metrica: Nome da coluna de valor a espalhar (ex.: 'R2' ou 'MAE').

    Returns:
        DataFrame indexado por horizonte 'h' com uma coluna por conjunto.
    """
    return metricas.pivot(index="h", columns="conjunto", values=metrica)


def calcular_lift_do_vetor(mae_por_conjunto: pd.DataFrame) -> pd.Series:
    """Calcula o lift marginal do vetor: reducao percentual do MAE de M1 sobre M0.

    Lift positivo significa que adicionar o vetor reduziu o erro (MAE) em relacao
    ao modelo so-clima.

    Args:
        mae_por_conjunto: MAE em formato largo (horizonte x conjunto).

    Returns:
        Serie de lift (%) indexada por horizonte.
    """
    mae_so_clima = mae_por_conjunto[CONJUNTO_SO_CLIMA]
    mae_clima_vetor = mae_por_conjunto[CONJUNTO_CLIMA_VETOR]
    reducao_proporcional = (mae_so_clima - mae_clima_vetor) / mae_so_clima
    return reducao_proporcional * PERCENTUAL


def cores_das_barras_de_lift(lift: pd.Series) -> np.ndarray:
    """Escolhe a cor de cada barra de lift: verde se positivo, vermelho caso contrario.

    Args:
        lift: Serie de lift (%) por horizonte.

    Returns:
        Array de cores alinhado a 'lift' (verde para lift > 0, vermelho caso contrario).
    """
    lift_positivo = lift.to_numpy() > 0
    return np.where(lift_positivo, COR_LIFT_POSITIVO, COR_LIFT_NAO_POSITIVO)


def desenhar_painel_r2(eixo: plt.Axes, r2_por_conjunto: pd.DataFrame) -> None:
    """Desenha o painel de R2 x horizonte, com curvas dos dois conjuntos.

    Args:
        eixo: Eixo matplotlib onde desenhar.
        r2_por_conjunto: R2 em formato largo (horizonte x conjunto).
    """
    eixo.plot(
        r2_por_conjunto.index,
        r2_por_conjunto[CONJUNTO_SO_CLIMA],
        "o-",
        color=COR_SO_CLIMA,
        label="M0: só clima (sem ENSO)",
    )
    eixo.plot(
        r2_por_conjunto.index,
        r2_por_conjunto[CONJUNTO_CLIMA_VETOR],
        "o-",
        color=COR_CLIMA_VETOR,
        label="M1: clima + vetor",
    )
    eixo.axhline(0, color="k", lw=0.8, ls="--")
    eixo.axvspan(
        INICIO_FAIXA_HORIZONTE_LONGO,
        FIM_FAIXA_HORIZONTE_LONGO,
        color=COR_CLIMA_VETOR,
        alpha=ALPHA_FAIXA_HORIZONTE,
    )
    eixo.annotate(
        TEXTO_ANOTACAO,
        POSICAO_ANOTACAO,
        fontsize=FONTE_ANOTACAO,
        color="dimgray",
        ha="center",
    )
    eixo.set_title("R² × horizonte (sem ENSO, alvo maduro)")
    eixo.set_xlabel("semanas à frente")
    eixo.set_ylabel("R²")
    eixo.legend(loc="upper right", fontsize=FONTE_LEGENDA)
    eixo.grid(alpha=ALPHA_GRADE)


def desenhar_painel_lift(eixo: plt.Axes, lift: pd.Series) -> None:
    """Desenha o painel de lift marginal do vetor, em barras coloridas por sinal.

    Args:
        eixo: Eixo matplotlib onde desenhar.
        lift: Serie de lift (%) por horizonte.
    """
    cores = cores_das_barras_de_lift(lift)
    eixo.bar(lift.index, lift, color=cores)
    eixo.axhline(0, color="k", lw=0.8)
    eixo.axvspan(
        INICIO_FAIXA_HORIZONTE_LONGO,
        FIM_FAIXA_HORIZONTE_LONGO,
        color=COR_CLIMA_VETOR,
        alpha=ALPHA_FAIXA_HORIZONTE,
    )
    eixo.set_title("Lift marginal do vetor (% redução do MAE)")
    eixo.set_xlabel("semanas à frente")
    eixo.set_ylabel("lift %")
    eixo.grid(alpha=ALPHA_GRADE)


def montar_figura(r2_por_conjunto: pd.DataFrame, lift: pd.Series) -> plt.Figure:
    """Monta a figura de dois paineis (R2 e lift do vetor).

    Args:
        r2_por_conjunto: R2 em formato largo (horizonte x conjunto).
        lift: Serie de lift (%) por horizonte.

    Returns:
        Figura matplotlib pronta para ser salva.
    """
    figura, eixos = plt.subplots(1, 2, figsize=TAMANHO_FIGURA)
    desenhar_painel_r2(eixos[0], r2_por_conjunto)
    desenhar_painel_lift(eixos[1], lift)
    figura.tight_layout()
    return figura


def salvar_figura(figura: plt.Figure) -> Path:
    """Salva a figura como PNG no diretorio de trabalho atual.

    Args:
        figura: Figura a gravar.

    Returns:
        Caminho do arquivo PNG gerado.
    """
    caminho_saida = Path.cwd() / NOME_ARQUIVO_FIGURA
    figura.savefig(caminho_saida, dpi=RESOLUCAO_DPI, bbox_inches="tight")
    return caminho_saida


def main() -> None:
    """Le as metricas, monta a figura headline de lift e a salva em PNG."""
    metricas = carregar_metricas()
    r2_por_conjunto = pivotar_por_horizonte(metricas, "R2")
    mae_por_conjunto = pivotar_por_horizonte(metricas, "MAE")
    lift = calcular_lift_do_vetor(mae_por_conjunto)

    figura = montar_figura(r2_por_conjunto, lift)
    caminho_saida = salvar_figura(figura)
    print("salvo:", caminho_saida)


if __name__ == "__main__":
    main()
