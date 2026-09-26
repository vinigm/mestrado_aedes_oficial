# Critério oficial de surto/epidemia de dengue para Porto Alegre

**Data:** 25/09/2026 · **Pergunta:** existe critério oficial (não convenção própria) para o limiar de
"surto"/"epidemia" de dengue em Porto Alegre, em casos/semana, para substituir o limiar de 100
casos/semana usado hoje no projeto?

**Resposta curta:** SIM. A Prefeitura de Porto Alegre (SMS) tem critério numérico oficial, publicado
no *Plano Municipal de Contingência ARBOVIROSES 2026* (dez/2025). Ele não é um número fixo de
casos — é uma fórmula sobre a incidência (casos/100 mil hab.), com dois patamares fixos auxiliares
(**30,0** e **50,0** por 100 mil) que dão, em casos/semana de Porto Alegre, **~421** e **~702**.

---

## PARTE A — o que os dados do InfoDengue mostram (fato, não hipótese)

Arquivo: `modelagem_aedes/dados/entradas/infodengue_poa/infodengue_poa_dengue.csv` (857 semanas,
2010–2026). Colunas usadas: `nivel` (alerta 1–4), `nivel_inc` (nível de incidência 0–2), `p_inc100k`,
`casos`, `pop`.

### `nivel_inc` (0/1/2) — o corte é sobre `casos`, não sobre `p_inc100k`

Para cada ano, o maior `casos` com `nivel_inc=0` e o menor `casos` com `nivel_inc=1` batem quase
sempre em **5 e 6 casos/semana** — de 2010 a 2021, com população constante (1.488.252). Isso é a
"faixa endêmica" do método MEM do InfoDengue: um corredor (baixo → médio → alto) recalculado sobre a
série histórica recente, não um número fixo de casos.

- **O corte SOBE junto com o histórico recente** (achado central, explica por que "100
  casos/semana" é arbitrário mesmo dentro do próprio InfoDengue):

| Ano | corte 0→1 (casos) | corte 1→2 (casos) |
|---|---|---|
| 2010–2021 (típico) | 6 | 20–23 |
| 2022 | 8 | 48 |
| 2023 | 14 | 49 |
| 2024 | 36–47 | 55 |
| 2025 | 94 | 105 |

- **Interpretação:** o InfoDengue usa uma janela histórica móvel para definir a faixa esperada — depois
  de anos de epidemia grande (2022–2025), a própria "normalidade" do modelo sobe. Um limiar fixo de
  100 casos/semana teria significados completamente diferentes em 2015 (muito acima de qualquer
  epidemia) e em 2025 (dentro da faixa "baixa").

### `nivel` (alerta 1–4, verde/amarelo/laranja/vermelho) — NÃO é só incidência

As faixas de `casos` e `p_inc100k` **se sobrepõem** entre os 4 níveis dentro do mesmo ano (ex.:
2022, nível 2 vai de 2 a 18 casos e nível 4 vai de 32 a 1088 — mas nível 1 também cobre 0–54).
Isso é esperado: o `nivel` combina incidência **com tendência** (Rt), não é só um corte de
casos/semana. Não dá para traduzir `nivel` isolado em "X casos/semana" sem o Rt — **isso é fato dos
dados, não hipótese**.

---

## PARTE B — fontes oficiais

### 1. InfoDengue (Fiocruz/PROCC + FGV) — método MEM

- **Fonte:** glossário oficial (via LAC/TGHN) — https://lac.tghn.org/recursos/glossario-infodengue/
- **Critério:** o limiar epidêmico é uma "linha de alarme" estatística (quartil superior/desvio-padrão
  da série histórica) calculada pelo MEM (Moving Epidemic Method); "corredor endêmico" = faixa
  esperada com limite superior e inferior. Os 4 níveis (verde/amarelo/laranja/vermelho) combinam esse
  corredor com Rt > 1 sustentado (transmissão) — **não achei o valor numérico fixo publicado
  oficialmente para Porto Alegre**; ele é recalculado por município e por ano (compatível com o
  achado da Parte A).
- Confirmação parcial na própria página de POA (info.dengue.mat.br/alerta/4314902/dengue, lida
  25/09/2026): população **1.404.269** (mesma da coluna `pop` do CSV), mas o limiar numérico do
  momento não apareceu no texto extraído — só o percentual de chance de alerta laranja/vermelho.

### 2. Ministério da Saúde — Guia para Elaboração de Planos de Contingência (2024)

- **Fonte:** https://bvsms.saude.gov.br/bvs/publicacoes/guia_orientacoes_elaboracao_planos_contingencia.pdf
- **Critério:** define os 5 estágios (Normalidade/verde, Mobilização/amarelo, Alerta/laranja,
  Situação de Emergência/vermelho, Crise/roxo) **de forma qualitativa**, sem número de
  casos/incidência. Texto literal (p.22): *"A definição e a aplicação dos estágios operacionais podem
  variar de acordo com a natureza e a gravidade do evento, assim como as diretrizes específicas de
  cada estado e município."* → **achado confirmado: o nível federal não fixa um número; delega para
  estado/município.**

### 3. Plano de Contingência Dengue RS 2024–2025 (SES/CEVS-RS)

- **Fonte:** https://saude.rs.gov.br/upload/arquivos/202502/12113524-plano-de-contingencia-dengue-2024-2025-versao2-10-02.pdf
- PDF não extraível por texto no WebFetch; conteúdo confirmado indiretamente pela busca (WebSearch) e
  por citar-se a mesma fórmula usada no plano de POA (ver item 4) — **mesma fonte estadual do LSE/LA**.

### 4. Plano Municipal de Contingência ARBOVIROSES 2026 — Porto Alegre/SMS (dez/2025) — CRITÉRIO OPERATIVO

- **Fonte:** https://prefeitura.poa.br/sites/default/files/usu_doc/sites/sms/2026_Plano_Municipal_de_Contingencia_Arboviroses.docx_0.pdf
  (Quadro 1, p.15)
- **Critério literal:**
  - **NORMALIDADE:** incidência de confirmados < LA em todas as últimas 4 SE, OU < 10,00/100mil em
    todas as últimas 4 SE.
  - **MOBILIZAÇÃO:** confirmados < LA E prováveis > 10,00/100mil em ≥2 das 4 SE (ou variantes
    equivalentes cruzando LA com o corte fixo de 10,00).
  - **ALERTA:** confirmados entre LA e LSE em ≥3 das 4 SE E confirmados >30,0 e ≤50,0/100mil em ≥1 SE;
    OU ≥3 SE acima do LSE E >30,0 em 1 SE; OU novo sorotipo; OU 1 óbito confirmado nas últimas 4 SE.
  - **EPIDEMIA:** confirmados > LSE nas últimas 4 SE E >50,0/100mil em ≥1 SE; OU >1 óbito confirmado
    nas últimas 4 SE.
  - **LSE** (Limite Superior Endêmico) = média móvel da incidência de casos prováveis + 2 desvios
    padrão, série RS. **LA** (Limite de Alerta) = curva do LSE 45% abaixo. Ambos **dinâmicos**, calculados
    sobre a série estadual — não são números fixos de casos/semana.

---

## Limiar traduzido em casos/semana para Porto Alegre

Usando `pop = 1.404.269` (campo `pop` do InfoDengue, igual ao valor exibido na página do InfoDengue
para POA em 25/09/2026):

- **10,00/100 mil → 140,4 casos/semana** (piso fixo do estágio Normalidade/Mobilização)
- **30,0/100 mil → 421,3 casos/semana** (piso fixo do estágio Alerta)
- **50,0/100 mil → 702,1 casos/semana** (piso fixo do estágio Epidemia)

⚠️ **LA e LSE não têm tradução fixa** — variam semana a semana com a série histórica do RS. Não
invento um número para eles.

---

## Recomendação

**Não existe um único "número mágico" oficial e fixo** — mas existe critério oficial, mais rigoroso
que a convenção de 100/semana: o piso fixo e citável de **702 casos/semana** (50/100mil) para
"Epidemia" segundo o Plano Municipal de POA 2026, com **421/semana** (30/100mil) já classificando
"Alerta". Como comparação, os **100 casos/semana** hoje usados no projeto ficam **abaixo do próprio
piso de Alerta** (421) — ou seja, o critério do projeto é mais sensível (dispara "surto" mais cedo)
que o critério oficial da SMS-POA. Sugiro citar essa fonte e decidir, por escrito, se o projeto adota
os 3 patamares oficiais (140/421/702) ou mantém o próprio, agora justificado por comparação explícita.
