"""

Configuracao do experimento de regressao SEM os dados do El Nino/La Nina e SEM
cortar as semanas recentes (o "Modelo 4b").

E igual ao cidade_regressao, mas sem apagar as semanas mais novas de casos. Serve
pra ver o ganho do mosquito quando a gente usa todas as semanas de casos que o
governo ja reportou, e sem deixar o El Nino entre os candidatos de clima.

"""

from config.experimentos.cidade_regressao import ConfiguracaoRegressao, LGBM_REGRESSAO

CIDADE_REGRESSAO_SEM_ENSO = ConfiguracaoRegressao(
    nome="cidade_regressao_sem_enso",
    coluna_alvo="casos",
    modelo=LGBM_REGRESSAO,
    modelo_selecao_clima=LGBM_REGRESSAO,
    # 0 = nao apaga nenhuma semana recente (diferente do cidade_regressao, que apaga 12).
    semanas_corte_maturidade=0,
    horizontes=tuple(range(1, 13)),
    horizontes_selecao_clima=(1, 4, 8),
    valores_k=(6, 8),
    fracao_treino_selecao=0.60,
    minimo_semanas_treino=104,
    passo=2,
    # O El Nino/La Nina (nino34_anom, oni) fica de fora dos candidatos de clima.
    colunas_ignorar=(
        "fonte", "SE", "data", "ano", "semana", "interpolado",
        "aedes_aegypti", "aedes_albopictus", "culex_sp", "numero_de_armadilhas",
        "nino34_anom", "oni",
    ),
    padroes_vetor=("aedes", "armadilha", "vetor"),
    padroes_clima=(
        "temp", "precip", "orvalho", "umid", "pressao", "radiacao", "vento", "dias_de_chuva",
    ),
    arquivo_saida="clima_enxuto_sem_enso_resultados.csv",
    colunas_saida=("algoritmo", "conjunto", "h", "MAE", "R2"),
)
