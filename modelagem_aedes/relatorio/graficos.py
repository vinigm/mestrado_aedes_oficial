"""

Aqui o programa desenha as figuras dos experimentos feitos com dados da cidade (parte do relatorio final).

Isto e uma versao organizada dos scripts antigos plot_deteccao_surto.py,
plot_lift_maturidade.py e plot_lift_sem_enso.py. Cada figura e desenhada por
uma funcao que recebe uma tabela ja pronta e o lugar onde salvar; quem abre os
arquivos CSV com os resultados fica so na funcao gerar_todas_figuras(), pra
manter separado o "abrir arquivo" do "desenhar o grafico".

Entra: os CSVs da pasta dados/saidas/resultados (gerados pelo main.py).
Sai: as figuras em .png na pasta dados/saidas/figuras.

"""

import dataclasses
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # escolhe um jeito de desenhar que nao precisa de tela (funciona rodando por comando, sem abrir janela)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import settings

# Numero que decide o que conta como "surto" na figura de deteccao (aqui e o percentil 90, o mais usado).
PERCENTIL_SURTO_FIGURA = 90

# Pontos marcados no eixo x da figura de deteccao: daqui a 1, 2 e 3 meses.
HORIZONTES_DESTAQUE = [4, 8, 12]

# Cor de cada linha do grafico (as mesmas cores dos scripts antigos, pra ficar tudo igual).
COR_CLIMA_AR = "#1f77b4"
COR_PERSISTENCIA = "#7f7f7f"
COR_SAZONAL = "#ff7f0e"
COR_SO_CLIMA = "#2ca02c"
COR_CLIMA_VETOR = "#d62728"

# Pedaco do grafico (mais ou menos de 1,5 a 3 meses pra frente) que fica sombreado nas figuras de lift.
INICIO_FAIXA_HORIZONTE_LONGO = 5.5
FIM_FAIXA_HORIZONTE_LONGO = 12.5

# Nomes dos grupos comparados nas figuras de lift (sao colunas dos arquivos CSV com os resultados da regressao).
CONJUNTO_SO_CLIMA = "M0_clima6"
CONJUNTO_CLIMA_VETOR = "M1_clima6_vetor"



def plotar_deteccao_surto(
    resultados: pd.DataFrame,
    caminho_saida: Path,
    percentil: int = PERCENTIL_SURTO_FIGURA,
) -> Path:
    """

    Desenha a figura do experimento de deteccao de surto (sao dois quadros lado a lado).

    O quadro A (se da pra usar de verdade; dados do InfoDengue de 2010 a 2026)
    compara o quanto o modelo (chamado LGBM) acerta contra dois jeitos simples
    de prever: repetir o valor da semana anterior, ou seguir a media de cada
    epoca do ano; isso pra cada tempo de antecedencia da previsao. O quadro B
    (o quanto o mosquito ajuda a prever; dados da tabela_final) compara o
    quanto acerta usando so a epoca do ano, so o clima, ou clima junto com os
    dados do mosquito, tambem pra cada tempo de antecedencia.

    Args:
        resultados: O conteudo do arquivo deteccao_surto_resultados.csv
            (colunas exp, pctl, modelo, h, f1 -- essa ultima e um numero que
            mostra o quanto o modelo acerta).
        caminho_saida: Onde salvar a imagem .png.
        percentil: Numero que decide o que conta como "surto" (usado pra
            escolher as linhas certas do arquivo).

    Returns:
        O caminho de onde a figura foi salva.

    """
    figura, eixos = plt.subplots(1, 2, figsize=(12, 4.6))

    # --- Quadro A: da pra usar de verdade? (LGBM contra os jeitos simples de prever) ---
    painel_a = resultados[
        (resultados["exp"] == "A_infodengue") & (resultados["pctl"] == percentil)
    ]
    eixo_a = eixos[0]
    series_painel_a = [
        ("clima+AR_LGBM", COR_CLIMA_AR),
        ("persistencia", COR_PERSISTENCIA),
        ("sazonal", COR_SAZONAL),
    ]
    for nome_modelo, cor in series_painel_a:
        serie = painel_a[painel_a["modelo"] == nome_modelo].sort_values("h")
        eixo_a.plot(serie["h"], serie["f1"], marker="o", label=nome_modelo, color=cor)
    eixo_a.set_title(
        f"A) Viabilidade — InfoDengue 2010-26 (surto = P{percentil})\n"
        "F1 de deteccao por horizonte"
    )
    eixo_a.set_xlabel("horizonte (semanas a frente)")
    eixo_a.set_ylabel("F1")
    eixo_a.set_xticks(HORIZONTES_DESTAQUE)
    eixo_a.set_ylim(0, 1)
    eixo_a.grid(alpha=0.3)
    eixo_a.legend(fontsize=8)
    anotacoes_de_meses = [(4, "1 mes"), (8, "2 meses"), (12, "3 meses")]
    for posicao_x, rotulo in anotacoes_de_meses:
        eixo_a.annotate(rotulo, (posicao_x, 0.02), ha="center", fontsize=7, color="gray")

    # --- Quadro B: o quanto o mosquito ajuda a prever (dados da tabela_final) ---
    painel_b = resultados[
        (resultados["exp"] == "B_tabela_final") & (resultados["pctl"] == percentil)
    ]
    eixo_b = eixos[1]
    series_painel_b = [
        ("sazonal", COR_SAZONAL),
        ("so-clima", COR_SO_CLIMA),
        ("clima+vetor", COR_CLIMA_VETOR),
    ]
    for nome_modelo, cor in series_painel_b:
        serie = painel_b[painel_b["modelo"] == nome_modelo].sort_values("h")
        eixo_b.plot(serie["h"], serie["f1"], marker="o", label=nome_modelo, color=cor)
    eixo_b.set_title(
        f"B) Lift do vetor na deteccao — tabela_final (surto = P{percentil})\n"
        "F1: so-clima vs clima+VETOR"
    )
    eixo_b.set_xlabel("horizonte (semanas a frente)")
    eixo_b.set_ylabel("F1")
    eixo_b.set_xticks(HORIZONTES_DESTAQUE)
    eixo_b.set_ylim(0, 1)
    eixo_b.grid(alpha=0.3)
    eixo_b.legend(fontsize=8)

    figura.tight_layout()
    figura.savefig(caminho_saida, dpi=130, bbox_inches="tight")
    plt.close(figura)
    return caminho_saida


@dataclasses.dataclass(frozen=True)
class EstiloFiguraLift:
    """

    Guarda os textos que mudam entre as duas figuras de lift do vetor (regressao).

    As figuras "maturidade" e "sem_enso" tem o mesmo desenho (R2 por tempo de
    antecedencia, mais barras mostrando o quanto o erro cai); so mudam os
    titulos, o rotulo, o texto da anotacao e o quanto a faixa colorida aparece.

    Attributes:
        titulo_r2: Titulo do quadro de R2 por tempo de antecedencia.
        rotulo_so_clima: Rotulo da linha "so clima" na legenda.
        texto_anotacao: Texto escrito dentro do quadro de R2.
        posicao_anotacao: Onde (x, y) fica esse texto dentro do quadro.
        titulo_lift: Titulo do quadro com as barras.
        transparencia_faixa: O quanto a faixa colorida do horizonte longo aparece (de 0 a 1).

    """

    titulo_r2: str
    rotulo_so_clima: str
    texto_anotacao: str
    posicao_anotacao: tuple[float, float]
    titulo_lift: str
    transparencia_faixa: float


ESTILO_LIFT_MATURIDADE = EstiloFiguraLift(
    titulo_r2="R² × horizonte (sem ENSO, alvo maduro)",
    rotulo_so_clima="M0: só clima (sem ENSO)",
    texto_anotacao="1,5–3 meses:\nclima sozinho ~0,08\nvetor segura ~0,35",
    posicao_anotacao=(10, 0.62),
    titulo_lift="Lift marginal do vetor (% redução do MAE)",
    transparencia_faixa=0.08,
)

ESTILO_LIFT_SEM_ENSO = EstiloFiguraLift(
    titulo_r2="R² × horizonte (sem ENSO)",
    rotulo_so_clima="M0: só clima-enxuto (sem ENSO)",
    texto_anotacao="clima puro perde a skill\n(R² ≤ 0); o vetor segura",
    posicao_anotacao=(9, -0.05),
    titulo_lift="Lift marginal do vetor (% redução do MAE), sem ENSO",
    transparencia_faixa=0.07,
)



def plotar_lift_do_vetor(
    resultados: pd.DataFrame,
    caminho_saida: Path,
    estilo: EstiloFiguraLift,
) -> Path:
    """

    Desenha uma figura mostrando o quanto o mosquito ajuda a prever, numa regressao (sao dois quadros).

    O quadro da esquerda mostra o R2 (um numero que diz o quanto o modelo
    explica a realidade) por tempo de antecedencia, comparando so-clima com
    clima+mosquito. O quadro da direita mostra, em barras, o quanto o erro cai
    (em %) quando se usa o mosquito, tambem por tempo de antecedencia.

    Args:
        resultados: Tabela da regressao com as colunas conjunto, h, R2, MAE
            (o MAE e o tamanho medio do erro).
        caminho_saida: Onde salvar a imagem .png.
        estilo: Os textos e ajustes visuais que mudam entre as versoes
            (maturidade / sem ENSO).

    Returns:
        O caminho de onde a figura foi salva.

    """
    r2_por_horizonte = resultados.pivot(index="h", columns="conjunto", values="R2")
    mae_por_horizonte = resultados.pivot(index="h", columns="conjunto", values="MAE")
    mae_so_clima = mae_por_horizonte[CONJUNTO_SO_CLIMA]
    mae_clima_vetor = mae_por_horizonte[CONJUNTO_CLIMA_VETOR]
    lift_percentual = (mae_so_clima - mae_clima_vetor) / mae_so_clima * 100

    figura, eixos = plt.subplots(1, 2, figsize=(13, 4.5))

    # --- Quadro da esquerda: R2 por tempo de antecedencia ---
    eixo_r2 = eixos[0]
    eixo_r2.plot(
        r2_por_horizonte.index,
        r2_por_horizonte[CONJUNTO_SO_CLIMA],
        "o-",
        color="tab:blue",
        label=estilo.rotulo_so_clima,
    )
    eixo_r2.plot(
        r2_por_horizonte.index,
        r2_por_horizonte[CONJUNTO_CLIMA_VETOR],
        "o-",
        color="tab:green",
        label="M1: clima + vetor",
    )
    eixo_r2.axhline(0, color="k", lw=0.8, ls="--")
    eixo_r2.axvspan(
        INICIO_FAIXA_HORIZONTE_LONGO,
        FIM_FAIXA_HORIZONTE_LONGO,
        color="tab:green",
        alpha=estilo.transparencia_faixa,
    )
    eixo_r2.annotate(
        estilo.texto_anotacao,
        estilo.posicao_anotacao,
        fontsize=9,
        color="dimgray",
        ha="center",
    )
    eixo_r2.set_title(estilo.titulo_r2)
    eixo_r2.set_xlabel("semanas à frente")
    eixo_r2.set_ylabel("R²")
    eixo_r2.legend(loc="upper right", fontsize=9)
    eixo_r2.grid(alpha=0.3)

    # --- Quadro da direita: barras mostrando o quanto o erro caiu ---
    eixo_lift = eixos[1]
    cores_das_barras = []
    for valor_de_lift in lift_percentual:
        if valor_de_lift > 0:
            cores_das_barras.append("tab:green")
        else:
            cores_das_barras.append("tab:red")
    eixo_lift.bar(lift_percentual.index, lift_percentual, color=cores_das_barras)
    eixo_lift.axhline(0, color="k", lw=0.8)
    eixo_lift.axvspan(
        INICIO_FAIXA_HORIZONTE_LONGO,
        FIM_FAIXA_HORIZONTE_LONGO,
        color="tab:green",
        alpha=estilo.transparencia_faixa,
    )
    eixo_lift.set_title(estilo.titulo_lift)
    eixo_lift.set_xlabel("semanas à frente")
    eixo_lift.set_ylabel("lift %")
    eixo_lift.grid(alpha=0.3)

    figura.tight_layout()
    figura.savefig(caminho_saida, dpi=110, bbox_inches="tight")
    plt.close(figura)
    return caminho_saida



def plotar_comparacao_casos(resultados: pd.DataFrame, caminho_saida: Path) -> Path:
    """

    Desenha a comparacao de previsao de casos: so-clima contra clima + mosquito.

    Uma linha pra cada modelo, mostrando o quanto ele explica os casos (R2) pra
    cada quantidade de semanas a frente.

    Args:
        resultados: O conteudo de comparacao_casos_resultados.csv (colunas h,
            R2_so_clima, R2_clima_vetor, ganho).
        caminho_saida: Onde salvar a imagem .png.

    Returns:
        O caminho de onde a figura foi salva.

    """
    cor_cinza = "#9b9488"
    cor_verde = "#0e7c7b"
    cor_tinta = "#0f2540"

    figura, eixo = plt.subplots(figsize=(8.6, 4.6))
    eixo.plot(
        resultados["h"], resultados["R2_so_clima"], "s--",
        color=cor_cinza, lw=2.2, ms=6, label="só-clima (estilo literatura)",
    )
    eixo.plot(
        resultados["h"], resultados["R2_clima_vetor"], "o-",
        color=cor_verde, lw=2.6, ms=7, label="clima + vetor (nosso)",
    )
    eixo.axhline(0, color="#c9c2b4", lw=1)
    eixo.set_xlabel("horizonte (semanas à frente)")
    eixo.set_ylabel("R² — previsão de casos")
    eixo.set_title(
        "Mesma POA, mesmas semanas: quem prevê melhor os casos?\n"
        "só-clima × clima+vetor · walk-forward",
        fontsize=13, fontweight="bold", color=cor_tinta, loc="left",
    )
    eixo.set_xticks(list(resultados["h"]))
    eixo.legend(frameon=False)
    eixo.grid(alpha=0.25)
    figura.tight_layout()
    figura.savefig(caminho_saida, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(figura)
    return caminho_saida



def plotar_comparacao_oliveira(resultados: pd.DataFrame, caminho_saida: Path) -> Path:
    """

    Desenha a replica da tarefa do Oliveira: acerto em dizer se os casos vao acelerar.

    Compara, em barras, o jeito da literatura (embaralhar e separar treino/teste)
    com o jeito honesto (treina no passado, preve o futuro), pros dois modelos, e
    marca com uma linha o valor que o trabalho do Oliveira reportou.

    Args:
        resultados: O conteudo de comparacao_oliveira_resultados.csv (uma linha
            por protocolo, com so_clima, clima_vetor e a referencia do Oliveira).
        caminho_saida: Onde salvar a imagem .png.

    Returns:
        O caminho de onde a figura foi salva.

    """
    cor_cinza = "#9b9488"
    cor_verde = "#0e7c7b"
    cor_destaque = "#c25a22"
    cor_tinta = "#0f2540"

    por_protocolo = resultados.set_index("protocolo")
    acerto_split_clima = por_protocolo.loc["split_aleatorio", "so_clima"]
    acerto_split_vetor = por_protocolo.loc["split_aleatorio", "clima_vetor"]
    acerto_honesto_clima = por_protocolo.loc["walk_forward", "so_clima"]
    acerto_honesto_vetor = por_protocolo.loc["walk_forward", "clima_vetor"]
    referencia_oliveira = por_protocolo["referencia_oliveira"].iloc[0]

    rotulos_grupos = ["split aleatório\n(protocolo Oliveira)", "walk-forward\n(honesto)"]
    posicoes = np.arange(2)
    largura = 0.36

    figura, eixo = plt.subplots(figsize=(7.6, 4.6))
    eixo.bar(
        posicoes - largura / 2, [acerto_split_clima, acerto_honesto_clima],
        largura, color=cor_cinza, label="só-clima (estilo literatura)",
    )
    eixo.bar(
        posicoes + largura / 2, [acerto_split_vetor, acerto_honesto_vetor],
        largura, color=cor_verde, label="clima + vetor (nosso)",
    )
    eixo.axhline(
        referencia_oliveira, color=cor_destaque, lw=2, ls=":",
        label=f"Oliveira 2025 ({referencia_oliveira:.2f})",
    )
    eixo.axhline(0.5, color="#c9c2b4", lw=1, ls="--")
    eixo.set_xticks(posicoes)
    eixo.set_xticklabels(rotulos_grupos)
    eixo.set_ylim(0.45, 0.8)
    eixo.set_ylabel("Balanced Accuracy — aceleração de casos")
    eixo.set_title(
        "Réplica da tarefa do Oliveira (POA)\naceleração de casos · LightGBM",
        fontsize=13, fontweight="bold", color=cor_tinta, loc="left",
    )
    eixo.legend(frameon=False, fontsize=10.5)
    eixo.grid(axis="y", alpha=0.25)

    posicoes_das_barras = [
        posicoes[0] - largura / 2, posicoes[0] + largura / 2,
        posicoes[1] - largura / 2, posicoes[1] + largura / 2,
    ]
    valores_das_barras = [
        acerto_split_clima, acerto_split_vetor, acerto_honesto_clima, acerto_honesto_vetor,
    ]
    for posicao_x, valor in zip(posicoes_das_barras, valores_das_barras):
        eixo.text(
            posicao_x, valor + 0.006, f"{valor:.2f}",
            ha="center", fontsize=10, fontweight="bold", color=cor_tinta,
        )

    figura.tight_layout()
    figura.savefig(caminho_saida, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(figura)
    return caminho_saida



# Abre um CSV de resultados; se ele ainda nao existe, avisa e devolve None (a figura e pulada).
def ler_resultado_se_existir(nome_arquivo: str) -> pd.DataFrame | None:
    caminho = settings.PASTA_RESULTADOS / nome_arquivo
    if not caminho.exists():
        print(f"pulando figura (falta {nome_arquivo})")
        return None
    return pd.read_csv(caminho)



def gerar_todas_figuras() -> list[Path]:
    """

    Abre os arquivos CSV com os resultados e desenha todas as figuras dos experimentos.

    So desenha a figura de um experimento que ja foi rodado (se o CSV dele nao
    existe, ele e pulado com um aviso).

    Returns:
        Lista com os caminhos de todas as figuras geradas.

    """
    settings.PASTA_FIGURAS.mkdir(parents=True, exist_ok=True)
    caminhos_gerados = []

    deteccao = ler_resultado_se_existir("deteccao_surto_resultados.csv")
    if deteccao is not None:
        caminhos_gerados.append(
            plotar_deteccao_surto(deteccao, settings.PASTA_FIGURAS / "deteccao_surto.png")
        )

    maturidade = ler_resultado_se_existir("clima_enxuto_maturidade_resultados.csv")
    if maturidade is not None:
        caminhos_gerados.append(
            plotar_lift_do_vetor(
                maturidade, settings.PASTA_FIGURAS / "lift_maturidade.png", ESTILO_LIFT_MATURIDADE
            )
        )

    sem_enso = ler_resultado_se_existir("clima_enxuto_sem_enso_resultados.csv")
    if sem_enso is not None:
        caminhos_gerados.append(
            plotar_lift_do_vetor(
                sem_enso, settings.PASTA_FIGURAS / "lift_sem_enso.png", ESTILO_LIFT_SEM_ENSO
            )
        )

    comparacao_casos = ler_resultado_se_existir("comparacao_casos_resultados.csv")
    if comparacao_casos is not None:
        caminhos_gerados.append(
            plotar_comparacao_casos(comparacao_casos, settings.PASTA_FIGURAS / "comparacao_casos.png")
        )

    comparacao_oliveira = ler_resultado_se_existir("comparacao_oliveira_resultados.csv")
    if comparacao_oliveira is not None:
        caminhos_gerados.append(
            plotar_comparacao_oliveira(
                comparacao_oliveira, settings.PASTA_FIGURAS / "comparacao_oliveira.png"
            )
        )

    return caminhos_gerados
