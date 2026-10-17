# Certificacao adversarial: E4 (corte) e integridade do codigo antigo, 12/10/2026

**Veredito: APROVADO_COM_RESSALVAS** (E4 e integridade passam; 3 ressalvas de leitura/documentacao, nenhuma invalida numero).

Scripts e saidas (nesta pasta): `cert_e4_corte.py` (V1+V2), `cert_integridade.py`, `cert_referencia.py`, `v1_retreino_tres_origens.csv`,
`v2_comparacao_recomputada.csv`, `v1_v2_resumo.json`, `integridade_resultado.json`, `referencia_resultado.json`, logs.

## V1 Semantica do corte ingenuo: PASSA
- Codigo (`aedes/walk_forward_com_corte.py`, regra PERGUNTA): treino = `data_origem < t`; a linha de teste (`s = t`) fica fora. Laco, modelo e validacao identicos ao `walk_forward.py`.
- Retreino com codigo proprio (sklearn direto, parametros explicitos = `FOLHA_5`, 0 divergentes): 12 origens (completo e sem_vetor x h=4 e h=12 x 3 origens: primeira, meio e ultima da janela).
- Treino == exatamente `{s < t}` nas 12; dif maxima do previsto vs salvo da E4 = **0,0** (bit a bit); corte pela resposta vs E2 tambem 0,0.
- Vazamento medido: h=4 -> 3 linhas de treino com resposta apos `t`; h=12 -> 11 (= h-1); corte pela resposta -> 0.
- Matriz: usei o construtor certificado `aedes.bracos` (nao reimplementei as 22 variaveis, por causa do caos de ultimo bit).

## V2 Recalculo de `comparacao.csv`: PASSA
- Recomputado do zero (pandas/numpy, formulas proprias): 24 linhas; dif maxima MAE 2,8e-14, variacao_pct 3,6e-15, R2 5,6e-17.
- n = 102 (completo) e 109 (sem_vetor) em todo h; mesmas `data_alvo` e mesmo `real` nos dois cortes; origens iguais em toda a serie (nao so na janela).
- h=1 variacao exatamente 0,0 nos dois bracos. `completo` corte-resposta == `referencia` (dif 0,0). 24 parciais = 7092 linhas = `previsoes.csv`; sem duplicatas.
- variacao_pct completo h=1..12: 0,0; -12,1; -18,3; -23,2; -11,1; -32,0; -33,4; -34,6; -40,6; -41,5; -43,7; -33,9. sem_vetor: 0,0; -10,8; -14,6; -18,3; -13,1; -16,8; -17,3; -28,8; -22,6; -28,9; -27,4; -29,8. Batem com o relato.

## V3 Integridade: PASSA
- (a) Manifesto recalculado (sha256, mesmo escopo e exclusoes do cert antigo): ANTES 4269; AGORA 4271; removidos 0; alterados 0; novos 2 = `analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md` e `.sha256` (pasta criada pela pre-declaracao, esperado). `__pycache__`: 29 = 29, novos 0, sumidos 0. Gabarito `testes/referencia_antiga`: 17 no MANIFESTO, 0 divergentes, 0 extras.
- (b) `find -newer .inicio_da_rodada` fora de `projeto_final/` (secretaria podada): `PENDENCIAS.md`, `CHECKLIST.md` (docs vivos, drill), a pasta da pre-declaracao (2 arquivos) e um `.git/objects/pack/*.pack`. Nada em modelagem_aedes/, analises antigas, NOVO_HTML, Raspagem, pagina_web, docs. O pack do `.git` e atividade de git externa (nao foi feita aqui); nao e codigo antigo.
- (c) `tabela_final.csv` sha256 = `6f34b854...f6f1f`, igual ao `.sha256`.
- (d) Todos os arquivos certificados do pacote tem data de criacao e modificacao <= 13:58, antes do marcador (14:31): `aedes/{configuracao,corte_temporal,dados,metricas,variaveis,walk_forward,__init__}.py`, `experimentos/{referencia,trava_walk_forward}.py`, testes antigos, `testes/referencia_antiga/`, `resultados/referencia/`, `resultados/ciclo2/`, `dados/`. Os 16 arquivos mais novos que o marcador nasceram depois dele (novos, nao alteracoes). Ancoras recalculadas de `resultados/referencia/previsoes.csv`: folha 5 MAE h1/4/8/12 = 97,987/219,669/272,627/278,818; folha 20 = 133,626/199,635/223,183/243,765; n=102 por h; calibracao n=193/190/186/182 e MAE 22,337/45,786/48,167/51,799. Todas iguais as ancoras. `metricas.csv` h=1 confere.
- (e) `PRE_DECLARACAO.md` sha256 `ef2b445d...87a` = ultima linha do `.sha256` (versao com a emenda 2). O arquivo contem 3 hashes (aprovada, +emenda 1, +emenda 2); nao consegui reproduzir o hash da versao aprovada cortando o texto antes de "## Emendas" (variacoes de quebra de linha testadas), entao a integridade do corpo original so e conferida pelo hash da versao final.
- Nenhum `__pycache__`, `.pyc` ou `.pytest_cache` em `projeto_final/`; nenhum processo orfao; nenhum `.tmp` remanescente.

## Ressalvas
1. **A ancora de 13/09 FOI reproduzida; o relato do executor leu a base errada.** O "+52%" de 13/09 e o custo de CORRIGIR sobre o MAE do corte ingenuo (`MAE_resposta/MAE_pergunta - 1`). Pela mesma conta aqui: completo h=12 **+51,4%** (ancora +52,5%), h=4 **+30,2%** (ancora +31,5%). A `variacao_pct` do arquivo usa a base oposta (resposta), por isso aparece -33,9%. A frase da pre-declaracao ("reduziu o MAE em ~52%") e ambigua. Texto do artigo deve dizer a base, ex.: "o corte ingenuo parece 34% melhor; corrigir custa 51% a mais de MAE". Nao e criterio de trava.
2. **Emenda 2 (R2 em pontos) nao esta no `comparacao.csv`**: o arquivo traz so `r2_corte_resposta`/`r2_corte_pergunta`; a diferenca em pontos precisa ser derivada (ja calculada em `v2_comparacao_recomputada.csv`, coluna `delta_r2_pontos`: h=12 completo +0,305, sem_vetor +0,319).
3. **Leitura descritiva do sem_vetor:** o corte ingenuo "melhora" o sem_vetor menos que o completo em h=6..12 (ex.: h=12 -29,8% vs -33,9%), mas em h=1 os MAE-base diferem (118,1 vs 98,0) porque o sem_vetor tem 109 semanas e o completo 102; as comparacoes de variacao_pct sao dentro de cada braco, nunca entre bracos em n. Sem teste, sem interpretacao.
