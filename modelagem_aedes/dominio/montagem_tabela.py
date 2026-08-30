"""

Aqui o programa monta a tabela_final: junta o mosquito capturado nas
armadilhas, o clima, os casos de dengue confirmados e o El Nino / La Nina
numa unica tabela, semana a semana.

Desde 16/08/2026 o mosquito vem de uma fonte so: o parquet certificado da
Secretaria Municipal de Saude de Porto Alegre (2012 ate hoje; o proprio
parquet ja traz 2026 em diante a partir da raspagem, ver
preparo/unificar_arquivos_secretaria.py). As duas fontes antigas (Marilia,
2019-2023, e a raspagem consolidada por fora, 2025+) saíram do fluxo - os
dados delas continuam guardados, so que ninguem mais le.

A tabela e montada numa grade semanal CONTINUA (todo domingo entre a primeira
e a ultima semana com dado no parquet vira uma linha, mesmo quando nao teve
NENHUMA inspecao naquela semana). Quando uma semana nao tem inspecao nenhuma,
as colunas do vetor ficam vazias (NaN) - nao se inventa e nao se calcula
nenhum valor a partir das semanas vizinhas (isso e diferente do que o projeto
fazia antes, com a interpolacao entre Marilia e raspagem; ver
agregar_vetor_semanal).

As funcoes daqui so recebem tabelas prontas e devolvem tabelas prontas —
nao abrem nem salvam arquivo nenhum. Quem abre e salva os arquivos e o
programa montar.py.

"""
import numpy as np
import pandas as pd

# A montagem NAO aplica janela de maturidade nos casos: ela entrega exatamente
# o que o arquivo do SINAN divulgou (zero de verdade dentro do periodo
# divulgado, sem informacao depois da ultima semana com registro). Descontar as
# semanas recentes que ainda estao em apuracao e decisao de MODELAGEM, feita
# por cada experimento com aplicar_corte_maturidade (dominio/surto.py) e o
# campo semanas_corte_maturidade da config. Se a montagem descontasse aqui,
# todos os experimentos receberiam o corte ja aplicado e a comparacao
# com/sem corte (cidade_diebold) deixaria de existir - alem de cravar na
# camada de dados um numero (12) que ainda esta em discussao na pesquisa.

# Ordem final das colunas da tabela semanal do mosquito.
COLUNAS_VETOR_SEMANAL = [
    "fonte", "SE", "data_inicio_semana_epidemi", "ano", "semana",
    "numero_de_armadilhas", "aedes_aegypti", "aedes_albopictus", "culex_sp",
    "aedes_aegypti_por_armadilha", "denominador_aproximado",
]


def calcular_semana_epidemiologica(data_inicio_semana: pd.Series) -> pd.DataFrame:
    """

    Calcula o ano e a semana epidemiologica de cada domingo que abre uma semana.

    A semana epidemiologica brasileira comeca no domingo e termina no sabado,
    e a semana 1 e a primeira que tem pelo menos 4 dias no ano novo (o mesmo
    que dizer que a semana pertence ao ano da sua quarta-feira). E a MESMA
    regra que preparo/unificar_arquivos_secretaria.py usa pra calcular a
    semana de cada inspecao (calcular_semana_epidemiologica); esta copia
    existe porque a montagem tambem precisa saber o ano e a semana das poucas
    semanas que nao tem nenhuma inspecao registrada (essas nao aparecem no
    parquet, entao nao tem como vir de la).

    Args:
        data_inicio_semana: O domingo que abre cada semana.

    Returns:
        Uma tabela com o ano, o numero da semana e o codigo SE (ano*100+semana).

    """
    quarta_feira = data_inicio_semana + pd.Timedelta(days=3)
    ano = quarta_feira.dt.year
    primeiro_de_janeiro = pd.to_datetime(ano.astype(str) + "-01-01")
    dias_ate_a_primeira_quarta = (2 - primeiro_de_janeiro.dt.weekday) % 7
    primeira_quarta_do_ano = primeiro_de_janeiro + pd.to_timedelta(
        dias_ate_a_primeira_quarta, unit="D"
    )
    semana = ((quarta_feira - primeira_quarta_do_ano).dt.days // 7) + 1
    codigo_se = ano * 100 + semana
    return pd.DataFrame({"ano": ano, "semana": semana, "SE": codigo_se})



# Diz se, numa semana, NENHUMA inspecao tem o campo inspecao_realizada preenchido (o caso de 2012 a 2018).
def semana_tem_denominador_aproximado(inspecao_realizada: pd.Series) -> bool:
    return bool(inspecao_realizada.isna().all())



def agregar_vetor_semanal(df_secretaria: pd.DataFrame) -> pd.DataFrame:
    """

    Agrupa as inspecoes de armadilha por semana e monta a grade semanal
    continua do vetor, da primeira a ultima semana que o parquet tiver.

    Cada semana soma as fêmeas e os machos de cada especie (de TODAS as
    inspecoes daquela semana) e conta quantas armadilhas foram REALMENTE
    inspecionadas (inspecao_realizada verdadeiro). A densidade
    (aedes_aegypti_por_armadilha) e as fêmeas de aegypti divididas por essa
    contagem.

    De 2012 a 2018 a Secretaria ainda nao registrava se a vistoria foi feita
    de verdade (inspecao_realizada fica vazio no parquet inteiro nesses
    anos - pendencia com a Secretaria). Nesses anos o denominador usado e o
    total de armadilhas com QUALQUER registro na semana (uma aproximacao,
    porque nem toda visita registrada e necessariamente uma inspecao
    completa); a coluna 'denominador_aproximado' marca essas semanas como
    True, pra quem for analisar a densidade saber que o denominador dali e
    menos confiavel.

    As poucas semanas sem NENHUMA inspecao registrada (a virada de 2017 pra
    2018 e as tres semanas da enchente de 2024) ficam com todas as colunas do
    vetor vazias (NaN) - nao se inventa nem se calcula nada a partir das
    semanas vizinhas pra essas semanas (o projeto antigo interpolava entre
    Marilia e a raspagem; isso saiu porque nao faz mais sentido pra uma fonte
    so, e porque nao se quer mais inventar dado de mosquito nenhum).

    Args:
        df_secretaria: A tabela do parquet certificado, uma linha por
            inspecao de armadilha (ver acesso.fontes.carregar_secretaria_armadilhas).

    Returns:
        A tabela semana a semana do vetor, uma linha por semana da grade
        continua, com as colunas definidas em COLUNAS_VETOR_SEMANAL.

    """
    inspecoes = df_secretaria.copy()
    inspecoes["aedes_aegypti_total"] = inspecoes["aegypti_femea"] + inspecoes["aegypti_macho"]
    inspecoes["aedes_albopictus_total"] = inspecoes["albopictus_femea"] + inspecoes["albopictus_macho"]
    inspecoes["culex_sp_total"] = inspecoes["culex_femea"] + inspecoes["culex_macho"]
    inspecoes["foi_inspecionada"] = inspecoes["inspecao_realizada"].fillna(False)

    por_semana = inspecoes.groupby("data_inicio_semana").agg(
        fonte=("fonte", "first"),
        registros_na_semana=("ano", "size"),
        armadilhas_inspecionadas=("foi_inspecionada", "sum"),
        realizada_desconhecida=("inspecao_realizada", semana_tem_denominador_aproximado),
        femeas_aegypti=("aegypti_femea", "sum"),
        aedes_aegypti=("aedes_aegypti_total", "sum"),
        aedes_albopictus=("aedes_albopictus_total", "sum"),
        culex_sp=("culex_sp_total", "sum"),
    )

    grade_semanal = pd.date_range(por_semana.index.min(), por_semana.index.max(), freq="W-SUN")
    vetor_semanal = (
        por_semana.reindex(grade_semanal)
        .rename_axis("data_inicio_semana_epidemi")
        .reset_index()
    )

    semana_epidemiologica = calcular_semana_epidemiologica(
        vetor_semanal["data_inicio_semana_epidemi"]
    )
    vetor_semanal["ano"] = semana_epidemiologica["ano"]
    vetor_semanal["semana"] = semana_epidemiologica["semana"]
    vetor_semanal["SE"] = semana_epidemiologica["SE"]

    # A marca vai como 0/1 (e nao True/False) de proposito: o CSV guarda texto,
    # e True/False relido do CSV vira texto de novo, o que derruba o modelo se
    # a coluna escapar para ele. Como 0/1 ela relida vira numero.
    vetor_semanal["denominador_aproximado"] = vetor_semanal["realizada_desconhecida"].astype("Int64")
    usa_denominador_aproximado = vetor_semanal["denominador_aproximado"].fillna(0) == 1
    vetor_semanal["numero_de_armadilhas"] = vetor_semanal["armadilhas_inspecionadas"]
    vetor_semanal.loc[usa_denominador_aproximado, "numero_de_armadilhas"] = vetor_semanal.loc[
        usa_denominador_aproximado, "registros_na_semana"
    ]
    vetor_semanal["numero_de_armadilhas"] = vetor_semanal["numero_de_armadilhas"].astype("Int64")

    vetor_semanal["aedes_aegypti_por_armadilha"] = (
        vetor_semanal["femeas_aegypti"] / vetor_semanal["numero_de_armadilhas"]
    )
    for coluna_contagem in ["aedes_aegypti", "aedes_albopictus", "culex_sp"]:
        vetor_semanal[coluna_contagem] = vetor_semanal[coluna_contagem].astype("Int64")

    return vetor_semanal[COLUNAS_VETOR_SEMANAL]



def incorporar_clima_casos_enso(
    vetor_semanal: pd.DataFrame,
    df_clima: pd.DataFrame,
    df_casos: pd.DataFrame,
    df_enso: pd.DataFrame,
) -> pd.DataFrame:
    """

    Junta o clima, os casos confirmados de dengue e o El Nino / La Nina na
    tabela semana a semana do mosquito.

    O clima entra casando pela data de inicio da semana. Os casos entram
    contando quantos casos tem em cada semana (SE). O El Nino / La Nina
    entra casando pelo mes do calendario do domingo daquela semana.

    Os casos confirmados so tem serie local a partir de 2018 (o SINAN so
    comeca a reportar POA daquele ano em diante nesta base): semana anterior
    a 2018 fica sem informacao (NaN), nunca zero, porque simplesmente nao
    existe serie ali. Dentro do periodo com serie, quando uma semana nao tem
    nenhum caso registrado, o numero de casos vira zero de verdade - isso
    vale ate a ultima semana que ja teve tempo de amadurecer (ver
    JANELA_MATURACAO_CASOS_SEMANAS); as semanas mais recentes que ainda podem
    estar em apuracao no SINAN ficam em branco (NaN) em vez de zero.

    Returns:
        A tabela_final semana a semana, com o mosquito, o clima, os casos
        confirmados e o El Nino / La Nina juntos.

    """
    df_casos = df_casos.copy()
    df_casos["SE"] = pd.to_numeric(df_casos["SEM_PRI"], errors="coerce").astype("Int64")
    casos_semanais = (
        df_casos.groupby("SE").size().rename("casos_confirmados").reset_index()
    )

    tabela = vetor_semanal.merge(
        df_clima, on="data_inicio_semana_epidemi", how="left"
    ).merge(casos_semanais, on="SE", how="left")

    # A serie local de casos comeca na primeira semana que o arquivo de casos
    # tem (por volta de 2018); antes disso nao e "zero caso", e "sem serie".
    primeira_se_com_serie_de_casos = int(casos_semanais["SE"].min())

    # Dentro do periodo que o arquivo de casos divulgou, semana sem nenhum
    # registro e zero de verdade. Depois da ultima semana com registro nao
    # existe divulgacao nenhuma, entao fica sem informacao (NaN), nunca zero.
    # As semanas recentes DENTRO do periodo divulgado podem estar com numero
    # baixo por ainda estarem em apuracao - quem desconta isso e o corte de
    # maturidade de cada experimento (ver comentario no topo deste arquivo).
    ultima_se_divulgada = int(casos_semanais["SE"].max())

    dentro_da_serie_divulgada = (tabela["SE"] >= primeira_se_com_serie_de_casos) & (
        tabela["SE"] <= ultima_se_divulgada
    )
    tabela.loc[dentro_da_serie_divulgada, "casos_confirmados"] = tabela.loc[
        dentro_da_serie_divulgada, "casos_confirmados"
    ].fillna(0)

    depois_da_serie_divulgada = tabela["SE"] > ultima_se_divulgada
    tabela.loc[depois_da_serie_divulgada, "casos_confirmados"] = np.nan

    tabela["casos_confirmados"] = tabela["casos_confirmados"].astype("Int64")

    # O El Nino / La Nina (dado mensal) casa pelo mes do calendario do domingo da semana.
    enso_por_mes = df_enso.rename(columns={"ano": "ano_cal", "mes": "mes_cal"})
    tabela["ano_cal"] = tabela["data_inicio_semana_epidemi"].dt.year
    tabela["mes_cal"] = tabela["data_inicio_semana_epidemi"].dt.month
    tabela = tabela.merge(enso_por_mes, on=["ano_cal", "mes_cal"], how="left").drop(
        columns=["ano_cal", "mes_cal"]
    )
    return tabela



def montar_tabela_final(
    df_secretaria: pd.DataFrame,
    df_clima: pd.DataFrame,
    df_casos: pd.DataFrame,
    df_enso: pd.DataFrame,
) -> pd.DataFrame:
    """

    Junta todos os passos e monta a tabela_final inteira, a partir dos
    arquivos originais (ainda sem nenhum tratamento).

    Returns:
        A tabela_final semana a semana, pronta para ser salva e usada nos
        experimentos.

    """
    vetor_semanal = agregar_vetor_semanal(df_secretaria)
    return incorporar_clima_casos_enso(vetor_semanal, df_clima, df_casos, df_enso)
