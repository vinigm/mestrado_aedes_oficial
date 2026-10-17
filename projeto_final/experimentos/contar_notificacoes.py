"""Conta as fichas de dengue de Porto Alegre nos zips publicos DENGBR18 a DENGBR26 (limitacao da temporada de 2026).

Pergunta: quantas fichas existem por arquivo e por ano de inicio dos sintomas, e quantas viram
"confirmada" (CLASSI_FIN 10, 11, 12), "inconclusiva" (8), "em aberto" (vazio) ou outro codigo?
Municipio de NOTIFICACAO (`ID_MUNICIP` = 431490). Le so 4 colunas, em pedacos, tudo como texto.
Grava apenas contagens agregadas (nenhum registro individual).

Grava em `resultados/notificacoes/`: `contagens_por_arquivo.csv`, `contagens_por_ano_de_sintomas.csv`,
`contar_notificacoes.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.contar_notificacoes
"""

import pathlib
import zipfile
from collections import Counter

import pandas as pd

from aedes.alarme import (
    CLASSIFICACOES_CONFIRMADAS,
    CODIGO_DE_PORTO_ALEGRE,
    COLUNA_DA_CLASSIFICACAO,
    COLUNA_DA_DATA_DE_SINTOMAS,
    COLUNA_DE_NOTIFICACAO,
    FORMATO_DA_DATA_DE_SINTOMAS,
)
from experimentos.comum_ciencia import PASTA_DO_PROJETO, RegistradorDeLog

COLUNA_DA_DATA_DE_ENCERRAMENTO = "DT_ENCERRA"
COLUNAS_LIDAS = [
    COLUNA_DE_NOTIFICACAO,
    COLUNA_DA_CLASSIFICACAO,
    COLUNA_DA_DATA_DE_SINTOMAS,
    COLUNA_DA_DATA_DE_ENCERRAMENTO,
]
CODIGO_INCONCLUSIVO = "8"
LINHAS_POR_PEDACO = 300_000
ROTULO_EM_ABERTO = "em_aberto"
ROTULO_SEM_DATA = "sem_data_valida"
SITUACOES = ["confirmadas", "inconclusivas", "em_aberto", "outros"]

PASTA_DOS_ZIPS = PASTA_DO_PROJETO.parent / "modelagem_aedes" / "dados" / "entradas" / "bases_governo"
PASTA_DE_SAIDA = PASTA_DO_PROJETO / "resultados" / "notificacoes"
CAMINHO_POR_ARQUIVO = PASTA_DE_SAIDA / "contagens_por_arquivo.csv"
CAMINHO_POR_ANO = PASTA_DE_SAIDA / "contagens_por_ano_de_sintomas.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "contar_notificacoes.log")

# Duas versoes do DENGBR26 existem; na soma por ano entra so a mais recente, para nao contar a ficha duas vezes.
ARQUIVOS = [f"DENGBR{sufixo}.csv.zip" for sufixo in range(18, 27)] + ["DENGBR26_atualizado_set26.csv.zip"]
ARQUIVO_SUBSTITUIDO_NA_SOMA = "DENGBR26.csv.zip"


def classificar_situacao(codigo_da_classificacao: str) -> str:
    """Traduz o texto de `CLASSI_FIN` (ja sem espacos; vazio = 'nan' tratado antes) em uma das 4 situacoes."""
    if codigo_da_classificacao == ROTULO_EM_ABERTO:
        return "em_aberto"
    if codigo_da_classificacao in CLASSIFICACOES_CONFIRMADAS:
        return "confirmadas"
    if codigo_da_classificacao == CODIGO_INCONCLUSIVO:
        return "inconclusivas"
    return "outros"


def preparar_fichas_de_porto_alegre(pedaco: pd.DataFrame) -> pd.DataFrame:
    """Filtra Porto Alegre (notificacao) e devolve codigo textual, ano de sintomas e data de encerramento."""
    municipio = pedaco[COLUNA_DE_NOTIFICACAO].astype(str).str.strip()
    fichas = pedaco[municipio == CODIGO_DE_PORTO_ALEGRE]
    classificacao_bruta = fichas[COLUNA_DA_CLASSIFICACAO]
    codigo = classificacao_bruta.fillna("").astype(str).str.strip()
    codigo = codigo.where(codigo != "", ROTULO_EM_ABERTO)
    texto_da_data = fichas[COLUNA_DA_DATA_DE_SINTOMAS].astype(str).str.strip()
    data_dos_sintomas = pd.to_datetime(texto_da_data, format=FORMATO_DA_DATA_DE_SINTOMAS, errors="coerce")
    texto_do_encerramento = fichas[COLUNA_DA_DATA_DE_ENCERRAMENTO].astype(str).str.strip()
    data_do_encerramento = pd.to_datetime(texto_do_encerramento, format=FORMATO_DA_DATA_DE_SINTOMAS, errors="coerce")
    resultado = pd.DataFrame(
        {
            "codigo": codigo.to_numpy(),
            "ano": data_dos_sintomas.dt.year.to_numpy(),
            "encerramento": data_do_encerramento.to_numpy(),
        }
    )
    return resultado


def contar_um_zip(caminho_do_zip: pathlib.Path) -> tuple[Counter, Counter, Counter, pd.Timestamp, int]:
    """Le um zip em pedacos.

    Returns:
        (contagem por situacao, contagem por (ano, situacao), contagem por codigo, maior DT_ENCERRA, linhas lidas)
    """
    por_situacao: Counter = Counter()
    por_ano_e_situacao: Counter = Counter()
    por_codigo: Counter = Counter()
    maior_encerramento = pd.NaT
    linhas_lidas = 0
    with zipfile.ZipFile(caminho_do_zip) as arquivo_zip:
        nomes = arquivo_zip.namelist()
        if len(nomes) != 1:
            raise ValueError(f"{caminho_do_zip.name}: esperado 1 arquivo, achei {nomes}")
        with arquivo_zip.open(nomes[0]) as fluxo_csv:
            leitor = pd.read_csv(
                fluxo_csv, usecols=COLUNAS_LIDAS, dtype=str, chunksize=LINHAS_POR_PEDACO, low_memory=False
            )
            for pedaco in leitor:
                linhas_lidas += len(pedaco)
                fichas = preparar_fichas_de_porto_alegre(pedaco)
                if fichas.empty:
                    continue
                maior_do_pedaco = fichas["encerramento"].max()
                if pd.isna(maior_encerramento) or maior_do_pedaco > maior_encerramento:
                    maior_encerramento = maior_do_pedaco
                for codigo, ano in zip(fichas["codigo"], fichas["ano"]):
                    situacao = classificar_situacao(codigo)
                    ano_texto = ROTULO_SEM_DATA if pd.isna(ano) else str(int(ano))
                    por_situacao[situacao] += 1
                    por_ano_e_situacao[(ano_texto, situacao)] += 1
                    por_codigo[codigo] += 1
    return por_situacao, por_ano_e_situacao, por_codigo, maior_encerramento, linhas_lidas


def main() -> None:
    """Conta cada zip disponivel, grava as duas tabelas e registra tudo no log."""
    linhas_por_arquivo: list[dict[str, object]] = []
    soma_por_ano: Counter = Counter()
    for nome in ARQUIVOS:
        caminho = PASTA_DOS_ZIPS / nome
        if not caminho.exists():
            REGISTRADOR.registrar(f"{nome}: nao encontrado, pulado.")
            continue
        por_situacao, por_ano, por_codigo, maior_encerramento, linhas_lidas = contar_um_zip(caminho)
        total = sum(por_situacao.values())
        confirmadas = por_situacao["confirmadas"]
        fracao = confirmadas / total if total else float("nan")
        data_do_arquivo = pd.Timestamp(caminho.stat().st_mtime, unit="s").date()
        entra_na_soma = nome != ARQUIVO_SUBSTITUIDO_NA_SOMA
        codigos_texto = ";".join(f"{codigo}={quantidade}" for codigo, quantidade in sorted(por_codigo.items()))
        linhas_por_arquivo.append(
            {
                "arquivo": nome,
                "linhas_do_arquivo": linhas_lidas,
                "total_fichas": total,
                "confirmadas": confirmadas,
                "inconclusivas": por_situacao["inconclusivas"],
                "em_aberto": por_situacao["em_aberto"],
                "outros": por_situacao["outros"],
                "fracao_confirmada": round(fracao, 6),
                "codigos_classi_fin": codigos_texto,
                "maior_dt_encerra": "" if pd.isna(maior_encerramento) else str(maior_encerramento.date()),
                "data_do_arquivo_no_disco": str(data_do_arquivo),
                "entra_na_soma_por_ano": entra_na_soma,
            }
        )
        REGISTRADOR.registrar(
            f"{nome}: linhas={linhas_lidas} total={total} conf={confirmadas} incl={por_situacao['inconclusivas']} "
            f"aberto={por_situacao['em_aberto']} outros={por_situacao['outros']} codigos=[{codigos_texto}] "
            f"maior_dt_encerra={maior_encerramento} entra_na_soma={entra_na_soma}"
        )
        if entra_na_soma:
            soma_por_ano.update(por_ano)

    PASTA_DE_SAIDA.mkdir(parents=True, exist_ok=True)
    tabela_por_arquivo = pd.DataFrame(linhas_por_arquivo)
    tabela_por_arquivo.to_csv(CAMINHO_POR_ARQUIVO, index=False)

    anos = sorted({ano for ano, _ in soma_por_ano})
    linhas_por_ano: list[dict[str, object]] = []
    for ano in anos:
        linha: dict[str, object] = {"ano_dos_sintomas": ano}
        total_do_ano = 0
        for situacao in SITUACOES:
            quantidade = soma_por_ano[(ano, situacao)]
            linha[situacao] = quantidade
            total_do_ano += quantidade
        linha["total_fichas"] = total_do_ano
        linha["fracao_confirmada"] = round(linha["confirmadas"] / total_do_ano, 6) if total_do_ano else float("nan")
        linhas_por_ano.append(linha)
    tabela_por_ano = pd.DataFrame(linhas_por_ano)
    tabela_por_ano.to_csv(CAMINHO_POR_ANO, index=False)
    REGISTRADOR.registrar("Por ano de sintomas:\n" + tabela_por_ano.to_string(index=False))
    REGISTRADOR.registrar(f"Gravado: {CAMINHO_POR_ARQUIVO.name}, {CAMINHO_POR_ANO.name}")


if __name__ == "__main__":
    main()
