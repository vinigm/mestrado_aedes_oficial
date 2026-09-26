# Pré-declaração — segunda bateria noturna: os resultados em 2026

> **Escrita em 25/09/2026, às 23h, antes de qualquer número de 2026 da tabela oficial atualizada existir.**
> Autorizada pelo Vinicius em 25/09/2026 ("pode"). Roda depois da atualização dos dados
> (`analises/2026-09-25_atualizacao_dados_2026/`) e da busca de hiperparâmetros
> (`analises/2026-09-25_busca_de_hiperparametros/`). Mudança posterior vira **emenda datada**.
>
> **2026 não entrou em nenhuma decisão do projeto.** As hipóteses abaixo foram formadas antes, com dados
> até fev/2026.

Comum às quatro rodadas: tabela oficial atualizada, município de notificação, corte de maturidade de 12
semanas, walk-forward pela data da resposta, quantil 0,85 salvo quando dito, 1 thread por processo.
**Recorte 2026** = de 01/01/2026 até o último alvo maduro. Travas antes de ler resultado; certificação
independente depois.

---

## A. Os resultados principais em 2026

**Braços**, em 12 horizontes: os 8 distintos da bateria noturna. São eles o cenário adotado (HistGB folha 5, com
vetor), HistGB folha 5 sem vetor, HistGB folha 20 com e sem vetor, LightGBM com e sem vetor, e GradientBoosting
com e sem vetor. Mais a régua sazonal.

**Trava:** o cenário adotado reproduz, até fev/2026, MAE 98,0 / 219,7 / 272,6 / 278,7 com tolerância de 0,5.
Se as semanas de jan-fev/2026 mudaram com a tabela nova, a diferença é explicada antes de seguir.

| Hipótese | Formada em | Teste em 2026 | Família |
|---|---|---|---|
| **A1:** com folha mínima 20, o vetor reduz o erro de 3 meses | 24/09, bloco 7 | M1 × M0 no HistGB folha 20 e no LightGBM, em h 8 e 12, Wilcoxon pareado | 4, Holm |
| **A2:** o modelo erra menos que "o ano passado" num ano atípico | 25/09 | cenário adotado e HistGB folha 20 × régua, em h 4 e 12 | 4, Holm |
| **A3:** o alarme dispara menos alarmes falsos que a régua | 25/09 | alarmes falsos com os limiares **100**, **421** e **702** casos por semana, em h 1, 4, 8, 12 | descritivo |

- Os limiares 421 e 702 são os pisos de Alerta e Epidemia do Plano Municipal de Contingência de 2026 da
  SMS-POA, usados como **corte de uma semana só**. É uma simplificação declarada: o plano também exige
  condições em 4 semanas.
- **Decisão:** A1 se confirma se M1 < M0 em h=12 nos dois algoritmos, com p Holm < 0,05. Com ~20 semanas, o
  poder é baixo: a direção nos dois algoritmos já conta como leitura descritiva.
- **Descritivo:** o período inteiro 2024-2026 e o skill contra a régua.

## B. Modelos com vários quantis e o WIS

- **Modelos:** o cenário adotado e o HistGB folha 20, treinados nos quantis **0,05 · 0,10 · 0,25 · 0,50 · 0,75 ·
  0,90 · 0,95**, em h 1, 4, 8, 12. Os quantis cruzados são ordenados por previsão, e isso é contado.
- **Métrica:** o **WIS** de Bracher et al. 2021, com a mediana e os intervalos de 50%, 80% e 90%. Mais a cobertura
  dos intervalos de 50% e 90%.
- **Régua probabilística:** a **climatológica**, com os quantis da mesma semana epidemiológica nos anos
  anteriores, que é a régua oficial dos sprints.
- **Teste:** WIS do modelo × WIS da régua climatológica, em h 4 e 12, nos dois modelos. Família de 4, Holm.
  Recortes 2024-2025, 2026 e tudo.

## C. Estabilidade das vencedoras da busca

- As vencedoras `HB_best` e `LGB_best` da busca, rodadas com as sementes **1 a 5**, em 12 horizontes.
- **Estável** se o desvio-padrão do MAE em h=12 for menor que 5% da média **e** a comparação com o cenário
  adotado em 2026 tiver o mesmo sinal nas 5 sementes. Descritivo.
- ⚠️ O HistGB só tem aleatoriedade se `max_features < 1`. Se a vencedora for determinística, isso é registrado e
  a rodada vale só para o LightGBM.

## D. Calibração do quantil, sem treino

- Sobre as previsões q0,85 do cenário adotado e do HistGB folha 20 da rodada A.
- **Correção conformal:** em cada origem, soma-se à previsão o quantil 0,85 empírico dos resíduos, real menos
  previsto. A conta usa só os pares já respondidos na origem, do mesmo horizonte, com `data_alvo ≥ 2022-01-01`.
  Com menos de 26 pares, não há correção.
- **Métricas:** cobertura, perda quantílica 0,85, MAE e alarmes falsos, em 2024-2025, 2026 e tudo.
- **Teste:** perda quantílica corrigida × original, em h 4 e 12, nos dois modelos. Família de 4, Holm.

---

## Ameaças

- **2026 é uma temporada só, e atípica:** houve 4 mil notificações e quase nenhum confirmado.
- **Com ~20 semanas por horizonte em 2026, os testes têm pouco poder.**
- **Os confirmados de 2026 ainda podem ser reclassificados.**

---

## Emendas

- **25/09/2026, 23h30, antes de rodar:** o Vinicius conferiu o Quadro 1 do plano municipal no PDF. São **4
  estágios**, não 3. A3 passa a incluir também o limiar de **140** casos por semana, o piso de Mobilização
  (10 por 100 mil). Ficam 100, 140, 421 e 702.

- **25/09/2026, 23h50, antes de rodar:** a trava do cenário adotado passa a usar **âncoras recalculadas na tabela
  atualizada**, e não os números publicados. Até fev/2026, o adotado dá h=1 **97,4** e h=12 **280,0**, contra 98,0 e
  278,7 publicados. A diferença vem da revisão dos casos de jan/2026 e da ordem das colunas de clima; ver o adendo
  em `analises/2026-09-25_atualizacao_dados_2026/CERTIFICACAO.md`. A trava exige reproduzir esses valores com
  tolerância de 0,2. Os de h=4 e h=8 são calculados e registrados pelo próprio script. Com a série maior, o
  recorte 2026 vai até **19/04/2026**, a última semana válida depois do corte de maturidade.
- **26/09/2026, 01h20, antes de ler qualquer WIS:** a rodada B parou na trava porque a lista de quantis da seção B
  não incluía o **0,85**, que é o quantil que a trava confere. Foi falha da pré-declaração, não do código. A B
  passa a treinar também o 0,85, usado **só para a trava**; o WIS segue com os 7 níveis declarados.
- **26/09/2026, 01h20:** na busca, a função de trava filtrou só `data_alvo ≤ 01/02/2026`, sem o início em
  2024-01-01, e por isso deu "inválida". Recalculado na janela certa, a partir das previsões gravadas: h=1
  **97,38** · h=4 211,31 · h=8 270,55 · h=12 **279,96**. **Bate as âncoras**, e as previsões da busca valem.
