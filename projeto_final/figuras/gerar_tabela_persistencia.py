"""Gera a tabela suplementar "composto x persistencia" (comparacao exploratoria, Emenda 6, 17/10/2026).

A tabela so formata numeros: nada e recalculado aqui. A conta (MAE, ganho, DM-HLN, Holm) e feita por
`experimentos/composto_x_persistencia.py`, que grava
`resultados/ciencia/composto_x_persistencia/composto_x_persistencia.csv`; este script le esse CSV.

Comparacao NAO pre-declarada, feita depois da avaliacao e registrada como emenda 6. Nada do que a tabela traz
muda os vereditos pre-declarados.

Entrada (SOMENTE LEITURA):
    - `resultados/ciencia/composto_x_persistencia/composto_x_persistencia.csv` (6 horizontes: 1, 2, 3, 4, 8 e 12).
Saida (unica):
    - `entregas/artigo/tabelas/tabelaS_persistencia.tex` (so o ambiente `table`, sem \\section).

Ancoras: `ANCORAS_DAS_LINHAS` traz as celulas esperadas de cada linha, ja formatadas (as da tabela do README de
`analises/2026-10-17_persistencia_exploratorio/`); se qualquer uma divergir, o script PARA com a diferenca e nao
grava a tabela.

Rodar, de dentro de projeto_final/:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B figuras/gerar_tabela_persistencia.py
"""

import logging
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("tabela_persistencia")

# ----------------------------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------------------------
PASTA_DO_PACOTE = Path(__file__).resolve().parents[1]
PASTA_DA_PESQUISA = PASTA_DO_PACOTE.parents[1]

ARQUIVO_DOS_RESULTADOS = (
    PASTA_DO_PACOTE / "resultados" / "ciencia" / "composto_x_persistencia" / "composto_x_persistencia.csv"
)
ARQUIVO_DE_SAIDA = PASTA_DA_PESQUISA / "entregas" / "artigo" / "tabelas" / "tabelaS_persistencia.tex"

CAMINHO_DO_SCRIPT_PARA_O_COMENTARIO = "Meu_Projeto/projeto_final/figuras/gerar_tabela_persistencia.py"
CAMINHO_DA_ENTRADA_PARA_O_COMENTARIO = (
    "Meu_Projeto/projeto_final/resultados/ciencia/composto_x_persistencia/composto_x_persistencia.csv"
)
DATA_DA_GERACAO = "17/10/2026"

# ----------------------------------------------------------------------------------------------
# Definicoes da tabela
# ----------------------------------------------------------------------------------------------
HORIZONTES_DA_TABELA = (1, 2, 3, 4, 8, 12)
HORIZONTES_COM_P_DE_HOLM = (1, 4, 8, 12)

COLUNAS_OBRIGATORIAS_DO_CSV = (
    "h",
    "n",
    "mae_composto",
    "mae_persistencia",
    "ganho_pct_composto",
    "p_dm_hln",
    "p_holm_dm_hln_h1_4_8_12",
)
SEMANAS_DA_JANELA_POR_HORIZONTE = 102

CASAS_DO_MAE = 1
CASAS_DO_GANHO = 1
CASAS_DO_P = 3
CELULA_SEM_VALOR = "---"
MENOR_P_IMPRESSO = 0.001


class LinhaDaTabela(NamedTuple):
    """Celulas de uma linha da tabela, ja formatadas (sem os separadores `&`)."""

    horizonte: str
    mae_do_composto: str
    mae_da_persistencia: str
    ganho_do_composto: str
    p_dm_hln: str
    p_de_holm: str


# Celulas esperadas (calculadas antes, da tabela do README da analise de 17/10/2026), no formato do LaTeX.
ANCORAS_DAS_LINHAS = (
    LinhaDaTabela("1", "102,3", "83,3", "$-$22,9", "0,127", "0,253"),
    LinhaDaTabela("2", "185,7", "153,5", "$-$21,0", "0,349", CELULA_SEM_VALOR),
    LinhaDaTabela("3", "198,4", "214,6", "$+$7,5", "0,703", CELULA_SEM_VALOR),
    LinhaDaTabela("4", "205,7", "279,0", "$+$26,3", "0,222", "0,253"),
    LinhaDaTabela("8", "233,5", "531,0", "$+$56,0", "0,045", "0,155"),
    LinhaDaTabela("12", "260,1", "697,5", "$+$62,7", "0,039", "0,155"),
)


# ==============================================================================================
# Leitura (I/O)
# ==============================================================================================
def ler_resultados(caminho: Path) -> pd.DataFrame:
    """Le o CSV da comparacao com os floats em precisao total.

    Raises:
        FileNotFoundError: Se o arquivo nao existir (rodar antes `experimentos/composto_x_persistencia.py`).
    """
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho}")
    resultados = pd.read_csv(caminho, float_precision="round_trip")
    LOGGER.info("Lido %s: %d linhas.", caminho.name, len(resultados))
    return resultados


def validar_resultados(resultados: pd.DataFrame) -> None:
    """Garante colunas, horizontes, 102 semanas por horizonte e p de Holm so em h = 1, 4, 8 e 12.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se os horizontes, o `n` ou a posicao dos vazios do p de Holm divergirem do esperado.
    """
    colunas_ausentes: list[str] = []
    for nome_da_coluna in COLUNAS_OBRIGATORIAS_DO_CSV:
        if nome_da_coluna not in resultados.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes em {ARQUIVO_DOS_RESULTADOS.name}: {colunas_ausentes}")

    horizontes_do_csv = tuple(int(horizonte) for horizonte in resultados["h"])
    if horizontes_do_csv != HORIZONTES_DA_TABELA:
        raise ValueError(f"Horizontes do CSV {horizontes_do_csv}; esperado {HORIZONTES_DA_TABELA}.")

    semanas_por_horizonte = resultados["n"].to_numpy()
    if not (semanas_por_horizonte == SEMANAS_DA_JANELA_POR_HORIZONTE).all():
        raise ValueError(f"`n` do CSV {semanas_por_horizonte.tolist()}; esperado {SEMANAS_DA_JANELA_POR_HORIZONTE}.")

    for posicao, horizonte in enumerate(HORIZONTES_DA_TABELA):
        tem_p_de_holm = not np.isnan(resultados["p_holm_dm_hln_h1_4_8_12"].iloc[posicao])
        deveria_ter_p_de_holm = horizonte in HORIZONTES_COM_P_DE_HOLM
        if tem_p_de_holm and not deveria_ter_p_de_holm:
            raise ValueError(f"p de Holm presente em h={horizonte}, que fica fora da familia de Holm.")
        if deveria_ter_p_de_holm and not tem_p_de_holm:
            raise ValueError(f"p de Holm ausente em h={horizonte}, que esta na familia de Holm.")


# ==============================================================================================
# Formatacao em LaTeX (pura)
# ==============================================================================================
def formatar_decimal_br(valor: float, casas: int) -> str:
    """Numero positivo com virgula decimal e `casas` casas (os MAE)."""
    return f"{valor:.{casas}f}".replace(".", ",")


def formatar_ganho(valor: float) -> str:
    """Ganho percentual com uma casa, sinal explicito e virgula; o sinal e `$+$` ou `$-$` do LaTeX.

    Um valor que arredonda para 0,0 sai como `$+$0,0` (nao ha `-0,0`).
    """
    valor_arredondado = round(valor, CASAS_DO_GANHO) + 0.0
    texto_do_modulo = formatar_decimal_br(abs(valor_arredondado), CASAS_DO_GANHO)
    if valor_arredondado < 0.0:
        return f"$-${texto_do_modulo}"
    return f"$+${texto_do_modulo}"


def formatar_p(valor: float) -> str:
    """p-valor com tres casas e virgula; abaixo de 0,001 vira `<0,001`; ausente vira travessao."""
    if np.isnan(valor):
        return CELULA_SEM_VALOR
    if round(valor, CASAS_DO_P) < MENOR_P_IMPRESSO:
        return "<0,001"
    return formatar_decimal_br(valor, CASAS_DO_P)


def montar_linha_formatada(linha_do_csv: pd.Series) -> LinhaDaTabela:
    """Formata as seis celulas de uma linha do CSV."""
    return LinhaDaTabela(
        horizonte=str(int(linha_do_csv["h"])),
        mae_do_composto=formatar_decimal_br(float(linha_do_csv["mae_composto"]), CASAS_DO_MAE),
        mae_da_persistencia=formatar_decimal_br(float(linha_do_csv["mae_persistencia"]), CASAS_DO_MAE),
        ganho_do_composto=formatar_ganho(float(linha_do_csv["ganho_pct_composto"])),
        p_dm_hln=formatar_p(float(linha_do_csv["p_dm_hln"])),
        p_de_holm=formatar_p(float(linha_do_csv["p_holm_dm_hln_h1_4_8_12"])),
    )


def montar_linhas_formatadas(resultados: pd.DataFrame) -> list[LinhaDaTabela]:
    """Uma `LinhaDaTabela` por horizonte, na ordem do CSV."""
    linhas_formatadas: list[LinhaDaTabela] = []
    for _, linha_do_csv in resultados.iterrows():
        linhas_formatadas.append(montar_linha_formatada(linha_do_csv))
    return linhas_formatadas


def conferir_ancoras_das_linhas(linhas_formatadas: list[LinhaDaTabela]) -> None:
    """Para se alguma celula divergir das ancoras, listando todas as divergencias.

    Raises:
        ValueError: Se o numero de linhas ou alguma celula divergir.
    """
    if len(linhas_formatadas) != len(ANCORAS_DAS_LINHAS):
        raise ValueError(f"{len(linhas_formatadas)} linhas; esperado {len(ANCORAS_DAS_LINHAS)}.")

    divergencias: list[str] = []
    for linha_medida, ancora in zip(linhas_formatadas, ANCORAS_DAS_LINHAS, strict=True):
        for nome_da_celula in LinhaDaTabela._fields:
            valor_medido = getattr(linha_medida, nome_da_celula)
            valor_esperado = getattr(ancora, nome_da_celula)
            if valor_medido != valor_esperado:
                divergencias.append(
                    f"h={ancora.horizonte} {nome_da_celula}: medido {valor_medido!r}, esperado {valor_esperado!r}"
                )
    if divergencias:
        texto_das_divergencias = "\n  ".join(divergencias)
        raise ValueError(f"Ancoras divergentes ({len(divergencias)}):\n  {texto_das_divergencias}")
    LOGGER.info("Ancoras conferidas: %d linhas, todas iguais.", len(ANCORAS_DAS_LINHAS))


def montar_corpo_da_tabela(linhas_formatadas: list[LinhaDaTabela]) -> str:
    """Linhas do `tabular`: um horizonte por linha, celulas separadas por `&`."""
    linhas_do_tabular: list[str] = []
    for linha in linhas_formatadas:
        celulas = list(linha)
        linhas_do_tabular.append(" & ".join(celulas) + " \\\\")
    return "\n".join(linhas_do_tabular)


def montar_texto_latex(linhas_formatadas: list[LinhaDaTabela]) -> str:
    """Texto completo do `.tex`: comentario de origem e o ambiente `table` (sem \\section)."""
    corpo_da_tabela = montar_corpo_da_tabela(linhas_formatadas)
    return rf"""% Tabela suplementar: comparacao exploratoria do modelo composto com a persistencia (emenda 6).
% GERADA POR SCRIPT em {DATA_DA_GERACAO}: {CAMINHO_DO_SCRIPT_PARA_O_COMENTARIO}. Nao editar a mao; rodar o script de novo.
% Comparacao feita depois da avaliacao e nao pre-declarada (emenda 6, 17/10/2026).
% Entrada: {CAMINHO_DA_ENTRADA_PARA_O_COMENTARIO} (gerado por experimentos/composto_x_persistencia.py).
\begin{{table}}[!htbp]
\centering
\footnotesize
\caption{{Comparação exploratória, não pré-declarada (emenda 6), entre o modelo composto e a persistência nas 102
semanas de avaliação. Ganho: quanto o composto erra a menos que a persistência (negativo: a persistência erra menos).
$p$: teste de Diebold-Mariano com correção HLN; correção de Holm sobre 1, 4, 8 e 12 semanas.}}
\label{{tab:s_persistencia}}
\begin{{tabular}}{{rrrrrr}}
\toprule
Horizonte & \shortstack[r]{{MAE do\\composto}} & \shortstack[r]{{MAE da\\persistência}} & \shortstack[r]{{Ganho do\\composto (\%)}} & \shortstack[r]{{$p$\\(DM-HLN)}} & \shortstack[r]{{$p$ corrigido\\(Holm)}} \\
\midrule
{corpo_da_tabela}
\bottomrule
\end{{tabular}}
\end{{table}}
"""


# ==============================================================================================
# Escrita (I/O)
# ==============================================================================================
def gravar_texto(texto: str, caminho: Path) -> None:
    """Grava o `.tex` em UTF-8 (a pasta de destino precisa existir; reescrever e idempotente).

    Raises:
        FileNotFoundError: Se a pasta de destino nao existir.
    """
    if not caminho.parent.is_dir():
        raise FileNotFoundError(f"Pasta de saida ausente: {caminho.parent}")
    caminho.write_text(texto, encoding="utf-8")
    LOGGER.info("Gravado %s (%d caracteres).", caminho, len(texto))


# ==============================================================================================
# Orquestracao
# ==============================================================================================
def main() -> None:
    """Le o CSV da comparacao, confere as ancoras e grava a tabela."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    resultados = ler_resultados(ARQUIVO_DOS_RESULTADOS)
    validar_resultados(resultados)
    linhas_formatadas = montar_linhas_formatadas(resultados)
    conferir_ancoras_das_linhas(linhas_formatadas)

    texto_latex = montar_texto_latex(linhas_formatadas)
    gravar_texto(texto_latex, ARQUIVO_DE_SAIDA)
    print(texto_latex)


if __name__ == "__main__":
    main()
