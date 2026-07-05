"""

Configuracao do experimento de Diebold-Mariano: prova (estatistica) se somar o
mosquito faz o modelo errar menos de um jeito confiavel.

Compara o M0 (so clima, sem El Nino) com o M1 (clima + mosquito), semana a
semana, pra cada quantidade de semanas a frente. Roda de dois jeitos: sem cortar
as semanas recentes e cortando as ultimas 12 (pra ver se a conclusao depende
disso). Usa as 6 colunas de clima que mais ajudam.

"""

import dataclasses

from config.experimentos.cidade_regressao import LGBM_REGRESSAO
from config.modelo import EspecificacaoModelo


@dataclasses.dataclass(frozen=True)
class ConfiguracaoDiebold:
    """

    Os ajustes do experimento de Diebold-Mariano.

    Attributes:
        nome: Nome que identifica este experimento.
        coluna_alvo: Nome da coluna que o modelo tenta prever ('casos').
        modelo: A ficha do algoritmo comparado (M0 so-clima x M1 clima+mosquito).
        modelo_selecao_clima: A ficha do algoritmo que escolhe as colunas de clima.
        horizontes: Quantas semanas a frente o modelo tenta prever, em cada rodada.
        horizontes_selecao_clima: Quais semanas a frente sao usadas pra escolher
            as colunas de clima que mais ajudam.
        valor_k: Quantas colunas de clima entram no modelo (as que mais ajudam).
        fracao_treino_selecao: Que pedaco inicial dos dados e usado nessa escolha.
        minimo_semanas_treino: Historico minimo antes de comecar a prever.
        passo: De quantas em quantas semanas o treino-e-previsao se repete.
        colunas_ignorar: Colunas que nao entram no modelo (inclui o El Nino/La
            Nina, que aqui fica de fora).
        padroes_vetor: Pedacos de nome que indicam que a coluna e sobre o mosquito.
        padroes_clima: Pedacos de nome que indicam que a coluna e sobre o clima.
        cortes_maturidade: Lista de (nome, quantas semanas recentes apagar). Roda
            o teste uma vez pra cada opcao.
        colunas_saida: Quais colunas (e em que ordem) ficam na tabela final.
        arquivo_saida: Nome do arquivo .csv onde a tabela de resultados e salva.

    """

    nome: str
    coluna_alvo: str
    modelo: EspecificacaoModelo
    modelo_selecao_clima: EspecificacaoModelo
    horizontes: tuple[int, ...]
    horizontes_selecao_clima: tuple[int, ...]
    valor_k: int
    fracao_treino_selecao: float
    minimo_semanas_treino: int
    passo: int
    colunas_ignorar: tuple[str, ...]
    padroes_vetor: tuple[str, ...]
    padroes_clima: tuple[str, ...]
    cortes_maturidade: tuple[tuple[str, int], ...]
    colunas_saida: tuple[str, ...]
    arquivo_saida: str


CIDADE_DIEBOLD = ConfiguracaoDiebold(
    nome="cidade_diebold",
    coluna_alvo="casos",
    modelo=LGBM_REGRESSAO,
    modelo_selecao_clima=LGBM_REGRESSAO,
    horizontes=tuple(range(1, 13)),
    horizontes_selecao_clima=(1, 4, 8),
    valor_k=6,
    fracao_treino_selecao=0.60,
    minimo_semanas_treino=104,
    # Passo 1: testa TODAS as semanas (o teste estatistico quer o maximo de pontos).
    passo=1,
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
    cortes_maturidade=(
        ("sem_maturidade", 0),
        ("com_maturidade", 12),
    ),
    colunas_saida=("algoritmo", "conjunto", "h", "n", "dMAE", "DM_sq", "p_sq", "DM_abs", "p_abs"),
    arquivo_saida="diebold_mariano_resultados.csv",
)
