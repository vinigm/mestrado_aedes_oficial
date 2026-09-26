# CORREÇÕES PENDENTES — DOCUMENTACAO_COMPLETA.md

> Consolidação de 5 verificadores independentes (conceitos, dados-modelos, hipoteses-resultados,
> literatura-alarme, coerencia) sobre as ~94 mil palavras de `documentacao_completa/`. Ordenado por
> gravidade. Cada item cita arquivo, trecho, o que está escrito × o que deveria estar, e a fonte que decide.

---

## 🔴 GRAVES (6)

### 1. Contradição interna: alarme de 1 mês descrito como "com significância" quando a própria Parte 4 reporta p NÃO significativo

- **Arquivo:** `partes/04_modelos.md`, linhas 2056-2058.
- **Está escrito:** "✅ FATO — em 1 mês, o quadro se inverte... o cenário adotado vence tanto a régua
  sazonal quanto a régua de 'hoje já passou', em erro pontual (MAE) e em desempenho de alarme (Youden de
  0,94), **com significância estatística onde ela foi testada**."
- **Deveria estar:** a vitória em MAE/WIS tem significância; a vitória em **alarme/Youden** em h=4 **não
  tem** — a própria Parte 4, ~150 linhas antes (linha 1861), reporta p de Holm **0,103** (× "hoje já
  passou") e **1,000** (× "o ano passado"), ambos rotulados **NÃO**. A frase generaliza "significância"
  para uma comparação (alarme) que não passou no mesmo documento.
- **Fonte que decide:** a própria tabela em `04_modelos.md` linha 1861 (`mcnemar_holm.csv`).
- **Gravidade:** 🔴 — contradição interna na mesma parte, no padrão exato de erro mais grave sinalizado.

### 2. V1_alvo_log: 23,0% de redução citado contra o controle, mas é redução contra a régua sazonal — contra o controle o erro PIORA 9,90%

- **Arquivo:** `partes/05_hipoteses.md`, linhas 758-761 (item "1. `V1_alvo_log`").
- **Está escrito:** "Em h=12, é uma redução de **23,0%** frente ao **controle** (o próprio HistGB folha 20
  sem essa transformação) — mas ainda não bate a régua sazonal."
- **Deveria estar:** contra o controle B0, o V1_alvo_log **piora 9,90%** (243,76 → 267,90). Os 23,0%/23,01%
  são a perda contra a **régua sazonal** (217,78), não contra o controle. Não há "redução" nenhuma contra
  o controle — é o oposto.
- **Fonte que decide:** `analises/2026-09-25_bateria_formulacao_do_alvo/saidas/familia_f1_variante_vs_b0.csv`
  (V1_alvo_log h=12: referência 243,76 → variante 267,90, redução −9,90%) e
  `familia_f2_variante_vs_regua_sazonal.csv` (referência 217,78, redução −23,01%).
- **Nota:** a Parte 4 (`04_modelos.md` linha ~1035) usa o número certo (9,9% pior que B0) — o erro **não**
  se propagou para lá, só para a Parte 5.

### 3. "Pares avaliados" errado na tabela de erro por horizonte — deveria ser n=102 nos 4 horizontes, não 295/292/288/284

- **Arquivos:** `partes/08_resultados.md` linhas 129-132 **e** `partes/04_modelos.md` linha 154-156
  (mesmo erro, propagado).
- **Está escrito:** tabela lista "Pares avaliados" = 295 / 292 / 288 / 284 para h=1/4/8/12.
- **Deveria estar:** **n=102** nos 4 horizontes — é o valor que reproduz exatamente os MAE (98,0/219,7/
  272,6/278,8) e R² (0,898/0,628/0,450/0,437) citados nas mesmas tabelas.
- **Fonte que decide:** `analises/2026-09-25_regua_regras_simples/saidas/conferencia_ancoras_numericas.csv`
  e `metricas_por_horizonte_e_periodo.csv`; confirmado em
  `analises/2026-09-25_comparacao_direta_literatura/metricas_do_projeto.csv` (R²=0,8979137481774447 em
  h=1, n=102).

### 4. Bootstrap por blocos da Seção 15.3 é do evento E_421, mas o texto o apresenta como parte do mesmo "FATO" do evento E_100

- **Arquivo:** `partes/02_conceitos.md`, Seção 15 (linhas 1054-1088).
- **Está escrito:** um único bloco "FATO (medido em 26/09/2026)" mistura a contagem de blocos do evento
  E_100 (39 semanas, 2 blocos, maior bloco de 20 — linhas 1062-1065, correta) com as razões
  p_bootstrap/p_nominal citadas na sequência (0,0001-0,82 contra "hoje já passou"; 1,10-1,51 e 2,11-3,44
  contra "o ano passado" — linhas 1080-1088), como se fossem sobre o mesmo evento de limiar 100.
- **Deveria estar:** as razões de bootstrap citadas pertencem TODAS ao evento **E_421** (limiar de Alerta),
  não ao E_100 — não existe no repositório nenhum bootstrap por blocos rodado especificamente para o
  limiar de 100 casos. A ligação precisa de uma ressalva explícita de que a contagem de blocos (E_100) e as
  razões de p-valor (E_421) vêm de análises de limiares diferentes.
- **Fonte que decide:** `analises/2026-09-26_varredura_limiar_de_decisao/saidas/bootstrap_inflacao_p.csv`
  (todas as linhas são E_421) × `metricas_estagios_oficiais.csv` (confirma 39 semanas/2 blocos/maior 20
  para E_100).

### 5. Especificidade calculada dá 0,969, mas o valor real na fonte é 0,971 — a conta didática (arredondar antes de subtrair) diverge do dado bruto

- **Arquivos:** `partes/02_conceitos.md` linha 856 **e** `partes/09_argumentos.md` linha 243 (mesmo erro,
  propagado nos dois lugares).
- **Está escrito:** "Especificidade = J − Sensibilidade + 1 = 0,94 − 0,971 + 1 = 0,969".
- **Deveria estar:** a especificidade real (h=4, cenário adotado, evento >100, avaliação 2024+) está
  direto na fonte, sem precisar derivar: **0,9705882352941176** (≈97,1%), não 0,969 (96,9%). O erro nasce
  de arredondar Youden (0,9412→0,94) e sensibilidade (0,9706→0,971) antes de subtrair — a conta "didática"
  produz um número que diverge do valor disponível na mesma fonte.
- **Fonte que decide:**
  `analises/2026-09-25_alarme_contra_canal_endemico/saidas/metricas_por_regra.csv` (linha
  `E_100,-,M_adotado,4,avaliacao_2024_mais`).
- **Gravidade:** diferença pequena (~0,2pp), mas é um número apresentado como resultado de derivação que
  não bate com a própria fonte citada, repetido em duas partes.

### 6. Grupo clima tem 22 colunas brutas, não 20 — a conta "20+20+2=42" esconde 2 colunas que já estavam nas 22

- **Arquivo:** `partes/03_dados.md`, §3.4.3, linhas 411-415.
- **Está escrito:** "o grupo clima tem 42 colunas candidatas — as **20 colunas brutas** de clima listadas
  em 3.4.2 mais... 20 defasagens adicionais, totalizando 20 + 20 + 2 = 42".
- **Deveria estar:** **22** colunas brutas, não 20. A própria tabela do documento em §3.4.2 (linhas 374-379)
  soma chuva (4) + temperatura (4) + umidade (6) + pressão (3) + radiação (3) + vento (2) = **22**. O total
  final (42) está certo, mas só fecha porque o texto tira artificialmente `temp_amplitude_media` e
  `dias_de_chuva` do grupo bruto e as soma à parte como "+2" — elas já estavam nas 22.
- **Fonte que decide:** tabela do próprio documento (§3.4.2) + reprodução de `dominio/features.py` +
  `dominio/selecao_features.py` sobre `tabela_final.csv` atual (`colunas_clima` = 42 itens = 22 sem
  defasagem + 20 com defasagem de 5 variáveis × 4 lags).
- **Sugestão de reescrita:** "22 colunas brutas (das quais 5 recebem 4 defasagens cada = +20; as outras 17,
  incluindo `temp_amplitude_media` e `dias_de_chuva`, entram só sem atraso)".

---

## ⚠️ MÉDIOS (4)

### 7. Youden arredondado para cima em dois pontos (h=12): 0,81 e 0,12 deveriam ser 0,80 e 0,11

- **Arquivo:** `partes/08_resultados.md`, linhas 601-603.
- **Está escrito:** Youden de "o ano passado passou de 100" em h=12 = **0,81**; Youden de "hoje já passou
  de 100" em h=12 = **0,12**.
- **Deveria estar:** fonte dá 0,8046398046398044 → arredonda para **0,80** (não 0,81); e
  0,11477411477411481 → arredonda para **0,11** (não 0,12). Erro de arredondamento na casa decimal, valores
  na fronteira.
- **Fonte que decide:**
  `analises/2026-09-25_alarme_contra_canal_endemico/saidas/metricas_por_regra.csv`
  (`R_ano_passado,12,avaliacao_2024_mais` e `R_hoje,12,...`).

### 8. Âncora do V3 descrita como "próxima do teto do treino" quando na verdade está ACIMA do teto (extrapolação, não proximidade)

- **Arquivo:** `partes/05_hipoteses.md`, linhas 768-769.
- **Está escrito:** "a diferença aprendida multiplicou um crescimento observado de 9,5 vezes por uma âncora
  **já próxima do teto do treino** [879]".
- **Deveria estar:** a âncora (**1.109** casos, semana de 23/03/2025) está **acima** do máximo visto no
  treino (1.109 > 879) — é **extrapolação para fora da faixa treinada**, não proximidade do teto. É essa
  extrapolação, não a proximidade, que causa a explosão (1.109 × 9,5 ≈ 10.524).
- **Fonte que decide:** `analises/2026-09-25_bateria_formulacao_do_alvo/README.md` §4.
- **Por que importa:** sugere ao leitor a causa errada do problema ("estar perto do limite" vs "estar fora
  dele").

### 9. Referências cruzadas quebradas para CRPS, RMSE e valor-p em `06_literatura.md` — as fórmulas nunca são formalizadas onde o texto promete

- **Arquivo:** `partes/06_literatura.md`, linhas 190, 308, 330, 631, 637.
- **Está escrito:**
  - Linhas 631/637: definição/fórmula do CRPS prometida nas "seções 6.4.6" e "6.4.7" — **não existem**
    (numeração para em 6.4.5).
  - Linha 190: a mesma definição de CRPS apontada para "seção 6.4.3" — essa seção na verdade é
    "Chen & Moraga 2025" (efeito espacial), sem relação com CRPS.
  - Linha 308: definição de RMSE prometida na "seção 6.4.2" — essa seção define R² e sMAPE, não RMSE.
  - Linha 330: definição de valor-p prometida na "seção 6.4.4" (na verdade sobre Lowe et al. 2016) — a
    definição real só aparece na seção 6.6.5.
- **Deveria estar:** renumerar as referências para onde o conteúdo de fato está, ou escrever as definições
  que faltam — **CRPS e RMSE nunca ganham fórmula formal** em nenhum lugar da Parte 6 (só o CRPSS,
  versão relativa, é explicado).
- **Fonte que decide:** grep interno da própria numeração de seções em `06_literatura.md`.

### 10. "Incidência" definida do zero, de forma independente, em três partes diferentes

- **Arquivos:** `06_literatura.md` (~linha 13), `04_modelos.md` (~linha 1994), `07_alarme.md` (~linha 121).
- **Está escrito:** três definições independentes de "incidência" (casos/100 mil hab.), sem uma remeter à
  outra.
- **Deveria estar:** uma definição única, com as demais ocorrências remetendo a ela. O glossário
  (`10_anexos.md`) só aponta "Definido em Parte 7.2", ignorando que a definição já aparece antes, nas
  Partes 4 e 6.
- **Fonte que decide:** leitura cruzada das três partes citadas.

---

## 🔵 LEVES (2)

### 11. Forward-references longas dentro da própria Parte 2 ("hiperparâmetro", "quantil")

- **Arquivo:** `partes/02_conceitos.md`.
- **Descrição:** "hiperparâmetro" citado na linha 276 com nota "definido na Seção X", mas a definição
  formal só aparece ~900 linhas depois (linha 1169). Mesmo padrão, menor, com "quantil" (linha 644 vs
  definição na 717).
- **Não é erro entre partes** (a definição chega antes do fim da Parte 2, que precede a Parte 4), mas quebra
  a promessa da Parte 0 de "definido antes de ser usado".

### 12. Redação confusa do "20+20+2=42" em `03_dados.md` (ligado ao item grave #6)

- Além do número errado (item 6), a frase em si é didaticamente confusa: isolar duas colunas como um "+2"
  à parte sugere uma categoria extra que não existe. Ver sugestão de reescrita no item 6.

---

## ⚖️ Pontos sem discordância entre verificadores a registrar

Nenhum verificador discordou entre si sobre o mesmo ponto nesta rodada — todos os achados numéricos e de
afirmação tiveram fonte única e não houve leitura conflitante do mesmo trecho por dois verificadores
diferentes.

---

## O que foi conferido e está CORRETO (não mexer)

- MAE 86,39, WIS 44,98, perdas quantílicas 85/15, razão 5,67, McNemar p bruto 0,00739 / p Holm 0,103,
  família de 16 testes, R² 0,898/0,437, +31,5%/+52,5% do vazamento, 152 células, 725 linhas/36 colunas,
  taxas de confirmação 73,2→38,3%, atrasos de confirmação (mediana 10,4/p90 31,6), corte de maturidade,
  núcleo (8 colunas)/vetor (6 colunas)/6 colunas de clima escolhidas, hiperparâmetros dos 9 algoritmos,
  todas as citações de da Silva 2026 / Shi 2016 / Finch 2025 / Zhao 2020 / Aleixo 2022 / Porto Rico /
  canal endêmico / plano municipal (140/421/702) / população 1.404.269.
- O erro de calibração do V1_alvo_log **não** apareceu em `04_modelos.md` (só em `05_hipoteses.md`, item 2).
- A armadilha "alarme de 1 mês vence com significância" foi evitada em `04_modelos.md` linha 1861 (mesma
  parte que a comete na linha 2057 — ver item 1) e em todas as demais partes.
- Nenhuma menção a "vírus no mosquito", dados da Prefeitura, ou violação de pastas proibidas.

---

## PLACAR

| Gravidade | Itens |
|---|---|
| 🔴 Grave | **6** |
| ⚠️ Média | **4** |
| 🔵 Leve | **2** |
| **Total** | **12** |

**Avaliação:** o documento **não deve ser usado como está para a banca** sem passar por esta lista antes.
O item mais grave (#1) é uma contradição interna que afirma significância estatística num resultado que a
própria Parte 4 rotula, 150 linhas antes, como não significativo — exatamente o tipo de frase que um
avaliador atento (ou o próprio Mansilha, cuidando do tom) vai pegar. Os itens #2, #3 e #4 são números/
atribuições erradas que decidem se uma afirmação central do texto ("o vetor ajuda", "o modelo vence a
régua") está sendo lida com o dado certo. Nenhum dos 6 itens graves exige remontar a metodologia — são
todos correções pontuais de texto contra fonte já existente, prováveis de resolver em poucas horas.
