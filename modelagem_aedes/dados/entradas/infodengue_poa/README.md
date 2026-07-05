# InfoDengue — Porto Alegre (séries semanais de arboviroses + clima)

Dados baixados do **InfoDengue** (projeto Alerta Dengue — Fiocruz + FGV/EMAp) para **Porto Alegre** (geocode IBGE **4314902**), por **semana epidemiológica**. Baixado em **12/06/2026**.

Fonte / API (sem chave): `https://info.dengue.mat.br/api/alertcity`
Documentação: https://info.dengue.mat.br/services/api/doc

## Arquivos

| Arquivo | Doença | Semanas | Período | Casos notif. (total) |
|---|---|---|---|---|
| `infodengue_poa_dengue.csv` | dengue | 857 | 2010-01-03 → 2026-05-31 | 125.868 |
| `infodengue_poa_zika.csv` | zika | 737 | 2010-01-03 → 2024-02-11 | 364 |
| `infodengue_poa_chikungunya.csv` | chikungunya | 857 | 2010-01-03 → 2026-05-31 | 528 |

> Zika e chikungunya têm pouquíssimos casos em POA (centenas no total) — úteis como covariáveis/coinfecção, não como alvo. Dengue é a série principal.

## Como atualizar / rebaixar

```bash
GEOCODE=4314902
for d in dengue zika chikungunya; do
  curl -sS "https://info.dengue.mat.br/api/alertcity?geocode=${GEOCODE}&disease=${d}&format=csv&ew_start=1&ew_end=53&ey_start=2010&ey_end=2026" \
    -o "infodengue_poa_${d}.csv"
done
```
(Ajustar `ey_end` para o ano corrente. Formato `json` também disponível trocando `format=`.)

## Dicionário de colunas

**Tempo / local**
- `data_iniSE` — data (segunda-feira) de início da semana epidemiológica (YYYY-MM-DD).
- `SE` — semana epidemiológica no formato AAAASS (ex.: 202517 = SE 17 de 2025).
- `municipio_nome`, `Localidade_id`, `pop` — município, id e população.

**Casos**
- `casos` — **casos notificados** na semana (dado bruto do SINAN).
- `casos_est`, `casos_est_min`, `casos_est_max` — **casos estimados por nowcasting** (corrige o atraso de digitação; nas semanas recentes `casos_est > casos`). Use estes para a série mais recente.
- `casprov`, `casprov_est` (+ `_min`/`_max`) — casos prováveis (notificados/estimados).
- `casconf` — casos confirmados (vem **vazio** neste endpoint para POA).
- `notif_accum_year` — acumulado de notificações no ano.

**Epidemiologia / alerta** (já calculados)
- `p_inc100k` — incidência por 100 mil habitantes.
- `nivel` — **nível de alerta 1–4 (1 verde, 2 amarelo, 3 laranja, 4 vermelho)** — heurística oficial do Min. da Saúde combinando incidência, Rt e clima.
- `nivel_inc` — nível só pela incidência.
- `Rt` — número reprodutivo efetivo estimado (>1 = transmissão crescente).
- `p_rt1` — probabilidade de Rt > 1.

**Clima** (preenchido em ~96% das semanas a partir de ~2018; mais esparso nos anos antigos)
- `tempmin`, `tempmed`, `tempmax` — temperatura (°C).
- `umidmin`, `umidmed`, `umidmax` — umidade relativa (%).

**Indicadores derivados**
- `receptivo` — receptividade climática (1 = clima favorável à proliferação do vetor naquela semana).
- `transmissao` — evidência de transmissão sustentada.
- `tweet` — volume de menções em redes (sinal social; pode estar descontinuado).
- `id`, `versao_modelo` — controle interno do InfoDengue.

## Ressalvas importantes

- **Caso ≠ caso confirmado do SINAN.** `casos` aqui são **notificações** (mais amplo que o recorte confirmado `CLASSI_FIN ∈ {10,11,12}` em `base_oficial_filtrada_poa/`). Ex.: 2025 → InfoDengue ~64,7 mil notificados vs. ~24,8 mil confirmados no recorte SINAN. **Não misturar as duas séries** sem decidir a definição de "caso".
- **Granularidade só municipal** (cidade inteira) — InfoDengue **não** desagrega por bairro nem traz dado entomológico/armadilha (isso vem da SMS/CGVS/Ecovec).
- Clima é modelado/agregado pelo InfoDengue para o município. Cobertura **boa desde 2010** (52/52 semanas na maioria dos anos); parcial só em 2017 (41/52), 2021 (42/52) e no ano corrente (2026, em curso).
- Para uso acadêmico, citar o projeto **Alerta Dengue / InfoDengue (Fiocruz–FGV)**.

## Análises

- `analises_infodengue/eda_infodengue_poa.ipynb` — EDA simples das três séries: visão geral, série temporal de casos, sazonalidade (boxplot por SE + heatmap ano×semana), nível de alerta e Rt, clima e **correlação defasada (lags) clima→casos**, e comparação dengue/zika/chikungunya. Requer `pandas` + `matplotlib` (já instalados no `.venv`); rode "Run All" usando o kernel do `.venv`.

Ver contexto da pesquisa em `../../../Contexto/06_dados_externos/historico_dados_miaedes.md` (§5.1) e `../../../Contexto/01_projeto_pesquisa/dados_disponiveis.md`.
</content>
