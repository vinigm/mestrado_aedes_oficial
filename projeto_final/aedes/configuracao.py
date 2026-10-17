"""Configuracao do pacote `aedes`.

Cada grupo de parametros vive em sua propria dataclass imutavel (frozen):

    ConfiguracaoDados       carga, validacao e corte de maturidade (ciclo 1)
    ConfiguracaoVariaveis   defasagens, media movel, clima congelado e a ordem
                            das 22 variaveis do modelo (ciclo 2)
    ConfiguracaoModelo      hiperparametros do HistGradientBoosting; duas
                            instancias, FOLHA_5 e FOLHA_20 (ciclo 2)
    ConfiguracaoAvaliacao   horizontes, treino minimo e janela de avaliacao
                            (ciclo 2)

Nada aqui e variavel de modulo que se troca em execucao: o codigo antigo
trocava `features.LAGS_SEMANAS` em tempo de execucao (estado global); no pacote
novo as defasagens e as colunas sao parametros, entregues dentro de uma
configuracao.

Este modulo nao conhece nenhum caminho de arquivo: quem le a tabela (os
testes e, no futuro, `experimentos/`) decide de onde ela vem.
"""

import dataclasses

import pandas as pd

# Convencao do pandas: segunda-feira = 0, domingo = 6. As semanas
# epidemiologicas da tabela comecam no domingo.
DIA_DA_SEMANA_DO_DOMINGO = 6


@dataclasses.dataclass(frozen=True)
class ConfiguracaoDados:
    """Parametros da carga, da validacao e do corte de maturidade da tabela semanal.

    Attributes:
        sha256_esperado_da_tabela: Impressao digital (64 caracteres
            hexadecimais) do arquivo `dados/tabela_final.csv`, o snapshot
            certificado em 26/09/2026. Se o arquivo mudar, nenhuma ancora do
            artigo vale.
        linhas_esperadas: Quantas semanas a tabela tem (grade de domingos).
        colunas_esperadas: Quantas colunas a tabela tem.
        coluna_de_data: Coluna com o domingo que abre cada semana.
        coluna_de_casos: Coluna com os casos confirmados de dengue na semana.
        colunas_obrigatorias: Colunas que o modelo e a montagem de variaveis
            consomem (alem da data): `semana` (sazonalidade), `casos`, clima
            (`temp_media`, `temp_max`, `umid_media`, `pressao_media`) e vetor
            (`aedes_aegypti_por_armadilha`). Faltar uma delas e erro.
        primeira_data_da_grade: Domingo em que a grade semanal comeca.
        semanas_corte_maturidade: Quantas semanas, contadas a partir da
            ultima semana COM caso, tem os casos apagados. Os casos recentes
            ainda estao em confirmacao no SINAN e aparecem subestimados; o
            valor 12 vem do Modelo 4c de 14/06/2026 e nao foi validado com
            dados da epoca (sem dados vintage). Zero desliga o corte.
    """

    sha256_esperado_da_tabela: str
    linhas_esperadas: int
    colunas_esperadas: int
    coluna_de_data: str
    coluna_de_casos: str
    colunas_obrigatorias: tuple[str, ...]
    primeira_data_da_grade: pd.Timestamp
    semanas_corte_maturidade: int

    def __post_init__(self) -> None:
        """Rejeita configuracao incoerente na criacao, antes de qualquer calculo.

        Raises:
            ValueError: Se o hash nao tiver 64 caracteres hexadecimais, se
                linhas ou colunas esperadas nao forem positivas, se
                `semanas_corte_maturidade` for negativo ou nao inteiro, ou se
                a data e os casos nao estiverem entre as colunas obrigatorias.
        """
        tamanho_do_sha256 = 64
        hash_em_minusculas = self.sha256_esperado_da_tabela.lower()
        caracteres_validos = set("0123456789abcdef")
        hash_tem_tamanho_certo = len(hash_em_minusculas) == tamanho_do_sha256
        hash_e_hexadecimal = set(hash_em_minusculas) <= caracteres_validos
        if not (hash_tem_tamanho_certo and hash_e_hexadecimal):
            raise ValueError(
                "sha256_esperado_da_tabela deve ter 64 caracteres hexadecimais, "
                f"recebido {self.sha256_esperado_da_tabela!r}."
            )

        if self.linhas_esperadas <= 0 or self.colunas_esperadas <= 0:
            raise ValueError(
                "linhas_esperadas e colunas_esperadas devem ser positivas, "
                f"recebido {self.linhas_esperadas} x {self.colunas_esperadas}."
            )

        corte_e_inteiro = isinstance(self.semanas_corte_maturidade, int)
        corte_e_booleano = isinstance(self.semanas_corte_maturidade, bool)
        if not corte_e_inteiro or corte_e_booleano or self.semanas_corte_maturidade < 0:
            raise ValueError(
                "semanas_corte_maturidade deve ser um inteiro >= 0, "
                f"recebido {self.semanas_corte_maturidade!r}."
            )

        if self.coluna_de_data not in self.colunas_obrigatorias:
            raise ValueError(
                f"coluna_de_data {self.coluna_de_data!r} deve estar em colunas_obrigatorias."
            )
        if self.coluna_de_casos not in self.colunas_obrigatorias:
            raise ValueError(
                f"coluna_de_casos {self.coluna_de_casos!r} deve estar em colunas_obrigatorias."
            )


CONFIGURACAO_DADOS = ConfiguracaoDados(
    sha256_esperado_da_tabela=(
        "6f34b8549009c01b39b8080b904ef69af5d209ebbcbdba9357a708fd044f6f1f"
    ),
    linhas_esperadas=725,
    colunas_esperadas=36,
    coluna_de_data="data_inicio_semana_epidemi",
    coluna_de_casos="casos_confirmados",
    colunas_obrigatorias=(
        "data_inicio_semana_epidemi",
        "semana",
        "casos_confirmados",
        "temp_media",
        "temp_max",
        "umid_media",
        "pressao_media",
        "aedes_aegypti_por_armadilha",
    ),
    primeira_data_da_grade=pd.Timestamp("2012-09-23"),
    semanas_corte_maturidade=12,
)


# ---------------------------------------------------------------------------
# Ciclo 2: variaveis, modelo e avaliacao
# ---------------------------------------------------------------------------

# Nomes das colunas da matriz de um horizonte (saida de
# `aedes.variaveis.montar_matriz_do_horizonte`, entrada de
# `aedes.corte_temporal`). Sao o contrato do gabarito
# `testes/referencia_antiga/matriz_hXX.csv`.
COLUNA_DATA_DE_ORIGEM = "data_origem"
COLUNA_DATA_ALVO = "data_alvo"
COLUNA_DO_ALVO = "y_h"


def _e_inteiro_de_verdade(valor: object) -> bool:
    """Diz se o valor e `int` e nao `bool` (em Python, `True` tambem e `int`)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def nome_da_variavel_defasada(nome_base: str, defasagem_em_semanas: int) -> str:
    """Monta o nome de uma variavel atrasada: `casos` e 2 viram `casos_lag2`.

    E a mesma regra do codigo antigo (`features.construir_features_temporais`,
    `modelagem_aedes/dominio/features.py:99`: f"{coluna_origem}_lag{numero_de_semanas}").

    Args:
        nome_base: Nome da variavel sem atraso.
        defasagem_em_semanas: Quantas semanas de atraso.

    Returns:
        O nome da variavel atrasada.
    """
    return f"{nome_base}_lag{defasagem_em_semanas}"


def _validar_defasagens(nome_do_campo: str, defasagens: tuple[int, ...]) -> None:
    """Exige defasagens inteiras, positivas e sem repeticao.

    Raises:
        ValueError: Se alguma defasagem nao for inteiro positivo ou se houver
            defasagem repetida.
    """
    for defasagem in defasagens:
        if not _e_inteiro_de_verdade(defasagem) or defasagem < 1:
            raise ValueError(
                f"{nome_do_campo} deve conter inteiros >= 1, recebido {defasagens!r}."
            )
    if len(set(defasagens)) != len(defasagens):
        raise ValueError(f"{nome_do_campo} tem defasagem repetida: {defasagens!r}.")


@dataclasses.dataclass(frozen=True)
class VariavelDeClima:
    """Uma coluna de clima do modelo: a coluna da tabela e quantas semanas ela e atrasada.

    Attributes:
        nome: Nome final da variavel na matriz (por exemplo `temp_media_lag4`).
        coluna_de_origem: Coluna da tabela de onde ela vem (`temp_media`).
        defasagem_em_semanas: Atraso aplicado a coluna de origem. Zero usa a
            coluna como esta (`umid_media`, `temp_max`).
    """

    nome: str
    coluna_de_origem: str
    defasagem_em_semanas: int

    def __post_init__(self) -> None:
        """Confere que o nome final e coerente com a origem e a defasagem.

        Raises:
            ValueError: Se a defasagem for negativa ou nao inteira, ou se o
                nome nao for a coluna de origem (defasagem 0) ou
                `<origem>_lag<k>` (defasagem k).
        """
        defasagem = self.defasagem_em_semanas
        if not _e_inteiro_de_verdade(defasagem) or defasagem < 0:
            raise ValueError(
                f"defasagem_em_semanas deve ser inteiro >= 0, recebido {defasagem!r}."
            )

        if defasagem == 0:
            nome_esperado = self.coluna_de_origem
        else:
            nome_esperado = nome_da_variavel_defasada(self.coluna_de_origem, defasagem)

        if self.nome != nome_esperado:
            raise ValueError(
                f"Nome {self.nome!r} incoerente com origem {self.coluna_de_origem!r} "
                f"e defasagem {defasagem}: esperado {nome_esperado!r}."
            )


@dataclasses.dataclass(frozen=True)
class ConfiguracaoVariaveis:
    """Como a matriz de variaveis do modelo e montada a partir da tabela cortada.

    As defasagens e as colunas de clima sao PARAMETROS desta configuracao. No
    codigo antigo as defasagens ficavam numa variavel de modulo
    (`features.LAGS_SEMANAS`) trocada em execucao pelo harness
    (`harness.py:162`); aqui duas configuracoes diferentes convivem no mesmo
    processo sem se afetar.

    Attributes:
        nome_da_variavel_de_casos: Nome da variavel de casos na matriz
            (`casos`); a coluna da tabela e `ConfiguracaoDados.coluna_de_casos`.
        coluna_do_vetor: Coluna da tabela com a captura de Aedes aegypti por
            armadilha; a variavel tem o mesmo nome.
        coluna_da_semana: Coluna da tabela com o numero da semana
            epidemiologica (1 a 53), base da sazonalidade.
        semanas_por_ano: Divisor da sazonalidade: sen/cos de 2*pi*semana/52.
            O 52 vem de `config/settings.py:85` do codigo antigo.
        defasagens_de_casos: Atrasos (em semanas) dos casos como variavel.
        defasagens_do_vetor: Atrasos (em semanas) do vetor como variavel.
        janela_da_media_movel: Semanas da media movel de casos e do vetor.
        prefixo_da_media_movel_do_vetor: Prefixo do nome da media movel do
            vetor (`vetor` gera `vetor_mm4`).
        variaveis_de_clima: As colunas de clima, na ordem do ranking de
            importancia do codigo antigo, CONGELADAS por nome. A escolha delas
            usou LightGBM sem semente, entao nao e recalculada aqui.
        nomes_da_sazonalidade_da_origem: Nomes do seno e cosseno da semana de origem.
        nomes_da_sazonalidade_do_alvo: Nomes do seno e cosseno da semana-alvo.
        nomes_das_variaveis: Nomes e ORDEM FINAL das variaveis que o modelo
            recebe (22). A ordem importa: treinar e prever exigem as mesmas
            colunas na mesma ordem.
    """

    nome_da_variavel_de_casos: str
    coluna_do_vetor: str
    coluna_da_semana: str
    semanas_por_ano: int
    defasagens_de_casos: tuple[int, ...]
    defasagens_do_vetor: tuple[int, ...]
    janela_da_media_movel: int
    prefixo_da_media_movel_do_vetor: str
    variaveis_de_clima: tuple[VariavelDeClima, ...]
    nomes_da_sazonalidade_da_origem: tuple[str, str]
    nomes_da_sazonalidade_do_alvo: tuple[str, str]
    nomes_das_variaveis: tuple[str, ...]

    def nome_da_media_movel_de_casos(self) -> str:
        """Nome da media movel dos casos (por exemplo `casos_mm4`)."""
        return f"{self.nome_da_variavel_de_casos}_mm{self.janela_da_media_movel}"

    def nome_da_media_movel_do_vetor(self) -> str:
        """Nome da media movel do vetor (por exemplo `vetor_mm4`)."""
        return f"{self.prefixo_da_media_movel_do_vetor}_mm{self.janela_da_media_movel}"

    def nomes_gerados_pela_receita(self) -> list[str]:
        """Todos os nomes que a receita desta configuracao gera, sem ordem relevante."""
        nomes: list[str] = [self.nome_da_variavel_de_casos]
        for defasagem in self.defasagens_de_casos:
            nomes.append(nome_da_variavel_defasada(self.nome_da_variavel_de_casos, defasagem))
        nomes.append(self.nome_da_media_movel_de_casos())
        nomes.extend(self.nomes_da_sazonalidade_da_origem)
        for variavel_de_clima in self.variaveis_de_clima:
            nomes.append(variavel_de_clima.nome)
        nomes.append(self.coluna_do_vetor)
        for defasagem in self.defasagens_do_vetor:
            nomes.append(nome_da_variavel_defasada(self.coluna_do_vetor, defasagem))
        nomes.append(self.nome_da_media_movel_do_vetor())
        nomes.extend(self.nomes_da_sazonalidade_do_alvo)
        return nomes

    def __post_init__(self) -> None:
        """Rejeita configuracao incoerente na criacao, antes de qualquer calculo.

        Raises:
            ValueError: Se as defasagens forem invalidas, se janela ou
                semanas por ano nao forem inteiros positivos, ou se
                `nomes_das_variaveis` tiver nome repetido ou nao coincidir com
                o conjunto de nomes que a receita gera (nome faltando ou
                sobrando).
        """
        _validar_defasagens("defasagens_de_casos", self.defasagens_de_casos)
        _validar_defasagens("defasagens_do_vetor", self.defasagens_do_vetor)

        janela_e_valida = _e_inteiro_de_verdade(self.janela_da_media_movel)
        if not janela_e_valida or self.janela_da_media_movel < 1:
            raise ValueError(
                "janela_da_media_movel deve ser inteiro >= 1, "
                f"recebido {self.janela_da_media_movel!r}."
            )

        semanas_por_ano_e_valido = _e_inteiro_de_verdade(self.semanas_por_ano)
        if not semanas_por_ano_e_valido or self.semanas_por_ano < 1:
            raise ValueError(
                f"semanas_por_ano deve ser inteiro >= 1, recebido {self.semanas_por_ano!r}."
            )

        nomes_repetidos = len(set(self.nomes_das_variaveis)) != len(self.nomes_das_variaveis)
        if nomes_repetidos:
            raise ValueError(f"nomes_das_variaveis tem nome repetido: {self.nomes_das_variaveis!r}.")

        nomes_gerados = self.nomes_gerados_pela_receita()
        if len(set(nomes_gerados)) != len(nomes_gerados):
            raise ValueError(f"A receita gera nome repetido: {nomes_gerados!r}.")

        faltam_na_lista = sorted(set(nomes_gerados) - set(self.nomes_das_variaveis))
        sobram_na_lista = sorted(set(self.nomes_das_variaveis) - set(nomes_gerados))
        if faltam_na_lista or sobram_na_lista:
            raise ValueError(
                "nomes_das_variaveis nao coincide com a receita: "
                f"faltam {faltam_na_lista}, sobram {sobram_na_lista}."
            )


CONFIGURACAO_VARIAVEIS = ConfiguracaoVariaveis(
    nome_da_variavel_de_casos="casos",
    coluna_do_vetor="aedes_aegypti_por_armadilha",
    coluna_da_semana="semana",
    semanas_por_ano=52,
    defasagens_de_casos=(1, 2, 3, 4),
    defasagens_do_vetor=(1, 2, 3, 4),
    janela_da_media_movel=4,
    prefixo_da_media_movel_do_vetor="vetor",
    # Ordem do ranking de ganho do codigo antigo; conferida contra
    # `testes/referencia_antiga/colunas_clima_congeladas.txt`.
    variaveis_de_clima=(
        VariavelDeClima("temp_media_lag4", "temp_media", 4),
        VariavelDeClima("umid_media", "umid_media", 0),
        VariavelDeClima("temp_media_lag3", "temp_media", 3),
        VariavelDeClima("temp_max", "temp_max", 0),
        VariavelDeClima("pressao_media_lag3", "pressao_media", 3),
        VariavelDeClima("pressao_media_lag4", "pressao_media", 4),
    ),
    nomes_da_sazonalidade_da_origem=("sem_sin", "sem_cos"),
    nomes_da_sazonalidade_do_alvo=("alvo_sin", "alvo_cos"),
    # Ordem do modelo: nucleo (8), clima (6), vetor (6) e, por ultimo, a
    # sazonalidade da semana-alvo. Conferida contra o cabecalho de
    # `testes/referencia_antiga/matriz_h01.csv`.
    nomes_das_variaveis=(
        "casos",
        "casos_lag1",
        "casos_lag2",
        "casos_lag3",
        "casos_lag4",
        "casos_mm4",
        "sem_sin",
        "sem_cos",
        "temp_media_lag4",
        "umid_media",
        "temp_media_lag3",
        "temp_max",
        "pressao_media_lag3",
        "pressao_media_lag4",
        "aedes_aegypti_por_armadilha",
        "aedes_aegypti_por_armadilha_lag1",
        "aedes_aegypti_por_armadilha_lag2",
        "aedes_aegypti_por_armadilha_lag3",
        "aedes_aegypti_por_armadilha_lag4",
        "vetor_mm4",
        "alvo_sin",
        "alvo_cos",
    ),
)


@dataclasses.dataclass(frozen=True)
class ConfiguracaoModelo:
    """Hiperparametros do HistGradientBoostingRegressor (scikit-learn 1.8.0).

    O codigo antigo passa so 7 parametros ao modelo
    (`modelagem_aedes/config/experimentos/cidade_referencia.py:72-84`; a folha
    20 em `analises/2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/rodar.py:30-42`).
    Todos os outros ficam no PADRAO do scikit-learn; aqui eles estao escritos
    por extenso (valores do padrao do scikit-learn 1.8.0) para que uma troca de
    versao do sklearn nao mude o modelo em silencio. Um teste compara esta
    configuracao com o padrao do sklearn instalado.

    Attributes:
        nome: Identificador do modelo nos resultados.
        perda: Funcao de perda (`quantile`: patamar que so e ultrapassado em
            `1 - quantil` das vezes; enviesado para cima de proposito).
        quantil: Quantil da perda quantilica.
        numero_de_iteracoes: Arvores do ensemble (`max_iter`).
        taxa_de_aprendizado: `learning_rate`.
        maximo_de_folhas: `max_leaf_nodes`.
        folha_minima: `min_samples_leaf`, o que separa FOLHA_5 de FOLHA_20.
        semente_aleatoria: `random_state`.
        parada_antecipada: `early_stopping`; "auto" so liga acima de 10.000
            amostras, e a matriz tem ~400 linhas, entao fica desligada.
        regularizacao_l2: `l2_regularization`.
        profundidade_maxima: `max_depth`; None = sem limite de profundidade.
        maximo_de_bins: `max_bins`.
        fracao_de_validacao: `validation_fraction` (so vale com parada antecipada).
        iteracoes_sem_melhora: `n_iter_no_change` (so vale com parada antecipada).
        tolerancia: `tol` (so vale com parada antecipada).
        metrica_da_parada: `scoring` (so vale com parada antecipada).
    """

    nome: str
    perda: str
    quantil: float
    numero_de_iteracoes: int
    taxa_de_aprendizado: float
    maximo_de_folhas: int
    folha_minima: int
    semente_aleatoria: int
    parada_antecipada: str | bool
    regularizacao_l2: float
    profundidade_maxima: int | None
    maximo_de_bins: int
    fracao_de_validacao: float
    iteracoes_sem_melhora: int
    tolerancia: float
    metrica_da_parada: str

    def __post_init__(self) -> None:
        """Rejeita hiperparametro impossivel na criacao.

        Raises:
            ValueError: Se o quantil nao estiver em (0, 1), ou se iteracoes,
                folhas, folha minima ou bins nao forem inteiros positivos
                (folhas >= 2), ou se a taxa de aprendizado nao for positiva.
        """
        if not 0.0 < self.quantil < 1.0:
            raise ValueError(f"quantil deve estar em (0, 1), recebido {self.quantil!r}.")
        if self.taxa_de_aprendizado <= 0.0:
            raise ValueError(
                f"taxa_de_aprendizado deve ser > 0, recebido {self.taxa_de_aprendizado!r}."
            )
        if not _e_inteiro_de_verdade(self.numero_de_iteracoes) or self.numero_de_iteracoes < 1:
            raise ValueError(
                f"numero_de_iteracoes deve ser inteiro >= 1, recebido {self.numero_de_iteracoes!r}."
            )
        if not _e_inteiro_de_verdade(self.maximo_de_folhas) or self.maximo_de_folhas < 2:
            raise ValueError(
                f"maximo_de_folhas deve ser inteiro >= 2, recebido {self.maximo_de_folhas!r}."
            )
        if not _e_inteiro_de_verdade(self.folha_minima) or self.folha_minima < 1:
            raise ValueError(
                f"folha_minima deve ser inteiro >= 1, recebido {self.folha_minima!r}."
            )
        if not _e_inteiro_de_verdade(self.maximo_de_bins) or self.maximo_de_bins < 2:
            raise ValueError(
                f"maximo_de_bins deve ser inteiro >= 2, recebido {self.maximo_de_bins!r}."
            )

    def parametros_do_sklearn(self) -> dict[str, object]:
        """Traduz a configuracao para os argumentos de `HistGradientBoostingRegressor(**...)`.

        Returns:
            Um dicionario NOVO a cada chamada, com os 15 parametros que
            definem o modelo (os 7 do codigo antigo e os 8 do padrao do sklearn).
        """
        return {
            "loss": self.perda,
            "quantile": self.quantil,
            "max_iter": self.numero_de_iteracoes,
            "learning_rate": self.taxa_de_aprendizado,
            "max_leaf_nodes": self.maximo_de_folhas,
            "min_samples_leaf": self.folha_minima,
            "random_state": self.semente_aleatoria,
            "early_stopping": self.parada_antecipada,
            "l2_regularization": self.regularizacao_l2,
            "max_depth": self.profundidade_maxima,
            "max_bins": self.maximo_de_bins,
            "validation_fraction": self.fracao_de_validacao,
            "n_iter_no_change": self.iteracoes_sem_melhora,
            "tol": self.tolerancia,
            "scoring": self.metrica_da_parada,
        }


FOLHA_5 = ConfiguracaoModelo(
    nome="histgb_folha5",
    perda="quantile",
    quantil=0.85,
    numero_de_iteracoes=250,
    taxa_de_aprendizado=0.05,
    maximo_de_folhas=15,
    folha_minima=5,
    semente_aleatoria=42,
    parada_antecipada="auto",
    regularizacao_l2=0.0,
    profundidade_maxima=None,
    maximo_de_bins=255,
    fracao_de_validacao=0.1,
    iteracoes_sem_melhora=10,
    tolerancia=1e-07,
    metrica_da_parada="loss",
)

# Unica diferenca para a FOLHA_5: `min_samples_leaf` 20 em vez de 5.
FOLHA_20 = dataclasses.replace(FOLHA_5, nome="histgb_folha20", folha_minima=20)


@dataclasses.dataclass(frozen=True)
class ConfiguracaoAvaliacao:
    """Horizontes, treino minimo, passo do walk-forward e janela de avaliacao.

    Attributes:
        horizontes: Semanas a frente que o modelo preve, um modelo por horizonte.
        treino_minimo_em_semanas: Quantas linhas validas (semanas com todas as
            variaveis e o alvo) a matriz tem antes da primeira origem de teste.
        passo_do_retreino_em_semanas: De quantas em quantas origens o walk-forward
            avanca (1 = retreina toda semana).
        fim_da_calibracao: Ultimo dia da calibracao; a escolha da configuracao
            aconteceu ate aqui.
        primeira_data_alvo_avaliada: Primeiro domingo-alvo que julga o resultado.
        ultima_data_alvo_avaliada: Ultimo domingo-alvo avaliado; e a ultima
            semana com caso depois do corte de maturidade.
    """

    horizontes: tuple[int, ...]
    treino_minimo_em_semanas: int
    passo_do_retreino_em_semanas: int
    fim_da_calibracao: pd.Timestamp
    primeira_data_alvo_avaliada: pd.Timestamp
    ultima_data_alvo_avaliada: pd.Timestamp

    def __post_init__(self) -> None:
        """Rejeita avaliacao incoerente na criacao.

        Raises:
            ValueError: Se os horizontes nao forem inteiros >= 1 sem repeticao
                e em ordem crescente, se treino minimo ou passo nao forem
                inteiros >= 1, ou se as datas nao seguirem a ordem
                fim da calibracao < primeira avaliada <= ultima avaliada.
        """
        if len(self.horizontes) == 0:
            raise ValueError("horizontes nao pode ser vazio.")
        for horizonte in self.horizontes:
            if not _e_inteiro_de_verdade(horizonte) or horizonte < 1:
                raise ValueError(f"horizontes deve conter inteiros >= 1, recebido {self.horizontes!r}.")
        horizontes_ordenados = tuple(sorted(set(self.horizontes)))
        if horizontes_ordenados != self.horizontes:
            raise ValueError(
                f"horizontes deve estar em ordem crescente e sem repeticao, recebido {self.horizontes!r}."
            )

        treino_e_valido = _e_inteiro_de_verdade(self.treino_minimo_em_semanas)
        if not treino_e_valido or self.treino_minimo_em_semanas < 1:
            raise ValueError(
                "treino_minimo_em_semanas deve ser inteiro >= 1, "
                f"recebido {self.treino_minimo_em_semanas!r}."
            )
        passo_e_valido = _e_inteiro_de_verdade(self.passo_do_retreino_em_semanas)
        if not passo_e_valido or self.passo_do_retreino_em_semanas < 1:
            raise ValueError(
                "passo_do_retreino_em_semanas deve ser inteiro >= 1, "
                f"recebido {self.passo_do_retreino_em_semanas!r}."
            )

        calibracao_antes_da_avaliacao = self.fim_da_calibracao < self.primeira_data_alvo_avaliada
        janela_nao_invertida = self.primeira_data_alvo_avaliada <= self.ultima_data_alvo_avaliada
        if not (calibracao_antes_da_avaliacao and janela_nao_invertida):
            raise ValueError(
                "Datas fora de ordem: esperado fim_da_calibracao < primeira_data_alvo_avaliada "
                f"<= ultima_data_alvo_avaliada, recebido {self.fim_da_calibracao.date()}, "
                f"{self.primeira_data_alvo_avaliada.date()}, {self.ultima_data_alvo_avaliada.date()}."
            )


CONFIGURACAO_AVALIACAO = ConfiguracaoAvaliacao(
    horizontes=tuple(range(1, 13)),
    treino_minimo_em_semanas=104,
    passo_do_retreino_em_semanas=1,
    fim_da_calibracao=pd.Timestamp("2023-12-31"),
    primeira_data_alvo_avaliada=pd.Timestamp("2024-01-07"),
    ultima_data_alvo_avaliada=pd.Timestamp("2026-02-01"),
)
