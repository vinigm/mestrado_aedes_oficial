# Varredura de literatura — previsão de dengue de 1 a 3 meses

> **Rodada em 25/09/2026**, a pedido do Vinicius, depois de a [régua das regras simples](../2026-09-25_regua_regras_simples/)
> mostrar o modelo perdendo para a regra "mesma semana do ano passado" em 2 e 3 meses.
> Quatro pesquisadores independentes, um por ângulo, e um verificador adversarial para cada um.

---

## Em uma frase

**Perder para uma régua estatística simples em 3 meses é o resultado comum da literatura, não uma falha
exclusiva do projeto** — e o que costuma vencer a régua nesse horizonte são ensembles heterogêneos, não
um algoritmo melhor.

---

## 1. Pergunta e método

**Pergunta:** o que a literatura usa de dados, atributos, modelos e réguas para prever dengue com 1 a 3
meses de antecedência, e o que venceu a régua sazonal nesse horizonte?

| Ângulo | Arquivo | Verificação |
|---|---|---|
| 1. Atributos e fontes de dados | [`1_atributos.md`](1_atributos.md) | [`verificacao_1_atributos.md`](verificacao_1_atributos.md) |
| 2. Modelos e formulação do alvo | [`2_modelos_e_alvo.md`](2_modelos_e_alvo.md) | [`verificacao_2_modelos_e_alvo.md`](verificacao_2_modelos_e_alvo.md) |
| 3. Avaliação e réguas | [`3_avaliacao_e_reguas.md`](3_avaliacao_e_reguas.md) | [`verificacao_3_avaliacao_e_reguas.md`](verificacao_3_avaliacao_e_reguas.md) |
| 4. O vetor como preditor | [`4_vetor_como_preditor.md`](4_vetor_como_preditor.md) | [`verificacao_4_vetor_como_preditor.md`](verificacao_4_vetor_como_preditor.md) |

- Cada pesquisador devolveu os **10 achados mais importantes**; o verificador tentou refutar cada um na fonte.
- **Resultado da verificação, 40 achados:** 32 confirmados · 6 parciais · 2 não verificáveis · **0 refutados**.
- Os 2 não verificáveis são alegações de **ausência**, como "nenhum trabalho usa o resíduo sobre o ano
  anterior como alvo". Ausência não se prova; os dois verificadores também não acharam contraexemplo.
- ⚠️ Parte das confirmações da PNAS veio de trechos indexados pela busca, porque o site bloqueou a leitura
  direta. Está marcado em cada arquivo de verificação.

---

## 2. 🔴 Um trabalho gêmeo da tese, publicado em 2026

**da Silva, Ferreira, Lourenço & Freitas (2026), PLOS NTD**, DOI `10.1371/journal.pntd.0014201`.

- **Mesma cidade e mesma fonte de dado:** armadilhas MosquiTRAP/MI-Aedes de Porto Alegre + casos do
  SINAN/InfoDengue, 2018-2025.
- **FATO:** a correlação de Kendall entre infestação e incidência cresce com a defasagem:
  τ = **0,27** no lag 0 · **0,50** no lag 4 · **0,59** no lag 8 semanas.
- **FATO:** o modelo com o vetor tem R² **0,46** e MAE **0,79**, contra R² **−0,07** do modelo só com clima,
  prevendo incidência em log.
  - ⚠️ O relatório do pesquisador trazia MAE 0,19. **Está errado:** 0,19 é de outro modelo do mesmo
    artigo, o que prevê o próprio vetor. Corrigido pelo verificador na fonte.
- **O que ainda não se sabe:** o horizonte de previsão desse R² e se o desenho é fora da amostra.
  Ler o artigo inteiro é pendência.
- **Por que importa:** a pergunta "o vetor ajuda a prever dengue em Porto Alegre?" já tem uma resposta
  publicada, e positiva. O diferencial da tese precisa ser explícito diante dele.

---

## 3. O que a literatura diz sobre o problema do projeto

### Perder para a régua em 3 meses é comum

- **Johansson et al. 2019, PNAS:** no Dengue Forecasting Project, 16 equipes e 8 temporadas, um SARIMA
  simples teve a melhor calibração geral e a maior habilidade na semana do pico.
- **Benedum et al. 2020, PLOS NTD:** Random Forest vence ARIMA em 4 semanas por 21-33%, mas **perde em 12
  semanas** em Iquitos e Singapura.
- **Sprint InfoDengue-Mosqlimate 2024, PNAS 2026:** 6 equipes, 5 estados. Nenhum modelo se destacou de
  forma consistente, em especial no ano atípico de 2024, com mais casos que a década anterior somada.
- **Nenhum dos trabalhos de atributos lidos compara o modelo com "a mesma semana do ano anterior".** O
  achado do projeto não tem contraponto direto.

### O que venceu a régua

- **Colón-González et al. 2021, PLOS Medicine:** superensemble no Vietnã, CRPS **66,8 contra 79,4** da régua
  sazonal em 1-3 meses. A vantagem **desaparece em 4-6 meses**.
- **Wu et al. 2025, PNAS:** ensemble de 11 modelos heterogêneos em mais de 180 locais, erro percentual de
  38,5 / 54,5 / 62,7% em 1 / 2 / 3 meses, melhor que o melhor modelo isolado.
- **Cramer et al. 2022, PNAS:** no COVID-19 Forecast Hub, só o ensemble venceu a régua em todas as
  localidades.

### Sobre o vetor

- **Sedda et al. 2020, Acta Tropica:** a taxa de crescimento do vetor superou a abundância bruta como
  preditor. A diferença de WAIC é pequena: 503,88 contra 505,34.
- **Ribeiro et al. 2021, Cad. Saúde Pública:** o índice predial do LIRAa previu mal a dengue no Rio, e de
  forma inconsistente de ano para ano.
- **Córdoba, Argentina, 2009-2017:** cidade temperada, e a dengue autóctone **não** se associou ao vetor
  nem ao clima; o pico seguiu os casos importados.

### Sobre avaliação

- A régua padrão é **sazonal ou de persistência**, e o resultado se reporta como **skill score por
  horizonte**, nunca agregado.
- Com poucas temporadas, a literatura recomenda Diebold-Mariano com correção para amostra pequena
  (Coroneo et al. 2023).
- A perda quantílica do projeto é a peça que compõe o WIS, a métrica dos sprints (Bracher et al. 2021).

---

## 4. Das ideias ao teste

### Entraram na [bateria de formulação do alvo](../2026-09-25_bateria_formulacao_do_alvo/)

| Ideia | Base |
|---|---|
| Ensemble do modelo com a régua sazonal | Colón-González 2021, Wu 2025, Cramer 2022 |
| Taxa de crescimento do vetor | Sedda et al. 2020 |
| Modelo linear que extrapola | SARIMA e ARIMA vencendo em 12 semanas |
| Casos da semana-alvo do ano anterior como atributo | lacuna: nenhum trabalho localizado |
| Resíduo sobre o ano anterior como alvo | lacuna: nenhum trabalho localizado |

### Ficaram de fora, e por quê

- **Modelos de fundação de séries temporais**, como Chronos e TimesFM, em modo zero-shot: nenhuma aplicação a
  dengue encontrada. Exigem instalar pacote e baixar pesos, o que precisa de autorização.
- **Alvo categórico de risco**, com acerto de tercil (Lowe et al. 2016: 57% contra 33% da régua em 3
  meses): muda a pergunta. Cabe na métrica de alarme, não na regressão.
- **Estabilidade do período entre surtos** (Rypdal & Sugihara 2019): é um atributo por temporada, e com 4
  temporadas o modelo teria 4 valores para aprender.
- **Vetor defasado 8 semanas:** a correlação sobe até o lag 8 em da Silva 2026, mas o projeto já testou
  5-12 semanas no vetor em 23/09 e não ajudou.
- **Google Trends:** só ajudou em nowcasting de atraso de notificação; em previsão, piorou (Vietnã 2026).
- **Sorotipo circulante:** Porto Alegre não tipa sorotipo de forma rotineira.
- **Pipeline de dois estágios**, prever o vetor e usar a previsão: nenhum trabalho lido fez; fica como
  candidato para depois.

---

## 5. Limitações

- Leitura por resumo e texto aberto. PNAS e parte do PMC bloquearam a leitura direta.
- 10 achados por ângulo é um recorte: os arquivos detalhados têm mais trabalhos que o retorno.
- A varredura não é revisão sistemática. Não há protocolo PRISMA nem busca exaustiva.
