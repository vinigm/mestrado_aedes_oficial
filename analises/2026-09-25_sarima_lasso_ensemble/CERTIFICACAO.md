# Certificação adversarial independente — SARIMA + LASSO + ensemble

> Escrita em 25/09/2026. Certificador tentou **REPROVAR** a rodada, com código próprio (não importou
> `rodar_sarima.py`, `rodar_lasso.py` nem `combinar_e_avaliar.py`), medindo do zero a partir dos CSVs
> brutos (`saidas/previsoes_sarima.csv`, `saidas/previsoes_lasso.csv`) e dos braços externos (B0,
> `c2_casos`, régua). Reusou só `harness.py` da bateria noturna (motor já certificado em 13/09/2026,
> não é um dos 3 scripts sob auditoria) para reconstruir as 20 colunas do LASSO.
>
> **Veredito: NÃO REPROVADA.** Todos os números batem byte a byte com o que o orquestrador reportou.
> As duas "explosões" (SARIMA e LASSO) são comportamento real do desenho declarado, não bug. As
> travas 4 e 5, que o combinador não verifica em tempo de execução, foram checadas aqui e passam.

---

## 1. O que bateu — recálculo independente de MAE, n e famílias J1/J2/J3

- **MAE e n reproduzidos exatamente** para os 7 braços em todos os h (102 pares na avaliação,
  `data_alvo ≥ 2024-01-01`), com join e filtro refeitos do zero. Nenhuma divergência.
- **`ens_pesos` reconstruído com grade própria de 1.001 pesos** (não copiada do combinador): os pesos
  médios por horizonte batem **exatamente** com `leitura_pesos_medios_ens_pesos.csv` (ex.: h=12 →
  B0 0,332 · c2 0,191 · sarima 0,110 · lasso 0,246 · régua 0,121). Confirma que a lógica "só pares já
  respondidos" está correta, não só por leitura de código.
- **Holm e Wilcoxon reimplementados** (Wilcoxon com aproximação normal + correção de continuidade,
  Holm por conta própria): p-valores batem com diferença ≤ 2% do relatado, mesma ordem de grandeza,
  **nenhuma conclusão muda**. Critérios da seção 5, h=12: **nenhum braço bate a régua nem melhora o B0
  com significância** (`candidato_2026_2027=False` nos 4) e `vetor_vale_no_lasso=False`. Idêntico ao
  que o orquestrador leu.

## 2. Divergências encontradas

**Nenhuma.** Toda âncora numérica do briefing (MAE por braço/h, pesos médios, contagem de fallback do
SARIMA na avaliação) foi reproduzida com diferença zero ou desprezível (arredondamento de Wilcoxon).

## 3. SARIMA: a explosão é comportamento real do modelo, não bug

- **Caso mais explosivo isolado e refeito do zero**: h=12, origem `04/02/2024`, `data_alvo` `28/04/2024`.
  Real = **1.347**; `q085` do arquivo = **43.423,1**; reproduzido via `SARIMAX` independente =
  **43.423,1** (diferença relativa 0,0%).
- **Mecanismo**: nas 10 semanas antes da origem os casos saltam de 7 para 80 (início da temporada
  epidêmica de 2024). O ajuste dá **AR(1)=0,635, AR(2)=0,310, soma=0,945** — muito perto da raiz
  unitária. **Meia-vida do decaimento ≈ 12,2 semanas**, quase igual ao próprio horizonte pedido (h=12).
  Isso **invalida a premissa da seção 6 da pré-declaração** ("sem constante, a correção some com o
  horizonte e a previsão converge para a régua"): quando o AR fica perto do unit root, a correção
  **não** some em 12 semanas — é matemática do modelo encontrando dado real, não erro de código.
- **Trava 2 (sem futuro) verificada em 100% das 1.159 linhas**: `ultima_data_ajuste == data_alvo − h`
  sempre verdadeiro (o fix do orquestrador — gravar `contexto['data'].max()` em vez de `origem` —
  confirmado presente no código e correto).
- **Fallback**: total 42-45 de ~284-295 origens por h (2020-2026), mas **18/18/18/20 de 102 na
  avaliação** — bate exatamente a âncora do briefing ("18 a 20"). Não é falta de histórico (mínimo de
  106 semanas já satisfeito desde a 1ª origem avaliada): é não-convergência real do MLE, espalhada pela
  série, ~15% das vezes.

## 4. LASSO: mesma família de explicação, também real

- **Caso mais explosivo de h=8 refeito do zero**: `data_alvo` `28/04/2024`, origem `03/03/2024`.
  Real = **1.347**; previsto do arquivo = **15.316,8**; reproduzido com `QuantileRegressor` próprio
  (mesmas 20 colunas via `harness`, log1p+padronização feitos à mão, alpha=0,001) = **15.316,8**
  (diferença zero).
- **Mecanismo**: na origem, `casos` já valia **1.311** (mesma disparada do início da epidemia:
  12→30→39→80→156→249→558→1.311 em 8 semanas). O regressor linear em log1p está extrapolando um ponto
  de entrada muito fora da distribuição de treino — é o análogo do SARIMA: **modelo linear/AR sem
  mecanismo de saturação, alimentado com o início de uma curva epidêmica, explode.** Árvore (B0) não
  tem esse problema porque satura nas folhas.
- **Não é bug**: features, corte de treino (`data + h ≤ origem`, refeito à mão) e clima usado batem
  exatamente com o pipeline original.

## 5. Ensemble: sem vazamento, confirmado por reconstrução própria

- Reconstruí `ens_pesos` para 3 origens de 2024-2025 em h=12, com grade própria de 1.001 combinações,
  usando **só pares com `data_alvo ≤ origem`** (verificado par a par que nenhum ponto futuro entrou).
- Ex.: origem `04/02/2024` (a mesma do caso explosivo do SARIMA) → pesos escolhidos
  B0=0,50 / c2=0,00 / sarima=0,10 / lasso=0,40 / régua=0,00. O ensemble **absorve mas não neutraliza**
  a explosão: previsão final 5.066 contra real 1.347 (o SARIMA sozinho previa 43.423). Mostra o
  ensemble funcionando como amortecedor parcial, não filtro.
- Pesos médios da reconstrução batem 100% com o arquivo oficial (ver seção 1).

## 6. Travas 4 e 5 — não verificadas em runtime, checadas aqui

- **Trava 4 (determinismo)**: repeti 5 origens do SARIMA (h=12) e 5 do LASSO (h=8, `lasso`) do zero —
  **as 10 batem exatamente** com os CSVs gravados.
- **Trava 5 (mesmo clima do B0)**: chamei `harness.montar_features_do_braco` para o braço `lasso` e,
  separadamente, para uma réplica do braço `HistGB_folha20_M1` (o B0) — **as 6 colunas de clima são
  idênticas** (`temp_media_lag4, umid_media, temp_media_lag3, temp_max, pressao_media_lag3,
  pressao_media_lag4`) e as 20 colunas do modelo batem. Confirmado empiricamente, não só por leitura de
  código: a seleção de clima não depende do algoritmo nem do nome do braço, só da tabela e da
  configuração fixa (`CIDADE_REFERENCIA`), que não mudou entre 23/09 (corrida do B0) e 25/09
  (`tabela_final.csv` sem alteração de mtime desde 29/08).

## Conclusão

A rodada é **mecanicamente sólida**: nenhuma trava furada, nenhuma divergência numérica, nenhum
vazamento. O resultado negativo (nenhum critério da seção 5 sobrevive a Holm em h=12) **não é
artefato de bug** — é a conclusão que os dados sustentam. As duas explosões (SARIMA e LASSO) têm o
mesmo diagnóstico: modelos lineares/autorregressivos sem mecanismo de saturação, aplicados a origens
que caem bem no início de uma temporada epidêmica, extrapolam a subida recente sem freio. Isso é uma
**limitação de desenho dos dois modelos**, não um erro de implementação, e derruba a premissa da seção
6 sobre o SARIMA convergir para a régua em horizontes longos quando o AR fica perto da raiz unitária.

Código da certificação: `/private/tmp/claude-501/.../scratchpad/cert_sarima_lasso.py` (não gravado
nesta pasta, por instrução do brief).
