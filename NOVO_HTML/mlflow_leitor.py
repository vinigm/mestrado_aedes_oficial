"""Lê a pasta 'mlruns' (que o MLflow cria) e devolve tudo em objetos simples de
Python — sem precisar do MLflow instalado.

O MLflow guarda cada execução numa árvore de pastas com arquivinhos de texto:
um arquivo por parâmetro, um por métrica, e uma pasta de anexos. Aqui a gente
só abre essa árvore e organiza: cada CENÁRIO (experimento) vira um objeto e,
dentro dele, cada MODELO (run) vira outro — já com parâmetros, métricas e as
tabelas de resultado prontos para a página montar.

Ler direto assim deixa o site novo independente: ele não depende do MLflow nem
sofre com nenhum problema de versão dele. É uma cópia adaptada de
`pagina_web/leitor_mlflow.py`, com acentuação corrigida, type hints e
docstrings no formato Google.
"""

import csv
import dataclasses
import datetime
from pathlib import Path

# Onde a pasta mlruns do projeto mora, relativa a este arquivo (que fica em
# NOVO_HTML/, irmã de modelagem_aedes/ dentro de Meu_Projeto/).
PASTA_AQUI = Path(__file__).resolve().parent
PASTA_MLRUNS_PADRAO = PASTA_AQUI.parent / "modelagem_aedes" / "mlruns"

# Nomes de pasta dentro de mlruns que não são experimentos (a gente pula).
PASTAS_IGNORADAS = {"models", ".trash", ".mlflow"}

# O MLflow guarda o status como número; aqui viram palavras simples.
STATUS_EM_PALAVRAS = {
    "1": "em andamento",
    "2": "agendado",
    "3": "concluido",
    "4": "falhou",
    "5": "interrompido",
}


@dataclasses.dataclass(frozen=True)
class TabelaDeResultado:
    """Uma tabela de resultado anexada a um modelo (um CSV gravado pelo MLflow).

    Attributes:
        colunas: Nomes das colunas, na ordem do cabeçalho do CSV.
        linhas: Uma linha por dicionário, com o texto bruto de cada célula
            (sem conversão de tipo — quem consome decide se é número ou texto).
    """

    colunas: list[str]
    linhas: list[dict[str, str]]


@dataclasses.dataclass(frozen=True)
class Modelo:
    """Uma execução (run) de um algoritmo dentro de um cenário.

    Attributes:
        nome: Nome do modelo (normalmente o algoritmo, ex.: "lightgbm").
        run_id: Identificador da execução no MLflow.
        status: Situação da execução, já traduzida (ex.: "concluido").
        inicio: Instante em que a execução começou, ou None se ausente.
        fim: Instante em que a execução terminou, ou None se ausente.
        duracao_segundos: Duração da execução, ou None se início ou fim faltar.
        parametros: Parâmetros registrados (chave -> valor, ambos texto).
        metricas: Métricas de resumo registradas (chave -> último valor).
        tabelas: Tabelas de resultado anexadas, por nome de arquivo.
    """

    nome: str
    run_id: str
    status: str
    inicio: datetime.datetime | None
    fim: datetime.datetime | None
    duracao_segundos: float | None
    parametros: dict[str, str] = dataclasses.field(default_factory=dict)
    metricas: dict[str, float] = dataclasses.field(default_factory=dict)
    tabelas: dict[str, TabelaDeResultado] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class Cenario:
    """Um cenário (experimento do MLflow) com os modelos testados dentro dele.

    Attributes:
        nome: Nome do cenário, como registrado no MLflow (ex.: "cidade_regressao").
        experiment_id: Identificador do experimento no MLflow.
        modelos: Os modelos selecionados para exibição (ver `_selecionar_modelos_validos`).
    """

    nome: str
    experiment_id: str
    modelos: list[Modelo] = dataclasses.field(default_factory=list)


def _ler_meta(caminho: Path) -> dict[str, str]:
    """Lê um `meta.yaml` simples (linhas "chave: valor") sem depender de biblioteca.

    O meta.yaml do file store do MLflow é plano (uma chave por linha), então dá
    para ler no braço: separa no primeiro ":" e tira as aspas da ponta. Só o
    que a gente precisa (nome, tempos, status) mora nesse formato simples.

    Args:
        caminho: Caminho do arquivo `meta.yaml`.

    Returns:
        Um dicionário chave -> valor, ambos como texto.
    """
    dados: dict[str, str] = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if ":" not in linha:
            continue
        chave, _, valor = linha.partition(":")
        valor_limpo = valor.strip().strip("'\"")
        dados[chave.strip()] = valor_limpo
    return dados


def _converter_timestamp_em_data(texto: str) -> datetime.datetime | None:
    """Transforma o carimbo de tempo do MLflow (milissegundos) em data e hora.

    Args:
        texto: O carimbo de tempo em milissegundos, como texto.

    Returns:
        A data e hora correspondente, ou None se o texto não for um número
        válido (campo ausente ou vazio).
    """
    try:
        return datetime.datetime.fromtimestamp(int(texto) / 1000)
    except (ValueError, TypeError):
        return None


def _ler_parametros(pasta: Path) -> dict[str, str]:
    """Lê a pasta `params` (um arquivo por parâmetro; o nome do arquivo é a chave).

    Args:
        pasta: A pasta `params` de um run. Pode não existir.

    Returns:
        Um dicionário chave -> valor, ou vazio se a pasta não existir.
    """
    parametros: dict[str, str] = {}
    if not pasta.is_dir():
        return parametros
    for arquivo in sorted(pasta.iterdir()):
        if arquivo.is_file():
            parametros[arquivo.name] = arquivo.read_text(encoding="utf-8").strip()
    return parametros


def _ler_metricas(pasta: Path) -> dict[str, float]:
    """Lê a pasta `metrics` (cada arquivo tem "tempo valor passo" por linha).

    Cada métrica pode ter vários registros ao longo do tempo, um por linha, no
    formato "tempo valor passo". Aqui a gente pega a ÚLTIMA linha (o valor mais
    recente) e guarda só o número.

    Args:
        pasta: A pasta `metrics` de um run. Pode não existir.

    Returns:
        Um dicionário chave -> último valor numérico, ou vazio se a pasta não
        existir ou nenhum arquivo tiver linha válida.
    """
    metricas: dict[str, float] = {}
    if not pasta.is_dir():
        return metricas
    for arquivo in sorted(pasta.iterdir()):
        if not arquivo.is_file():
            continue
        linhas_nao_vazias = [
            linha for linha in arquivo.read_text(encoding="utf-8").splitlines() if linha.strip()
        ]
        if not linhas_nao_vazias:
            continue
        partes_da_ultima_linha = linhas_nao_vazias[-1].split()
        if len(partes_da_ultima_linha) >= 2:
            try:
                metricas[arquivo.name] = float(partes_da_ultima_linha[1])
            except ValueError:
                pass
    return metricas


def _ler_tabelas(pasta: Path) -> dict[str, TabelaDeResultado]:
    """Lê os CSVs anexados ao modelo (as tabelas de resultado do experimento).

    Args:
        pasta: A pasta `artifacts` de um run. Pode não existir.

    Returns:
        Um dicionário nome_do_arquivo -> tabela lida, ou vazio se a pasta não
        existir ou não houver CSV anexado.
    """
    tabelas: dict[str, TabelaDeResultado] = {}
    if not pasta.is_dir():
        return tabelas
    for arquivo in sorted(pasta.iterdir()):
        if arquivo.is_file() and arquivo.suffix == ".csv":
            with arquivo.open(encoding="utf-8", newline="") as origem:
                leitor_csv = csv.DictReader(origem)
                colunas = leitor_csv.fieldnames or []
                linhas = list(leitor_csv)
            tabelas[arquivo.name] = TabelaDeResultado(colunas=list(colunas), linhas=linhas)
    return tabelas


def _ler_modelo(pasta: Path) -> Modelo | None:
    """Lê um modelo (run) inteiro a partir da pasta dele.

    Args:
        pasta: A pasta do run dentro do experimento.

    Returns:
        O modelo lido, ou None se a pasta não tiver `meta.yaml` ou se o run
        estiver marcado como excluído (`lifecycle_stage: deleted`).
    """
    meta_arquivo = pasta / "meta.yaml"
    if not meta_arquivo.is_file():
        return None
    meta = _ler_meta(meta_arquivo)
    if meta.get("lifecycle_stage") == "deleted":
        return None

    inicio = _converter_timestamp_em_data(meta.get("start_time", ""))
    fim = _converter_timestamp_em_data(meta.get("end_time", ""))
    duracao_segundos = (fim - inicio).total_seconds() if inicio and fim else None

    return Modelo(
        nome=meta.get("run_name") or pasta.name,
        run_id=meta.get("run_id", pasta.name),
        status=STATUS_EM_PALAVRAS.get(meta.get("status", ""), meta.get("status", "")),
        inicio=inicio,
        fim=fim,
        duracao_segundos=duracao_segundos,
        parametros=_ler_parametros(pasta / "params"),
        metricas=_ler_metricas(pasta / "metrics"),
        tabelas=_ler_tabelas(pasta / "artifacts"),
    )


def _instante_de_inicio(modelo: Modelo) -> datetime.datetime:
    """Devolve o início do modelo, trocando None pelo menor instante possível.

    Serve só para ordenar e comparar datas sem quebrar quando o modelo não tem
    início registrado (run que falhou antes de começar, por exemplo).

    Args:
        modelo: O modelo cujo instante de início se quer.

    Returns:
        `modelo.inicio`, ou `datetime.datetime.min` quando ausente.
    """
    if modelo.inicio is None:
        return datetime.datetime.min
    return modelo.inicio


def _selecionar_modelos_validos(modelos: list[Modelo]) -> list[Modelo]:
    """Filtra os modelos de um cenário: só os concluídos, e um por nome (o mais novo).

    O mlruns acumula várias GERAÇÕES de execução ao longo do projeto (testes de
    julho, uma rodada intermediária de agosto que saiu com bug, e a rodada
    oficial). Todas continuam na pasta como histórico, então sem filtro a
    página misturaria resultado velho com o oficial.

    A regra: descarta runs que não terminaram (só fica "concluido") e, quando
    duas execuções têm o MESMO nome de modelo dentro do mesmo cenário, fica só
    com a que começou por último — é a versão mais nova daquele modelo.

    Args:
        modelos: Lista de modelos lidos de dentro de um cenário (experimento).

    Returns:
        Lista filtrada, um modelo por nome, ordenada do mais recente para o
        mais antigo.
    """
    modelos_concluidos = [modelo for modelo in modelos if modelo.status == "concluido"]

    modelo_mais_recente_por_nome: dict[str, Modelo] = {}
    for modelo in modelos_concluidos:
        modelo_ja_guardado = modelo_mais_recente_por_nome.get(modelo.nome)
        if modelo_ja_guardado is None:
            modelo_mais_recente_por_nome[modelo.nome] = modelo
            continue
        if _instante_de_inicio(modelo) > _instante_de_inicio(modelo_ja_guardado):
            modelo_mais_recente_por_nome[modelo.nome] = modelo

    modelos_selecionados = list(modelo_mais_recente_por_nome.values())
    modelos_selecionados.sort(key=_instante_de_inicio, reverse=True)
    return modelos_selecionados


def _ler_cenario(pasta: Path) -> Cenario | None:
    """Lê um cenário (experimento) inteiro: os dados dele + todos os modelos dentro.

    Args:
        pasta: A pasta do experimento dentro de `mlruns`.

    Returns:
        O cenário lido, ou None se a pasta não tiver `meta.yaml`, não tiver
        nome ou estiver marcada como excluída.
    """
    meta_arquivo = pasta / "meta.yaml"
    if not meta_arquivo.is_file():
        return None
    meta = _ler_meta(meta_arquivo)
    if not meta.get("name") or meta.get("lifecycle_stage") == "deleted":
        return None

    modelos: list[Modelo] = []
    for subpasta in sorted(pasta.iterdir()):
        if subpasta.is_dir():
            modelo = _ler_modelo(subpasta)
            if modelo:
                modelos.append(modelo)

    modelos_selecionados = _selecionar_modelos_validos(modelos)
    return Cenario(
        nome=meta["name"],
        experiment_id=meta.get("experiment_id", pasta.name),
        modelos=modelos_selecionados,
    )


def carregar_cenarios(pasta_mlruns: Path = PASTA_MLRUNS_PADRAO) -> list[Cenario]:
    """Lê a pasta mlruns inteira e devolve a lista de cenários com modelo.

    É a porta de entrada do módulo: aponta para a pasta `mlruns` e recebe de
    volta a lista de cenários, cada um com seus modelos já lidos. Pula as
    pastas que não são experimentos e ignora cenários sem nenhum modelo
    concluído.

    Args:
        pasta_mlruns: Caminho da pasta `mlruns`. Por padrão, a do projeto
            (`modelagem_aedes/mlruns`).

    Returns:
        Os cenários com pelo menos um modelo concluído, ordenados por nome.
        Lista vazia se a pasta não existir.
    """
    if not pasta_mlruns.is_dir():
        return []

    cenarios: list[Cenario] = []
    for pasta in sorted(pasta_mlruns.iterdir()):
        if not pasta.is_dir() or pasta.name in PASTAS_IGNORADAS:
            continue
        cenario = _ler_cenario(pasta)
        if cenario and cenario.modelos:
            cenarios.append(cenario)

    cenarios.sort(key=lambda cenario: cenario.nome)
    return cenarios
