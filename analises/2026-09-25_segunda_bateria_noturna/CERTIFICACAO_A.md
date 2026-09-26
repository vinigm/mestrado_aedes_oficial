# Certificação adversarial — rodada A (segunda bateria noturna)

**Certificador independente, 26/09/2026, 01h30 aproximadamente.** Processos terminados,
resultados completos em disco. Substitui a certificação anterior (feita com a rodada
incompleta). Tudo recalculado do zero em código próprio, em
`/private/tmp/.../scratchpad/certificar_A.py` e `retreinar_h12.py`, sem reusar nenhuma
função de `rodar.py`. Fórmulas de Wilcoxon/Holm reimplementadas independentemente.

## Veredito: CERTIFICADO — bate em todos os 5 pontos

| Item | Resultado |
|---|---|
| (1) Trava | **VÁLIDA.** h=1: 97,376 (âncora 97,4) · h=12: 279,958 (âncora 280,0), tolerância 0,2. h=4/h=8 recalculados batem a emenda de 26/09 01h20 (211,31 / 270,55). |
| (2) MAE por braço/h/recorte | **324 células conferidas contra `metricas.csv`, diferença máxima 1,1e-13** (erro de ponto flutuante). `n_semanas` bate em todas. |
| (3) A1 e A2 (Wilcoxon+Holm) | **12+12 linhas conferidas, diferença máxima de p_Holm ~1e-16.** `familia_a1.csv` e `familia_a2.csv` reproduzidos exatamente. |
| (4) Alarmes 2026 | **432 células conferidas contra `alarmes_2026.csv`, diferença zero** em emitidos e falsos, nos 4 limiares (100/140/421/702). |
| (5) Re-treino do zero | **HistGB folha 20 M1 e M0, h=12, 3 origens de 2026: previsão re-treinada bate a gravada com diferença 0,000000** em todos os 6 casos (2 modelos × 3 origens). |

## Números principais (A1 e A2, recorte 2026)

- **A1 (vetor, folha 20):** confirma exatamente o oposto da hipótese. Em h=12, **MAE com
  vetor (578,97 HistGB / 565,09 LightGBM) é PIOR que sem vetor (315,07 / 314,65)**,
  p_Holm 0,0499 nos dois — significativo, mas na direção contrária à declarada
  ("A1 confirma se MAE(M1) < MAE(M0)"). Veredito do script, **NÃO confirma**, está correto.
- **A2 (modelo × régua):** cenário adotado bate a régua em h=4 (p_Holm 0,0001) e h=12
  (p_Holm 0,0039); folha20 bate só em h=12 (p_Holm 0,022), não em h=4 (p_Holm 0,175).
- **Alarmes falsos em 2026 (soma dos 12 h, por braço):** cenário adotado 107/95/60/39
  (limiares 100/140/421/702) · folha20 121/109/81/63 · régua 132/132/96/84. Modelo emite
  **menos falsos que a régua em todos os limiares**, mas `n_surtos_reais = 0` em TODAS as
  combinações de braço/limiar em 2026 — não há nenhum verdadeiro positivo para comparar.

## Achado que qualifica A2 (não é defeito da rodada, é do ano)

- A régua sazonal em 2026 repete o pico epidêmico de 2025 (chega a prever **2381** casos
  em 22/03/2026, contra **real = 0**). O `real` de 2026 inteiro fica entre 0 e 3 casos por
  semana. A régua erra catastroficamente (MAE 902,9) não por ser um método ruim em geral,
  mas porque 2026 é a exceção que ela não pode capturar (não houve repetição do surto).
- Os modelos também superestimam muito em 2026 (ex.: HistGB_folha20_M1 previu 654 e 1188
  contra reais de 1 e 3), só que menos que a régua. **A2 "confirma" porque a régua é pior
  ainda, não porque o modelo é preciso.** Isso já está registrado como ameaça na
  pré-declaração ("2026 é uma temporada só, e atípica") — aqui fica confirmado com número.

## O que foi conferido e como

- Recarreguei só `previsoes_por_braco.csv` (33.174 linhas, 9 braços) e recalculei MAE,
  Wilcoxon pareado e Holm com implementação própria — sem importar `rodar.py`.
- Para o item 5, usei o motor compartilhado `harness.py` (leitura, não alterado) só para
  montar a mesma tabela de features, e treinei/previ com chamadas `.fit()/.predict()`
  próprias para 3 origens de 2026 (04/01, 01/03, 19/04), HistGB folha 20 com e sem vetor,
  h=12. As 6 previsões batem a gravada exatamente.
- Conferi o log (`execucao.log`): os 8 braços terminaram sem erro, warning ou traceback.
- Threats da pré-declaração ("2026 atípica", "~20 semanas, pouco poder") se confirmam nos
  números: n_pareado = 16 em todas as comparações de 2026, e o A2 é lido com a ressalva
  acima.

## Não certificado / fora de escopo desta rodada

- Famílias B (WIS), C (estabilidade) e D (calibração) já têm certificação própria em
  `CERTIFICACAO_A_B.md` (parcial, na época) e `CERTIFICACAO_C_D.md` — não repetidas aqui.
- A3 é descritivo por desenho da pré-declaração (sem teste de hipótese formal); os números
  acima são só a contagem, como pedido.
