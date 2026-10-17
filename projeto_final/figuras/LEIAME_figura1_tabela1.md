# Tabela 1, Figura 1 e Figura S1 definitivas (geradas pelo pacote)

**Gerado em 16/10/2026.** Substitui as versões preliminares de 10/10/2026 (Tabela 1 escrita à mão; figuras de
`analises/2026-10-10_figura1_preliminar/gerar_figura1.py`, que continua intocado).

## O que gera, de onde lê

| Script | Lê | Escreve |
|---|---|---|
| `gerar_tabela1.py` | `aedes/configuracao.py` + `dados/tabela_final.csv` | `entregas/artigo/tabelas/tabela1_variaveis.tex` (mesmo formato da preliminar, `\label{tab:variaveis}`) |
| `gerar_figura1.py` | `aedes/configuracao.py` + `dados/tabela_final.csv` | `figuras/figura1_series.{pdf,png}` e `figuras/figuraS1_clima.{pdf,png}`; os PDFs são copiados para `entregas/artigo/figuras/` |

- **Tabela de entrada:** `dados/tabela_final.csv`, sha256 `6f34b8549009c01b39b8080b904ef69af5d209ebbcbdba9357a708fd044f6f1f`
  (725 × 36). Os dois scripts passam os bytes por `aedes.dados.montar_tabela_a_partir_dos_bytes`, que PARA se o hash ou o
  esquema divergirem; depois aplicam o corte de maturidade (uma vez, como em todo o pacote).
- **Rodar:** `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B figuras/gerar_tabela1.py` (idem `gerar_figura1.py`).
- **Reprodutível:** rodar duas vezes dá os mesmos bytes (PDF sem data de criação).
- **Nenhum código antigo é importado.** O gabarito de desenho só foi lido.

## O que sai da configuração e o que sai dos dados

- **Da configuração (`aedes.configuracao`):** os 22 nomes e a contagem por bloco (casos 6, clima 6, vetor 6, calendário 4),
  as defasagens (1 a 4) e a janela da média móvel (4) de casos e vetor, as 6 colunas de clima congeladas e as defasagens
  de cada uma (temperatura média 3 e 4; temperatura máxima e umidade sem defasagem; pressão 3 e 4), a primeira e a última
  semana-alvo avaliadas (07/01/2024 e 01/02/2026).
- **Dos dados:** o período de cada fonte, e o início do gráfico (primeira semana com caso: 18/02/2018).
- **Âncoras conferidas pelo script (ele para se divergir):** 6 + 6 + 6 + 4 = 22; 416 semanas no gráfico; 18/02/2018 a
  01/02/2026. **Conferido à parte (leitura):** treino inicial de 104 semanas, origens de 18/03/2018 a 08/03/2020
  (matriz h = 1, 399 linhas).

## Decisão sobre o "período de cada fonte" (⚠️ ponto de método)

- **Recorte usado:** da primeira semana com caso (18/02/2018) até a última semana-alvo avaliada (01/02/2026). É a janela
  de dados que o modelo de fato enxerga; antes de 18/02/2018 nenhuma linha da matriz existe (sem caso), e depois de
  01/02/2026 as semanas foram descartadas.
- **Resultado:** casos, clima e vetor saem todos **fev/2018 a fev/2026**.
- **Alternativa (não adotada):** o período da série inteira, sem recorte. Casos 18/02/2018 a 26/04/2026 (428 semanas),
  clima 23/09/2012 a 09/08/2026 (725 semanas), vetor 23/09/2012 a 09/08/2026 (718 semanas; 7 sem vistoria). É o que a
  preliminar escrevia para clima e vetor ("set/2012 a ago/2026"). Se a banca ou o orientador preferir mostrar o que a
  Secretaria cedeu (e o texto de Dados já diz "setembro de 2012 a agosto de 2026" para a base de vistorias), basta trocar
  as constantes do recorte em `gerar_tabela1.py`.
- **Ressalva:** a seleção das 6 colunas de clima usou a série de clima desde 2012 (fora do walk-forward; limitação já
  declarada no Método). Isso não muda o período que alimenta as matrizes.

## Diferenças para as versões preliminares

- **Tabela 1:** só os períodos de Meteorologia e Vetor mudam (de "set/2012 a ago/2026" para "fev/2018 a fev/2026").
  Casos, variáveis, contagens, colunas e rótulos são idênticos; mudam só o comentário do topo e a quebra de linha da legenda.
- **Figuras 1 e S1:** os PNGs novos são **idênticos, pixel a pixel** (0 pixels diferentes, mesmas dimensões), aos
  preliminares: mesmos dados, período (416 semanas, fev/2018 a fev/2026), faixa da avaliação (07/01/2024 a 01/02/2026),
  eixos e anos em todos os painéis. O que muda é a procedência: tabela certificada do pacote, período e faixa lidos da
  configuração, e PDF sem data de criação.

## Impressões digitais das saídas (16/10/2026)

- `tabela1_variaveis.tex` `0cb81424...` · `figura1_series.pdf` `680f2790...` · `figuraS1_clima.pdf` `c6d83db3...`
- Manifesto do código antigo antes e depois: `manifesto_antigo_2026-10-16_antes.csv` e `..._depois.csv` (a pasta
  `arquivos_secretaria_saude_poa/` e o CSV do Sinan 2010-2022 entram só com tamanho e data: **não foram abertos**).
- A preliminar da Tabela 1 está em `entregas/artigo/_arquivo/2026-10-16_antes_v1/`.

## Pendente (fora do escopo desta tarefa)

- ⏳ Trocar `figura1_series_preliminar.pdf` e `figuraS1_clima_preliminar.pdf` pelos nomes novos em `secoes/03_dados.tex`
  e `suplementar.tex`, e tirar os avisos `\pendente{...}`.
