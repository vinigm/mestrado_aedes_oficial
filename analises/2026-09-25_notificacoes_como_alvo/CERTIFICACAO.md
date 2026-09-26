# Certificação adversarial — notificações como alvo

> 25/09/2026. Certificador independente, com código próprio (reimplementação, não reuso do `rodar.py`).
> Veredito: **APROVADO**, com uma divergência pontual no texto do resumo (não afeta as tabelas/critérios).

---

## O que foi refeito do zero

- **Junção CEVS × tabela_final**: reconstruída em pandas puro, sem importar `montar_tabela_cevs.py`.
  - Totais anuais 2022-2025 (confirmados e notificações): **batem exato** com o protocolo.
  - 2026: bate exato contra o total recalculado na janela da `tabela_final` (semana ≤ 32): confirmados
    **10/10**, notificações **4.056/4.056**. Confirma a investigação do executor (não é erro de junção).
  - `tabela_cevs.csv` do executor comparado linha a linha com a minha montagem: **0 divergências em 725
    linhas**.
  - 10 semanas aleatórias contra o CSV bruto do CEVS: **todas batem**.
- **MAE, skill score e métricas de 2026**: recalculados do zero a partir de `previsoes_por_braco.csv`
  (60 combinações braço×h×recorte). Diferença máxima contra `metricas.csv`: **4,5e-13** (ruído de ponto
  flutuante). Zero divergências acima de tolerância.
- **Família K1** (C2a/C2b × C0, Wilcoxon pareado + Holm próprio sobre 8): reproduz `familia_k1.csv`
  exatamente, incluindo os p de Holm.
- **Família K2** (C0/N1 × régua, Wilcoxon + Holm próprio sobre 6): reproduz `familia_k2.csv` exatamente.
- **Critérios da seção 6**: recomputados — K1 h=12 não passa para C2a nem C2b (confirma "NÃO"); o segundo
  critério usa a **média do erro relativo across h=1,4,8,12** (não só h=12) — reproduz 9,419 / 397,158 /
  11,281 exatos. É a leitura correta do código, mas é uma média grosseira sobre horizontes com escalas de
  erro muito diferentes (h=1 quase zero, h=12 na casa das centenas) — registrar isso ao usar o número.

## Vazamento e trocas — nada encontrado

- **Taxa de confirmação e notificações (com lags)**: usam sempre `rolling(...).ffill()` ou `.shift(+n)`
  sobre a série bruta do CEVS, calculadas na própria linha de origem; `construir_alvo_horizonte` desloca
  só o `y_h` para frente, nunca as features. Sem vazamento de semana-alvo.
- **Alvo por braço**: confere exatamente com a tabela do protocolo (T0=casos oficial, C0/C2a/C2b=CEVS
  confirmados, N1=CEVS notificações).
- **Régua por braço**: cada braço busca a régua na sua própria série (`alvo_por_braco`), sem cruzar alvo.
- **Corte de maturidade**: todos os 5 braços usam o default (12 semanas da `CIDADE_REFERENCIA`) — nenhum
  braço tem corte diferente.
- **TRAVA 1 em outro período?** Não. T0 só tem dado oficial até 2026-04-26 (297 NaN em
  `casos_confirmados` no fim da série); o corte em 2026-02-28 do protocolo já era um não-operante (T0 não
  passa disso de qualquer forma). Os 4 MAE batem exatos com o README do bloco 7.
- **TRAVA 3 (clima diverge)**: investigado e correto — a seleção de clima treina no alvo (60% iniciais,
  dívida técnica já registrada em PENDENCIAS). T0, C0 e N1 têm alvos diferentes → clima diferente; C2a e
  C2b têm o MESMO alvo de C0 → mesmo clima de C0, como devia ser.

## Divergência encontrada (no texto do resumo, não nos dados)

- O resumo do executor diz que C0 "chega a prever 833,9 numa semana onde o real é 2". Conferido:
  a semana com `previsto=833,85` é **C0, h=12, data_alvo=2026-03-15, com `real=0.0`**, não 2. A semana com
  `real=2` (2026-04-19, h=12) tem `previsto=205,3`. É erro de redação ao ilustrar o achado — o achado em
  si (C0 não acompanha a queda, erro relativo médio 397×) está correto e recalculado exato.

## Erro de método (pré-existente, não introduzido por esta rodada)

- O critério 2 da seção 6 (seção "modelo acompanha a transmissão") usa média do erro relativo entre
  h=1,4,8,12. Como h=1 e h=4 têm erro quase nulo e h=8/h=12 são grandes, a média "SIM" esconde que em
  horizontes curtos a diferença N1×C0 é menos clara. Não invalida o resultado, mas o "SIM" deveria vir
  com essa qualificação ao ser citado fora desta análise.
