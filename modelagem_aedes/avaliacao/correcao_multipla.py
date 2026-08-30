"""

Correcao de multiplas comparacoes.

Quando o mesmo estudo roda varios testes (aqui: 3 horizontes x 2 percentis = 6
comparacoes), a chance de pelo menos um dar "significativo" por puro acaso
cresce com o numero de testes. Com 6 testes a 5%, essa chance passa de 5% pra
cerca de 26% se ninguem corrigir nada. A correcao ajusta os p-valores pra que a
conclusao continue valendo pro conjunto todo, e nao so pro teste isolado que
por acaso saiu melhor.

O metodo usado e o de Holm (1979), tambem chamado de Holm-Bonferroni. Ele
controla a mesma coisa que o Bonferroni (a chance de QUALQUER falso positivo no
conjunto) e sempre rejeita pelo menos tanto quanto ele, entao nao ha motivo pra
preferir o Bonferroni puro.

"""

import numpy as np


def corrigir_holm(valores_p: np.ndarray) -> np.ndarray:
    """

    Ajusta uma lista de p-valores pelo metodo de Holm-Bonferroni.

    O procedimento ordena os p-valores do menor pro maior, multiplica cada um
    pelo numero de testes que ainda restam naquele ponto da fila (o primeiro
    por n, o segundo por n-1, e assim por diante) e depois impoe que a
    sequencia nunca diminua - se um ajustado ficasse menor que o anterior, ele
    sobe pro valor do anterior. Por fim, nenhum ajustado passa de 1,0.

    O resultado volta na ORDEM ORIGINAL da entrada, nao na ordem crescente:
    assim da pra colar a coluna corrigida ao lado da tabela de resultados sem
    reordenar nada.

    Args:
        valores_p: Os p-valores brutos, um por comparacao. Pode conter NaN;
            comparacoes com NaN sao ignoradas na correcao e voltam como NaN
            (elas nao contam no numero de testes).

    Returns:
        Os p-valores ajustados, na mesma ordem e com o mesmo tamanho da
        entrada.

    Raises:
        ValueError: Se algum p-valor estiver fora do intervalo [0, 1].

    """
    valores_p_originais = np.asarray(valores_p, dtype=float)

    e_valido = ~np.isnan(valores_p_originais)
    valores_validos = valores_p_originais[e_valido]

    if valores_validos.size > 0:
        fora_do_intervalo = (valores_validos < 0.0) | (valores_validos > 1.0)
        if fora_do_intervalo.any():
            raise ValueError(
                "p-valores precisam estar entre 0 e 1; recebidos: "
                f"{valores_validos[fora_do_intervalo].tolist()}"
            )

    valores_corrigidos = np.full_like(valores_p_originais, np.nan)

    numero_de_testes = valores_validos.size
    if numero_de_testes == 0:
        return valores_corrigidos

    ordem_crescente = np.argsort(valores_validos)
    valores_ordenados = valores_validos[ordem_crescente]

    # Cada p-valor e multiplicado pelo numero de testes que ainda restam na
    # fila naquele ponto: o menor por n, o seguinte por n-1, etc.
    multiplicadores = numero_de_testes - np.arange(numero_de_testes)
    ajustados_ordenados = valores_ordenados * multiplicadores

    # A sequencia ajustada nao pode diminuir: um teste com p bruto maior nunca
    # pode terminar com p corrigido menor que o de um teste anterior na fila.
    ajustados_ordenados = np.maximum.accumulate(ajustados_ordenados)
    ajustados_ordenados = np.minimum(ajustados_ordenados, 1.0)

    ajustados_na_ordem_de_entrada = np.empty(numero_de_testes, dtype=float)
    ajustados_na_ordem_de_entrada[ordem_crescente] = ajustados_ordenados

    valores_corrigidos[e_valido] = ajustados_na_ordem_de_entrada
    return valores_corrigidos
