# Pré-declaração — modelos de fundação em modo zero-shot

> **Escrita em 25/09/2026, antes de qualquer previsão com dado do projeto.** Autorizada pelo Vinicius em
> 25/09/2026 ("vai la, vamos ver o que aparece, tentar nao custa"). O único teste feito antes foi uma
> série sintética de seno, para conferir a instalação. Mudança posterior vira **emenda datada** no fim.
>
> ⚠️ **Rodada exploratória.** A avaliação 2024+ já foi vista nas rodadas de 25/09. O juiz confirmatório é
> a temporada **2026-2027**.

---

## 1. Pergunta

**Um modelo pré-treinado em milhões de séries de outras áreas, sem treinar na nossa, prevê casos de dengue
de Porto Alegre em 3 meses melhor que a regra "mesma semana do ano passado"?**

E duas perguntas derivadas:

- ele prevê melhor que o nosso HistGB com folha 20 e vetor, o `B0`?
- dentro dele, o vetor ajuda?

### Por que vale perguntar

- **O que o dado mostra:** a regra sazonal vence todos os modelos do projeto em h=8 e h=12. Seis
  formulações novas não mudaram isso.
- **Hipótese:** o limite é de dado. Com 4 temporadas epidêmicas, nenhum modelo treinado só na nossa série
  aprende o formato de uma epidemia. Um modelo que já viu milhões de curvas traz esse conhecimento de fora.
- **Na literatura:** a varredura de 25/09 não achou aplicação de modelo de fundação a dengue.

---

## 2. Os braços

| Braço | Modelo | Entrada |
|---|---|---|
| `bolt_casos` | Chronos-Bolt base | só a série de casos |
| `c2_casos` | Chronos-2 | só a série de casos |
| `c2_casos_clima` | Chronos-2 | casos + covariáveis de clima |
| `c2_casos_clima_vetor` | Chronos-2 | casos + clima + vetor |

**Comparadores, já existentes e não re-rodados:**

- a régua sazonal: casos em `data_alvo − 52` semanas;
- o `B0`, do bloco 7 da bateria noturna.

### Regras de construção, fixadas antes

- **Pares avaliados:** exatamente os pares `(h, data_alvo)` do `HistGB_folha20_M1` do bloco 7, nos
  horizontes **1, 4, 8 e 12**. Origem = `data_alvo − h` semanas.
- **Contexto de cada previsão:** a série semanal de `casos_confirmados` de **18/02/2018 até a origem,
  inclusive**. Nada depois da origem entra, nem em covariável.
- **Covariáveis de clima:** `temp_media`, `temp_max`, `umid_media` e `pressao_media`. São as variáveis-base
  das 6 colunas de clima que o projeto escolheu. Entram cruas, sem defasagem: o modelo vê a história delas.
- **Covariável de vetor:** `aedes_aegypti_por_armadilha`, crua.
- **Buracos na covariável**, como as semanas da enchente de 2024: passados como `NaN`, se a biblioteca
  aceitar. Se não aceitar, a solução vira emenda datada antes de ler resultado.
- **Previsão usada:** o quantil **0,85** do horizonte `h`, o mesmo quantil do projeto. Previsão negativa
  vira 0.
- **Configuração dos modelos:** a padrão da biblioteca, em CPU. Sem ajuste fino e sem aprendizado
  cruzado entre séries.
- Revisões dos pesos fixadas em [AMBIENTE.md](AMBIENTE.md).

---

## 3. Travas, antes de ler qualquer resultado

1. **Pareamento:** cada braço tem os mesmos pares `(h, data_alvo)` do `B0`, com **102** semanas por
   horizonte na avaliação.
2. **Sem futuro no contexto:** para toda previsão, a última data do contexto é exatamente a origem.
3. **Determinismo:** 5 origens sorteadas, previstas de novo, dão resultado idêntico.
4. **Coerência:** q0,85 ≥ q0,5 em toda previsão.
5. **Âncoras dos comparadores:** o `B0` reproduz MAE **133,6 / 199,6 / 223,2 / 243,8**; a régua sazonal
   reproduz **202,1 / 213,2 / 216,2 / 217,8**.

Se uma trava falhar, nada é lido.

---

## 4. Métrica, teste e famílias

- **Métrica primária:** MAE do q0,85, pareado por `data_alvo`, avaliação `data_alvo ≥ 2024-01-01`.
- **Teste:** Wilcoxon bilateral do erro absoluto, pareado.
- **Família H1 — bate a régua sazonal?** 4 braços × h 4, 8, 12 = **12 comparações**, Holm sobre 12.
- **Família H2 — melhora o B0?** 4 braços × h 1, 4, 8, 12 = **16 comparações**, Holm sobre 16.
- **Família H3 — o vetor vale dentro do Chronos-2?** `c2_casos_clima_vetor` × `c2_casos_clima` × h 1, 4,
  8, 12 = **4 comparações**, Holm sobre 4.

### Leituras descritivas, sem teste

- MAE da **mediana** contra a régua: ponto contra ponto, sem o viés para cima do 0,85.
- Perda quantílica 0,85 e **cobertura** do q0,85, a fração de semanas com o real abaixo dele. O nominal
  é 0,85.
- MAE na calibração epidêmica 2022-2023, por ano do alvo e em semanas com `real ≥ 100` e `real < 100`.

---

## 5. Critérios de decisão

- **Bate a régua** se, em **h=12**, o MAE for menor que o da régua sazonal com **p Holm H1 < 0,05**.
- **Melhora o modelo** se, em **h=12**, o MAE for menor que o do `B0` com **p Holm H2 < 0,05**.
- **O vetor vale no Chronos-2** se, em **h=12**, o braço com vetor tiver MAE menor com **p Holm H3 < 0,05**.
- **Candidato à rodada confirmatória 2026-2027** se bater a régua **ou** melhorar o modelo, **e** não for
  pior que o `B0` em h=12 na calibração epidêmica.
- Nada troca a referência nesta rodada.

---

## 6. Ameaças já conhecidas

- 🔴 **Contaminação do pré-treino.** Não se sabe exatamente quais séries estão no treino dos modelos. Séries
  públicas de dengue do Brasil, como as do InfoDengue, podem estar lá.
  - O Chronos-2 é de **outubro de 2025**: pode ter visto as temporadas 2024 e 2025, que são a avaliação.
  - O Chronos-Bolt é de **fim de 2024**: não pode ter visto 2025.
  - Por isso a leitura por ano do alvo é obrigatória. A única avaliação livre de contaminação é
    **2026-2027**, posterior aos dois.
- **Duas temporadas de avaliação**, as maiores da série.
- **O corte de maturidade age só no fim da série.** Os casos do contexto aparecem maduros, como em todos
  os braços do projeto.
- **Quatro braços no mesmo período:** um resultado positivo aqui é hipótese para 2026-2027, não conclusão.

---

## Emendas

- **25/09/2026, antes da rodada completa:** a trava 5 aceita diferença de até **±0,15** no MAE, porque as
  âncoras acima têm uma casa decimal. Decisão do agente implementador, registrada aqui antes de qualquer
  resultado. A régua e o B0 bateram as âncoras com folga dentro disso.
