⚠️ **RASCUNHO — NÃO APROVADO E NÃO RODADO.** Escrito em 26/09/2026 por desenho de 3 agentes. Só vira
pré-declaração válida depois que o Vinicius aprovar. Nenhum número novo foi medido para escrevê-lo.

---

## 1. Pergunta

Trocar o alarme binário atual ("surto = **100** casos/semana, convenção do projeto) pelos **4 estágios**
do Plano Municipal de Contingência de Arboviroses 2026 da SMS-POA (Quadro 1, p. 15), convertidos para
casos/semana: **Normalidade** (< 140) · **Mobilização** (> 140) · **Alerta** (> 421) · **Epidemia** (> 702).

---

## 2. Veredito do cético — vem antes de tudo

**SÓ SE**, com escopo cortado pela metade do pedido original.

- **Fazer sem rodada nova:** trocar o rótulo "surto = 100" por "Mobilização = 140" na documentação. É
  **decisão institucional**, não achado — a troca muda **1 semana em 121** (38/39, nesting de 97%).
- **Fazer como extensão:** somar `E_140` à família **já aberta** em `2026-09-25_alarme_contra_canal_endemico/rodar.py`
  (McNemar pareado, h=4/h=12, modelo × R_hoje/R_ano_passado) — não abrir família nova de Holm para isso.
- **Não fazer:** tratar Alerta (421) e Epidemia (702) como confirmatório com Youden "vencendo". Nascem de
  **2 episódios só** (2024, 2025) — 702⊂421⊂140 em **100%** (23/23 e 28/28), é o mesmo teste com corte
  deslizante, não 3 eventos independentes.
- **Condição para valer:** pré-declarar a métrica (Youden) e a família **antes** de rodar, e aceitar
  publicar mesmo que 3 meses repita a derrota para a régua sazonal (Youden 0,81 da régua × 0,66 do modelo).

---

## 3. Hipóteses

**Alvo escolhido:** 3 alarmes binários **aninhados** — `E_140` (Mobilização), `E_421` (Alerta), `E_702`
(Epidemia) — reaproveitando a *family* do `rodar.py` de 25/09, só trocando o limite.

- **Por quê aninhado, não ordinal:** com **2 episódios** (2024, 2025) a matriz 4×4 (Normalidade → Epidemia)
  não tem células suficientes para estimar variância entre classes com poder. QWK e MAE ordinal ficam
  leitura **descritiva**, sem p-valor, nunca teste confirmatório.
- **H1 (confirmatória):** o alarme do modelo em cada estágio vence `R_ano_passado` e `R_hoje` em Youden,
  com significância após Holm.
- **H0:** não vence — repete o padrão de `E_100`/3-meses, onde `R_ano_passado` empata ou vence.

---

## 4. Métricas e comparadores

- **Por estágio:** sensibilidade, precisão, especificidade, Youden, falsos-por-ano (as 5 já calculadas no
  `rodar.py` de 25/09). Matriz de confusão **2×2 por estágio**, nunca 4×4 conjunta.
- **QWK / MAE ordinal:** reportar o número, sem teste de hipótese em cima — descritivo.
- **Comparadores obrigatórios:** `R_ano_passado` (já vence o modelo em `E_100`/3-meses: Youden 0,81 × 0,66)
  e `R_hoje` (o modelo já vence este com significância). Estágio novo só conta como ganho se vencer
  `R_ano_passado` com p_holm < 0,05 — vencer só `R_hoje` não é suficiente.
- ⚠️ **Divergência não resolvida — métrica de decisão:**
  - **Opção A (estatístico/cético):** Youden puro, pesos iguais para falso alarme e surto perdido.
  - **Opção B (operacional):** métrica assimétrica, peso(perder Epidemia) ≫ peso(falso alarme de
    Mobilização), usando a razão do quantil já adotado (0,85/0,15 ≈ **5,7×**) como ponto de partida.
  - **Vinicius decide** qual entra no critério de decisão antes de rodar — não dá para pré-declarar as duas.

---

## 5. Família de correção múltipla

⚠️ **Divergência não resolvida — escopo e método:**

| Opção | Testes | Horizonte | Família de Holm |
|---|---|---|---|
| **A — Cético** | `E_140` só, 2 modelos × 2 regras × h=4/h=12 = **8** | 4 e 12 | Somada à família **já existente** de 25/09 (16→24 testes); 421/702 ficam fora do teste, só descritivos |
| **B — Estatístico** | 3 estágios × 1h × 2 modelos × 2 regras = **12** | h=12 só (único em disputa) | Família **nova**, separada da de 25/09 |
| **C — Operacional** | 3 estágios × até 4h × 2 × 2 = até **48** | h=1 (Mobilização) / h=4-8 (Alerta) / h=12 (Epidemia) | Não especificada — provável inviável (poder) |

- A família cheia (3 estágios × 2h × 2 modelos × 2 regras = 24) é descartada pelos três agentes: com
  `n_surto` de 23 a 38 e **n efetivo de ~2 episódios**, Holm sobre 24+ testes mata o poder.
- **Vinicius decide entre A e B** (C é descartada por inviabilidade de poder, mantendo só a leitura
  descritiva por estágio nos horizontes 1/4-8/12 que o operacional pediu).

---

## 6. Critério de decisão (escrito para poder falhar)

- **Estágio "vence"** se, no horizonte testado, o alarme do modelo supera `R_ano_passado` em Youden **e**
  a diferença sobrevive a Holm (p < 0,05) na família escolhida (opção A ou B do item 5).
- **Estágio "não vence"** se perder ou empatar com `R_ano_passado`, mesmo vencendo `R_hoje`.
- **Resultado esperado, pré-declarado:** réplica do padrão de `E_100`/3-meses — Mobilização deve repetir
  quase 1:1 o resultado de 100 (nesting 97%); Alerta e Epidemia continuam descritivos, sem veredito de
  vitória/derrota.
- **Aceite obrigatório:** publicar mesmo se o resultado repetir a derrota para a régua sazonal.

---

## 7. Confirmatório × descritivo

- **Confirmatório (se aprovado):** `E_140` em h=4 e h=12 (opção A) **ou** os 3 estágios em h=12 (opção B).
- **Descritivo, sempre:** Alerta (421) e Epidemia (702) fora da opção B; QWK/MAE ordinal; qualquer leitura
  por episódio (só 2 casos, 2024 e 2025); ranking de braços no estágio Epidemia (n=23).

---

## 8. Fidelidade ao plano

| Elemento do Quadro 1 | Status no projeto | Direção do viés |
|---|---|---|
| Corte de incidência (10/30/50 por 100mil → 140/421/702 casos/semana) | **Reproduzível** (a única parte usada) | — |
| Condição **E** com Limite de Alerta / Limite Superior Endêmico (canal do RS, casos prováveis) | **Impossível hoje** — falta a série estadual de prováveis | Nossa versão **relaxa** o critério → dispara **mais** que o oficial |
| Gatilho por óbito confirmado ou sorotipo novo | **Impossível hoje** — não modelado | Dispara **menos** só nos raros casos em que só óbito/sorotipo ativariam o estágio |
| Janela de 4 semanas (histerese: entra por máximo, sai por mínimo) | **Aproximável** — `rolling(4)` já disponível na infra | — |
| Base populacional "por 100 mil" | **Inferência** — o plano não declara a base; usamos 1.404.269 | Se a base oficial for outra, os cortes em casos/semana mudam |

- **Nunca escrever "conforme o Plano Municipal" ou "critério oficial".** Rotular sempre: "patamares
  numéricos do Plano (140/421/702), sem a condição de canal estadual, óbito ou sorotipo — **simplificação
  declarada**".

---

## 9. Trava de validação

Reproduzir antes de qualquer teste novo (mesmo cenário adotado, evento `E_100`, `rodar.py` de 25/09):
**h=4** sensibilidade 0,971 / precisão 0,943 / falsos 0,7 · **h=12** sensibilidade 0,769 / precisão 0,811 /
falsos 2,3. Tolerância: 0,002 em proporção, 0,05 em falsos/ano. Se não bater, **investigar, nunca forçar**.

---

## 10. Ameaças, sem suavizar

- **Poder (a mais grave):** 121 semanas, mas só **2 episódios reais** — semanas de surto são serialmente
  correlacionadas dentro do episódio, então o **N efetivo é ~2**, não 23-38. McNemar/Holm tratam cada
  semana como par independente: **infla a significância nominal**. Só diferenças ≥20-25 p.p. de
  sensibilidade são detectáveis no estágio mais raro (702, n=23, erro-padrão ~10 p.p.).
- **Aninhamento é fato medido, não hipótese:** 702⊂421 = 100% (23/23) · 421⊂140 = 100% (28/28) ·
  140≈100 = 97% (38/39). Os "3 estágios" são o mesmo corte deslizante sobre os mesmos 2 episódios.
- **Pesca de resultado:** se o motivo real é "achar um limiar em que o modelo bata a régua", é p-hacking
  disfarçado de adoção institucional. Só deixa de ser se a métrica e a família forem travadas antes.
- **Base rate:** Mobilização (140) ocorre em 31% das semanas (38/121) — pode ser o modelo aprendendo o
  calendário, não anomalia real.
- **Precedente ruim:** regra importada (Malásia) teve Youden −0,05; canal endêmico deu limite 0 fora de
  temporada. Nada indica que um limiar externo (RS-calibrado) performe melhor aqui.
- **Citação:** usar 140/421/702 como "critério oficial" pleno repete o erro já identificado em 25/09 (falta
  o **E** com LA/LSE).

---

## 11. Custo estimado

- **Execução:** baixo. Reaproveita previsões já salvas (bateria de 23/09) e a estrutura do `rodar.py` de
  25/09 — só troca de constantes (`LIMITE_E100` → 140/421/702) e adição do branco de custo assimétrico, se
  a opção B do item 4 for escolhida. **Sem treino de modelo, sem walk-forward novo.**
- **Base do cálculo:** o script de 25/09 já roda em segundos de CPU (lê CSV, calcula métricas e McNemar
  sobre séries semanais curtas) — não se qualifica como "rodada longa" (não precisa aviso prévio de
  >15-30 min).
- **Trabalho humano-agente:** estimar ~1 sessão de Sonnet para estender o script + reexecutar a trava do
  item 9, dado que a lógica e a infraestrutura já existem prontas.

---

**Decisões que faltam do Vinicius:** (1) métrica do item 4 (Youden puro × assimétrico) · (2) escopo/família
do item 5 (opção A × B) · (3) aprovar ou não o rascunho como um todo.

---

## 12. Adendo do orquestrador, 26/09/2026 — dois reparos no rascunho

**Reparo 1 — o aninhamento é aritmética, não achado.** O rascunho apresenta "702⊂421⊂140 em 100%" como
medição. É verdade **por construção**: os limiares são encaixados, então toda semana acima de 702 está acima
de 421. Isso não enfraquece o argumento do cético, mas não pode ser citado como evidência empírica.

**Reparo 2 — o número que importa não é 39 semanas, é 2 blocos.** Medido agora, na avaliação de 121 semanas:

| Limiar | Semanas acima | **Blocos contíguos** | Maior bloco |
|---|---|---|---|
| 100 | 39 | **2** | 20 semanas |
| 140 | 38 | **2** | 20 semanas |
| 421 | 28 | **2** | 14 semanas |
| 702 | 23 | **2** | 12 semanas |

- **Todo limiar dá exatamente 2 blocos**, um em 2024 e outro em 2025. As "39 semanas de surto" são **2
  eventos** de ~20 semanas cada, não 39 observações independentes.
- 🔴 **Isso não é problema só desta rodada.** Todo teste de alarme do projeto — incluindo o de 13/09, que é o
  único resultado que sobrevive a Holm — usa McNemar tratando **semana** como par independente. Semanas dentro
  do mesmo bloco são fortemente correlacionadas, então o p nominal é **otimista** e a direção do viés é
  conhecida: contra a hipótese nula, ou seja, a favor de achar significância.
- ⏳ **Pendência nova, que precede esta rodada:** estimar o quanto o p é inflado, por bloco-bootstrap ou
  por teste em nível de episódio. Até isso existir, **todo p de alarme do projeto deve ser citado com essa
  ressalva**, inclusive o p Holm 0,037 de 13/09.
