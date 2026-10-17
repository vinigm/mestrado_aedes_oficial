# E6 — reprodução da seleção do modelo no pacote (12/10/2026)

> Pré-declaração aprovada pelo Vinicius em 12/10/2026: `analises/2026-10-12_pre_declaracao_reproducao_e_wis/PRE_DECLARACAO.md`.
> Certificada por agente independente (`certificacao/CERTIFICACAO.md`, APROVADO), com integridade conferida
> (`certificacao_integridade/RELATORIO.md`: código antigo intocado, 919 testes passando).

## Pergunta

As etapas que escolheram o modelo do artigo podem ser refeitas em código novo, sem depender do código antigo, e dão o
mesmo resultado?

## Resultado: sim, nas três etapas

- **E6a, seleção do clima:** as **mesmas 6 colunas, na mesma ordem**, em 3 execuções do executor e em 5 do certificador:
  temp_media_lag4, umid_media, temp_media_lag3, temp_max, pressao_media_lag3, pressao_media_lag4.
  - Testadas com e sem semente e com 1 ou todas as threads; o ganho é idêntico entre as variantes.
  - **Margem:** a 7ª candidata (temp_amplitude_media) tem 85,9% do ganho da 6ª.
- **E6b, grade de 30:** **35.490 previsões iguais às do código antigo**, com diferença 0,0 nos 3 algoritmos.
  - Ranking idêntico: 1º HistGB q0,85 M1 com **42,019**, depois 42,516, 42,712 e 42,715; 30º com 58,455.
  - O vencedor é a configuração do artigo.
- **E6c, grade de 18:** **13.518 previsões iguais**.
  - Fase 1: 1º 0,03×400 com **41,662**; a configuração principal fica em 4º com **42,022**, menos de 1% atrás.
  - Fase 2, com Wilcoxon e Holm em 4 testes, n = 102: −7,52%, +3,31%, +0,13% e +0,15%; p de Holm 1,0. Não há troca.
- **O modelo do artigo não muda**, pela regra do Vinicius, e a reprodução não deu nenhum motivo para mudar.

## Ressalvas

- **Empates exatos de MAE na E6c** (10º/11º, 13º/14º e 16º/17º, todos na folha 20): o pacote usa ordem alfabética
  estável e só o 13º/14º troca de posição em relação ao antigo.
- **A seleção do clima continua fora do walk-forward** (até nov/2022). É a limitação declarada no artigo; agora ela é
  reproduzível.

## Arquivos

- `E6a_clima/`: ganho de cada candidata e `resumo.json`.
- `E6b_grade30/`: ranking e previsões.
- `E6c_grade18/`: fase 1 e fase 2.
- Scripts: `experimentos/e6a_clima.py`, `e6b_grade30.py` e `e6c_grade18.py`; ver `experimentos/LEIAME_reproducao.md`.
