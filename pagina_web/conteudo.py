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
        "tipo": "vetor",
        "periodo": "2025 em diante",
        "cadencia": "semanal",
        "papel": "Quanto mosquito foi pego nas armadilhas da cidade a cada semana. E o “vetor” — o personagem principal da pesquisa.",
        "origem": "Raspado do sistema oficial, semana a semana.",
        "vital": True,
    },
    {
        "nome": "Captura de mosquito (historico)",
        "tipo": "vetor",
        "periodo": "2019 a 2023",
        "cadencia": "semanal",
        "papel": "A mesma contagem de mosquito, so que do passado, para dar historico ao modelo.",
        "origem": "Base da pesquisadora Marilia.",
        "vital": False,
    },
    {
        "nome": "Clima",
        "tipo": "clima",
        "periodo": "serie longa",
        "cadencia": "diario e semanal",
        "papel": "Temperatura, chuva, umidade, orvalho e pressao — o que faz o mosquito crescer.",
        "origem": "NASA POWER (satelite e reanalise).",
        "vital": False,
    },
    {
        "nome": "El Nino / La Nina (ENSO)",
        "tipo": "clima",
        "periodo": "serie longa",
        "cadencia": "mensal",
        "papel": "A fase do oceano Pacifico que empurra o clima da regiao para mais quente ou mais chuvoso.",
        "origem": "NOAA.",
        "vital": False,
    },
    {
        "nome": "Casos de dengue confirmados",
        "tipo": "alvo",
        "periodo": "serie longa",
        "cadencia": "semanal",
        "papel": "Os casos confirmados em Porto Alegre. E o alvo — o numero que a gente quer prever.",
        "origem": "SINAN / Ministerio da Saude (dado publico).",
        "vital": False,
    },
    {
        "nome": "InfoDengue (Porto Alegre)",
        "tipo": "contexto",
        "periodo": "desde 2010",
        "cadencia": "semanal",
        "papel": "Serie historica de casos e clima da cidade, para completar o passado.",
        "origem": "InfoDengue (Fiocruz e FGV).",
        "vital": False,
    },
]


# O que compoe o "clima" (mostrado na pagina "Dados"): cada tema e as colunas
# que ele gera. Cada grandeza vira minimo/media/maximo na semana, por isso sao
# varias por tema. Tudo vem do NASA POWER, agregado de diario para semanal.
COLUNAS_CLIMA = {
    "intro": "Cada grandeza vem resumida na semana (minimo / media / maximo), por isso sao varias por tema:",
    "fonte": "NASA POWER",
    "nota_agregacao": "agregadas de diario para semanal",
    "nota_lag": "O modelo ainda cria versoes defasadas (1 a 4 semanas) de algumas delas, para tambem olhar o clima das semanas anteriores.",
    "temas": [
        ("🌧️", "Chuva", ["precip_total_mm", "precip_max_dia_mm", "precip_media_dia_mm", "dias_de_chuva"]),
        ("🌡️", "Temperatura", ["temp_media", "temp_min", "temp_max", "temp_amplitude_media"]),
        ("💧", "Ponto de orvalho", ["orvalho_min", "orvalho_media", "orvalho_max"]),
        ("💦", "Umidade", ["umid_min", "umid_media", "umid_max"]),
        ("🔻", "Pressao", ["pressao_min", "pressao_media", "pressao_max"]),
        ("☀️", "Radiacao solar", ["radiacao_min", "radiacao_media", "radiacao_max"]),
        ("🌫️", "Vento", ["vento_media", "vento_max"]),
    ],
}


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
# proprio nome tecnico. "menu" e o rotulo curto que aparece no menu lateral.
CENARIOS = {
    "cidade_regressao": {
        "menu": "Previsao principal",
        "titulo": "Quantos casos vao ter",
        "pergunta": "Quantos casos de dengue a cidade vai ter nas proximas semanas?",
        "descricao": "O modelo principal do trabalho. Usa clima e mosquito para prever o numero de casos, e deixa de fora as semanas mais recentes, que ainda estao sendo contadas e enganam.",
    },
    "cidade_regressao_com_enso": {
        "menu": "Com El Nino",
        "titulo": "E se o El Nino entrar na conta?",
        "pergunta": "Somar o El Nino ao clima melhora a previsao?",
        "descricao": "A previsao principal, mas deixando o El Nino (o esquenta e esfria do oceano Pacifico) concorrer com o clima local.",
    },
    "cidade_regressao_sem_enso": {
        "menu": "Sem apagar semanas",
        "titulo": "E sem apagar as semanas recentes?",
        "pergunta": "O que muda se a gente confiar nas semanas que ainda nao fecharam?",
        "descricao": "A previsao principal sem tirar as semanas recentes. Serve de comparacao para mostrar que deixar essas semanas de fora ajuda mesmo.",
    },
    "cidade_lift_vetor": {
        "menu": "O ganho do mosquito",
        "titulo": "O mosquito ajuda a prever?",
        "pergunta": "So clima, clima mais mosquito, ou so mosquito — o que preve melhor?",
        "descricao": "Compara os tres jeitos lado a lado para medir quanto a contagem de mosquito acrescenta a previsao.",
    },
    "cidade_diebold": {
        "menu": "E ganho de verdade?",
        "titulo": "Esse ganho e real ou foi sorte?",
        "pergunta": "A melhora que o mosquito traz aguenta um teste estatistico?",
        "descricao": "Poe o modelo so com clima contra o modelo com clima mais mosquito e testa (Diebold-Mariano) se a diferenca e real, e nao coincidencia.",
    },
    "comparacao_literatura": {
        "menu": "Contra a literatura",
        "titulo": "Como a gente se sai contra o metodo publicado",
        "pergunta": "Somando o mosquito, a gente bate o metodo publicado que usa so clima?",
        "descricao": "Recria um metodo ja publicado (Oliveira et al., so com clima) e coloca lado a lado com o nosso, que tambem usa o mosquito.",
    },
    "cidade_deteccao_surto": {
        "menu": "Vai ter surto?",
        "titulo": "Vai ter surto ou nao?",
        "pergunta": "As proximas semanas vao passar do limite de surto?",
        "descricao": "Em vez de um numero, responde sim ou nao para “vai ter surto” e compara com um palpite simples para ver se acerta mais.",
    },
    "bairro_surto": {
        "menu": "Por bairro",
        "titulo": "Onde o mosquito vai subir",
        "pergunta": "Em quais bairros o mosquito tende a crescer?",
        "descricao": "O rumo novo da pesquisa. Como so ha contagem de mosquito por bairro (e nao de casos), aqui a gente preve o proprio mosquito, olhando tambem os bairros vizinhos.",
    },
}


# Como os cenarios sao agrupados no menu e na pagina de cenarios, seguindo a
# historia do trabalho: primeiro prever os casos, depois provar que o mosquito
# ajuda, e por fim as outras frentes. Cada grupo lista os nomes tecnicos na
# ordem em que devem aparecer.
GRUPOS_CENARIOS = [
    ("Prever os casos", [
        "cidade_regressao",
        "cidade_regressao_com_enso",
        "cidade_regressao_sem_enso",
    ]),
    ("O mosquito faz diferenca?", [
        "cidade_lift_vetor",
        "cidade_diebold",
        "comparacao_literatura",
    ]),
    ("Outras frentes", [
        "cidade_deteccao_surto",
        "bairro_surto",
    ]),
]


# Ficha de dados de cada cenario (mostrada no topo da pagina do cenario): as
# mesmas linhas em todos, pra dar pra comparar um cenario com o outro so de
# bater o olho. A ultima linha, "O que muda", e a diferenca entre os testes
# daquele cenario. Os valores saem direto dos arquivos de config dos experimentos.
FICHA_DADOS = {
    "cidade_regressao": [
        ("Alvo", "Casos de dengue confirmados na cidade"),
        ("Clima", "Entra — o modelo fica so com as 6 ou 8 colunas que mais ajudam"),
        ("Mosquito", "Entra — captura semanal nas armadilhas"),
        ("El Nino", "Fica de fora"),
        ("Corte de maturidade", "12 semanas: apaga as mais recentes, que ainda estao sendo contadas"),
        ("Horizontes", "1 a 12 semanas a frente"),
        ("O que muda", "Varios algoritmos (LightGBM, RandomForest e outros) com exatamente os mesmos dados"),
    ],
    "cidade_regressao_com_enso": [
        ("Alvo", "Casos de dengue confirmados na cidade"),
        ("Clima", "Entra — 6 ou 8 colunas escolhidas, e o El Nino concorre por uma vaga"),
        ("Mosquito", "Entra"),
        ("El Nino", "Entra — disputa espaco com o clima na hora de escolher as colunas"),
        ("Corte de maturidade", "Nenhum: usa todas as semanas"),
        ("Horizontes", "1 a 12 semanas a frente"),
        ("O que muda", "So clima, clima + mosquito e so mosquito — pra ver se o El Nino mudava o ganho do mosquito"),
    ],
    "cidade_regressao_sem_enso": [
        ("Alvo", "Casos de dengue confirmados na cidade"),
        ("Clima", "Entra — 6 ou 8 colunas que mais ajudam"),
        ("Mosquito", "Entra"),
        ("El Nino", "Fica de fora"),
        ("Corte de maturidade", "Nenhum: usa todas as semanas ja reportadas"),
        ("Horizontes", "1 a 12 semanas a frente"),
        ("O que muda", "So clima x clima + mosquito. A unica diferenca pro principal e nao apagar as semanas recentes"),
    ],
    "cidade_lift_vetor": [
        ("Alvo", "Casos de dengue confirmados na cidade"),
        ("Clima", "Entra o clima INTEIRO (aqui nao escolhe as melhores colunas)"),
        ("Mosquito", "Entra"),
        ("El Nino", "Entra, junto com o clima"),
        ("Corte de maturidade", "Nenhum"),
        ("Horizontes", "1 a 12 semanas a frente"),
        ("O que muda", "Tres conjuntos fixos de colunas: so clima, clima + mosquito e so mosquito"),
    ],
    "cidade_diebold": [
        ("Alvo", "Casos de dengue confirmados na cidade"),
        ("Clima", "Entra — as 6 colunas que mais ajudam"),
        ("Mosquito", "Entra no M1 (o M0 fica so com clima)"),
        ("El Nino", "Fica de fora"),
        ("Corte de maturidade", "Roda dos dois jeitos: sem corte e cortando 12 semanas"),
        ("Horizontes", "1 a 12 semanas a frente, testando todas as semanas"),
        ("O que muda", "M0 (so clima) x M1 (clima + mosquito), com o teste de Diebold-Mariano dizendo se a diferenca e confiavel"),
    ],
    "cidade_deteccao_surto": [
        ("Alvo", "Vai ter surto? (sim/nao) — passar do percentil 90 ou 95 de casos"),
        ("Clima", "Entra — clima de semanas atras (temperatura, chuva, orvalho, umidade, pressao)"),
        ("Mosquito", "Entra — captura de semanas atras e media movel"),
        ("El Nino", "Fica de fora"),
        ("Corte de maturidade", "12 semanas"),
        ("Horizontes", "4, 8 e 12 semanas a frente"),
        ("O que muda", "Modelo com mosquito x sem mosquito (teste de McNemar), e a comparacao com um palpite simples"),
    ],
    "comparacao_literatura": [
        ("Alvo", "Duas coisas: o numero de casos, e se os casos vao acelerar (subir)"),
        ("Clima", "Entra nos dois metodos"),
        ("Mosquito", "Entra so no nosso metodo"),
        ("El Nino", "Fica de fora"),
        ("Corte de maturidade", "Nao se aplica"),
        ("Horizontes", "1 a 12 semanas a frente"),
        ("O que muda", "O metodo da literatura (Oliveira et al., so clima) x o nosso (clima + mosquito), nos mesmos dados de POA"),
    ],
    "bairro_surto": [
        ("Alvo", "Densidade de mosquito de cada bairro (nao ha casos de dengue por bairro)"),
        ("Clima", "Nao usa"),
        ("Mosquito", "E o proprio alvo: usa o passado da densidade do bairro e dos 4 vizinhos (2019-2023)"),
        ("El Nino", "Nao usa"),
        ("Corte de maturidade", "Nao se aplica"),
        ("Horizontes", "1 a 4 semanas a frente"),
        ("O que muda", "Quatro receitas de colunas: so o bairro x + vizinhanca, e basico x melhorado (passado mais longe e criticidade)"),
    ],
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
