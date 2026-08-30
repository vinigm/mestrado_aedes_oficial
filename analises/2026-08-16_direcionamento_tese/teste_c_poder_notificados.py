"""
TESTE C — Poder estatistico com casos notificados (frente deteccao de surto)

Pergunta: migrar o alvo de confirmados (SINAN, 2018+) para notificados
(InfoDengue, ~2010+) aumenta quanto o numero de semanas de surto -- e isso
basta para os testes pareados (McNemar) ganharem poder?

Regras seguidas:
- leitura apenas; nenhum arquivo do projeto foi alterado.
- limiar de surto = percentil EXPANSIVEL (so passado), replicando a logica
  do projeto: para a semana i, o limiar usa apenas os valores de casos das
  semanas 0..i-1 (minimo de historico definido abaixo); a semana e' marcada
  como "surto" se casos[i] > limiar(P90 ou P95) calculado com esse passado.
- nao ha treinamento de modelo algum aqui: este script so caracteriza as
  series (contagem de semanas de surto) e faz a PROJECAO binomial de poder
  do McNemar descrita no protocolo (item 3), a partir das taxas de
  discordancia observadas ontem com confirmados.

Saidas (nesta mesma pasta):
- semanas_surto_por_serie.csv
- poder_projetado_mcnemar.csv
- bandas_infodengue_colunas.csv
"""

import numpy as np
import pandas as pd
from scipy import stats

BASE = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto"
TABELA_FINAL = f"{BASE}/modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv"
INFODENGUE_DENGUE = f"{BASE}/modelagem_aedes/dados/entradas/infodengue_poa/infodengue_poa_dengue.csv"
OUT_DIR = f"{BASE}/analises/2026-08-16_direcionamento_tese"

MIN_HISTORICO = 52  # minimo de semanas passadas para comecar a calcular percentil expansivel


def limiar_expansivel(serie: pd.Series, percentil: float, min_historico: int) -> pd.Series:
    """
    Calcula, para cada posicao i da serie (ja ordenada no tempo, sem gaps
    de indice), o percentil `percentil` (0-100) computado APENAS com os
    valores anteriores (indices 0..i-1). Antes de acumular `min_historico`
    observacoes validas, o limiar fica NaN (semana nao classificavel).
    """
    valores = serie.to_numpy(dtype=float)
    n = len(valores)
    limiares = np.full(n, np.nan)
    historico_valido = []
    for i in range(n):
        if len(historico_valido) >= min_historico:
            limiares[i] = np.percentile(historico_valido, percentil)
        if not np.isnan(valores[i]):
            historico_valido.append(valores[i])
    return pd.Series(limiares, index=serie.index)


def contar_semanas_surto(df: pd.DataFrame, coluna_casos: str, percentil: float) -> dict:
    """
    Retorna contagem de semanas de surto (casos > limiar expansivel) e
    quantas semanas foram de fato classificaveis (limiar nao-NaN e casos
    nao-NaN).
    """
    limiar = limiar_expansivel(df[coluna_casos], percentil, MIN_HISTORICO)
    classificavel = limiar.notna() & df[coluna_casos].notna()
    surto = classificavel & (df[coluna_casos] > limiar)
    return {
        "n_semanas_classificaveis": int(classificavel.sum()),
        "n_semanas_surto": int(surto.sum()),
        "taxa_surto": float(surto.sum() / classificavel.sum()) if classificavel.sum() > 0 else np.nan,
    }


def main():
    # ---------- 1. InfoDengue: periodo coberto ----------
    infod = pd.read_csv(INFODENGUE_DENGUE)
    infod["data_iniSE"] = pd.to_datetime(infod["data_iniSE"])
    infod = infod.sort_values("data_iniSE").reset_index(drop=True)

    periodo_infodengue = {
        "primeira_semana": str(infod["data_iniSE"].min().date()),
        "ultima_semana_com_dado": str(infod["data_iniSE"].max().date()),
        "n_semanas": len(infod),
        "coluna_usada_notificados": "casos",  # 'casos' = notificados na semana (nao estimados)
        "n_semanas_casos_nao_nulo": int(infod["casos"].notna().sum()),
    }

    # ---------- 2. tabela_final: confirmados (2018+) ----------
    tf = pd.read_csv(TABELA_FINAL)
    tf["data_inicio_semana_epidemi"] = pd.to_datetime(tf["data_inicio_semana_epidemi"])
    tf = tf.sort_values("data_inicio_semana_epidemi").reset_index(drop=True)

    # ---------- Contagem de semanas de surto (P90 e P95) ----------
    resultados = []
    for percentil in (90, 95):
        r_notif = contar_semanas_surto(infod, "casos", percentil)
        r_notif.update({"serie": "notificados_infodengue", "percentil": percentil,
                         "periodo": f"{infod['data_iniSE'].min().date()} a {infod['data_iniSE'].max().date()}"})
        resultados.append(r_notif)

        r_conf = contar_semanas_surto(tf, "casos_confirmados", percentil)
        r_conf.update({"serie": "confirmados_sinan_tabela_final", "percentil": percentil,
                        "periodo": f"{tf['data_inicio_semana_epidemi'].min().date()} a {tf['data_inicio_semana_epidemi'].max().date()}"})
        resultados.append(r_conf)

    df_resultados = pd.DataFrame(resultados)[
        ["serie", "percentil", "periodo", "n_semanas_classificaveis", "n_semanas_surto", "taxa_surto"]
    ]
    df_resultados.to_csv(f"{OUT_DIR}/semanas_surto_por_serie.csv", index=False)

    # ---------- 3. Projecao de poder do McNemar ----------
    # Ontem (confirmados, melhor caso observado): b=4, c=14, n_discordantes=18
    # p bruto = 0.031 (McNemar exato/binomial), Holm com 6 comparacoes -> 0.185
    b_ontem, c_ontem = 4, 14
    n_disc_ontem = b_ontem + c_ontem

    # taxa de discordancia por semana de surto (base = semanas de surto confirmados, P90)
    linha_conf_p90 = df_resultados[
        (df_resultados["serie"] == "confirmados_sinan_tabela_final") & (df_resultados["percentil"] == 90)
    ].iloc[0]
    linha_notif_p90 = df_resultados[
        (df_resultados["serie"] == "notificados_infodengue") & (df_resultados["percentil"] == 90)
    ].iloc[0]

    n_surto_conf = linha_conf_p90["n_semanas_surto"]
    n_surto_notif = linha_notif_p90["n_semanas_surto"]

    # taxa de discordancia observada ontem = discordantes / semanas de surto (aproximacao
    # conservadora: o denominador correto seria "semanas classificadas como surto por
    # pelo menos um dos dois metodos comparados no McNemar", que nao temos aqui; usamos
    # n_semanas_surto (confirmados, P90) como proxy do denominador disponivel ontem).
    taxa_discordancia = n_disc_ontem / n_surto_conf if n_surto_conf > 0 else np.nan
    proporcao_b = b_ontem / n_disc_ontem  # fracao dos discordantes que sao "b" (mantida constante)

    # discordantes projetados para a serie de notificados, mantendo a MESMA taxa
    # de discordancia por semana de surto, escalada pelo numero de semanas de surto
    # da serie de notificados
    n_disc_proj = taxa_discordancia * n_surto_notif
    b_proj = round(proporcao_b * n_disc_proj)
    c_proj = round(n_disc_proj) - b_proj

    n_total_proj = b_proj + c_proj
    # McNemar exato (binomial): p = 2 * P(X <= min(b,c)) sob Binomial(n, 0.5), truncado em 1
    k = min(b_proj, c_proj)
    p_bruto_proj = min(1.0, 2 * stats.binom.cdf(k, n_total_proj, 0.5)) if n_total_proj > 0 else np.nan

    # Holm com 6 comparacoes: menor p bruto entre as 6 é multiplicado por 6 (holm passo 1);
    # aqui simulamos apenas a comparacao de interesse assumindo que ela seria a menor
    # (cenario mais favoravel), reportando o teto Holm-passo-1 = p_bruto * 6.
    p_holm_teto_proj = min(1.0, p_bruto_proj * 6)

    # Para comparacao, refazemos o calculo do caso de ontem (confirmados) com a mesma
    # formula, para conferir que reproduz p=0.031 aproximadamente.
    k_ontem = min(b_ontem, c_ontem)
    p_bruto_ontem_recalc = min(1.0, 2 * stats.binom.cdf(k_ontem, n_disc_ontem, 0.5))
    p_holm_teto_ontem_recalc = min(1.0, p_bruto_ontem_recalc * 6)

    df_poder = pd.DataFrame([
        {
            "cenario": "ontem_confirmados_observado",
            "n_semanas_surto_base": n_surto_conf,
            "b": b_ontem, "c": c_ontem, "n_discordantes": n_disc_ontem,
            "p_bruto_recalculado": round(p_bruto_ontem_recalc, 4),
            "p_holm_teto_6comp": round(p_holm_teto_ontem_recalc, 4),
        },
        {
            "cenario": "projecao_notificados_mesma_taxa_discordancia",
            "n_semanas_surto_base": n_surto_notif,
            "b": b_proj, "c": c_proj, "n_discordantes": n_total_proj,
            "p_bruto_recalculado": round(p_bruto_proj, 4),
            "p_holm_teto_6comp": round(p_holm_teto_proj, 4),
        },
    ])
    df_poder["taxa_discordancia_por_semana_surto"] = round(taxa_discordancia, 4)
    df_poder.to_csv(f"{OUT_DIR}/poder_projetado_mcnemar.csv", index=False)

    # ---------- 4. Bonus: colunas de banda/percentil prontas no InfoDengue ----------
    colunas_banda_candidatas = [c for c in infod.columns if c.lower() in
                                 ("nivel", "nivel_inc", "p_rt1", "rt", "receptivo", "transmissao")]
    df_bandas = pd.DataFrame({
        "coluna": colunas_banda_candidatas,
        "n_nao_nulo": [int(infod[c].notna().sum()) for c in colunas_banda_candidatas],
        "valores_unicos_amostra": [sorted(infod[c].dropna().unique().tolist())[:6] for c in colunas_banda_candidatas],
    })
    df_bandas.to_csv(f"{OUT_DIR}/bandas_infodengue_colunas.csv", index=False)

    # ---------- Print para o console (log da rodada) ----------
    print("=== PERIODO INFODENGUE ===")
    print(periodo_infodengue)
    print("\n=== SEMANAS DE SURTO POR SERIE ===")
    print(df_resultados.to_string(index=False))
    print("\n=== PODER PROJETADO MCNEMAR ===")
    print(df_poder.to_string(index=False))
    print("\n=== COLUNAS DE BANDA/PERCENTIL NO INFODENGUE ===")
    print(df_bandas.to_string(index=False))


if __name__ == "__main__":
    main()
