"""

Configuracao do experimento de regressao COM os dados do El Nino/La Nina entre
os candidatos de clima (e sem cortar as semanas recentes).

E o teste do confundimento: aqui o El Nino (nino34_anom, oni) PODE entrar na
escolha das poucas colunas de clima que mais ajudam. Comparando com o
cidade_regressao_sem_enso, da pra ver se o El Nino estava "mascarando" o ganho
do mosquito. No fim, junta as linhas de referencia (so clima e so mosquito)
que vieram do experimento cidade_lift_vetor.

"""

from config.experimentos.cidade_regressao import ConfiguracaoRegressao, LGBM_REGRESSAO

CIDADE_REGRESSAO_COM_ENSO = ConfiguracaoRegressao(
    nome="cidade_regressao_com_enso",
    coluna_alvo="casos",
    modelo=LGBM_REGRESSAO,
    modelo_selecao_clima=LGBM_REGRESSAO,
    # 0 = nao apaga nenhuma semana recente.
    semanas_corte_maturidade=0,
    horizontes=tuple(range(1, 13)),
    horizontes_selecao_clima=(1, 4, 8),
    valores_k=(6, 8),
    fracao_treino_selecao=0.60,
    minimo_semanas_treino=104,
    passo=2,
    # Aqui o El Nino/La Nina NAO esta na lista de ignorados, entao ele entra
    # como candidato de clima (repare que os padroes de clima abaixo incluem
    # "nino34" e "oni").
    colunas_ignorar=(
        "fonte", "SE", "data", "ano", "semana", "interpolado",
        "aedes_aegypti", "aedes_albopictus", "culex_sp", "numero_de_armadilhas",
    ),
    padroes_vetor=("aedes", "armadilha", "vetor"),
    padroes_clima=(
        "temp", "precip", "orvalho", "umid", "pressao", "radiacao", "vento", "dias_de_chuva",
        "nino34", "oni",
    ),
    arquivo_saida="clima_enxuto_vetor_resultados.csv",
    colunas_saida=("algoritmo", "conjunto", "h", "MAE", "R2"),
    # Junta no fim as linhas "so clima" e "so mosquito" ja calculadas no cidade_lift_vetor.
    arquivo_referencias="lift_limpo_resultados.csv",
    conjuntos_referencia=("so_clima", "so_vetor"),
)
