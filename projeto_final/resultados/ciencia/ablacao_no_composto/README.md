# Ablação no composto (17/10/2026) — EXPLORATÓRIA

> ⚠️ **Não pré-declarada. Nada daqui vai ao artigo** (decisão do pedido de 17/10/2026). Medida depois de ver os resultados
> da E2/E3/F1-F4. Nenhum modelo foi treinado: só as previsões que já existem em `../E2_ablacao/previsoes.csv`.

## O que é

- **Pergunta:** o que cada fonte b ∈ {casos, clima, vetor} acrescenta ao **composto de defesa** (E3, N = 13), e não a uma folha só?
- **Composto sem b:** a MESMA regra do composto (`aedes.composto.montar_composto`, N = 13) aplicada ao par `sem_b@f5` × `sem_b@f20`.
  A escolha de folha é refeita sem b, então o composto sem b pode escolher folhas diferentes do completo.
- **Comparação:** composto completo (A) × composto sem b (B), h = 1, 4, 8 e 12, pareado por `data_alvo` (interseção), janela de
  avaliação (07/01/2024 a 01/02/2026). **Δ = MAE(sem b) − MAE(completo)**; positivo = tirar b piora o composto (b contribui).
  `ganho % = Δ / MAE(sem b) × 100`, a mesma convenção da F1.
- **Estatística (pacote, sem alteração):** DM-HLN, IC 95% por bootstrap de blocos (8 semanas, 2.000, semente 42), Holm sobre os
  **12 testes** (uma família), veredito pela regra pré-declarada (Holm < 0,05 e |Δ| > 2 × piso; piso = o MAIOR entre as duas
  folhas no horizonte, Emenda 1; `../piso_de_ruido/piso.csv`).
- **Script:** `experimentos/ablacao_no_composto.py` · **CSV (precisão total):** `ablacao_no_composto.csv` · **log:** `ablacao_no_composto.log`.

## Âncora (obrigatória, passou)

- O composto completo remontado aqui (N = 13) reproduz **exatamente** `../E3_composto/previsoes.csv` (N == 13): linhas
  (282, 276, 268 e 260 em h = 1, 4, 8, 12), `data_origem`, `data_alvo`, `real`, `previsto` e `folha_escolhida`, **diferença 0**.
- O MAE do composto completo na janela bate com `../E3_composto/resumo.csv` (n = 102; 102,33 · 205,73 · 233,51 · 260,14).
- Conferência independente (numpy/pandas do zero, regra reescrita) de dois casos: `sem_casos` h = 1 (MAE 205,807, troca de folha 46,1%)
  e `sem_vetor` h = 12 (MAE 289,056, troca 47,1%) coincidem com o script.
- n = 102 nos 12 testes (o `sem_vetor` tem 109 semanas na janela; a interseção com o completo é 102).

## Tabela (12 testes)

| fonte | h | n | MAE completo | MAE sem b | Δ | ganho % | IC 95% (ganho %) | p DM-HLN | p Holm | limiar (2×piso) | veredito | troca de folha |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| casos | 1 | 102 | 102.3 | 205.8 | +103.5 | +50.3 | [+20.6; +66.6] | 0.002 | 0.025 | 10.4 | A melhor | 46% |
| casos | 4 | 102 | 205.7 | 192.1 | -13.6 | -7.1 | [-43.4; +8.8] | 0.511 | 1.000 | 24.6 | sem evidencia | 35% |
| casos | 8 | 102 | 233.5 | 247.0 | +13.5 | +5.5 | [-2.0; +8.7] | 0.220 | 1.000 | 27.1 | sem evidencia | 25% |
| casos | 12 | 102 | 260.1 | 281.5 | +21.4 | +7.6 | [-4.3; +16.2] | 0.304 | 1.000 | 20.4 | sem evidencia | 25% |
| clima | 1 | 102 | 102.3 | 98.9 | -3.5 | -3.5 | [-12.9; +8.1] | 0.627 | 1.000 | 10.4 | sem evidencia | 25% |
| clima | 4 | 102 | 205.7 | 214.9 | +9.1 | +4.2 | [-9.7; +14.7] | 0.520 | 1.000 | 24.6 | sem evidencia | 15% |
| clima | 8 | 102 | 233.5 | 212.7 | -20.8 | -9.8 | [-26.3; +4.1] | 0.250 | 1.000 | 27.1 | sem evidencia | 24% |
| clima | 12 | 102 | 260.1 | 215.0 | -45.2 | -21.0 | [-37.7; -1.1] | 0.245 | 1.000 | 20.4 | sem evidencia | 24% |
| vetor | 1 | 102 | 102.3 | 100.3 | -2.0 | -2.0 | [-33.7; +22.6] | 0.822 | 1.000 | 10.4 | sem evidencia | 38% |
| vetor | 4 | 102 | 205.7 | 219.6 | +13.9 | +6.3 | [-15.9; +22.1] | 0.472 | 1.000 | 24.6 | sem evidencia | 37% |
| vetor | 8 | 102 | 233.5 | 250.8 | +17.3 | +6.9 | [-16.1; +27.3] | 0.594 | 1.000 | 27.1 | sem evidencia | 22% |
| vetor | 12 | 102 | 260.1 | 289.1 | +28.9 | +10.0 | [-0.4; +17.3] | 0.177 | 1.000 | 20.4 | sem evidencia | 47% |

- **Troca de folha** (descritivo): fração das semanas da interseção em que a folha escolhida pelo composto sem b difere da do completo.

## Leitura em 3 linhas

- **Casos em h = 1 é o único que passa** (Δ = +103,5; +50,3%; Holm 0,025; acima do limiar de 10,4): sem casos o composto dobra o erro de 1 semana.
  Os outros 11 testes ficam **sem evidência** (Holm = 1,0 em todos).
- **Vetor** tem ganho positivo e crescente em h = 4, 8 e 12 (+6,3%, +6,9%, +10,0%), mas com IC cruzando zero; **clima** tem sinal de
  piora quando presente em h = 8 e 12 (tirar o clima melhora o composto: −9,8% e −21,0%), também sem passar em Holm. São descrições, não efeitos.
- A escolha de folha muda em 15% a 47% das semanas ao tirar uma fonte: **o composto não é uma folha só**, e a contribuição da fonte
  passa em parte pela escolha da folha.

## Comparação com F1 (folha 5) e F3 (folha 20) — ganho %

| fonte | h | ganho % no composto | ganho % F1 (folha 5) | ganho % F3 (folha 20) | veredito F1 | veredito F3 |
|---|---|---|---|---|---|---|
| casos | 1 | +50.3 | +54.7 | +36.1 | A melhor | sem evidencia |
| casos | 4 | -7.1 | +3.7 | -3.4 | sem evidencia | sem evidencia |
| casos | 8 | +5.5 | +2.2 | +9.1 | sem evidencia | sem evidencia |
| casos | 12 | +7.6 | +6.6 | +12.3 | sem evidencia | sem evidencia |
| clima | 1 | -3.5 | -2.9 | -0.4 | sem evidencia | sem evidencia |
| clima | 4 | +4.2 | -1.8 | -0.2 | sem evidencia | sem evidencia |
| clima | 8 | -9.8 | -13.4 | -11.5 | sem evidencia | sem evidencia |
| clima | 12 | -21.0 | -27.2 | -30.5 | sem evidencia | sem evidencia |
| vetor | 1 | -2.0 | -6.5 | -15.7 | sem evidencia | sem evidencia |
| vetor | 4 | +6.3 | -0.1 | +4.1 | sem evidencia | sem evidencia |
| vetor | 8 | +6.9 | -7.7 | +8.1 | sem evidencia | sem evidencia |
| vetor | 12 | +10.0 | +2.2 | +12.3 | sem evidencia | sem evidencia |

- Casos h = 1: o composto (+50,3%) fica perto da folha 5 (+54,7%, passa em Holm na F1) e acima da folha 20 (+36,1%, não passa na F3).
- Vetor: em h = 8 e 12 o composto fica **entre** as duas folhas (h = 12: +2,2% folha 5, +10,0% composto, +12,3% folha 20); em h = 4 fica acima das duas
  (+6,3% contra −0,1% e +4,1%); em h = 1 fica perto de zero (−2,0%), menos negativo que as duas (−6,5% e −15,7%).
  perto de zero (−2,0%), melhor que a folha 20 (−15,7%).
- Clima: mesmo padrão das folhas em h = 8 e 12 (−13,4% e −27,2% na folha 5; −11,5% e −30,5% na folha 20; −9,8% e −21,0% no composto).
- Nenhum veredito novo em relação a F1/F3; **hipótese a confirmar** apenas com temporada nova (2026-27). Família de 12 testes, exploratória: não citar "significativo" sem ressalva.
