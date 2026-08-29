"""

Le a pasta 'mlruns' (que o MLflow cria) e devolve tudo em objetos simples de
Python — SEM precisar do MLflow instalado.

O MLflow guarda cada execucao numa arvore de pastas com arquivinhos de texto:
um arquivo por parametro, um por metrica, e uma pasta de anexos. Aqui a gente so
abre essa arvore e organiza: cada CENARIO (experimento) vira um objeto e, dentro
dele, cada MODELO (run) vira outro — ja com parametros, metricas e as tabelas de
resultado prontos para a pagina montar.

Ler direto assim deixa a pagina_web independente: ela nao depende do MLflow nem
sofre com nenhum problema de versao dele.

"""

import csv
import datetime
from dataclasses import dataclass, field
from pathlib import Path

# Nomes de pasta dentro de mlruns que NAO sao experimentos (a gente pula).
PASTAS_IGNORADAS = {"models", ".trash", ".mlflow"}

# O MLflow guarda o status como numero; aqui viram palavras simples.
STATUS_EM_PALAVRAS = {
    "1": "em andamento",
    "2": "agendado",
    "3": "concluido",
    "4": "falhou",
    "5": "interrompido",
}


@dataclass
class Modelo:
    nome: str
    run_id: str
    status: str
    inicio: datetime.datetime | None
    fim: datetime.datetime | None
    duracao_segundos: float | None
    parametros: dict = field(default_factory=dict)
    metricas: dict = field(default_factory=dict)
    tabelas: dict = field(default_factory=dict)


@dataclass
class Cenario:
    nome: str
    experiment_id: str
    modelos: list = field(default_factory=list)


# Le um meta.yaml simples (linhas 'chave: valor') sem precisar de biblioteca.
def _ler_meta(caminho: Path) -> dict:
    """

    O meta.yaml do file store e plano (uma chave por linha), entao da pra ler no
    braco: separa no primeiro ':' e tira as aspas da ponta. So o que a gente
    precisa (nome, tempos, status) mora nesse formato simples.

    """
    dados = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if ":" not in linha:
            continue
        chave, _, valor = linha.partition(":")
        valor = valor.strip().strip("'\"")
        dados[chave.strip()] = valor
    return dados


# Transforma o carimbo de tempo do MLflow (milissegundos) em data/hora.
def _para_data(texto: str) -> datetime.datetime | None:
    try:
        return datetime.datetime.fromtimestamp(int(texto) / 1000)
    except (ValueError, TypeError):
        return None


# Le a pasta 'params' (um arquivo por parametro; o nome e a chave).
def _ler_parametros(pasta: Path) -> dict:
    parametros = {}
    if not pasta.is_dir():
        return parametros
    for arquivo in sorted(pasta.iterdir()):
        if arquivo.is_file():
            parametros[arquivo.name] = arquivo.read_text(encoding="utf-8").strip()
    return parametros


# Le a pasta 'metrics' (cada arquivo tem "tempo valor passo"; fica o ultimo valor).
def _ler_metricas(pasta: Path) -> dict:
    """

    Cada metrica pode ter varios registros ao longo do tempo, um por linha, no
    formato "tempo valor passo". Aqui a gente pega a ULTIMA linha (o valor mais
    recente) e guarda so o numero.

    """
    metricas = {}
    if not pasta.is_dir():
        return metricas
    for arquivo in sorted(pasta.iterdir()):
        if not arquivo.is_file():
            continue
        linhas = [linha for linha in arquivo.read_text(encoding="utf-8").splitlines() if linha.strip()]
        if not linhas:
            continue
        partes = linhas[-1].split()
        if len(partes) >= 2:
            try:
                metricas[arquivo.name] = float(partes[1])
            except ValueError:
                pass
    return metricas


# Le os CSV anexados ao modelo (as tabelas de resultado) para colunas + linhas.
def _ler_tabelas(pasta: Path) -> dict:
    tabelas = {}
    if not pasta.is_dir():
        return tabelas
    for arquivo in sorted(pasta.iterdir()):
        if arquivo.is_file() and arquivo.suffix == ".csv":
            with arquivo.open(encoding="utf-8", newline="") as origem:
                leitor = csv.DictReader(origem)
                colunas = leitor.fieldnames or []
                linhas = list(leitor)
            tabelas[arquivo.name] = {"colunas": colunas, "linhas": linhas}
    return tabelas


# Le um modelo (run) inteiro a partir da pasta dele.
def _ler_modelo(pasta: Path) -> Modelo | None:
    meta_arquivo = pasta / "meta.yaml"
    if not meta_arquivo.is_file():
        return None
    meta = _ler_meta(meta_arquivo)
    if meta.get("lifecycle_stage") == "deleted":
        return None

    inicio = _para_data(meta.get("start_time", ""))
    fim = _para_data(meta.get("end_time", ""))
    duracao = (fim - inicio).total_seconds() if inicio and fim else None

    return Modelo(
        nome=meta.get("run_name") or pasta.name,
        run_id=meta.get("run_id", pasta.name),
        status=STATUS_EM_PALAVRAS.get(meta.get("status", ""), meta.get("status", "")),
        inicio=inicio,
        fim=fim,
        duracao_segundos=duracao,
        parametros=_ler_parametros(pasta / "params"),
        metricas=_ler_metricas(pasta / "metrics"),
        tabelas=_ler_tabelas(pasta / "artifacts"),
    )


# Devolve o inicio do modelo, trocando None pelo menor instante possivel.
def _instante_de_inicio(modelo: Modelo) -> datetime.datetime:
    """

    Serve so pra ordenar e comparar datas sem quebrar quando o modelo nao tem
    inicio registrado (run que falhou antes de comecar, por exemplo).

    """
    if modelo.inicio is None:
        return datetime.datetime.min
    return modelo.inicio


# Filtra os modelos de um cenario: so os concluidos, e um por nome (o mais novo).
def _selecionar_modelos_validos(modelos: list) -> list:
    """

    O mlruns acumula varias GERACOES de execucao ao longo do projeto (testes de
    julho, uma rodada intermediaria de agosto que saiu com bug, e a rodada
    oficial). Todas continuam na pasta como historico, entao sem filtro a
    pagina misturaria resultado velho com o oficial.

    A regra: descarta runs que nao terminaram (so fica "concluido") e, quando
    duas execucoes tem o MESMO nome de modelo dentro do mesmo cenario, fica so
    com a que comecou por ultimo — e a versao mais nova daquele modelo.

    Args:
        modelos: lista de modelos lidos de dentro de um cenario (experimento).

    Returns:
        Lista filtrada, um modelo por nome, ordenada do mais recente pro mais
        antigo — mesma ordem que a funcao ja devolvia antes do filtro existir.

    """
    modelos_concluidos = [modelo for modelo in modelos if modelo.status == "concluido"]

    modelo_mais_recente_por_nome = {}
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


# Le um cenario (experimento) inteiro: os dados dele + todos os modelos dentro.
def _ler_cenario(pasta: Path) -> Cenario | None:
    meta_arquivo = pasta / "meta.yaml"
    if not meta_arquivo.is_file():
        return None
    meta = _ler_meta(meta_arquivo)
    if not meta.get("name") or meta.get("lifecycle_stage") == "deleted":
        return None

    modelos = []
    for sub in sorted(pasta.iterdir()):
        if sub.is_dir():
            modelo = _ler_modelo(sub)
            if modelo:
                modelos.append(modelo)

    modelos_selecionados = _selecionar_modelos_validos(modelos)
    return Cenario(nome=meta["name"], experiment_id=meta.get("experiment_id", pasta.name), modelos=modelos_selecionados)


# Le a pasta mlruns inteira e devolve a lista de cenarios (so os que tem modelo).
def carregar_cenarios(pasta_mlruns: Path) -> list:
    """

    E a porta de entrada do modulo: aponta pra pasta mlruns e recebe de volta a
    lista de cenarios, cada um com seus modelos ja lidos. Pula as pastas que nao
    sao experimentos e ignora cenarios sem nenhum modelo.

    """
    if not pasta_mlruns.is_dir():
        return []

    cenarios = []
    for pasta in sorted(pasta_mlruns.iterdir()):
        if not pasta.is_dir() or pasta.name in PASTAS_IGNORADAS:
            continue
        cenario = _ler_cenario(pasta)
        if cenario and cenario.modelos:
            cenarios.append(cenario)

    cenarios.sort(key=lambda c: c.nome)
    return cenarios
