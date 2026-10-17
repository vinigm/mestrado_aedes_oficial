# Certificacao adversarial da E5 (alarme) - 12/10/2026

Veredito: **APROVADO** (todas as quatro verificacoes batem; 0 divergencias numericas). Ressalvas de leitura abaixo.

Codigo proprio, sem importar aedes/alarme*/experimentos. Scripts: `verif_razao.py`, `verif_ancora.py`, `verif_alarme.py` (+ logs, `razao_por_arquivo_e_ano.json`, `alarme_recalculado.csv`). `python3 -B`, so leitura dos zips publicos DENGBR18-24 e das previsoes da E2/E3.

## 1. Razao r (zips lidos em pedacos, colunas ID_MUNICIP, ID_MN_RESI, CLASSI_FIN, DT_SIN_PRI)
- DENGBR18-24: notificacao 12.778, residencia 12.033, r = 1,0619131, L = 447,0654. Identico a razao.json.
- DENGBR18-23: 12.776 / 12.032, r = 1,0618351, L = 447,0326. Identico.
- Por arquivo (sintomas 2018-23 / fora da janela): o arquivo 2024 contribui 2 (notif) e 1 (resid) de sintomas em 2023; o 2020 contribui 1 residencia de 2019.
- Previsoes entre L(18-23) e L(18-24): 0 previsoes caem entre os dois L (`verif_sensibilidade_L.log`), logo a escolha da versao nao altera nenhuma contagem.

## 1b. Ancora 12.785
- Tabela_final (semanas iniciadas em 2018-23): 12.785 (confere). Numerador 12.778: -7 casos, -0,055% (<1%).
- Por ano (tabela x DENGBR por DT_SIN_PRI): 2018 4x3, 2019 489x489, 2020 37x38, 2021 72x72, 2022 5.583x5.583, 2023 6.600x6.593. A diferenca liquida (-7) vem quase toda de 2023, na fronteira de ano (semana epidemiologica que inicia em dezembro x data de sintomas); 2018/2020 trocam 1 caso. Explicacao plausivel, nao testada ficha a ficha.

## 2. Definicao do evento no codigo antigo (calcular_alarme.py, lido, nao executado)
- `houve_surto = real > limiar`; `disparou_alarme = previsto > limiar`: **estrito (>)**, **semanas** (nao episodios). Executor usou a mesma (e registrou o desvio da spec que dizia >=).
- Sensibilidade = VP/(VP+FN), precisao = VP/(VP+FP). Identicas.
- Por seguranca testei tambem >=: com L convertido nenhuma linha muda (0 diferencas em 51), porque real e inteiro e L nao e.

## 3. Metricas recalculadas
- 17 combinacoes (8 bracos x 2 folhas + composto) x h 1/4/8 = 51 linhas, L convertido e L = 421, nas 102 semanas-alvo do completo (102 por h em folha 5 e 20).
- Contagens VP/FN/FP/VN, n, semanas de surto, sensibilidade e precisao: **identicas** (0 diferencas) em `alarme.csv` e `alarme_421_sem_conversao.csv`.
- Composto N=13 refeito do zero a partir das previsoes das duas folhas: 3.252 linhas, previsao e folha escolhida identicas a E3 (dif max 0,0).

## 4. Denominador de falsos por ano
- 102 semanas / (365,25/7) = 1,9548 ano; 102/52 = 1,9615 (o que o codigo antigo faz, SEMANAS_POR_ANO = 52).
- O executor usou **exatamente 1,96** (FP/1,96 reproduz a coluna com dif 0,0), nao o valor calculado.
- Efeito: com o valor calculado (1,9548), falsos/ano sobem ate 0,008 (ex.: 0,5102 -> 0,5116; 2,5510 -> 2,5578), ~0,3%. Irrelevante ao 1 decimal; coerente com a pre-declaracao (1,96) e com o texto do projeto.

## Ressalvas (nao reprovam)
- "1,96" e arredondamento (102/52 = 1,9615); se o artigo citar "1,96 ano" esta correto; so nao e 102/(365,25/7).
- E5 e descritiva: n de semanas de surto pequeno (24/27/28 em h 1/4/8) e blocos contiguos; precisao 1,000 em h=8 vem de FP = 0.
