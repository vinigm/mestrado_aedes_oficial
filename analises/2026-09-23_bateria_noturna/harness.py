"""Motor compartilhado da bateria noturna de 23/09/2026.

Os cinco testes da noite variam coisas diferentes — corte de maturidade,
conjunto de features, janela de lag por grupo, algoritmo — mas todos fazem a
mesma coisa depois: rodam o walk-forward da configuracao de referencia e
comparam os bracos de forma pareada.

Um motor unico e parametrizado, em vez de cinco scripts parecidos, existe por
um motivo pratico: cinco copias do mesmo walk-forward dariam cinco
oportunidades de um erro sutil entrar em uma delas e passar despercebido a
noite inteira.

⚠️ NAO altera nada do pipeline. So le.
"""

import dataclasses
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, r2_score

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DO_PIPELINE = PASTA_DESTE_ARQUIVO.parent.parent / "modelagem_aedes"
if str(PASTA_DO_PIPELINE) not in sys.path:
    sys.path.insert(0, str(PASTA_DO_PIPELINE))

from acesso import fontes  # noqa: E402  (depende do sys.path ajustado acima)
from config.experimentos.cidade_referencia import CIDADE_REFERENCIA  # noqa: E402
from config.modelo import EspecificacaoModelo  # noqa: E402
from dominio import features, selecao_features, surto  # noqa: E402
from dominio.features import construir_alvo_horizonte  # noqa: E402
from motor import corte_temporal  # noqa: E402

# Onde comeca o periodo que julga o resultado. A escolha da configuracao
# aconteceu na calibracao, que termina antes disso.
INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")

NIVEL_DE_SIGNIFICANCIA = 0.05

# Os oito numeros que o braco de referencia tem de reproduzir para o teste
# valer. Vem do painel publico e foram conferidos em 23/09/2026 recalculando
# do CSV bruto da correcao de vazamento.
PAINEL_PUBLICADO = {
    1: {"mae": 98.0, "r2": 0.898},
    4: {"mae": 219.7, "r2": 0.628},
    8: {"mae": 272.6, "r2": 0.450},
    12: {"mae": 278.7, "r2": 0.437},
}
TOLERANCIA_DE_MAE = 0.2
TOLERANCIA_DE_R2 = 0.003


@dataclasses.dataclass(frozen=True)
class Braco:
    """Uma variante a medir contra a referencia.

    Cada campo que vier vazio usa o valor da configuracao de referencia. Um
    braco que nao preenche nada É a referencia.

    Attributes:
        nome: Identificador nas saidas.
        semanas_corte_maturidade: Quantas semanas finais tem os casos apagados
            do treino, porque a contagem ainda nao fechou.
        lags_em_semanas: Defasagens aplicadas a todas as colunas elegiveis.
        colunas_extras: Colunas ja presentes na tabela que entram no modelo
            alem das escolhidas pelo procedimento normal.
        modelo: Algoritmo e hiperparametros. Vazio usa o da referencia.
        sem_vetor: Quando True, as colunas do vetor ficam de fora. E o M0 do
            projeto, usado para medir quanto o vetor vale.
        descricao: Uma linha dizendo o que este braco investiga.
    """

    nome: str
    semanas_corte_maturidade: int | None = None
    lags_em_semanas: list[int] | None = None
    colunas_extras: tuple[str, ...] = ()
    modelo: EspecificacaoModelo | None = None
    sem_vetor: bool = False
    descricao: str = ""

    def corte_efetivo(self) -> int:
        """O corte de maturidade deste braco, caindo na referencia se vazio."""
        if self.semanas_corte_maturidade is None:
            return CIDADE_REFERENCIA.semanas_corte_maturidade

        return self.semanas_corte_maturidade

    def lags_efetivos(self) -> list[int]:
        """As defasagens deste braco, caindo na referencia se vazio."""
        if self.lags_em_semanas is None:
            return [1, 2, 3, 4]

        return self.lags_em_semanas

    def modelo_efetivo(self) -> EspecificacaoModelo:
        """O algoritmo deste braco, caindo no da referencia se vazio."""
        if self.modelo is None:
            return CIDADE_REFERENCIA.modelo

        return self.modelo


@dataclasses.dataclass(frozen=True)
class ComparacaoPareada:
    """Resultado de comparar uma variante com a referencia num horizonte."""

    braco: str
    horizonte: int
    mae_referencia: float
    mae_variante: float
    r2_referencia: float
    r2_variante: float
    semanas_pareadas: int
    p_bruto: float

    def reducao_percentual(self) -> float:
        """Quanto a variante reduziu o MAE. Negativo significa que piorou."""
        return 100.0 * (self.mae_referencia - self.mae_variante) / self.mae_referencia


def carregar_tabela_bruta() -> pd.DataFrame:
    """Le a tabela semanal antes de qualquer corte ou feature."""
    return fontes.carregar_tabela_final()


def montar_features_do_braco(
    tabela_bruta: pd.DataFrame,
    braco: Braco,
    construir_extras=None,
    colunas_reservadas: tuple[str, ...] = (),
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Aplica corte de maturidade, cria features e escolhe o clima do braco.

    ⚠️ A lista de defasagens vive numa constante de modulo que
    `construir_features_temporais` le por dentro, entao ela e trocada aqui
    antes da chamada. Duplicar a construcao de features criaria uma segunda
    implementacao que envelheceria em silencio quando o pipeline mudasse.

    Args:
        tabela_bruta: A tabela semanal sem corte nem features.
        braco: A variante a montar.
        construir_extras: Funcao opcional que recebe a tabela ja com features
            e devolve a tabela acrescida das colunas extras do teste. Usada
            pelo bloco de features longas.
        colunas_reservadas: Colunas que NUNCA entram na separacao automatica
            em grupos, em nenhum braco. So entram no modelo quando o braco as
            pede em `colunas_extras`.

            ⚠️ Existe porque `construir_extras` roda em TODOS os bracos. Sem
            esta reserva, no braco de referencia as colunas de anomalia e de
            acumulo cairiam no grupo de clima pelo nome e disputariam as seis
            vagas — e a referencia deixaria de ser a referencia.

    Returns:
        A tabela pronta, as colunas que vao ao modelo e o clima escolhido.
    """
    tabela = surto.aplicar_corte_maturidade(tabela_bruta, braco.corte_efetivo())

    features.LAGS_SEMANAS = braco.lags_efetivos()
    tabela = features.construir_features_temporais(tabela)

    if construir_extras is not None:
        tabela = construir_extras(tabela)

    colunas_nucleo, colunas_clima, colunas_vetor = (
        selecao_features.separar_grupos_de_features(
            tabela,
            CIDADE_REFERENCIA.colunas_ignorar,
            CIDADE_REFERENCIA.padroes_vetor,
            CIDADE_REFERENCIA.padroes_clima,
        )
    )

    # As colunas reservadas e as extras do braco nao disputam vaga de clima
    # nem entram em grupo nenhum: elas entram por fora, e so onde pedidas,
    # para o braco isolar o efeito delas.
    fora_dos_grupos = set(colunas_reservadas) | set(braco.colunas_extras)
    colunas_clima = [c for c in colunas_clima if c not in fora_dos_grupos]
    colunas_nucleo = [c for c in colunas_nucleo if c not in fora_dos_grupos]
    colunas_vetor = [c for c in colunas_vetor if c not in fora_dos_grupos]

    ranking_de_clima = selecao_features.selecionar_clima_por_ganho(
        tabela,
        colunas_nucleo,
        colunas_clima,
        CIDADE_REFERENCIA.coluna_alvo,
        CIDADE_REFERENCIA.horizontes_selecao_clima,
        CIDADE_REFERENCIA.modelo_selecao_clima,
        CIDADE_REFERENCIA.fracao_treino_selecao,
    )
    clima_escolhido = (
        ranking_de_clima.head(CIDADE_REFERENCIA.valores_k[0]).index.tolist()
    )

    # O M0 tira o vetor inteiro, inclusive colunas extras que sejam de vetor.
    # A selecao de clima acima NAO muda: ela nunca olha o vetor, entao os dois
    # bracos de um mesmo algoritmo recebem exatamente o mesmo clima.
    if braco.sem_vetor:
        colunas_vetor = []

    colunas_do_modelo = (
        colunas_nucleo + clima_escolhido + colunas_vetor + list(braco.colunas_extras)
    )

    return tabela, colunas_do_modelo, clima_escolhido


def rodar_walk_forward(
    tabela: pd.DataFrame,
    colunas_do_modelo: list[str],
    horizonte: int,
    especificacao_modelo: EspecificacaoModelo,
) -> pd.DataFrame:
    """Roda o walk-forward de um horizonte, guardando a data de cada previsao.

    Espelha `motor.walk_forward_regressao.executar_walk_forward_regressao`,
    incluindo o corte de treino pela data da RESPOSTA. A diferenca e devolver
    a `data_alvo`: sem ela nao da para parear a comparacao entre bracos, e
    comparacao nao pareada nao vale pela regra do projeto.

    Args:
        tabela: A tabela com as features do braco.
        colunas_do_modelo: Entradas do modelo, sem a sazonalidade do alvo.
        horizonte: Quantas semanas a frente prever.
        especificacao_modelo: Qual algoritmo treinar.

    Returns:
        Uma linha por semana avaliada, com h, data_alvo, real e previsto.
    """
    dados_do_horizonte = construir_alvo_horizonte(
        tabela, CIDADE_REFERENCIA.coluna_alvo, horizonte
    )
    features_com_sazonalidade = colunas_do_modelo + ["alvo_sin", "alvo_cos"]

    dados_validos = (
        dados_do_horizonte.dropna(subset=features_com_sazonalidade + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    linhas = []
    for indice_do_corte in range(
        CIDADE_REFERENCIA.minimo_semanas_treino,
        len(dados_validos),
        CIDADE_REFERENCIA.passo,
    ):
        teste = dados_validos.iloc[indice_do_corte : indice_do_corte + 1]
        data_do_teste = teste["data"].to_numpy()[0]

        treino = corte_temporal.selecionar_treino_ja_respondido(
            dados_validos, data_do_teste, horizonte
        )

        modelo = especificacao_modelo.criar()
        modelo.fit(treino[features_com_sazonalidade], treino["y_h"])
        previsao = float(modelo.predict(teste[features_com_sazonalidade])[0])

        linhas.append(
            {
                "h": horizonte,
                "data_alvo": pd.Timestamp(data_do_teste)
                + pd.Timedelta(weeks=horizonte),
                "real": float(teste["y_h"].to_numpy()[0]),
                "previsto": previsao,
            }
        )

    return pd.DataFrame(linhas)


def conferir_trava_de_validacao(previsoes: pd.DataFrame, nome_do_braco: str) -> bool:
    """Diz se o braco de referencia reproduziu os numeros ja publicados.

    Serve de prova de que o arranjo do teste esta correto ANTES de qualquer
    resultado novo ser lido. Um braco de referencia que nao reproduz o painel
    significa que algo no arranjo mudou sem querer.

    ⚠️ So vale para bracos que rodam a configuracao de referencia intacta.
    Um braco que muda o corte de maturidade, por exemplo, tem outro conjunto
    de semanas e nao tem por que reproduzir o painel.

    Args:
        previsoes: As previsoes de todos os bracos.
        nome_do_braco: Qual deles e a referencia.

    Returns:
        True se os oito numeros baterem dentro da tolerancia.
    """
    avaliacao = previsoes[
        (previsoes["data_alvo"] >= INICIO_DA_AVALIACAO)
        & (previsoes["braco"] == nome_do_braco)
    ]

    print(f"\n  TRAVA DE VALIDACAO — {nome_do_braco} contra o painel publicado")
    tudo_bate = True
    for horizonte, esperado in PAINEL_PUBLICADO.items():
        celula = avaliacao[avaliacao["h"] == horizonte]
        if celula.empty:
            print(f"    h={horizonte:2d}  SEM DADOS")
            tudo_bate = False
            continue

        mae = mean_absolute_error(celula["real"], celula["previsto"])
        r2 = r2_score(celula["real"], celula["previsto"])
        bate = (
            abs(mae - esperado["mae"]) < TOLERANCIA_DE_MAE
            and abs(r2 - esperado["r2"]) < TOLERANCIA_DE_R2
        )
        tudo_bate = tudo_bate and bate
        marca = "ok" if bate else "<<< DIVERGE"
        print(
            f"    h={horizonte:2d}  MAE {mae:7.1f} (painel {esperado['mae']:6.1f})  "
            f"R2 {r2:6.3f} (painel {esperado['r2']:5.3f})  {marca}"
        )

    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}")
    return tudo_bate


def comparar_pareado(
    previsoes: pd.DataFrame, braco_referencia: str, braco_variante: str, horizonte: int
) -> ComparacaoPareada:
    """Compara uma variante com a referencia semana a semana.

    O pareamento e por `data_alvo`: so entram as semanas que os dois bracos
    previram. Bracos com janela de lag maior ou corte de maturidade diferente
    perdem semanas, entao os conjuntos nao sao identicos e a intersecao e o
    que torna a comparacao honesta.

    Args:
        previsoes: Todas as previsoes, de todos os bracos.
        braco_referencia: O braco de controle.
        braco_variante: A variante a comparar.
        horizonte: O horizonte a comparar.

    Returns:
        O resultado da comparacao naquele horizonte.

    Raises:
        ValueError: Se nao sobrar nenhuma semana em comum.
    """
    do_horizonte = previsoes[previsoes["h"] == horizonte]
    da_referencia = do_horizonte[do_horizonte["braco"] == braco_referencia]
    da_variante = do_horizonte[do_horizonte["braco"] == braco_variante]

    pareado = da_referencia.merge(
        da_variante, on="data_alvo", suffixes=("_ref", "_var")
    )
    if pareado.empty:
        raise ValueError(
            f"Nenhuma semana em comum entre {braco_referencia} e "
            f"{braco_variante} em h={horizonte}."
        )

    erro_da_referencia = np.abs(pareado["real_ref"] - pareado["previsto_ref"])
    erro_da_variante = np.abs(pareado["real_var"] - pareado["previsto_var"])

    if np.allclose(erro_da_referencia, erro_da_variante):
        p_bruto = 1.0
    else:
        _, p_bruto = stats.wilcoxon(erro_da_referencia, erro_da_variante)

    return ComparacaoPareada(
        braco=braco_variante,
        horizonte=horizonte,
        mae_referencia=mean_absolute_error(
            pareado["real_ref"], pareado["previsto_ref"]
        ),
        mae_variante=mean_absolute_error(pareado["real_var"], pareado["previsto_var"]),
        r2_referencia=r2_score(pareado["real_ref"], pareado["previsto_ref"]),
        r2_variante=r2_score(pareado["real_var"], pareado["previsto_var"]),
        semanas_pareadas=len(pareado),
        p_bruto=float(p_bruto),
    )


def _p_bruto_da_comparacao(comparacao: ComparacaoPareada) -> float:
    """Chave de ordenacao do Holm: o p antes da correcao."""
    return comparacao.p_bruto


def _achar_comparacao(
    comparacoes: list[ComparacaoPareada], braco: str, horizonte: int
) -> ComparacaoPareada:
    """Devolve a comparacao de um braco num horizonte.

    Raises:
        KeyError: Se a combinacao nao estiver na familia.
    """
    for comparacao in comparacoes:
        mesmo_braco = comparacao.braco == braco
        mesmo_horizonte = comparacao.horizonte == horizonte
        if mesmo_braco and mesmo_horizonte:
            return comparacao

    raise KeyError(f"Sem comparacao para {braco} em h={horizonte}.")


def corrigir_por_holm(comparacoes: list[ComparacaoPareada]) -> dict[str, float]:
    """Aplica a correcao de Holm sobre a familia inteira de comparacoes.

    Holm ordena os p do menor para o maior e exige que o i-esimo sobreviva a
    um limiar que vai afrouxando. E mais poderoso que Bonferroni e continua
    controlando a chance de um falso positivo em qualquer ponto da familia.

    Args:
        comparacoes: Todas as comparacoes da familia, sem excecao. Deixar uma
            de fora inflaria a significancia das que ficaram.

    Returns:
        O p corrigido de cada comparacao, indexado por "braco:horizonte".
    """
    ordenadas = sorted(comparacoes, key=_p_bruto_da_comparacao)
    quantidade = len(ordenadas)

    p_corrigidos: dict[str, float] = {}
    maior_p_ate_agora = 0.0

    for posicao, comparacao in enumerate(ordenadas):
        p_ajustado = min(1.0, comparacao.p_bruto * (quantidade - posicao))
        maior_p_ate_agora = max(maior_p_ate_agora, p_ajustado)
        p_corrigidos[f"{comparacao.braco}:{comparacao.horizonte}"] = maior_p_ate_agora

    return p_corrigidos


def executar_bateria(
    bracos: tuple[Braco, ...],
    pasta_de_saidas: pathlib.Path,
    construir_extras=None,
    colunas_reservadas: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Roda todos os bracos e grava uma previsao por linha.

    Args:
        bracos: As variantes a medir. A primeira e tratada como referencia.
        pasta_de_saidas: Onde gravar os CSVs.
        construir_extras: Funcao opcional de colunas extras, repassada ao
            montador de features.
        colunas_reservadas: Colunas fora da separacao automatica em todos os
            bracos. Ver `montar_features_do_braco`.

    Returns:
        Todas as previsoes, de todos os bracos, num DataFrame so.
    """
    import time

    pasta_de_saidas.mkdir(parents=True, exist_ok=True)
    tabela_bruta = carregar_tabela_bruta()

    previsoes_de_todos = []
    resumo_dos_bracos = []

    for braco in bracos:
        inicio = time.perf_counter()
        tabela, colunas, clima = montar_features_do_braco(
            tabela_bruta, braco, construir_extras, colunas_reservadas
        )
        modelo = braco.modelo_efetivo()

        print(
            f"\n[{braco.nome}] {braco.descricao}\n"
            f"  corte {braco.corte_efetivo()} sem · lags {braco.lags_efetivos()} · "
            f"{len(colunas)} features · {modelo.nome}",
            flush=True,
        )

        for horizonte in CIDADE_REFERENCIA.horizontes:
            marca = time.perf_counter()
            previsoes = rodar_walk_forward(tabela, colunas, horizonte, modelo)
            previsoes["braco"] = braco.nome
            previsoes_de_todos.append(previsoes)
            print(
                f"  h={horizonte:2d}  {len(previsoes):3d} sem  "
                f"{time.perf_counter() - marca:5.1f}s",
                flush=True,
            )

        resumo_dos_bracos.append(
            {
                "braco": braco.nome,
                "descricao": braco.descricao,
                "corte_maturidade": braco.corte_efetivo(),
                "lags": str(braco.lags_efetivos()),
                "modelo": modelo.nome,
                "n_features": len(colunas),
                "clima_escolhido": " | ".join(clima),
                "colunas_extras": " | ".join(braco.colunas_extras),
                "sem_vetor": braco.sem_vetor,
            }
        )
        print(
            f"[{braco.nome}] {(time.perf_counter() - inicio) / 60:.1f} min", flush=True
        )

    todas = pd.concat(previsoes_de_todos, ignore_index=True)
    todas.to_csv(pasta_de_saidas / "previsoes_por_braco.csv", index=False)
    pd.DataFrame(resumo_dos_bracos).to_csv(
        pasta_de_saidas / "resumo_dos_bracos.csv", index=False
    )
    return todas


def relatar_comparacoes(
    previsoes: pd.DataFrame,
    braco_referencia: str,
    horizontes_da_familia: tuple[int, ...],
    horizontes_de_decisao: tuple[int, ...],
    pasta_de_saidas: pathlib.Path,
) -> pd.DataFrame:
    """Imprime e grava a tabela de comparacoes com Holm aplicado.

    Args:
        previsoes: Todas as previsoes.
        braco_referencia: O braco de controle.
        horizontes_da_familia: Todos os horizontes que entram na correcao.
        horizontes_de_decisao: Onde o criterio pre-declarado decide.
        pasta_de_saidas: Onde gravar o CSV do resultado.

    Returns:
        A tabela de comparacoes, com o p de Holm por linha.
    """
    avaliacao = previsoes[previsoes["data_alvo"] >= INICIO_DA_AVALIACAO]
    variantes = [
        nome for nome in avaliacao["braco"].unique() if nome != braco_referencia
    ]

    comparacoes = []
    for braco in sorted(variantes):
        for horizonte in horizontes_da_familia:
            comparacoes.append(
                comparar_pareado(avaliacao, braco_referencia, braco, horizonte)
            )

    p_corrigidos = corrigir_por_holm(comparacoes)

    print(
        f"\n  familia: {len(comparacoes)} comparacoes, Holm · "
        f"avaliacao a partir de {INICIO_DA_AVALIACAO.date()}"
    )
    print(
        f"  {'braco':>22} {'h':>3} {'MAE ref':>9} {'MAE var':>9} {'red':>8} "
        f"{'R2 var':>8} {'p Holm':>8} {'n':>4}"
    )
    linhas = []
    for comparacao in comparacoes:
        p_holm = p_corrigidos[f"{comparacao.braco}:{comparacao.horizonte}"]
        marca = "*" if p_holm < NIVEL_DE_SIGNIFICANCIA else " "
        print(
            f"  {comparacao.braco:>22} {comparacao.horizonte:3d} "
            f"{comparacao.mae_referencia:9.1f} {comparacao.mae_variante:9.1f} "
            f"{comparacao.reducao_percentual():7.2f}% {comparacao.r2_variante:8.3f} "
            f"{p_holm:8.4f}{marca} {comparacao.semanas_pareadas:4d}"
        )
        linhas.append(
            {
                "braco": comparacao.braco,
                "h": comparacao.horizonte,
                "mae_referencia": comparacao.mae_referencia,
                "mae_variante": comparacao.mae_variante,
                "reducao_percentual": comparacao.reducao_percentual(),
                "r2_referencia": comparacao.r2_referencia,
                "r2_variante": comparacao.r2_variante,
                "p_bruto": comparacao.p_bruto,
                "p_holm": p_holm,
                "semanas_pareadas": comparacao.semanas_pareadas,
            }
        )

    tabela = pd.DataFrame(linhas)
    tabela.to_csv(pasta_de_saidas / "comparacoes.csv", index=False)

    print("\n  VEREDITO pelo criterio pre-declarado:")
    for braco in sorted(variantes):
        aprovado = True
        for horizonte in horizontes_de_decisao:
            do_braco = _achar_comparacao(comparacoes, braco, horizonte)
            p_holm = p_corrigidos[f"{braco}:{horizonte}"]
            reduziu = do_braco.mae_variante < do_braco.mae_referencia
            aprovado = aprovado and reduziu and p_holm < NIVEL_DE_SIGNIFICANCIA

        print(f"    {braco:>22}: {'ENTRA' if aprovado else 'NAO entra'}")

    return tabela
