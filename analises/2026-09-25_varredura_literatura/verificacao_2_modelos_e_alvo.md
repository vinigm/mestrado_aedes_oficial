# Verificação adversarial — Ângulo 2: Modelos e alvo

> Verificador independente, 25/09/2026. Método: WebSearch + WebFetch direto nas fontes (sem download de
> arquivo). Veredicto por achado, com trecho/número encontrado. Rótulo `nao_verificavel` quando a fonte
> não abriu (paywall/reCAPTCHA) e não há snippet confiável o suficiente.

---

## 0. Lowe et al. 2016, eLife 5:e11285 — 57% vs 33%

**CONFIRMADO.** Fetch direto em `midasnetwork.us` (resumo do próprio paper) e snippet de busca
convergem: *"the forecast model produced more hits and fewer missed events than the null model, with a
hit rate of 57% for the forecast model compared to 33% for the null model"*, validado contra os casos de
junho/2014 (Copa do Mundo). Referência bate: Lowe et al. 2016, eLife, DOI `10.7554/eLife.11285`. Achado do
relatório é fiel ao paper, sem inferência disfarçada de fato.

## 1. Zhao et al. 2020, PLOS NTD — RF Colômbia MAE 9,32/24,56

**CONFIRMADO.** Fetch direto em `journals.plos.org/plosntds/...pntd.0008056`: MAE de **9,32 (1 semana)**
e **24,56 (12 semanas)** para o RF nacional; texto do próprio artigo citado: *"for any of the n-week-ahead
(n≤12) forecasts, the national RF model more accurately predicted... than the ARIMA models"* e RF também
superou ANN em todos os horizontes. Título, DOI e conclusão batem exatamente com o relatório.

## 2. Wu et al. 2025, PNAS — ensemble 38,5/54,5/62,7% vs 40/55/64%

**CONFIRMADO.** Fetch direto em PMC12377650 (mirror do artigo PNAS 122(33):e2422335122): ensemble PAE
**38,5% / 54,5% / 62,7%** (1/2/3 meses) contra melhor modelo individual (VAR) **40% / 55% / 64%**. Frase do
próprio artigo: *"the country-specific and overall ensembles had the lowest mean percent absolute errors
compared to all other models across all forecast horizons."* Autores/DOI batem.

## 3. Sprint IMDC24, PNAS 2026 — nenhum modelo consistente

**CONFIRMADO (via snippet convergente, fetch direto bloqueado por reCAPTCHA em 2 tentativas).** Dois
snippets independentes de busca trazem o mesmo texto do artigo (PMC12912988, DOI `10.1073/pnas.2508989123`,
publicado 17/02/2026): *"no single model consistently excelled across all forecast targets"* e *"neither
individual models nor ensemble models provided accurate results for the extreme epidemic observed during
the 2024 epiyear."* O relatório já rotula este número como "via snippet, não confirmado por leitura
direta" — postura correta, e o conteúdo do snippet sustenta a afirmação como escrita.

## 4. Morbey et al. 2023, PLOS ONE — seleção por MAE ≠ seleção por pico

**CONFIRMADO.** Fetch direto em PMC10516409: *"the models with the lowest daily forecast errors... were
not the models that were best at predicting the timing and intensity of a seasonal peak"* e *"the models
with the lowest peak errors for the typical season included seasonality variables, whilst those for the
atypical seasons did not."* Ressalva menor: o modelo com menor erro diário no paper é RF, e os de menor
erro de pico são GLM-elastic-net/regressão linear — o relatório generaliza corretamente sem citar RF
especificamente, o que não distorce a conclusão central.

## 5. McGough et al. 2021, J R Soc Interface — 71,7%/75%, 17 anos, 20 municípios

**CONFIRMADO.** Fetch direto em PMC8205538: 17 anos (2001–2017), 20 municípios brasileiros, acurácia
**71,7%** (só clima) e **75%** (clima + ciclos de dengue). DOI `10.1098/rsif.2020.1006` bate com o título
buscado. Números e desenho (classificação epidêmico/não-epidêmico) exatamente como reportado.

## 6. SARIMAX Rio de Janeiro — MAE 279,15/375,15 vs 308,92/396,91

**PARCIAL.** O trecho de SARIMAX foi confirmado por snippet de busca (agregando medRxiv/PMC11984044/
Springer): *"SARIMAX_Lag consistently maintained a lower error rate... MAE of 279.15 and 375.15... for 8
and 12 weeks ahead"* — bate exatamente com o relatório. O par "ARIMA puro 308,92/396,91" **não foi
confirmado por leitura direta** (PMC bloqueado por reCAPTCHA em nova tentativa) nem apareceu explicitado
no snippet agregado — permanece no mesmo status que o próprio relatório já declarou ("não confirmado por
leitura direta"). Referência (DOI `10.1186/s41182-025-00723-7`) existe e bate com veículo/ano.

## 7. Modelos de fundação de séries temporais — lacuna (Chronos/TimesFM/Moirai/Lag-Llama)

**NÃO VERIFICÁVEL como certeza absoluta, mas corroborado.** Busca própria independente (termos cruzando
os 4 nomes com "dengue"/"zero-shot") não retornou nenhuma aplicação a dengue ou arbovirose — mesmo
resultado qualitativo do relatório. Não é possível provar uma ausência de forma exaustiva (limitação
inerente a qualquer varredura), mas a checagem independente não encontra contra-exemplo. Trata-se
corretamente de lacuna, não de achado positivo.

## 8. Alvo como razão/resíduo sobre mesma semana do ano anterior — lacuna

**NÃO VERIFICÁVEL como certeza absoluta, mas corroborado.** Busca própria não encontrou paper que
formule o alvo explicitamente como razão ou resíduo sobre o mesmo período do ano anterior (apenas
formulações com defasagem de 52 semanas como atributo, GAM+EWMA de resíduo dentro do mesmo ano, etc.).
Mesma ressalva do item 7: ausência não é prova exaustiva, mas nenhum contra-exemplo apareceu.

## 9. TFT malária/dengue — R² até 0,90 (PMC12841506)

**CONFIRMADO.** Snippet de busca cita diretamente o texto do artigo (Pillay, Le, Takamatsu, Phong,
Kgalane, Minakawa; IJERPH 2026, DOI `10.3390/ijerph23010075`, PMC12841506): *"leading dengue models
reached R2 values up to 0.90"* (e malária: melhor modelo R²=0,95, MAE=4,98). Bate com o número e o
enquadramento ("via snippet, não confirmado por leitura direta") que o próprio relatório já usa —
fetch direto ao PMC segue bloqueado por reCAPTCHA, mas o conteúdo do snippet sustenta a afirmação.

---

## Achados adicionais (fora da lista, mas notados na verificação)

- Nenhuma referência da lista se mostrou **inexistente, com autor/ano/veículo trocado**, nem com número
  fabricado — o padrão de honestidade do pesquisador original (rotular "via snippet" quando o fetch
  falhou) se sustentou em todos os casos checados.
- Único ponto de atenção real: o par ARIMA puro do estudo do Rio (item 6) segue sem confirmação
  independente — mas o próprio relatório já sinalizava essa fragilidade, então não há inferência
  apresentada como fato consumado.
