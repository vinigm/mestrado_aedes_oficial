# Certificacao de integridade - 12/10/2026 (agente independente, somente leitura)

Veredito: APROVADO COM RESSALVAS (ressalvas nao sao violacao; ver fim).

## (a) Codigo antigo intocado
- Manifesto sha256 recalculado com codigo proprio (`verif_manifesto.py`, mesmo escopo do cert do construtor: modelagem_aedes, analises, NOVO_HTML, Raspagem, pagina_web; sem a pasta de dados da Secretaria nem o CSV da Prefeitura).
- ANTES 4.269 | AGORA 4.274 | removidos 0 | alterados 0 | novos 5 = exatamente as adicoes esperadas (pre_declaracao_ciencia: PRE_DECLARACAO.md, .sha256, README.md; pre_declaracao_reproducao_e_wis: PRE_DECLARACAO.md, .sha256).
- `__pycache__`: 29 antes, 29 agora, 0 novos, 0 sumidos. Repetido depois da suite de testes: identico.
- Zonas ignoradas (dados da Secretaria, CSV da Prefeitura): so `find -newer` (stat), nada mais novo que o marcador. Nao abertas.

## (b) Arquivos mais novos que `.inicio_da_rodada` (17:56:59), raiz excluindo projeto_final/ e .git/
- `PENDENCIAS.md` e `CHECKLIST.md` (17:58:06): docs vivos da raiz, drill do orquestrador; fora do codigo antigo.
- `analises/2026-10-12_pre_declaracao_reproducao_e_wis/` (so a pasta, 17:57:10); os 2 arquivos dentro sao de 17:56:59 (nao posteriores ao marcador).
- Nenhum outro. Nada em modelagem_aedes/, NOVO_HTML/, Raspagem/, pagina_web/, docs/, resto de analises/.
- Informativo: 10 objetos novos em `.git/objects` (17:58 e 18:08), nenhuma ref/HEAD/log movido (ultimo commit 08/10): provavel git gc/maintenance ou hash-object; nao ha commit novo.

## (c) Arquivos certificados do pacote
- aedes (20 arquivos): 15 antigos com mtime < marcador, 5 novos (grade, hiperparametros, quantis, selecao_clima, wis), todos com birth time > marcador (criados, nao editados).
- experimentos: 13 antigos inalterados; 6 novos (comum_reproducao, e6a, e6b, e6c, e7, LEIAME_reproducao).
- testes: existentes inalterados; 6 novos (test_selecao_clima, test_grade, test_hiperparametros, test_quantis_wis, test_experimentos_reproducao, test_reproducao_diferencial).
- testes/referencia_antiga: MANIFESTO.csv (17 linhas) todos ok; 10 arquivos novos (MANIFESTO_E6_E7.csv + 9 copias); MANIFESTO_E6_E7 (9) ok e cada copia tem o mesmo sha256 do original no manifesto ANTES do codigo antigo; 0 nao listados.
- dados/ (0 arquivos mais novos), resultados/referencia (0/28), resultados/ciclo2 (0/2), resultados/ciencia (0/504): nenhum mais novo que o marcador.
- `dados/tabela_final.csv` sha256 6f34b854...6f1f = `tabela_final.sha256`. Confere.

## (d) Suite de testes
- `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m pytest -p no:cacheprovider -q` (sklearn 1.8.0, Python 3.14.4): **919 passed** em 156,75 s. Log: `pytest.log`.
- Nenhum `__pycache__`/.pyc/.pytest_cache criado em projeto_final.

## (e) Pre-declaracao
- sha256 de `analises/2026-10-12_pre_declaracao_reproducao_e_wis/PRE_DECLARACAO.md` = 4e6e3490...e6cb = conteudo do `.sha256`. Confere (9.543 bytes). Emendas: nenhuma.

## Ressalvas (nao violam as regras)
1. 8 arquivos `cert_*.csv` soltos na raiz de `projeto_final/` (20:09-20:11), de um certificador paralelo do E6 (scripts em resultados/reproducao_selecao/certificacao/). Dentro da zona permitida, mas poluem a raiz; mover para a pasta de certificacao.
2. Nao ha processo de rodada/pytest vivo no momento da checagem.
3. Esta certificacao cobre integridade e regressao, nao a ciencia de E6/E7 (reproducao dos numeros): isso e de outros certificadores.
