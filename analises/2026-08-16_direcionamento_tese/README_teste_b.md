# TESTE B — Sinal espacial do vetor (pré-requisito de "prever o vetor por bairro")

## O que este teste responde

1. O sinal de densidade de Aedes por bairro é **persistente** o bastante pra ser previsível?
2. Em que **granularidade** (bairro vs zona sintética) o **ruído de amostragem** (poucas
   armadilhas por bairro-semana) é aceitável?

## Dados e escopo

- Fonte única: `secretaria_poa_armadilhas.parquet` (636.587 linhas brutas, 2012-2026).
  **Nenhum arquivo do projeto foi alterado** — só leitura.
- Filtro: `inspecao_realizada == True`. Isso **automaticamente restringe a amostra a
  2019+**: a coluna `inspecao_realizada` é `NA` para 100% das linhas antes de
  2018-12-30 (não dá pra saber quais armadilhas foram checadas antes disso).
- Janela final: **393 semanas**, 2019-01-06 a 2026-08-09.
- Correção de dado: `'CAMAQUÃƑ'` e `'CAMAQUÃ'` são **o mesmo bairro** — artefato de
  encoding duplicado (confirmado: as duas grafias não se sobrepõem no tempo, uma
  cobre partes de 2020/2025 e a outra o resto). Mesclados só em memória, script não
  toca no parquet.
- Densidade = `femeas ÷ armadilhas inspecionadas` no bairro-semana. Alvo suavizado
  (`mm4`) = média móvel de 4 semanas (mínimo 2 não-nulas na janela).
- Elegibilidade: bairro/zona entra no painel só se tem **≥10 armadilhas em ≥50% das
  393 semanas** (denominador = grade completa de semanas, não só as semanas em que
  o bairro aparece — isso evita inflar artificialmente a cobertura).
- Zonas sintéticas: K-Means nas coordenadas médias de cada armadilha (1.452
  armadilhas únicas), k=8 e k=16.

## Números-âncora

### Cobertura / elegibilidade

| Granularidade | Grupos totais | Grupos elegíveis (≥10 armadilhas em ≥50% das semanas) |
|---|---|---|
| Bairro | 68 | **37** |
| Zona k=8 | 8 | **7** |
| Zona k=16 | 16 | **15** |

Zonas sintéticas quase não perdem grupos por baixa cobertura (K-Means distribui
armadilhas de forma mais equilibrada que os limites administrativos de bairro) —
bairro perde **31 de 68** (46%) por ter poucas armadilhas.

### 1. Persistência — autocorrelação do mm4 (mediana entre grupos)

| Lag | Bairro (n=37) | Zona k=8 (n=7) | Zona k=16 (n=15) |
|---|---|---|---|
| 1 semana | 0,961 | 0,973 | 0,970 |
| 2 semanas | 0,896 | 0,927 | 0,915 |
| 4 semanas | 0,728 | 0,796 | 0,765 |
| 8 semanas | **0,433** | **0,477** | **0,457** |

### 1b. Persistência — Spearman do ranking de grupos (mediana ao longo das semanas)

| Lag | Bairro | Zona k=8 | Zona k=16 |
|---|---|---|---|
| t → t+4 | 0,476 | 0,607 | 0,559 |
| t → t+8 | **0,352** | **0,500** | **0,423** |

**Leitura:** autocorrelação é alta em lags curtos (1-2 semanas) em qualquer
granularidade — mas isso é dominado pela sazonalidade comum da cidade (ver bloco 4).
O teste que isola sinal **espacial** de verdade é o ranking: em 8 semanas o
ranking de bairros ainda guarda só **35% de correlação** de posição (0,352) — ou
seja, "qual bairro vai estar mais infestado daqui a 2 meses" é uma pergunta com
sinal fraco-a-moderado no nível bairro, e **melhora em zona sintética** (0,42-0,50).

### 2. Ruído de amostragem — split-half (mediana de 50 sorteios, correlação de Pearson)

| Granularidade | Bairro-semanas qualificados (≥8 armadilhas) | Split-half bruto (raw) | Split-half no mm4 |
|---|---|---|---|
| Bairro | 13.310 | 0,688 | **0,883** |
| Zona k=8 | 2.720 | 0,920 | **0,975** |
| Zona k=16 | 5.673 | 0,825 | **0,941** |

**Leitura:** a densidade bruta de UMA semana no nível bairro tem confiabilidade
split-half de só **0,69** — quase 1/3 da variância observada numa semana isolada é
ruído puro de qual armadilha caiu em qual metade do sorteio, não sinal real. Suavizar
com `mm4` (o que o projeto já faz) recupera bastante disso (0,88), mas zona
sintética é estruturalmente mais confiável em ambos os casos porque agrega mais
armadilhas por unidade — zona k=8 chega a 0,92 bruto / 0,975 suavizado.

### 3. Decomposição de variância do alvo suavizado (painel grupo-semana balanceado)

| Granularidade | Semanas 100% completas usadas | % variância = sazonalidade comum | % variância = efeito fixo de grupo | % variância = resíduo (só espacial explica) |
|---|---|---|---|---|
| Bairro | 307 de 393 | 77,4% | 3,8% | **18,8%** |
| Zona k=8 | 391 de 393 | 90,6% | 1,7% | **7,7%** |
| Zona k=16 | 353 de 393 | 83,2% | 2,9% | **13,9%** |

**Leitura:** a maior parte da variância do alvo (77-91%) é **sazonalidade
compartilhada por toda a cidade** — a mesma onda de clima/temporada que sobe e desce
junto em todo lugar, e que o clima (variável única para a cidade inteira) já cobre.
O "efeito fixo de bairro/zona" (bairro sempre mais quente ou mais frio que a média,
constante no tempo) é pequeno (2-4%) — não é isso que sustenta a tese de "prever o
vetor por bairro". O que sobra pro dado espacial prever de fato é o **resíduo**:
**18,8% no bairro**, caindo pra **7,7% na zona k=8**. Isso é o espaço real de "sinal
espacial dinâmico" (por que ESTE bairro está mais quente que o esperado ESTA
semana) — pequeno, mas não-zero, e majoritariamente **ruído de amostragem**, não
"sinal espacial real": o bloco de split-half mostra que boa parte desses 18,8% no
bairro é justamente a mesma instabilidade split-half medida acima (raw=0,69 →
1-0,69≈31% de ruído por semana isolada, consistente em ordem de grandeza com os
18,8% do resíduo do painel suavizado).

## Veredicto (linha honesta)

**Há sinal espacial real, mas ele é fraco no nível bairro e majoritariamente
ofuscado por dois fatores: sazonalidade comum da cidade (77-91% da variância) e
ruído de amostragem de poucas armadilhas por bairro-semana (split-half bruto
0,69 no bairro).** "Prever quais bairros vão estar mais infestados" tem sinal
mensurável (ranking Spearman 0,35-0,48 em 4-8 semanas, resíduo espacial 8-19% da
variância do alvo suavizado) mas é **claramente mais previsível em zona sintética
(k=8) do que em bairro administrativo** — zona k=8 tem persistência de ranking
maior (0,61 vs 0,48 em lag 4), split-half muito melhor (0,92 vs 0,69 bruto) e
perde menos grupos por baixa cobertura (7/8 vs 37/68). **Recomendação de
granularidade: zona sintética k=8 (ou algo entre 8-16), não bairro administrativo**
— bairro tem resolução espacial mais fina mas paga isso com ruído de amostragem que
consome boa parte do sinal.

## Ressalvas (hipótese, não fato)

- ⏳ Persistência e split-half aqui são medidos **sem controlar por clima** —
  parte da autocorrelação de curto prazo (lag 1-2) é a mesma tendência sazonal
  que já aparece na decomposição de variância (77-91%), não sinal espacial
  independente. O número que isola isso de verdade é o ranking Spearman e o
  resíduo da decomposição, não a autocorrelação bruta.
- ⏳ K-Means nas coordenadas cria zonas geograficamente compactas mas **não
  necessariamente epidemiologicamente coerentes** (não usa nenhuma informação de
  uso do solo, densidade populacional, tipo de imóvel etc.) — é um agrupamento
  puramente espacial, ponto de partida, não zoneamento definitivo.
- ⏳ O split-half no `mm4` usa um sorteio aleatório **independente a cada semana**
  dentro da mesma rodada (não um sorteio fixo por armadilha ao longo do tempo) —
  isso é uma escolha metodológica specific para testar "a suavização temporal
  reduz ruído de amostragem semana-a-semana", não testa se duas metades FIXAS de
  armadilhas (p.ex. metade "norte" e metade "sul" dentro do bairro) dariam a
  mesma série ao longo do tempo — seria um teste complementar, não feito aqui.
- ⏳ A decomposição de variância usa só as semanas 100% completas (307/393 no
  bairro, 391/393 na zona k8) pra manter a soma dos quadrados exatamente aditiva
  — os 22% de semanas descartadas no bairro não foram checados por viés
  sistemático (p.ex. se são majoritariamente semanas de baixa temporada com menos
  armadilhas em campo).

## Arquivos desta pasta

- `teste_b_sinal_espacial.py` — script único, roda em **~4-6s** (bem abaixo do
  orçamento de 5-25min).
- `teste_b_cobertura_elegibilidade.csv` — quantos grupos totais/elegíveis por
  granularidade, e a lista de grupos elegíveis.
- `teste_b_persistencia_autocorrelacao.csv` — autocorrelação mediana do mm4 por
  lag (1/2/4/8 semanas) e granularidade.
- `teste_b_persistencia_ranking_spearman.csv` — Spearman do ranking de grupos
  entre t e t+4/t+8, mediano ao longo das semanas.
- `teste_b_split_half_confiabilidade.csv` — confiabilidade split-half (raw e
  mm4), mediana/min/max de 50 sorteios.
- `teste_b_decomposicao_variancia.csv` — decomposição da variância do mm4 em
  sazonalidade comum / efeito fixo de grupo / resíduo.
