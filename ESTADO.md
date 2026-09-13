# ESTADO — o que o projeto É hoje

> Retrato honesto do sistema. **Atualizado em 13/09/2026**, depois da correção do vazamento temporal.
>
> Fila de trabalho: [PENDENCIAS.md](PENDENCIAS.md) · Por que cada teste foi feito e o que deu:
> [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md)
>
> Regra deste documento: **honestidade acima de marketing**. Fato e hipótese vêm rotulados.

---

## 1. Os dados

| Camada | Onde | Regra |
|---|---|---|
| **Datalake** | `.../arquivos_secretaria_saude_poa/brutos_secretaria/` | **NUNCA tocar.** 12 arquivos originais, com defeitos e dado pessoal. |
| **Warehouse** | `.../limpos_secretaria/` | Um arquivo por ano, sem dado pessoal. Regenerável. Nunca editar à mão. |
| **Produto** | `.../secretaria_poa_armadilhas.parquet` | A fonte que todo o resto consome. **Preferir o parquet.** |

✅ **FATO — a base certificada** (conferida célula a célula em 13/09/2026):
**636.587 inspeções · 236.166 fêmeas de _Aedes aegypti_ · 718 semanas** (23/09/2012 a 09/08/2026) ·
**81 bairros · 2.742 armadilhas**.

- Faltam 7 semanas em 14 anos: 4 antigas fora de temporada e **3 da enchente de maio/2024**
  (28/04, 05/05, 12/05), quando as vistorias pararam.
- **Duas fontes, sem vão:** Secretaria (2012–2025) + raspagem própria (2026 em diante).
- ⚠️ **A raspagem é manual.** Sem cron, sem launchd. O weekid 458 (05–11/10/2025) nunca foi raspado —
  sem prejuízo, porque a Secretaria cobre 2025. De 2026 em diante seria irrecuperável.

### Armadilhas do dado (ler antes de analisar)

- ⚠️ `id_inspecao` **não é único** em 2012–2019 e 2021. Nunca deduplicar por ele nesses anos.
- ⚠️ `data_banco` tem ~18% de valores invertidos em 2019 e 2021. **Não usar analiticamente.**
- ⚠️ `inspecao_realizada` vazia em 2012–2018 → denominador aproximado, marcado por `denominador_aproximado`.
- ⚠️ `codigo_tubito_*` é número de tubo, não contagem. Nunca somar.
- ⚠️ 2,2% das linhas sem coordenada.
- ⚠️ **Densidade e contagem têm numeradores diferentes:** `aedes_aegypti_por_armadilha` usa só **fêmeas**;
  `aedes_aegypti` soma machos e fêmeas.
- ⚠️ **Casos só existem a partir de 18/02/2018** (428 semanas). Não há 14 anos de casos.

### Bases legadas (preservadas, fora do fluxo)

**Marília 2019–2023** é o padrão-ouro de validação — foi ela que provou a correção das datas.
**Raspagem própria de 2025**: conferência independente. Nunca apagar nenhuma das duas.

---

## 2. O código

- Pipeline integrado à base certificada. `tabela_final.csv`: **725 semanas × 36 colunas**, grade contínua.
  - semana sem inspeção = **NaN**, nunca zero inventado;
  - densidade = fêmeas ÷ armadilhas **inspecionadas**;
  - casos: NaN antes de 2018 e depois da última semana divulgada.
- **Corte de maturidade é decisão de EXPERIMENTO**, não da camada de dados. Ancora na última semana
  **com** caso divulgado, não no fim da tabela.
- ✅ **13/09/2026 — o corte de treino do walk-forward foi corrigido.** A regra vive num lugar só,
  `modelagem_aedes/motor/corte_temporal.py`: só entra no treino a linha cuja **resposta** já tinha acontecido na data da
  previsão. Aplicada em 5 pontos de produção. Ver [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md) §6.1.
- Testes: **22/22 passando** (`pytest tests -q`).
- ⚠️ **`modelagem_aedes/config/experimentos/cidade_referencia.py` está desatualizado** — aponta para quantil 0,80, que
  deixou de ser a vencedora.

---

## 3. Os resultados

**Todos os números abaixo são pós-correção.** O que cada teste perguntou e por quê está em
[HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md).

### 3.1 O modelo de casos

✅ **FATO — a configuração de referência é HistGradientBoosting · `quantile=0.85` · com vetor**,
vencedora entre as 30 testadas pelo menor erro de calibração.

| Horizonte | MAE | R² | Captura do pico |
|---|---|---|---|
| 1 semana | 98,0 | **0,898** | 0,886 |
| 4 semanas | 219,7 | **0,628** | 0,702 |
| 8 semanas | 272,6 | **0,450** | 0,417 |
| 12 semanas | 278,7 | **0,437** | 0,388 |

- ✅ **O modelo é honesto até um mês.** Em três meses explica 44% da variação.
- ⚠️ **A previsão quantílica estima um patamar**, ultrapassado em 15% das vezes, não a média. Precisa
  estar declarado em qualquer texto que cite uma previsão.
- ⚠️ Escrever **"a melhor entre as 30 testadas"**, nunca "a melhor possível".
- ✅ **A degradação tem causa medida:** a autocorrelação dos casos explica 91% em h=1 e **0%** em h=12.

### 3.2 O vetor na previsão de casos

✅ **FATO — não há efeito demonstrável.** 60 comparações pareadas (15 pares × 4 horizontes):
o vetor erra menos em **27 de 60**, e **nenhuma sobrevive a Holm**.

⚠️ Onde ele ganha, ganha compensando algoritmo fraco: em h=12 os 5 maiores ganhos são as 5
configurações de LightGBM; o HistGradientBoosting fica entre +8,9 e −11,2.

### 3.3 O vetor no alarme de surto

🔴 ✅ **FATO — o vetor PIORA o alarme em três meses, e é o único resultado do projeto que sobrevive a
Holm.** Alvo notificados, P90, h=12, n=553: o só-clima acerta onde o clima+vetor erra em **23 semanas**,
contra 7 no sentido inverso. p bruto **0,0062**, Holm **0,037**.

⚠️ Robusto, porém **não pré-declarado** nessa direção. Vira confirmatório só com a temporada 2026-2027.

### 3.4 A camada espacial

✅ **FATO — a regra simples vence o aprendizado de máquina em 8 de 8 combinações.** A persistência
("a ordem de hoje vale para daqui a h semanas") bate o modelo em todas.

✅ **FATO — mas o sinal espacial é real:** persistência 0,89 contra climatologia 0,46 em h=1. Nenhuma
das duas treina, logo nenhuma tinha vazamento.

**Entrega possível:** um protocolo de priorização de zonas transparente e sem infraestrutura.

### 3.5 Os dados

✅ **FATO — treinar desde 2012 vence em 3 de 4 horizontes**, e a vantagem cresce com o horizonte. Os
14 anos resgatados melhoram a previsão. (Alvo: densidade do vetor. Para casos, nunca testado.)

✅ **FATO — o alvo é casos confirmados**, decidido por medição em 30/08/2026.

### 3.6 O que NÃO se pode afirmar

- 🚫 **"O vetor melhora a previsão de casos."** 0 de 60 em Holm.
- 🚫 **"A equivalência clima × vetor está demonstrada."** Com a margem pré-declarada e o alvo decidido:
  1 de 8.
- 🚫 **"A função de perda importa mais que o algoritmo."** Sem vazamento: perda +9,9%, algoritmo +11,8%.
- 🚫 **"Estas 6 variáveis de clima são as que importam."** Recortando a série em 2023, 4 das 6 mudam.

---

## 4. Direção da tese — **em revisão desde 13/09/2026**

**A pergunta continua de pé: "Quanto vale a rede de armadilhas para a vigilância de dengue em Porto
Alegre?"** O que caiu foi a resposta que estava sendo montada.

🚫 **O núcleo proposto em 29/08 — a equivalência clima × vetor — está refutado.** Não por falta de
poder: são 576 a 587 semanas pareadas.

### O que sobrevive, e é material de tese

1. **A contribuição de dados.** A série de 14 anos resgatada, corrigida, certificada e documentada.
   Ninguém mais tem. E há evidência de que ela melhora a previsão do próprio vetor.
2. **Um resultado negativo forte e bem medido.** A armadilha não melhora a previsão de casos e
   **piora** o alarme de surto em horizonte longo, com correção de múltiplas comparações e 553 semanas.
   Resultado negativo pré-declarado é publicável e é o que falta na literatura da área.
3. **A camada espacial como entrega operacional.** Protocolo simples de priorização de zonas que vence
   o ML em 8 de 8, com sinal espacial real.
4. **A contribuição metodológica.** O vazamento temporal, medido em +52% de MAE em h=12, e a
   demonstração de que ele **não é neutro**: favorece exatamente as escolhas que o projeto tinha
   adotado. É defeito que a literatura da área comete.

⏳ **Decisão pendente do Vinicius:** qual desses vira o eixo. Não há proposta fechada — a de 29/08 caiu.

**Escopo fechado, não reabrir:** casos existem só em nível cidade (Comitê de Ética inviável no prazo);
o eixo espacial é entomológico puro, sobre zona sintética; decisões de método são nossas, pré-declaradas
por escrito antes de rodar.

---

## 5. O painel publicado

- No ar: **https://vinigm.github.io/mestrado_aedes_oficial/**
- Gerado por `pagina_web/gerar.py` → `docs/`.

🔴 **O painel publica hoje quatro números que sabemos estarem errados**, todos anteriores à correção:

| No site | Correto |
|---|---|
| R² 0,758 em h=12 | **0,437** |
| Trocar a perda custa +20,2% | **+9,9%** |
| "A melhor entre as 30" (quantil 0,80) | Agora é quantil 0,85; a antiga é 3ª |
| Captura do pico 98/92/70/62% | 89/70/42/39 |

⚠️ **Risco adicional:** o painel lê a execução **mais recente de cada nome** no MLflow. Como só parte
dos experimentos foi refeita, gerar o site agora **mistura números corrigidos e não corrigidos** sem
aviso ao leitor.

⏳ **Nada foi publicado.** O gerador não foi rodado. Ver [PENDENCIAS.md](PENDENCIAS.md).

---

## 6. Fonte da verdade (ordem por pergunta)

- **"O que o sistema FAZ hoje?"** → o código vivo em `modelagem_aedes/` vence sempre.
- **"O que os dados dizem?"** → o parquet certificado; depois
  `../Contexto/01_projeto_pesquisa/base_unificada_armadilhas.md`.
- **"O que já foi testado e o que deu?"** → [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md).
- **"O que está em aberto?"** → [PENDENCIAS.md](PENDENCIAS.md).
- **"O que o sistema DEVERIA fazer?"** → a decisão pré-declarada mais recente vence, inclusive sobre o
  código. A diferença é ⏳ pendência, não contradição.
