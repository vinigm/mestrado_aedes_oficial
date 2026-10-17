"""Gera a Tabela 1 do artigo (fontes de dados e as 22 variáveis do modelo, por bloco) em LaTeX.

O que faz: lê a configuração do pacote (`aedes.configuracao`) e a `dados/tabela_final.csv` certificada, e escreve
`entregas/artigo/tabelas/tabela1_variaveis.tex` no mesmo formato da versão preliminar de 10/10/2026 (escrita à mão).

O que vem da configuração (nada de memória):
    - os nomes das 22 variáveis e a quantidade de cada bloco (casos C, meteorologia M, vetor V, calendário K);
    - as defasagens e a janela da média móvel de casos e do vetor;
    - as colunas de clima congeladas e as defasagens de cada uma.

O que vem dos dados:
    - o período de cada fonte: primeira e última semana com valor não ausente, no recorte que o modelo usa.

Recorte do modelo (decisão registrada em LEIAME_figura1_tabela1.md): da primeira semana com caso confirmado
(18/02/2018) até a última semana de casos que sobrevive ao corte de maturidade (01/02/2026), que é também a última
semana-alvo avaliada. Antes de 18/02/2018 o modelo não tem caso (nenhuma linha da matriz chega a existir), e depois de
01/02/2026 as semanas foram descartadas da avaliação.

Se a contagem de variáveis por bloco ou o total divergir do esperado (6 + 6 + 6 + 4 = 22), o script PARA: não força.

Rodar, de qualquer pasta:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B figuras/gerar_tabela1.py
"""

import dataclasses
import sys
import textwrap
from pathlib import Path

import pandas as pd

PASTA_DO_PACOTE = Path(__file__).resolve().parents[1]
# O script e rodado pelo caminho do arquivo; sem isto o pacote `aedes` nao seria encontrado.
sys.path.insert(0, str(PASTA_DO_PACOTE))

from aedes.configuracao import (  # noqa: E402
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    ConfiguracaoVariaveis,
    nome_da_variavel_defasada,
)
from aedes.dados import (  # noqa: E402
    aplicar_corte_de_maturidade,
    montar_tabela_a_partir_dos_bytes,
    obter_ultima_semana_com_caso,
)

# ----------------------------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------------------------
ARQUIVO_DA_TABELA = PASTA_DO_PACOTE / "dados" / "tabela_final.csv"
PASTA_DO_PESQUISA = PASTA_DO_PACOTE.parents[1]
ARQUIVO_DE_SAIDA = PASTA_DO_PESQUISA / "entregas" / "artigo" / "tabelas" / "tabela1_variaveis.tex"
DATA_DE_GERACAO = "16/10/2026"

# ----------------------------------------------------------------------------------------------
# Ancoras (calculadas antes; se divergirem, o script PARA e nao forca nada)
# ----------------------------------------------------------------------------------------------
TOTAL_DE_VARIAVEIS_ESPERADO = 22
VARIAVEIS_POR_BLOCO_ESPERADAS = {"C": 6, "M": 6, "V": 6, "K": 4}
LARGURA_DA_LINHA_NO_ARQUIVO = 120

# ----------------------------------------------------------------------------------------------
# Rotulos de apresentacao (texto do artigo; a ORDEM do dicionario e a ordem de leitura na tabela)
# ----------------------------------------------------------------------------------------------
ROTULO_DA_COLUNA_DE_CLIMA = {
    "temp_media": "temperatura média",
    "temp_max": "temperatura máxima",
    "umid_media": "umidade relativa média",
    "pressao_media": "pressão média",
}
NOMES_DOS_MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")

FONTE_DOS_CASOS = (
    "Sinan, casos confirmados notificados em Porto Alegre, por semana de início dos sintomas"
)
FONTE_DO_CLIMA = "NASA POWER, reanálise diária agregada por semana"
FONTE_DO_VETOR = "MI-Aedes (SMS-POA), armadilhas MosquiTRAP"
FONTE_DO_CALENDARIO = "---"
VARIAVEL_DE_CASOS_NO_TEXTO = "casos da semana $t$"
VARIAVEL_DE_VETOR_NO_TEXTO = (
    r"fêmeas de \textit{Ae.~aegypti} por vistoria na semana $t$"
)
VARIAVEIS_DO_CALENDARIO_NO_TEXTO = (
    "seno e cosseno da semana do ano de $t$ e da semana-alvo $t+h$"
)


@dataclasses.dataclass(frozen=True)
class LinhaDaTabela:
    """Uma linha da Tabela 1: um bloco de variáveis, sua fonte e sua contagem.

    Attributes:
        rotulo_do_bloco: Nome do bloco com o símbolo, como aparece na primeira coluna.
        fonte_e_periodo: Texto da segunda coluna (fonte e, quando há, período).
        variaveis_e_quantidade: Texto da terceira coluna, terminado pela contagem entre parênteses.
        quantidade: Quantas variáveis do modelo o bloco tem.
    """

    rotulo_do_bloco: str
    fonte_e_periodo: str
    variaveis_e_quantidade: str
    quantidade: int


def carregar_tabela_cortada() -> pd.DataFrame:
    """Lê a tabela certificada (confere sha256 e esquema) e aplica o corte de maturidade.

    O corte age uma vez, sobre a tabela crua, como em todo o pacote: os casos depois de 01/02/2026 viram ausentes.

    Returns:
        A tabela semanal inteira (725 semanas) com os casos recentes apagados.

    Raises:
        ValueError: Se o sha256 ou o esquema divergirem do snapshot certificado.
    """
    conteudo_em_bytes = ARQUIVO_DA_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    tabela_cortada = aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)
    return tabela_cortada


def recortar_no_periodo_do_modelo(tabela_cortada: pd.DataFrame) -> pd.DataFrame:
    """Fica com as semanas do primeiro caso até a última semana-alvo avaliada.

    Raises:
        RuntimeError: Se a última semana com caso depois do corte não for a última semana-alvo da avaliação
            configurada (as duas são 01/02/2026; se divergirem, algo mudou e nada deve ser forçado).
    """
    coluna_de_data = CONFIGURACAO_DADOS.coluna_de_data
    coluna_de_casos = CONFIGURACAO_DADOS.coluna_de_casos

    semanas_com_caso = tabela_cortada.dropna(subset=[coluna_de_casos])
    primeira_semana_com_caso = semanas_com_caso[coluna_de_data].min()
    ultima_semana_com_caso = obter_ultima_semana_com_caso(tabela_cortada, CONFIGURACAO_DADOS)
    ultima_semana_avaliada = CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada

    if ultima_semana_com_caso != ultima_semana_avaliada:
        raise RuntimeError(
            f"Última semana com caso depois do corte ({ultima_semana_com_caso.date()}) difere da última "
            f"semana-alvo avaliada ({ultima_semana_avaliada.date()})."
        )

    datas = tabela_cortada[coluna_de_data]
    dentro_do_recorte = datas.between(primeira_semana_com_caso, ultima_semana_avaliada)
    return tabela_cortada[dentro_do_recorte]


def calcular_periodo_da_fonte(
    tabela_do_recorte: pd.DataFrame,
    colunas_da_fonte: list[str],
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Primeira e última semana em que TODAS as colunas da fonte têm valor.

    Args:
        tabela_do_recorte: Tabela já recortada no período do modelo.
        colunas_da_fonte: Colunas que alimentam o modelo vindas desta fonte.

    Returns:
        A primeira e a última data (domingo que abre a semana) com valor não ausente.

    Raises:
        ValueError: Se nenhuma semana tiver valor.
    """
    semanas_com_valor = tabela_do_recorte.dropna(subset=colunas_da_fonte)
    if semanas_com_valor.empty:
        raise ValueError(f"Nenhuma semana com valor em {colunas_da_fonte}.")
    coluna_de_data = CONFIGURACAO_DADOS.coluna_de_data
    primeira_semana = semanas_com_valor[coluna_de_data].min()
    ultima_semana = semanas_com_valor[coluna_de_data].max()
    return primeira_semana, ultima_semana


def formatar_mes_e_ano(data: pd.Timestamp) -> str:
    """Formata como no texto do artigo: fev/2018."""
    nome_do_mes = NOMES_DOS_MESES[data.month - 1]
    return f"{nome_do_mes}/{data.year}"


def formatar_periodo(primeira_semana: pd.Timestamp, ultima_semana: pd.Timestamp) -> str:
    """Monta o período como `fev/2018 a fev/2026`."""
    inicio = formatar_mes_e_ano(primeira_semana)
    fim = formatar_mes_e_ano(ultima_semana)
    return f"{inicio} a {fim}"


def formatar_defasagens(defasagens: tuple[int, ...]) -> str:
    """Escreve as defasagens como no artigo: `defasagens de 1 a 4 semanas`, `defasagens de 3 e 4 semanas`.

    Regra: um só valor vira `defasagem de k semana(s)`; três ou mais valores consecutivos viram `de a a b`; o
    resto vira lista com `e` antes do último.
    """
    ordenadas = sorted(defasagens)
    if len(ordenadas) == 1:
        unica = ordenadas[0]
        unidade = "semana" if unica == 1 else "semanas"
        return f"defasagem de {unica} {unidade}"

    primeira = ordenadas[0]
    ultima = ordenadas[-1]
    sao_consecutivas = ultima - primeira + 1 == len(ordenadas)
    if sao_consecutivas and len(ordenadas) >= 3:
        return f"defasagens de {primeira} a {ultima} semanas"

    todas_menos_a_ultima = ", ".join(str(valor) for valor in ordenadas[:-1])
    return f"defasagens de {todas_menos_a_ultima} e {ultima} semanas"


def agrupar_clima_por_coluna_de_origem(
    configuracao: ConfiguracaoVariaveis,
) -> dict[str, list[int]]:
    """Agrupa as 6 variáveis de clima congeladas pela coluna de origem, com as defasagens de cada uma.

    Returns:
        Dicionário `coluna de origem -> defasagens (0 = sem defasagem)`, na ordem de ROTULO_DA_COLUNA_DE_CLIMA.

    Raises:
        KeyError: Se a configuração usar uma coluna de clima sem rótulo de apresentação (o texto não pode adivinhar).
    """
    defasagens_por_coluna: dict[str, list[int]] = {}
    for variavel in configuracao.variaveis_de_clima:
        if variavel.coluna_de_origem not in ROTULO_DA_COLUNA_DE_CLIMA:
            raise KeyError(
                f"Coluna de clima {variavel.coluna_de_origem!r} sem rótulo de apresentação em "
                "ROTULO_DA_COLUNA_DE_CLIMA."
            )
        lista_de_defasagens = defasagens_por_coluna.setdefault(variavel.coluna_de_origem, [])
        lista_de_defasagens.append(variavel.defasagem_em_semanas)

    em_ordem_de_leitura: dict[str, list[int]] = {}
    for coluna_de_origem in ROTULO_DA_COLUNA_DE_CLIMA:
        if coluna_de_origem in defasagens_por_coluna:
            em_ordem_de_leitura[coluna_de_origem] = sorted(defasagens_por_coluna[coluna_de_origem])
    return em_ordem_de_leitura


def descrever_uma_variavel_de_clima(coluna_de_origem: str, defasagens: list[int]) -> str:
    """Descreve uma coluna de clima e suas defasagens: `temperatura média com defasagens de 3 e 4 semanas`."""
    rotulo = ROTULO_DA_COLUNA_DE_CLIMA[coluna_de_origem]
    defasagens_positivas = tuple(valor for valor in defasagens if valor > 0)
    tem_versao_sem_defasagem = 0 in defasagens

    if not defasagens_positivas:
        return rotulo

    frase_das_defasagens = formatar_defasagens(defasagens_positivas)
    if tem_versao_sem_defasagem:
        return f"{rotulo}, sem defasagem e com {frase_das_defasagens}"
    return f"{rotulo} com {frase_das_defasagens}"


def separar_nomes_por_bloco(configuracao: ConfiguracaoVariaveis) -> dict[str, list[str]]:
    """Reparte os nomes das variáveis do modelo nos blocos C, M, V e K, a partir da configuração.

    Raises:
        RuntimeError: Se algum nome ficar sem bloco, ou se os blocos não somarem exatamente os nomes do modelo.
    """
    nome_dos_casos = configuracao.nome_da_variavel_de_casos
    nome_do_vetor = configuracao.coluna_do_vetor

    nomes_de_casos = [nome_dos_casos]
    for defasagem in configuracao.defasagens_de_casos:
        nomes_de_casos.append(nome_da_variavel_defasada(nome_dos_casos, defasagem))
    nomes_de_casos.append(configuracao.nome_da_media_movel_de_casos())

    nomes_de_clima = [variavel.nome for variavel in configuracao.variaveis_de_clima]

    nomes_de_vetor = [nome_do_vetor]
    for defasagem in configuracao.defasagens_do_vetor:
        nomes_de_vetor.append(nome_da_variavel_defasada(nome_do_vetor, defasagem))
    nomes_de_vetor.append(configuracao.nome_da_media_movel_do_vetor())

    nomes_de_calendario = list(configuracao.nomes_da_sazonalidade_da_origem)
    nomes_de_calendario.extend(configuracao.nomes_da_sazonalidade_do_alvo)

    nomes_por_bloco = {
        "C": nomes_de_casos,
        "M": nomes_de_clima,
        "V": nomes_de_vetor,
        "K": nomes_de_calendario,
    }

    todos_os_nomes_dos_blocos: list[str] = []
    for nomes_do_bloco in nomes_por_bloco.values():
        todos_os_nomes_dos_blocos.extend(nomes_do_bloco)

    nomes_do_modelo = list(configuracao.nomes_das_variaveis)
    if sorted(todos_os_nomes_dos_blocos) != sorted(nomes_do_modelo):
        raise RuntimeError(
            "Os blocos não coincidem com nomes_das_variaveis: "
            f"blocos {sorted(todos_os_nomes_dos_blocos)} vs modelo {sorted(nomes_do_modelo)}."
        )
    return nomes_por_bloco


def conferir_contagens(nomes_por_bloco: dict[str, list[str]]) -> None:
    """Para o script se a contagem por bloco ou o total divergir das âncoras (6, 6, 6, 4 = 22).

    Raises:
        RuntimeError: Se qualquer contagem divergir.
    """
    contagem_encontrada = {bloco: len(nomes) for bloco, nomes in nomes_por_bloco.items()}
    total_encontrado = sum(contagem_encontrada.values())
    if contagem_encontrada != VARIAVEIS_POR_BLOCO_ESPERADAS or total_encontrado != TOTAL_DE_VARIAVEIS_ESPERADO:
        raise RuntimeError(
            f"A configuração diverge das âncoras: encontrado {contagem_encontrada} (total {total_encontrado}); "
            f"esperado {VARIAVEIS_POR_BLOCO_ESPERADAS} (total {TOTAL_DE_VARIAVEIS_ESPERADO})."
        )


def montar_linhas_da_tabela(
    tabela_do_recorte: pd.DataFrame,
    nomes_por_bloco: dict[str, list[str]],
) -> list[LinhaDaTabela]:
    """Monta as quatro linhas (C, M, V, K) com fonte, período calculado dos dados, variáveis e contagem."""
    configuracao = CONFIGURACAO_VARIAVEIS
    janela = configuracao.janela_da_media_movel
    frase_da_media_movel = f"média móvel de {janela} semanas"

    # Casos
    periodo_dos_casos = calcular_periodo_da_fonte(tabela_do_recorte, [CONFIGURACAO_DADOS.coluna_de_casos])
    texto_dos_casos = (
        f"{VARIAVEL_DE_CASOS_NO_TEXTO}; {formatar_defasagens(configuracao.defasagens_de_casos)}; "
        f"{frase_da_media_movel}"
    )

    # Meteorologia
    defasagens_por_coluna = agrupar_clima_por_coluna_de_origem(configuracao)
    colunas_de_clima = list(defasagens_por_coluna.keys())
    periodo_do_clima = calcular_periodo_da_fonte(tabela_do_recorte, colunas_de_clima)
    descricoes_do_clima = []
    for coluna_de_origem, defasagens in defasagens_por_coluna.items():
        descricoes_do_clima.append(descrever_uma_variavel_de_clima(coluna_de_origem, defasagens))
    texto_do_clima = "; ".join(descricoes_do_clima)

    # Vetor
    periodo_do_vetor = calcular_periodo_da_fonte(tabela_do_recorte, [configuracao.coluna_do_vetor])
    texto_do_vetor = (
        f"{VARIAVEL_DE_VETOR_NO_TEXTO}; {formatar_defasagens(configuracao.defasagens_do_vetor)}; "
        f"{frase_da_media_movel}"
    )

    quantidades = {bloco: len(nomes) for bloco, nomes in nomes_por_bloco.items()}
    linhas = [
        LinhaDaTabela(
            rotulo_do_bloco="Casos ($C$)",
            fonte_e_periodo=f"{FONTE_DOS_CASOS}; {formatar_periodo(*periodo_dos_casos)}",
            variaveis_e_quantidade=f"{texto_dos_casos} ({quantidades['C']})",
            quantidade=quantidades["C"],
        ),
        LinhaDaTabela(
            rotulo_do_bloco="Meteorologia ($M$)",
            fonte_e_periodo=f"{FONTE_DO_CLIMA}; {formatar_periodo(*periodo_do_clima)}",
            variaveis_e_quantidade=f"{texto_do_clima} ({quantidades['M']})",
            quantidade=quantidades["M"],
        ),
        LinhaDaTabela(
            rotulo_do_bloco="Vetor ($V$)",
            fonte_e_periodo=f"{FONTE_DO_VETOR}; {formatar_periodo(*periodo_do_vetor)}",
            variaveis_e_quantidade=f"{texto_do_vetor} ({quantidades['V']})",
            quantidade=quantidades["V"],
        ),
        LinhaDaTabela(
            rotulo_do_bloco="Calendário ($K$)",
            fonte_e_periodo=FONTE_DO_CALENDARIO,
            variaveis_e_quantidade=f"{VARIAVEIS_DO_CALENDARIO_NO_TEXTO} ({quantidades['K']})",
            quantidade=quantidades["K"],
        ),
    ]
    return linhas


def quebrar_linha_do_arquivo(texto: str, recuo_das_continuacoes: str = "  ") -> str:
    """Quebra o texto em linhas de até 120 caracteres, com recuo nas continuações (2 espaços, como a preliminar).

    A legenda (caption) da preliminar não tinha recuo; as linhas da tabela tinham 2 espaços.
    """
    return textwrap.fill(
        texto,
        width=LARGURA_DA_LINHA_NO_ARQUIVO,
        subsequent_indent=recuo_das_continuacoes,
        break_long_words=False,
        break_on_hyphens=False,
    )


def montar_texto_latex(linhas: list[LinhaDaTabela], total_de_variaveis: int, impressao_digital: str) -> str:
    """Escreve o arquivo .tex inteiro: comentário de origem, ambiente table, cabeçalho e as quatro linhas."""
    caminho_do_script = Path(__file__).resolve()
    comentario = (
        f"% Tabela 1: fontes e variáveis do modelo. GERADA por script em {DATA_DE_GERACAO}; não editar à mão.\n"
        f"% Script: {caminho_do_script}\n"
        f"% Lê: aedes/configuracao.py (variáveis, defasagens, clima congelado) e dados/tabela_final.csv "
        f"(sha256 {impressao_digital[:8]}...).\n"
        "% Períodos: primeira e última semana com valor, de 18/02/2018 (1º caso) a 01/02/2026 (última semana-alvo avaliada).\n"
        "% Versão preliminar (escrita à mão, 10/10/2026): entregas/artigo/_arquivo/2026-10-16_antes_v1/."
    )

    cabecalho = (
        "\\begin{table}[!htbp]\n"
        "\\centering\n"
        + quebrar_linha_do_arquivo(
            f"\\caption{{Fontes de dados e as {total_de_variaveis} variáveis de entrada do modelo, por bloco. "
            "Todas as séries são semanais, com a semana começando no domingo.}",
            recuo_das_continuacoes="",
        )
        + "\n"
        "\\label{tab:variaveis}\n"
        "\\small\n"
        "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{0.17\\linewidth}>{\\raggedright\\arraybackslash}p{0.28\\linewidth}>{\\raggedright\\arraybackslash}p{0.43\\linewidth}}\n"
        "\\toprule\n"
        "\\textbf{Bloco} & \\textbf{Fonte e período} & \\textbf{Variáveis (quantidade)} \\\\\n"
        "\\midrule\n"
    )

    textos_das_linhas = []
    for linha in linhas:
        texto_da_linha = (
            f"{linha.rotulo_do_bloco} & {linha.fonte_e_periodo} & {linha.variaveis_e_quantidade} \\\\"
        )
        textos_das_linhas.append(quebrar_linha_do_arquivo(texto_da_linha))
    corpo = "\n\\addlinespace\n".join(textos_das_linhas) + "\n"

    rodape = "\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    return comentario + "\n" + cabecalho + corpo + rodape


def main() -> None:
    """Carrega os dados, confere as âncoras, monta a tabela e grava o .tex."""
    impressao_digital = CONFIGURACAO_DADOS.sha256_esperado_da_tabela
    tabela_cortada = carregar_tabela_cortada()
    tabela_do_recorte = recortar_no_periodo_do_modelo(tabela_cortada)

    nomes_por_bloco = separar_nomes_por_bloco(CONFIGURACAO_VARIAVEIS)
    conferir_contagens(nomes_por_bloco)
    total_de_variaveis = len(CONFIGURACAO_VARIAVEIS.nomes_das_variaveis)

    linhas = montar_linhas_da_tabela(tabela_do_recorte, nomes_por_bloco)
    texto_latex = montar_texto_latex(linhas, total_de_variaveis, impressao_digital)

    ARQUIVO_DE_SAIDA.write_text(texto_latex, encoding="utf-8")
    print(f"Tabela 1 gravada em {ARQUIVO_DE_SAIDA}")
    print(f"Recorte: {len(tabela_do_recorte)} semanas; variáveis por bloco: "
          f"{ {bloco: len(nomes) for bloco, nomes in nomes_por_bloco.items()} }; total {total_de_variaveis}")
    for linha in linhas:
        print(f"  {linha.rotulo_do_bloco}: {linha.fonte_e_periodo}")


if __name__ == "__main__":
    main()
