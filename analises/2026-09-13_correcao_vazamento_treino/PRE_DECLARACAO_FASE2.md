# PRÉ-DECLARAÇÃO — FASE 2: correção aplicada a todo o projeto

**Escrita em 13/09/2026, antes de rodar.** Continua [PRE_DECLARACAO.md](PRE_DECLARACAO.md), cuja fase 1
mediu o custo do vazamento em 8 configurações e **reprovou** o critério de ranking. Ponto de retorno:
tag `antes-correcao-vazamento` (commit `6656598`).

---

## 1. O que motiva a fase 2

A fase 1 mostrou que o vazamento **não era neutro entre configurações**:

- com vetor apanhou **~2×** mais que sem vetor (20,5% × 11,3% de piora no MAE de calibração);
- perda quantílica apanhou **~2×** mais que a padrão (28,7% × 15,8%, mesmo algoritmo e conjunto).

Como vetor e perda quantílica são os dois ingredientes da configuração de referência, nenhuma
comparação do projeto pode ser considerada de modo comum sem medição. Daí refazer tudo.

## 2. A correção aplicada

Regra única, centralizada em **`modelagem_aedes/motor/corte_temporal.py`**: só entra no treino a linha
cuja **resposta** já tinha acontecido na data da previsão. Filtro por data, nunca por posição.

Aplicada em **5 pontos do código de produção** (`walk_forward_regressao`, `walk_forward_pareado`,
`walk_forward`, `comparacao_literatura`, `walk_forward_bairro`) e em **3 cópias corrigidas** das
rodadas de 29/08, nesta pasta. Suíte: **22/22**.

**Não corrigido, por não ter o defeito:** `acerto_aceleracao_walk_forward`. O rótulo dele é
`casos[t] − casos[t−2] > 0`, que olha só para trás — é contemporâneo à origem, não tem horizonte.

## 3. O que será rodado

| Bloco | O que | Custo | O que destrava |
|---|---|---|---|
| A | Grid: as **22** configurações restantes (88 células) | ~2h | Configuração de referência · "a perda importa mais que o algoritmo" |
| B | **Rodada 2**, equivalência clima × vetor, 2 alvos | ~6 min | O núcleo proposto da tese |
| C | **Rodada 4**, janela de treino | ~2 min | "Treinar desde 2012 vence" (bloqueado pela Emenda 1.3) |
| D | **Rodada 3**, ranking espacial | ~2 min | A célula 1 de 8 em que o modelo vence (bloqueada pela Emenda 1.4) |
| E | Pipeline: `comparacao_literatura`, `cidade_regressao`, `cidade_diebold`, os 2 de surto | ~15 min | "Vence persistência e sazonalidade" · converte as dispensas em medição |

Ordem: **os baratos primeiro** (B a E, ~25 min), o grid por último. Erro de setup aparece em minutos.

## 4. Controle (gate de toda a fase)

**h=1 tem 0 linhas contaminadas, logo todo resultado de h=1 tem de ser idêntico ao original.**

- Vale para o grid (22 células de h=1), a Rodada 2, a Rodada 4 e a Rodada 3.
- Critério: diferença de previsão < 0,01.
- **Se qualquer h=1 divergir, a fase inteira é descartada** e nada dela é interpretado.
- ⚠️ **Exceção declarada:** os experimentos de surto usam horizontes (4, 8, 12) e **não têm h=1**.
  Eles ficam sem controle interno e serão lidos com essa ressalva por escrito.

## 5. Critérios de decisão, fixados agora

**Bloco A — grid.** O vencedor é quem tiver o menor MAE de calibração (média dos 4 horizontes), mesmo
critério de 30/08. Adotado sem discussão, seja quem for, e `config/experimentos/cidade_referencia.py`
passa a refleti-lo. A vantagem da perda quantílica sobre a padrão no par de mesmo algoritmo e conjunto
é reportada pelo valor medido, sem limiar: era 20,2 pp, na fase 1 deu 8,1 pp com 8 configurações.

**Bloco B — equivalência.** Reportar o TOST com **as duas margens**:

- % do MAE da **persistência**, que é o que a pré-declaração de 29/08 fixou → **é a que vale**;
- % do MAE do **clima**, que é o que o código fez → reportada só para mostrar a diferença.

O alvo que decide é **confirmados** (decisão de 30/08). Notificados entra como secundário. Declarado
agora: se a equivalência fechar em confirmados com a margem da persistência, o núcleo se sustenta; se
não fechar, **a equivalência não pode ser o núcleo da tese** e isso será escrito assim.

**Bloco C — janela de treino.** Se `expansivel_2012` continuar vencendo em 3 de 4 horizontes, o item
volta a ser citável. Se cair para 2 de 4 ou menos, vira resultado indeterminado.

**Bloco D — espacial.** Se a única célula k×h em que o modelo vencia a persistência deixar de vencer,
a conclusão passa a ser **8 de 8 a favor da regra simples**, o que fortalece a Camada 2.

**Bloco E — negativos.** Se os resultados negativos (vetor não melhora alarme de surto; nada sobrevive
a Holm) se mantiverem, deixam de ser "reforçados por argumento" e passam a **medidos**. Se algum
inverter, é achado maior e a Emenda 1.5 é revista.

## 6. O que esta fase NÃO faz

- **Não publica o site.** O bloco E sobrescreve `dados/saidas/resultados/` e cria execuções novas no
  MLflow, mas `pagina_web/gerar.py` **não** será rodado e nada será commitado em `docs/`. A decisão de
  publicar fica para depois de ler os números. Os resultados antigos estão versionados no git e
  voltam pela tag.
- **Não corrige a seleção das 6 colunas de clima**, que segue por fração de posição sobre 60% da
  série. ⏳ próprio.
- **Não corrige a margem do TOST no código** — a margem pré-declarada é recalculada na análise.
- **Não troca a métrica de captura do pico**, que segue sendo razão de nível e não taxa de alarme.
- **Não refaz** o teste focado de h=12 (sobreviveu na fase 1) nem a calibração quantílica (superada
  pelo grid).

## 7. Riscos declarados

- O grid pode eleger uma configuração diferente. Isso é esperado e aceito: o critério manda.
- Os experimentos de surto não têm controle de h=1.
- `bairro_surto` recebeu a correção mas **não** será rodado nesta fase; qualquer número de bairro
  anterior segue marcado como medido com o corte antigo.

---

## Emendas

*(nenhuma até agora)*
