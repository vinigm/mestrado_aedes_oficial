# Pré-declaração — transformação de escala para calibrar a faixa em epidemia

> **Escrita em 26/09/2026, antes de qualquer número novo ser calculado.** Autorizada pelo Vinicius em
> 26/09/2026 ("ok, pode rodar e vamos ver"). Mudança posterior vira **emenda datada** no fim.
>
> Tabela: `tabela_final.csv` **restaurada**, sha256 `6f34b854…`, idêntica ao commit `544263a`. Sem 2026 na
> avaliação, que vai até 01/02/2026.

---

## 1. A pergunta

**Treinar numa escala transformada conserta a faixa de previsão nas semanas de epidemia, sem destruir o
erro pontual?**

---

## 2. Por que, e o que já se sabe

**O defeito, medido em 26/09** (`../2026-09-26_calibracao_por_faixa/`), no cenário adotado:

| Faixa de casos reais | Semanas | Intervalo de 50% | Intervalo de 90% |
|---|---|---|---|
| Calmaria, 0 a 20 | 814 | 59,2% | 90,5% |
| **Alerta ou mais, > 421** | 163 | **8,0%** | **17,8%** |

- Na calmaria a calibração é quase perfeita; acima de 421 a faixa não vale nada.
- **Mecanismo proposto, e é hipótese:** dado de contagem tem variância que cresce com o nível. Treinando em
  escala transformada, uma faixa de largura aproximadamente constante volta como faixa **proporcional** ao
  nível, que é o que falta.

🔴 **O log já foi testado e reprovado, no erro pontual.** Em 25/09, `V1_alvo_log`
(`../2026-09-25_bateria_formulacao_do_alvo/`): MAE **174,4 · 205,8 · 251,0 · 267,9** em h=1/4/8/12, contra
o B0 em **+3,5% · −16,1% · −23,0%** em h=4/8/12. Conclusão registrada lá: *"o log ajuda na baixa e
atrapalha no pico"*.

- ⚠️ **Estou retestando uma formulação reprovada, com outro critério.** Isso é declarado aqui, antes de
  rodar, justamente porque seria pesca se aparecesse depois. A calibração da faixa **nunca** foi avaliada
  em nenhuma variante — `V1` foi julgado só por MAE.
- **A raiz quadrada nunca foi testada** em nenhuma forma. É a transformação estabilizadora de variância
  canônica para contagem (Anscombe), e é bem mais suave que o log.

## 3. Braços

Tudo com o **cenário adotado**: HistGB, 250 iterações, taxa 0,05, 15 folhas, folha mínima 5, as 20 colunas.

| Braço | Alvo treinado | Volta |
|---|---|---|
| **`T_raiz`** | `sqrt(casos)` | elevar ao quadrado |
| **`T_log`** | `log1p(casos)` | `expm1` |
| `B0` (controle) | `casos`, sem transformação | — |

- **Quantis:** 0,05 · 0,10 · 0,25 · 0,50 · 0,75 · 0,90 · 0,95, mais **0,85 só para a trava**.
- **Horizontes:** 1, 4, 8, 12.
- **O controle `B0` NÃO é re-rodado.** Usa as previsões já certificadas de
  `../2026-09-26_wis_na_tabela_restaurada/`, do mesmo cenário e da mesma tabela.
- ⚠️ **A transformação é monotônica**, então transformar de volta preserva a ordem dos quantis: `T_raiz` e
  `T_log` **não podem cruzar** por construção. Isso é consequência esperada, não resultado a comemorar.

## 4. Métricas

- **Principal:** cobertura dos intervalos de **50%** e **90%**, na faixa **acima de 421 casos**.
- **Obrigatórias junto, sempre reportadas:** MAE e WIS, no total e por faixa; cobertura nas outras 3
  faixas; captura do pico.
- **Por faixa** usando as mesmas 4 faixas de `../2026-09-26_calibracao_por_faixa/`.

## 5. Critério de decisão — os DOIS têm de valer

Um braço **funciona** se, contra o `B0`:

1. a cobertura do intervalo de **90%** acima de 421 sair de **17,8%** e chegar a **pelo menos 50%**;
2. **e** o **MAE em h=12** não piorar mais que **10%** (o B0 é **278,8**, então o teto é **306,7**).

- **Se só (1) valer, o resultado é NEGATIVO.** Trocar erro por faixa não é vitória, e não se escolhe o
  critério depois.
- 🚫 **Proibido** relatar "melhorou a cobertura" sem o MAE ao lado, na mesma tabela.
- **Expectativa declarada, que pode falhar:** `T_raiz` cumpre os dois; `T_log` cumpre (1) e falha (2),
  repetindo os −23% de h=12 de 25/09.

## 6. Estatuto

**Descritivo.** Cobertura é proporção; reporto o intervalo binomial de Wilson a 95% junto de cada valor,
mas **não abro família de correção múltipla nem declaro significância**. Motivo: são **163 semanas acima
de 421, em apenas 2 blocos contíguos** (2024 e 2025), e o n efetivo é 2.

## 7. Trava — roda antes de qualquer resultado ser lido

O `B0` em q0,85 tem de reproduzir o painel publicado: MAE h=1 **98,0** · h=4 **219,7** · h=8 **272,6** ·
h=12 **278,7**, tolerância **0,2**. Se não bater, a rodada para e a diferença é explicada.

## 8. Ameaças

- 🔴 **2 blocos, não 163 semanas.** Toda cobertura acima de 421 descreve 2 epidemias.
- 🔴 **Reteste de formulação reprovada.** Mitigado pelo critério duplo declarado acima.
- ⚠️ **Voltar da escala transformada enviesa a média**, não a mediana. Como o alvo é quantil e não média,
  o efeito é pequeno, mas a transformação inversa de um quantil é exata só porque é monotônica — a
  interpretação de "previsão central" muda.
- ⚠️ **A raiz de contagem pequena é grosseira:** entre 0, 1 e 2 casos, `sqrt` dá 0, 1 e 1,41. Na calmaria
  isso pode piorar uma calibração que hoje está boa. Medir e reportar, não esconder.
- ⚠️ **Se `T_raiz` funcionar, não vira referência nesta rodada.** Trocar a configuração adotada exige
  rodada confirmatória própria.

## 9. Custo

**6 a 10 min de parede.** Conta: 2 braços × 8 quantis × 4 horizontes = **64 células**; a rodada de WIS fez
**60 células em 5,4 min** com 8 processos, medido em 26/09. Teto rígido: **25 min**, e para se passar.

## 10. Certificação

Reimplementação independente por agente que tente **reprovar**: a trava, a volta da transformação em pelo
menos uma célula, a cobertura acima de 421 recalculada do zero, e a conferência de que o critério duplo
foi aplicado como está escrito aqui.

---

## Emendas

- *(nenhuma até agora)*
