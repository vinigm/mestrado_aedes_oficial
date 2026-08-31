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
        "Como os dados de captura de mosquito em armadilhas podem ajudar a "
        "prever o surto de dengue na cidade?"
    ),
    "objetivo_central": (
        "Usar modelos de machine learning — de classificacao ou de regressao — "
        "para prever o surto de dengue com 1, 2 e 3 meses de antecedencia."
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
        "nome": "Captura de mosquito (raspagem propria)",
        "tipo": "vetor",
        "periodo": "2026 em diante",
        "cadencia": "semanal",
        "papel": "Quanto mosquito foi pego nas armadilhas da cidade a cada semana. E o “vetor” — o personagem principal da pesquisa. Continua a serie oficial sem interrupcao.",
        "origem": "Raspagem propria do portal publico do MI-Aedes.",
        "vital": True,
    },
    {
        "nome": "Captura de mosquito (Secretaria Municipal de Saude)",
        "tipo": "vetor",
        "periodo": "2012 a 2025",
        "cadencia": "semanal",
        "papel": "A mesma contagem de mosquito, historico oficial que da a base longa ao modelo: 636.587 inspecoes de armadilha, 236.166 femeas de Aedes aegypti, 81 bairros e 2.742 armadilhas ao longo de 14 anos.",
        "origem": "Secretaria Municipal de Saude — serie historica oficial do MI-Aedes, obtida em agosto de 2026, corrigida e certificada: 636.587 inspecoes, 236.166 femeas de Aedes aegypti, 81 bairros, 2.742 armadilhas.",
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
        "unico que os modelos usam para treinar e prever. Hoje a tabela cobre "
        "718 semanas com dado de mosquito, de 23/09/2012 a 09/08/2026, sem "
        "interrupcao — faltam so 7 semanas em 14 anos, 3 delas a enchente de "
        "maio de 2024, quando as vistorias de campo pararam."
    ),
}


# Dicionario de dados: uma entrada por COLUNA da tabela_final (o arquivo unico
# que alimenta os modelos). Cada tupla e (coluna, grupo, o_que_e, unidade). Os
# nomes e a ordem seguem exatamente o cabecalho de tabela_final.csv (36 colunas).
DICIONARIO_COLUNAS = [
    ("fonte", "Nucleo", "De onde veio a linha (secretaria ou raspagem propria).", "texto"),
    ("SE", "Nucleo", "Semana epidemiologica no formato ANOSS (ex.: 201901).", "codigo"),
    ("data_inicio_semana_epidemi", "Nucleo", "Data em que a semana epidemiologica comeca.", "data"),
    ("ano", "Nucleo", "Ano.", "ano"),
    ("semana", "Nucleo", "Numero da semana no ano.", "1-53"),
    ("numero_de_armadilhas", "Vetor", "Quantas armadilhas foram lidas na semana.", "contagem"),
    ("aedes_aegypti", "Vetor", "Aedes aegypti capturados na semana (soma da cidade).", "contagem"),
    ("aedes_albopictus", "Contexto", "Aedes albopictus capturados (outra especie).", "contagem"),
    ("culex_sp", "Contexto", "Culex sp capturados (pernilongo comum).", "contagem"),
    ("aedes_aegypti_por_armadilha", "Vetor", "Aedes aegypti por armadilha: a densidade do vetor. E a principal medida do mosquito.", "indice"),
    ("denominador_aproximado", "Nucleo", "Diz se o numero de armadilhas da semana e aproximado (2012 a 2018, quando o dado nao informa quais inspecoes foram concluidas).", "0/1"),
    ("precip_total_mm", "Clima · chuva", "Chuva total na semana.", "mm"),
    ("precip_max_dia_mm", "Clima · chuva", "Maior chuva num unico dia da semana.", "mm"),
    ("precip_media_dia_mm", "Clima · chuva", "Chuva media por dia na semana.", "mm"),
    ("dias_de_chuva", "Clima · chuva", "Quantos dias choveu na semana.", "dias"),
    ("temp_media", "Clima · temperatura", "Temperatura media da semana.", "°C"),
    ("temp_min", "Clima · temperatura", "Temperatura minima da semana.", "°C"),
    ("temp_max", "Clima · temperatura", "Temperatura maxima da semana.", "°C"),
    ("temp_amplitude_media", "Clima · temperatura", "Diferenca media entre a maxima e a minima do dia.", "°C"),
    ("orvalho_min", "Clima · orvalho", "Ponto de orvalho minimo (indica a umidade do ar).", "°C"),
    ("orvalho_media", "Clima · orvalho", "Ponto de orvalho medio.", "°C"),
    ("orvalho_max", "Clima · orvalho", "Ponto de orvalho maximo.", "°C"),
    ("umid_min", "Clima · umidade", "Umidade relativa minima.", "%"),
    ("umid_media", "Clima · umidade", "Umidade relativa media.", "%"),
    ("umid_max", "Clima · umidade", "Umidade relativa maxima.", "%"),
    ("pressao_min", "Clima · pressao", "Pressao atmosferica minima.", "kPa"),
    ("pressao_media", "Clima · pressao", "Pressao atmosferica media.", "kPa"),
    ("pressao_max", "Clima · pressao", "Pressao atmosferica maxima.", "kPa"),
    ("radiacao_min", "Clima · radiacao", "Radiacao solar minima.", "MJ/m²"),
    ("radiacao_media", "Clima · radiacao", "Radiacao solar media.", "MJ/m²"),
    ("radiacao_max", "Clima · radiacao", "Radiacao solar maxima.", "MJ/m²"),
    ("vento_media", "Clima · vento", "Velocidade media do vento.", "m/s"),
    ("vento_max", "Clima · vento", "Velocidade maxima do vento.", "m/s"),
    ("casos_confirmados", "Alvo", "Casos de dengue confirmados na semana. E o que o modelo quer prever.", "contagem"),
    ("nino34_anom", "El Nino", "Anomalia de temperatura do Pacifico (regiao Nino 3.4).", "°C"),
    ("oni", "El Nino", "Indice ONI: mede a fase El Nino / La Nina.", "°C"),
]


# Diario de atividades (pagina "Diario de atividades"): um bloco por dia, com o
# que foi feito e os "proximos" passos. Para adicionar um dia, copie um item e
# edite (data no formato AAAA-MM-DD). Ordene do mais recente para o mais antigo
# (o primeiro aparece no topo). O dia da semana e o mes saem sozinhos da data, e
# a busca da pagina acha por data, mes ou qualquer palavra (sem acento).
#
# O que foi feito no dia pode ser escrito de duas formas:
#   - "feito": uma lista de frases, tudo junto (aparece como "Atividades realizadas");
#   - "blocos": separado por assunto, cada bloco com "titulo" e "itens".
# Em "blocos" da pra pedir uma cor para o titulo com a chave "cor":
#   "modelos" = verde | "dados" = ambar | sem a chave = cinza padrao.
# Os "proximos" passos saem sempre em roxo, no fim do dia.
#
# Cada item de uma lista (tanto dos "itens" quanto dos "proximos") pode ser:
#   - uma frase, escrita direto entre aspas; ou
#   - um topico com sub-topicos: {"texto": "a frase", "sub": ["detalhe", "detalhe"]}.
# Os sub-topicos aparecem recuados, com um tracinho em vez da bolinha. Use-os
# para quebrar explicacao comprida em pedacos curtos, em vez de texto corrido.
DIARIO = [
    {
        "data": "2026-08-30",
        "blocos": [
            {
                "titulo": "Clima recapturado: a serie dobrou",
                "cor": "dados",
                "itens": [
                    {
                        "texto": "A captura de clima do NASA POWER comecava em dezembro de 2018 por causa de uma constante herdada de uma base que saiu do projeto em agosto. O dado sempre existiu; o projeto e que nao estava pedindo.",
                        "sub": [
                            "Clima semanal: de 388 para 727 semanas (setembro de 2012 em diante).",
                            "A interseccao clima + mosquito + casos subiu de 379 para 424 semanas.",
                        ],
                    },
                    {
                        "texto": "A certificacao REPROVOU a recaptura na primeira tentativa, e a investigacao mostrou que estava tudo certo.",
                        "sub": [
                            "365 das 388 semanas antigas bateram exatamente.",
                            "As 23 divergentes sao todas posteriores a 28/12/2025: e o reprocessamento normal da NASA, que revisa as semanas recentes.",
                            "Mosquito e casos ficaram intocados, conferidos celula a celula.",
                        ],
                    },
                ],
            },
            {
                "titulo": "A funcao de perda importa mais que o algoritmo",
                "cor": "modelos",
                "itens": [
                    {
                        "texto": "Um grid de 120 execucoes comparou 30 configuracoes: 3 algoritmos x 5 funcoes de perda x com e sem mosquito, em 4 horizontes.",
                        "sub": [
                            "Trocar o melhor algoritmo pelo pior custa 16,5% de erro.",
                            "Trocar a funcao de perda, no MESMO algoritmo, custa 20,2%.",
                            "As 6 configuracoes de perda padrao ficaram entre a 10a e a 23a posicao de 30.",
                        ],
                    },
                    "Configuracao de referencia do projeto: HistGradientBoosting com perda quantilica em 0,80, incluindo as variaveis de mosquito. As tres primeiras colocadas sao o mesmo algoritmo variando so o quantil, separadas por 2% a 4% — sao estatisticamente indistinguiveis.",
                    "O projeto passou meses comparando 9 algoritmos, e o ganho maior estava numa linha de configuracao que ninguem tinha mexido.",
                ],
            },
            {
                "titulo": "O modelo subestimava os picos: causa achada e tratada",
                "cor": "modelos",
                "itens": [
                    {
                        "texto": "Nas semanas de pico o modelo previa bem menos casos do que aconteceu, e a subestimacao crescia com a distancia da previsao.",
                        "sub": [
                            "Hipotese testada e REFUTADA: nao era limite de extrapolacao das arvores. O teto do treino era 1.439 casos e o pico medio 829 — o modelo tinha folga e mesmo assim previa baixo.",
                            "Causa real: 61% das semanas tem 5 casos ou menos, e a perda padrao puxa toda previsao para o centro dessa distribuicao.",
                            "O remedio veio de um projeto antigo de previsao de demanda no varejo, que ja tinha resolvido problema parecido.",
                        ],
                    },
                    "Com a calibracao quantilica, a captura do pico em 1 mes subiu de 78% para 92%.",
                    {
                        "texto": "Limite de confianca medido por horizonte, no periodo que nao participou da escolha:",
                        "sub": [
                            "1 semana: captura 98% da magnitude do pico.",
                            "1 mes: 92%.",
                            "2 meses: 70%.",
                            "3 meses: 62% — serve para alarmar, nao para dimensionar resposta.",
                        ],
                    },
                ],
            },
            {
                "titulo": "Por que a previsao piora com a distancia",
                "cor": "dados",
                "itens": [
                    {
                        "texto": "A degradacao tem causa medida, e nao e falta de ajuste do modelo.",
                        "sub": [
                            "O numero de casos de hoje explica 91% da variacao dos casos da semana que vem.",
                            "Em 12 semanas, explica ZERO — a correlacao e -0,005.",
                            "Nesse regime o mosquito passa a ser o preditor individual mais forte disponivel (0,61 a 0,62 entre 4 e 8 semanas, contra 0,27 a 0,40 do clima).",
                        ],
                    },
                    {
                        "texto": "Cinco familias de variaveis novas foram testadas para sustentar o horizonte longo. Quatro reprovaram.",
                        "sub": [
                            "Reprovadas: comparacao com o mesmo periodo de anos anteriores, anomalia climatica contra a media historica, acumulo de chuva e calor em 8 e 12 semanas, e os indicadores de transmissao do InfoDengue.",
                            "Aprovada: El Nino / La Nina, com ganho de cerca de 7% em 2 meses.",
                        ],
                    },
                    {
                        "texto": "O que falta nao e mais clima nem mais mosquito. E o sorotipo em circulacao e a imunidade da populacao, que determinam o tamanho de uma epidemia de dengue.",
                        "sub": [
                            "A base do SINAN tem o campo de sorotipo, mas so 0,33% dos 56.624 casos estao preenchidos — 43 registros em 2025.",
                            "O grupo InfoDengue declara exatamente a mesma limitacao no Relatorio Tecnico 02/2026: os modelos nao capturam imunidade previa nem introducao de novos sorotipos.",
                        ],
                    },
                ],
            },
            {
                "titulo": "O alvo da previsao ficou decidido por medicao",
                "cor": "dados",
                "itens": [
                    {
                        "texto": "A escolha entre casos confirmados e casos notificados estava em aberto desde junho. Os tres candidatos foram testados na mesma configuracao.",
                        "sub": [
                            "Casos confirmados vencem: R² de 0,758 contra 0,418 dos notificados em 3 meses.",
                            "O terceiro candidato, a serie corrigida por nowcasting do InfoDengue, e IDENTICA aos notificados em 99,1% das semanas — ela so corrige as 8 semanas mais recentes.",
                        ],
                    },
                    {
                        "texto": "Fica registrada uma ressalva sobre esse alvo: a taxa de confirmacao caiu de 73% em 2022 para 38% em 2025.",
                        "sub": [
                            "Quanto maior a epidemia, menor a fracao que chega a ser confirmada em laboratorio.",
                            "Parte da subestimacao dos picos pode vir dessa compressao do proprio alvo, e nao do modelo.",
                        ],
                    },
                ],
            },
            {
                "titulo": "O que o mosquito mostra, e o que ainda nao prova",
                "cor": "modelos",
                "itens": [
                    {
                        "texto": "No grid completo, as variaveis de mosquito aparecem em 8 das 10 melhores configuracoes.",
                        "sub": [
                            "Em 3 meses, incluir o mosquito melhorou o resultado em 15 de 15 combinacoes de algoritmo e perda.",
                            "Em 1 semana, piorou em 15 de 15 — coerente com a biologia, ja que a densidade de mosquito e um sinal antecedente.",
                        ],
                    },
                    {
                        "texto": "Mas o teste estatistico continua nao fechando.",
                        "sub": [
                            "Das 60 comparacoes pareadas, nenhuma sobrevive a correcao para multiplas comparacoes.",
                            "A direcao e consistente; a prova nao existe. O texto da tese precisa dizer as duas coisas.",
                        ],
                    },
                ],
            },
            {
                "titulo": "O ganho do projeto, medido de ponta a ponta",
                "cor": "modelos",
                "itens": [
                    {
                        "texto": "A primeira configuracao (LightGBM, perda padrao, sem mosquito) foi comparada com a atual nas MESMAS semanas de avaliacao. A diferenca e so de modelagem: nenhuma recebeu dado que a outra nao tivesse.",
                        "sub": [
                            "Captura do pico em 1 mes: de 65% para 83%.",
                            "Captura do pico em 3 meses: de 46% para 62%.",
                            "R² em 3 meses: de 0,541 para 0,758.",
                        ],
                    },
                    {
                        "texto": "Decompondo o ganho de 1 mes, uma mudanca por vez, aparece algo que nenhuma analise anterior tinha visto:",
                        "sub": [
                            "Trocar o algoritmo para HistGradientBoosting: +15,1 pontos.",
                            "Acrescentar as variaveis de mosquito: MENOS 9,9 pontos.",
                            "Calibrar a funcao de perda: +13,3 pontos.",
                            "Ou seja: o mosquito sozinho DERRUBA a captura do pico. Ele melhora o erro medio e piora o topo; so nao prejudica porque a calibracao vem depois e corrige o topo com folga. E um efeito de interacao — as duas mudancas isoladas nao entregam o que entregam juntas.",
                        ],
                    },
                ],
            },
            {
                "titulo": "Teste focado no horizonte de 3 meses",
                "cor": "modelos",
                "itens": [
                    {
                        "texto": "O padrao de 15 vitorias em 15 combinacoes precisava ser medido, e nao so contado. Foram 60 execucoes: 3 algoritmos, 2 horizontes, 2 conjuntos de variaveis e 5 sementes diferentes.",
                        "sub": [
                            "Em 3 meses o mosquito reduz o erro em 33,5 a 44,3 casos, sobre uma base de 215.",
                            "O ganho aparece nas 5 sementes, nos 3 algoritmos — nao depende da inicializacao do modelo.",
                            "O intervalo de confianca exclui zero em 2 dos 3 algoritmos, em todas as sementes.",
                            "Em 2 meses o efeito desaparece e o sinal muda conforme o algoritmo: e especifico do horizonte longo.",
                        ],
                    },
                    {
                        "texto": "Mesmo assim, nenhuma das 6 comparacoes sobrevive a correcao para multiplas comparacoes. Os melhores valores brutos, 0,027 e 0,031, passariam sozinhos, mas multiplicados por seis nao passam.",
                        "sub": [
                            "O resultado e EXPLORATORIO, nao confirmatorio: a hipotese nasceu destes mesmos dados.",
                            "So a temporada 2026-2027, que ainda nao existe, poderia confirma-lo.",
                        ],
                    },
                ],
            },
            {
                "titulo": "Tres trocas que os numeros sugeriram e que NAO foram feitas",
                "cor": "dados",
                "itens": [
                    {
                        "texto": "O protocolo do dia separa o periodo que ESCOLHE (ate 2023) do periodo que JULGA (2024 em diante). Em tres momentos o periodo de julgamento apontou uma escolha diferente, e em nenhum deles a escolha foi trocada.",
                        "sub": [
                            "O quantil 0,85 saiu melhor que o 0,80 selecionado.",
                            "O LightGBM lidera em 2 e 3 meses — mas e o pior dos tres no periodo de selecao, nos 4 horizontes.",
                            "Trocar pelo periodo que serve de juiz destruiria o valor do proprio julgamento. As tres ficam registradas como hipoteses para teste proprio.",
                        ],
                    },
                ],
            },
            {
                "titulo": "Pagina Cenario Principal no painel",
                "cor": "dados",
                "itens": [
                    "Criada uma pagina de acompanhamento com a configuracao vigente, a linha do tempo do projeto em seis etapas, o desempenho por horizonte, as 12 versoes testadas e descartadas, e as limitacoes assumidas.",
                    "Um erro foi corrigido no caminho: os numeros de captura do pico que a pagina exibia vinham de OUTRA configuracao (quantil 0,85 sem mosquito). Recalculados a partir das previsoes da configuracao de referencia.",
                    "Outro foi evitado: uma diferenca de 2 pontos em 2 meses estava escrita como piora. Conferido o intervalo de confianca, ele cruza zero — nao ha piora, ha ausencia de ganho mensuravel.",
                ],
            },
            {
                "titulo": "Proximos passos",
                "cor": "dados",
                "itens": [
                    "Gravar a configuracao de referencia no codigo do projeto: hoje ela existe so nas analises datadas.",
                    "Validar o El Nino dentro do grid completo, e nao isolado como foi testado.",
                    "Republicar o painel: as paginas de resultados ainda mostram os numeros de 16 de agosto.",
                ],
            },
        ],
    },
    {
        "data": "2026-08-16",
        "blocos": [
            {
                "titulo": "Base de mosquito corrigida e certificada",
                "cor": "dados",
                "itens": [
                    {
                        "texto": "A serie da Secretaria Municipal de Saude (2012-2025) passou por auditoria antes de virar oficial.",
                        "sub": [
                            "Datas invertidas em varias linhas de 2022 a 2025, corrigidas.",
                            "222 duplicatas removidas.",
                        ],
                    },
                    "A auditoria revelou a enchente de maio de 2024 nos proprios dados: as vistorias de armadilha pararam nas semanas de 28/04, 05/05 e 12/05, exatamente a cheia.",
                    "A raspagem propria (2026 em diante) virou a continuacao corrente dessa mesma serie oficial, sem interrupcao entre as duas fontes; o historico agora e atribuido direto a Secretaria Municipal de Saude, a origem verdadeira do dado.",
                ],
            },
            {
                "titulo": "Pipeline migrado e cenarios reexecutados",
                "cor": "modelos",
                "itens": [
                    "O pipeline de modelagem foi migrado da serie curta para a serie completa (2012-2026).",
                    "Todos os cenarios foram reexecutados na base corrigida — essa e a geracao OFICIAL de resultados (rodadas das 16h11 as 21h38).",
                    {
                        "texto": "Veredito honesto da estatistica:",
                        "sub": [
                            "O modelo vence persistencia e sazonalidade nos 12 horizontes (R² de 0,89 em 1 semana a 0,63 em 12 semanas).",
                            "O ganho do mosquito favorece o vetor em estimativa pontual em todos os horizontes, mas nem o Diebold-Mariano nem o McNemar sao significativos apos correcao de multiplas comparacoes.",
                            "Poder estatistico limitado: a serie ainda tem so cerca de 2 epidemias grandes para comparar.",
                        ],
                    },
                ],
            },
        ],
        "proximos": [
            "Estender a cobertura de casos e clima para antes de 2018, hoje o gargalo do lift do vetor.",
            "Levar mais epidemias para a serie assim que novos surtos forem confirmados, para ganhar poder estatistico.",
        ],
    },
    {
        "data": "2026-08-08",
        "blocos": [
            {
                "titulo": "Em relacao aos dados com a prefeitura",
                "cor": "dados",
                "itens": [
                    "Recebimento dos dados de armadilhas da Secretaria de Saude: os anos de 2012 a 2021.",
                    "Os arquivos vem em tres formatos diferentes ao longo dos anos, com nomes de coluna distintos para a mesma informacao.",
                    {
                        "texto": "Unificamos tudo num arquivo unico.",
                        "sub": [
                            "435.157 inspecoes, de setembro de 2012 a dezembro de 2021.",
                            "Uma linha por armadilha por semana, com bairro, quadra, coordenada e contagem por especie e sexo.",
                        ],
                    },
                    {
                        "texto": "Conferimos contra a base que ja tinhamos e os dados batem.",
                        "sub": [
                            "Os anos de 2019, 2020 e 2021 se sobrepoem e dao o mesmo numero, exato: 13.619, 8.527 e 13.084 femeas de Aedes aegypti.",
                            "Ou seja, as duas bases vem da mesma origem.",
                        ],
                    },
                    "A serie de mosquito passa de 276 para cerca de 600 semanas, somada ao que ja existia.",
                    "Ainda faltam os anos de 2022 a 2025, que a Secretaria vai enviar.",
                ],
            },
            {
                "titulo": "Coleta do dia",
                "itens": [
                    "Raspagem da captura de mosquito (semana 501): 112 exemplares.",
                ],
            },
        ],
        "proximos": [
            "Reforcar o pedido dos anos de 2022 a 2025, que sao os que contem os grandes surtos de dengue.",
            "Pedir o significado de alguns codigos de coluna dos anos mais antigos.",
            "Refazer a tabela de modelagem usando a serie longa.",
        ],
    },
    {
        "data": "2026-07-31",
        "blocos": [
            {
                "titulo": "Em relacao aos modelos",
                "cor": "modelos",
                "itens": [
                    "Conferimos as 6 fontes de dados e os 9 cenarios, arquivo por arquivo: os numeros batem com o que estava anotado.",
                    {
                        "texto": "Erro 1: a densidade de mosquito esta sendo calculada errado.",
                        "sub": [
                            "A conta divide sempre por 910 armadilhas.",
                            "Mas em muitas semanas menos armadilhas foram inspecionadas.",
                            "Resultado: o numero sai mais baixo do que deveria.",
                        ],
                    },
                    {
                        "texto": "Erro 2: as 17 primeiras semanas de 2026 entram no modelo quase sem dengue.",
                        "sub": [
                            "Era justo o periodo em que o mosquito estava no pico do ano.",
                            "Houve mais de 4 mil notificacoes nessas semanas.",
                            "O que faltava era a papelada, nao a doenca.",
                        ],
                    },
                    {
                        "texto": "Erro 3: no modelo por bairro, quase um quarto da tabela foi preenchido com zero.",
                        "sub": [
                            "O zero entrou onde ninguem passou para inspecionar.",
                            "Assim o modelo aprende o roteiro do agente de saude, e nao onde tem mosquito.",
                        ],
                    },
                    {
                        "texto": "Entendemos o que a coluna de casos confirmados mede de verdade.",
                        "sub": [
                            "Em 2025, mais da metade das fichas foi encerrada como inconclusiva.",
                            "Ou seja: ela mede quanto a vigilancia conseguiu concluir, e nao quanta dengue houve.",
                        ],
                    },
                    {
                        "texto": "Descobrimos por que o ganho do mosquito muda tanto de um cenario para outro.",
                        "sub": [
                            "Ele parece grande quando o modelo de comparacao esta ruim.",
                            "Isso enfraquece o nosso resultado principal.",
                        ],
                    },
                    "Confirmamos que as armadilhas de hoje sao as mesmas de 2019: a rede so encolheu, de 1.430 para 910.",
                ],
            },
            {
                "titulo": "Em relacao aos dados com a prefeitura",
                "cor": "dados",
                "itens": [
                    "Conversamos com o responsavel pelas armadilhas e com a responsavel pelo banco de casos de dengue.",
                    {
                        "texto": "As duas bases seguem caminhos diferentes.",
                        "sub": [
                            "Armadilhas: vem direto, sem comite de etica, porque mosquito nao e pessoa.",
                            "Casos de dengue: tem que passar pelo comite, porque envolve dado de gente.",
                        ],
                    },
                    {
                        "texto": "O banco de casos vale a espera: ele traz os casos separados por bairro.",
                        "sub": [
                            "E o que falta para o modelo por bairro fazer sentido.",
                            "O dado publico do SINAN nao tem bairro: 121 colunas e nenhuma de endereco.",
                        ],
                    },
                    {
                        "texto": "Mapeamos o caminho no comite de etica.",
                        "sub": [
                            "A submissao e uma so, feita pela UFRGS.",
                            "O orientador precisa ser o pesquisador responsavel; o aluno entra como assistente.",
                            "Antes dela falta o parecer da comissao de pesquisa do Instituto de Informatica.",
                        ],
                    },
                ],
            },
            {
                "titulo": "Coleta do dia",
                "itens": [
                    "Raspagem da captura de mosquito (semana 500): 112 exemplares.",
                ],
            },
        ],
        "proximos": [
            {
                "texto": "Retornar a ligacao no dia 10 e pedir a serie historica das armadilhas.",
                "sub": [
                    "No mesmo formato da nossa raspagem: uma linha por armadilha por semana.",
                    "Dizendo tambem se cada armadilha foi inspecionada ou nao na semana.",
                    "Mandar uma planilha nossa como modelo.",
                ],
            },
            {
                "texto": "Perguntar se a contagem de casos por bairro dispensa o comite de etica.",
                "sub": [
                    "Ja somada por semana e sem nome de ninguem.",
                    "Se dispensar, economiza meses.",
                ],
            },
            "Pedir para as duas areas usarem os mesmos nomes de bairro, senao da retrabalho para juntar as bases.",
            "Ligar para a comissao de pesquisa do Instituto de Informatica: (51) 3308-7760.",
            "Pedir ao orientador que se cadastre na Plataforma Brasil como pesquisador responsavel.",
            "Corrigir os tres erros de dado antes de rodar os modelos de novo.",
            "Corrigir a data do formulario de submissao, que esta como 2015.",
            "Copiar as semanas 497 a 500 da raspagem para o backup.",
        ],
    },
    {
        "data": "2026-07-28",
        "feito": [
            "A DVS (Assessoria de Ensino e Pesquisa) retornou e enviou o Termo de Anuencia assinado, liberando o seguimento do processo e a submissao ao Comite de Etica em Pesquisa (CEP).",
            "A DVS colocou em copia as areas responsaveis pela base do monitoramento do MI-Aedes e pelo banco de casos humanos notificados de dengue; as equipes tecnicas vao definir como compartilhar os dados.",
        ],
        "proximos": [
            "Submeter o projeto ao Comite de Etica em Pesquisa (CEP) com o Termo de Anuencia.",
            "Alinhar com as equipes tecnicas da DVS o formato de compartilhamento das bases (MI-Aedes e casos de dengue notificados).",
        ],
    },
    {
        "data": "2026-07-27",
        "feito": [
            "Novo contato por telefone com a Secretaria de Saude, porque a pessoa de contato nao respondeu sobre a liberacao dos dados.",
            "E-mail enviado para dvs@portoalegre.rs.gov.br, que em tese vai liberar os dados e conectar com o pessoal de dados da secretaria.",
            "Raspagem da captura de mosquito (semana 500): 42 exemplares.",
            "Diario de atividades reformado no painel: timeline com atividades realizadas e proximos passos, mais busca.",
        ],
        "proximos": [
            "Aguardar o retorno da Secretaria de Saude / DVS sobre a liberacao e a conexao com o pessoal de dados.",
            "Quando os dados oficiais chegarem, integrar a serie de casos na tabela_final.",
        ],
    },
    {
        "data": "2026-07-25",
        "feito": [
            "Raspagem da captura de mosquito (semana 499): 137 exemplares.",
        ],
        "proximos": [],
    },
    {
        "data": "2026-07-24",
        "feito": [
            "Painel publicado no GitHub Pages com o novo layout: menu em arvore, home enxuta, Metodologia, arvore de cenarios, dicionario de dados e versao para celular.",
            "Raspagem da captura de mosquito (semana 499): 116 exemplares.",
        ],
        "proximos": [],
    },
]


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
        "tipo": "Regressao",
        "rotulo": "Casos de dengue — previsao direta do numero de casos (sem El Nino, com corte de maturidade)",
        "titulo": "Quantos casos vao ter",
        "pergunta": "Quantos casos de dengue a cidade vai ter nas proximas semanas?",
        "descricao": "O modelo principal do trabalho. Usa clima e mosquito para prever o numero de casos, e deixa de fora as semanas mais recentes, que ainda estao sendo contadas e enganam.",
    },
    "cidade_regressao_com_enso": {
        "menu": "Com El Nino",
        "tipo": "Regressao",
        "rotulo": "Casos de dengue — previsao direta do numero de casos (COM dados de El Nino)",
        "titulo": "E se o El Nino entrar na conta?",
        "pergunta": "Somar o El Nino ao clima melhora a previsao?",
        "descricao": "A previsao principal, mas deixando o El Nino (o esquenta e esfria do oceano Pacifico) concorrer com o clima local.",
    },
    "cidade_regressao_sem_enso": {
        "menu": "Sem apagar semanas",
        "tipo": "Regressao",
        "rotulo": "Casos de dengue — previsao direta do numero de casos (sem corte de maturidade)",
        "titulo": "E sem apagar as semanas recentes?",
        "pergunta": "O que muda se a gente confiar nas semanas que ainda nao fecharam?",
        "descricao": "A previsao principal sem tirar as semanas recentes. Serve de comparacao para mostrar que deixar essas semanas de fora ajuda mesmo.",
    },
    "cidade_lift_vetor": {
        "menu": "O ganho do mosquito",
        "tipo": "Regressao",
        "rotulo": "Ganho do mosquito — compara so-clima x clima+mosquito x so-mosquito",
        "titulo": "O mosquito ajuda a prever?",
        "pergunta": "So clima, clima mais mosquito, ou so mosquito — o que preve melhor?",
        "descricao": "Compara os tres jeitos lado a lado para medir quanto a contagem de mosquito acrescenta a previsao.",
    },
    "cidade_diebold": {
        "menu": "E ganho de verdade?",
        "tipo": "Regressao",
        "rotulo": "Teste de significancia (Diebold-Mariano) — o ganho do mosquito e real?",
        "titulo": "Esse ganho e real ou foi sorte?",
        "pergunta": "A melhora que o mosquito traz aguenta um teste estatistico?",
        "descricao": "Poe o modelo so com clima contra o modelo com clima mais mosquito e testa (Diebold-Mariano) se a diferenca e real, e nao coincidencia.",
    },
    "comparacao_literatura": {
        "menu": "Contra a literatura",
        "tipo": "Regressao + Classificacao",
        "rotulo": "Nosso metodo x a literatura (Oliveira et al., so clima)",
        "titulo": "Como a gente se sai contra o metodo publicado",
        "pergunta": "Somando o mosquito, a gente bate o metodo publicado que usa so clima?",
        "descricao": "Recria um metodo ja publicado (Oliveira et al., so com clima) e coloca lado a lado com o nosso, que tambem usa o mosquito.",
    },
    "cidade_deteccao_surto": {
        "menu": "Vai ter surto?",
        "tipo": "Classificacao",
        "rotulo": "Vai ter surto? — sim/nao acima do limite de casos (teste de McNemar)",
        "titulo": "Vai ter surto ou nao?",
        "pergunta": "As proximas semanas vao passar do limite de surto?",
        "descricao": "Em vez de um numero, responde sim ou nao para “vai ter surto” e compara com um palpite simples para ver se acerta mais.",
    },
    "bairro_surto": {
        "menu": "Por bairro",
        "tipo": "Regressao",
        "rotulo": "Densidade de mosquito por bairro (nao ha casos de dengue por bairro)",
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
