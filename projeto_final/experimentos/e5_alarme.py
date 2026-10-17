"""E5: leitura de alarme no limiar convertido para a escala da notificacao (pre-declaracao, secao 7; DESCRITIVA).

Passos:
    1. Le os zips publicos DENGBR18 a DENGBR24 (OpenDataSUS) em pedacos, so 4 colunas, tudo como texto,
       e conta os confirmados de Porto Alegre com `DT_SIN_PRI` em 2018 a 2023 por municipio de NOTIFICACAO
       e por municipio de RESIDENCIA. Nenhum registro individual e gravado: so contagens por arquivo.
    2. `r` = notificacao / residencia; `L = 421 x r`. Confere a ANCORA: a soma de `casos_confirmados` de
       `dados/tabela_final.csv` nas semanas iniciadas em 2018 a 2023 (12.785) deve ficar a ~1% do numerador;
       se nao, a etapa PARA (codigo 1) e grava so `razao.json` para investigacao.
    3. Metricas de alarme (VP, FN, FP, sensibilidade, precisao, falsos por ano = FP / 1,96) por braco x folha e
       composto N=13, h em {1, 4, 8}, nas 102 semanas-alvo do `completo` em cada h (mesmo denominador para todos),
       com `L` convertido e com 421 sem conversao.

Definicao de alarme: a do codigo antigo (`>` estrito, semanas), ver `aedes/alarme.py`.

Grava em `resultados/ciencia/E5_alarme/`: `razao.json`, `alarme.csv`, `alarme_421_sem_conversao.csv`, `E5_alarme.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`; a leitura dos zips leva minutos):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.e5_alarme > /dev/null 2>&1 &
"""

import pathlib
import sys
import zipfile

import pandas as pd

from aedes.alarme import (
    ANOS_DA_AVALIACAO,
    CODIGO_DE_PORTO_ALEGRE,
    COLUNA_DA_CLASSIFICACAO,
    COLUNA_DA_DATA_DE_SINTOMAS,
    COLUNA_DE_NOTIFICACAO,
    COLUNA_DE_RESIDENCIA,
    LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS,
    ContagemDeConfirmados,
    MetricasDoAlarme,
    calcular_metricas_do_alarme,
    calcular_razao_notificacao_residencia,
    contar_confirmados_de_porto_alegre,
    converter_limiar,
)
from aedes.bracos import NOMES_DOS_BRACOS
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
)
from aedes.familias import NOME_DO_COMPOSTO
from aedes.metricas import (
    COLUNA_DO_BRACO,
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_PREVISTO,
    COLUNA_DO_REAL,
    recortar_janela_de_avaliacao,
)
from experimentos.comum_ciencia import (
    PASTA_DA_CIENCIA,
    PASTA_DO_PROJETO,
    RegistradorDeLog,
    gravar_json_de_forma_atomica,
)
from experimentos.e3_composto import (
    COLUNA_DA_FOLHA,
    COLUNA_DA_JANELA_N,
    JANELA_PRIMARIA,
    exigir_travas_da_e2_aprovadas,
    ler_previsoes_da_e2,
)
from experimentos.e3_composto import CAMINHO_DAS_PREVISOES as CAMINHO_DAS_PREVISOES_DA_E3
from experimentos.e3_composto import CAMINHO_DO_RESUMO as CAMINHO_DO_RESUMO_DA_E3

PASTA_DE_SAIDA = PASTA_DA_CIENCIA / "E5_alarme"
CAMINHO_DA_RAZAO = PASTA_DE_SAIDA / "razao.json"
CAMINHO_DO_ALARME = PASTA_DE_SAIDA / "alarme.csv"
CAMINHO_DO_ALARME_SEM_CONVERSAO = PASTA_DE_SAIDA / "alarme_421_sem_conversao.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E5_alarme.log")

PASTA_DOS_ZIPS_DENGBR = PASTA_DO_PROJETO.parent / "modelagem_aedes" / "dados" / "entradas" / "bases_governo"
CAMINHO_DA_TABELA_FINAL = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
ANOS_DOS_ARQUIVOS_PRINCIPAIS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)
ANOS_DOS_ARQUIVOS_SEM_2024 = (2018, 2019, 2020, 2021, 2022, 2023)
PRIMEIRO_ANO_DOS_SINTOMAS = 2018
ULTIMO_ANO_DOS_SINTOMAS = 2023
LINHAS_POR_PEDACO = 500_000
COLUNAS_LIDAS = [
    COLUNA_DE_NOTIFICACAO,
    COLUNA_DE_RESIDENCIA,
    COLUNA_DA_CLASSIFICACAO,
    COLUNA_DA_DATA_DE_SINTOMAS,
]

SOMA_DA_ANCORA_DA_TABELA = 12785
TOLERANCIA_DA_ANCORA_DO_NUMERADOR = 0.01
HORIZONTES_DO_ALARME = (1, 4, 8)
BRACO_DA_GRADE = "completo"
FOLHA_DA_GRADE = 5
NOME_DA_FOLHA_DO_COMPOSTO = "composto"
SEMANAS_ESPERADAS_NA_JANELA = 102
COLUNAS_DO_ALARME = (
    COLUNA_DO_BRACO,
    COLUNA_DA_FOLHA,
    COLUNA_DO_HORIZONTE,
    "limiar",
    "n",
    "semanas_de_surto",
    "VP",
    "FN",
    "FP",
    "VN",
    "sensibilidade",
    "precisao",
    "falsos_por_ano",
)


def caminho_do_zip(ano_do_arquivo: int) -> pathlib.Path:
    """Caminho de `DENGBRaa.csv.zip` em `modelagem_aedes/dados/entradas/bases_governo/`."""
    sufixo = str(ano_do_arquivo)[-2:]
    return PASTA_DOS_ZIPS_DENGBR / f"DENGBR{sufixo}.csv.zip"


def contar_confirmados_de_um_zip(caminho_do_arquivo_zip: pathlib.Path) -> tuple[ContagemDeConfirmados, int]:
    """Le um zip em pedacos e soma os confirmados de Porto Alegre com sintomas em 2018 a 2023.

    Args:
        caminho_do_arquivo_zip: Zip publico (OpenDataSUS) com um unico CSV.

    Returns:
        `(contagem, linhas_lidas)`; nada individual e guardado.

    Raises:
        ValueError: Se o zip nao tiver exatamente um arquivo.
    """
    total_por_notificacao = 0
    total_por_residencia = 0
    linhas_lidas = 0
    with zipfile.ZipFile(caminho_do_arquivo_zip) as arquivo_zip:
        nomes_dentro_do_zip = arquivo_zip.namelist()
        if len(nomes_dentro_do_zip) != 1:
            raise ValueError(f"{caminho_do_arquivo_zip.name}: esperado 1 arquivo, achei {nomes_dentro_do_zip}")
        with arquivo_zip.open(nomes_dentro_do_zip[0]) as fluxo_csv:
            leitor = pd.read_csv(
                fluxo_csv,
                usecols=COLUNAS_LIDAS,
                dtype=str,
                chunksize=LINHAS_POR_PEDACO,
                low_memory=False,
            )
            for pedaco in leitor:
                linhas_lidas += len(pedaco)
                contagem_do_pedaco = contar_confirmados_de_porto_alegre(
                    pedaco, PRIMEIRO_ANO_DOS_SINTOMAS, ULTIMO_ANO_DOS_SINTOMAS
                )
                total_por_notificacao += contagem_do_pedaco.por_notificacao
                total_por_residencia += contagem_do_pedaco.por_residencia
    contagem = ContagemDeConfirmados(por_notificacao=total_por_notificacao, por_residencia=total_por_residencia)
    return contagem, linhas_lidas


def somar_contagens(contagens: list[ContagemDeConfirmados]) -> ContagemDeConfirmados:
    """Soma numeradores e denominadores de varios arquivos."""
    por_notificacao = 0
    por_residencia = 0
    for contagem in contagens:
        por_notificacao += contagem.por_notificacao
        por_residencia += contagem.por_residencia
    return ContagemDeConfirmados(por_notificacao=por_notificacao, por_residencia=por_residencia)


def calcular_soma_da_ancora_na_tabela() -> int:
    """Soma de `casos_confirmados` em `dados/tabela_final.csv` nas semanas iniciadas em 2018 a 2023 (serie por notificacao)."""
    tabela = pd.read_csv(CAMINHO_DA_TABELA_FINAL, parse_dates=[CONFIGURACAO_DADOS.coluna_de_data])
    ano_da_semana = tabela[CONFIGURACAO_DADOS.coluna_de_data].dt.year
    no_periodo = (ano_da_semana >= PRIMEIRO_ANO_DOS_SINTOMAS) & (ano_da_semana <= ULTIMO_ANO_DOS_SINTOMAS)
    casos_do_periodo = tabela.loc[no_periodo, CONFIGURACAO_DADOS.coluna_de_casos]
    return int(round(float(casos_do_periodo.sum())))


def descrever_razao(contagem: ContagemDeConfirmados) -> dict[str, object]:
    """Contagens e `r` de uma versao (conjunto de arquivos)."""
    razao = calcular_razao_notificacao_residencia(contagem.por_notificacao, contagem.por_residencia)
    return {
        "numerador": contagem.por_notificacao,
        "denominador": contagem.por_residencia,
        "r": razao,
        "L": converter_limiar(LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS, razao),
    }


def medir_a_razao() -> dict[str, object]:
    """Passos 1 e 2: contagens por arquivo, `r` das duas versoes, `L` e a conferencia da ancora.

    Returns:
        Dicionario do `razao.json` (inclui `ancora_ok`).
    """
    contagens_por_ano: dict[int, ContagemDeConfirmados] = {}
    por_arquivo: dict[str, dict[str, int]] = {}
    for ano_do_arquivo in ANOS_DOS_ARQUIVOS_PRINCIPAIS:
        caminho = caminho_do_zip(ano_do_arquivo)
        contagem, linhas_lidas = contar_confirmados_de_um_zip(caminho)
        contagens_por_ano[ano_do_arquivo] = contagem
        por_arquivo[caminho.name] = {
            "linhas_lidas": linhas_lidas,
            "numerador": contagem.por_notificacao,
            "denominador": contagem.por_residencia,
        }
        REGISTRADOR.registrar(
            f"{caminho.name}: {linhas_lidas} linhas; confirmados POA com sintomas 2018-2023: "
            f"notificacao={contagem.por_notificacao} residencia={contagem.por_residencia}"
        )

    contagem_principal = somar_contagens([contagens_por_ano[ano] for ano in ANOS_DOS_ARQUIVOS_PRINCIPAIS])
    contagem_sem_2024 = somar_contagens([contagens_por_ano[ano] for ano in ANOS_DOS_ARQUIVOS_SEM_2024])
    principal = descrever_razao(contagem_principal)
    sem_2024 = descrever_razao(contagem_sem_2024)

    soma_da_tabela = calcular_soma_da_ancora_na_tabela()
    diferenca_relativa = (contagem_principal.por_notificacao - SOMA_DA_ANCORA_DA_TABELA) / SOMA_DA_ANCORA_DA_TABELA
    ancora_ok = abs(diferenca_relativa) <= TOLERANCIA_DA_ANCORA_DO_NUMERADOR and soma_da_tabela == SOMA_DA_ANCORA_DA_TABELA
    REGISTRADOR.registrar(
        f"ancora: soma da tabela={soma_da_tabela} (esperado {SOMA_DA_ANCORA_DA_TABELA}); "
        f"numerador={contagem_principal.por_notificacao}; diferenca={100.0 * diferenca_relativa:.3f}%; ancora_ok={ancora_ok}"
    )
    return {
        "r": principal["r"],
        "numerador": principal["numerador"],
        "denominador": principal["denominador"],
        "limiar_base": LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS,
        "L": principal["L"],
        "versoes": {
            "DENGBR18_a_24 (principal)": principal,
            "DENGBR18_a_23": sem_2024,
        },
        "por_arquivo": por_arquivo,
        "ancora": {
            "soma_casos_confirmados_tabela_final_semanas_2018_2023": soma_da_tabela,
            "valor_esperado": SOMA_DA_ANCORA_DA_TABELA,
            "numerador_menos_ancora_pct": 100.0 * diferenca_relativa,
            "tolerancia_pct": 100.0 * TOLERANCIA_DA_ANCORA_DO_NUMERADOR,
        },
        "ancora_ok": bool(ancora_ok),
        "definicao": {
            "confirmado": "CLASSI_FIN em 10, 11 ou 12",
            "porto_alegre": CODIGO_DE_PORTO_ALEGRE,
            "periodo_dos_sintomas": f"DT_SIN_PRI de {PRIMEIRO_ANO_DOS_SINTOMAS} a {ULTIMO_ANO_DOS_SINTOMAS}",
            "r": "confirmados por ID_MUNICIP / confirmados por ID_MN_RESI",
            "evento": "semana com real > L (estrito) e alarme com previsto > L (estrito), como em calcular_alarme.py antigo",
            "anos_da_avaliacao": ANOS_DA_AVALIACAO,
        },
    }


def ler_composto_primario_na_janela() -> pd.DataFrame:
    """Composto N = 13 na janela de avaliacao (E3 concluida)."""
    if not CAMINHO_DO_RESUMO_DA_E3.exists():
        raise FileNotFoundError(f"E3 nao concluida: {CAMINHO_DO_RESUMO_DA_E3} ausente.")
    todos = pd.read_csv(CAMINHO_DAS_PREVISOES_DA_E3, parse_dates=["data_origem", COLUNA_DATA_ALVO], float_precision="round_trip")
    do_n_primario = todos.loc[todos[COLUNA_DA_JANELA_N] == JANELA_PRIMARIA]
    return recortar_janela_de_avaliacao(do_n_primario, CONFIGURACAO_AVALIACAO)


def semanas_do_completo_no_horizonte(previsoes_na_janela: pd.DataFrame, horizonte: int) -> pd.DatetimeIndex:
    """As `data_alvo` do `completo` folha 5 no horizonte (as 102 semanas do denominador comum)."""
    e_completo = previsoes_na_janela[COLUNA_DO_BRACO] == BRACO_DA_GRADE
    e_da_folha = previsoes_na_janela[COLUNA_DA_FOLHA] == FOLHA_DA_GRADE
    e_do_horizonte = previsoes_na_janela[COLUNA_DO_HORIZONTE] == horizonte
    selecao = previsoes_na_janela.loc[e_completo & e_da_folha & e_do_horizonte]
    return pd.DatetimeIndex(selecao[COLUNA_DATA_ALVO])


def montar_linha_do_alarme(
    braco: str,
    folha: str | int,
    horizonte: int,
    limiar: float,
    previsoes_do_candidato: pd.DataFrame,
    semanas_do_denominador: pd.DatetimeIndex,
) -> dict[str, object]:
    """Metricas do alarme de um candidato nas semanas do denominador comum."""
    esta_no_denominador = previsoes_do_candidato[COLUNA_DATA_ALVO].isin(semanas_do_denominador)
    nas_semanas = previsoes_do_candidato.loc[esta_no_denominador].sort_values(COLUNA_DATA_ALVO)
    metricas: MetricasDoAlarme = calcular_metricas_do_alarme(
        nas_semanas[COLUNA_DO_REAL].to_numpy(dtype=float),
        nas_semanas[COLUNA_DO_PREVISTO].to_numpy(dtype=float),
        limiar,
    )
    return {
        COLUNA_DO_BRACO: braco,
        COLUNA_DA_FOLHA: folha,
        COLUNA_DO_HORIZONTE: horizonte,
        "limiar": limiar,
        "n": metricas.n,
        "semanas_de_surto": metricas.semanas_de_surto,
        "VP": metricas.verdadeiros_positivos,
        "FN": metricas.falsos_negativos,
        "FP": metricas.falsos_positivos,
        "VN": metricas.verdadeiros_negativos,
        "sensibilidade": metricas.sensibilidade,
        "precisao": metricas.precisao,
        "falsos_por_ano": metricas.falsos_por_ano,
    }


def montar_tabela_do_alarme(
    previsoes_na_janela: pd.DataFrame,
    composto_na_janela: pd.DataFrame,
    limiar: float,
) -> pd.DataFrame:
    """Alarme de cada braco x folha (8 x 2) e do composto N=13, em h = 1, 4 e 8, com um limiar dado."""
    linhas: list[dict[str, object]] = []
    for horizonte in HORIZONTES_DO_ALARME:
        semanas_do_denominador = semanas_do_completo_no_horizonte(previsoes_na_janela, horizonte)
        for braco in NOMES_DOS_BRACOS:
            for folha in (5, 20):
                e_do_braco = previsoes_na_janela[COLUNA_DO_BRACO] == braco
                e_da_folha = previsoes_na_janela[COLUNA_DA_FOLHA] == folha
                e_do_horizonte = previsoes_na_janela[COLUNA_DO_HORIZONTE] == horizonte
                do_candidato = previsoes_na_janela.loc[e_do_braco & e_da_folha & e_do_horizonte]
                linhas.append(montar_linha_do_alarme(braco, folha, horizonte, limiar, do_candidato, semanas_do_denominador))
        do_composto = composto_na_janela.loc[composto_na_janela[COLUNA_DO_HORIZONTE] == horizonte]
        linhas.append(
            montar_linha_do_alarme(
                NOME_DO_COMPOSTO, NOME_DA_FOLHA_DO_COMPOSTO, horizonte, limiar, do_composto, semanas_do_denominador
            )
        )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_ALARME))


def main() -> int:
    """Mede `r`, confere a ancora e, se passar, grava as duas tabelas de alarme.

    Returns:
        0 se tudo passou; 1 se a ancora do numerador divergiu (so `razao.json` e gravado).
    """
    exigir_travas_da_e2_aprovadas()
    REGISTRADOR.registrar(f"inicio E5: zips em {PASTA_DOS_ZIPS_DENGBR}")
    razao = medir_a_razao()
    gravar_json_de_forma_atomica(razao, CAMINHO_DA_RAZAO)
    if not razao["ancora_ok"]:
        REGISTRADOR.registrar("ANCORA DIVERGE: tabelas de alarme NAO geradas; investigar antes de seguir.")
        return 1

    previsoes_na_janela = recortar_janela_de_avaliacao(ler_previsoes_da_e2(), CONFIGURACAO_AVALIACAO)
    composto_na_janela = ler_composto_primario_na_janela()

    limiar_convertido = float(razao["L"])
    tabela_convertida = montar_tabela_do_alarme(previsoes_na_janela, composto_na_janela, limiar_convertido)
    tabela_sem_conversao = montar_tabela_do_alarme(
        previsoes_na_janela, composto_na_janela, float(LIMIAR_DO_ALERTA_NA_ESCALA_DOS_CASOS)
    )
    tabela_convertida.to_csv(CAMINHO_DO_ALARME, index=False)
    tabela_sem_conversao.to_csv(CAMINHO_DO_ALARME_SEM_CONVERSAO, index=False)

    valores_de_n = sorted(tabela_convertida["n"].unique().tolist())
    REGISTRADOR.registrar(
        f"fim E5: r={razao['r']:.6f} L={limiar_convertido:.3f}; {len(tabela_convertida)} linhas em {CAMINHO_DO_ALARME.name} "
        f"e {len(tabela_sem_conversao)} em {CAMINHO_DO_ALARME_SEM_CONVERSAO.name}; valores de n={valores_de_n} "
        f"(esperado {SEMANAS_ESPERADAS_NA_JANELA})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
