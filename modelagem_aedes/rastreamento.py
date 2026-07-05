"""

Versiona cada execucao de experimento no MLflow: guarda QUAL modelo foi usado,
os hiperparametros dele, as metricas de resumo e os arquivos gerados.

E um OBSERVADOR do pipeline: mora so aqui e e chamado so pelo main.py. O motor,
o dominio e o pipeline NAO sabem que o MLflow existe (a matematica continua
pura). Grava tudo numa pasta local (mlruns/), sem precisar de servidor no ar.

Organizacao: cada CENARIO vira um "experimento" do MLflow (ex.: cidade_regressao,
bairro_surto) e cada MODELO vira um "run" dentro dele (ex.: lightgbm,
random_forest) — assim da pra comparar os modelos de um cenario lado a lado.

Se o MLflow nao estiver instalado (ou der algum problema), tudo aqui vira
"no-op": o experimento roda igual, so nao fica versionado — pra nunca derrubar
o experimento por causa do rastreamento.

"""

import contextlib
import dataclasses
import math
import os
import re

import pandas as pd

from config import settings
from config.modelo import EspecificacaoModelo

# O MLflow 3+ marcou o backend de ARQUIVOS (a pasta mlruns/) como "modo
# manutencao" e, por padrao, se recusa a usar ele. Como aqui a gente quer
# justamente o versionamento local simples (uma pasta, sem servidor nem banco),
# a gente liga esse opt-in. Tem que ser ANTES de importar o mlflow.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

try:
    import mlflow

    MLFLOW_DISPONIVEL = True
except ImportError:
    MLFLOW_DISPONIVEL = False


# O cenario (experimento do MLflow) e o campo 'cenario' da config, se houver; senao, o nome.
def cenario_do_experimento(config) -> str:
    return getattr(config, "cenario", None) or config.nome


# O nome do modelo (vira o nome do run). A maioria tem 'modelo'; a comparacao tem 'modelo_regressao'.
def nome_do_modelo(config) -> str:
    especificacao = getattr(config, "modelo", None) or getattr(config, "modelo_regressao", None)
    return especificacao.nome if especificacao else "desconhecido"


def parametros_da_config(config) -> dict:
    """

    Achata a ficha de configuracao em parametros simples pro MLflow.

    Guarda o cenario e o algoritmo em destaque, e depois cada campo da config:
    as fichas de modelo viram nome + hiperparametros; valores simples vao direto;
    o resto (listas, tuplas) vira texto.

    """
    parametros = {
        "cenario": cenario_do_experimento(config),
        "algoritmo": nome_do_modelo(config),
    }
    for campo in dataclasses.fields(config):
        valor = getattr(config, campo.name)
        if isinstance(valor, EspecificacaoModelo):
            parametros[f"{campo.name}_nome"] = valor.nome
            for chave, ajuste in valor.parametros.items():
                parametros[f"{campo.name}.{chave}"] = ajuste
        elif isinstance(valor, (str, int, float, bool)) or valor is None:
            parametros[campo.name] = valor
        else:
            parametros[campo.name] = str(valor)
    return parametros


def metricas_das_saidas(saidas: dict) -> dict:
    """

    Tira metricas-resumo (a media de cada coluna numerica) de cada tabela de saida.

    E o que aparece no painel pra comparar os runs de forma rapida (ex.: MAE
    medio, R2 medio). A tabela completa vai como arquivo anexado ao run.

    """
    metricas = {}
    for nome_arquivo, tabela in saidas.items():
        base = nome_arquivo.replace(".csv", "")
        for coluna in tabela.columns:
            if pd.api.types.is_numeric_dtype(tabela[coluna]):
                media = tabela[coluna].mean()
                if pd.notna(media) and math.isfinite(media):
                    metricas[f"{base}__{coluna}_media"] = float(media)
    return metricas


@contextlib.contextmanager
def rastrear(config):
    """

    Abre um run do MLflow pro experimento e o fecha no fim (use com 'with').

    Se o MLflow nao estiver disponivel ou der erro na preparacao, nao faz nada
    (o experimento roda igual, so sem rastreamento).

    """
    if not MLFLOW_DISPONIVEL:
        yield None
        return
    try:
        settings.PASTA_MLRUNS.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(settings.PASTA_MLRUNS.as_uri())
        mlflow.set_experiment(cenario_do_experimento(config))
        run_do_mlflow = mlflow.start_run(run_name=nome_do_modelo(config))
    except Exception as erro:
        print(f"[aviso] MLflow indisponivel ({erro}); rodando sem rastreamento.")
        yield None
        return
    with run_do_mlflow as run:
        yield run


# O MLflow so aceita nestes nomes: letras, numeros, _ - . espaco : /. Qualquer
# outro caractere (ex.: o '+' de "base_+viz") vira '_' pra nao ser recusado.
_CARACTERES_PROIBIDOS = re.compile(r"[^0-9a-zA-Z_\-. :/]")


def nome_valido_mlflow(nome: str) -> str:
    return _CARACTERES_PROIBIDOS.sub("_", nome)


def registrar(config, saidas: dict, caminhos_artefatos) -> None:
    """

    Registra no run atual os parametros, as metricas-resumo e os arquivos gerados.

    Cada pedaco e registrado por conta propria: se um falhar (ex.: um nome
    invalido), os outros continuam, e nada disso derruba o experimento.

    """
    if not MLFLOW_DISPONIVEL:
        return
    try:
        parametros = {nome_valido_mlflow(chave): valor for chave, valor in parametros_da_config(config).items()}
        mlflow.log_params(parametros)
    except Exception as erro:
        print(f"[aviso] parametros nao registrados no MLflow ({erro}).")

    for nome_metrica, valor in metricas_das_saidas(saidas).items():
        try:
            mlflow.log_metric(nome_valido_mlflow(nome_metrica), valor)
        except Exception as erro:
            print(f"[aviso] metrica '{nome_metrica}' nao registrada ({erro}).")

    for caminho in caminhos_artefatos:
        try:
            mlflow.log_artifact(str(caminho))
        except Exception as erro:
            print(f"[aviso] artefato '{caminho}' nao anexado ({erro}).")
