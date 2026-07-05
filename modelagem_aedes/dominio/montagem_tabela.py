"""

Aqui o programa monta a tabela_final: junta os dados de mosquito capturado
nas armadilhas, o clima, os casos de dengue confirmados e o El Nino / La
Nina numa unica tabela, semana a semana.

Isso veio de um notebook (um arquivo de anotacoes) chamado
montagem_da_tabela.ipynb, so que reescrito aqui do jeito certo. O programa
junta as capturas de mosquito vindas de duas fontes (a Marilia, de 2019 a
2023, e a raspagem, de 2025 pra frente), organiza tudo semana a semana e
calcula o valor das semanas sem coleta que ficam no meio do periodo, a
partir das semanas vizinhas. Depois junta o clima (dados da NASA), os casos
confirmados de dengue (dados do SINAN, o sistema do governo) e o El Nino /
La Nina. Essa e a parte que vem antes de tudo e deixa o projeto sempre
atualizado: quando chegam dados novos da raspagem, e so rodar de novo que a
tabela_final e refeita.

As funcoes daqui so recebem tabelas prontas e devolvem tabelas prontas —
nao abrem nem salvam arquivo nenhum. Quem abre e salva os arquivos e o
programa montar.py.

"""
import numpy as np
import pandas as pd

# Colunas do vetor semanal: quando falta uma semana no meio (sem coleta), o
# valor dela e calculado a partir das semanas vizinhas (isso e "interpolar"),
# separado por cada fonte.
COLUNAS_INTERPOLADAS = [
    "SE", "numero_de_armadilhas", "aedes_aegypti", "aedes_albopictus", "culex_sp",
]

# Essas contagens, depois de calculadas as semanas que faltavam, sao
# arredondadas para numero inteiro.
COLUNAS_CONTAGEM_VETOR = ["aedes_aegypti", "aedes_albopictus", "culex_sp"]

# Ordem final das colunas da tabela semanal do mosquito.
COLUNAS_VETOR_SEMANAL = [
    "fonte", "SE", "data_inicio_semana_epidemi", "ano", "semana",
    "numero_de_armadilhas", "aedes_aegypti", "aedes_albopictus", "culex_sp",
    "aedes_aegypti_por_armadilha", "interpolado",
]

DIAS_POR_SEMANA = 7


def unificar_marilia(df_marilia: pd.DataFrame) -> pd.DataFrame:
    """

    Deixa os dados de mosquito capturado pela Marilia no mesmo formato usado
    pelas outras fontes de armadilha.

    A latitude e a longitude da Marilia vem escritas com virgula no lugar do
    ponto (em 2021 e 2022), e tem 5 valores errados em 2022. Aqui a gente
    converte tudo para numero; o que nao da certo vira vazio (NaN).

    """
    return pd.DataFrame(
        {
            "fonte": "marilia",
            "SE": df_marilia["Ano"] * 100 + df_marilia["Semana"],
            "data_inicio_semana_epidemi": df_marilia["Data Inicio"],
            "ano": df_marilia["Ano"],
            "semana": df_marilia["Semana"],
            "id_inspecao": df_marilia["ID"],
            "local": df_marilia["Local"],
            "latitude": pd.to_numeric(
                df_marilia["Latitude"].astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            ),
            "longitude": pd.to_numeric(
                df_marilia["Longitude"].astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            ),
            "aedes_aegypti": df_marilia["Aedes aegypti"],
            "aedes_albopictus": df_marilia["Aedes albopictus"],
            "culex_sp": df_marilia["Culex sp"],
            "arquivo_origem": df_marilia["arquivo_origem"],
        }
    )



def unificar_raspagem(df_raspagem: pd.DataFrame) -> pd.DataFrame:
    """

    Deixa os dados de mosquito capturado pela raspagem no mesmo formato
    usado pelas outras fontes de armadilha.

    Aqui a gente soma femea e macho de cada especie de mosquito. O codigo
    da semana (SE) vem da coluna 'week', que traz a semana e o ano juntos
    (tipo 'SS/AAAA'). E a data de inicio da semana e sempre o domingo
    anterior ao dia em que a coleta foi feita.

    """
    partes_da_semana = df_raspagem["week"].str.split("/", expand=True)
    semana = partes_da_semana[0].astype(int)
    ano = partes_da_semana[1].astype(int)
    dias_desde_domingo = (df_raspagem["data_coleta"].dt.weekday + 1) % DIAS_POR_SEMANA
    domingo_da_semana = df_raspagem["data_coleta"] - pd.to_timedelta(
        dias_desde_domingo, unit="D"
    )
    return pd.DataFrame(
        {
            "fonte": "raspagem",
            "SE": ano * 100 + semana,
            "data_inicio_semana_epidemi": domingo_da_semana,
            "ano": ano,
            "semana": semana,
            "id_inspecao": df_raspagem["id"],
            "local": df_raspagem["neighborhood"],
            "latitude": df_raspagem["latitude"],
            "longitude": df_raspagem["longitude"],
            "aedes_aegypti": df_raspagem["aedes_aegypti_femea"] + df_raspagem["aedes_aegypti_macho"],
            "aedes_albopictus": (
                df_raspagem["aedes_albopictus_femea"] + df_raspagem["aedes_albopictus_macho"]
            ),
            "culex_sp": df_raspagem["culex_sp_femea"] + df_raspagem["culex_sp_macho"],
            "arquivo_origem": df_raspagem["arquivo_origem"],
        }
    )



# Junta as duas fontes de captura de mosquito numa unica tabela, em ordem por semana (SE) e por fonte.
def concatenar_armadilhas(
    marilia_unificada: pd.DataFrame,
    raspagem_unificada: pd.DataFrame,
) -> pd.DataFrame:
    return (
        pd.concat([marilia_unificada, raspagem_unificada], ignore_index=True)
        .sort_values(["SE", "fonte"])
        .reset_index(drop=True)
    )



def agregar_vetor_semanal(df_armadilhas: pd.DataFrame) -> pd.DataFrame:
    """

    Agrupa as capturas por semana (separado por fonte) e calcula o valor das
    semanas sem coleta que ficam no meio do periodo.

    Conta quantas armadilhas tiveram naquela semana e soma os mosquitos de
    cada especie, sempre separado por fonte e semana. Para cada fonte, a
    gente completa o calendario com todos os domingos do periodo e calcula,
    a partir das semanas vizinhas, o valor das semanas que faltam no meio
    (sem inventar valor antes do inicio, depois do fim, ou no buraco entre
    uma fonte e outra). As semanas calculadas assim ficam marcadas como
    True na coluna 'interpolado'.

    Returns:
        A tabela semana a semana do mosquito, com as colunas definidas em
        COLUNAS_VETOR_SEMANAL.

    """
    agregado = (
        df_armadilhas.groupby(["fonte", "data_inicio_semana_epidemi"])
        .agg(
            SE=("SE", "first"),
            numero_de_armadilhas=("id_inspecao", "size"),
            aedes_aegypti=("aedes_aegypti", "sum"),
            aedes_albopictus=("aedes_albopictus", "sum"),
            culex_sp=("culex_sp", "sum"),
        )
        .reset_index()
    )

    blocos = []
    for fonte in ["marilia", "raspagem"]:
        bloco = (
            agregado[agregado["fonte"] == fonte]
            .set_index("data_inicio_semana_epidemi")
            .sort_index()
            .drop(columns="fonte")
        )
        calendario_de_domingos = pd.date_range(
            bloco.index.min(), bloco.index.max(), freq="W-SUN"
        )
        bloco = bloco.reindex(calendario_de_domingos)
        bloco["fonte"] = fonte
        bloco["interpolado"] = bloco["numero_de_armadilhas"].isna()
        for coluna in COLUNAS_INTERPOLADAS:
            bloco[coluna] = bloco[coluna].interpolate(method="linear", limit_area="inside")
        blocos.append(bloco)

    vetor_semanal = (
        pd.concat(blocos).rename_axis("data_inicio_semana_epidemi").reset_index()
    )
    vetor_semanal["SE"] = vetor_semanal["SE"].round().astype(int)
    vetor_semanal["ano"] = vetor_semanal["SE"] // 100
    vetor_semanal["semana"] = vetor_semanal["SE"] % 100
    vetor_semanal["numero_de_armadilhas"] = (
        vetor_semanal["numero_de_armadilhas"].round().astype(int)
    )
    for coluna in COLUNAS_CONTAGEM_VETOR:
        vetor_semanal[coluna] = vetor_semanal[coluna].round().astype(int)
    vetor_semanal["aedes_aegypti_por_armadilha"] = (
        vetor_semanal["aedes_aegypti"] / vetor_semanal["numero_de_armadilhas"]
    )
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
    entra casando pelo mes do calendario do domingo daquela semana. Quando
    uma semana nao tem nenhum caso registrado, o numero de casos vira zero
    de verdade — isso vale ate a ultima semana que o SINAN ja divulgou;
    depois disso, como ainda pode chegar caso atrasado, o numero fica em
    branco (NaN) em vez de zero.

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

    # Semana sem caso registrado ate a ultima semana ja divulgada = zero de
    # verdade; depois disso = em branco (o caso ainda pode nao ter sido notificado).
    ultima_se_reportada = int(casos_semanais["SE"].max())
    dentro_do_reportado = tabela["SE"] <= ultima_se_reportada
    tabela.loc[dentro_do_reportado, "casos_confirmados"] = tabela.loc[
        dentro_do_reportado, "casos_confirmados"
    ].fillna(0)
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
    df_raspagem: pd.DataFrame,
    df_marilia: pd.DataFrame,
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
    marilia_unificada = unificar_marilia(df_marilia)
    raspagem_unificada = unificar_raspagem(df_raspagem)
    df_armadilhas = concatenar_armadilhas(marilia_unificada, raspagem_unificada)
    vetor_semanal = agregar_vetor_semanal(df_armadilhas)
    return incorporar_clima_casos_enso(vetor_semanal, df_clima, df_casos, df_enso)
