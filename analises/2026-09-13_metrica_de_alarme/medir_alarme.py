"""

Uma metrica de alarme de verdade, a partir das previsoes que ja existem.

POR QUE ESTE SCRIPT EXISTE

  O projeto mede "captura do pico" como media(previsto) / media(real) nas
  semanas com mais de 100 casos. Isso e uma RAZAO DE NIVEL: diz se o patamar
  medio previsto se aproxima do real. Nao diz quantos surtos seriam
  sinalizados, nem com quanta antecedencia, nem quantos alarmes falsos.

  Para a vigilancia, o que importa e: o alarme toca? quando? quantas vezes a
  toa? Este script responde isso re-agregando as previsoes ja salvas do grid
  corrigido de 13/09/2026. Nao roda modelo nenhum.

DEFINICOES, FIXADAS ANTES DE OLHAR O RESULTADO

  LIMITE = 100 casos na semana. E o mesmo corte que o projeto ja usa em
  "captura do pico" e em "vies do pico", entao os numeros sao comparaveis.

  SEMANA DE SURTO   real  > LIMITE
  ALARME            previsto > LIMITE

  EPISODIO          sequencia de semanas de surto consecutivas. Dois episodios
                    separados por menos de FOLGA_ENTRE_EPISODIOS semanas
                    calmas contam como UM SO - senao uma unica epidemia com
                    dois picos vira dois eventos e infla a contagem.

  SENSIBILIDADE     das semanas de surto, quantas dispararam alarme.
  PRECISAO          dos alarmes, quantos eram surto de verdade.
  INICIO PEGO       o alarme disparou ja na PRIMEIRA semana do episodio?
                    E a pergunta operacional: a vigilancia foi avisada a tempo
                    de agir, ou so depois que a epidemia ja estava instalada.
  ATRASO            quantas semanas do episodio passaram ate o primeiro alarme.
  FALSOS/TEMPORADA  alarmes fora de episodio, por ano de avaliacao.

  ANTECEDENCIA: como o horizonte e fixo, um alarme para a semana W e emitido
  h semanas antes. Entao "inicio pego em h=8" significa 8 semanas de aviso.
  Nao ha o que estimar aqui - a antecedencia E o horizonte.

Uso:  python medir_alarme.py

"""

from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
GRID = PASTA.parent / "2026-09-13_correcao_vazamento_treino" / "saidas"

LIMITE = 100
FOLGA_ENTRE_EPISODIOS = 4
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")
REFERENCIA = ("hist_gradient_boosting", "quantil_0.85", "M1_com_vetor")


def carregar_previsoes() -> pd.DataFrame:
    """Junta as tres bateladas do grid corrigido e marca o periodo."""
    nomes = ("corrigido_previsoes_parciais.csv", "corrigido_previsoes_padrao.csv",
             "corrigido_previsoes_restante.csv")
    dados = pd.concat([pd.read_csv(GRID / n) for n in nomes], ignore_index=True)
    dados["data_alvo"] = pd.to_datetime(dados["data_alvo"])
    return dados[dados["data_alvo"] > FIM_DA_CALIBRACAO].copy()


def marcar_episodios(e_surto: pd.Series) -> pd.Series:
    """

    Numera os episodios de surto, juntando os que estao perto demais.

    Args:
        e_surto: Serie booleana por semana, em ordem cronologica.

    Returns:
        Serie de inteiros: 0 fora de episodio, 1..N dentro de cada episodio.

    """
    valores = e_surto.to_numpy()
    episodio = np.zeros(len(valores), dtype=int)
    numero = 0
    semanas_calmas = FOLGA_ENTRE_EPISODIOS + 1
    for i, dentro in enumerate(valores):
        if dentro:
            if semanas_calmas > FOLGA_ENTRE_EPISODIOS:
                numero += 1
            episodio[i] = numero
            semanas_calmas = 0
        else:
            semanas_calmas += 1
            # uma semana calma DENTRO da folga continua pertencendo ao episodio
            if numero > 0 and semanas_calmas <= FOLGA_ENTRE_EPISODIOS:
                if valores[i:i + FOLGA_ENTRE_EPISODIOS + 1].any():
                    episodio[i] = numero
    return pd.Series(episodio, index=e_surto.index)


def medir(grupo: pd.DataFrame) -> pd.Series:
    """Calcula as metricas de alarme de uma celula (uma configuracao, um h)."""
    g = grupo.sort_values("data_alvo").reset_index(drop=True)
    g["e_surto"] = g["real"] > LIMITE
    g["alarme"] = g["pred"] > LIMITE
    g["episodio"] = marcar_episodios(g["e_surto"])

    semanas_surto = g["e_surto"].sum()
    alarmes = g["alarme"].sum()
    verdadeiros = (g["e_surto"] & g["alarme"]).sum()

    inicios_pegos, atrasos = 0, []
    episodios = [n for n in g["episodio"].unique() if n > 0]
    for numero in episodios:
        bloco = g[g["episodio"] == numero]
        semanas_de_surto_do_bloco = bloco[bloco["e_surto"]]
        primeiro_alarme = bloco[bloco["alarme"]]
        if primeiro_alarme.empty:
            atrasos.append(np.nan)
            continue
        indice_inicio = semanas_de_surto_do_bloco.index[0]
        indice_alarme = primeiro_alarme.index[0]
        atrasos.append(max(indice_alarme - indice_inicio, 0))
        if indice_alarme <= indice_inicio:
            inicios_pegos += 1

    anos = g["data_alvo"].dt.year.nunique()
    falsos = int(((~g["e_surto"]) & g["alarme"]).sum())
    reais_pico = g.loc[g["e_surto"], "real"]
    pred_pico = g.loc[g["e_surto"], "pred"]

    return pd.Series({
        "n_semanas": len(g),
        "semanas_surto": int(semanas_surto),
        "episodios": len(episodios),
        "sensibilidade": verdadeiros / semanas_surto if semanas_surto else np.nan,
        "precisao": verdadeiros / alarmes if alarmes else np.nan,
        "inicios_pegos": f"{inicios_pegos}/{len(episodios)}",
        "atraso_mediano": np.nanmedian(atrasos) if atrasos else np.nan,
        "falsos_por_ano": falsos / anos if anos else np.nan,
        "captura_pico_antiga": pred_pico.mean() / reais_pico.mean() if semanas_surto else np.nan,
    })


previsoes = carregar_previsoes()
pd.set_option("display.width", 200)

algoritmo, perda, conjunto = REFERENCIA
referencia = previsoes[(previsoes.algoritmo == algoritmo) & (previsoes.perda == perda)
                       & (previsoes.conjunto == conjunto)]

print("=" * 92)
print("CONFIGURACAO DE REFERENCIA — HistGradientBoosting · quantil 0,85 · com vetor")
print(f"avaliacao 2024+ · surto = mais de {LIMITE} casos na semana")
print("=" * 92)
tabela = referencia.groupby("h").apply(medir, include_groups=False)
print(tabela.round(3).to_string())

print("\n" + "=" * 92)
print("A MESMA COISA, SEM O VETOR (para ver se o vetor muda o ALARME)")
print("=" * 92)
sem_vetor = previsoes[(previsoes.algoritmo == algoritmo) & (previsoes.perda == perda)
                      & (previsoes.conjunto == "M0_sem_vetor")]
print(sem_vetor.groupby("h").apply(medir, include_groups=False).round(3).to_string())

print("\n" + "=" * 92)
print("TODAS AS 30 CONFIGURACOES EM h=4 — quem seria o melhor ALARME?")
print("=" * 92)
h4 = previsoes[previsoes.h == 4].groupby(["algoritmo", "perda", "conjunto"]).apply(
    medir, include_groups=False).reset_index()
h4 = h4.sort_values("sensibilidade", ascending=False)
print(h4[["algoritmo", "perda", "conjunto", "sensibilidade", "precisao",
          "inicios_pegos", "falsos_por_ano", "captura_pico_antiga"]].head(10).round(3).to_string(index=False))

tabela.to_csv(PASTA / "saidas" / "alarme_configuracao_de_referencia.csv")
h4.to_csv(PASTA / "saidas" / "alarme_30_configuracoes_h4.csv", index=False)
print(f"\nsalvo em {PASTA / 'saidas'}")
