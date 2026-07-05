"""

Configuracao do experimento que preve o mosquito POR BAIRRO.

A gente so tem contagem de mosquito por bairro (nao casos de dengue por bairro),
entao aqui o alvo e a densidade de mosquito de cada bairro. O experimento compara
quatro receitas de colunas, pra ver o quanto ajuda (1) somar o que acontece na
vizinhanca e (2) somar as colunas "melhoradas" (passado mais longe, criticidade
e a epoca do ano do alvo):

  - base_own:  so o passado do proprio bairro (semanas atras, media movel, epoca do ano);
  - base_+viz: base_own + o passado da vizinhanca;
  - enh_own:   base_own + colunas melhoradas + a epoca do ano da semana-alvo;
  - enh_+viz:  enh_own + vizinhanca (semanas atras, media movel e a diferenca pro vizinho).

"""

import dataclasses

from lightgbm import LGBMRegressor

from config.modelo import EspecificacaoModelo

# Colunas de "semanas atras" da densidade do proprio bairro e da vizinhanca.
COLUNAS_LAG_DENSIDADE = ["dens_lag1", "dens_lag2", "dens_lag3", "dens_lag4"]
COLUNAS_LAG_VIZINHANCA = ["viz_lag1", "viz_lag2", "viz_lag3", "viz_lag4"]

# As quatro receitas de colunas comparadas no experimento.
FEATURES_OWN_BASE = COLUNAS_LAG_DENSIDADE + ["dens_mm4", "sin", "cos"]
FEATURES_VIZ_BASE = FEATURES_OWN_BASE + COLUNAS_LAG_VIZINHANCA
FEATURES_OWN_ENH = FEATURES_OWN_BASE + ["crit", "dens_lag8", "dens_lag52"]
FEATURES_VIZ_ENH = FEATURES_OWN_ENH + COLUNAS_LAG_VIZINHANCA + ["viz_mm4", "grad1"]


@dataclasses.dataclass(frozen=True)
class ConfiguracaoBairroSurto:
    """

    Os ajustes do experimento de previsao de mosquito por bairro.

    Attributes:
        nome: Nome que identifica este experimento.
        coluna_alvo: O que o modelo tenta prever ('dens', a densidade de mosquito).
        anos: De quais anos abrir as capturas de mosquito.
        numero_vizinhos: Quantos bairros vizinhos considerar em cada bairro.
        modelo: A ficha do algoritmo usado pra prever a densidade de mosquito.
        horizontes: Quantas semanas a frente prever, em cada rodada.
        semana_minima_teste: A partir de qual semana comecar a testar.
        passo: De quantas em quantas semanas testar.
        minimo_linhas_treino: Quantas linhas de treino sao precisas, no minimo.
        combos: Lista de (nome, colunas, usar_epoca_do_alvo). Cada combo e uma
            receita de colunas comparada com as outras.
        colunas_ganho: (coluna_A, coluna_B) usadas pra calcular o ganho das
            colunas melhoradas (A - B).
        colunas_lift_vizinhanca: (coluna_A, coluna_B) usadas pra calcular o
            quanto a vizinhanca ajuda (A - B).
        arquivo_saida: Nome do arquivo .csv onde a tabela de resultados e salva.

    """

    nome: str
    coluna_alvo: str
    anos: tuple[int, ...]
    numero_vizinhos: int
    modelo: EspecificacaoModelo
    horizontes: tuple[int, ...]
    semana_minima_teste: int
    passo: int
    minimo_linhas_treino: int
    combos: tuple[tuple[str, tuple[str, ...], bool], ...]
    colunas_ganho: tuple[str, str]
    colunas_lift_vizinhanca: tuple[str, str]
    arquivo_saida: str


BAIRRO_SURTO = ConfiguracaoBairroSurto(
    nome="bairro_surto",
    coluna_alvo="dens",
    anos=tuple(range(2019, 2024)),
    numero_vizinhos=4,
    modelo=EspecificacaoModelo(
        nome="lightgbm",
        classe=LGBMRegressor,
        parametros={
            "n_estimators": 300,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_child_samples": 20,
            "verbose": -1,
            "n_jobs": -1,
        },
    ),
    horizontes=tuple(range(1, 5)),
    semana_minima_teste=120,
    passo=4,
    minimo_linhas_treino=200,
    combos=(
        ("base_own", tuple(FEATURES_OWN_BASE), False),
        ("base_+viz", tuple(FEATURES_VIZ_BASE), False),
        ("enh_own", tuple(FEATURES_OWN_ENH), True),
        ("enh_+viz", tuple(FEATURES_VIZ_ENH), True),
    ),
    colunas_ganho=("enh_+viz", "base_+viz"),
    colunas_lift_vizinhanca=("enh_+viz", "enh_own"),
    arquivo_saida="bairro_vetor_r2_resultados.csv",
)
