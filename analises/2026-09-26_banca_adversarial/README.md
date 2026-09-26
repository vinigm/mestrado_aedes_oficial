# Banca Adversarial — 26/09/2026

**Pergunta:** os três argumentos do seminário (A1 calmaria/alarme, A2 subestimação de picos, A3 limite de dados) sobrevivem a uma banca simulada?

**Método:** quatro pareceres independentes (estatístico, epidemiologista, revisor-ml, advogado) atacaram cada argumento contra a evidência certificada em `analises/2026-09-25_*` e `analises/2026-09-26_*`. Este documento consolida — não decide sozinho onde os quatro discordaram (ver §4).

---

## 1. Veredito por argumento

| Argumento | Veredito | Número que decide |
|---|---|---|
| **A1** (calmaria + alarme 1 mês) | **SUSTENTA COM AJUSTE** | McNemar h=4 × R_hoje: p_Holm=**0,103** (não significativo, 15 pares) — mas WIS h=4 vence a régua climatológica com p<**0,0001** |
| **A2** (subestimação + transformações) | **SUSTENTA COM AJUSTE** | Cobertura piora nas 4 faixas (calmaria 90,5%→**80,5%**, log) — mas MAE **melhora** em h=4 com raiz (−**6,7%**): exceção real, não pode ser omitida |
| **A3** (limite de dados) | **SUSTENTA COM AJUSTE** | **120** configs + 2 foundation models + SARIMA/LASSO: nenhum bate a régua (**239,6** × **226,8** em 3 meses) — mas GEV/GPD e modelos mecanicistas **nunca foram testados** |

Nenhum dos três é **NÃO SUSTENTA**. Nenhum sobrevive **sem ajuste** na redação atual.

---

## 2. Argumento por argumento

### A1 — "fiável na calmaria, excelente a 1 mês"

**O que cai:**
- "Excelente" para o alarme de 1 mês contra réguas simples não tem respaldo estatístico: McNemar+Holm não fecha nem contra R_hoje (p=**0,103**) nem contra R_ano_passado (p=**1,000**).
- Em 3 meses (h=12), o modelo **empata** com "o ano passado passou de 100" (Youden **0,66-0,78** vs régua **0,81**, p_Holm=**0,845**/**1,000**) — só vence a régua mais fraca ("hoje já passou", p=**0,00062**).
- Em E_421 (limiar alto), **0 de 4** combinações vencem R_ano_passado (varredura 26/09).

**O que fica:**
- Calibração de calmaria é fato sólido: IC90 cobre **90,5%** das **814** semanas calmas.
- WIS em h=4 vence a régua climatológica com significância robusta (p<**0,0001**) — métrica contínua pré-declarada, não descritiva.
- Direção do efeito em h=4 é favorável (**13** de **15** discordantes a favor do modelo) — amostra pequena, não ausência de efeito.

**Reescrita para o slide:**
> "O modelo é bem calibrado em calmaria — o intervalo de 90% cobre 90,5% das 814 semanas calmas — e, a 1 mês, vence a régua climatológica com significância (WIS, p<0,0001). Contra o calendário do ano passado, o efeito aponta a favor mas a amostra ainda não fecha estatisticamente; tratamos isso como resultado em aberto, não como vitória geral."

---

### A2 — "subestima os picos; raiz e log pioram"

**O que cai:**
- "Provámos que elas pioram a previsão" generaliza demais: só **2** transformações testadas (raiz, log) de uma família maior (Box-Cox geral, Anscombe, Tweedie/binomial-negativa, conformal por regime).
- Existe exceção real que a frase esconde: MAE em h=4 **melhora** com raiz (−**6,7%**) — omitir isso é o tipo de seletividade que uma banca cita.
- "Testámos as correções matemáticas padrão" deveria dizer **quais** ("raiz e logaritmo"), não deixar implícito que é o catálogo inteiro.

**O que fica:**
- Subestimação sistemática é fato medido: captura do pico **0,388**; erro mediano **539** sobre real de **917** (**59%** do nível) acima de 421 casos.
- Cobertura piora nas **4** faixas de gravidade, **sem exceção**, inclusive na calmaria (90,5%→84,2%→**80,5%**) — certificado adversarialmente, aprovado.
- Conformal como alternativa é pior ainda: cobertura sobe (50%→78%) mas falsos-alarme disparam (**15→124**).

**Reescrita para o slide:**
> "Confirmamos subestimação sistemática dos picos — a previsão captura em média 39% da magnitude real nas semanas de surto. Testamos, com pré-declaração e certificação adversarial, raiz e logaritmo: as duas pioraram a cobertura nas quatro faixas de gravidade, inclusive na calmaria. A única exceção é uma melhora pontual de erro em 1 mês, que não compensa a perda de calibração nos extremos."

---

### A3 — "não é defeito de código; é limitação dos dados (2 epidemias)"

**O que cai:**
- "Nenhum algoritmo de machine learning consegue aprender" é alegação teórica universal, **não testada** por este experimento — é a leitura mais perigosa segundo o revisor-ml.
- A causa não é só quantidade de exemplos: também faltam variáveis-chave (sorotipo circulante, imunidade populacional, mobilidade) — duas limitações concorrentes, a frase reduz a uma só.
- Contaminação metodológica: a configuração vencedora da busca (LGB_best) foi selecionada em 2022-2025 e julgada no mesmo período — mesmo assim perdeu (239,6×226,8), mas precisa re-rodar sem 2026 (excluído em 26/09) antes de citar com autoridade.

**O que fica:**
- A busca foi ampla para as famílias testadas: **120** configurações (60 HistGB + 60 LightGBM), **9** algoritmos (grid 30/08), **2** foundation models zero-shot, SARIMA, LASSO, **6** formulações de alvo — nenhum bateu a régua sazonal em extremos.
- Zero-shot (Chronos-2, MAE **227,2**) também perde para a régua (**217,8**) — reforça que não é falta de tuning.
- Série tem só **2** epidemias documentadas (2024, 2025); dengue é endemia recente em Porto Alegre.

**Reescrita para o slide:**
> "Testamos 120 configurações de boosting, 9 algoritmos, 2 modelos de fundação zero-shot, SARIMA, LASSO e 6 formulações de alvo — nenhum superou a régua sazonal em eventos extremos. Isso é consistente com uma série de apenas duas epidemias documentadas, somada à ausência de sorotipo, imunidade e mobilidade como atributos. É limitação de dados para as arquiteturas testadas — não afirmamos que nenhum algoritmo, em tese, poderia aprender com dois exemplos."

---

## 3. As 5 perguntas mais perigosas

| # | Pergunta | Resposta (uma linha, ancorada) |
|---|---|---|
| 1 | Se McNemar não fecha em h=4 contra as duas réguas (p=**0,103** e p=**1,000**), com que direito dizem "excelente"? | Não dizemos "vence com significância" nas réguas binárias — dizemos que o WIS vence a climatológica (p<**0,0001**) e que o efeito aponta a favor sob amostra pequena (**13/15**). |
| 2 | Se "o ano passado passou de 100" empata com o modelo em 3 meses (Youden **0,81** vs **0,66-0,78**), qual o valor incremental do modelo além de 1 mês? | O ganho comprovado em 3 meses existe só contra a régua mais fraca (p=**0,00062**); contra a régua dura, é resultado em aberto, não vitória. |
| 3 | Por que a teoria de valores extremos (GEV/GPD) — desenhada para eventos raros — nunca foi testada? | Não foi testada; por isso a frase foi ajustada de "nenhum algoritmo" para "nenhuma arquitetura testada" (**120** configs + 2 foundation models + SARIMA/LASSO). |
| 4 | Se só 2 de N transformações de variância foram testadas, como afirmar que "as correções padrão pioram"? | A frase agora nomeia as duas testadas (raiz, log) em vez de generalizar para "padrão"; ambas pioraram cobertura nas **4** faixas. |
| 5 | A configuração vencedora da busca de hiperparâmetros foi selecionada e avaliada no mesmo período (2022-2025) — o resultado não é otimista? | Sim, é viés de seleção conhecido; mesmo com esse viés a favor, ainda perdeu (**239,6** × **226,8**) — e roda com 2026 hoje excluído da avaliação, precisa re-rodar antes de citar com autoridade. |

---

## 4. Onde os quatro pareceres discordaram

**A1 — quão grave é a não-significância em h=4:**
- **Advogado** salva "excelente" trocando o argumento para WIS (p<0,0001), trata o McNemar como limite de amostra, não de efeito.
- **Estatístico** trata como "em aberto": não é vitória nem derrota, é poder insuficiente.
- **Epidemiologista** é o mais duro: descarta "calmaria" como achado (acertar o estado de menor ação vale pouco clinicamente) e aponta o empate em h=12 com "ano passado" como o problema mais sério, mais que a não-significância em si.
- **Revisor-ml** enquadra como "fronteira da contribuição": vence baselines fracas, não vence a régua dura — não é vitória geral.

**A2 — quão "sem exceção" é o resultado:**
- **Advogado** descreve como pioria "sem exceção" e não menciona a melhora de MAE em h=4.
- **Estatístico** insiste que essa exceção existe e **não pode ser escondida** — a diferença é sobre cobertura (sem exceção, correto) vs. MAE (com exceção, omitido pelo advogado).
- **Epidemiologista** adiciona uma dimensão que os outros três não discutem: risco operacional de subestimar picos para dimensionar recursos — a frase precisa de um adendo de uso, não só o número.

**A3 — qual é a causa real e o que caberia adicionar:**
- **Revisor-ml** é o mais rigoroso: separa 3 camadas (fato sobre estes dados / fato sobre a classe testada / alegação teórica não testada) e classifica a versão atual da frase como overclaim central citável por um revisor.
- **Epidemiologista** propõe uma causa concorrente diferente: falta de atributos (sorotipo, imunidade, mobilidade), não só poucos exemplos.
- **Advogado** prefere reforçar com uma comparação positiva (R² acima de 3 estudos publicados) em vez de estreitar a alegação.
- **Estatístico** fica no meio-termo: só troca "nenhum algoritmo" por "nenhuma arquitetura testada".

---

## 5. O que está sendo subvendido

- **WIS h=4 com p<0,0001** contra a régua climatológica é o resultado estatístico mais limpo do trabalho para A1 e está sendo ofuscado pela frase genérica "excelente para alarme".
- **Youden 0,94 / sensibilidade 97,1% / 0,7 falso-alarme por ano** em h=4 é um número operacional forte que não aparece destacado nas versões atuais dos argumentos.
- **R² do modelo (0,63 em 1 mês / 0,44 em 3 meses) supera 3 estudos publicados** — CatBoost-Rio (0,38), CatBoost-27-capitais-POA (−0,21), da Silva 2026 (0,46 em log) — e está sendo apagado pela autocrítica de A3.
- **Perder para a régua sazonal em 3 meses é comum na literatura** (comparação direta, 25/09) — isso normaliza o resultado negativo e não está sendo usado para contextualizar A3.
- **O rigor adversarial em si** (120 configs + 9 algoritmos + 2 foundation models + SARIMA/LASSO + bateria de transformações pré-declarada e certificada) é, pela comparação com a literatura, acima da média da área — vale posicionar como diferencial metodológico, não só como "tentamos tudo e falhou".

---

## 6. Lacunas que um revisor citaria

| Lacuna | Por que importa | Custo estimado |
|---|---|---|
| **GEV/GPD** (teoria de valores extremos) | Desenhada especificamente para eventos raros — é a lacuna mais perigosa para A3, porque o argumento central é exatamente sobre raridade | Baixo-médio: framework estatístico conhecido, poucos dias de implementação e validação |
| **Modelos mecanicistas (SIR/SEIR)** | Incorporam dinâmica epidêmica que não depende de aprender de exemplos históricos | Médio-alto: exige parâmetros epidemiológicos (R0, suscetíveis), 1-2 semanas |
| **Transfer learning de outra cidade** com mais epidemias documentadas | Poderia injetar exemplos de eventos extremos que POA não tem | Médio-alto: depende de acesso a dado externo comparável (ex.: da Silva 2026) |
| **Família mais ampla de transformações** (Box-Cox geral, Anscombe, perda Tweedie/binomial-negativa, conformal por regime) | Só 2 de N testadas; enfraquece "provámos" em A2 | Baixo: reaproveita o pipeline já certificado, dias |
| **Re-rodar a busca de hiperparâmetros sem contaminação** (2026 fora da avaliação) | LGB_best foi selecionado e avaliado no mesmo período (2022-2025) | Baixo: script já existe, é re-execução |
| **Atributos ausentes** (sorotipo, imunidade, mobilidade, vírus no mosquito 2026) | Reconhecido como limitação real, mas não testável sem dado novo da Prefeitura (já descartado por decisão de 25/09) | Alto / fora de alcance no momento — registrar como limitação declarada, não lacuna a fechar agora |

---

## Adendo do orquestrador, 26/09/2026 — um erro apanhado dentro da própria banca

O parecer do **epidemiologista se contradiz**, e o erro é do tipo que destruiria um slide:

- Na seção de ataques ele **acerta**: registra que em 3 meses o modelo não vence `R_ano_passado`.
- Mas na redação segura ele escreve que em 1 mês o modelo supera *"com significância tanto 'esperar o
  surto' quanto a régua sazonal"*. **É falso.** Os p de Holm em h=4 são **0,103** e **1,000**.

**Fica registrado por dois motivos:**

1. **A redação dele não pode ser usada.** As três frases válidas são as da seção 2 deste documento, que o
   consolidador escreveu sem propagar o erro. Conferi o CSV `mcnemar_holm.csv` de 25/09 por conta própria.
2. **É evidência de que "Youden 0,94 contra 0,84" convida ao erro.** Um avaliador com o número correto na
   mão na mesma página escorregou. Numa banca, com a plateia lendo rápido, escorrega de novo.

⚠️ **Regra que decorre disso:** sempre que a sensibilidade de 97,1% aparecer em slide ou texto, ela vem
acompanhada de "não testado contra as réguas com significância". Sem exceção.

## O que sustenta o alarme de 1 mês, e é outra coisa

A defesa de A1 **não passa pelo alarme binário**. Passa pelo **WIS**:

| | Comparador | Métrica | Resultado |
|---|---|---|---|
| ❌ Não sustenta | `R_hoje` e `R_ano_passado` | Youden, McNemar | p Holm **0,103** e **1,000** |
| ✅ Sustenta | régua **climatológica** | **WIS** | p Holm **< 0,0001** |

São comparadores e métricas diferentes, e isso precisa ficar explícito ao citar:

- **`R_ano_passado`** = a mesma semana do ano anterior cruzou o limiar. É regra binária.
- **Régua climatológica** = os quantis da mesma semana epidemiológica nos anos anteriores. É a régua
  probabilística oficial dos sprints brasileiros, e o WIS é a métrica oficial deles.

**A frase honesta e forte:** *avaliado pela métrica oficial dos sprints brasileiros, o modelo vence a régua
climatológica em 1 mês com p < 0,0001.* Isso é verdade, é relevante e não depende do alarme binário.
