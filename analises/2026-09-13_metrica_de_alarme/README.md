# Uma métrica de alarme de verdade — 13/09/2026

> **A pergunta:** o modelo serve como alarme epidemiológico? A "captura do pico" não responde isso.
> **A resposta:** serve, e bem melhor do que a métrica antiga sugeria. **97% de sensibilidade a um mês
> e 77% a três meses**, com precisão acima de 80% e menos de 2,5 alarmes falsos por ano.
> Status: ✅ concluído · Custo: **zero CPU** (re-agregação das previsões já salvas).

## 1. Por que este teste foi feito

- O projeto media "captura do pico" como `média(previsto) ÷ média(real)` nas semanas com mais de 100
  casos. **Isso é razão de nível, não alarme.**
- Ela não diz quantos surtos seriam sinalizados, nem com quanta antecedência, nem quantos alarmes
  falsos. E a perda quantílica infla essa razão por construção, então a métrica e o remédio empurram
  na mesma direção.
- Uma banca que ouvir "serve para alarme" vai pedir sensibilidade e antecedência. Não existiam.

## 2. Como foi medido

Nenhum modelo rodou. São as previsões das 120 células do grid corrigido de 13/09, re-agregadas.

**Definições, fixadas antes de olhar o resultado:**

| Termo | Definição |
|---|---|
| Semana de surto | `real > 100` casos. Mesmo corte já usado em "captura do pico", para os números serem comparáveis. |
| Alarme | `previsto > 100` casos. |
| Episódio | Semanas de surto consecutivas. Dois episódios separados por menos de 4 semanas calmas contam como um só, senão uma epidemia com dois picos vira dois eventos. |
| Sensibilidade | Das semanas de surto, quantas dispararam alarme. |
| Precisão | Dos alarmes, quantos eram surto de verdade. |
| Falsos por ano | Alarmes fora de episódio, por ano de avaliação. |

**Antecedência não precisa ser estimada.** O horizonte é fixo: um alarme para a semana W em h=8 foi
emitido 8 semanas antes. A antecedência **é** o horizonte.

## 3. O que deu

Configuração de referência (HistGB · quantil 0,85 · com vetor), avaliação 2024+:

| h | Sensibilidade | Precisão | Falsos/ano | Captura do pico (métrica antiga) |
|---|---|---|---|---|
| 1 semana | **96,9%** | 91,2% | 1,0 | 0,886 |
| 4 semanas | **97,1%** | **94,3%** | **0,7** | 0,702 |
| 8 semanas | **81,6%** | 86,1% | 1,7 | 0,417 |
| 12 semanas | **76,9%** | 81,1% | 2,3 | 0,388 |

**A métrica antiga subestimava muito a utilidade do modelo.** Em três meses, "captura de 0,388" soa
como fracasso; "sinaliza 77% das semanas de surto com 81% de precisão e 2,3 alarmes falsos por ano"
é um instrumento utilizável.

**Por que as duas discordam:** a captura do pico mede se o modelo acerta o **tamanho** da epidemia. Ele
não acerta — subestima. Mas para alarme não é preciso acertar o tamanho, basta cruzar o limiar. São
perguntas diferentes, e a operacional é a segunda.

### O vetor no alarme, pareado pelas mesmas semanas

| h | Sensibilidade com vetor | sem vetor | Precisão com | sem | Falsos com | sem |
|---|---|---|---|---|---|---|
| 1 | 96,9% | 100% | 91,2% | 91,4% | 3 | 3 |
| 4 | 97,1% | 97,1% | **94,3%** | 89,2% | **2** | 4 |
| 8 | 81,6% | 81,6% | 86,1% | 86,1% | 5 | 5 |
| 12 | **76,9%** | 61,5% | 81,1% | 82,8% | 7 | 5 |

⚠️ **EXPLORATÓRIO.** Em h=12 o vetor sobe a sensibilidade em 15,4 pontos, ao custo de 2 alarmes falsos
a mais. Em h=4 empata em sensibilidade, melhora a precisão e corta os falsos pela metade.

## 4. Conclusão

- ✅ **FATO — o modelo é um bom alarme até um mês** (97,1% de sensibilidade, 94,3% de precisão, menos
  de 1 falso por ano) **e um alarme aceitável a três meses** (76,9% e 81,1%).
- ✅ **FATO — a "captura do pico" não é métrica de alarme** e subestima a utilidade operacional. Deve
  ser reportada como o que é: viés de nível nas semanas de pico.
- ⚠️ **EXPLORATÓRIO — o vetor ajuda o alarme em h=12 e h=4.** Não pré-declarado, sem teste de
  significância, e a amostra é pequena.

## 5. Ressalvas

- 🔴 **Só existem 2 episódios no período de avaliação.** Toda métrica por episódio (início pego,
  atraso) é baseada em n=2 e **não deve ser citada**. Foram calculadas e ficam no CSV, mas não valem.
- As métricas por semana repousam em 32 a 39 semanas de surto. Melhor, ainda pequeno.
- **Nenhum teste de significância.** É descrição, não inferência.
- O limiar de 100 casos é convenção do projeto, não um corte epidemiológico validado.
- ⚠️ **Tensão com o experimento de surto.** Ali o vetor **piora** o alarme em h=12 (Holm 0,037). Aqui
  ele **ajuda**. Não é contradição direta: lá o alvo é notificados e o método é um classificador com
  limiar por percentil; aqui é confirmados e um regressor cortado em 100. **São tarefas diferentes e
  a discordância precisa constar no texto**, não se escolhe a conveniente.

## 6. Dois números do projeto, verificados

**A autocorrelação: ✅ CONFIRMADA.** R² de prever `casos[t+h]` usando só `casos[t]`:

| h | 1 | 2 | 4 | 8 | 12 |
|---|---|---|---|---|---|
| R² | **0,915** | 0,804 | 0,527 | 0,080 | **0,000** |

A frase "explica 91% em h=1 e 0% em h=12" estava **certa**; só não tinha script. Agora tem.

**A taxa de confirmação: ❌ um número errado, outro certo.**

| Ano | Confirmados | Notificados | Taxa medida |
|---|---|---|---|
| 2022 | 5.583 | 7.622 | **73,2%** |
| 2023 | 6.600 | 9.522 | **69,3%** |
| 2024 | 19.034 | 31.652 | 60,1% |
| 2025 | 24.793 | 64.704 | **38,3%** |

- 🚫 **"99,6% em 2023 → 42,0% em 2025"**, citado em `PENDENCIAS` e em `modelagem_aedes/acesso/fontes.py`
  e usado como argumento para trocar o alvo: **não bate.** O real é 69,3% e 38,3%.
- ✅ **"73,2% em 2022 → 38,3% em 2025"**, da pré-declaração de `alvo_e_features_infodengue`: **bate
  exatamente.**

A direção da alegação (a taxa despencou) se sustenta. O valor de 2023 não. Corrigir o docstring de
`fontes.py`.

## 7. Arquivos

- `medir_alarme.py` — a métrica, com as definições no cabeçalho.
- `saidas/alarme_configuracao_de_referencia.csv` — os 4 horizontes da referência.
- `saidas/alarme_30_configuracoes_h4.csv` — as 30 configurações em h=4.
- `saidas/alarme_pareado_e_numeros.txt` — comparação pareada do vetor e as duas verificações.
