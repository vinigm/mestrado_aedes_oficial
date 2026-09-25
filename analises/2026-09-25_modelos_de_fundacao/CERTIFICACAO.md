# Certificação adversarial — modelos de fundação (25/09/2026)

Certificador independente, código próprio (`cert_fundacao.py`), sem importar `rodar.py`.

## Travas 2 e 4 (recheck independente)

- **Trava 2** (`ultima_data_do_contexto == origem`): OK — 0 violações em 4636 linhas.

- **Trava 4** (`q085 >= q050`): OK — 0 violações.


## Item 1 — MAE recalculado do zero (q0,85, avaliação data_alvo>=2024-01-01)

| h | n | régua | B0 | bolt_casos | c2_casos | c2_casos_clima | c2_casos_clima_vetor |
|---|---|---|---|---|---|---|---|
| 1 | 102 | 202.1 | 133.6 | 144.4 | 193.6 | 208.1 | 207.5 |
| 4 | 102 | 213.2 | 199.6 | 193.8 | 255.8 | 275.7 | 263.0 |
| 8 | 102 | 216.2 | 223.2 | 274.7 | 256.1 | 269.8 | 252.7 |
| 12 | 102 | 217.8 | 243.8 | 289.5 | 227.2 | 275.0 | 265.2 |

### Reprodução dos p-valores dos CSVs do orquestrador

- H1: bate
- H2: bate
- H3: bate

- Âncoras do orquestrador (MAE h=1/4/8/12, 6 braços): todas conferem


### Direção de cada comparação com p_holm < 0,05

- **H1 (bate a régua):** `bolt_casos` h=8 — braço pior (MAE braço 274.7 vs comparador 216.2, p_holm=0.003279).

- **H1 (bate a régua):** `bolt_casos` h=12 — braço pior (MAE braço 289.5 vs comparador 217.8, p_holm=1.182e-06).

- **H2 (melhora B0):** `bolt_casos` h=1 — braço pior (MAE braço 144.4 vs comparador 133.6, p_holm=0.002221).

- **H2 (melhora B0):** `bolt_casos` h=8 — braço pior (MAE braço 274.7 vs comparador 223.2, p_holm=0.0003505).

- **H2 (melhora B0):** `bolt_casos` h=12 — braço pior (MAE braço 289.5 vs comparador 243.8, p_holm=0.001997).

- **H3 (vetor no Chronos-2):** h=4 — vetor melhora (com vetor 263.0 vs sem vetor 275.7, p_holm=0.004957).

- **H3 (vetor no Chronos-2):** h=8 — vetor melhora (com vetor 252.7 vs sem vetor 269.8, p_holm=0.006579).

- **H3 (vetor no Chronos-2):** h=12 — vetor melhora (com vetor 265.2 vs sem vetor 275.0, p_holm=0.006579).


## Item 3 — veredito dos critérios da seção 5

- **Bate a régua** (`bolt_casos`, h=12): NÃO.

- **Bate a régua** (`c2_casos`, h=12): NÃO.

- **Bate a régua** (`c2_casos_clima`, h=12): NÃO.

- **Bate a régua** (`c2_casos_clima_vetor`, h=12): NÃO.

- **Melhora o B0** (`bolt_casos`, h=12): NÃO.

- **Melhora o B0** (`c2_casos`, h=12): NÃO.

- **Melhora o B0** (`c2_casos_clima`, h=12): NÃO.

- **Melhora o B0** (`c2_casos_clima_vetor`, h=12): NÃO.

- **Vetor vale no Chronos-2** (h=12): SIM.

- Candidato 2026-2027 `bolt_casos`: bate_regua=False, melhora_B0=False, MAE calibração 22-23 (h=12) braço=244.6 vs B0=90.9 → não candidato.

- Candidato 2026-2027 `c2_casos`: bate_regua=False, melhora_B0=False, MAE calibração 22-23 (h=12) braço=161.6 vs B0=90.9 → não candidato.

- Candidato 2026-2027 `c2_casos_clima`: bate_regua=False, melhora_B0=False, MAE calibração 22-23 (h=12) braço=154.8 vs B0=90.9 → não candidato.

- Candidato 2026-2027 `c2_casos_clima_vetor`: bate_regua=False, melhora_B0=False, MAE calibração 22-23 (h=12) braço=157.0 vs B0=90.9 → não candidato.

- **Nenhum braço vira candidato à rodada confirmatória 2026-2027** pelos critérios da seção 5.


## Item 4 — efeito do vetor por ano do alvo (h=4, 8, 12)

| ano | h | n | MAE com vetor | MAE sem vetor | redução % |
|---|---|---|---|---|---|
| 2022 | 4 | 47 | 150.2 | 143.1 | -4.9% |
| 2022 | 8 | 47 | 229.1 | 221.7 | -3.3% |
| 2022 | 12 | 47 | 241.5 | 231.5 | -4.3% |
| 2023 | 4 | 53 | 57.5 | 52.9 | -8.7% |
| 2023 | 8 | 53 | 71.8 | 68.6 | -4.6% |
| 2023 | 12 | 53 | 82.0 | 86.8 | +5.5% |
| 2024 | 4 | 45 | 289.2 | 307.4 | +5.9% |
| 2024 | 8 | 45 | 347.7 | 362.8 | +4.2% |
| 2024 | 12 | 45 | 360.0 | 365.5 | +1.5% |
| 2025 | 4 | 52 | 262.0 | 271.2 | +3.4% |
| 2025 | 8 | 52 | 191.6 | 212.4 | +9.8% |
| 2025 | 12 | 52 | 203.6 | 218.3 | +6.7% |

Redução média por ano: 2022=-4.2%, 2023=-2.6%, 2024=+3.9%, 2025=+6.6%. 
O efeito **não** está carregado por um ano só **dentro da janela de avaliação** (2024 e 2025 são ambos positivos). Mas há uma quebra de sinal relevante: em **2022 e 2023 o vetor piora** (redução negativa), e só em **2024-2025 — que é a própria janela de avaliação da pré-declaração — ele ajuda**. Como o teste estatístico da família H3 usa exatamente `data_alvo >= 2024-01-01`, o resultado positivo é sustentado só pelos dois anos que também são os únicos dentro do escopo avaliado; não há forma de testar se o padrão se repete fora dele sem a temporada 2026-2027.


## Item 5 — leitura de contaminação (h=12, c2_casos x bolt_casos, por ano)

| ano | n | MAE c2_casos | MAE bolt_casos | c2 melhor que bolt? |
|---|---|---|---|---|
| 2022 | 47 | 241.1 | 270.4 | sim |
| 2023 | 53 | 91.1 | 221.7 | sim |
| 2024 | 45 | 339.2 | 361.2 | sim |
| 2025 | 52 | 149.3 | 232.0 | sim |

Vantagem média de c2_casos sobre bolt_casos: **+79.9 MAE em 2022-2023** vs **+52.4 MAE em 2024-2025**. 
Não há um padrão claro de vantagem crescente do Chronos-2 em 2024-2025 — a leitura de contaminação não encontra suporte direto nesta comparação (n pequeno, ler com cautela).


## Item 6 — falha de documentação (não bloqueante)

- Os CSVs `familia_h1_bate_regua.csv`, `familia_h2_melhora_b0.csv` e `familia_h3_vetor_no_chronos2.csv` gravados por `rodar.py` trazem só `p_bruto`/`p_holm` — sem MAE do braço, MAE do comparador, nem direção da diferença. Quem lê só o CSV não sabe se um p pequeno é melhora ou piora. Não bloqueia a certificação (os p-valores batem, ver acima), mas é um defeito de `rodar.py` a corrigir antes da rodada confirmatória de 2026-2027.

- Tabela completa gravada em `familias_completas_certificacao.csv` (32 linhas).


## Veredito final

🟢 **APROVADO (leitura confirmada)** — travas 2 e 4 OK, MAE/p-valores/âncoras reproduzem exatamente os números do orquestrador. Achado do orquestrador se sustenta: nenhum braço bate a régua ou melhora o B0 em h=12 com significância; as significâncias de H1/H2 são todas do `bolt_casos` sendo **pior**; o vetor melhora o Chronos-2-com-clima em h=4/8/12 mas o efeito é **carregado** — ver Item 4. Rodada é exploratória por desenho (seção 6); confirmatório é 2026-2027.
