"""E6a: reproducao da escolha das 6 colunas de clima (pre-declaracao de 12/10/2026, secao 2).

Roda o procedimento do codigo antigo (LightGBM, ganho somado em h = 1, 4 e 8,
primeiros 60% das linhas validas, top 6; ver `aedes/selecao_clima.py`) sobre a
tabela certificada com o corte de maturidade, em TRES variantes:

    1. `identico_ao_antigo`:        `n_jobs=-1`, sem semente (como o antigo);
    2. `um_processo_sem_semente`:   `n_jobs=1`, sem semente;
    3. `um_processo_semente_42`:    `n_jobs=1`, `random_state=42`.

Em cada variante guarda o ganho de cada candidata (o antigo nao guardava).

CRITERIO DE REPRODUCAO: os 6 nomes, na mesma ordem, do clima congelado do
artigo (`aedes.configuracao.CONFIGURACAO_VARIAVEIS`): temp_media_lag4,
umid_media, temp_media_lag3, temp_max, pressao_media_lag3, pressao_media_lag4.
LEITURA DESCRITIVA: a margem entre a 6a e a 7a candidata.

REGRA DO VINICIUS (12/10): o modelo de referencia do artigo NAO muda, qualquer
que seja o resultado desta etapa. Divergencia e documentada, nunca forcada.

Grava em `resultados/reproducao_selecao/E6a_clima/` (ou na pasta de `--saida`):
    - `ganho_<variante>.csv`: candidata, ganho por horizonte, ganho somado, posicao;
    - `resumo.json`: por variante, as 6 escolhidas, se reproduz, a margem 6a-7a;
    - `E6a_clima.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`; leva segundos):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e6a_clima
"""

import argparse
import dataclasses
import pathlib
import sys

import pandas as pd

from aedes.configuracao import CONFIGURACAO_DADOS, CONFIGURACAO_VARIAVEIS
from aedes.selecao_clima import (
    COLUNAS_IGNORADAS,
    FRACAO_DE_TREINO_DA_SELECAO,
    HORIZONTES_DA_SELECAO,
    MODELO_DE_SELECAO_IDENTICO_AO_ANTIGO,
    MODELO_DE_SELECAO_UM_PROCESSO,
    MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE,
    PADROES_DO_CLIMA,
    PADROES_DO_VETOR,
    QUANTIDADE_DE_COLUNAS_DE_CLIMA,
    QUANTIDADE_ESPERADA_DE_CANDIDATAS,
    QUANTIDADE_ESPERADA_DO_NUCLEO,
    ConfiguracaoDoModeloDeSelecao,
    GruposDeColunas,
    calcular_margem_de_entrada,
    construir_tabela_de_candidatas,
    escolher_as_melhores,
    selecionar_clima_por_ganho,
    separar_grupos_de_colunas,
)
from experimentos.comum_reproducao import (
    PASTA_DA_REPRODUCAO,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_json_de_forma_atomica,
)

PASTA_DE_SAIDA_PADRAO = PASTA_DA_REPRODUCAO / "E6a_clima"

# Ordem das variantes = ordem da pre-declaracao.
VARIANTES: dict[str, ConfiguracaoDoModeloDeSelecao] = {
    "identico_ao_antigo": MODELO_DE_SELECAO_IDENTICO_AO_ANTIGO,
    "um_processo_sem_semente": MODELO_DE_SELECAO_UM_PROCESSO,
    "um_processo_semente_42": MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE,
}


def listar_o_clima_do_artigo() -> list[str]:
    """Os 6 nomes de clima congelados no pacote, na ordem do ranking antigo."""
    nomes: list[str] = []
    for variavel_de_clima in CONFIGURACAO_VARIAVEIS.variaveis_de_clima:
        nomes.append(variavel_de_clima.nome)
    return nomes


def montar_tabela_de_ganhos(resultado_ganho_por_horizonte: pd.DataFrame, ranking: pd.Series) -> pd.DataFrame:
    """Uma linha por candidata, na ordem do ranking: ganho por horizonte, ganho somado e posicao (de 1).

    Args:
        resultado_ganho_por_horizonte: Ganho de cada candidata por horizonte (`ResultadoDaSelecaoDeClima`).
        ranking: Ganho somado, ordenado do maior para o menor.

    Returns:
        DataFrame com `posicao`, `candidata`, `ganho_h*` e `ganho_total`.
    """
    por_horizonte_na_ordem = resultado_ganho_por_horizonte.loc[ranking.index]
    tabela = por_horizonte_na_ordem.copy()
    tabela.insert(0, "candidata", ranking.index)
    tabela["ganho_total"] = ranking.to_numpy()
    tabela.insert(0, "posicao", range(1, len(tabela) + 1))
    return tabela.reset_index(drop=True)


def rodar_uma_variante(
    nome_da_variante: str,
    configuracao_do_modelo: ConfiguracaoDoModeloDeSelecao,
    tabela_de_candidatas: pd.DataFrame,
    grupos: GruposDeColunas,
    pasta_de_saida: pathlib.Path,
    registrador: RegistradorDeLog,
) -> dict[str, object]:
    """Roda a selecao de uma variante, grava o ganho de todas as candidatas e devolve o resumo.

    Args:
        nome_da_variante: Nome da variante (vai no nome do CSV).
        configuracao_do_modelo: Hiperparametros do LightGBM da variante.
        tabela_de_candidatas: Saida de `construir_tabela_de_candidatas`.
        grupos: Colunas do nucleo, do clima e do vetor.
        pasta_de_saida: Onde gravar `ganho_<variante>.csv`.
        registrador: Log da etapa.

    Returns:
        O resumo da variante: as 6 escolhidas, se reproduz o clima do artigo, a margem.
    """
    resultado = selecionar_clima_por_ganho(
        tabela_de_candidatas, grupos, HORIZONTES_DA_SELECAO, FRACAO_DE_TREINO_DA_SELECAO, configuracao_do_modelo
    )
    escolhidas = escolher_as_melhores(resultado.ranking, QUANTIDADE_DE_COLUNAS_DE_CLIMA)
    clima_do_artigo = listar_o_clima_do_artigo()
    reproduz = escolhidas == clima_do_artigo
    mesmo_conjunto = sorted(escolhidas) == sorted(clima_do_artigo)
    margem = calcular_margem_de_entrada(resultado.ranking, QUANTIDADE_DE_COLUNAS_DE_CLIMA)

    tabela_de_ganhos = montar_tabela_de_ganhos(resultado.ganho_por_horizonte, resultado.ranking)
    caminho_do_csv = pasta_de_saida / f"ganho_{nome_da_variante}.csv"
    pasta_de_saida.mkdir(parents=True, exist_ok=True)
    tabela_de_ganhos.to_csv(caminho_do_csv, index=False)

    registrador.registrar(
        f"variante={nome_da_variante} top6={escolhidas} reproduz_na_ordem={reproduz} "
        f"mesmo_conjunto={mesmo_conjunto} margem_6a_7a={margem['diferenca']:.1f} "
        f"(7a={margem['proxima']})"
    )
    return {
        "configuracao_do_modelo": dataclasses.asdict(configuracao_do_modelo),
        "escolhidas": escolhidas,
        "reproduz_os_6_nomes_na_ordem": reproduz,
        "mesmo_conjunto_de_6": mesmo_conjunto,
        "margem_entre_a_6a_e_a_7a": margem,
        "linhas_validas_por_horizonte": resultado.linhas_validas_por_horizonte,
        "linhas_de_treino_por_horizonte": resultado.linhas_de_treino_por_horizonte,
        "nucleo": grupos.nucleo,
        "quantidade_de_candidatas_de_clima": len(grupos.clima),
    }


def ler_argumentos() -> argparse.Namespace:
    """Le `--saida` (pasta de saida; padrao: `resultados/reproducao_selecao/E6a_clima`)."""
    leitor = argparse.ArgumentParser(description="E6a: reproducao da selecao das 6 colunas de clima.")
    leitor.add_argument(
        "--saida",
        type=pathlib.Path,
        default=PASTA_DE_SAIDA_PADRAO,
        help="Pasta de saida (para uma conferencia fora de `resultados/`).",
    )
    return leitor.parse_args()


def main() -> int:
    """Roda as tres variantes e grava os ganhos e o resumo.

    Returns:
        0 sempre que as tres rodaram (reproduzir ou nao e RESULTADO, nao erro);
        1 se a tabela nao tiver as 42 candidatas de clima e os 8 do nucleo esperados.
    """
    argumentos = ler_argumentos()
    pasta_de_saida: pathlib.Path = argumentos.saida
    registrador = RegistradorDeLog(pasta_de_saida / "E6a_clima.log")

    tabela_cortada = carregar_tabela_cortada()
    tabela_de_candidatas = construir_tabela_de_candidatas(tabela_cortada, CONFIGURACAO_DADOS)
    grupos = separar_grupos_de_colunas(
        list(tabela_de_candidatas.columns), COLUNAS_IGNORADAS, PADROES_DO_VETOR, PADROES_DO_CLIMA
    )
    registrador.registrar(
        f"inicio E6a: {len(grupos.nucleo)} do nucleo, {len(grupos.clima)} candidatas de clima, "
        f"{len(grupos.vetor)} do vetor; horizontes={list(HORIZONTES_DA_SELECAO)}"
    )
    if len(grupos.clima) != QUANTIDADE_ESPERADA_DE_CANDIDATAS or len(grupos.nucleo) != QUANTIDADE_ESPERADA_DO_NUCLEO:
        registrador.registrar(
            f"ANCORA DIVERGE: esperadas {QUANTIDADE_ESPERADA_DE_CANDIDATAS} candidatas e "
            f"{QUANTIDADE_ESPERADA_DO_NUCLEO} do nucleo; a etapa PARA."
        )
        return 1

    resumo_das_variantes: dict[str, object] = {}
    for nome_da_variante, configuracao_do_modelo in VARIANTES.items():
        resumo_das_variantes[nome_da_variante] = rodar_uma_variante(
            nome_da_variante,
            configuracao_do_modelo,
            tabela_de_candidatas,
            grupos,
            pasta_de_saida,
            registrador,
        )

    conteudo = {
        "criterio": "os 6 nomes na mesma ordem do clima congelado do artigo",
        "clima_do_artigo": listar_o_clima_do_artigo(),
        "variantes": resumo_das_variantes,
    }
    gravar_json_de_forma_atomica(conteudo, pasta_de_saida / "resumo.json")
    registrador.registrar(f"fim E6a: {len(VARIANTES)} variantes; resumo em {pasta_de_saida / 'resumo.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
