"""

Aqui ficam as configuracoes gerais da modelagem: os caminhos dos arquivos e uns numeros fixos que valem pra tudo.

Tudo que NAO muda de um teste pro outro fica aqui. Os caminhos sao montados a partir de onde este arquivo esta salvo, entao da pra mover a pasta do projeto inteira pra outro lugar que nada quebra.

O que MUDA de um experimento pro outro (quais colunas entram no modelo, o que ele tenta prever, o limite pra contar como surto, quantas semanas ele tenta prever na frente) fica em config/experimentos/<experimento>.py, e nao aqui.

"""

from pathlib import Path

# Este arquivo esta em modelagem_aedes/config/settings.py, entao subindo uma pasta (parents[1]) a gente chega em modelagem_aedes/
PASTA_PROJETO = Path(__file__).resolve().parents[1]

PASTA_DADOS = PASTA_PROJETO / "dados"
PASTA_ENTRADAS = PASTA_DADOS / "entradas"   # tem uma pasta pra cada fonte de dados
PASTA_SAIDAS = PASTA_DADOS / "saidas"
PASTA_RESULTADOS = PASTA_SAIDAS / "resultados"   # as tabelas de resultado que cada experimento gera
PASTA_FIGURAS = PASTA_SAIDAS / "figuras"         # os graficos que os experimentos geram


# --- Fontes de dados (cada uma tem sua pasta dentro de dados/entradas) ---

# Tabela semanal com tudo junto (mosquito, clima, casos e El Nino/La Nina); e o que os modelos da cidade tentam prever.
CAMINHO_TABELA_FINAL = PASTA_ENTRADAS / "tabela_modelagem" / "tabela_final.csv"

# Dados do InfoDengue de Porto Alegre (casos e clima, semana a semana, desde 2010, sem ajuste pra atraso de notificacao).
CAMINHO_INFODENGUE = PASTA_ENTRADAS / "infodengue_poa" / "infodengue_poa_dengue.csv"

# Capturas de mosquito por armadilha (dados da Marilia, 2019 a 2023, 68 bairros).
PASTA_DADOS_MARILIA = PASTA_ENTRADAS / "dados_marilia"

# Outras fontes de dados (ainda como vieram, antes de virarem tabelas prontas pra usar).
PASTA_CLIMA = PASTA_ENTRADAS / "clima"
PASTA_SINAN_NACIONAL = PASTA_ENTRADAS / "bases_governo"
PASTA_RASPAGEM_CONSOLIDADA = PASTA_ENTRADAS / "juntar_arquivos_raspagem"

# Os arquivos .xlsx CRUS da raspagem (os DADOS QUE NAO PODEM SER PERDIDOS). Ficam
# fora do pacote, na pasta Raspagem do projeto. A consolidacao SO LE esses arquivos;
# nunca escreve nem apaga nada aqui.
PASTA_RASPAGEM_ARQUIVOS = PASTA_PROJETO.parent / "Raspagem" / "Arquivos"


# --- Pecas que entram na montagem da tabela_final (arquivos que cada fonte ja deixou prontos) ---
# Cada arquivo e feito por um script de captura ou processamento dentro da pasta da sua fonte; quem so junta tudo na tabela_final e o arquivo dominio/montagem_tabela.py.
CAMINHO_RASPAGEM_CONSOLIDADA = PASTA_RASPAGEM_CONSOLIDADA / "output" / "base_armadilhas_concatenada.csv"
CAMINHO_MARILIA_CONSOLIDADA = PASTA_DADOS_MARILIA / "output" / "base_dados_marilia.csv"
CAMINHO_CLIMA_SEMANAL = PASTA_CLIMA / "output" / "clima_nasa_power_semanal.csv"
CAMINHO_CASOS_NIVEL_CASO = PASTA_SINAN_NACIONAL / "output" / "casos_confirmados_poa.csv"
CAMINHO_ENSO = PASTA_CLIMA / "output" / "enso_mensal.csv"


# Monta o caminho do arquivo de capturas de mosquito da Marilia de um ano especifico (2019 a 2023).
def caminho_capturas_marilia(ano: int) -> Path:
    return PASTA_DADOS_MARILIA / f"saida_{ano}.csv"


# --- Numeros fixos que valem pra todos os experimentos ---

# Quantidade de semanas que o ano tem, contando do jeito que a saude publica conta (semana epidemiologica); usado pra ensinar o modelo que a epoca do ano se repete todo ano, dando a volta (a semana 52 fica perto da semana 1).
SEMANAS_POR_ANO = 52

# Quantidade minima de semanas que o modelo precisa ver antes de comecar a prever (o modelo treina no passado e preve o futuro, semana a semana); da mais ou menos 2 anos de historico.
MINIMO_SEMANAS_TREINO = 104
