"""

Configuracao do experimento de deteccao de surto na cidade com alvo NOTIFICADOS.

E o mesmo experimento do cidade_deteccao_surto - "vai ter surto ou nao?" -
mudando SO o alvo: no lugar dos casos confirmados do SINAN (serie que so
comeca em 2018), entram os casos notificados do InfoDengue (serie desde 2010).
Todo o resto e identico de proposito: mesmos horizontes, mesmos percentis,
mesmo classificador, mesmos hiperparametros. Se algo mais mudasse, nao daria
pra atribuir a diferenca ao alvo.

Pre-declarado em 29/08/2026 (analises/2026-08-29_rodadas_notificados_zonas/
PRE_DECLARACAO.md, Rodada 1), ANTES de rodar: 6 comparacoes (3 horizontes x 2
percentis), correcao de Holm, alfa 0,05.

"""

import dataclasses

from lightgbm import LGBMClassifier

from config.modelo import EspecificacaoModelo


@dataclasses.dataclass(frozen=True)
class ConfiguracaoSurtoNotificados:
    """

    Parametros do experimento de deteccao de surto com alvo notificados.

    Attributes:
        nome: Nome que identifica este experimento.
        horizontes: Pra quantas semanas a frente o modelo tenta prever.
        percentis: Percentis de casos que marcam a partir de quando e
            considerado surto.
        modelo: A ficha do classificador usado.
        semanas_corte_maturidade: Semanas mais recentes em que os casos ficam
            em branco (NaN) por ainda estarem em apuracao. Mantido em 12,
            igual ao experimento de confirmados, pra que a unica diferenca
            entre os dois seja o alvo. O InfoDengue tambem revisa as semanas
            recentes pra tras, entao o corte continua fazendo sentido aqui.
        alfa: Nivel de significancia usado na correcao de multiplas comparacoes.
        prefixos_clima: Comeco do nome das colunas de clima usadas.
        prefixos_autorregressivo: Comeco do nome das colunas que usam os casos
            do passado pra ajudar a prever os casos futuros.
        prefixos_vetor: Comeco do nome das colunas que vem das armadilhas.
        arquivo_saida_metricas: Nome do CSV com as metricas por modelo.
        arquivo_saida_mcnemar: Nome do CSV com o McNemar ja corrigido por Holm.

    """

    nome: str
    horizontes: tuple[int, ...]
    percentis: tuple[int, ...]
    modelo: EspecificacaoModelo
    semanas_corte_maturidade: int
    alfa: float
    prefixos_clima: tuple[str, ...]
    prefixos_autorregressivo: tuple[str, ...]
    prefixos_vetor: tuple[str, ...]
    arquivo_saida_metricas: str
    arquivo_saida_mcnemar: str


CIDADE_SURTO_NOTIFICADOS = ConfiguracaoSurtoNotificados(
    nome="cidade_surto_notificados",
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
    alfa=0.05,
    prefixos_clima=(
        "temp_media_lag",
        "precip_total_mm_lag",
        "orvalho_media_lag",
        "umid_media_lag",
        "pressao_media_lag",
    ),
    prefixos_autorregressivo=("casos_lag", "casos_mm"),
    prefixos_vetor=("aedes_aegypti_por_armadilha_lag", "vetor_mm"),
    arquivo_saida_metricas="surto_notificados_resultados.csv",
    arquivo_saida_mcnemar="surto_notificados_mcnemar.csv",
)
