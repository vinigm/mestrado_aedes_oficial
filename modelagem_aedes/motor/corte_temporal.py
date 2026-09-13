"""

A regra que decide quais linhas podem entrar no treino de um walk-forward.

POR QUE ESTE MODULO EXISTE

  Numa tabela de previsao, cada linha tem DUAS datas: a data de ORIGEM, de
  onde vem as features, e a data da RESPOSTA, que e a origem mais o horizonte.
  A linha so fica pronta na data da resposta - antes disso o rotulo dela ainda
  nao aconteceu.

  Ate 13/09/2026 os walk-forwards do projeto cortavam o treino por POSICAO
  (dados.iloc[:indice_corte]), o que equivale a filtrar pela data de ORIGEM.
  Com isso, as h-1 linhas mais recentes do treino entravam com rotulo datado
  DEPOIS da semana que estava sendo prevista.

  Exemplo real, h=12: ao prever 26/05/2024 a partir de 03/03/2024, o treino
  incluia a linha de 18/02/2024, cujo rotulo e 12/05/2024 = 1.510 casos, o
  pico da epidemia. Em 03/03 esse numero nao existia.

  Medido em 13/09/2026: corrigir custa +31,5% de MAE em h=4 e +52,5% em h=12,
  na configuracao de referencia. Ver analises/2026-09-13_correcao_vazamento_treino/.

POR QUE FILTRAR POR DATA E NAO POR POSICAO

  A forma curta - iloc[:indice_corte - horizonte + 1] - parece equivalente e
  esta ERRADA: depois do dropna a tabela tem buracos (o vetor e NaN nas
  semanas da enchente de maio/2024, por exemplo). Com buraco, recuar 12
  POSICOES nao equivale a recuar 12 SEMANAS.

"""

import pandas as pd


def selecionar_treino_ja_respondido(
    dados_validos: pd.DataFrame,
    data_de_origem_do_teste,
    horizonte: int,
    coluna_data: str = "data",
) -> pd.DataFrame:
    """

    Devolve so as linhas cuja RESPOSTA ja tinha acontecido na data da previsao.

    A linha cuja resposta cai exatamente na data de origem do teste ENTRA: o
    valor dela ja e conhecido nesse dia.

    Args:
        dados_validos: Tabela do walk-forward, ja sem nulos e em ordem
            cronologica, com uma coluna de data de ORIGEM.
        data_de_origem_do_teste: A data da semana a partir da qual a previsao
            esta sendo feita.
        horizonte: Quantas semanas a frente se preve.
        coluna_data: Nome da coluna com a data de origem.

    Returns:
        Um recorte de dados_validos com as linhas liberadas para treino.

    """
    atraso_do_horizonte = pd.Timedelta(weeks=horizonte)
    linha_ja_respondida = (
        dados_validos[coluna_data] + atraso_do_horizonte <= data_de_origem_do_teste
    )
    return dados_validos.loc[linha_ja_respondida]
