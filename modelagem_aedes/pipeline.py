"""

Este arquivo comanda os experimentos do projeto, na ordem em que eles acontecem
(leia de cima pra baixo).

Cada experimento tem uma funcao rodar_<nome>(config) que reaproveita o mesmo
motor (que treina no passado e preve o futuro, semana a semana), as mesmas
colunas calculadas e a mesma forma de avaliar. QUAL modelo cada experimento usa
vem da ficha (config.modelo); assim da pra comparar LightGBM, RandomForest, etc.
Toda tabela de saida ganha uma coluna 'algoritmo' com o nome do modelo, pra
comparar os resultados de modelos diferentes lado a lado.

"""

import numpy as np
import pandas as pd

from acesso import fontes
from avaliacao import diebold_mariano, mcnemar
from avaliacao.metricas import calcular_metricas_classificacao
from avaliacao.metricas_regressao import calcular_metricas_regressao
from config import settings
from dominio import features, features_bairro, features_comparacao, selecao_features, surto
from motor import comparacao_literatura
from motor.walk_forward import executar_walk_forward_surto
from motor.walk_forward_bairro import executar_walk_forward_bairro
from motor.walk_forward_pareado import executar_walk_forward_pareado
from motor.walk_forward_regressao import executar_walk_forward_regressao

# Colunas, e a ordem delas, que aparecem nas tabelas de resultado impressas na tela.
COLUNAS_EXIBICAO = [
    "pctl", "h", "modelo", "n", "n_pos",
    "sensib", "espec", "f1", "bal_acc", "auc", "ap",
]

# Modelos comparados no Experimento A: nome que aparece na tela, coluna com o
# palpite do modelo e coluna com a chance que o modelo deu pra esse palpite.
MODELOS_EXPERIMENTO_A = [
    ("clima+AR_LGBM", "pred", "prob"),
    ("sazonal", "pred_saz", "prob_saz"),
    ("persistencia", "pred_pers", None),
]


def rodar_experimento_a(config, infodengue: pd.DataFrame) -> pd.DataFrame:
    """

    Experimento A: confere se da pra detectar surto so usando o InfoDengue.

    Pra cada percentil (o corte que define o que conta como surto) e cada
    horizonte de tempo, o codigo treina no passado e preve o futuro, semana a
    semana, e compara o modelo principal - o do config.modelo, que usa o clima e
    o proprio historico de casos - com dois modelos bem mais simples, usados so
    de comparacao: um que so olha a epoca do ano (sazonal) e outro que so
    repete o ultimo valor visto (persistencia).

    Returns:
        Tabela com os resultados de cada percentil, horizonte e modelo.

    """
    print("#" * 80)
    print("# EXPERIMENTO A — InfoDengue notificado (2010-2026, sem censura)")
    print("#   'da pra detectar surto 1-3 meses a frente em POA?'")
    print("#" * 80)

    features_infodengue = features.selecionar_colunas_por_prefixo(
        infodengue, config.prefixos_features_infodengue
    ) + ["sem_sin", "sem_cos"]

    linhas_metricas = []
    for percentil in config.percentis:
        for horizonte in config.horizontes:
            resultado_walk_forward = executar_walk_forward_surto(
                infodengue, features_infodengue, "fonte", horizonte, percentil,
                config.modelo,
            )
            for nome_modelo, coluna_pred, coluna_prob in MODELOS_EXPERIMENTO_A:
                probabilidade = (
                    resultado_walk_forward[coluna_prob] if coluna_prob else None
                )
                metricas = calcular_metricas_classificacao(
                    resultado_walk_forward["real"],
                    resultado_walk_forward[coluna_pred],
                    probabilidade,
                )
                metricas.update(
                    {
                        "exp": "A_infodengue",
                        "pctl": percentil,
                        "h": horizonte,
                        "modelo": nome_modelo,
                    }
                )
                linhas_metricas.append(metricas)

    resultados_experimento_a = pd.DataFrame(linhas_metricas)
    print(resultados_experimento_a[COLUNAS_EXIBICAO].round(3).to_string(index=False))
    return resultados_experimento_a



def rodar_experimento_b(config, tabela_final: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """

    Experimento B: confere se os dados de mosquito ajudam a detectar surto,
    usando o teste de McNemar.

    Pra cada percentil e cada horizonte de tempo, o codigo treina no passado e
    preve o futuro (semana a semana) duas vezes - uma so com clima, outra com
    clima e mosquito - usando exatamente as mesmas divisoes de treino e teste
    nas duas rodadas, e depois compara os acertos par a par com o teste de
    McNemar. O modelo sazonal, que e igual nos dois casos, e mostrado a partir
    da rodada so-clima.

    Returns:
        Dois resultados juntos: a tabela com os numeros de cada modelo e a
        tabela com os resultados do teste de McNemar.

    """
    print("\n" + "#" * 80)
    print("# EXPERIMENTO B — tabela_final: so-clima vs clima+VETOR na deteccao (McNemar)")
    print("#" * 80)

    colunas_clima = features.selecionar_colunas_por_prefixo(tabela_final, config.prefixos_clima)
    colunas_autorregressivas = features.selecionar_colunas_por_prefixo(
        tabela_final, config.prefixos_autorregressivo
    )
    colunas_vetor = features.selecionar_colunas_por_prefixo(tabela_final, config.prefixos_vetor)
    features_so_clima = colunas_autorregressivas + colunas_clima + ["sem_sin", "sem_cos"]
    features_clima_vetor = (
        colunas_autorregressivas + colunas_clima + colunas_vetor + ["sem_sin", "sem_cos"]
    )

    linhas_metricas = []
    linhas_mcnemar = []
    for percentil in config.percentis:
        for horizonte in config.horizontes:
            resultado_clima = executar_walk_forward_surto(
                tabela_final, features_so_clima, "fonte", horizonte, percentil,
                config.modelo,
            )
            resultado_vetor = executar_walk_forward_surto(
                tabela_final, features_clima_vetor, "fonte", horizonte, percentil,
                config.modelo,
            )
            comparacao = resultado_clima.merge(
                resultado_vetor, on=["h", "data", "real"], suffixes=("_c", "_v")
            )

            # O modelo sazonal e igual nos dois casos, entao ele vem so do lado so-clima.
            metricas_sazonal = calcular_metricas_classificacao(
                comparacao["real"], comparacao["pred_saz_c"], comparacao["prob_saz_c"]
            )
            metricas_sazonal.update(
                {"exp": "B_tabela_final", "pctl": percentil, "h": horizonte, "modelo": "sazonal"}
            )
            linhas_metricas.append(metricas_sazonal)

            for nome_modelo, sufixo in [("so-clima", "_c"), ("clima+vetor", "_v")]:
                metricas = calcular_metricas_classificacao(
                    comparacao["real"],
                    comparacao[f"pred{sufixo}"],
                    comparacao[f"prob{sufixo}"],
                )
                metricas.update(
                    {"exp": "B_tabela_final", "pctl": percentil, "h": horizonte, "modelo": nome_modelo}
                )
                linhas_metricas.append(metricas)

            # Teste de McNemar: compara so-clima (A) com clima+mosquito (B) nos mesmos casos de teste.
            resultado_mcnemar = mcnemar.teste_mcnemar(
                (comparacao["pred_c"] == comparacao["real"]).to_numpy(),
                (comparacao["pred_v"] == comparacao["real"]).to_numpy(),
            )
            linhas_mcnemar.append(
                {
                    "pctl": percentil,
                    "h": horizonte,
                    "n": len(comparacao),
                    "n_pos": int(comparacao["real"].sum()),
                    "clima_certo_vetor_errado": resultado_mcnemar.n_a_certo_b_errado,
                    "vetor_certo_clima_errado": resultado_mcnemar.n_a_errado_b_certo,
                    "p": round(resultado_mcnemar.valor_p, 3),
                }
            )
            mensagem_mcnemar = (
                f"  P{percentil} h={horizonte:2d}: n={len(comparacao):3d} "
                f"pos={int(comparacao['real'].sum()):2d} | "
                f"clima>vetor={resultado_mcnemar.n_a_certo_b_errado} "
                f"vetor>clima={resultado_mcnemar.n_a_errado_b_certo} "
                f"McNemar p={resultado_mcnemar.valor_p:.3f}"
            )
            print(mensagem_mcnemar)

    resultados_experimento_b = pd.DataFrame(linhas_metricas)
    print("\n=== Metricas por modelo (Experimento B) ===")
    print(resultados_experimento_b[COLUNAS_EXIBICAO].round(3).to_string(index=False))
    resultados_mcnemar = pd.DataFrame(linhas_mcnemar)
    return resultados_experimento_b, resultados_mcnemar



def rodar_cidade_deteccao_surto(config) -> dict[str, pd.DataFrame]:
    """

    Roda o experimento completo de deteccao de surto na cidade (A + B, os dois
    juntos).

    Returns:
        Um dicionario ligando o nome de cada arquivo de saida a tabela que vai
        dentro dele, pronto pra salvar.

    """
    infodengue = fontes.carregar_infodengue()
    infodengue = features.construir_features_temporais(infodengue)
    resultados_experimento_a = rodar_experimento_a(config, infodengue)

    tabela_final = fontes.carregar_tabela_final()
    tabela_final = surto.aplicar_corte_maturidade(tabela_final, config.semanas_corte_maturidade)
    tabela_final = features.construir_features_temporais(tabela_final)
    resultados_experimento_b, resultados_mcnemar = rodar_experimento_b(config, tabela_final)

    resultados_completos = pd.concat(
        [resultados_experimento_a, resultados_experimento_b], ignore_index=True
    )
    resultados_completos.insert(0, "algoritmo", config.modelo.nome)
    resultados_mcnemar.insert(0, "algoritmo", config.modelo.nome)
    return {
        "deteccao_surto_resultados.csv": resultados_completos,
        "deteccao_surto_mcnemar.csv": resultados_mcnemar,
    }



# Junta no fim algumas linhas de referencia vindas de outro resultado ja salvo (se a config pedir).
def juntar_referencias(resultados: pd.DataFrame, config) -> pd.DataFrame:
    if not config.arquivo_referencias:
        return resultados
    referencias = pd.read_csv(settings.PASTA_RESULTADOS / config.arquivo_referencias)
    referencias = referencias[referencias["conjunto"].isin(config.conjuntos_referencia)]
    # Traz o 'algoritmo' do arquivo de referencia se ele existir la; senao, as
    # linhas de referencia ficam sem algoritmo (viram vazio depois do concat).
    colunas_referencia = ["MAE", "R2"]
    if "algoritmo" in referencias.columns:
        colunas_referencia = ["algoritmo"] + colunas_referencia
    referencias = referencias.groupby(["conjunto", "h"])[colunas_referencia].first().reset_index()
    return pd.concat([resultados, referencias], ignore_index=True)



def rodar_regressao_selecao_clima(config) -> dict[str, pd.DataFrame]:
    """

    Roda um experimento de previsao do numero de casos que primeiro escolhe as
    poucas colunas de clima que mais ajudam e depois mede o ganho do mosquito.

    Serve a varios experimentos da familia regressao (com ou sem o corte das
    semanas recentes, com ou sem os dados do El Nino entre os candidatos de
    clima). Abre a tabela, calcula as colunas usadas pelo modelo, escolhe as
    colunas de clima que mais ajudam (pelo "ganho" que cada uma traz) e, pra
    cada quantidade K de colunas de clima, treina no passado e preve o futuro
    (semana a semana) duas vezes: so com clima (M0) e com clima + mosquito (M1),
    medindo o erro medio (MAE) e o quanto o modelo explica (R2). Se a config
    pedir, junta no fim linhas de referencia de outro resultado ja salvo.

    Returns:
        Um dicionario ligando o nome do arquivo de saida a tabela de resultados.

    """
    tabela_final = fontes.carregar_tabela_final()
    tabela_final = surto.aplicar_corte_maturidade(tabela_final, config.semanas_corte_maturidade)
    tabela_final = features.construir_features_temporais(tabela_final)

    colunas_nucleo, colunas_clima, colunas_vetor = selecao_features.separar_grupos_de_features(
        tabela_final, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )
    ranking_clima = selecao_features.selecionar_clima_por_ganho(
        tabela_final, colunas_nucleo, colunas_clima, config.coluna_alvo,
        config.horizontes_selecao_clima, config.modelo_selecao_clima, config.fracao_treino_selecao,
    )
    print("clima top-8:", ranking_clima.head(8).index.tolist())

    linhas_metricas = []
    for k in config.valores_k:
        clima_enxuto = ranking_clima.head(k).index.tolist()

        resultado_m0 = executar_walk_forward_regressao(
            tabela_final, colunas_nucleo + clima_enxuto, config.coluna_alvo,
            config.horizontes, config.modelo, config.minimo_semanas_treino, config.passo,
        )
        linhas_metricas += calcular_metricas_regressao(resultado_m0, f"M0_clima{k}")

        resultado_m1 = executar_walk_forward_regressao(
            tabela_final, colunas_nucleo + clima_enxuto + colunas_vetor, config.coluna_alvo,
            config.horizontes, config.modelo, config.minimo_semanas_treino, config.passo,
        )
        linhas_metricas += calcular_metricas_regressao(resultado_m1, f"M1_clima{k}_vetor")

    resultados = pd.DataFrame(linhas_metricas)
    resultados["algoritmo"] = config.modelo.nome
    resultados = juntar_referencias(resultados, config)
    resultados = resultados[list(config.colunas_saida)]
    return {config.arquivo_saida: resultados}



def rodar_regressao_conjuntos_fixos(config) -> dict[str, pd.DataFrame]:
    """

    Roda um experimento de previsao de casos comparando conjuntos FIXOS de
    colunas, sem escolher clima por importancia.

    Pra cada conjunto pedido na config (por exemplo: so clima, clima + mosquito,
    so mosquito), treina no passado e preve o futuro (semana a semana) e mede o
    erro medio (MAE) e o quanto o modelo explica (R2).

    Returns:
        Um dicionario ligando o nome do arquivo de saida a tabela de resultados.

    """
    tabela_final = fontes.carregar_tabela_final()
    tabela_final = surto.aplicar_corte_maturidade(tabela_final, config.semanas_corte_maturidade)
    tabela_final = features.construir_features_temporais(tabela_final)

    colunas_nucleo, colunas_clima, colunas_vetor = selecao_features.separar_grupos_de_features(
        tabela_final, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )

    linhas_metricas = []
    for nome_conjunto, incluir_clima, incluir_vetor in config.conjuntos:
        colunas = list(colunas_nucleo)
        if incluir_clima:
            colunas = colunas + colunas_clima
        if incluir_vetor:
            colunas = colunas + colunas_vetor
        resultado = executar_walk_forward_regressao(
            tabela_final, colunas, config.coluna_alvo,
            config.horizontes, config.modelo, config.minimo_semanas_treino, config.passo,
        )
        linhas_metricas += calcular_metricas_regressao(resultado, nome_conjunto)

    resultados = pd.DataFrame(linhas_metricas)
    resultados["algoritmo"] = config.modelo.nome
    resultados = resultados[list(config.colunas_saida)]
    return {config.arquivo_saida: resultados}



def rodar_cidade_diebold(config) -> dict[str, pd.DataFrame]:
    """

    Roda o teste de Diebold-Mariano: prova (estatistica) se somar o mosquito faz
    o modelo de casos errar menos de um jeito confiavel.

    Pra cada opcao de corte das semanas recentes (sem cortar e cortando as
    ultimas 12), escolhe as poucas colunas de clima que mais ajudam, monta o M0
    (so clima) e o M1 (clima + mosquito) e, pra cada semana a frente, treina os
    dois nas MESMAS semanas de teste e compara os erros deles semana a semana.
    Guarda a diferenca media de erro e o quao confiavel e essa vantagem (dois
    jeitos de medir o erro: ao quadrado e pelo valor absoluto).

    Returns:
        Um dicionario ligando o nome do arquivo de saida a tabela de resultados.

    """
    linhas_resultado = []
    for nome_corte, semanas_corte in config.cortes_maturidade:
        tabela_final = fontes.carregar_tabela_final()
        tabela_final = surto.aplicar_corte_maturidade(tabela_final, semanas_corte)
        tabela_final = features.construir_features_temporais(tabela_final)

        colunas_nucleo, colunas_clima, colunas_vetor = selecao_features.separar_grupos_de_features(
            tabela_final, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
        )
        ranking_clima = selecao_features.selecionar_clima_por_ganho(
            tabela_final, colunas_nucleo, colunas_clima, config.coluna_alvo,
            config.horizontes_selecao_clima, config.modelo_selecao_clima, config.fracao_treino_selecao,
        )
        clima_enxuto = ranking_clima.head(config.valor_k).index.tolist()
        colunas_m0 = colunas_nucleo + clima_enxuto
        colunas_m1 = colunas_nucleo + clima_enxuto + colunas_vetor
        print(f"=== {nome_corte} | clima top-{config.valor_k}: {clima_enxuto} ===")

        for horizonte in config.horizontes:
            erros_m0, erros_m1 = executar_walk_forward_pareado(
                tabela_final, colunas_m0, colunas_m1, config.coluna_alvo, horizonte,
                config.modelo, config.minimo_semanas_treino, config.passo,
            )
            diferenca_mae = np.abs(erros_m0).mean() - np.abs(erros_m1).mean()
            resultado_quadratico = diebold_mariano.teste_diebold_mariano(
                erros_m0, erros_m1, horizonte, "quadratico"
            )
            resultado_absoluto = diebold_mariano.teste_diebold_mariano(
                erros_m0, erros_m1, horizonte, "absoluto"
            )
            linhas_resultado.append(
                {
                    "conjunto": nome_corte,
                    "h": horizonte,
                    "n": resultado_quadratico.n,
                    "dMAE": diferenca_mae,
                    "DM_sq": resultado_quadratico.estatistica,
                    "p_sq": resultado_quadratico.valor_p,
                    "DM_abs": resultado_absoluto.estatistica,
                    "p_abs": resultado_absoluto.valor_p,
                }
            )

    resultados = pd.DataFrame(linhas_resultado)
    resultados["algoritmo"] = config.modelo.nome
    resultados = resultados[list(config.colunas_saida)]
    return {config.arquivo_saida: resultados}



def rodar_comparacao_literatura(config) -> dict[str, pd.DataFrame]:
    """

    Compara o nosso modelo (clima + mosquito) com o metodo da literatura (so
    clima), nos mesmos dados de Porto Alegre.

    Faz duas comparacoes. Na primeira, mede o quanto cada modelo explica os casos
    (R2) pra cada semana a frente. Na segunda, refaz a tarefa do trabalho do
    Oliveira: dizer se os casos vao "acelerar" (subir em relacao a duas semanas
    atras), medindo o acerto de dois jeitos - o honesto (treina no passado, preve
    o futuro) e o da literatura (embaralha e separa treino/teste).

    Returns:
        Um dicionario com duas tabelas: a comparacao de casos e a da aceleracao.

    """
    tabela_final = fontes.carregar_tabela_final()
    tabela_final, features_so_clima, features_clima_vetor = (
        features_comparacao.construir_features_comparacao(tabela_final)
    )

    print("PARTE 1: previsao de casos (treina no passado, preve o futuro)...")
    r2_so_clima = comparacao_literatura.r2_por_horizonte(
        tabela_final, features_so_clima, config.coluna_alvo, config.horizontes,
        config.modelo_regressao, config.minimo_semanas_treino, config.passo_regressao,
    )
    r2_clima_vetor = comparacao_literatura.r2_por_horizonte(
        tabela_final, features_clima_vetor, config.coluna_alvo, config.horizontes,
        config.modelo_regressao, config.minimo_semanas_treino, config.passo_regressao,
    )
    comparacao_casos = pd.DataFrame(
        {"R2_so_clima": r2_so_clima, "R2_clima_vetor": r2_clima_vetor}
    )
    comparacao_casos["ganho"] = comparacao_casos["R2_clima_vetor"] - comparacao_casos["R2_so_clima"]
    comparacao_casos = comparacao_casos.reset_index(names="h")
    comparacao_casos.insert(0, "algoritmo", config.modelo_regressao.nome)
    print(comparacao_casos.round(3).to_string(index=False))

    print("\nPARTE 2: aceleracao de casos (replica do Oliveira)...")
    grupos_por_fonte = tabela_final.groupby("fonte", group_keys=False)
    diferenca_de_casos = grupos_por_fonte[config.coluna_alvo].diff(config.defasagem_aceleracao)
    tabela_final["aceleracao"] = (diferenca_de_casos > 0).astype(int)

    acerto_honesto_clima, n_testes = comparacao_literatura.acerto_aceleracao_walk_forward(
        tabela_final, features_so_clima, "aceleracao", config.modelo_classificacao,
        config.minimo_semanas_treino, config.passo_classificacao,
    )
    acerto_honesto_vetor, _ = comparacao_literatura.acerto_aceleracao_walk_forward(
        tabela_final, features_clima_vetor, "aceleracao", config.modelo_classificacao,
        config.minimo_semanas_treino, config.passo_classificacao,
    )
    acerto_split_clima = comparacao_literatura.acerto_aceleracao_split_aleatorio(
        tabela_final, features_so_clima, "aceleracao", config.modelo_classificacao,
        config.sementes_split, config.fracao_teste,
    )
    acerto_split_vetor = comparacao_literatura.acerto_aceleracao_split_aleatorio(
        tabela_final, features_clima_vetor, "aceleracao", config.modelo_classificacao,
        config.sementes_split, config.fracao_teste,
    )

    comparacao_oliveira = pd.DataFrame(
        [
            {
                "protocolo": "split_aleatorio",
                "so_clima": acerto_split_clima,
                "clima_vetor": acerto_split_vetor,
                "n": pd.NA,
                "referencia_oliveira": config.referencia_oliveira,
            },
            {
                "protocolo": "walk_forward",
                "so_clima": acerto_honesto_clima,
                "clima_vetor": acerto_honesto_vetor,
                "n": n_testes,
                "referencia_oliveira": config.referencia_oliveira,
            },
        ]
    )
    comparacao_oliveira.insert(0, "algoritmo", config.modelo_regressao.nome)
    print(comparacao_oliveira.round(3).to_string(index=False))

    return {
        config.arquivo_saida_casos: comparacao_casos,
        config.arquivo_saida_oliveira: comparacao_oliveira,
    }



def rodar_bairro_surto(config) -> dict[str, pd.DataFrame]:
    """

    Roda o experimento que preve a densidade de mosquito por bairro.

    Abre as capturas de mosquito, monta a tabela bairro x semana, descobre os
    bairros vizinhos e cria as colunas do modelo (do proprio bairro e da
    vizinhanca). Depois roda as quatro receitas de colunas (so o bairro, com
    vizinhanca, melhoradas, e melhoradas + vizinhanca), medindo o quanto cada uma
    explica (R2) por semana a frente, e calcula o ganho das colunas melhoradas e
    o quanto a vizinhanca ajuda.

    Returns:
        Um dicionario ligando o nome do arquivo de saida a tabela de resultados.

    """
    capturas = fontes.carregar_capturas_marilia_por_ano(config.anos)
    painel = features_bairro.construir_painel_semanal(capturas)
    bairros = sorted(painel["bairro"].unique())

    dados_bairro = features_bairro.construir_grade_completa(painel)
    vizinhos_de = features_bairro.mapear_vizinhos(painel, bairros, config.numero_vizinhos)
    dados_bairro = features_bairro.adicionar_densidade_vizinhanca(dados_bairro, vizinhos_de, bairros)
    dados_bairro = features_bairro.adicionar_features_temporais(dados_bairro)

    r2_por_combo = {}
    for nome_combo, colunas, usar_epoca_do_alvo in config.combos:
        print(f"rodando combo: {nome_combo} ({len(colunas)} colunas)", flush=True)
        r2_por_combo[nome_combo] = executar_walk_forward_bairro(
            dados_bairro, list(colunas), config.coluna_alvo, config.horizontes,
            config.semana_minima_teste, config.passo, config.minimo_linhas_treino,
            config.modelo, usar_epoca_do_alvo,
        )

    resultados = pd.DataFrame(r2_por_combo).round(3)
    coluna_ganho_a, coluna_ganho_b = config.colunas_ganho
    resultados["ganho_enh"] = (resultados[coluna_ganho_a] - resultados[coluna_ganho_b]).round(3)
    coluna_lift_a, coluna_lift_b = config.colunas_lift_vizinhanca
    resultados["lift_viz_enh"] = (resultados[coluna_lift_a] - resultados[coluna_lift_b]).round(3)
    resultados = resultados.reset_index(names="h")
    resultados.insert(0, "algoritmo", config.modelo.nome)
    print(resultados.to_string(index=False))
    return {config.arquivo_saida: resultados}
