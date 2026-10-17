# Certificação adversarial — E1 (quantil) e piso de ruído (12/10/2026)

**Veredito: APROVADO COM RESSALVAS.** Nenhuma tentativa de reprovar funcionou; as ressalvas são não bloqueantes (seção 4).

Método: código próprio (`comum_cert.py`, `verif_*.py`), laço de treino direto com scikit-learn 1.8.0 (`python3`, `OMP_NUM_THREADS=1`).
Não importei `e1_quantil.py`, `piso_de_ruido.py` nem `perturbacao.py`; só a montagem da matriz (`aedes.dados`, `variaveis`, `configuracao`).
Tabela com hash conferido (`6f34b854...`); os 17 arquivos do gabarito batem com `MANIFESTO.csv`.

## 1. E1 recalculada das previsões salvas (`verif_1_recalculo.py`)

- 3.755 previsões, `data_alvo` entre 22/03/2020 e **31/12/2023** (nenhuma depois); sem ausentes, sem duplicatas, `data_origem + 7h = data_alvo` em todas.
- `n` por h = 193/190/186/182 (ancora). MAE e cobertura por (q, h): diferença máxima contra `metricas.csv` = **0,0** (cobertura 5e-17).
- MAE médio por q: 0,50 = 45,753 · 0,70 = 43,729 · 0,80 = 42,727 · **0,85 = 42,022** · 0,90 = 43,856.
- Melhor = 0,85; ganho = 0,0. O candidato mais próximo (0,80) fica **1,68%** pior que o 0,85. `decisao.json` bate em tudo (inclui `n_por_horizonte`).
- MAE de calibração do 0,85 recalculado **da própria referência** (independe da E1): 22,337/45,786/48,167/51,799; média 42,022. Bate com as âncoras.
- Descritivo (sem interpretar): cobertura do 0,85 (fração com real > previsto) = 0,326 / 0,374 / 0,355 / 0,429 em h = 1/4/8/12.

## 2. Trava 3 recomputada (`verif_1_recalculo.py`)

- q = 0,85 × `resultados/referencia/previsoes.csv` (braço `referencia`, h ∈ {1,4,8,12}, `data_alvo` ≤ 31/12/2023): 751 linhas de cada lado, 751 em comum, 0 só de um lado.
- Diferença máxima do previsto **0,0**, do real 0,0, `data_origem` idêntica.
- Triangulação extra contra o gabarito do **código antigo** (`testes/referencia_antiga/previsoes_referencia.csv`): 751 em comum, diferença máxima 0,0.
- Âncoras da referência na janela: n = 102 em todo h; folha 5 = 97,987/219,669/272,627/278,818; folha 20 = 133,626/199,635/223,183/243,765; 295 previsões em h = 1 e 284 em h = 12 por folha. Todas conferem.

## 3. Retreino próprio

### E1 (`verif_2_retreino_e1.py`)
- **Amostra:** q ∈ {0,50; 0,90} × h ∈ {1, 12} × 3 origens (início 15/03/2020, meio, fim da calibração), 12 treinos, cada um com matriz INTEIRA e com matriz TRUNCADA em `data_alvo` ≤ 31/12/2023.
  Sem × com truncagem: diferença **0,0** nos 12. Contra as salvas: 0,0.
- **Completo (além do pedido):** refiz as 20 células (5 q × 4 h) com a matriz truncada. Contra os **parciais brutos do executor**: diferença **0** nas 3.755 previsões (bit a bit). MAE médio por q idêntico.

### Piso (`verif_3_piso_retreino.py`)
- **Perturbação da semente 1 (minha):** colunas contínuas (17 de 22; inteiras = `casos`, `casos_lag1..4`); cada célula contínua move exatamente 1 ulp (`nextafter`); datas, `y_h` e colunas inteiras intactas; verificado nas sementes 1 a 4 e nos 4 horizontes.
- **Amostra pedida:** folha 20, h = 4, 2 origens (`data_alvo` 07/01/2024 e 09/02/2025): minha matriz s1 → previsão **igual** à salva (dif 0,0). Sem perturbar, a previsão difere 2,76 e 6,11 casos (a perturbação é efetiva).
- **Completo (além do pedido):** refiz as 16 células s1 e csv (2 folhas × 4 h) com laço próprio: mesmas linhas, n = 102, previsões iguais às salvas (dif máx. 2,3e-13, ver 4.1), MAE iguais (dif 6e-14).
- **Recálculo das salvas (`verif_1_recalculo.py`):** os 40 MAE, `n` = 102 nas 40, os deltas, o piso, o 2× e a perturbação do máximo batem com `piso.csv` (dif ≤ 3e-14; piso e 2× dif 0,0).
- Pisos (maior |Δ|): folha 5 = 5,221 / 12,311 / 12,677 / 7,019; folha 20 = 1,360 / 2,208 / 13,555 / 10,208 (h = 1/4/8/12). Deltas assinados vão de −12,68 a +13,56 (simétrico).

### Matriz `csv` (verificação 5)
- `matriz_hXX.csv` (h = 1, 4, 8, 12): mesmas colunas (mesma ordem), mesmas linhas (399/396/392/388), `data_origem`, `data_alvo` e `y_h` idênticos linha a linha com a matriz do pacote.
- Valores: 608 a 617 células diferem por matriz, diferença máxima **2,2e-16** (absoluta). Em ulps relativos chega a 199 (valores perto de zero, como `sem_cos` ≈ 1e-16); não é "≤ 1 ulp", e a pré-declaração só pede "a matriz lida do gabarito".

## 4. Divergências e observações (nenhuma bloqueia)

1. **`juntar_parciais` degrada as previsões em ~1 ulp.** Ele lê os parciais com `pd.read_csv` padrão (sem `float_precision="round_trip"`) e regrava `previsoes.csv`. Medido: parciais × junção diferem em até 5,7e-14 (E1; 904 de 3.755), 2,3e-13 (piso; 2.322 de 11.590) e 4,5e-13 (referência; 1.459 de 6.948). O retreino é bit a bit igual aos parciais; a diferença nasce na junção.
   - Efeito: nulo nos MAE (6e-14), nas decisões e nas travas (tolerância 1e-9, e a trava compara dois arquivos com a mesma degradação).
   - Sugestão (decisão do orquestrador): nos scripts novos (E2 etc.), ler com `float_precision="round_trip"`. `experimentos/referencia.py` é certificado e não deve mudar.
2. **A definição do sorteio das sementes não está na pré-declaração**; está só no docstring do módulo (um gerador `default_rng(semente)` percorrendo as colunas contínuas, `random(n) < 0.5` → +1 ulp). Minha implementação seguiu essa descrição e reproduziu as previsões salvas, o que confirma a implementação, mas outra convenção de sorteio daria outro piso.
3. **Zeros:** as sementes 1 a 4 levam **103 células com zero exato a ±5e-324** (denormal) por matriz, seguindo a letra da pré-declaração. Medi, como extra, a semente 1 com zeros preservados (8 células): deltas 1,60/2,02/2,32/0,89 (folha 20) e 4,78/0,35/13,43/2,10 (folha 5) contra 1,12/1,68/2,17/0,72 e 5,22/0,03/12,68/2,07 com zeros perturbados. Mesma ordem de grandeza; o piso não parece artefato dos denormais. Descritivo, sem decisão.
4. **O piso é o máximo de 5 sorteios**, então é um estimador ruidoso do ruído (por exemplo, a folha 5 em h = 4: delta de s4 = 12,3, de s1 = 0,03). Descritivo; a regra de 2× está aprovada.
5. Arquivo duplicado do Google Drive: `resultados/referencia/parciais/previsoes_folha20_h01 (1).csv` (idêntico por sha1 ao original; os scripts não o leem, mas um glob o contaria em dobro).

## 5. Arquivos

- Scripts: `comum_cert.py`, `verif_1_recalculo.py`, `verif_2_retreino_e1.py`, `verif_3_piso_retreino.py`, `diag_ulp_e1.py`.
- Saídas: `verif_1_recalculo.json`, `verif_2_amostra.{csv,json}`, `verif_2_completo.{csv,json,log}`, `verif_3_propriedades.json`, `verif_3_amostra.csv`, `verif_3_completo.{csv,log}`, `piso_mae_recalculado.csv`, `parciais_e1/`, `parciais_piso/`.
- Nada fora de `resultados/ciencia/certificacao/E1_piso/` foi escrito; nenhum teste estatístico rodado; sem git.
