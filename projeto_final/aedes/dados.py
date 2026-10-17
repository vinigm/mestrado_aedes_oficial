"""Dados do pacote `aedes`: impressao digital, esquema e corte de maturidade.

Todas as funcoes aqui sao puras: recebem bytes ou DataFrames e devolvem
resultado ou levantam erro. Nenhuma le nem grava arquivo; quem le
`dados/tabela_final.csv` (os testes e, no futuro, `experimentos/`) entrega o
conteudo a estas funcoes.

O corte de maturidade replica, sem nenhuma correcao, a regra do codigo antigo
(`modelagem_aedes/dominio/surto.py`, funcao `aplicar_corte_maturidade`).
"""

import hashlib
import io

import numpy as np
import pandas as pd

from aedes.configuracao import DIA_DA_SEMANA_DO_DOMINGO, ConfiguracaoDados

UMA_SEMANA = pd.Timedelta(weeks=1)
QUANTIDADE_DE_EXEMPLOS_NA_MENSAGEM = 5


def validar_impressao_digital(conteudo_em_bytes: bytes, sha256_esperado: str) -> None:
    """Garante que o arquivo da tabela e exatamente o snapshot certificado.

    Todo numero do artigo parte de `dados/tabela_final.csv`; se um byte mudar,
    as ancoras deixam de valer e a execucao tem de parar.

    Args:
        conteudo_em_bytes: Conteudo integral do arquivo, lido em modo binario.
        sha256_esperado: Hash sha256 esperado, em hexadecimal (maiusculas ou
            minusculas).

    Raises:
        ValueError: Se o sha256 calculado for diferente do esperado.
    """
    sha256_calculado = hashlib.sha256(conteudo_em_bytes).hexdigest()
    sha256_esperado_em_minusculas = sha256_esperado.strip().lower()

    if sha256_calculado != sha256_esperado_em_minusculas:
        raise ValueError(
            "Impressao digital da tabela diverge: "
            f"calculado {sha256_calculado}, esperado {sha256_esperado_em_minusculas}. "
            "O arquivo nao e o snapshot certificado; nenhuma ancora do artigo vale."
        )


def _formatar_exemplos(valores: pd.Series) -> str:
    """Mostra os primeiros valores de uma serie para compor mensagem de erro."""
    primeiros_valores = valores.head(QUANTIDADE_DE_EXEMPLOS_NA_MENSAGEM)
    return ", ".join(str(valor) for valor in primeiros_valores)


def validar_esquema(tabela: pd.DataFrame, configuracao: ConfiguracaoDados) -> None:
    """Confere que a tabela e uma grade semanal contigua e bem tipada.

    Verificacoes, na ordem em que sao feitas (a primeira que falhar levanta):
        1. colunas obrigatorias presentes;
        2. numero de linhas e de colunas igual ao esperado;
        3. coluna de data em formato de data, sem ausentes;
        4. toda data e um domingo;
        5. datas sem duplicata e em ordem crescente;
        6. grade sem buracos (cada data 7 dias depois da anterior);
        7. primeira data igual a `primeira_data_da_grade`;
        8. colunas obrigatorias numericas (a de data fica de fora);
        9. casos sem infinito e sem valor negativo (ausente e permitido: a
           serie so comeca em 2018 e termina antes do fim da grade).

    A primeira falha interrompe a validacao; os erros nao se acumulam.

    Args:
        tabela: Tabela semanal ja lida (a coluna de data ja convertida para
            data, por exemplo com `parse_dates` no `read_csv`).
        configuracao: Valores esperados da tabela.

    Raises:
        KeyError: Se faltar alguma coluna obrigatoria.
        ValueError: Para qualquer outra violacao, com mensagem que diz o que
            foi encontrado.
    """
    colunas_presentes = set(tabela.columns)
    colunas_ausentes = []
    for nome_da_coluna in configuracao.colunas_obrigatorias:
        if nome_da_coluna not in colunas_presentes:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas obrigatorias ausentes na tabela: {colunas_ausentes}")

    forma_esperada = (configuracao.linhas_esperadas, configuracao.colunas_esperadas)
    if tabela.shape != forma_esperada:
        raise ValueError(
            f"Tabela com forma {tabela.shape} (linhas, colunas); esperado {forma_esperada}."
        )

    datas = tabela[configuracao.coluna_de_data]
    if not pd.api.types.is_datetime64_any_dtype(datas):
        raise ValueError(
            f"A coluna {configuracao.coluna_de_data!r} deve ser de data, "
            f"mas tem dtype {datas.dtype}."
        )
    if datas.isna().any():
        raise ValueError(f"A coluna {configuracao.coluna_de_data!r} tem datas ausentes.")

    dias_da_semana = datas.dt.dayofweek
    datas_fora_de_domingo = datas[dias_da_semana != DIA_DA_SEMANA_DO_DOMINGO]
    if not datas_fora_de_domingo.empty:
        raise ValueError(
            f"{len(datas_fora_de_domingo)} data(s) que nao sao domingo, "
            f"por exemplo: {_formatar_exemplos(datas_fora_de_domingo.dt.date)}."
        )

    datas_duplicadas = datas[datas.duplicated(keep=False)]
    if not datas_duplicadas.empty:
        raise ValueError(
            f"Datas duplicadas na grade semanal, por exemplo: "
            f"{_formatar_exemplos(datas_duplicadas.dt.date)}."
        )
    if not datas.is_monotonic_increasing:
        raise ValueError("As datas da grade semanal nao estao em ordem crescente.")

    intervalos = datas.diff().dropna()
    intervalos_diferentes_de_uma_semana = intervalos[intervalos != UMA_SEMANA]
    if not intervalos_diferentes_de_uma_semana.empty:
        posicoes_dos_buracos = intervalos_diferentes_de_uma_semana.index
        datas_depois_do_buraco = datas.loc[posicoes_dos_buracos]
        raise ValueError(
            f"Buraco na grade semanal: {len(posicoes_dos_buracos)} intervalo(s) "
            "diferente(s) de 7 dias, antes de "
            f"{_formatar_exemplos(datas_depois_do_buraco.dt.date)}."
        )

    primeira_data = datas.iloc[0]
    if primeira_data != configuracao.primeira_data_da_grade:
        raise ValueError(
            f"A grade comeca em {primeira_data.date()}; "
            f"esperado {configuracao.primeira_data_da_grade.date()}."
        )

    for nome_da_coluna in configuracao.colunas_obrigatorias:
        if nome_da_coluna == configuracao.coluna_de_data:
            continue
        coluna = tabela[nome_da_coluna]
        coluna_e_numerica = pd.api.types.is_numeric_dtype(coluna)
        coluna_e_booleana = pd.api.types.is_bool_dtype(coluna)
        if not coluna_e_numerica or coluna_e_booleana:
            raise ValueError(
                f"A coluna {nome_da_coluna!r} deve ser numerica, mas tem dtype {coluna.dtype}."
            )

    casos = tabela[configuracao.coluna_de_casos].astype("float64")
    casos_infinitos = casos[np.isinf(casos)]
    if not casos_infinitos.empty:
        raise ValueError(
            f"{len(casos_infinitos)} valor(es) infinito(s) em {configuracao.coluna_de_casos!r}."
        )
    casos_negativos = casos[casos < 0]
    if not casos_negativos.empty:
        raise ValueError(
            f"{len(casos_negativos)} valor(es) negativo(s) em {configuracao.coluna_de_casos!r}."
        )


def montar_tabela_a_partir_dos_bytes(
    conteudo_em_bytes: bytes, configuracao: ConfiguracaoDados
) -> pd.DataFrame:
    """Valida o arquivo e devolve a tabela semanal pronta para o corte.

    Une as tres guardas da carga na ordem certa: impressao digital dos bytes,
    leitura do CSV com a coluna de data convertida para data, e validacao do
    esquema. Nao toca em disco: o chamador le o arquivo em modo binario.

    Args:
        conteudo_em_bytes: Conteudo integral de `dados/tabela_final.csv`.
        configuracao: Valores esperados da tabela.

    Returns:
        A tabela como veio do arquivo (mesmas linhas, mesma ordem de colunas),
        com a coluna de data em formato de data.

    Raises:
        ValueError: Se o hash divergir ou o esquema for violado.
        KeyError: Se faltar coluna obrigatoria.
    """
    validar_impressao_digital(conteudo_em_bytes, configuracao.sha256_esperado_da_tabela)

    fluxo_de_bytes = io.BytesIO(conteudo_em_bytes)
    tabela = pd.read_csv(
        fluxo_de_bytes,
        parse_dates=[configuracao.coluna_de_data],
    )

    validar_esquema(tabela, configuracao)
    return tabela


def aplicar_corte_de_maturidade(
    tabela: pd.DataFrame, configuracao: ConfiguracaoDados
) -> pd.DataFrame:
    """Apaga os casos das semanas recentes, que ainda nao terminaram de ser confirmadas.

    Os casos das semanas mais recentes aparecem subestimados no SINAN porque
    a classificacao final demora. Se o modelo os tratasse como definitivos,
    aprenderia errado; por isso viram "sem informacao" (NaN, nunca zero).

    Regra (identica a de `modelagem_aedes/dominio/surto.py:12-50`):
        1. A contagem parte da ultima semana que TEM caso, nao do fim da
           tabela. A tabela segue ate agosto/2026, mas os casos acabam em
           26/04/2026; contar do fim da tabela nao apagaria nada.
        2. `limite = ultima semana com caso - semanas_corte_maturidade semanas`.
        3. Toda linha com data ESTRITAMENTE maior que o limite fica com
           casos = NaN. Na data-limite o caso e mantido.
        4. So a coluna de casos muda; as demais colunas, o indice e a ordem
           das linhas ficam como entraram.
        5. Sem nenhum caso na tabela, ou com `semanas_corte_maturidade` = 0,
           nada e apagado e a funcao devolve uma copia igual a entrada.

    Atencao: a funcao nao e idempotente. Aplicada duas vezes, a segunda
    passada recua mais 12 semanas a partir da nova ultima semana com caso.
    O corte age UMA vez, sobre a tabela crua.

    Args:
        tabela: Tabela semanal com a coluna de data (em formato de data) e a
            de casos. Nao e modificada.
        configuracao: Fornece as colunas e `semanas_corte_maturidade`.

    Returns:
        Um DataFrame NOVO. A coluna de casos sai em float64 (precisa guardar
        NaN); as demais colunas mantem o dtype.

    Raises:
        KeyError: Se faltar a coluna de data ou a de casos.
        ValueError: Se a coluna de data nao for de data.
    """
    coluna_de_data = configuracao.coluna_de_data
    coluna_de_casos = configuracao.coluna_de_casos

    colunas_ausentes = []
    for nome_da_coluna in (coluna_de_data, coluna_de_casos):
        if nome_da_coluna not in tabela.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas necessarias ao corte ausentes: {colunas_ausentes}")

    if not pd.api.types.is_datetime64_any_dtype(tabela[coluna_de_data]):
        raise ValueError(
            f"A coluna {coluna_de_data!r} deve ser de data, mas tem dtype "
            f"{tabela[coluna_de_data].dtype}."
        )

    tabela_com_corte = tabela.copy()
    tabela_com_corte[coluna_de_casos] = tabela_com_corte[coluna_de_casos].astype("float64")

    semanas_com_caso = tabela_com_corte.dropna(subset=[coluna_de_casos])
    nao_ha_casos = semanas_com_caso.empty
    corte_desligado = configuracao.semanas_corte_maturidade == 0
    if nao_ha_casos or corte_desligado:
        return tabela_com_corte

    ultima_semana_com_caso = semanas_com_caso[coluna_de_data].max()
    limite_de_maturidade = ultima_semana_com_caso - pd.Timedelta(
        weeks=configuracao.semanas_corte_maturidade
    )

    mascara_de_semanas_imaturas = tabela_com_corte[coluna_de_data] > limite_de_maturidade
    tabela_com_corte.loc[mascara_de_semanas_imaturas, coluna_de_casos] = np.nan
    return tabela_com_corte


def obter_ultima_semana_com_caso(
    tabela: pd.DataFrame, configuracao: ConfiguracaoDados
) -> pd.Timestamp:
    """Devolve a data da ultima semana com caso nao ausente da tabela recebida.

    Aplicada a tabela JA cortada, e a ultima semana mantida (para a tabela
    certificada, 01/02/2026). Aplicada a tabela crua, e a ultima semana com
    caso divulgado (26/04/2026).

    Args:
        tabela: Tabela semanal com a coluna de data e a de casos.
        configuracao: Fornece os nomes das colunas.

    Returns:
        A maior data cuja linha tem casos nao ausentes.

    Raises:
        KeyError: Se faltar a coluna de data ou a de casos.
        ValueError: Se nao houver nenhuma semana com caso.
    """
    colunas_ausentes = []
    for nome_da_coluna in (configuracao.coluna_de_data, configuracao.coluna_de_casos):
        if nome_da_coluna not in tabela.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes: {colunas_ausentes}")

    semanas_com_caso = tabela.dropna(subset=[configuracao.coluna_de_casos])
    if semanas_com_caso.empty:
        raise ValueError("A tabela nao tem nenhuma semana com caso.")

    ultima_semana = semanas_com_caso[configuracao.coluna_de_data].max()
    return ultima_semana
