# Ficha do artigo gêmeo — da Silva et al. 2026 (Porto Alegre, MI-Aedes)

**Contexto:** ficha para a banca do seminário de andamento (21/09/2026), pedida em 26/09/2026, para
comparar nosso trabalho com o estudo mais próximo (mesma cidade, mesma rede de armadilhas).

**Arquivo lido:** `Artigos de referencia/Climate-driven spatiotemporal dynamics of Aedes infestation
and dengue.pdf` (41 páginas, lido integralmente). Este arquivo **não foi renomeado** para o padrão
`ano_autor_tema_revista.pdf` — segue com o nome antigo, embora esteja na pasta raiz de "Artigos de
referencia" e não na subpasta `artigos comparacao 2026-09-25/`.

---

## ⚠️ CORREÇÃO FATUAL — não é PLOS NTD

O pedido (e o `README.md` de `artigos comparacao 2026-09-25/`) chama este artigo de "PLOS NTD".
**Isso está errado.** O cabeçalho aparece em **todas as 41 páginas** do PDF:

> "**medRxiv** preprint doi: https://doi.org/10.64898/2026.03.31.26349860; esta versão postada em 2
> de abril de 2026. **(which was not certified by peer review)**"

- É um **preprint do medRxiv**, ainda **sem revisão por pares**, não um artigo publicado na PLOS NTD.
- Não há DOI de PLOS NTD em lugar nenhum do documento — só o DOI do medRxiv acima (p.1, repetido em
  todas as páginas).
- **Isso é um risco direto para a banca:** se o Vinicius disser "artigo da PLOS NTD" e um membro da
  banca conferir, a citação erra a revista e o status editorial (preprint ≠ publicado). Recomendo
  citar como "**da Silva et al. 2026, preprint medRxiv**" até confirmar se saiu uma versão revisada
  em outro periódico.

## 1. Identificação

- **Título:** "Climate-driven spatiotemporal dynamics of *Aedes* infestation and dengue transmission
  in Porto Alegre, Southern Brazil." (p.1)
- **Autores:** Adryan Aparecido da Silva¹, Álvaro Gil Araujo Ferreira², José Lourenço³, Amanda
  Cupertino de Freitas²,⁴ (p.1).
  - ¹ Faculdade de Farmácia, UFMG · ² Mosquitos Vetores, Instituto René Rachou–Fiocruz Minas ·
    ³ Universidade Católica Portuguesa · **⁴ Ecovec, Belo Horizonte** (p.1).
  - **Autora com vínculo Ecovec:** Amanda Cupertino de Freitas (afiliação 4), autora correspondente.
    Não é "um autor" genérico — é a autora sênior/correspondente.
- **Ano:** postado em 02/04/2026 (medRxiv). **Revista:** nenhuma — é preprint. **DOI:**
  `10.64898/2026.03.31.26349860` (p.1).
- Agradecimentos (p.26) citam financiamento Fapemig e apoio institucional Fiocruz Minas/BHTEC — **não
  há menção a financiamento da Ecovec**, mas a empresa é citada como fonte de dados/apoio junto com a
  Prefeitura de Porto Alegre e a Rentokil (p.26).

## 2. O que fizeram

- **Alvos (três, não um só):**
  - **MFAI** (Mean Female *Aedes* Index) — média de fêmeas capturadas por armadilha/semana, por
    espécie (*Ae. aegypti* e *Ae. albopictus*), **não log-transformado** (p.6).
  - **Índice de positividade DENV** nas armadilhas (% de armadilhas positivas para dengue por RT-PCR)
    (p.6).
  - **Incidência de dengue** — usada como `log(incidência por 100.000 hab. + 1)`, **semanal, para a
    cidade toda** (não por bairro) no modelo LASSO final (p.9, 20).
- **Período dos dados:** entomológico e climático 2018–2025 (8 anos); casos autóctones de dengue
  2019–2025, com **72.965 casos notificados**, 51% confirmados, 93% destes autóctones (p.19).
- **Horizonte de previsão:** **não há um horizonte de previsão formal como o nosso.** Trabalham com
  **defasagens (lags) de 0 a 4 semanas** em correlação de Kendall e regressão LASSO — é associação
  contemporânea/defasada, não uma previsão testada fora da amostra em T+1, T+4, T+12 etc. (p.9, 17,
  20).
- **Algoritmos:** Moran's I + LISA (autocorrelação espacial, por bairro/ano) · correlação de Kendall
  (τ, por bairro e por semana, com lags 0–4) · regressão polinomial (1ª a 4ª ordem, AIC) para
  frequência de chuva × MFAI · **LASSO** (`glmnet`, R 4.4.1) para (i) MFAI-*aegypti*, (ii)
  MFAI-*albopictus*, (iii) log(incidência+1), cada um comparado a um modelo linear (LM) simples
  (p.8–10).
- **Variáveis:** precipitação acumulada, temperatura média, umidade relativa (todas com lags 0–4
  semanas) · Index P (adequação climática vetor-vírus, pacote MVSE) · VFII = MFAI × Index P (índice
  próprio, "Vector-Fitness Infestation Index") (p.7, 39–41).
- **Validação:** **validação cruzada de 10 folds (k-fold)** no LASSO, com lambda mínimo por erro
  cruzado — **não é walk-forward, não corta pela data da resposta, não é um teste fora da amostra no
  tempo.** É ajuste dentro do mesmo período histórico (p.9–10).
- **Unidade espacial:** duas escalas diferentes conforme a análise —
  - Moran's I/LISA e correlação de Kendall por distrito: ~**50 distritos/bairros** de Porto Alegre
    (p.10).
  - Modelo LASSO final de incidência de dengue: **série semanal agregada para o município inteiro**
    (não por bairro) (p.9).

## 3. Resultados (todos os números com página)

- **MFAI - *Ae. aegypti*:** RMSE (LM) 0,2866 · RMSE (LASSO) 0,2864 · razão de deviance 0,5225 (p.20,
  legenda Fig.5).
- **MFAI - *Ae. albopictus*:** RMSE (LM) 0,00977 · RMSE (LASSO) 0,00975 · razão de deviance 0,4933
  (p.20, legenda Fig.5).
- **log(incidência de dengue +1):** RMSE (LM) 1,003 · RMSE (LASSO) 1,006 · razão de deviance **0,61**
  (p.20–21). Não há R², MAE ou MAPE em nenhum lugar do artigo — só RMSE (em escala log) e razão de
  deviance.
- **Correlação de Kendall — clima × MFAI, lag 0 a 4** (Tabela 1, p.17): temperatura τ sobe de 0,419
  (lag0) a 0,581 (lag4) para *Ae. aegypti*; umidade negativa de −0,216 a −0,293; precipitação fraca e
  negativa (−0,09 a −0,125).
- **Correlação de Kendall — MFAI defasado × casos autóctones, lag 0 a 4** (Tabela 2, p.20):
  - *Ae. aegypti*: τ = 0,2737 (lag0) → 0,3376 (1) → 0,3911 (2) → 0,4470 (3) → **0,4953 (lag4)**.
  - *Ae. albopictus*: τ = 0,1206 (lag0) → 0,322 (1) → 0,3645 (2) → 0,4085 (3) → 0,4479 (lag4).
  - Todos p < 0,001. O texto (p.19) interpreta a subida do τ com o lag como **"lead relationship"**
    do vetor sobre a ocorrência de dengue.
  - **Não há dado de lag 8** no artigo — a tabela para em lag 4 (conferido também na última página,
    41/41). ⚠️ O item de `PENDENCIAS.md` ("τ 0,27 · 0,50 · 0,59 nos lags 0 · 4 · 8") **não bate** com
    o texto lido: os valores mais próximos são 0,2737 (lag0) e 0,4953 (lag4) para *Ae. aegypti* — não
    há um terceiro ponto em lag 8. **Fato, não hipótese: recomendo corrigir `PENDENCIAS.md`.**
- **Moran's I anual (S1 Table, p.36–37):** pico em 2023 para ambas espécies (*Ae. aegypti* 0,6235,
  *Ae. albopictus* 0,4377, ambos p<0,001).
- **Positividade das armadilhas para DENV:** subiu de 0,01% (2018) a 0,98% (2025) (p.13).

## 4. Comparabilidade com o nosso trabalho — item a item

| Item | Nosso trabalho | da Silva et al. 2026 | Comparável? |
|---|---|---|---|
| Alvo | Casos confirmados semanais, contagem bruta, por notificação | (i) MFAI bruto, (ii) % armadilha positiva, (iii) **log**(incidência/100k+1) | **Não.** Alvo (iii) é o mais próximo, mas está em log e em incidência, não em casos brutos — não converter, conforme a regra do projeto. |
| Horizonte | 1 a 12 semanas, testado fora da amostra | 0 a 4 semanas, só como **lag de correlação/regressão dentro da amostra** | **Não.** Eles não têm horizonte de previsão prospectivo — é ajuste histórico com variável defasada. |
| Validação | Walk-forward, corte pela data da resposta | k-fold (10) cruzado, sem corte temporal | **Não.** k-fold embaralha o tempo; não é teste prospectivo. RMSE/deviance ratio deles não são comparáveis a MAE/R² de walk-forward. |
| Unidade espacial | Cidade inteira (POA) | Cidade inteira (modelo de dengue) + por bairro (MFAI/Moran's I) | Parcialmente comparável só no agregado municipal. |
| Métrica | MAE 98,0–278,8 · R² 0,898–0,437 (por horizonte) | RMSE 1,003–1,006 em log(incidência+1) · deviance ratio 0,61 | **Não comparável diretamente** — escalas diferentes (log vs. bruto) e RMSE em log não equivale a MAE em casos. A razão de deviance (~R² generalizado) é o único ponto de contato conceitual com nosso R², mas mede ajuste dentro da amostra, não previsão fora da amostra. |
| Papel do vetor | Vetor **piora** o alarme em walk-forward de 3 meses (p Holm 0,037–0,0499) | Vetor (MFAI) **correlaciona positivamente e de forma crescente com o lag** com casos futuros — interpretado como "lead relationship" | **Achados na direção oposta em espírito**, mas metodologias diferentes: eles não testam se adicionar o vetor melhora previsão contra um modelo sem vetor; é correlação bivariada, não teste preditivo controlado. Ver §5. |

## 5. Risco para nós — o que pode ser usado para questionar o trabalho

- **Direção oposta na narrativa sobre o vetor.** Eles concluem que a infestação de *Aedes* **antecede
  e ajuda a prever** casos de dengue (Kendall crescente com o lag, "lead relationship", p.19). Nosso
  achado é que o vetor **piora** o alarme em walk-forward pareado (Holm p=0,037–0,0499). Um membro da
  banca pode perguntar: "se o artigo gêmeo de Porto Alegre encontrou o vetor útil, por que o de vocês
  não?" A resposta tem que ser metodológica, não um desmentido do achado deles: eles medem
  **correlação bivariada não controlada por sazonalidade compartilhada** (ambos vetor e dengue sobem
  com calor/umidade); nós medimos **contribuição incremental em previsão fora da amostra**, controlando
  para o que a régua sazonal já captura. São perguntas diferentes — **"o vetor se move com dengue?"
  (sim, nos dois estudos, no fundo) vs. "o vetor ajuda a PREVER além do que já sabemos pela época do
  ano?" (não, no nosso teste).**
- **Eles não fazem holdout temporal.** Isso enfraquece a força da conclusão deles como "capacidade
  preditiva" — é adequação de modelo, não previsão. Vale explicitar isso na defesa, com cuidado para
  não soar como ataque: é uma diferença de desenho, não um erro deles (o objetivo do artigo é outro —
  entender associação espaço-temporal, não fazer forecasting operacional).
- **Defasagem vetor→casos:** eles **mediram e quantificaram** (Tabela 2, lags 0–4 semanas, p.20) — a
  banca pode perguntar por que nós não fizemos o mesmo. Vale citar que nosso desenho testa a mesma
  pergunta de um jeito mais rigoroso (fora da amostra), não que a pergunta deles seja inválida.
  **Não há lag 8 no artigo**, então qualquer alegação nossa citando "lag 8" precisa ser removida ou
  atribuída a outra fonte.
  ⚠️ **Não confirmar/usar até revisar** — o número de `PENDENCIAS.md` (τ 0,59 em lag 8) não tem
  respaldo neste PDF.
  - **Aviso preventivo (Mansilha, 24/09):** o vínculo Ecovec (afiliação 4, autora correspondente) é
  um fato relevante mas **não é motivo para desqualificar o estudo** — registrar sem tom acusatório,
  conforme orientação já registrada para o texto do site.
- **É preprint, não peer-reviewed.** Isso reduz o peso dele como "literatura consolidada" numa
  argumentação de defesa — mas também significa que citar "PLOS NTD" (como o pedido fez) é
  factualmente incorreto e corrigível antes que a banca note.
- **Conclusão geral do artigo é favorável à vigilância entomológica** ("early-warning component",
  p.25) — alinhada com a tese de que a rede de armadilhas tem valor, mas por um caminho
  (correlação/associação) diferente do nosso (previsão testada). Não é uma ameaça direta à pergunta
  "quanto vale a rede", é outro ângulo de resposta à mesma pergunta.

## Fontes e rastreabilidade

- Todos os números acima vêm do PDF citado, com página indicada entre parênteses/tabelas.
- Nenhum dado foi convertido de escala (log→bruto) ou de unidade (incidência→casos) para viabilizar
  comparação — conforme a regra do projeto.
