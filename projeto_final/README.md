# projeto_final

Pacote **novo e reprodutível** do mestrado (PPGC/UFRGS): previsão semanal de casos confirmados de dengue em Porto Alegre,
de 1 a 12 semanas à frente, com `HistGradientBoostingRegressor` (quantil 0,85) e walk-forward com corte do treino pela
data da **resposta**. Ele gera, do zero, os números, tabelas e figuras do artigo e da dissertação.

Criado em 12/10/2026 (ciclo 0). Desenho e ordem de construção: [DESENHO.md](DESENHO.md).

## Aviso de ambiente (ler antes de rodar qualquer coisa)

- Use **sempre `python3`** (o do sistema, **Python 3.14.4**). **Nunca o `.venv`** do projeto antigo: ele tem
  scikit-learn 1.9.0, que muda os resultados em silêncio.
- As versões estão **fixadas** (`==`) em [requirements.txt](requirements.txt) e conferidas por `testes/test_ambiente.py`.
  Versão diferente = o teste falha com mensagem clara. Pare e corrija o ambiente antes de seguir.
- Rode a partir de dentro desta pasta (`projeto_final/`), sem `sys.path.insert` e sem instalar o pacote.

## Como reproduzir, do zero, na ordem

1. **Entre na pasta:** `cd projeto_final`
2. **Confira o ambiente:** `python3 --version` deve imprimir `Python 3.14.4`. Se faltar pacote, instale as versões exatas:
   `python3 -m pip install -r requirements.txt`
3. **Rode os testes** (ambiente, hash e forma da tabela; unidades e testes diferenciais; cobre os ciclos 0 a 3):
   `PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -p no:cacheprovider`
4. **Os dados** já estão em `dados/tabela_final.csv`. A execução parte dela; se o hash não bater, para.
   Verificação manual: `cd dados && shasum -a 256 -c tabela_final.sha256` (deve imprimir `OK`).
5. **Experimentos:** cada um grava em `resultados/<nome>/`. A referência (ciclo 3) é
   `OMP_NUM_THREADS=1 python3 -B -m experimentos.referencia` (~8 min; seção Ciclo 3 abaixo).

## O que é cada pasta

| Pasta / arquivo | O que é | Estado no ciclo 0 |
|---|---|---|
| `dados/tabela_final.csv` | Única entrada do pacote: agregado semanal (725 linhas × 36 colunas), snapshot certificado em 26/09/2026 | ✅ copiada |
| `dados/tabela_final.sha256` | Hash esperado; a execução para se não bater | ✅ |
| `dados/PROVENIENCIA.md` | De onde cada coluna vem, como a tabela foi gerada e o que **não** é reproduzível | ✅ |
| `aedes/` | O pacote: funções puras, sem leitura nem escrita de arquivo | ✅ `configuracao.py` e `dados.py` (ciclo 1); ✅ `variaveis.py` e `corte_temporal.py` (ciclo 2, parte 1); ✅ `walk_forward.py` (ciclo 2, parte 2); ✅ `metricas.py` (ciclo 3) |
| `experimentos/` | Um script por resultado do texto; lê dados e grava em `resultados/` | ✅ `trava_walk_forward.py` (ciclo 2); ✅ `referencia.py` (ciclo 3) |
| `resultados/` | CSVs gerados pelos experimentos (pequenos) | ✅ `ciclo2/previsoes_trava.csv`; ✅ `referencia/` (previsões, métricas, log, parciais) |
| `figuras/` | Figuras do artigo e da dissertação, geradas por script | ⏳ vazio |
| `testes/` | Ambiente e dados (ciclos 0 e 1); variáveis, corte e walk-forward (ciclo 2); métricas, réguas e referência completa (ciclo 3) | ✅ ciclos 0 a 3 |
| `DESENHO.md` | Desenho aprovado em 09/10/2026 | ✅ só leitura |
| `mapa_do_codigo_antigo_*.md`, `PREPROCESSAMENTO_mapa_*.md` | Evidência que originou o desenho e a proveniência | ✅ só leitura |

## Ciclo 1: dados

Carga validada e corte de maturidade, em `aedes/configuracao.py` (`ConfiguracaoDados`, imutável, `CONFIGURACAO_DADOS`) e
`aedes/dados.py` (funções puras: recebem bytes ou DataFrame, nunca abrem arquivo).

- **Carga:** `montar_tabela_a_partir_dos_bytes` confere o sha256 (`validar_impressao_digital`), lê o CSV com a data convertida
  e valida o esquema (`validar_esquema`): 725 × 36, colunas obrigatórias, domingos, grade semanal contínua desde 23/09/2012
  sem buraco nem duplicata, colunas numéricas, casos sem infinito nem negativo.
- **Corte de maturidade** (`aplicar_corte_de_maturidade`): contando da **última semana com caso** (não do fim da tabela),
  apaga (NaN, nunca 0) os casos com `data > última − 12 semanas`. Só a coluna de casos muda. Réplica exata de
  `modelagem_aedes/dominio/surto.py` L12-50. Não é idempotente: age **uma vez**, sobre a tabela crua.
- **Âncoras conferidas:** 428 semanas com caso (18/02/2018 a 26/04/2026) → 416 depois do corte; última mantida
  **01/02/2026**, primeira apagada **08/02/2026**; igualdade exata com `testes/referencia_antiga/serie_casos_apos_corte.csv`.
- **Testes:** `testes/test_dados_unidade.py` (tabelas sintéticas, casos-limite) e `testes/test_diferencial_dados.py`
  (contra o gabarito do código antigo, sem tolerância).

## Ciclo 2, parte 1: variáveis e corte temporal (sem treinar modelo)

- **`aedes/configuracao.py`** ganhou 3 configurações imutáveis: `ConfiguracaoVariaveis` (defasagens 1 a 4, média móvel de 4,
  as 6 colunas de clima congeladas por nome com a defasagem de cada uma, e os nomes e a ORDEM das 22 variáveis),
  `ConfiguracaoModelo` (`FOLHA_5` e `FOLHA_20`; todos os 15 parâmetros do HistGradientBoosting escritos, inclusive os que o
  código antigo deixava no padrão do sklearn, como `early_stopping="auto"`) e `ConfiguracaoAvaliacao` (horizontes 1 a 12,
  treino mínimo de 104 semanas, retreino semanal, calibração até 31/12/2023, avaliação de 07/01/2024 a 01/02/2026).
  **Sem estado global:** as defasagens e as colunas são parâmetros, não variável de módulo trocada em execução.
- **`aedes/variaveis.py`** (`montar_matriz_do_horizonte`): da tabela cortada e do horizonte h devolve `data_origem`,
  `data_alvo`, as 22 variáveis e `y_h`; descarta (`dropna`) toda linha com ausente. Exige grade semanal contígua.
- **`aedes/corte_temporal.py`** (`selecionar_treino_ja_respondido`): treino só com as linhas cuja resposta já existia na
  origem do teste (`data_origem + h semanas <= t`).
- **Âncoras conferidas:** 399 linhas válidas em h=1 até 388 em h=12; 1ª origem 18/03/2018; 105ª linha (1ª origem de teste)
  15/03/2020, que bate com a 1ª previsão salva (`data_alvo` 22/03/2020 em h=1); 102 semanas avaliadas por horizonte.
- **Testes:** `test_variaveis_diferencial.py` (12 matrizes idênticas ao gabarito, tolerância absoluta 1e-12),
  `test_corte_temporal.py`, `test_variaveis_unidade.py`, `test_configuracao_ciclo2.py`.

## Ciclo 2, parte 2: o walk-forward (treina modelo)

- **`aedes/walk_forward.py`** (`executar_walk_forward`): laço único e puro. Recebe a matriz do horizonte, o horizonte, a
  `ConfiguracaoModelo` e a `ConfiguracaoAvaliacao`; devolve `h`, `data_origem`, `data_alvo`, `real`, `previsto`. A cada origem `t`
  (da 105ª linha em diante, passo 1) treina um modelo NOVO só com `selecionar_treino_ja_respondido` e prevê a linha de `t`
  (previsão para `t + h`). Variáveis = colunas da matriz fora as datas e `y_h`, na ordem da matriz. Sem estado global.
- **`experimentos/trava_walk_forward.py`**: h=1 e h=12, folha 5 (`referencia`) e folha 20 (`HistGB_folha20_M1`). Roda em ~7 min
  com as threads padrão (0,25 a 0,5 s por retreino, 284 a 295 retreinos por horizonte): em segundo plano,
  `PYTHONDONTWRITEBYTECODE=1 nohup python3 -B -m experimentos.trava_walk_forward > resultados/ciclo2/trava_walk_forward.log 2>&1 &`.
  Grava `resultados/ciclo2/previsoes_trava.csv` (1.158 linhas).
- **Resultado da trava (12/10/2026):** as 1.158 previsões são **idênticas** ao gabarito do código antigo (diferença máxima de
  `previsto` = 0,0 nos 4 conjuntos); MAE na janela de 102 semanas: folha 5 = 97,987 (h=1) e 278,818 (h=12); folha 20 = 133,626 e 243,765.
- **Testes:** `test_walk_forward_diferencial.py` (contra `previsoes_referencia.csv`; é **pulado** se a trava ainda não rodou) e
  `test_walk_forward_unidade.py` (dados sintéticos: treino nunca vê `data_alvo > t`, nº de previsões, retreino do zero,
  determinismo, buraco na grade, validações).

## Ciclo 3: métricas, réguas e a referência completa (12 horizontes × folhas 5 e 20)

- **`aedes/metricas.py`** (funções puras): `erro_absoluto_medio`, `r_quadrado`, `previsao_regua_sazonal` (casos em `data_alvo − 52 semanas`),
  `previsao_persistencia` (casos em `data_alvo − h semanas`, a semana de origem), `montar_previsoes_das_reguas` (as réguas na **mesma grade
  (h, data_alvo)** do braço `referencia`; semana sem régua sai da conta e o `n` mostra), `recortar_janela_de_avaliacao` e
  `resumir_na_janela_de_avaliacao` (MAE, R² e `n` por braço e horizonte). Réplica de `analises/2026-09-25_regua_regras_simples/calcular_regua.py`
  (L490-534 réguas, L582-673 pareamento, L747-785 métricas). Entrada com ausente ou infinito **levanta erro**; R² de série real constante segue a
  convenção do sklearn (1,0 se o erro é zero, senão 0,0), e com menos de 2 pontos é NaN, como no código antigo.
- **`experimentos/referencia.py`** grava em `resultados/referencia/`: `previsoes.csv` (6.948 linhas: h, data_origem, data_alvo, real, previsto,
  braco), `metricas.csv` (MAE, R², n por braço e h; braços `referencia` = folha 5, `HistGB_folha20_M1` = folha 20, `regua_sazonal`,
  `persistencia`), `referencia.log` e `parciais/` (um CSV por folha e horizonte, escrita atômica).
- **Como reproduzir:** de dentro de `projeto_final/`, **`OMP_NUM_THREADS=1`** e `python3 -B`. A rodada toda cabe em ~8 min, em dois processos:
  ```
  export OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
  nohup python3 -B -m experimentos.referencia --folha 5  > /dev/null 2>&1 &
  nohup python3 -B -m experimentos.referencia --folha 20 > /dev/null 2>&1 &
  tail -f resultados/referencia/referencia.log     # a junção acontece sozinha quando os 24 parciais existem
  ```
  Em pedaços de primeiro plano: `--folha 5 --horizontes 1 2 3` (cada pedaço < 3 min). `--so-juntar` só junta e mede.
- **Quanto leva (medido em 12/10/2026, 10 núcleos):** 12,4 min de CPU somados (folha 5: ~34-50 s por horizonte; folha 20: ~21-33 s), **7,5 min** de relógio
  com 2 processos. ⚠️ **`OMP_NUM_THREADS=1` é ~7× mais rápido** que o padrão (0,07 s contra 0,49 s por retreino: com 10 threads o custo de coordenar
  as threads domina em 300 linhas) e dá resultado **idêntico** (diferença 0,0 medida em 10 retreinos). Sem a variável, a rodada leva ~40 min.
- **Resultado (12/10/2026):** as 6.948 previsões são **idênticas** ao gabarito do código antigo (diferença máxima de `previsto` e de `real` = 0,0
  nos 2 braços × 12 horizontes); MAE e R² idênticos a `metricas_ancora.csv` (diferença 0,0). Janela de avaliação 07/01/2024 a 01/02/2026, n = 102 em todo h.

  | h | folha 5: MAE / R² | folha 20: MAE / R² | régua sazonal: MAE | persistência: MAE |
  |---|---|---|---|---|
  | 1 | 97,987 / 0,898 | 133,626 / 0,834 | 202,108 | 83,294 |
  | 4 | 219,669 / 0,628 | 199,635 / 0,717 | 213,176 | 278,951 |
  | 8 | 272,627 / 0,450 | 223,183 / 0,576 | 216,167 | 530,971 |
  | 12 | 278,818 / 0,437 | 243,765 / 0,558 | 217,784 | 697,490 |

- **Testes:** `test_metricas_unidade.py` (40 casos: sklearn, série constante, ausente, régua sem ano anterior, janela, pareamento) e
  `test_referencia_diferencial.py` (previsões 12 h × 2 braços iguais ao gabarito por (h, data_alvo, braco), tol. 1e-9; métricas iguais às âncoras,
  tol. 1e-6; réguas iguais às âncoras do código antigo, tol. 0,05, e refeitas do zero com laço simples sobre a série do gabarito; métricas
  refeitas com sklearn sobre as previsões do gabarito). Pulado se `resultados/referencia/` não existe. Suíte inteira: **479 testes passam**.

## O que o pacote NÃO contém (decisão de 09/10/2026)

- **Nenhum dado cru da Secretaria Municipal de Saúde** nem derivado dele que localize residência. São de acesso restrito, sob
  guarda da Secretaria.
- **Nenhum microdado individual do Sinan** (quase-identificadores). O pacote usa só a contagem semanal que já está na tabela.
- **Nenhum script que trate dado cru.** A geração da tabela é **descrita** em `dados/PROVENIENCIA.md`, não reexecutada.

## Âncora de toda a construção

O experimento `referencia.py` (ciclo 3, ✅ reproduzido com diferença 0,0) reproduz, sobre o mesmo snapshot, 102 semanas-alvo por horizonte
(07/01/2024 a 01/02/2026): MAE 98,0 · 219,7 · 272,6 · 278,8 e R² 0,898 · 0,628 · 0,450 · 0,437 para h = 1, 4, 8, 12.
Tolerância do desenho: 0,2 no MAE e 0,003 no R² (na prática, 0,0). Se não bater: para, investiga, registra.
