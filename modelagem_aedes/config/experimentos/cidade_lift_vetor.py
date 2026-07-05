"""

Configuracao do experimento que compara conjuntos FIXOS de colunas, pra medir o
ganho bruto do mosquito na previsao de casos (o "lift" do vetor).

Diferente dos outros experimentos de regressao, aqui NAO se escolhe as colunas
de clima que mais ajudam: usa-se o clima inteiro. Compara-se tres conjuntos:
so clima, clima + mosquito, e so mosquito. O El Nino/La Nina entra junto no
clima. Nao corta as semanas recentes.

"""

import dataclasses

from config.experimentos.cidade_regressao import LGBM_REGRESSAO
from config.modelo import EspecificacaoModelo


@dataclasses.dataclass(frozen=True)
class ConfiguracaoRegressaoConjuntos:
    """

    Os ajustes do experimento de lift do vetor por conjuntos fixos.

    Attributes:
        nome: Nome que identifica este experimento.
        coluna_alvo: Nome da coluna que o modelo tenta prever ('casos').
        modelo: A ficha do algoritmo usado (LightGBM, RandomForest, etc.).
        semanas_corte_maturidade: Quantas semanas recentes ficam com os casos
            apagados (0 = nao apaga nenhuma).
        horizontes: Quantas semanas a frente o modelo tenta prever, em cada rodada.
        minimo_semanas_treino: Quantas semanas de historico o modelo precisa ter,
            no minimo, antes de comecar a prever.
        passo: De quantas em quantas semanas o treino-e-previsao se repete.
        colunas_ignorar: Colunas que nao entram no modelo (identificadores e
            numeros brutos que ja viraram outras colunas).
        padroes_vetor: Pedacos de nome que indicam que a coluna e sobre o mosquito.
        padroes_clima: Pedacos de nome que indicam que a coluna e sobre o clima.
        conjuntos: Lista de (nome, inclui_clima, inclui_mosquito). O nucleo (o
            historico dos proprios casos e a epoca do ano) entra sempre.
        colunas_saida: Quais colunas (e em que ordem) ficam na tabela final.
        arquivo_saida: Nome do arquivo .csv onde a tabela de resultados e salva.

    """

    nome: str
    coluna_alvo: str
    modelo: EspecificacaoModelo
    semanas_corte_maturidade: int
    horizontes: tuple[int, ...]
    minimo_semanas_treino: int
    passo: int
    colunas_ignorar: tuple[str, ...]
    padroes_vetor: tuple[str, ...]
    padroes_clima: tuple[str, ...]
    conjuntos: tuple[tuple[str, bool, bool], ...]
    colunas_saida: tuple[str, ...]
    arquivo_saida: str


CIDADE_LIFT_VETOR = ConfiguracaoRegressaoConjuntos(
    nome="cidade_lift_vetor",
    coluna_alvo="casos",
    modelo=LGBM_REGRESSAO,
    semanas_corte_maturidade=0,
    horizontes=tuple(range(1, 13)),
    minimo_semanas_treino=104,
    passo=2,
    # O El Nino/La Nina entra junto no clima (os padroes de clima incluem "nino34" e "oni").
    colunas_ignorar=(
        "fonte", "SE", "data", "ano", "semana", "interpolado",
        "aedes_aegypti", "aedes_albopictus", "culex_sp", "numero_de_armadilhas",
    ),
    padroes_vetor=("aedes", "armadilha", "vetor"),
    padroes_clima=(
        "temp", "precip", "orvalho", "umid", "pressao", "radiacao", "vento", "dias_de_chuva",
        "nino34", "oni",
    ),
    conjuntos=(
        ("so_clima", True, False),
        ("clima_vetor", True, True),
        ("so_vetor", False, True),
    ),
    colunas_saida=("algoritmo", "conjunto", "h", "MAE", "R2"),
    arquivo_saida="lift_limpo_resultados.csv",
)
