"""Ablacao NO COMPOSTO (EXPLORATORIA, nao pre-declarada; nada daqui vai ao artigo). Nenhum modelo e treinado.

Pergunta: o que cada fonte b (casos, clima, vetor) acrescenta ao proprio composto de defesa (E3, N = 13)?
Para cada b, monta o "composto sem b" aplicando a MESMA regra do composto (`aedes.composto.montar_composto`,
N = 13) ao par `sem_b@f5` x `sem_b@f20` das previsoes da E2, e compara com o composto completo
(`completo@f5` x `completo@f20`) em h = 1, 4, 8 e 12, pareado por `data_alvo`, na janela de avaliacao.

Ancoras obrigatorias (o script PARA, codigo de saida 1, se alguma falhar):
    1. O composto completo remontado aqui reproduz EXATAMENTE `E3_composto/previsoes.csv` (N == 13):
       mesmas linhas, mesmas previsoes e mesma folha escolhida (diferenca zero).
    2. O MAE na janela desse composto bate com `E3_composto/resumo.csv` (N == 13), nos 12 horizontes.

A estatistica e a do pacote: DM-HLN, IC 95% por bootstrap de blocos (8 semanas, 2.000, semente 42), Holm
(uma unica familia de 12 testes) e a regra pre-declarada de veredito (Holm < 0,05 e |delta| > 2 x piso, onde o
piso e o MAIOR entre as duas folhas no horizonte, Emenda 1). Tudo via `aedes.familias.executar_familias`.

Convencao: A = composto completo, B = composto sem b; `delta = MAE(sem b) - MAE(completo)`; positivo = tirar b
piora o composto (b contribui). `ganho_pct = delta / MAE(sem b) * 100`, como na familia F1.

Grava em `resultados/ciencia/ablacao_no_composto/`: `ablacao_no_composto.csv` (precisao total) e o log.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B experimentos/ablacao_no_composto.py
"""

import pathlib
import sys

PASTA_DO_PROJETO_FINAL = pathlib.Path(__file__).resolve().parents[1]
if str(PASTA_DO_PROJETO_FINAL) not in sys.path:
    sys.path.insert(0, str(PASTA_DO_PROJETO_FINAL))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from aedes.composto import NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA, montar_composto  # noqa: E402
from aedes.configuracao import (  # noqa: E402
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
)
from aedes.familias import (  # noqa: E402
    FOLHA_PRIMARIA,
    FOLHA_SECUNDARIA,
    FONTES_TESTADAS,
    HORIZONTES_TESTADOS,
    DefinicaoDoTeste,
    executar_familias,
)
from aedes.metricas import (  # noqa: E402
    COLUNA_DO_BRACO,
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_PREVISTO,
    COLUNA_DO_REAL,
    erro_absoluto_medio,
    recortar_janela_de_avaliacao,
)
from experimentos.comum_ciencia import PASTA_DA_CIENCIA, RegistradorDeLog  # noqa: E402
from experimentos.e3_composto import (  # noqa: E402
    CAMINHO_DAS_PREVISOES as CAMINHO_DAS_PREVISOES_DA_E3,
    CAMINHO_DO_RESUMO as CAMINHO_DO_RESUMO_DA_E3,
    COLUNA_DA_FOLHA,
    COLUNA_DA_JANELA_N,
    JANELA_PRIMARIA,
    exigir_travas_da_e2_aprovadas,
    ler_previsoes_da_e2,
)

PASTA_DE_SAIDA = PASTA_DA_CIENCIA / "ablacao_no_composto"
CAMINHO_DO_CSV = PASTA_DE_SAIDA / "ablacao_no_composto.csv"
CAMINHO_DO_PISO = PASTA_DA_CIENCIA / "piso_de_ruido" / "piso.csv"
CAMINHO_DAS_FAMILIAS = PASTA_DA_CIENCIA / "estatistica" / "familias.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "ablacao_no_composto.log")

BRACO_COMPLETO = "completo"
FAMILIA_DA_ABLACAO_NO_COMPOSTO = "AC"
NOME_DO_COMPOSTO_COMPLETO = "composto_completo"
SEMANAS_ESPERADAS_NA_JANELA = 102
TOLERANCIA_DO_MAE_DA_ANCORA_2 = 1e-9

COLUNAS_DO_CSV = (
    "fonte",
    "h",
    "n",
    "mae_completo",
    "mae_sem_b",
    "delta",
    "ganho_pct",
    "ic_inf",
    "ic_sup",
    "dm_hln",
    "p_bruto",
    "p_holm",
    "limiar_piso",
    "variancia_fallback",
    "veredito",
    "frac_folha20_completo",
    "frac_folha20_sem_b",
    "frac_troca_de_folha",
    "delta_F1_folha5",
    "ganho_pct_F1_folha5",
    "veredito_F1_folha5",
    "delta_F3_folha20",
    "ganho_pct_F3_folha20",
    "veredito_F3_folha20",
)


def selecionar_braco_da_folha(previsoes_da_e2: pd.DataFrame, braco: str, folha: int, horizonte: int) -> pd.DataFrame:
    """Linhas de um braco da E2 numa folha e num horizonte (`data_alvo`, `real`, `previsto`, etc.)."""
    e_do_braco = previsoes_da_e2[COLUNA_DO_BRACO] == braco
    e_da_folha = previsoes_da_e2[COLUNA_DA_FOLHA] == folha
    e_do_horizonte = previsoes_da_e2[COLUNA_DO_HORIZONTE] == horizonte
    return previsoes_da_e2.loc[e_do_braco & e_da_folha & e_do_horizonte]


def montar_composto_do_braco(previsoes_da_e2: pd.DataFrame, braco: str, horizonte: int) -> pd.DataFrame:
    """Composto (regra de `aedes.composto`, N = 13) do par `braco@f5` x `braco@f20` em um horizonte.

    Usa todas as origens da E2 (nao so a janela de avaliacao), como a E3: o historico recente da regra
    precisa das semanas anteriores a janela. O recorte na janela e feito depois, por quem chama.

    Args:
        previsoes_da_e2: `previsoes.csv` da E2 inteiro.
        braco: `completo`, `sem_casos`, `sem_clima` ou `sem_vetor`.
        horizonte: h.

    Returns:
        O composto do horizonte, com `COLUNAS_DO_COMPOSTO` (inclui `folha_escolhida`).
    """
    da_folha_5 = selecionar_braco_da_folha(previsoes_da_e2, braco, FOLHA_PRIMARIA, horizonte)
    da_folha_20 = selecionar_braco_da_folha(previsoes_da_e2, braco, FOLHA_SECUNDARIA, horizonte)
    return montar_composto(da_folha_5, da_folha_20, horizonte, JANELA_PRIMARIA)


def ler_previsoes_do_composto_da_e3() -> pd.DataFrame:
    """Previsoes da E3 com N = 13, todas as origens (nao so a janela), precisao total dos floats."""
    todas = pd.read_csv(
        CAMINHO_DAS_PREVISOES_DA_E3,
        parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
        float_precision="round_trip",
    )
    return todas.loc[todas[COLUNA_DA_JANELA_N] == JANELA_PRIMARIA]


def conferir_ancora_1_reproducao_exata(composto_remontado: pd.DataFrame, composto_da_e3: pd.DataFrame, horizonte: int) -> int:
    """Ancora 1: o composto completo remontado e IGUAL ao da E3 (mesmas linhas, previsoes e folha escolhida).

    Args:
        composto_remontado: Composto completo montado neste script, um horizonte.
        composto_da_e3: Linhas da E3 (N = 13) do mesmo horizonte.
        horizonte: h (so para a mensagem).

    Returns:
        Quantidade de linhas comparadas.

    Raises:
        RuntimeError: Se houver qualquer diferenca (linhas, datas, real, previsto ou folha).
    """
    remontado = composto_remontado.reset_index(drop=True)
    da_e3 = composto_da_e3.reset_index(drop=True)
    if len(remontado) != len(da_e3):
        raise RuntimeError(f"ANCORA 1 FALHOU h={horizonte}: {len(remontado)} linhas remontadas contra {len(da_e3)} da E3.")

    datas_de_origem_iguais = bool((remontado[COLUNA_DATA_DE_ORIGEM] == da_e3[COLUNA_DATA_DE_ORIGEM]).all())
    datas_alvo_iguais = bool((remontado[COLUNA_DATA_ALVO] == da_e3[COLUNA_DATA_ALVO]).all())
    folhas_iguais = bool(
        (remontado[NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA] == da_e3[NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA]).all()
    )
    diferenca_do_previsto = float(np.abs(remontado[COLUNA_DO_PREVISTO] - da_e3[COLUNA_DO_PREVISTO]).max())
    diferenca_do_real = float(np.abs(remontado[COLUNA_DO_REAL] - da_e3[COLUNA_DO_REAL]).max())

    reproduziu = (
        datas_de_origem_iguais
        and datas_alvo_iguais
        and folhas_iguais
        and diferenca_do_previsto == 0.0
        and diferenca_do_real == 0.0
    )
    if not reproduziu:
        raise RuntimeError(
            f"ANCORA 1 FALHOU h={horizonte}: origens iguais={datas_de_origem_iguais}, alvos iguais={datas_alvo_iguais}, "
            f"folhas iguais={folhas_iguais}, dif previsto={diferenca_do_previsto!r}, dif real={diferenca_do_real!r}."
        )
    return len(remontado)


def conferir_ancora_2_mae_da_janela(composto_completo_na_janela: pd.DataFrame, horizonte: int) -> float:
    """Ancora 2: o MAE na janela do composto completo bate com `E3_composto/resumo.csv` (N = 13).

    Raises:
        RuntimeError: Se o MAE diferir mais que a tolerancia ou a janela nao tiver 102 semanas.
    """
    resumo_da_e3 = pd.read_csv(CAMINHO_DO_RESUMO_DA_E3, float_precision="round_trip")
    e_do_n_primario = resumo_da_e3[COLUNA_DA_JANELA_N] == JANELA_PRIMARIA
    e_do_horizonte = resumo_da_e3[COLUNA_DO_HORIZONTE] == horizonte
    linha = resumo_da_e3.loc[e_do_n_primario & e_do_horizonte]
    if len(linha) != 1:
        raise RuntimeError(f"ANCORA 2 FALHOU h={horizonte}: resumo da E3 sem linha unica.")

    mae_da_e3 = float(linha["mae"].iloc[0])
    mae_remontado = erro_absoluto_medio(
        composto_completo_na_janela[COLUNA_DO_REAL], composto_completo_na_janela[COLUNA_DO_PREVISTO]
    )
    semanas_na_janela = len(composto_completo_na_janela)
    mae_bate = abs(mae_remontado - mae_da_e3) < TOLERANCIA_DO_MAE_DA_ANCORA_2
    if semanas_na_janela != SEMANAS_ESPERADAS_NA_JANELA or not mae_bate:
        raise RuntimeError(
            f"ANCORA 2 FALHOU h={horizonte}: n={semanas_na_janela}, MAE remontado={mae_remontado!r}, MAE da E3={mae_da_e3!r}."
        )
    return mae_remontado


def nome_do_composto_sem(fonte: str) -> str:
    """Nome do candidato `composto_sem_<fonte>`."""
    return f"composto_sem_{fonte}"


def montar_compostos_na_janela(previsoes_da_e2: pd.DataFrame) -> dict[tuple[str, int], pd.DataFrame]:
    """`(nome, h) -> composto na janela de avaliacao` do completo e dos tres `sem_b`, depois de conferir as ancoras.

    Raises:
        RuntimeError: Se alguma das duas ancoras falhar (nada e calculado depois).
    """
    composto_da_e3 = ler_previsoes_do_composto_da_e3()
    compostos_na_janela: dict[tuple[str, int], pd.DataFrame] = {}

    for horizonte in HORIZONTES_TESTADOS:
        composto_completo = montar_composto_do_braco(previsoes_da_e2, BRACO_COMPLETO, horizonte)
        da_e3_do_horizonte = composto_da_e3.loc[composto_da_e3[COLUNA_DO_HORIZONTE] == horizonte]
        linhas_comparadas = conferir_ancora_1_reproducao_exata(composto_completo, da_e3_do_horizonte, horizonte)
        completo_na_janela = recortar_janela_de_avaliacao(composto_completo, CONFIGURACAO_AVALIACAO)
        mae_da_ancora = conferir_ancora_2_mae_da_janela(completo_na_janela, horizonte)
        REGISTRADOR.registrar(
            f"ANCORA OK h={horizonte:2d}: {linhas_comparadas} linhas identicas as da E3 (dif 0); "
            f"MAE na janela {mae_da_ancora:.6f} (n={len(completo_na_janela)})"
        )
        compostos_na_janela[(NOME_DO_COMPOSTO_COMPLETO, horizonte)] = completo_na_janela

        for fonte in FONTES_TESTADAS:
            composto_sem_a_fonte = montar_composto_do_braco(previsoes_da_e2, f"sem_{fonte}", horizonte)
            sem_na_janela = recortar_janela_de_avaliacao(composto_sem_a_fonte, CONFIGURACAO_AVALIACAO)
            compostos_na_janela[(nome_do_composto_sem(fonte), horizonte)] = sem_na_janela
            REGISTRADOR.registrar(
                f"composto sem_{fonte:6s} h={horizonte:2d}: {len(composto_sem_a_fonte)} previsoes; "
                f"{len(sem_na_janela)} na janela"
            )
    return compostos_na_janela


def montar_definicoes_da_ablacao() -> list[DefinicaoDoTeste]:
    """12 testes (3 fontes x 4 horizontes): composto completo (A) contra composto sem b (B), uma unica familia.

    O limiar usa o maior piso entre as duas folhas no horizonte (Emenda 1: comparacao que envolve o composto).
    """
    definicoes: list[DefinicaoDoTeste] = []
    for fonte in FONTES_TESTADAS:
        for horizonte in HORIZONTES_TESTADOS:
            definicoes.append(
                DefinicaoDoTeste(
                    FAMILIA_DA_ABLACAO_NO_COMPOSTO,
                    horizonte,
                    NOME_DO_COMPOSTO_COMPLETO,
                    nome_do_composto_sem(fonte),
                    (FOLHA_PRIMARIA, FOLHA_SECUNDARIA),
                )
            )
    return definicoes


def calcular_fracoes_de_folha(composto_completo: pd.DataFrame, composto_sem_b: pd.DataFrame) -> dict[str, float]:
    """Fracoes descritivas de folha escolhida, nas semanas-alvo em comum (as mesmas do teste pareado).

    Returns:
        `frac_folha20_completo`, `frac_folha20_sem_b` e `frac_troca_de_folha` (fracao de semanas em que a
        folha escolhida do composto sem b difere da do composto completo).
    """
    escolhas_do_completo = composto_completo[[COLUNA_DATA_ALVO, NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA]].rename(
        columns={NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA: "folha_completo"}
    )
    escolhas_sem_b = composto_sem_b[[COLUNA_DATA_ALVO, NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA]].rename(
        columns={NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA: "folha_sem_b"}
    )
    em_comum = escolhas_do_completo.merge(escolhas_sem_b, on=COLUNA_DATA_ALVO, how="inner")
    usou_folha_20_no_completo = em_comum["folha_completo"] == FOLHA_SECUNDARIA
    usou_folha_20_sem_b = em_comum["folha_sem_b"] == FOLHA_SECUNDARIA
    folhas_diferem = em_comum["folha_completo"] != em_comum["folha_sem_b"]
    return {
        "frac_folha20_completo": float(usou_folha_20_no_completo.mean()),
        "frac_folha20_sem_b": float(usou_folha_20_sem_b.mean()),
        "frac_troca_de_folha": float(folhas_diferem.mean()),
    }


def ler_resultados_de_f1_e_f3() -> pd.DataFrame:
    """Linhas F1 (folha 5) e F3 (folha 20) de `estatistica/familias.csv` (completo x sem_b), para comparar."""
    familias = pd.read_csv(CAMINHO_DAS_FAMILIAS, float_precision="round_trip")
    e_f1_ou_f3 = familias["familia"].isin(["F1", "F3"])
    return familias.loc[e_f1_ou_f3]


def buscar_resultado_da_familia(familias_f1_f3: pd.DataFrame, familia: str, fonte: str, horizonte: int) -> pd.Series:
    """Linha unica de F1 ou F3 para uma fonte e horizonte.

    Raises:
        RuntimeError: Se nao houver exatamente uma linha.
    """
    e_da_familia = familias_f1_f3["familia"] == familia
    e_da_fonte = familias_f1_f3["B"].str.startswith(f"sem_{fonte}@")
    e_do_horizonte = familias_f1_f3["h"] == horizonte
    linha = familias_f1_f3.loc[e_da_familia & e_da_fonte & e_do_horizonte]
    if len(linha) != 1:
        raise RuntimeError(f"Linha de {familia} nao unica para {fonte}, h={horizonte}.")
    return linha.iloc[0]


def montar_tabela_final(
    definicoes: list[DefinicaoDoTeste],
    tabela_do_pacote: pd.DataFrame,
    compostos_na_janela: dict[tuple[str, int], pd.DataFrame],
) -> pd.DataFrame:
    """Junta o resultado do pacote, as fracoes de folha e a comparacao com F1 e F3 em uma tabela de 12 linhas."""
    familias_f1_f3 = ler_resultados_de_f1_e_f3()
    linhas: list[dict[str, object]] = []
    for posicao, definicao in enumerate(definicoes):
        resultado = tabela_do_pacote.iloc[posicao]
        fonte = definicao.nome_b.removeprefix("composto_sem_")
        composto_completo = compostos_na_janela[(definicao.nome_a, definicao.horizonte)]
        composto_sem_b = compostos_na_janela[(definicao.nome_b, definicao.horizonte)]
        fracoes = calcular_fracoes_de_folha(composto_completo, composto_sem_b)
        da_f1 = buscar_resultado_da_familia(familias_f1_f3, "F1", fonte, definicao.horizonte)
        da_f3 = buscar_resultado_da_familia(familias_f1_f3, "F3", fonte, definicao.horizonte)
        linhas.append(
            {
                "fonte": fonte,
                "h": definicao.horizonte,
                "n": int(resultado["n"]),
                "mae_completo": resultado["mae_A"],
                "mae_sem_b": resultado["mae_B"],
                "delta": resultado["delta"],
                "ganho_pct": resultado["ganho_pct"],
                "ic_inf": resultado["ic_inf"],
                "ic_sup": resultado["ic_sup"],
                "dm_hln": resultado["dm_hln"],
                "p_bruto": resultado["p_bruto"],
                "p_holm": resultado["p_holm"],
                "limiar_piso": resultado["limiar_piso"],
                "variancia_fallback": resultado["variancia_fallback"],
                "veredito": resultado["veredito"],
                "frac_folha20_completo": fracoes["frac_folha20_completo"],
                "frac_folha20_sem_b": fracoes["frac_folha20_sem_b"],
                "frac_troca_de_folha": fracoes["frac_troca_de_folha"],
                "delta_F1_folha5": da_f1["delta"],
                "ganho_pct_F1_folha5": da_f1["ganho_pct"],
                "veredito_F1_folha5": da_f1["veredito"],
                "delta_F3_folha20": da_f3["delta"],
                "ganho_pct_F3_folha20": da_f3["ganho_pct"],
                "veredito_F3_folha20": da_f3["veredito"],
            }
        )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_CSV))


def main() -> int:
    """Confere as ancoras, roda os 12 testes e grava o CSV.

    Returns:
        0 se terminou; 1 se uma ancora falhou (nada e gravado como resultado).
    """
    exigir_travas_da_e2_aprovadas()
    previsoes_da_e2 = ler_previsoes_da_e2()
    piso_de_ruido = pd.read_csv(CAMINHO_DO_PISO, float_precision="round_trip")
    REGISTRADOR.registrar(
        f"inicio ablacao no composto (EXPLORATORIA): {len(previsoes_da_e2)} previsoes da E2 lidas; N={JANELA_PRIMARIA}"
    )

    try:
        compostos_na_janela = montar_compostos_na_janela(previsoes_da_e2)
    except RuntimeError as erro:
        REGISTRADOR.registrar(f"PARADO: {erro}")
        return 1

    definicoes = montar_definicoes_da_ablacao()
    previsoes_por_candidato = {}
    for chave, composto in compostos_na_janela.items():
        previsoes_por_candidato[chave] = composto[[COLUNA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]].copy()
    tabela_do_pacote = executar_familias(definicoes, previsoes_por_candidato, piso_de_ruido)

    tabela_final = montar_tabela_final(definicoes, tabela_do_pacote, compostos_na_janela)
    tabela_final.to_csv(CAMINHO_DO_CSV, index=False)

    contagem_de_vereditos = tabela_final["veredito"].value_counts().to_dict()
    REGISTRADOR.registrar(
        f"fim: {len(tabela_final)} testes em {CAMINHO_DO_CSV.name}; vereditos={contagem_de_vereditos}; "
        f"valores de n={sorted(tabela_final['n'].unique().tolist())}; "
        f"variancia_fallback={int(tabela_final['variancia_fallback'].sum())}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
