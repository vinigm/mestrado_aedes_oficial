# Revisão adversarial — página Comparações

**Data:** 25/09/2026 · **Revisor:** agente independente · **Veredito: REPROVADO** (achados abaixo, sem
divergência numérica)

---

## O que foi conferido

- Todos os números exibidos em `NOVO_HTML/saida/comparacoes.html` contra as 4 fontes (READMEs de
  `2026-09-25_regua_regras_simples`, `_modelos_de_fundacao`, `_sarima_lasso_ensemble`,
  `_comparacao_direta_literatura`): **0 divergências numéricas, 0 arredondamento errado, 0 sinal
  invertido.** Gráficos de barra (literatura e vantagem) reproduzem exatamente os 8 e 3 itens esperados,
  na ordem certa, com SARIMA e Superensemble fora do gráfico como planejado.
- Menu "Comparações" entre "Cenário adotado" e "Próximos passos" nas **7** páginas de `saida/`.
- `docs/` intocado (`git diff --stat docs/` vazio); nenhum commit foi feito.
- HTML bem formado (0 tags soltas), os 11 `<svg>` têm `viewBox`.
- Código novo: sem `lambda`, comprehensions são só reshape de dado (sem regra de negócio), type hints e
  docstrings presentes em `graficos.py` e `numeros_do_projeto.py`.
- Texto: acentuação completa, sem "h=12", sem dupla negação, sem adjetivo de efeito.

## Achados

### 1. Números soltos no código da página (viola o item 2 do pedido)

`montar_metricas()` grava `217.8`, `227.2`, `"+13%"` e `"6"` como literais em `comparacoes.py`, em vez de
ler de `numeros_do_projeto.py`. O mesmo ocorre nos 3 cartões da Seção 1 (`83,3` / `199,6` / `217,8`,
linhas 85, 90, 96) e na nota do SARIMA na Seção 2 (`1.971,0`, linha 142). Os valores **batem** com a
fonte, mas a regra explícita — "nenhum número solto no código da página" — foi quebrada em 4 pontos.
Solução: montar esses textos a partir de `REGUA_DE_METODOS_SIMPLES` / `METODOS_DA_LITERATURA_NOS_DADOS`
(inclusive o "6" deveria ser `len(...)`, não uma contagem manual).

### 2. Proveniência do "Ensemble com pesos aprendidos" (Seção 2)

A linha usa `este_projeto=False` e atribui a origem a **"Wu et al. 2025; Colón-González et al. 2021"**.
Mas, pela `PRE_DECLARACAO.md` de `2026-09-25_sarima_lasso_ensemble` (linhas 36-39, 63-68), `ens_pesos` é
**"um ensemble de tudo o que temos"**: 5 componentes do próprio projeto (B0, Chronos-2, SARIMA, LASSO,
régua), com pesos aprendidos no walk-forward do projeto — não é a reprodução do método de nenhum dos dois
artigos, só foi **motivado** pela leitura de que ensembles bateram a régua nesses papers. Na seção
"Métodos da literatura nos nossos dados", isso lê como se fosse o método deles rodado aqui. Ajustar para
`este_projeto=True` (ou origem "este projeto, inspirado em Wu et al. 2025 e Colón-González et al. 2021").

### 3. Rótulo do R² do da Silva et al. 2026 inconsistente com a linha vizinha

Na tabela 3c, a ressalva "escala log, horizonte não declarado" foi para a coluna **Onde**, deixando
`0,46` sozinho sob o cabeçalho **"1 mês"** — parece um R² comparável aos demais. A linha de cima
(CatBoost 27 capitais) resolve o mesmo problema colocando a ressalva **dentro da própria célula**
("−0,21 (até 4 semanas)"). Duas soluções diferentes para o mesmo tipo de nota, na mesma tabela; a segunda
é mais clara e evita o risco de leitura errada.

### 4. Nitpick tipográfico

Sinal negativo com hífen comum (`-7%`, `-21%`, seção 3d) em vez do menos tipográfico `−` usado na tabela
3c (`−0,21`). Inconsistência visual, não numérica.

## Recomendação

Corrigir os itens 1 e 2 antes de aprovar (são o item 2 do pedido e uma questão de honestidade de
atribuição, sensível dado o retorno do Mansilha de 24/09 sobre tom). Itens 3 e 4 são polimento, a
critério do Vinicius.
