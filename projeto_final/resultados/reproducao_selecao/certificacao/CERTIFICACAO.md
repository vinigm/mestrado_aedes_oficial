# Certificacao adversarial da E6 (12/10/2026)

**Veredito: APROVADO.** Codigo proprio (nao importa `aedes/`, `experimentos/`); `python3` 1.8.0 (sklearn), lightgbm 4.6.0, `-B`, `OMP_NUM_THREADS=1`.
Scripts: `cert_comum.py`, `cert_e6a.py`, `cert_e6b_ranking.py`, `cert_e6b_retreino.py`, `cert_e6c_estat.py`, `cert_e6c_retreino.py`; logs `*.log`.

## E6a (clima)
- Tabela, corte (12 sem, ultima com caso 26/04/2026 -> limite 01/02/2026), candidatas (42 clima, 8 nucleo, 6 vetor), LightGBM 250/0,05/15/5, h 1/4/8, 60% (246/244/242 linhas) refeitos do zero.
- 5 execucoes (n_jobs -1/1, sem semente, semente 42, 42 repetida, 7): lista identica = temp_media_lag4, umid_media, temp_media_lag3, temp_max, pressao_media_lag3, pressao_media_lag4. Semente irrelevante (sem bagging).
- Ganhos: dif max vs executor 2,3e-10 (ordem de soma). 6a = 2.353.990; 7a (temp_amplitude_media) = 2.021.356; margem 332.634.

## E6b (grade de 30)
- Previsoes do executor vs 3 CSVs antigos (sha256 dos gabaritos = originais): 35.490 linhas, 0 so de um lado, dif max **0,0** (3 algoritmos). Truncamento em 0 confere (min = 0 nos dois).
- Ranking refeito do CSV antigo e do novo: dif 0,0 / 1e-14 vs `ranking.csv`; posicoes iguais. 1o 42,019; 2o 42,516; 3o 42,712; 4o 42,715; HistGB padrao M1 19o 46,171; LightGBM padrao M1 21o 46,995; 30o 58,455. Sem empates.
- Retreino com sklearn/lightgbm direto, hiperparametros conferidos contra `rodar_grid.py` antigo: 22 previsoes (5 celulas: HistGB q0,85 M1 h4; GBR q0,80 M1 h12; LGBM q0,90 M1 h1; LGBM padrao M0 h8; HistGB padrao M0 h4; origens inicial, meio, final e dentro da enchente de 2024): dif **0,0**.
- Trava: HistGB q0,85 M1 vs `resultados/referencia` truncada: 1159 linhas, dif 2,3e-13.

## E6c (grade de 18)
- Fase 1: 13.518 previsoes vs CSV antigo, dif 0,0; ranking refeito do zero = executor (7e-15). 1o lr0,03x400/15/5 = 41,662; ref em 4o = 42,022; 9 de folha min. 20 do 10o ao 18o (54,68 a 55,69). Empates exatos 10/11, 13/14, 16/17 (ordem so depende do desempate; antigo e novo diferem so em 13/14; sem consequencia).
- Retreino direto (sem truncar, como o antigo): 20 previsoes em 4 configuracoes (inclui min20): dif **0,0**. As folhas 15 e 31 com min20 empatam na calibracao e divergem depois (dif 0,66 numa origem de 2026): empate real, nao artefato.
- Fase 2 refeita: Wilcoxon (scipy e implementacao manual com postos medios e correcao de empates) + Holm em 4; n=102; reducoes -7,52 / +3,31 / +0,13 / +0,15 %; p bruto 0,430 / 0,585 / 0,864 / 0,551; Holm 1,0 nos 4; igual ao executor e ao antigo (dif 0,0). Regra de troca: nao dispara. Modelo do artigo inalterado.

## Afirmacao do executor
- "Reproduziu" assenta nas ancoras certas (E6a: lista e ordem; E6b: ranking/MAE/previsoes; E6c: ranking/MAE/fase 2).
- Falhas de orquestracao relatadas (xargs, rotulo invalido, lotes sobrepostos, pkill largo) nao afetaram os arquivos de E6: todos os numeros acima conferem. O pkill pode ter atingido a E7: **conferir a E7 em separado**.
- Nao encontrado `__pycache__` em `projeto_final/`. Nao rodei a suite (919 testes), nao verifiquei o manifesto do codigo antigo alem do sha256 dos 4 gabaritos copiados.
