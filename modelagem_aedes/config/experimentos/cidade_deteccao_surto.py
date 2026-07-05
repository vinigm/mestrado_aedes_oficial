"""

Configuracao do experimento de deteccao de surto na cidade (antes chamado de Modelo 6).

Antes o modelo tentava adivinhar QUANTOS casos de dengue vao aparecer (uma
conta, o que se chama de regressao). Agora ele so precisa responder SIM ou
NAO: vai ter surto ou nao vai (isso se chama classificacao). Pra isso a gente
usa metricas de alarme (acertou o alerta, ou errou) e um teste estatistico
(o teste de McNemar) pra ver se os dados do mosquito realmente ajudam a
acertar mais. Tudo que e especifico deste experimento fica neste arquivo; o
resto do programa (o "motor") nao muda.

"""

import dataclasses

from lightgbm import LGBMClassifier

from config.modelo import EspecificacaoModelo


@dataclasses.dataclass(frozen=True)
class ConfiguracaoDeteccaoSurto:
    """

    Parametros do experimento de deteccao de surto na cidade.

    Attributes:
        nome: Nome que identifica este experimento.
        horizontes: Pra quantas semanas a frente o modelo tenta prever
            (1, 2 ou 3 meses vira 4, 8 ou 12 semanas).
        percentis: Percentis de casos que marcam a partir de quando e considerado surto.
        modelo: A ficha do algoritmo (um classificador) usado pra dizer se vai ter surto ou nao.
        semanas_corte_maturidade: Semanas mais recentes em que os casos ainda
            ficam em branco (NaN), porque o SINAN ainda nao fechou a contagem
            dessas semanas direito; isso so vale pra tabela_final.
        prefixos_features_infodengue: Comeco do nome das colunas calculadas a partir do Experimento A (InfoDengue).
        prefixos_clima: Comeco do nome das colunas de clima usadas (Experimento B).
        prefixos_autorregressivo: Comeco do nome das colunas que usam os casos do passado pra ajudar a prever os casos futuros.
        prefixos_vetor: Comeco do nome das colunas que vem das armadilhas de mosquito.
    """

    nome: str
    horizontes: tuple[int, ...]
    percentis: tuple[int, ...]
    modelo: EspecificacaoModelo
    semanas_corte_maturidade: int
    prefixos_features_infodengue: tuple[str, ...]
    prefixos_clima: tuple[str, ...]
    prefixos_autorregressivo: tuple[str, ...]
    prefixos_vetor: tuple[str, ...]


CIDADE_DETECCAO_SURTO = ConfiguracaoDeteccaoSurto(
    nome="cidade_deteccao_surto",
    horizontes=(4, 8, 12),
    percentis=(90, 95),
    modelo=EspecificacaoModelo(
        nome="lightgbm",
        classe=LGBMClassifier,
        parametros={
            "n_estimators": 250,
            "learning_rate": 0.05,
            "num_leaves": 15,
            "min_child_samples": 5,
            "class_weight": "balanced",
            "verbose": -1,
            "n_jobs": 1,
        },
    ),
    semanas_corte_maturidade=12,
    prefixos_features_infodengue=("casos_lag", "casos_mm", "temp_media_lag", "umid_media_lag"),
    prefixos_clima=(
        "temp_media_lag",
        "precip_total_mm_lag",
        "orvalho_media_lag",
        "umid_media_lag",
        "pressao_media_lag",
    ),
    prefixos_autorregressivo=("casos_lag", "casos_mm"),
    prefixos_vetor=("aedes_aegypti_por_armadilha_lag", "vetor_mm"),
)
