# Certificação adversarial da E7 (WIS) — 12/10/2026

**Veredito: APROVADO.** Reimplementação independente (código próprio, sem importar `aedes/wis*`, `quantis*`, `estatistica*`, `experimentos/e7*`) reproduz todas as saídas da E7.
Ambiente: `python3` (sklearn 1.8.0, numpy 2.4.4, pandas 3.0.2, scipy 1.17.1), `OMP_NUM_THREADS=1`, `-B`, no máx. 3 processos. Nada fora de `certificacao/` foi escrito; sem `__pycache__`.

## Scripts e logs (todos aqui)
- `verificar_wis.py` + `verificar_wis.log`, `resultado_verificacao.json`, `meu_wis_resumo.csv`, `meu_familia_F5.csv`
- `retreino.py` (sklearn direto, matrizes de `testes/referencia_antiga/matriz_hXX.csv`) + `retreino/` (18 células) + `retreino_vs_parciais.csv`
- `verificar_extras.py` + `verificar_extras.log`, `resultado_verificacao_extras.json`

## O que foi medido
1. **WIS**: Bracher 2021 (K=3, mediana) e, em paralelo, a identidade WIS = soma das 7 perdas pinball / 3,5. Teste unitário (zero perfeito, exemplo manual 14,6286, 500 casos aleatórios: as duas formas iguais).
   - 4 modelos x 12 h x 2 janelas (96 linhas): WIS dif máx **1,1e-13**, cobertura 50/80/90 dif **0**, n igual. Por origem: 13.152 linhas, 0 só de um lado, 0 divergência de cobertura.
2. **26/09**: previsões brutas dos 7 quantis, 16.226 linhas em comum, 0 só novas, 0 só antigas, dif **0,0**. WIS janela antiga (n=97; régua 96) dif 5,7e-14; as 12 âncoras da pré-declaração batem (tolerância 0,05).
3. **Retreino sklearn direto** (laço próprio, corte pela resposta): 18 células completas (folha 5 h=4 e folha 20 h=12 com os 7 quantis; q0,50 f5 h1; q0,25 f20 h8; q0,75 f5 h8; q0,05 f20 h1), 5.1 mil previsões: dif máx **0,0** contra os parciais, 0 linhas só de um lado. WIS ponta a ponta do retreino: f5 h4 = 204,99895947 e f20 h12 = 265,28166500, idênticos ao executor.
4. **F5 (12 testes)**: DM-HLN, Holm, bootstrap de blocos (8, 2000, semente 42) refeitos do `METODO_ESTATISTICO.md`: n, WIS, delta, ganho, DM, p bruto, p Holm dif ≤ 1e-13; **IC bootstrap dif 0,0000 pp** (duas formas de sortear os blocos dão o mesmo); vereditos 0 divergentes; 0 fallback de variância. Holm conferido por 2ª rotina (dif 0); p via `t.cdf` dif 1e-16.
5. **Composto**: reimplementei a escolha (MAE 13 semanas, q0,85 da E2, empate = folha 5): 3.252 escolhas, **0 divergentes** da E3; quantis do composto dif 0,0.
6. **Régua climatológica** do zero (`np.quantile`, anos 2018+, anteriores ao ano-alvo, mín. 3): 2.952 (h, data), dif **0,0**; nenhuma data minha sem a do executor e vice-versa.
7. **Cobertura** recalculada (inclusiva, `l <= y <= u`): idêntica; relato do executor (16 WIS da janela padrão e coberturas citadas) confere.
8. **Trava q0,85**: reproduz `referencia/previsoes.csv`, dif 2,3e-13 (f5) e 4,5e-13 (f20), 1.159 linhas cada, nenhuma órfã.
9. Série de casos após corte: minha construção vs `serie_casos_apos_corte.csv` dif 0; `real` dos parciais vs tabela dif 0.

## Achados e ressalvas (nenhum reprova)
- **Causa do n=101 da régua confirmada**: 28/12/2025 é semana epidemiológica 53 de 2025; entre 2018+ só 2020 tem semana 53 (1 ano < 3). A régua também não existe em 07 e 14/02/2021, fora da janela.
- **Janela padrão**: 109 semanas no calendário, 7 sem previsão (26/05 a 07/07/2024, enchente em h=4), 102 por h. As datas faltantes mudam com h (12 listas distintas).
- **Cruzamentos de quantis**: 65% a 89% das origens (24 combinações) tinham cruzamento antes de ordenar. Sem ordenar, o WIS ficaria **+0,7% a +3,9%** maior: a ordenação não é neutra, deve constar no Método.
- **Quantil 0,05 negativo** (sem truncar em 0, como no antigo): até 8,8% das origens, mínimo −97,9. Descritivo; o antigo fazia igual.
- **Cobertura abaixo do nominal em todos os modelos**: 50% → 12–42% (f5), 17–36% (f20), 17–42% (composto), 20–21% (régua); 90% → 49–78% (f5), 59–85% (f20), 56–78% (composto), 39–43% (régua).
- **Limites da minha independência**: o retreino usa as matrizes do gabarito antigo (iguais às do pacote, pois as previsões saem idênticas) e o mesmo sklearn/threads, então igualdade bit a bit era esperada. A mutação do DM por embaralhamento em h=1 não muda o valor (sem defasagens), então não prova sensibilidade; o sinal trocado inverte DM como deve.
- **Escolha não prevista na especificação**: o sorteio dos blocos do bootstrap não é descrito linha a linha; as duas formas razoáveis dão IC idêntico ao do executor.
- Nada foi interpretado; o modelo de referência do artigo não foi tocado.
