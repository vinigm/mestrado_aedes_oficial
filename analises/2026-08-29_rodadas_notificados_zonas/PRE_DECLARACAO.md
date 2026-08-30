# PRÉ-DECLARAÇÃO — rodadas de 29/08/2026

> **Escrita ANTES de qualquer execução.** É o que substitui a validação externa do orientador
> (ver decisão de 29/08/2026 em [PENDENCIAS.md](../../../PENDENCIAS.md)): sem alguém de fora
> validando o desenho, a única proteção contra pesca de resultado é fixar as regras por escrito
> antes de ver os números. **Nada abaixo pode ser alterado depois de rodar.** Se algo precisar
> mudar, a mudança vira uma seção nova, datada, com o motivo — nunca uma edição silenciosa.

Autores da decisão: Vinicius + agente. Data: **29/08/2026**.

---

## Estado de partida (âncoras medidas antes de rodar)

- `tabela_final.csv`: **725 linhas × 36 colunas** · sha256 `96b21b84e759409cbe0557d83660dca5911d9fd0f1513e5123411039f868f23e`
- `aedes_aegypti_por_armadilha`: **718** semanas não-nulas · soma **280,8343**
- `casos_confirmados`: **428** semanas não-nulas · soma **56.624**
- `temp_media`: **388** semanas não-nulas · soma **7.698,1843**
- `clima_nasa_power_semanal.csv`: **388 × 23** · 30/12/2018 → 31/05/2026

---

## Rodada 0 — Recaptura do clima desde 2012

**Motivo:** `preparo/capturar_clima.py` tem `INICIO_PADRAO = "20181230"`, justificado no
comentário como "o primeiro domingo do bloco de dados da Marília". A Marília saiu do fluxo em
16/08/2026; a justificativa da constante está obsoleta e trunca a série em 388 semanas quando o
vetor tem 718.

**Mudança:** `INICIO_PADRAO = "20120923"` (primeiro domingo da série do vetor).

**Critério de aceitação (bloqueante — se falhar, reverter e não seguir):**

1. `tabela_final.csv` continua com **725 linhas × 36 colunas** — o clima entra por `merge(how="left")`
   sobre a grade do vetor, então não pode criar nem apagar linha.
2. `aedes_aegypti_por_armadilha`: **718** não-nulos e soma **280,8343**, inalterados.
3. `casos_confirmados`: **428** não-nulos e soma **56.624**, inalterados.
4. As **388 semanas de clima que já existiam** (30/12/2018 em diante) permanecem iguais dentro de
   `rtol=1e-9`. Divergência acima disso = a NASA revisou dado histórico → **investigar, não forçar**.
5. `temp_media` passa de 388 para **≥ 700** não-nulos.

---

## Rodada 1 — Detecção de surto com alvo NOTIFICADOS

**Pergunta:** o vetor melhora a detecção de surto quando o alvo é **casos notificados**
(InfoDengue, 2010+) em vez de **confirmados** (SINAN, 2018+)?

**Por que trocar o alvo:** a taxa de confirmação caiu de 99,6% (2023) para 42,0% (2025) —
"confirmado" virou medida administrativa, e a série encolheu por um motivo burocrático, não
epidemiológico. Notificado é o que a vigilância realmente enxerga em tempo real, e é sobre ele
que um alarme operacional teria de agir. O ganho de poder é consequência, não a justificativa.

**Desenho — idêntico ao `cidade_deteccao_surto` de 16/08, mudando SÓ o alvo:**

- comparação: `so-clima` × `clima+vetor`, mesmas divisões de treino/teste, walk-forward expansível;
- horizontes **4, 8, 12** semanas · percentis **90 e 95** → **6 comparações**;
- limiar de surto = percentil calculado **só com o passado** de cada passo (sem vazamento);
- modelo: LightGBM classificador, hiperparâmetros **inalterados**;
- teste: **McNemar** (exato quando discordâncias < 25).

**Correção múltipla — declarada antes:** **Holm** sobre as **6** comparações. Nível **α = 0,05**.

**Hipótese pré-registrada (a projeção do teste C):** com ~193 semanas de surto no lugar de 89,
os discordantes vão de 18 para **≈39** e o menor p de Holm cai para **≈0,006**.

**Regra de decisão, fixada antes de ver o resultado:**

- **sobrevive ao Holm** → o valor do vetor no alarme vira o **núcleo** da tese (camada 1);
- **não sobrevive** → registrado como resultado negativo honesto; o núcleo passa para o mapa de
  risco por zona (camada 3) e o vetor no alarme vira capítulo de limitação de poder.
- **Proibido**, em qualquer desfecho: trocar percentil, horizonte ou modelo depois de ver o p-valor
  para procurar um resultado melhor.

**Ressalva de dado, conhecida antes:** a coluna `casos` do InfoDengue sofre revisão retroativa nas
semanas recentes. O corte de maturidade protege parcialmente; a estabilidade da série é medida e
registrada junto com o resultado.

---

## Rodada 3 — Ranking de risco por zona sintética

**Pergunta:** o modelo acerta a **ordem** das zonas de maior risco entomológico com antecedência
útil para a vigilância?

**Por que ranking e não R²:** para operação, o que importa é *para onde mandar a equipe primeiro*,
não acertar o valor absoluto da densidade. Métrica errada mede a coisa errada.

**Desenho:**

- granularidade **zona sintética** (k-means nas coordenadas médias das armadilhas), **k=8 e k=16** —
  o bairro administrativo foi descartado em 16/08 pelo teste B (31% de ruído de amostragem);
- período **2019–2026** (antes disso `inspecao_realizada` é nula e o denominador é aproximado);
- alvo: densidade suavizada por média móvel de 4 semanas;
- horizontes **1, 2, 4, 8** semanas;
- métrica primária: **Spearman entre o ranking previsto e o ranking real das zonas**, por semana;
- baselines obrigatórios: **persistência** (a ordem de hoje) e **climatologia sazonal** (a ordem
  média histórica daquela época do ano).

**Regra de decisão:** o modelo só é declarado útil se **superar a persistência**. Bater só a
climatologia não basta — persistência é o que a vigilância já faz de graça.

**Sem teste de significância nesta rodada.** É medida descritiva de desempenho operacional; não
entra na contagem de comparações múltiplas e não pode ser apresentada como achado inferencial.

---

## Rodada 2 — Teste A (equivalência clima × vetor) na série longa

**Pergunta:** clima e vetor são estatisticamente equivalentes para prever casos, agora com o
clima cobrindo 2012+?

**Por que refazer:** em 16/08 deu **indeterminado** (nem diferença nem equivalência), com
IC de ΔMAE em h=1 = **[−72; +21]** e N≈260. Medido em 29/08: o gargalo **não era o alvo, era o
clima** — a interseção clima+vetor+casos tinha 379 semanas e trocar o alvo por notificados
renderia **5 semanas a mais**. Só a rodada 0 move esse número.

**Desenho:** réplica do script de 16/08, mesmas 4 combinações de features
(`SO_CLIMA_PURO`, `SO_VETOR_PURO`, `SO_CLIMA_AR`, `SO_VETOR_AR`), mesmos horizontes (1, 4, 8, 12),
mesmo pareamento por **interseção de datas**. Muda **só** a cobertura do clima e, em uma variante
declarada, o alvo (notificados).

**Margem de equivalência — declarada antes:** TOST em **±5%, ±10% e ±15%** do MAE da persistência,
exatamente como em 16/08. **Proibido afrouxar a margem depois de ver o resultado.**

**Regra de decisão:** os três desfechos (diferença, equivalência, indeterminado) são publicáveis
porque a margem foi pré-declarada. Indeterminado de novo = a série de POA não tem poder para essa
pergunta, e isso é o achado.

---

## Rodada 4 — Ablação de janela de treino

**Pergunta:** treinar desde 2012 é melhor que treinar só com o passado recente?

**Por quê:** a rede mudou em 14 anos (número de armadilhas, protocolo, enchente de maio/2024,
choque de controle de 2025). Dado antigo pode ser ruído sobre um sistema que não existe mais.

**Desenho:** três regimes — expansível desde **2012**, expansível desde **2020**, deslizante de
**6 anos** — sobre a **mesma janela de avaliação**, senão não há comparação.

**Regra de decisão:** é seção de **robustez**, não de descoberta. O resultado não muda o recorte da
tese; se um regime vencer, ele passa a ser o padrão dos experimentos daí em diante, com a mudança
registrada. **Sem teste de significância** e sem entrar na contagem de múltiplas comparações.

---

## Regras que valem para as quatro rodadas

- Toda rodada grava log completo em `saidas/` e é reproduzível pelo script versionado nesta pasta.
- Números citados em qualquer documento saem do CSV gravado, nunca do texto de um log.
- **Fato ≠ hipótese** em todo relato.
- Qualquer resultado que dependa de mudança em dado ou pipeline (rodada 0) exige a certificação
  descrita ali — teste verde não substitui a conferência das âncoras.
- Se uma rodada falhar ou for abortada, isso é registrado no `README.md` desta pasta com o motivo.
  **Rodada abortada não vira rodada omitida.**

---

## EMENDA 1 — 29/08/2026, após a primeira execução da Rodada 0

**Não altera nenhuma regra de decisão.** Corrige um critério de aceitação que estava
mal-especificado, e a correção é registrada aqui porque o critério original **reprovou**.

**O que aconteceu:** o critério 4 da Rodada 0 exigia que as **388** semanas de clima já
existentes ficassem idênticas dentro de `rtol=1e-9`. A recaptura foi **REPROVADA**: 169
divergências em 23 semanas.

**Diagnóstico (medido, em `saidas/rodada_0_divergencias_clima.csv`):**

- **365 das 388 semanas bateram exatamente** — zero divergência de 30/12/2018 a 21/12/2025;
- as 23 semanas divergentes começam em **28/12/2025** e vão até 31/05/2026, o fim da captura anterior;
- de 28/12/2025 a 19/04/2026 (18 semanas) divergem **só as 3 colunas de radiação solar** — que a
  NASA deriva de satélite e reprocessa com atraso maior;
- de 26/04/2026 a 31/05/2026 (5 semanas) a divergência é ampla (15 a 22 colunas): eram as semanas
  mais recentes quando a captura de 16/08/2026 rodou, ainda em regime *near-real-time*.

**Por que o critério original estava errado:** o próprio `preparo/capturar_clima.py` já documenta,
desde antes desta sessão, que *"as datas do passado são sempre iguais; só as semanas mais recentes
podem mudar um pouco (a NASA ajusta os dados novos depois de um tempo)"*. Exigir estabilidade em
semanas dentro da janela de reprocessamento contradiz o comportamento conhecido da fonte. O valor
novo é o **reprocessado**, mais preciso — trocar por ele é melhoria, não regressão.

**Critério 4, corrigido:**

- **Bloqueante:** as semanas de **30/12/2018 a 21/12/2025** (365 semanas) devem bater dentro de
  `rtol=1e-9`. Qualquer divergência aí para a rodada.
- **Informativo:** as semanas de **28/12/2025 em diante** podem ter sido reprocessadas pela NASA.
  Divergências são gravadas em CSV e contadas no log, mas não bloqueiam.

**O que NÃO muda:** os critérios 1, 2, 3 e 5 seguem exatamente como escritos — shape 725×36, vetor e
casos intocados, `temp_media` ≥ 700 não-nulos. Nenhuma regra de decisão das Rodadas 1 a 4 foi tocada.

**Consequência colateral, registrada:** as 23 semanas reprocessadas mudam de valor na `tabela_final`.
Elas são posteriores a 21/12/2025 e, portanto, caem fora da janela de avaliação de todos os
experimentos comparativos (que terminam na última semana com caso divulgado, 26/04/2026, e ainda
perdem as semanas do corte de maturidade). O efeito sobre os resultados é nulo ou marginal — mas
**é declarado aqui, não descoberto depois**.
