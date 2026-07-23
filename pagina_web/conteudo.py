"""

Textos e rotulos que aparecem no site, separados do codigo que monta as
paginas. E aqui que voce edita as PALAVRAS (o objetivo, a descricao das fontes
de dados, o nome bonito de cada cenario) sem precisar mexer no gerador.

A ideia: o gerador (gerar.py) cuida do "como fica na tela"; este arquivo cuida
do "o que esta escrito". Mudou um texto? Edita aqui e roda o gerador de novo.

"""

# Identidade do projeto: aparece no topo de todas as paginas.
PROJETO = {
    "titulo": "Modelagem preditiva de Aedes aegypti e dengue",
    "subtitulo": "Porto Alegre — previsao semana a semana",
    "autor": "Vinicius Guerra",
    "instituicao": "PPGC — UFRGS (Mestrado)",
    "local": "Porto Alegre, RS",
}


# Objetivo do trabalho, em linguagem simples (pagina "Objetivo").
OBJETIVO = {
    "frase": (
        "Prever, com semanas de antecedencia, quando o mosquito Aedes aegypti "
        "e a dengue vao aumentar em Porto Alegre."
    ),
    "paragrafos": [
        (
            "A dengue anda junto com o mosquito e com o clima. Quando faz calor "
            "e chove, o mosquito se multiplica; algumas semanas depois, os casos "
            "de dengue sobem. Se der pra enxergar esse aumento ANTES de ele "
            "acontecer, a cidade ganha tempo pra agir (mutirao de limpeza, "
            "alerta, reforco nos postos)."
        ),
        (
            "Este trabalho usa tres coisas medidas semana a semana: quanto "
            "mosquito foi pego nas armadilhas, o clima (calor, chuva, umidade) e "
            "os casos de dengue confirmados. Com isso, treina modelos que tentam "
            "adivinhar o numero de casos das proximas semanas."
        ),
    ],
    "pergunta_central": (
        "Saber quanto mosquito foi capturado ajuda a prever a dengue melhor do "
        "que so olhar o clima?"
    ),
    "pergunta_explica": (
        "Essa e a pergunta central da pesquisa. No jargao, e o “lift do "
        "vetor”: o ganho que a informacao do mosquito traz para a previsao, "
        "alem do que o clima ja explica. Varios dos cenarios abaixo existem "
        "justamente para medir e comprovar esse ganho."
    ),
    "como_testa": [
        (
            "Treina no passado, preve o futuro (walk-forward)",
            "O modelo so pode usar o que ja aconteceu. Ele treina com tudo ate "
            "uma semana, preve a seguinte, depois inclui essa semana no treino e "
            "preve a proxima, e assim por diante. Nunca deixa o modelo espiar a "
            "resposta.",
        ),
        (
            "Preve varias semanas a frente (horizonte)",
            "Horizonte e quantas semanas na frente a previsao mira: 4 semanas "
            "(1 mes), 8 (2 meses), 12 (3 meses). Quanto mais longe, mais dificil "
            "acertar.",
        ),
        (
            "Compara com provas estatisticas",
            "Nao basta o modelo parecer melhor: testes como McNemar e "
            "Diebold-Mariano mostram se a diferenca e de verdade ou foi sorte.",
        ),
    ],
}


# As fontes de dados (pagina "Dados"): uma entrada por fonte.
FONTES_DADOS = [
    {
        "nome": "Captura de mosquito (atual)",
        "periodo": "2025 em diante",
        "cadencia": "semanal",
        "papel": "Quanto mosquito foi pego nas armadilhas da cidade a cada semana. E o “vetor” — o personagem principal da pesquisa.",
        "origem": "Raspado do sistema oficial, semana a semana.",
        "vital": True,
    },
    {
        "nome": "Captura de mosquito (historico)",
        "periodo": "2019 a 2023",
        "cadencia": "semanal",
        "papel": "A mesma contagem de mosquito, so que do passado, para dar historico ao modelo.",
        "origem": "Base da pesquisadora Marilia.",
        "vital": False,
    },
    {
        "nome": "Clima",
        "periodo": "serie longa",
        "cadencia": "diario e semanal",
        "papel": "Temperatura, chuva, umidade, orvalho e pressao — o que faz o mosquito crescer.",
        "origem": "NASA POWER (satelite e reanalise).",
        "vital": False,
    },
    {
        "nome": "El Nino / La Nina (ENSO)",
        "periodo": "serie longa",
        "cadencia": "mensal",
        "papel": "A fase do oceano Pacifico que empurra o clima da regiao para mais quente ou mais chuvoso.",
        "origem": "NOAA.",
        "vital": False,
    },
    {
        "nome": "Casos de dengue confirmados",
        "periodo": "serie longa",
        "cadencia": "semanal",
        "papel": "Os casos confirmados em Porto Alegre. E o alvo — o numero que a gente quer prever.",
        "origem": "SINAN / Ministerio da Saude (dado publico).",
        "vital": False,
    },
    {
        "nome": "InfoDengue (Porto Alegre)",
        "periodo": "desde 2010",
        "cadencia": "semanal",
        "papel": "Serie historica de casos e clima da cidade, para completar o passado.",
        "origem": "InfoDengue (Fiocruz e FGV).",
        "vital": False,
    },
]


# O que sai da juncao de tudo (mostrado na pagina "Dados").
TABELA_FINAL = {
    "nome": "tabela_final",
    "papel": (
        "Todas as fontes acima entram numa linha de montagem e viram UMA tabela "
        "por semana: mosquito, clima, casos e El Nino lado a lado. E esse arquivo "
        "unico que os modelos usam para treinar e prever."
    ),
}


# O caminho dos dados, de ponta a ponta (diagrama simples).
FLUXO = [
    ("Fontes", "mosquito, clima, casos, El Nino"),
    ("Montagem", "junta tudo por semana (tabela_final)"),
    ("Experimento", "treina o modelo e mede o acerto"),
    ("Resultados", "metricas, graficos e este painel"),
]


# Nome bonito e explicacao de cada cenario (experimento). A chave e o nome
# tecnico usado no MLflow; se um cenario nao estiver aqui, o gerador usa o
# proprio nome tecnico.
CENARIOS = {
    "cidade_regressao": {
        "titulo": "Quantos casos? (modelo principal)",
        "pergunta": "Quantos casos de dengue vao ter na cidade?",
        "descricao": "O resultado principal da pesquisa: preve o numero de casos usando clima e mosquito, apagando as semanas recentes que ainda nao fecharam (corte de maturidade).",
    },
    "cidade_regressao_sem_enso": {
        "titulo": "Quantos casos? (sem corte de maturidade)",
        "pergunta": "E se nao apagar as semanas recentes?",
        "descricao": "Igual ao principal, mas sem o corte de maturidade — serve de comparacao para mostrar que o corte ajuda.",
    },
    "cidade_regressao_com_enso": {
        "titulo": "Quantos casos? (deixando o El Nino entrar)",
        "pergunta": "O El Nino ajuda na escolha do clima?",
        "descricao": "Igual ao principal, mas deixando o El Nino disputar espaco entre as colunas de clima escolhidas.",
    },
    "cidade_lift_vetor": {
        "titulo": "O ganho do mosquito (lift)",
        "pergunta": "So-clima x clima+mosquito x so-mosquito?",
        "descricao": "Mede o ganho bruto do mosquito: compara prever com so clima, com clima mais mosquito, e com so mosquito.",
    },
    "cidade_diebold": {
        "titulo": "O ganho do mosquito e real? (Diebold-Mariano)",
        "pergunta": "A melhora do mosquito e estatistica ou foi sorte?",
        "descricao": "Prova estatistica de que o modelo com mosquito erra de fato menos que o modelo so com clima.",
    },
    "cidade_deteccao_surto": {
        "titulo": "Vai ter surto? (sim/nao)",
        "pergunta": "A proxima janela vai passar do limite de surto?",
        "descricao": "Em vez de um numero, responde sim ou nao para “vai ter surto”, e usa o teste de McNemar para comparar com um palpite simples.",
    },
    "comparacao_literatura": {
        "titulo": "Nosso metodo x a literatura",
        "pergunta": "Como nos comparamos com o metodo publicado?",
        "descricao": "Poe o nosso metodo lado a lado com o metodo da literatura (Oliveira et al.).",
    },
    "bairro_surto": {
        "titulo": "Onde o mosquito vai subir? (por bairro)",
        "pergunta": "Em quais bairros o mosquito tende a crescer?",
        "descricao": "A direcao nova da pesquisa: como so ha contagem de mosquito por bairro (e nao casos), preve o mosquito por bairro, usando tambem os vizinhos.",
    },
}


# Nome bonito das metricas (o que o MLflow guarda como MAE_media, R2_media...).
ROTULOS_METRICAS = {
    "MAE_media": "Erro medio (MAE)",
    "R2_media": "R² (o quanto explica)",
    "RMSE_media": "Erro quadratico (RMSE)",
    "acuracia_media": "Acerto (acuracia)",
    "precisao_media": "Precisao",
    "recall_media": "Sensibilidade (recall)",
    "f1_media": "F1",
    "auc_media": "AUC",
}


# Metricas de resumo que NAO sao "nota de qualidade" (escondidas da tabela
# principal; continuam aparecendo nos detalhes de cada modelo).
METRICAS_ESCONDIDAS = {"h_media", "n_media", "passo_media", "step_media"}


# Nome bonito de alguns parametros comuns (o resto aparece como esta).
ROTULOS_PARAMETROS = {
    "algoritmo": "Algoritmo",
    "cenario": "Cenario",
    "coluna_alvo": "O que preve",
    "horizontes": "Horizontes (semanas)",
    "semanas_corte_maturidade": "Corte de maturidade (semanas)",
    "modelo_nome": "Modelo",
    "modelo_selecao_clima_nome": "Modelo que escolhe o clima",
}
