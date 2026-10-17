"""E1: remedicao do quantil, so com o periodo de CALIBRACAO (decide o modelo das outras etapas).

Pre-declaracao: `analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`, secao 3.
Candidatos: quantis 0,50, 0,70, 0,80, 0,85 e 0,90; so a folha 5, braco `completo`,
h em {1, 4, 8, 12}; os demais hiperparametros ficam fixos
(`dataclasses.replace(FOLHA_5, quantil=q)`).

SO A CALIBRACAO: o criterio e o MAE nas semanas-alvo ate 31/12/2023, media dos
4 horizontes. A matriz e cortada em `data_alvo <= 2023-12-31` ANTES do laco. Isso
da as mesmas previsoes (bit a bit) que rodar a matriz inteira e filtrar, porque
com o corte pela resposta o treino de cada origem so usa linhas com `data_alvo <= t`;
nenhuma linha removida entraria no treino de uma origem que sobra (provado em
`testes/test_walk_forward_com_corte.py`). A avaliacao (2024 em diante) nunca e vista.

Regra de desempate (pre-declarada): o 0,85 CONTINUA se o melhor candidato for
menos de 2% melhor que ele; so troca com vantagem de 2% ou mais.

TRAVA 3: o quantil 0,85 desta etapa reproduz `resultados/referencia/previsoes.csv`
(braco `referencia`) nas mesmas (h, data_alvo) da calibracao, diferenca < 1e-9.
Se falhar, a etapa para: `decisao.json` leva so a trava, `metricas.csv` nao e gravado
e o codigo de saida e 1.

Grava em `resultados/ciencia/E1_quantil/`:
    - `parciais/previsoes_q<nnn>_h<hh>.csv`: um por (quantil, h);
    - `previsoes.csv`: quantil, h, data_origem, data_alvo, real, previsto;
    - `metricas.csv`: quantil, h, n, mae, cobertura (fracao com real > previsto);
    - `decisao.json`: MAE medio por quantil, melhor, ganho relativo, quantil escolhido, trava 3;
    - `E1_quantil.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`)

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.e1_quantil \\
        --quantis 0.5 0.7 > /dev/null 2>&1 &
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e1_quantil --so-juntar

Parciais existentes sao pulados; `--refazer` forca. Com os 20 parciais, o proprio
script junta e decide.
"""

import argparse
import dataclasses
import pathlib
import sys
import time

import pandas as pd

from aedes.bracos import montar_matriz_do_braco
from aedes.comparacoes import (
    calcular_cobertura,
    comparar_previsoes_com_gabarito,
    decidir_quantil,
)
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
)
from aedes.metricas import COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE, erro_absoluto_medio
from aedes.walk_forward import executar_walk_forward
from aedes.walk_forward_com_corte import recortar_matriz_ate_a_data_alvo
from experimentos.comum_ciencia import (
    NOME_DA_REFERENCIA_FOLHA_5,
    PASTA_DA_CIENCIA,
    TOLERANCIA_DAS_TRAVAS,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_json_de_forma_atomica,
    gravar_parcial,
    ler_previsoes_da_referencia,
    validar_horizontes,
)

PASTA_DE_SAIDA = PASTA_DA_CIENCIA / "E1_quantil"
PASTA_DOS_PARCIAIS = PASTA_DE_SAIDA / "parciais"
CAMINHO_DAS_PREVISOES = PASTA_DE_SAIDA / "previsoes.csv"
CAMINHO_DAS_METRICAS = PASTA_DE_SAIDA / "metricas.csv"
CAMINHO_DA_DECISAO = PASTA_DE_SAIDA / "decisao.json"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E1_quantil.log")

QUANTIS_CANDIDATOS = (0.50, 0.70, 0.80, 0.85, 0.90)
QUANTIL_DE_REFERENCIA = 0.85
GANHO_MINIMO_PARA_TROCAR = 0.02
HORIZONTES_DA_E1 = (1, 4, 8, 12)
BRACO_DA_E1 = "completo"

COLUNA_DO_QUANTIL = "quantil"
COLUNAS_DO_ARQUIVO_DE_PREVISOES = (
    COLUNA_DO_QUANTIL,
    COLUNA_DO_HORIZONTE,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DATA_ALVO,
    "real",
    "previsto",
)
COLUNAS_DAS_METRICAS = (COLUNA_DO_QUANTIL, COLUNA_DO_HORIZONTE, "n", "mae", "cobertura")
CHAVE_DA_TRAVA = [COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]


def sufixo_do_quantil(quantil: float) -> str:
    """Quantil em tres digitos para nome de arquivo: 0,85 vira `085`."""
    return f"{round(quantil * 100):03d}"


def caminho_do_parcial(quantil: float, horizonte: int) -> pathlib.Path:
    """Caminho do parcial de um quantil e um horizonte."""
    return PASTA_DOS_PARCIAIS / f"previsoes_q{sufixo_do_quantil(quantil)}_h{horizonte:02d}.csv"


def rodar_um_pedaco(quantil: float, horizonte: int, tabela_cortada: pd.DataFrame) -> pd.DataFrame:
    """Roda o walk-forward da calibracao (matriz cortada em `data_alvo <= 31/12/2023`) de um quantil e um horizonte."""
    configuracao_do_modelo = dataclasses.replace(
        FOLHA_5, nome=f"histgb_folha5_q{sufixo_do_quantil(quantil)}", quantil=quantil
    )
    matriz_inteira = montar_matriz_do_braco(
        tabela_cortada, horizonte, BRACO_DA_E1, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    matriz_da_calibracao = recortar_matriz_ate_a_data_alvo(
        matriz_inteira, CONFIGURACAO_AVALIACAO.fim_da_calibracao
    )
    inicio = time.perf_counter()
    previsoes = executar_walk_forward(
        matriz_da_calibracao, horizonte, configuracao_do_modelo, CONFIGURACAO_AVALIACAO
    )
    segundos = time.perf_counter() - inicio

    previsoes[COLUNA_DO_QUANTIL] = quantil
    previsoes = previsoes[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]
    REGISTRADOR.registrar(
        f"pedaco quantil={quantil:.2f} h={horizonte:2d} linhas_da_matriz={len(matriz_da_calibracao)} "
        f"previsoes={len(previsoes)} tempo={segundos:.1f}s"
    )
    return previsoes


def listar_parciais_faltantes() -> list[pathlib.Path]:
    """Parciais que ainda nao existem entre os 20 esperados (5 quantis x 4 horizontes)."""
    faltantes: list[pathlib.Path] = []
    for quantil in QUANTIS_CANDIDATOS:
        for horizonte in HORIZONTES_DA_E1:
            caminho = caminho_do_parcial(quantil, horizonte)
            if not caminho.exists():
                faltantes.append(caminho)
    return faltantes


def juntar_parciais() -> pd.DataFrame:
    """Junta os 20 parciais na ordem quantil, horizonte.

    Raises:
        FileNotFoundError: Se algum parcial nao existir.
    """
    faltantes = listar_parciais_faltantes()
    if faltantes:
        nomes = ", ".join(caminho.name for caminho in faltantes[:5])
        raise FileNotFoundError(f"{len(faltantes)} parcial(is) ausente(s), ex.: {nomes}")

    tabelas: list[pd.DataFrame] = []
    for quantil in QUANTIS_CANDIDATOS:
        for horizonte in HORIZONTES_DA_E1:
            parcial = pd.read_csv(
                caminho_do_parcial(quantil, horizonte),
                parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
            )
            tabelas.append(parcial)
    return pd.concat(tabelas, ignore_index=True)[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]


def calcular_metricas_da_calibracao(previsoes: pd.DataFrame) -> pd.DataFrame:
    """n, MAE e cobertura por quantil e horizonte, sobre todas as previsoes da calibracao."""
    linhas: list[dict[str, object]] = []
    for quantil in QUANTIS_CANDIDATOS:
        do_quantil = previsoes.loc[previsoes[COLUNA_DO_QUANTIL] == quantil]
        for horizonte in HORIZONTES_DA_E1:
            do_horizonte = do_quantil.loc[do_quantil[COLUNA_DO_HORIZONTE] == horizonte]
            valores_reais = do_horizonte["real"]
            valores_previstos = do_horizonte["previsto"]
            linhas.append(
                {
                    COLUNA_DO_QUANTIL: quantil,
                    COLUNA_DO_HORIZONTE: horizonte,
                    "n": len(do_horizonte),
                    "mae": erro_absoluto_medio(valores_reais, valores_previstos),
                    "cobertura": calcular_cobertura(valores_reais, valores_previstos),
                }
            )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DAS_METRICAS))


def conferir_trava_3(previsoes: pd.DataFrame) -> dict[str, object]:
    """Trava 3: o quantil 0,85 reproduz a referencia nas mesmas (h, data_alvo) da calibracao."""
    do_quantil_de_referencia = previsoes.loc[previsoes[COLUNA_DO_QUANTIL] == QUANTIL_DE_REFERENCIA]

    referencia = ler_previsoes_da_referencia()
    da_folha_5 = referencia[COLUNA_DO_BRACO] == NOME_DA_REFERENCIA_FOLHA_5
    dos_horizontes_da_e1 = referencia[COLUNA_DO_HORIZONTE].isin(HORIZONTES_DA_E1)
    ate_o_fim_da_calibracao = referencia[COLUNA_DATA_ALVO] <= CONFIGURACAO_AVALIACAO.fim_da_calibracao
    referencia_na_calibracao = referencia.loc[da_folha_5 & dos_horizontes_da_e1 & ate_o_fim_da_calibracao]

    resultado = comparar_previsoes_com_gabarito(
        do_quantil_de_referencia, referencia_na_calibracao, CHAVE_DA_TRAVA, TOLERANCIA_DAS_TRAVAS
    )
    conteudo = dataclasses.asdict(resultado)
    conteudo["gabarito"] = (
        f"resultados/referencia/previsoes.csv, braco {NOME_DA_REFERENCIA_FOLHA_5}, "
        f"h em {list(HORIZONTES_DA_E1)}, data_alvo <= {CONFIGURACAO_AVALIACAO.fim_da_calibracao.date()}"
    )
    return conteudo


def juntar_e_decidir(inicio_da_rodada: float) -> int:
    """Junta os parciais, confere a trava 3 e (so se passar) grava metricas e decisao.

    Returns:
        0 se a trava 3 passou, 1 se falhou.
    """
    previsoes = juntar_parciais()
    previsoes.to_csv(CAMINHO_DAS_PREVISOES, index=False)

    trava_3 = conferir_trava_3(previsoes)
    if not trava_3["passou"]:
        gravar_json_de_forma_atomica({"trava_3": trava_3, "decisao": None}, CAMINHO_DA_DECISAO)
        REGISTRADOR.registrar(
            "TRAVA 3 FALHOU: a etapa para. previsoes.csv e decisao.json (so a trava) gravados para "
            "diagnostico; metricas.csv NAO foi gerado e nenhum resultado deve ser lido."
        )
        return 1

    metricas = calcular_metricas_da_calibracao(previsoes)
    metricas.to_csv(CAMINHO_DAS_METRICAS, index=False)

    mae_medio_por_quantil: dict[float, float] = {}
    for quantil in QUANTIS_CANDIDATOS:
        do_quantil = metricas.loc[metricas[COLUNA_DO_QUANTIL] == quantil]
        mae_medio_por_quantil[quantil] = float(do_quantil["mae"].mean())
    decisao = decidir_quantil(mae_medio_por_quantil, QUANTIL_DE_REFERENCIA, GANHO_MINIMO_PARA_TROCAR)

    mae_medio_com_chave_em_texto: dict[str, float] = {}
    for quantil, mae_medio in decisao.mae_medio_por_quantil.items():
        mae_medio_com_chave_em_texto[f"{quantil:.2f}"] = mae_medio
    n_por_horizonte: dict[str, int] = {}
    do_quantil_de_referencia = metricas.loc[metricas[COLUNA_DO_QUANTIL] == QUANTIL_DE_REFERENCIA]
    for horizonte in HORIZONTES_DA_E1:
        linha = do_quantil_de_referencia.loc[do_quantil_de_referencia[COLUNA_DO_HORIZONTE] == horizonte]
        n_por_horizonte[str(horizonte)] = int(linha["n"].iloc[0])

    conteudo = {
        "regra": "0,85 continua se o melhor candidato for menos de 2% melhor (pre-declaracao, secao 3)",
        "criterio": "MAE medio dos horizontes 1, 4, 8 e 12, so com semanas-alvo ate 2023-12-31",
        "mae_medio_por_quantil": mae_medio_com_chave_em_texto,
        "quantil_de_referencia": decisao.quantil_de_referencia,
        "melhor_quantil": decisao.melhor_quantil,
        "mae_do_melhor": decisao.mae_do_melhor,
        "mae_da_referencia": decisao.mae_da_referencia,
        "ganho_relativo": decisao.ganho_relativo,
        "ganho_minimo_para_trocar": decisao.ganho_minimo_para_trocar,
        "quantil_escolhido": decisao.quantil_escolhido,
        "quantil_mudou": decisao.quantil_escolhido != decisao.quantil_de_referencia,
        "n_por_horizonte": n_por_horizonte,
        "trava_3": trava_3,
    }
    gravar_json_de_forma_atomica(conteudo, CAMINHO_DA_DECISAO)

    segundos = time.perf_counter() - inicio_da_rodada
    REGISTRADOR.registrar(
        f"juncao: {len(previsoes)} previsoes; trava 3 OK; quantil_escolhido={decisao.quantil_escolhido} "
        f"(melhor={decisao.melhor_quantil}, ganho={decisao.ganho_relativo:.4f}); "
        f"tempo deste processo={segundos:.1f}s"
    )
    return 0


def ler_argumentos() -> argparse.Namespace:
    """Le `--quantis`, `--horizontes`, `--refazer` e `--so-juntar`."""
    leitor = argparse.ArgumentParser(description="E1: remedicao do quantil na calibracao, em pedacos.")
    leitor.add_argument("--quantis", type=float, nargs="+", default=None,
                        help="Quantis a rodar (entre 0.50 0.70 0.80 0.85 0.90). Sem isso, roda os 5.")
    leitor.add_argument("--horizontes", type=int, nargs="+", default=None,
                        help="Horizontes a rodar (entre 1 4 8 12). Sem isso, roda os 4.")
    leitor.add_argument("--refazer", action="store_true", help="Recalcula parciais que ja existem.")
    leitor.add_argument("--so-juntar", action="store_true",
                        help="Nao treina nada: junta os 20 parciais ja gravados, confere a trava 3 e decide.")
    argumentos = leitor.parse_args()
    if argumentos.quantis is not None:
        quantis_invalidos = [q for q in argumentos.quantis if q not in QUANTIS_CANDIDATOS]
        if quantis_invalidos:
            leitor.error(f"quantis fora de {list(QUANTIS_CANDIDATOS)}: {quantis_invalidos}")
    if argumentos.horizontes is not None:
        try:
            validar_horizontes(argumentos.horizontes)
        except ValueError as erro:
            leitor.error(str(erro))
        horizontes_invalidos = [h for h in argumentos.horizontes if h not in HORIZONTES_DA_E1]
        if horizontes_invalidos:
            leitor.error(f"horizontes fora de {list(HORIZONTES_DA_E1)}: {horizontes_invalidos}")
    return argumentos


def main() -> int:
    """Roda os pedacos pedidos e, se os 20 parciais existirem, junta, confere a trava 3 e decide."""
    inicio_da_rodada = time.perf_counter()
    argumentos = ler_argumentos()

    if not argumentos.so_juntar:
        quantis = tuple(argumentos.quantis) if argumentos.quantis else QUANTIS_CANDIDATOS
        horizontes = tuple(argumentos.horizontes) if argumentos.horizontes else HORIZONTES_DA_E1
        tabela_cortada = carregar_tabela_cortada()
        REGISTRADOR.registrar(f"inicio: quantis={list(quantis)} horizontes={list(horizontes)}")
        for quantil in quantis:
            for horizonte in horizontes:
                caminho = caminho_do_parcial(quantil, horizonte)
                if caminho.exists() and not argumentos.refazer:
                    REGISTRADOR.registrar(f"pulado (parcial ja existe): {caminho.name}")
                    continue
                previsoes = rodar_um_pedaco(quantil, horizonte, tabela_cortada)
                gravar_parcial(previsoes, caminho)

    faltantes = listar_parciais_faltantes()
    if faltantes:
        REGISTRADOR.registrar(f"fim do pedaco: faltam {len(faltantes)} de 20 parciais; juncao adiada.")
        return 0
    return juntar_e_decidir(inicio_da_rodada)


if __name__ == "__main__":
    sys.exit(main())
