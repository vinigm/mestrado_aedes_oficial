# modelagem_aedes

Pacote modular da modelagem preditiva de *Aedes aegypti* / surto de dengue em Porto Alegre.

Substitui os notebooks e scripts soltos (antes espalhados em `codigos/modelagens/modelo1|2|6`,
com imagem, `.py` e notebook na mesma pasta) por uma arquitetura em **camadas** — para
**escalar** os experimentos (cidade × bairro, regressão × detecção de surto) sem virar um
arquivo de 2000 linhas. Espelha o padrão do `otimizador_v2` (projeto Sortimento/Panvel).

## Estrutura

```
CÓDIGO:
  config/        settings (paths) + modelo.py (a ficha do algoritmo) + experimentos/<x>.py (o que muda por experimento)
  acesso/        todo o I/O de leitura isolado aqui (carregar tabela_final, infodengue, capturas...)
  dominio/       monta tabelas e features SEM modelar (montagem da tabela, features, features espaciais, surto)
  motor/         o motor agnóstico ao experimento (walk-forward, baselines)
  avaliacao/     métricas + testes estatísticos (regressão/classificação, McNemar, Diebold-Mariano)
  relatorio/     gráficos (graficos.py: as figuras dos experimentos)
  preparo/       consolida os dados crus (Marília + SINAN + raspagem) nos insumos da montagem
  pipeline.py    o "código pai": a sequência de etapas de cada experimento
  preparar_dados.py  CLI: prepara as fontes (Marília, SINAN, raspagem, clima e El Niño)
  montar.py      CLI: (re)gera a tabela_final a partir dos insumos das fontes
  main.py        CLI: roda um experimento (ex.: python main.py --experimento cidade_deteccao_surto)
  plotar.py      CLI: gera as figuras a partir dos CSVs de resultados
  tests/         testes rápidos (unidade) + validar_experimentos.py (equivalência end-to-end, lento)

DADOS (não código):
  dados/entradas/<fonte>/   uma subpasta por fonte (tabela_modelagem, infodengue_poa,
                            arquivos_secretaria_saude_poa, clima, bases_governo,
                            dados_marilia e juntar_arquivos_raspagem - as duas ultimas
                            fora do fluxo da tabela_final desde 16/08/2026, ver abaixo)
  dados/saidas/resultados/  CSVs de métricas gerados pelos experimentos
  dados/saidas/figuras/     gráficos gerados
```

## Como rodar

```bash
pip install -r requirements.txt

python preparar_dados.py                            # (opcional) prepara as fontes: Marília, SINAN, raspagem, clima, ENSO
python montar.py                                    # (re)gera dados/.../tabela_final.csv
python main.py --experimento <nome>                 # roda um experimento -> CSVs em dados/saidas/resultados
python plotar.py                                    # gera as figuras em dados/saidas/figuras

pytest tests -q                                     # testes rápidos (ou: python tests/test_montagem.py)
```

Experimentos disponíveis (`--experimento`):

```
cidade_deteccao_surto       "vai ter surto?" (sim/não) na cidade + McNemar
cidade_regressao            "quantos casos?" — Modelo 4c (sem ENSO, corte de maturidade)
cidade_regressao_sem_enso   idem, sem corte de maturidade (Modelo 4b)
cidade_regressao_com_enso   idem, com ENSO entre os candidatos de clima
cidade_lift_vetor           lift bruto do vetor (só-clima / clima+vetor / só-vetor)
cidade_diebold              teste de Diebold-Mariano (o lift do vetor é significativo?)
comparacao_literatura       nosso método × método da literatura (Oliveira et al.)
bairro_surto                previsão da densidade de mosquito por bairro
```

O fluxo fecha dentro do pacote: **`preparar_dados.py` → `montar.py` → `tabela_final` → `main.py` → resultados → `plotar.py`**.
Com dados novos, `preparar_dados.py` reconsolida as fontes e `montar.py` regenera a base.

## Princípio central

O **motor é agnóstico ao experimento** (walk-forward, features e métricas existem UMA vez).
O que é específico — quais features, qual alvo, limiar de surto, horizontes — vive em
`config/experimentos/<experimento>.py`. **Experimento novo = arquivo de config novo**, sem
mexer no motor. É o que resolve a duplicação antiga (o mesmo `walk_forward`/`montar_features`
estava copiado em quase todo script).

O motor também é **agnóstico ao algoritmo**. Qual modelo cada experimento usa vem de uma
ficha `EspecificacaoModelo` (`config/modelo.py`) — `nome`, `classe` (ex.: `LGBMRegressor`,
`RandomForestRegressor`) e `parametros`. O motor faz `modelo = config.modelo.criar()` e confia
só no `.fit()/.predict()` (a API padrão do scikit-learn, que LightGBM, XGBoost e sklearn seguem).

## Comparar algoritmos (LightGBM × RandomForest × ...)

Pra testar outro algoritmo, **não se mexe no motor** — cria-se um config apontando outra
`classe`. Exemplo pronto: [config/experimentos/cidade_regressao_rf.py](config/experimentos/cidade_regressao_rf.py)
é o mesmo `cidade_regressao` (4c) trocando LightGBM por RandomForest:

```bash
python main.py --experimento cidade_regressao       # 4c com LightGBM
python main.py --experimento cidade_regressao_rf    # 4c com RandomForest
```

Toda saída tem uma coluna **`algoritmo`** (o `nome` da ficha), então dá pra empilhar os dois
resultados e comparar lado a lado. Para uma comparação justa, mantenha o `modelo_selecao_clima`
igual nos dois (a escolha das colunas de clima fica constante; só o estimador varia).

## Versionar os experimentos (MLflow)

Cada `python main.py --experimento X` é **automaticamente versionado** com MLflow: registra o
modelo, os hiperparâmetros, métricas de resumo (MAE médio, R² médio...) e anexa os CSVs. Tudo
local, numa pasta `mlruns/` (sem servidor). A organização é:

- **experimento MLflow = cenário** (`cidade_regressao`, `bairro_surto`, ...)
- **run = modelo** (`lightgbm`, `random_forest`, ...)

Assim, `cidade_regressao` (LightGBM) e `cidade_regressao_rf` (RandomForest) caem no **mesmo**
experimento e você compara os modelos lado a lado. Pra ver na interface:

```bash
cd modelagem_aedes
MLFLOW_ALLOW_FILE_STORE=true mlflow ui --backend-store-uri "$PWD/mlruns"
# abra http://localhost:5000
```

O rastreamento vive só em `rastreamento.py` + `main.py` (o motor/domínio/pipeline continuam
cegos ao MLflow). Se o MLflow não estiver instalado, os experimentos rodam igual — só não
versionam.

## Experimentos (mapa do antigo → novo)

| Antigo (`py_pre_refatoracao/`) | Novo (experimento) | O que é |
|---|---|---|
| `deteccao_surto.py` | `cidade_deteccao_surto` | "vai ter surto?" na cidade + McNemar |
| `clima_enxuto_sem_enso_maturidade.py` | `cidade_regressao` | "quantos casos?" — Modelo 4c |
| `clima_enxuto_sem_enso.py` | `cidade_regressao_sem_enso` | idem, sem corte de maturidade (4b) |
| `clima_enxuto_vetor.py` | `cidade_regressao_com_enso` | idem, com ENSO nos candidatos |
| `lift_entomologico_limpo.py` | `cidade_lift_vetor` | lift bruto do vetor (3 conjuntos) |
| `diebold_mariano.py` | `cidade_diebold` | significância do lift (Diebold-Mariano) |
| `comparacao_literatura.py` | `comparacao_literatura` | nosso método × literatura (Oliveira) |
| `modelo2_porbairro/_enh.py` | `bairro_surto` | densidade de mosquito por bairro |

## Status da migração

- ✅ **Estrutura + dados**: pacote criado; dados realocados para `dados/entradas`; saídas
  (resultados/figuras) separadas do código.
- ✅ **Preservação**: todo o código antigo está em `../arquivos_antigos/` (nada foi apagado).
- ✅ **Upstream (montagem)**: `montar.py` regenera a `tabela_final` — verificado byte a byte.
- ✅ **Detecção + regressão 4c**: validados byte a byte contra o código antigo.
- ✅ **Família regressão + Diebold + comparação + bairro**: portados; equivalência verificada
  (números batem com o antigo, onde há resultado antigo).
- ✅ **Estilo**: todos os `.py` no padrão de linguagem simples + estética (ver
  `../../Contexto/CODIGOS...rtf` §17 e `../../Contexto/ARQUITETURA_MODELAGEM_AEDES.md`).
- ✅ **Preparo das fontes (`preparo/`)**: Marília, SINAN, raspagem, **clima (NASA POWER) e El Niño
  (ENSO)** portados pra módulos (`preparar_dados.py`) e validados — Marília/SINAN byte a byte; a
  raspagem reproduz o antigo exatamente e incorpora as semanas novas; clima/ENSO reproduzem o
  histórico exatamente (só as semanas mais recentes mudam, por revisão da própria NASA/NOAA).
- ✅ **Arquitetura completa**: o fluxo inteiro (preparo → montagem → experimentos → relatório) está
  em camadas, no padrão e verificado. (A captura de vegetação/MODIS e de feriados existe como script
  solto, mas não entra no modelo — fica como exploração futura.)

## Migração pra base certificada (16/08/2026)

O vetor da `tabela_final` passou a vir de uma fonte só: o parquet certificado da
Secretaria Municipal de Saúde de Porto Alegre (`dados/entradas/arquivos_secretaria_saude_poa/
secretaria_poa_armadilhas.parquet`, 2012 até hoje, uma linha por inspeção, sem dado
pessoal — ver `preparo/limpar_arquivos_secretaria.py` e `preparo/unificar_arquivos_secretaria.py`).
O próprio parquet já inclui 2026 em diante a partir da raspagem própria.

O que muda:

- **Sai do fluxo**: os dados da Marília (2019-2023) e a raspagem consolidada por fora
  (`juntar_arquivos_raspagem/`) não alimentam mais a `tabela_final`. As pastas continuam
  existindo (nada foi apagado) — só não são mais lidas por `montar.py`. A Marília continua
  usada pelo experimento `bairro_surto` (captura por bairro), que é outro fluxo.
- **Grade semanal contínua**: a `tabela_final` agora tem uma linha para TODA semana entre
  23/09/2012 e a última semana com dado, mesmo quando não houve nenhuma inspeção naquela
  semana (são 7 semanas: a virada de 2017/2018 e as três semanas da enchente de 2024) — essas
  ficam com as colunas do vetor vazias (NaN), sem interpolação nenhuma.
- **Densidade**: `aedes_aegypti_por_armadilha` passou a ser fêmeas de Aedes aegypti dividido
  pelas armadilhas REALMENTE inspecionadas na semana. De 2012 a 2018 a Secretaria ainda não
  registrava isso; nesses anos o denominador é aproximado (todas as armadilhas com QUALQUER
  registro na semana) e a coluna nova `denominador_aproximado` marca essas semanas.
- **Casos confirmados**: a série local do SINAN só começa em 2018 (antes fica NaN, nunca
  zero) e as últimas semanas do arquivo de casos (que ainda podem estar em apuração no SINAN)
  também ficam NaN em vez de zero — ver `JANELA_MATURACAO_CASOS_SEMANAS` em
  `dominio/montagem_tabela.py`.
- **Lags/médias móveis**: `dominio/features.py` não separa mais os cálculos "por bloco de
  fonte" — a série agora é uma grade semanal única e contínua (sem buraco de tempo entre
  secretaria e raspagem), então separar por bloco só introduziria um corte artificial onde
  não existe corte nenhum.
- **Coluna `fonte`**: passou a significar `secretaria` ou `raspagem` (era `marilia`/`raspagem`).
