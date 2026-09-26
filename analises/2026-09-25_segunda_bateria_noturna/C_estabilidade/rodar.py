"""Rodada C da segunda bateria noturna: estabilidade das vencedoras da busca.

Pergunta (PRE_DECLARACAO.md, secao C): as vencedoras HB_best e LGB_best da
busca de hiperparametros (analises/2026-09-25_busca_de_hiperparametros/) sao
estaveis a troca de semente aleatoria, e concordam em sinal com o cenario
adotado na temporada de 2026?

Reusa o harness da bateria de 23/09 (analises/2026-09-23_bateria_noturna/
harness.py) sem altera-lo: so a montagem de features e o walk-forward pareado
por data_alvo sao dele. Este script so monta as fichas de modelo das
vencedoras (a partir de vencedoras.json) e organiza as 5 sementes.

⚠️ NAO altera harness.py, o pipeline nem outras pastas de analise. So le.
"""

import concurrent.futures
import json
import os
import pathlib
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_HARNESS = PASTA_DESTE_ARQUIVO.parent.parent / "2026-09-23_bateria_noturna"
if str(PASTA_HARNESS) not in sys.path:
    sys.path.insert(0, str(PASTA_HARNESS))

import harness  # noqa: E402  (depende do sys.path ajustado acima)

PASTA_BUSCA = PASTA_DESTE_ARQUIVO.parent.parent / "2026-09-25_busca_de_hiperparametros"
PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"
PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)

SEMENTES = (1, 2, 3, 4, 5)
QUANTIL_DE_REFERENCIA = 0.85
MAXIMO_DE_PROCESSOS = 5

# Trava do cenario adotado (emenda de 25/09/2026, 23h50): mesma janela de
# avaliacao do painel (harness.INICIO_DA_AVALIACAO, 2024-01-01) ate a ultima
# semana coberta pela pre-declaracao original, 01/02/2026.
FIM_DA_TRAVA = pd.Timestamp("2026-02-01")
TOLERANCIA_DA_TRAVA = 0.2
ANCORAS_DA_TRAVA = {1: 97.4, 12: 280.0}
HORIZONTES_DA_TRAVA = (1, 4, 8, 12)

# Recorte 2026 da secao C: da virada do ano ate a ultima semana madura
# (corte de maturidade de 12 semanas aplicado a tabela que vai ate julho/2026).
INICIO_RECORTE_2026 = pd.Timestamp("2026-01-01")
FIM_RECORTE_2026 = pd.Timestamp("2026-04-19")

# Criterio de estabilidade (secao C): desvio-padrao do MAE em h=12, entre as 5
# sementes, menor que 5% da media; e sinal da comparacao com o cenario
# adotado em 2026 igual nas 5 sementes.
LIMIAR_CV_ESTABILIDADE = 0.05


def eh_ausente(valor) -> bool:
    """True se o valor for None ou NaN (JSON grava campo ausente como NaN)."""
    return valor is None or (isinstance(valor, float) and np.isnan(valor))


def carregar_vencedoras() -> dict:
    """Le vencedoras.json da busca de hiperparametros.

    Raises:
        RuntimeError: Se o arquivo nao existir ou faltar HB_best/LGB_best.
    """
    caminho = PASTA_BUSCA / "saidas" / "vencedoras.json"
    if not caminho.exists():
        raise RuntimeError(
            f"A busca de hiperparametros nao gerou vencedoras: {caminho} nao existe."
        )

    with open(caminho, encoding="utf-8") as arquivo:
        vencedoras = json.load(arquivo)

    faltando = [chave for chave in ("HB_best", "LGB_best") if chave not in vencedoras]
    if faltando:
        raise RuntimeError(f"vencedoras.json nao tem: {faltando}")

    return vencedoras


def histgb_e_deterministico(config_hb: dict) -> bool:
    """A vencedora do HistGB e deterministica se max_features=1 (sem subamostra
    de colunas por split) e sem early stopping.

    HistGradientBoostingRegressor so usa random_state para: (1) a subamostra
    de colunas quando max_features<1, e (2) o split treino/validacao interno
    do early stopping. Com poucas centenas de linhas por horizonte,
    early_stopping='auto' fica False (auto so liga acima de 10 mil amostras),
    entao a unica fonte de aleatoriedade e o max_features.
    """
    max_features = config_hb.get("max_features", 1.0)
    if eh_ausente(max_features):
        max_features = 1.0
    return float(max_features) >= 1.0


def construir_hb_best(config_hb: dict, random_state: int, nome: str):
    """Ficha do HistGB vencedor, com a semente pedida no lugar do 42 fixo."""
    parametros = {
        "learning_rate": float(config_hb["learning_rate"]),
        "max_iter": int(config_hb["max_iter"]),
        "max_leaf_nodes": int(config_hb["max_leaf_nodes"]),
        "min_samples_leaf": int(config_hb["min_samples_leaf"]),
        "l2_regularization": float(config_hb.get("l2_regularization", 0.0)),
        "max_features": float(config_hb.get("max_features", 1.0)),
        "random_state": random_state,
        "loss": "quantile",
        "quantile": QUANTIL_DE_REFERENCIA,
    }
    max_depth = config_hb.get("max_depth")
    if not eh_ausente(max_depth):
        parametros["max_depth"] = int(max_depth)

    return harness.EspecificacaoModelo(
        nome=nome, classe=HistGradientBoostingRegressor, parametros=parametros
    )


def construir_lgb_best(config_lgb: dict, random_state: int, nome: str):
    """Ficha do LightGBM vencedor, com a semente pedida no lugar do 42 fixo."""
    parametros = {
        "learning_rate": float(config_lgb["learning_rate"]),
        "n_estimators": int(config_lgb["n_estimators"]),
        "num_leaves": int(config_lgb["num_leaves"]),
        "min_child_samples": int(config_lgb["min_child_samples"]),
        "reg_lambda": float(config_lgb["reg_lambda"]),
        "colsample_bytree": float(config_lgb["colsample_bytree"]),
        "subsample": float(config_lgb["subsample"]),
        "subsample_freq": 1,
        "extra_trees": bool(config_lgb["extra_trees"]),
        "random_state": random_state,
        "n_jobs": 1,
        "verbose": -1,
        "objective": "quantile",
        "alpha": QUANTIL_DE_REFERENCIA,
    }
    return harness.EspecificacaoModelo(
        nome=nome, classe=LGBMRegressor, parametros=parametros
    )


def montar_tabela_e_colunas_do_cenario_adotado():
    """Monta, uma unica vez, a mesma tabela e as mesmas 20 colunas que o
    cenario adotado e as vencedoras da busca usam.

    Chamar isto uma vez so (em vez de uma vez por semente) importa: a
    selecao de clima usa LGBM_REGRESSAO sem random_state (dívida tecnica
    conhecida, ver PENDENCIAS.md), entao repetir a chamada poderia sortear
    colunas de clima diferentes entre sementes — o que contaminaria a
    comparacao de estabilidade com uma segunda fonte de variacao, alem da
    semente do modelo.
    """
    tabela_bruta = harness.carregar_tabela_bruta()
    braco_base = harness.Braco(nome="base", descricao="features do cenario adotado")
    tabela, colunas, clima = harness.montar_features_do_braco(tabela_bruta, braco_base)
    return tabela, colunas, clima


def rodar_um_modelo(nome_job: str, especificacao_modelo, tabela, colunas) -> pd.DataFrame:
    """Roda o walk-forward de um modelo nos 12 horizontes da referencia."""
    linhas = []
    for horizonte in harness.CIDADE_REFERENCIA.horizontes:
        inicio = time.perf_counter()
        previsoes = harness.rodar_walk_forward(tabela, colunas, horizonte, especificacao_modelo)
        previsoes["job"] = nome_job
        linhas.append(previsoes)
        print(
            f"  [{nome_job}] h={horizonte:2d}  {len(previsoes):3d} sem  "
            f"{time.perf_counter() - inicio:6.1f}s",
            flush=True,
        )
    return pd.concat(linhas, ignore_index=True)


def _worker(pacote):
    """Ponto de entrada de cada processo do pool: roda 1 job e devolve o CSV
    em memoria (como DataFrame), com o nome do job de volta para juntar.
    """
    nome_job, especificacao_modelo, tabela, colunas = pacote
    return nome_job, rodar_um_modelo(nome_job, especificacao_modelo, tabela, colunas)


def conferir_trava(previsoes_referencia: pd.DataFrame) -> tuple[bool, dict]:
    """Confere a trava do cenario adotado: h=1 MAE 97,4 e h=12 MAE 280,0,
    dentro de INICIO_DA_AVALIACAO (2024-01-01, a mesma janela do painel
    publicado) ate 01/02/2026. Registra h=4 e h=8 tambem, sem tolerancia.
    """
    avaliacao = previsoes_referencia[
        (previsoes_referencia["data_alvo"] >= harness.INICIO_DA_AVALIACAO)
        & (previsoes_referencia["data_alvo"] <= FIM_DA_TRAVA)
    ]

    print("\n  TRAVA DO CENARIO ADOTADO (tabela nova, ate 01/02/2026)", flush=True)
    tudo_bate = True
    maes_por_horizonte = {}
    for horizonte in HORIZONTES_DA_TRAVA:
        celula = avaliacao[avaliacao["h"] == horizonte]
        mae = float(mean_absolute_error(celula["real"], celula["previsto"]))
        maes_por_horizonte[horizonte] = mae

        ancora = ANCORAS_DA_TRAVA.get(horizonte)
        if ancora is not None:
            bate = abs(mae - ancora) < TOLERANCIA_DA_TRAVA
            tudo_bate = tudo_bate and bate
            marca = "ok" if bate else "<<< DIVERGE"
            print(
                f"    h={horizonte:2d}  MAE {mae:7.2f} (trava {ancora:6.1f})  {marca}  "
                f"n={len(celula)}",
                flush=True,
            )
        else:
            print(f"    h={horizonte:2d}  MAE {mae:7.2f}  (sem trava — registrado)  n={len(celula)}", flush=True)

    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}", flush=True)

    with open(PASTA_DE_SAIDAS / "trava_cenario_adotado.json", "w", encoding="utf-8") as arquivo:
        json.dump(
            {
                "maes_ate_fev_2026": maes_por_horizonte,
                "trava_h1_h12": ANCORAS_DA_TRAVA,
                "tolerancia": TOLERANCIA_DA_TRAVA,
                "valido": tudo_bate,
            },
            arquivo,
            indent=2,
        )

    return tudo_bate, maes_por_horizonte


def montar_estabilidade(previsoes: pd.DataFrame, mae_referencia_h12_2026: float) -> pd.DataFrame:
    """Monta a tabela de estabilidade por familia (HB_best, LGB_best): MAE de
    cada semente em h=12 no recorte 2026, media, desvio, CV e sinal contra o
    cenario adotado.
    """
    recorte_2026 = previsoes[
        (previsoes["data_alvo"] >= INICIO_RECORTE_2026)
        & (previsoes["data_alvo"] <= FIM_RECORTE_2026)
        & (previsoes["h"] == 12)
    ]

    linhas = []
    for familia in sorted(recorte_2026["familia"].unique()):
        do_familia = recorte_2026[recorte_2026["familia"] == familia]
        maes_por_semente = {}
        for semente in SEMENTES:
            da_semente = do_familia[do_familia["semente"] == semente]
            if da_semente.empty:
                continue
            maes_por_semente[semente] = float(
                mean_absolute_error(da_semente["real"], da_semente["previsto"])
            )

        valores = list(maes_por_semente.values())
        media = float(np.mean(valores))
        desvio = float(np.std(valores, ddof=1)) if len(valores) > 1 else 0.0
        cv = desvio / media if media else float("nan")

        sinais = [np.sign(mae - mae_referencia_h12_2026) for mae in valores]
        sinal_consistente = len(set(sinais)) == 1

        for semente, mae in maes_por_semente.items():
            linhas.append(
                {
                    "familia": familia,
                    "semente": semente,
                    "mae_h12_2026": mae,
                    "mae_referencia_h12_2026": mae_referencia_h12_2026,
                    "delta_vs_referencia": mae - mae_referencia_h12_2026,
                    "media_das_sementes": media,
                    "desvio_padrao_das_sementes": desvio,
                    "cv": cv,
                    "estavel_cv": bool(cv < LIMIAR_CV_ESTABILIDADE) if not np.isnan(cv) else False,
                    "sinal_consistente_entre_sementes": sinal_consistente,
                    "n_sementes": len(valores),
                }
            )

    return pd.DataFrame(linhas)


def main() -> None:
    print("=" * 78)
    print("RODADA C — segunda bateria noturna: estabilidade das vencedoras")
    print("=" * 78, flush=True)

    vencedoras = carregar_vencedoras()
    config_hb = vencedoras["HB_best"]
    config_lgb = vencedoras["LGB_best"]

    hb_deterministico = histgb_e_deterministico(config_hb)
    print(
        f"\nHB_best = {config_hb['config_id']}  max_features="
        f"{config_hb.get('max_features')}  deterministico={hb_deterministico}",
        flush=True,
    )
    print(f"LGB_best = {config_lgb['config_id']}", flush=True)

    tabela, colunas, clima = montar_tabela_e_colunas_do_cenario_adotado()
    print(f"\n{len(colunas)} colunas do modelo, clima escolhido: {clima}", flush=True)

    sementes_hb = (SEMENTES[0],) if hb_deterministico else SEMENTES
    if hb_deterministico:
        print(
            "\n⚠️ HistGB vencedor e deterministico (max_features=1, sem early "
            "stopping): rodando 1 semente so, registrando e seguindo com as 5 "
            "sementes do LightGBM.",
            flush=True,
        )

    jobs = [("referencia", harness.CIDADE_REFERENCIA.modelo, tabela, colunas)]
    for semente in sementes_hb:
        modelo = construir_hb_best(config_hb, semente, f"HB_best_seed{semente}")
        jobs.append((f"HB_best_seed{semente}", modelo, tabela, colunas))
    for semente in SEMENTES:
        modelo = construir_lgb_best(config_lgb, semente, f"LGB_best_seed{semente}")
        jobs.append((f"LGB_best_seed{semente}", modelo, tabela, colunas))

    print(f"\n{len(jobs)} jobs, ate {MAXIMO_DE_PROCESSOS} processos simultaneos.", flush=True)

    resultados_por_job = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAXIMO_DE_PROCESSOS) as executor:
        futuros = {executor.submit(_worker, job): job[0] for job in jobs}
        for futuro in concurrent.futures.as_completed(futuros):
            nome_job = futuros[futuro]
            try:
                nome_devolvido, previsoes = futuro.result()
            except Exception as erro:
                print(f"  [{nome_job}] FALHOU: {erro!r}", flush=True)
                raise
            resultados_por_job[nome_devolvido] = previsoes
            print(f"[{nome_job}] concluido.", flush=True)

    todas = []
    for nome_job, previsoes in resultados_por_job.items():
        previsoes = previsoes.copy()
        if nome_job == "referencia":
            previsoes["familia"] = "referencia"
            previsoes["semente"] = np.nan
        else:
            familia, _, semente_str = nome_job.rpartition("_seed")
            previsoes["familia"] = familia
            previsoes["semente"] = int(semente_str)
        todas.append(previsoes)

    previsoes_completas = pd.concat(todas, ignore_index=True)
    previsoes_completas.to_csv(PASTA_DE_SAIDAS / "previsoes_sementes.csv", index=False)

    previsoes_referencia = previsoes_completas[previsoes_completas["familia"] == "referencia"]
    trava_valida, maes_trava = conferir_trava(previsoes_referencia)

    mae_referencia_h12_2026 = float(
        mean_absolute_error(
            previsoes_referencia[
                (previsoes_referencia["h"] == 12)
                & (previsoes_referencia["data_alvo"] >= INICIO_RECORTE_2026)
                & (previsoes_referencia["data_alvo"] <= FIM_RECORTE_2026)
            ]["real"],
            previsoes_referencia[
                (previsoes_referencia["h"] == 12)
                & (previsoes_referencia["data_alvo"] >= INICIO_RECORTE_2026)
                & (previsoes_referencia["data_alvo"] <= FIM_RECORTE_2026)
            ]["previsto"],
        )
    )
    print(f"\n  MAE h=12 do cenario adotado no recorte 2026: {mae_referencia_h12_2026:.2f}", flush=True)

    previsoes_vencedoras = previsoes_completas[previsoes_completas["familia"] != "referencia"]
    estabilidade = montar_estabilidade(previsoes_vencedoras, mae_referencia_h12_2026)
    estabilidade.to_csv(PASTA_DE_SAIDAS / "estabilidade.csv", index=False)

    print("\n  ESTABILIDADE (h=12, recorte 2026):")
    for familia in sorted(estabilidade["familia"].unique()):
        linha_do_familia = estabilidade[estabilidade["familia"] == familia].iloc[0]
        print(
            f"    {familia:>12}  media={linha_do_familia['media_das_sementes']:7.2f}  "
            f"cv={linha_do_familia['cv']:.4f}  "
            f"estavel_cv={linha_do_familia['estavel_cv']}  "
            f"sinal_consistente={linha_do_familia['sinal_consistente_entre_sementes']}",
            flush=True,
        )

    if not trava_valida:
        print(
            "\n⚠️ TRAVA FALHOU — investigando, nao forcando. Previsoes e "
            "trava_cenario_adotado.json ja gravados para diagnostico.",
            flush=True,
        )

    print("\nCONCLUIDO.", flush=True)


if __name__ == "__main__":
    main()
