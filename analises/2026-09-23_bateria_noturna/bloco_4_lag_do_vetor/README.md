# Bloco 4 — Janela de lag longa só no vetor

> **Rodado entre 23/09/2026 23h51 e 24/09/2026 00h48** (57 min). Parte da [bateria noturna](../README.md).
> Protocolo em [PRE_DECLARACAO.md](PRE_DECLARACAO.md).

---

## Em uma frase

**Estender a memória do vetor não ajuda o HistGB.** Com lags de 6 a 12 semanas acrescentados só ao vetor,
o erro fica igual ou um pouco maior em todos os horizontes de decisão, e nada chega perto de
significância. O gargalo não é quanto passado do vetor o modelo vê.

---

## 1. De onde veio este teste

### A cadeia de raciocínio

1. **23/09, tarde** — o [teste de janela de lag](../../2026-09-23_janela_de_lag/) estendeu a memória de
   **todas** as colunas juntas, de 4 para 8 e para 12 semanas. Nada melhorou; até 12 semanas, o horizonte
   longo piorou.
2. **23/09, noite** — o [bloco 3](../bloco_3_importancia_por_bloco/) mostrou que, a partir de 4 semanas à
   frente, o modelo depende **mais do vetor** do que do histórico de casos.
3. **A hipótese deste bloco:** se o sinal longo mora no vetor, estender tudo junto diluiu esse sinal com
   lags correlacionados de casos e de clima. Estender **só o vetor** isolaria o ganho.

---

## 2. O que foi feito

| Braço | Vetor | Casos e clima | Colunas |
|---|---|---|---|
| **A_referencia** | lags 1 a 4 e média de 4 semanas | lags 1 a 4 | 20 |
| **B_vetor_ate_8** | + lags 6 e 8 | lags 1 a 4 | 22 |
| **C_vetor_ate_12** | + lags 6, 8, 10 e 12 | lags 1 a 4 | 24 |

As colunas novas entram por fora da seleção de clima. **Conferido:** os três braços escolheram as mesmas
seis colunas de clima.

---

## 3. Trava de validação — passou

A referência reproduziu o painel: MAE **98,0 / 219,7 / 272,6 / 278,8**, R² **0,898 / 0,628 / 0,450 /
0,437**.

---

## 4. Resultado

Pareado por `data_alvo`, avaliação 2024+, Holm sobre 8 comparações. Queda do erro; negativo é pior.

| Braço | h=1 | h=4 | **h=8** | **h=12** |
|---|---|---|---|---|
| B vetor até 8 | −3,2% | −1,6% | −0,8% | −1,6% |
| C vetor até 12 | −3,6% | +5,1% | −2,3% | −3,1% |

Menor p de Holm: **0,156**, C em h=12. Todos os outros entre 0,63 e 1,00.

**Veredito pelo critério pré-declarado: nenhum braço entra na referência.**

Os braços com lag maior perdem as primeiras semanas da série, então o pareamento compara em 98 semanas
(B) e 94 (C), e não em 102. É por isso que o MAE da referência muda de linha para linha.

---

## 5. O que isso quer dizer

- **FATO:** acrescentar 6 a 12 semanas de memória ao vetor não melhora o HistGB em nenhum horizonte de
  decisão.
- **FATO:** o resultado é o mesmo do teste da tarde, que estendeu todas as colunas. Isolar o vetor não
  muda a conclusão.
- **Leitura, junto com o [bloco 5](../bloco_5_algoritmos/):** o LightGBM tira do vetor um ganho de 15%
  em h=12 **usando só os lags 1 a 4**. A informação que antecipa os casos já está nas quatro semanas mais
  recentes do vetor e na média móvel dele. O que limita o HistGB não é a janela; é como ele usa o que já
  recebe.
- A hipótese deste bloco — *o sinal longo está diluído* — **não se sustenta**. Não há sinal escondido em
  lags mais antigos do vetor, pelo menos não que o HistGB consiga aproveitar.

---

## 6. Limitações

- **Testado só no HistGB.** No LightGBM, que já aproveita o vetor, lags mais longos poderiam render outra
  coisa. Não foi medido.
- **Lags pontuais, não agregados.** Uma média móvel de 8 ou 12 semanas do vetor carregaria a tendência da
  temporada de um jeito diferente de lags soltos. Não foi medido.

---

## 7. Arquivos

| Arquivo | O que é |
|---|---|
| [`PRE_DECLARACAO.md`](PRE_DECLARACAO.md) | protocolo |
| [`rodar.py`](rodar.py) | o script |
| `execucao.log` | a saída completa |
| `saidas/previsoes_por_braco.csv` | uma previsão por linha, três braços |
| `saidas/comparacoes.csv` | a tabela do §4 |
| `saidas/resumo_dos_bracos.csv` | colunas e clima por braço |
