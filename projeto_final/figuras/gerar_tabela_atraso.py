"""Gera a Tabela S5 (atraso de encerramento por ano) a partir do CSV certificado de 10/10/2026.

Le: analises/2026-10-10_atraso_de_encerramento/saidas/atraso_por_ano.csv (universo notificacao).
Escreve: entregas/artigo/tabelas/tabelaS5_atraso.tex
"""
from pathlib import Path

import pandas as pd

RAIZ = Path("/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa")
CSV = RAIZ / "Meu_Projeto/analises/2026-10-10_atraso_de_encerramento/saidas/atraso_por_ano.csv"
SAIDA = RAIZ / "entregas/artigo/tabelas/tabelaS5_atraso.tex"

ROTULOS_ANOS = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]
ROTULO_AGREGADO = "2018-2024"


def decimal_br(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def inteiro_siunitx(valor: int) -> str:
    return f"\\num{{{int(valor)}}}"


def linha_tabela(rotulo: str, linha: pd.Series, negrito: bool = False) -> str:
    celulas = [
        rotulo.replace("-", "--"),
        inteiro_siunitx(linha["n_validos"]),
        decimal_br(linha["mediana_semanas"]),
        decimal_br(linha["p75_semanas"]),
        decimal_br(linha["p90_semanas"]),
        decimal_br(100 * linha["frac_ate_12sem_validos"]) + "\\%",
    ]
    if negrito:
        celulas = [f"\\textbf{{{c}}}" for c in celulas]
    return " & ".join(celulas) + " \\\\"


tabela = pd.read_csv(CSV, dtype={"ano_dos_sintomas": str})
tabela = tabela[tabela["universo"] == "notificacao"].set_index("ano_dos_sintomas")

# Ancoras certificadas
agregado = tabela.loc[ROTULO_AGREGADO]
assert round(agregado["mediana_semanas"], 1) == 20.6, agregado["mediana_semanas"]
assert round(100 * agregado["frac_ate_12sem_validos"], 1) == 39.5
assert round(100 * tabela.loc["2024", "frac_ate_12sem_validos"], 1) == 15.9

linhas = [linha_tabela(a, tabela.loc[a]) for a in ROTULOS_ANOS[:-1]]
linhas.append(linha_tabela(ROTULO_AGREGADO, agregado, negrito=True))
linhas.append(linha_tabela("2025", tabela.loc["2025"]))
# ordem: 2019-2024, agregado, 2025 (a parte, censurado)

corpo = "\n".join(linhas)
n_2018 = int(tabela.loc["2018", "n_validos"])

texto = rf"""\section*{{S5. Atraso de encerramento das fichas}}
\label{{sec:s5_atraso}}

A Tabela~\ref{{tab:s_atraso}} mede o intervalo entre o início dos sintomas e o encerramento da ficha de notificação, em
semanas, nos casos confirmados de dengue notificados em Porto Alegre, a partir dos arquivos públicos do Sinan. O ano é o
do início dos sintomas. A última coluna traz a fração dos casos já encerrados até 12 semanas depois dos sintomas.

\begin{{table}}[!htbp]
\centering
\small
\caption{{Atraso entre o início dos sintomas e o encerramento da ficha, em semanas, nos casos confirmados notificados em
Porto Alegre (município de notificação; arquivos públicos do Sinan). Casos: fichas com datas válidas. ``Até 12 sem.'':
fração encerrada até 12 semanas após os sintomas. A linha 2018--2024 agrega todos os anos de 2018 a 2024, incluindo
{n_2018} casos de 2018, omitidos da lista por ano. A linha de 2025 fica à parte porque o arquivo desse ano foi exportado
em 31/03/2026, e as fichas de 2025 ainda podiam estar abertas.}}
\label{{tab:s_atraso}}
\begin{{tabular}}{{lrrrrr}}
\toprule
Ano dos sintomas & Casos & Mediana & P75 & P90 & Até 12 sem. \\
\midrule
{corpo}
\bottomrule
\end{{tabular}}
\end{{table}}
"""
SAIDA.write_text(texto, encoding="utf-8")
print(texto)
