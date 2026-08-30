# PRÉ-DECLARAÇÃO — o vetor ajuda no modelo calibrado? (30/08/2026)

> Escrita antes de rodar. Autorizada pelo Vinicius em 30/08/2026.

## A pergunta central da tese

Todos os testes anteriores de *"a armadilha ajuda a prever dengue?"* rodaram com a **perda padrão**
(erro quadrático) — que hoje sabemos estar **sistematicamente enviesada para baixo** nos picos.

É uma falha de desenho: se o modelo estava mal calibrado, o teste do vetor pode ter medido a
limitação do modelo, e não a informação do vetor.

**Aqui o vetor é testado no modelo bem calibrado**: HistGradientBoosting com quantil 0,85, a
configuração validada em 30/08 fora do período de calibração.

## Desenho

- **Algoritmo:** `HistGradientBoostingRegressor`, hiperparâmetros do projeto.
- **Perdas:** padrão (`squared_error`) e **quantil 0,85**. O alpha 0,90 fica para o grid noturno.
- **Conjuntos de features:**
  - **M0** = núcleo + 6 variáveis de clima (**sem vetor**);
  - **M1** = M0 + as colunas do vetor (`aedes_aegypti_por_armadilha` e suas defasagens, `vetor_mm4`).
- **Horizontes:** 1, 4, 8, 12 · **`passo=1`** (~300 pontos por horizonte).
- **= 16 execuções de walk-forward.**

## Separação, igual à calibração anterior

- **calibração:** semanas-alvo até **31/12/2023**;
- **avaliação:** **2024 em diante**.

O veredito usa a **avaliação**. A calibração entra só como conferência de consistência.

## Teste estatístico — declarado agora

Comparar MAE lado a lado não basta: diferença pequena pode ser acaso. Uso o **Diebold-Mariano**
pareado (as duas configurações preveem exatamente as mesmas semanas), com correção de **Holm** sobre
as **8 comparações** (2 perdas × 4 horizontes). Nível **α = 0,05**.

## Regras de decisão, fixadas antes de ver o resultado

1. **M1 vence M0 e sobrevive a Holm** → o vetor **acrescenta informação** quando o modelo está bem
   calibrado. Isso **reabre** o valor preditivo das armadilhas e muda o eixo da tese de volta.
2. **M1 vence M0 mas não sobrevive a Holm** → indício, não achado. Registrado como direção
   favorável sem significância, e o eixo da equivalência permanece.
3. **M1 não vence M0** → a redundância do vetor com o clima fica **muito mais forte**: agora testada
   no melhor algoritmo, na melhor calibração, com ~300 pontos por horizonte. Passa a ser o achado
   mais bem sustentado do projeto.

**Os três desfechos são publicáveis.** O 3 é o mais provável dado tudo que já medimos — e é
justamente por isso que ele precisa estar declarado como aceitável ANTES de rodar.

**Proibido:** trocar alpha, algoritmo ou horizonte depois de ver o resultado para procurar um
desfecho melhor.

## Ressalva registrada antes

O modelo quantílico estima um **patamar**, não a média. A comparação M0 × M1 é justa porque **as
duas rodam na mesma perda** — o que se compara é o efeito de acrescentar o vetor, não o efeito da
calibração.
