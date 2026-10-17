"""Sensibilidade de Newey-West nos 13 testes de h = 1 (Emenda 5 da pre-declaracao, de 17/10/2026).

Em h = 1 o Diebold-Mariano com a correcao de Harvey, Leybourne e Newbold (DM-HLN) usa `h - 1 = 0`
autocovariancias, mas a diferenca semanal de perda tem autocorrelacao de defasagem 1 (~0,44 em
composto x regua sazonal). Esta analise recalcula o p bruto dos 13 testes de h = 1 das familias F1 a F4
com a variancia da media de Newey-West (pesos de Bartlett, L = 4), reaplica Holm dentro de cada familia
e reaplica o criterio do piso de ruido. E SENSIBILIDADE, nao pre-declarada: os vereditos pre-declarados
continuam sendo os do DM-HLN (`resultados/ciencia/estatistica/familias.csv`) e nao mudam.

Nenhum modelo e treinado e nenhum modulo existente e alterado: as previsoes, o pareamento, o DM-HLN, o Holm,
o piso e o veredito vem por importacao de `aedes/` e de `experimentos/testes_familias.py`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B experimentos/sensibilidade_newey_west.py

Saidas em `resultados/ciencia/sensibilidade_newey_west/`: `sensibilidade.csv`, `README.md`, `sensibilidade.log`.
"""

import dataclasses
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats

# O script e chamado pelo caminho do arquivo (nao por `-m`), entao a raiz do projeto precisa entrar no
# caminho de importacao para que `aedes` e `experimentos` sejam encontrados.
PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
if str(PASTA_DO_PROJETO) not in sys.path:
    sys.path.insert(0, str(PASTA_DO_PROJETO))

from aedes.configuracao import CONFIGURACAO_AVALIACAO  # noqa: E402
from aedes.estatistica import (  # noqa: E402
    calcular_autocovariancias,
    corrigir_por_holm,
    diebold_mariano_hln,
    parear_por_data_alvo,
)
from aedes.familias import (  # noqa: E402
    DefinicaoDoTeste,
    decidir_veredito,
    montar_definicoes_das_familias,
)
from aedes.metricas import COLUNA_DO_REAL, recortar_janela_de_avaliacao  # noqa: E402
from experimentos.comum_ciencia import PASTA_DA_CIENCIA, RegistradorDeLog  # noqa: E402
from experimentos.e3_composto import (  # noqa: E402
    JANELA_PRIMARIA,
    exigir_travas_da_e2_aprovadas,
    ler_previsoes_da_e2,
)
from experimentos.testes_familias import (  # noqa: E402
    CAMINHO_DA_TABELA_DE_FAMILIAS,
    conferir_real_da_regua_contra_a_e2,
    ler_composto_primario_na_janela,
    ler_piso_de_ruido,
    montar_previsoes_da_regua_sazonal,
    montar_previsoes_por_candidato,
)

PASTA_DE_SAIDA = PASTA_DA_CIENCIA / "sensibilidade_newey_west"
CAMINHO_DA_TABELA_DE_SENSIBILIDADE = PASTA_DE_SAIDA / "sensibilidade.csv"
CAMINHO_DO_README = PASTA_DE_SAIDA / "README.md"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "sensibilidade.log")

HORIZONTE_DA_SENSIBILIDADE = 1
LARGURA_DA_JANELA_DE_NEWEY_WEST = 4
QUANTIDADE_DE_TESTES_EM_H1 = 13
TOLERANCIA_DA_REPRODUCAO = 1e-12
TOLERANCIA_DO_DELTA = 1e-9

# Ancora exploratoria (composto N = 13 x regua sazonal, h = 1), vista antes da Emenda 5.
ANCORA_ACF1 = 0.44
ANCORA_P_NEWEY_WEST = 0.021
CASAS_DA_ANCORA_ACF1 = 2
CASAS_DA_ANCORA_P_NEWEY_WEST = 3
NOME_DO_CANDIDATO_DA_ANCORA = "composto_N13"
NOME_DO_COMPARADOR_DA_ANCORA = "regua_sazonal"

COLUNAS_DA_TABELA_DE_SENSIBILIDADE = (
    "familia",
    "A",
    "B",
    "n",
    "delta",
    "acf1",
    "p_dm_hln",
    "p_holm_dm_hln",
    "veredito_pre_declarado",
    "p_newey_west",
    "p_holm_sensibilidade",
    "veredito_sensibilidade",
)


@dataclasses.dataclass(frozen=True)
class ResultadoNeweyWest:
    """Teste t da media da diferenca de perda com a variancia de Newey-West (sem a correcao HLN).

    Attributes:
        n: Numero de pares.
        media_das_diferencas: `dbar`.
        variancia: `V`, variancia da media (Bartlett, L defasagens).
        estatistica: `dbar / sqrt(V)`.
        p_bilateral: p-valor bilateral pela t de Student com `n - 1` graus de liberdade.
        acf1: Autocorrelacao amostral de defasagem 1, `gamma_1 / gamma_0`.
    """

    n: int
    media_das_diferencas: float
    variancia: float
    estatistica: float
    p_bilateral: float
    acf1: float


def reconstruir_diferenca_de_perda(previsoes_a: pd.DataFrame, previsoes_b: pd.DataFrame) -> np.ndarray:
    """`d_t = |e_B,t| - |e_A,t|` na serie pareada por `data_alvo`, exatamente como `comparar_pareado`.

    Positivo quer dizer que o candidato A erra menos que o comparador B naquela semana.

    Args:
        previsoes_a: Previsoes do candidato A (`data_alvo`, `real`, `previsto`), um horizonte.
        previsoes_b: Previsoes do comparador B, mesmo horizonte.

    Returns:
        Vetor `d_t` ordenado por `data_alvo`.
    """
    pareado = parear_por_data_alvo(previsoes_a, previsoes_b)
    valores_reais = pareado[COLUNA_DO_REAL].to_numpy(dtype=float)
    previsto_a = pareado["previsto_a"].to_numpy(dtype=float)
    previsto_b = pareado["previsto_b"].to_numpy(dtype=float)
    erros_absolutos_a = np.abs(valores_reais - previsto_a)
    erros_absolutos_b = np.abs(valores_reais - previsto_b)
    return erros_absolutos_b - erros_absolutos_a


def calcular_teste_de_newey_west(diferencas_de_perda: np.ndarray, largura_da_janela: int) -> ResultadoNeweyWest:
    """Teste da media de `d_t` com a variancia de Newey-West (Bartlett) e t de Student, bilateral.

    `V = [gamma_0 + 2 * soma_{k=1}^{L} (1 - k/(L+1)) * gamma_k] / n`, com
    `gamma_k = (1/n) * soma_t (d_t - dbar)(d_{t-k} - dbar)` (divide por `n`, como no DM-HLN).
    Estatistica `dbar / sqrt(V)` comparada a t de Student com `n - 1` graus de liberdade. Nao aplica
    a correcao HLN. Os pesos de Bartlett mantem `V` positivo, exceto se `d_t` for constante.

    Args:
        diferencas_de_perda: Serie `d_t` em ordem cronologica, sem ausente nem infinito.
        largura_da_janela: L, numero de autocovariancias alem da de defasagem 0 (4).

    Returns:
        O `ResultadoNeweyWest`.

    Raises:
        ValueError: Se houver ausente ou infinito, se `L + 1 > n` ou se `V` nao for positiva.
    """
    diferencas = np.asarray(diferencas_de_perda, dtype=float)
    if diferencas.ndim != 1 or not np.isfinite(diferencas).all():
        raise ValueError("diferencas_de_perda deve ser 1-D, sem ausente nem infinito.")
    quantidade_de_pares = len(diferencas)
    quantidade_de_autocovariancias = largura_da_janela + 1
    if quantidade_de_autocovariancias > quantidade_de_pares:
        raise ValueError(f"n={quantidade_de_pares} insuficiente para L={largura_da_janela}.")

    media = float(diferencas.mean())
    autocovariancias = calcular_autocovariancias(diferencas, quantidade_de_autocovariancias)

    soma_ponderada = 0.0
    for defasagem in range(1, quantidade_de_autocovariancias):
        peso_de_bartlett = 1.0 - defasagem / quantidade_de_autocovariancias
        soma_ponderada += peso_de_bartlett * autocovariancias[defasagem]
    variancia_bruta = autocovariancias[0] + 2.0 * soma_ponderada
    variancia = float(variancia_bruta / quantidade_de_pares)
    if variancia <= 0.0:
        raise ValueError("Variancia de Newey-West nao positiva (d_t constante?).")

    estatistica = media / np.sqrt(variancia)
    graus_de_liberdade = quantidade_de_pares - 1
    p_bilateral = float(2.0 * stats.t.sf(abs(estatistica), df=graus_de_liberdade))
    acf1 = float(autocovariancias[1] / autocovariancias[0])
    return ResultadoNeweyWest(
        n=quantidade_de_pares,
        media_das_diferencas=media,
        variancia=variancia,
        estatistica=float(estatistica),
        p_bilateral=p_bilateral,
        acf1=acf1,
    )


def localizar_linha_da_familia(
    tabela_de_familias: pd.DataFrame,
    definicao: DefinicaoDoTeste,
) -> pd.Series:
    """Linha de `familias.csv` do teste (familia, h, A, B).

    Raises:
        ValueError: Se a linha nao existir ou nao for unica.
    """
    e_da_familia = tabela_de_familias["familia"] == definicao.familia
    e_do_horizonte = tabela_de_familias["h"] == definicao.horizonte
    e_do_candidato = tabela_de_familias["A"] == definicao.nome_a
    e_do_comparador = tabela_de_familias["B"] == definicao.nome_b
    linhas = tabela_de_familias.loc[e_da_familia & e_do_horizonte & e_do_candidato & e_do_comparador]
    if len(linhas) != 1:
        raise ValueError(f"{len(linhas)} linhas em familias.csv para {definicao}.")
    return linhas.iloc[0]


def conferir_reproducao_do_dm_hln(
    definicao: DefinicaoDoTeste,
    linha_do_csv: pd.Series,
    diferencas_de_perda: np.ndarray,
) -> float:
    """Trava (a): reproduz n, delta, DM-HLN e p bruto de `familias.csv` com diferenca < 1e-12.

    Args:
        definicao: O teste.
        linha_do_csv: A linha correspondente de `familias.csv`.
        diferencas_de_perda: `d_t` reconstruida.

    Returns:
        A maior diferenca absoluta entre o recalculado e o CSV (DM-HLN e p bruto).

    Raises:
        RuntimeError: Se `n`, `delta`, o DM-HLN ou o p bruto nao reproduzirem.
    """
    teste = diebold_mariano_hln(diferencas_de_perda, definicao.horizonte)
    delta_recalculado = float(diferencas_de_perda.mean())
    diferenca_do_dm = abs(teste.dm_hln - float(linha_do_csv["dm_hln"]))
    diferenca_do_p = abs(teste.p_bilateral - float(linha_do_csv["p_bruto"]))
    diferenca_do_delta = abs(delta_recalculado - float(linha_do_csv["delta"]))

    if teste.n != int(linha_do_csv["n"]):
        raise RuntimeError(f"n difere em {definicao}: {teste.n} contra {linha_do_csv['n']}.")
    if diferenca_do_delta > TOLERANCIA_DO_DELTA:
        raise RuntimeError(f"delta difere em {definicao}: {diferenca_do_delta}.")
    if diferenca_do_dm >= TOLERANCIA_DA_REPRODUCAO or diferenca_do_p >= TOLERANCIA_DA_REPRODUCAO:
        raise RuntimeError(f"DM-HLN nao reproduz em {definicao}: dif DM={diferenca_do_dm}, dif p={diferenca_do_p}.")
    return max(diferenca_do_dm, diferenca_do_p)


def conferir_holm_do_csv(tabela_de_familias: pd.DataFrame) -> float:
    """Confere que o Holm reaplicado sobre o `p_bruto` de `familias.csv` reproduz o `p_holm` do CSV.

    Raises:
        RuntimeError: Se alguma familia divergir em 1e-12 ou mais.

    Returns:
        A maior diferenca absoluta encontrada.
    """
    maior_diferenca = 0.0
    for familia in sorted(tabela_de_familias["familia"].unique()):
        da_familia = tabela_de_familias.loc[tabela_de_familias["familia"] == familia]
        p_holm_recalculado = corrigir_por_holm(da_familia["p_bruto"].to_numpy(dtype=float))
        diferencas = np.abs(p_holm_recalculado - da_familia["p_holm"].to_numpy(dtype=float))
        maior_diferenca = max(maior_diferenca, float(diferencas.max()))
    if maior_diferenca >= TOLERANCIA_DA_REPRODUCAO:
        raise RuntimeError(f"Holm do CSV nao reproduz: maior diferenca {maior_diferenca}.")
    return maior_diferenca


def aplicar_holm_da_sensibilidade(
    tabela_de_familias: pd.DataFrame,
    p_newey_west_por_posicao: dict[int, float],
) -> pd.Series:
    """Holm dentro de cada familia com o p de Newey-West nos testes de h = 1 e o p bruto do DM-HLN nos demais.

    Args:
        tabela_de_familias: `familias.csv` inteiro (52 linhas), na ordem original.
        p_newey_west_por_posicao: Posicao (rotulo do indice) da linha de h = 1 -> p bruto de Newey-West.

    Returns:
        Serie com o p de Holm da sensibilidade, indexada como `tabela_de_familias`.
    """
    p_para_holm = tabela_de_familias["p_bruto"].astype(float).copy()
    for posicao, p_newey_west in p_newey_west_por_posicao.items():
        p_para_holm.loc[posicao] = p_newey_west

    p_holm_da_sensibilidade = pd.Series(np.nan, index=tabela_de_familias.index, dtype=float)
    for familia in tabela_de_familias["familia"].unique():
        e_da_familia = tabela_de_familias["familia"] == familia
        p_da_familia = p_para_holm.loc[e_da_familia].to_numpy(dtype=float)
        p_holm_da_sensibilidade.loc[e_da_familia] = corrigir_por_holm(p_da_familia)
    return p_holm_da_sensibilidade


def montar_tabela_de_sensibilidade(
    definicoes_de_h1: list[DefinicaoDoTeste],
    tabela_de_familias: pd.DataFrame,
    previsoes_por_candidato: dict[tuple[str, int], pd.DataFrame],
) -> pd.DataFrame:
    """Calcula ACF1, DM-HLN conferido, Newey-West, Holm da sensibilidade e vereditos dos 13 testes de h = 1.

    Args:
        definicoes_de_h1: Os 13 testes de h = 1 (F1 a F4), na ordem de `familias.csv`.
        tabela_de_familias: `familias.csv` inteiro.
        previsoes_por_candidato: `(nome, h) -> previsoes` (de `montar_previsoes_por_candidato`).

    Returns:
        DataFrame com `COLUNAS_DA_TABELA_DE_SENSIBILIDADE`, uma linha por teste de h = 1.

    Raises:
        RuntimeError: Se o DM-HLN de algum teste nao reproduzir o CSV.
    """
    resultados_por_posicao: dict[int, ResultadoNeweyWest] = {}
    linhas_do_csv_por_posicao: dict[int, pd.Series] = {}
    maior_diferenca_de_reproducao = 0.0

    for definicao in definicoes_de_h1:
        linha_do_csv = localizar_linha_da_familia(tabela_de_familias, definicao)
        posicao = int(linha_do_csv.name)
        previsoes_a = previsoes_por_candidato[(definicao.nome_a, definicao.horizonte)]
        previsoes_b = previsoes_por_candidato[(definicao.nome_b, definicao.horizonte)]
        diferencas_de_perda = reconstruir_diferenca_de_perda(previsoes_a, previsoes_b)

        diferenca_de_reproducao = conferir_reproducao_do_dm_hln(definicao, linha_do_csv, diferencas_de_perda)
        maior_diferenca_de_reproducao = max(maior_diferenca_de_reproducao, diferenca_de_reproducao)

        resultados_por_posicao[posicao] = calcular_teste_de_newey_west(
            diferencas_de_perda, LARGURA_DA_JANELA_DE_NEWEY_WEST
        )
        linhas_do_csv_por_posicao[posicao] = linha_do_csv

    REGISTRADOR.registrar(
        f"trava (a) aprovada: DM-HLN e p bruto dos {len(definicoes_de_h1)} testes de h=1 reproduzem familias.csv; "
        f"maior diferenca = {maior_diferenca_de_reproducao:.3e}"
    )

    p_newey_west_por_posicao: dict[int, float] = {}
    for posicao, resultado in resultados_por_posicao.items():
        p_newey_west_por_posicao[posicao] = resultado.p_bilateral
    p_holm_da_sensibilidade = aplicar_holm_da_sensibilidade(tabela_de_familias, p_newey_west_por_posicao)

    linhas_da_tabela: list[dict[str, object]] = []
    for posicao, resultado in resultados_por_posicao.items():
        linha_do_csv = linhas_do_csv_por_posicao[posicao]
        delta = float(linha_do_csv["delta"])
        limiar_do_piso = float(linha_do_csv["limiar_piso"])
        p_holm_da_sensibilidade_do_teste = float(p_holm_da_sensibilidade.loc[posicao])
        veredito_da_sensibilidade = decidir_veredito(p_holm_da_sensibilidade_do_teste, delta, limiar_do_piso)
        linhas_da_tabela.append(
            {
                "familia": linha_do_csv["familia"],
                "A": linha_do_csv["A"],
                "B": linha_do_csv["B"],
                "n": int(linha_do_csv["n"]),
                "delta": delta,
                "acf1": resultado.acf1,
                "p_dm_hln": float(linha_do_csv["p_bruto"]),
                "p_holm_dm_hln": float(linha_do_csv["p_holm"]),
                "veredito_pre_declarado": linha_do_csv["veredito"],
                "p_newey_west": resultado.p_bilateral,
                "p_holm_sensibilidade": p_holm_da_sensibilidade_do_teste,
                "veredito_sensibilidade": veredito_da_sensibilidade,
            }
        )
    return pd.DataFrame(linhas_da_tabela, columns=list(COLUNAS_DA_TABELA_DE_SENSIBILIDADE))


def conferir_ancora_exploratoria(tabela_de_sensibilidade: pd.DataFrame) -> tuple[float, float, bool]:
    """Compara composto N=13 x regua sazonal (h = 1) com a ancora exploratoria (ACF1 ~ 0,44, p NW ~ 0,021).

    Returns:
        `(acf1, p_newey_west, bate)`; `bate` e verdadeiro se ambos arredondam para a ancora.

    Raises:
        ValueError: Se o teste da ancora nao estiver na tabela.
    """
    e_do_candidato = tabela_de_sensibilidade["A"] == NOME_DO_CANDIDATO_DA_ANCORA
    e_do_comparador = tabela_de_sensibilidade["B"] == NOME_DO_COMPARADOR_DA_ANCORA
    linhas = tabela_de_sensibilidade.loc[e_do_candidato & e_do_comparador]
    if len(linhas) != 1:
        raise ValueError("Teste da ancora (composto x regua, h=1) ausente ou repetido.")
    acf1 = float(linhas["acf1"].iloc[0])
    p_newey_west = float(linhas["p_newey_west"].iloc[0])
    acf1_bate = round(acf1, CASAS_DA_ANCORA_ACF1) == ANCORA_ACF1
    p_bate = round(p_newey_west, CASAS_DA_ANCORA_P_NEWEY_WEST) == ANCORA_P_NEWEY_WEST
    return acf1, p_newey_west, bool(acf1_bate and p_bate)


def formatar_p(valor: float) -> str:
    """p-valor para a tabela do README: quatro casas decimais, ou `<0,0001`."""
    if valor < 0.0001:
        return "<0,0001"
    return f"{valor:.4f}".replace(".", ",")


def montar_texto_do_readme(
    tabela_de_sensibilidade: pd.DataFrame,
    acf1_da_ancora: float,
    p_da_ancora: float,
    maior_diferenca_do_holm_do_csv: float,
) -> str:
    """Texto do README: o que e, Emenda 5, metodo, ancoras, tabela dos 13 testes e vereditos que mudam."""
    linhas_da_tabela: list[str] = []
    vereditos_que_mudam: list[str] = []
    for _, linha in tabela_de_sensibilidade.iterrows():
        veredito_antes = str(linha["veredito_pre_declarado"])
        veredito_depois = str(linha["veredito_sensibilidade"])
        teste = f"{linha['A']} x {linha['B']}"
        acf1_formatada = f"{linha['acf1']:.3f}".replace(".", ",")
        linhas_da_tabela.append(
            f"| {linha['familia']} | {teste} | {acf1_formatada}"
            + f" | {formatar_p(linha['p_dm_hln'])} → {formatar_p(linha['p_newey_west'])}"
            + f" | {formatar_p(linha['p_holm_dm_hln'])} → {formatar_p(linha['p_holm_sensibilidade'])}"
            + f" | {veredito_antes} → {veredito_depois} |"
        )
        if veredito_antes != veredito_depois:
            vereditos_que_mudam.append(f"- **{linha['familia']} {teste}**: {veredito_antes} → {veredito_depois}.")

    if len(vereditos_que_mudam) == 0:
        texto_dos_que_mudam = "**Nenhum dos 13 vereditos muda.**"
    else:
        texto_dos_que_mudam = (
            f"**{len(vereditos_que_mudam)} de 13 vereditos mudam** (sensibilidade; o pré-declarado não muda):\n\n"
            + "\n".join(vereditos_que_mudam)
        )

    cabecalho_da_tabela = (
        "| Família | A × B | ACF1 da diferença | p bruto: DM-HLN → Newey-West "
        "| p de Holm: pré-declarado → sensibilidade | Veredito: antes → depois |\n"
        "|---|---|---|---|---|---|"
    )
    corpo_da_tabela = "\n".join(linhas_da_tabela)

    return f"""# Sensibilidade de Newey-West nos 13 testes de h = 1

Gerado por `experimentos/sensibilidade_newey_west.py` (não editar à mão; refazer pelo script).

## O que é

- **Sensibilidade, não pré-declarada**, escrita pela **Emenda 5** da pré-declaração
  (`analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`, 17/10/2026, Vinicius, depois de ver os resultados).
- **Por que existe:** em h = 1 o DM-HLN usa h − 1 = 0 autocovariâncias, mas a diferença semanal de perda tem autocorrelação de
  defasagem 1 (ACF1 ≈ 0,44 em composto × régua). Um revisor da V1 apontou isso.
- **Uso:** só no material suplementar (S3). Os vereditos **pré-declarados continuam sendo os do DM-HLN** (`familias.csv`) e
  não mudam no artigo.
- Nenhum modelo foi treinado; nenhum módulo ou resultado existente foi alterado.

## Método (Emenda 5)

- **Mesma diferença de perda pareada** de `testes_familias.py`: `d_t = |e_B,t| − |e_A,t|`, pareada por `data_alvo`
  (`parear_por_data_alvo`); positivo = A erra menos.
- **Variância da média de Newey-West** com pesos de Bartlett e **L = 4** (regra floor(4·(n/100)^(2/9)) com n ≈ 102):
  V = [γ₀ + 2 Σₖ₌₁⁴ (1 − k/5) γₖ] / n, com γₖ = Σₜ (dₜ − d̄)(dₜ₊ₖ − d̄) / n.
- **Estatística** d̄ / √V comparada à **t de Student com n − 1 g.l., bilateral**, **sem** a correção HLN.
- **Holm** reaplicado dentro de cada família (F1 a F4 inteiras, 12 ou 16 testes): p de Newey-West nos testes de h = 1 e o p bruto
  do DM-HLN (de `familias.csv`) nos de h = 4, 8 e 12.
- **Critério do piso mantido:** |Δ| > `limiar_piso` de `familias.csv` (2 × piso de ruído) e p de Holm < 0,05.
  Veredito: "A melhor", "B melhor" (aqui, "A pior") ou "sem evidencia".
- **ACF1** = γ₁ / γ₀ (mesma divisão por n do DM-HLN).

## Números-âncora

- **Reprodução do DM-HLN:** estatística e p bruto dos 13 testes de h = 1 recalculados reproduzem `familias.csv` com diferença
  < 1e-12 (trava (a); o script para se falhar). n e Δ também conferidos.
- **Holm do CSV:** reaplicar Holm ao `p_bruto` de `familias.csv` reproduz o `p_holm` (diferença máxima {maior_diferenca_do_holm_do_csv:.1e}).
- **Âncora exploratória (composto N=13 × régua sazonal, h = 1):** ACF1 ≈ 0,44 e p bruto Newey-West ≈ 0,021.
  Obtido: **ACF1 = {acf1_da_ancora:.4f}** e **p Newey-West = {p_da_ancora:.4f}**.

## Os 13 testes de h = 1

{cabecalho_da_tabela}
{corpo_da_tabela}

Valores completos (precisão total) em `sensibilidade.csv`.

## Quais vereditos mudam

{texto_dos_que_mudam}

## Limites

- **Fato:** o p de Newey-West com L = 4 é um estimador entre vários; o revisor obteve ≈ 0,10 com outro estimador no teste de
  composto × régua (conta exploratória, antes da emenda). O método fixado aqui é UM, relatado como sensibilidade.
- **Fato:** o ACF1 e o p dependem de n ≈ 102 semanas; L fixo em 4 para todos os testes (inclusive n = 109 em F2).
- A leitura do artigo continua sendo a pré-declarada; esta tabela só mostra quanto ela depende de ignorar a autocorrelação em h = 1.
"""


def main() -> int:
    """Reproduz o DM-HLN de h = 1, calcula Newey-West, reaplica Holm e o piso e grava CSV e README.

    Returns:
        0 se terminou; uma excecao interrompe a analise (nada parcial e gravado).
    """
    exigir_travas_da_e2_aprovadas()
    tabela_de_familias = pd.read_csv(CAMINHO_DA_TABELA_DE_FAMILIAS, float_precision="round_trip")
    maior_diferenca_do_holm_do_csv = conferir_holm_do_csv(tabela_de_familias)

    previsoes_da_e2 = ler_previsoes_da_e2()
    previsoes_da_e2_na_janela = recortar_janela_de_avaliacao(previsoes_da_e2, CONFIGURACAO_AVALIACAO)
    composto_na_janela = ler_composto_primario_na_janela()
    regua = montar_previsoes_da_regua_sazonal(previsoes_da_e2_na_janela)
    conferir_real_da_regua_contra_a_e2(regua, previsoes_da_e2_na_janela)
    ler_piso_de_ruido()  # so garante que o piso existe; o limiar usado vem de `familias.csv`
    REGISTRADOR.registrar(
        f"inicio: familias.csv={len(tabela_de_familias)} linhas; E2 na janela={len(previsoes_da_e2_na_janela)}; "
        f"composto N={JANELA_PRIMARIA} na janela={len(composto_na_janela)}; regua={len(regua)}; "
        f"Holm do CSV reproduzido (dif max {maior_diferenca_do_holm_do_csv:.1e})"
    )

    todas_as_definicoes = montar_definicoes_das_familias()
    definicoes_de_h1: list[DefinicaoDoTeste] = []
    for definicao in todas_as_definicoes:
        if definicao.horizonte == HORIZONTE_DA_SENSIBILIDADE:
            definicoes_de_h1.append(definicao)
    if len(definicoes_de_h1) != QUANTIDADE_DE_TESTES_EM_H1:
        raise RuntimeError(f"{len(definicoes_de_h1)} testes de h=1 montados; esperado {QUANTIDADE_DE_TESTES_EM_H1}.")

    previsoes_por_candidato = montar_previsoes_por_candidato(
        definicoes_de_h1, previsoes_da_e2_na_janela, composto_na_janela, regua
    )
    tabela_de_sensibilidade = montar_tabela_de_sensibilidade(
        definicoes_de_h1, tabela_de_familias, previsoes_por_candidato
    )

    acf1_da_ancora, p_da_ancora, ancora_bate = conferir_ancora_exploratoria(tabela_de_sensibilidade)
    REGISTRADOR.registrar(
        f"ancora exploratoria (composto x regua, h=1): ACF1={acf1_da_ancora:.6f} (esperado ~{ANCORA_ACF1}); "
        f"p Newey-West={p_da_ancora:.6f} (esperado ~{ANCORA_P_NEWEY_WEST}); bate={ancora_bate}"
    )
    if not ancora_bate:
        raise RuntimeError("A ancora exploratoria nao bate; investigar antes de gravar qualquer saida.")

    PASTA_DE_SAIDA.mkdir(parents=True, exist_ok=True)
    tabela_de_sensibilidade.to_csv(CAMINHO_DA_TABELA_DE_SENSIBILIDADE, index=False)
    texto_do_readme = montar_texto_do_readme(
        tabela_de_sensibilidade, acf1_da_ancora, p_da_ancora, maior_diferenca_do_holm_do_csv
    )
    CAMINHO_DO_README.write_text(texto_do_readme, encoding="utf-8")

    quantidade_de_vereditos_que_mudam = int(
        (tabela_de_sensibilidade["veredito_pre_declarado"] != tabela_de_sensibilidade["veredito_sensibilidade"]).sum()
    )
    REGISTRADOR.registrar(
        f"fim: {len(tabela_de_sensibilidade)} testes em {CAMINHO_DA_TABELA_DE_SENSIBILIDADE.name}; "
        f"vereditos que mudam={quantidade_de_vereditos_que_mudam}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
