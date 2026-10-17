"""Verificacoes 4 e 5 do piso de ruido, com codigo proprio.

Modo `propriedades`: constroi a perturbacao da semente 1 (e 2 a 4) e confere o que a pre-declaracao 8b exige
(diferenca <= 1 ulp, so colunas continuas); confere a matriz `csv` contra a do pacote (verificacao 5).
Modo `amostra`: retreina 2 origens da folha 20, h=4, com a MINHA matriz da semente 1 e compara com as salvas.
Modo `completo`: refaz, com a matriz propria, as celulas s1 e csv (2 folhas x 4 h) e compara com as salvas;
    e, como observacao extra, roda s1 com os zeros exatos preservados.
"""

import json
import sys
import time

import numpy as np
import pandas as pd

from comum_cert import (
    COLUNA_ALVO_DATA,
    COLUNA_ORIGEM,
    COLUNA_Y,
    FIM_DA_JANELA,
    INICIO_DA_JANELA,
    PASTA_DA_CERTIFICACAO,
    PASTA_DA_CIENCIA,
    PASTA_DO_GABARITO,
    carregar_tabela_cortada,
    gravar_csv_atomico,
    ler_referencia,
    mae,
    montar_matriz_completa,
    nomes_das_variaveis,
    prever_uma_origem,
    walk_forward_proprio,
)

HORIZONTES = (1, 4, 8, 12)
MINIMO_POR_FOLHA = {5: 5, 20: 20}
QUANTIL = 0.85


def colunas_continuas_da_matriz(matriz: pd.DataFrame) -> list[str]:
    """Variaveis com ao menos um valor nao inteiro."""
    continuas: list[str] = []
    for nome in nomes_das_variaveis(matriz):
        valores = matriz[nome].to_numpy(dtype=float)
        if bool(np.any(valores != np.round(valores))):
            continuas.append(nome)
    return continuas


def perturbar_proprio(matriz: pd.DataFrame, semente: int, manter_zeros: bool) -> pd.DataFrame:
    """Soma ou subtrai 1 ulp (nextafter) em cada celula das colunas continuas, direcao sorteada.

    Um unico gerador `default_rng(semente)` percorre as colunas continuas na ordem da matriz; por coluna
    sorteia `random(n) < 0.5` -> +inf, senao -inf. Datas, y_h e colunas inteiras ficam intactas.
    """
    gerador = np.random.default_rng(semente)
    copia = matriz.copy()
    for nome in colunas_continuas_da_matriz(matriz):
        originais = matriz[nome].to_numpy(dtype=float)
        para_cima = gerador.random(len(originais)) < 0.5
        direcao = np.where(para_cima, np.inf, -np.inf)
        perturbados = np.nextafter(originais, direcao)
        if manter_zeros:
            perturbados = np.where(originais == 0.0, originais, perturbados)
        copia[nome] = perturbados
    return copia


def matriz_do_gabarito_csv(matriz_do_pacote: pd.DataFrame, horizonte: int) -> tuple[pd.DataFrame, dict[str, object]]:
    """Matriz do pacote com as variaveis trocadas pelas do CSV; devolve tambem o diagnostico do alinhamento."""
    gabarito = pd.read_csv(
        PASTA_DO_GABARITO / f"matriz_h{horizonte:02d}.csv", parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA]
    )
    diag: dict[str, object] = {"h": horizonte}
    diag["linhas_pacote"] = int(len(matriz_do_pacote))
    diag["linhas_csv"] = int(len(gabarito))
    diag["mesmo_conjunto_de_colunas"] = set(matriz_do_pacote.columns) == set(gabarito.columns)
    diag["mesma_ordem_de_colunas"] = list(matriz_do_pacote.columns) == list(gabarito.columns)
    if len(matriz_do_pacote) == len(gabarito):
        diag["datas_origem_iguais"] = bool((matriz_do_pacote[COLUNA_ORIGEM].to_numpy() == gabarito[COLUNA_ORIGEM].to_numpy()).all())
        diag["datas_alvo_iguais"] = bool((matriz_do_pacote[COLUNA_ALVO_DATA].to_numpy() == gabarito[COLUNA_ALVO_DATA].to_numpy()).all())
        diag["y_igual"] = bool(np.array_equal(matriz_do_pacote[COLUNA_Y].to_numpy(dtype=float), gabarito[COLUNA_Y].to_numpy(dtype=float)))
        celulas_diferentes = 0
        dif_max_abs = 0.0
        dif_max_em_ulps = 0.0
        for nome in nomes_das_variaveis(matriz_do_pacote):
            a = matriz_do_pacote[nome].to_numpy(dtype=float)
            b = gabarito[nome].to_numpy(dtype=float)
            diferentes = a != b
            celulas_diferentes += int(diferentes.sum())
            if diferentes.any():
                dif_max_abs = max(dif_max_abs, float(np.abs(a - b)[diferentes].max()))
                ulps = np.abs(a - b)[diferentes] / np.spacing(np.abs(a[diferentes]))
                dif_max_em_ulps = max(dif_max_em_ulps, float(ulps.max()))
        diag["celulas_diferentes"] = celulas_diferentes
        diag["dif_max_abs"] = dif_max_abs
        diag["dif_max_em_ulps"] = dif_max_em_ulps
    alinhada = matriz_do_pacote.copy()
    for nome in nomes_das_variaveis(matriz_do_pacote):
        alinhada[nome] = gabarito[nome].to_numpy(dtype=float)
    return alinhada, diag


tabela = carregar_tabela_cortada()
modo = sys.argv[1]
saida: dict[str, object] = {}
piso_salvo = pd.read_csv(
    PASTA_DA_CIENCIA / "piso_de_ruido" / "previsoes.csv", parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA]
)

if modo == "propriedades":
    props: list[dict[str, object]] = []
    diag_csv: list[dict[str, object]] = []
    for horizonte in HORIZONTES:
        matriz = montar_matriz_completa(tabela, horizonte)
        continuas = colunas_continuas_da_matriz(matriz)
        inteiras = [n for n in nomes_das_variaveis(matriz) if n not in continuas]
        for semente in (1, 2, 3, 4):
            pert = perturbar_proprio(matriz, semente, manter_zeros=False)
            celulas_mudadas = 0
            maior_em_ulps = 0.0
            zeros_perturbados = 0
            for nome in continuas:
                a = matriz[nome].to_numpy(dtype=float)
                p = pert[nome].to_numpy(dtype=float)
                celulas_mudadas += int((a != p).sum())
                # quantos ulps de distancia (nextafter move exatamente 1 ulp; conferimos por contagem de passos)
                passo_para_cima = np.nextafter(a, np.inf)
                passo_para_baixo = np.nextafter(a, -np.inf)
                eh_1_ulp = (p == passo_para_cima) | (p == passo_para_baixo)
                assert bool(eh_1_ulp.all()), (nome, semente, horizonte)
                maior_em_ulps = max(maior_em_ulps, 1.0)
                zeros_perturbados += int(((a == 0.0) & (p != 0.0)).sum())
            integras = all(np.array_equal(matriz[n].to_numpy(), pert[n].to_numpy()) for n in inteiras)
            datas_e_y_intactos = all(
                np.array_equal(matriz[c].to_numpy(), pert[c].to_numpy()) for c in (COLUNA_ORIGEM, COLUNA_ALVO_DATA, COLUNA_Y)
            )
            total_celulas = len(matriz) * len(continuas)
            props.append(
                {
                    "h": horizonte,
                    "semente": semente,
                    "n_continuas": len(continuas),
                    "continuas": continuas if semente == 1 else None,
                    "inteiras": inteiras if semente == 1 else None,
                    "celulas_continuas": total_celulas,
                    "celulas_mudadas": celulas_mudadas,
                    "todas_as_celulas_mudaram_1_ulp": celulas_mudadas == total_celulas,
                    "zeros_exatos_viraram_denormal": zeros_perturbados,
                    "colunas_inteiras_intactas": bool(integras),
                    "datas_e_y_intactos": bool(datas_e_y_intactos),
                }
            )
        _, diag = matriz_do_gabarito_csv(matriz, horizonte)
        diag_csv.append(diag)
    saida["propriedades"] = props
    saida["csv_alinhamento"] = diag_csv
    (PASTA_DA_CERTIFICACAO / "verif_3_propriedades.json").write_text(json.dumps(saida, indent=2, default=str))
    resumo = {
        "todas_1_ulp_celula_a_celula": all(p["todas_as_celulas_mudaram_1_ulp"] for p in props),
        "inteiras_e_datas_intactas": all(p["colunas_inteiras_intactas"] and p["datas_e_y_intactos"] for p in props),
        "zeros_virando_denormal_por_matriz": {f"h{p['h']}_s{p['semente']}": p["zeros_exatos_viraram_denormal"] for p in props},
        "continuas_h1": props[0]["continuas"],
        "inteiras_h1": props[0]["inteiras"],
    }
    print(json.dumps(resumo, indent=2, default=str))
    print(json.dumps(diag_csv, indent=2, default=str))

elif modo == "amostra":
    horizonte = 4
    matriz = montar_matriz_completa(tabela, horizonte)
    pert = perturbar_proprio(matriz, 1, manter_zeros=False)
    posicao_inicio_janela = int(np.flatnonzero((matriz[COLUNA_ALVO_DATA] >= INICIO_DA_JANELA).to_numpy())[0])
    posicao_fim = int(np.flatnonzero((matriz[COLUNA_ALVO_DATA] <= FIM_DA_JANELA).to_numpy())[-1])
    posicoes = [posicao_inicio_janela, (posicao_inicio_janela + posicao_fim) // 2]
    linhas: list[dict[str, object]] = []
    for posicao in posicoes:
        meu = prever_uma_origem(pert, posicao, horizonte, 20, QUANTIL)
        sem_perturbar = prever_uma_origem(matriz, posicao, horizonte, 20, QUANTIL)
        data_origem = pert[COLUNA_ORIGEM].iloc[posicao]
        salvo = piso_salvo.loc[
            (piso_salvo["perturbacao"] == "s1") & (piso_salvo["folha"] == 20) & (piso_salvo["h"] == horizonte)
            & (piso_salvo[COLUNA_ORIGEM] == data_origem)
        ]
        assert len(salvo) == 1
        linhas.append(
            {
                "data_origem": str(data_origem.date()),
                "data_alvo": str(pert[COLUNA_ALVO_DATA].iloc[posicao].date()),
                "meu_s1": meu,
                "salvo_s1": float(salvo["previsto"].iloc[0]),
                "dif": abs(meu - float(salvo["previsto"].iloc[0])),
                "sem_perturbar": sem_perturbar,
                "efeito_da_perturbacao": abs(meu - sem_perturbar),
            }
        )
    tabela_amostra = pd.DataFrame(linhas)
    tabela_amostra.to_csv(PASTA_DA_CERTIFICACAO / "verif_3_amostra.csv", index=False)
    print(tabela_amostra.to_string())

else:
    referencia = ler_referencia()
    nome_braco = {5: "referencia", 20: "HistGB_folha20_M1"}
    pasta_parciais = PASTA_DA_CERTIFICACAO / "parciais_piso"
    linhas_cel: list[dict[str, object]] = []
    # ordem: s1 e csv (comparaveis com as salvas), depois s1 com zeros mantidos (extra)
    for variante in ("s1", "csv", "s1_zeros_mantidos"):
        for folha in (20, 5):
            for horizonte in HORIZONTES:
                caminho = pasta_parciais / f"meu_{variante}_f{folha}_h{horizonte:02d}.csv"
                inicio = time.perf_counter()
                if caminho.exists():
                    meu = pd.read_csv(caminho, parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA])
                else:
                    matriz = montar_matriz_completa(tabela, horizonte)
                    if variante == "s1":
                        usada = perturbar_proprio(matriz, 1, manter_zeros=False)
                    elif variante == "s1_zeros_mantidos":
                        usada = perturbar_proprio(matriz, 1, manter_zeros=True)
                    else:
                        usada, _ = matriz_do_gabarito_csv(matriz, horizonte)
                    meu = walk_forward_proprio(usada, horizonte, MINIMO_POR_FOLHA[folha], QUANTIL)
                    gravar_csv_atomico(meu, caminho)
                na_janela = meu.loc[(meu[COLUNA_ALVO_DATA] >= INICIO_DA_JANELA) & (meu[COLUNA_ALVO_DATA] <= FIM_DA_JANELA)]
                ref_janela = referencia.loc[
                    (referencia["braco"] == nome_braco[folha]) & (referencia["h"] == horizonte)
                    & (referencia[COLUNA_ALVO_DATA] >= INICIO_DA_JANELA) & (referencia[COLUNA_ALVO_DATA] <= FIM_DA_JANELA)
                ]
                mae_meu = mae(na_janela["real"].to_numpy(), na_janela["previsto"].to_numpy())
                mae_ref = mae(ref_janela["real"].to_numpy(), ref_janela["previsto"].to_numpy())
                registro: dict[str, object] = {
                    "variante": variante, "folha": folha, "h": horizonte,
                    "n_janela": int(len(na_janela)), "mae_meu": mae_meu, "mae_ref": mae_ref,
                    "delta_meu": abs(mae_meu - mae_ref), "segundos": time.perf_counter() - inicio,
                }
                if variante in ("s1", "csv"):
                    rotulo = variante
                    salvo = piso_salvo.loc[
                        (piso_salvo["perturbacao"] == rotulo) & (piso_salvo["folha"] == folha) & (piso_salvo["h"] == horizonte)
                    ]
                    cruz = meu.merge(salvo, on=[COLUNA_ORIGEM, COLUNA_ALVO_DATA], how="outer", suffixes=("_meu", "_salvo"), indicator=True)
                    ambos = cruz.loc[cruz["_merge"] == "both"]
                    registro["n_meu"] = int(len(meu))
                    registro["n_salvo"] = int(len(salvo))
                    registro["so_um_lado"] = int((cruz["_merge"] != "both").sum())
                    registro["dif_max_previsto_vs_salvo"] = float((ambos["previsto_meu"] - ambos["previsto_salvo"]).abs().max())
                linhas_cel.append(registro)
                print(registro, flush=True)
                pd.DataFrame(linhas_cel).to_csv(PASTA_DA_CERTIFICACAO / "verif_3_completo.csv", index=False)
    print("FIM")
