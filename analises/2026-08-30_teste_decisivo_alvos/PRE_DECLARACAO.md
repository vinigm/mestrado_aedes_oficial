# PRÉ-DECLARAÇÃO — teste decisivo dos alvos (30/08/2026)

> Escrita **antes** de rodar. Autorizada pelo Vinicius em 30/08/2026.

## O problema que este teste resolve

Em 29/08 rodei detecção de surto com dois alvos e obtive respostas opostas:

- **confirmados** (2018+): o vetor ajuda em h=12 — p exato **0,00018**, sobrevive a Holm (0,00108);
- **notificados** (2012+): o vetor não ajuda, e inverte — p **0,541**.

Concluí que o vetor não ajudava. **A conclusão estava confundida por um erro de desenho meu.**
A pré-declaração da Rodada 1 dizia "muda só o alvo", mas era falso: estender a série para 2012
também mudou a **qualidade da medição do vetor**.

- de 2012 a 2018 a Secretaria não registrava se a vistoria aconteceu (`inspecao_realizada` nula);
- a densidade desses anos usa **denominador aproximado** — marcado pela coluna homônima;
- **45,8%** das semanas do experimento de notificados são assim; no de confirmados, ~0%.

Ou seja: os dois experimentos diferiam em **duas** variáveis ao mesmo tempo. Não dá para atribuir
a diferença ao alvo.

## O desenho — mais estrito do que o proposto originalmente

Propus rodar só notificados restrito a 2019+. **Vou fazer melhor:** rodar os **dois alvos sobre o
conjunto de semanas EXATAMENTE IDÊNTICO**.

**Janela comum, fixada antes de rodar:**

- `denominador_aproximado == 0` (vetor com denominador exato, 30/12/2018 em diante);
- **e** as duas séries de casos não-nulas na mesma semana;
- as duas rodadas veem a mesma grade, os mesmos lags e os mesmos passos de walk-forward.

Assim a **única** diferença remanescente entre os dois braços é o alvo — que é o que eu queria ter
feito na Rodada 1.

**Tudo o mais é idêntico à produção:** o motor é o `executar_walk_forward_surto` do próprio pacote
(importado, não copiado), horizontes **4, 8, 12**, percentis **90 e 95**, LightGBM com os mesmos
hiperparâmetros, corte de maturidade de 12 semanas.

## Correção múltipla — declarada agora

- **6 comparações por alvo** → Holm dentro de cada braço;
- **12 comparações no total** → Holm sobre o conjunto, porque a pergunta é a mesma nos dois braços.
- Nível **α = 0,05**. Reporto os dois, e o veredito usa o de 12.

## Regras de decisão, fixadas antes de ver o resultado

1. **Se o vetor ajudar nos DOIS alvos** → o negativo de 29/08 era o meu confundimento. O vetor no
   alarme de surto volta a ser candidato a núcleo da tese.
2. **Se ajudar SÓ nos confirmados**, com a janela agora idêntica → a diferença é do alvo, não da
   medição. Vira um achado sobre o que "confirmado" e "notificado" medem — e uma limitação séria da
   série de confirmados, que é administrativamente contaminada (taxa de confirmação caiu de 99,6%
   em 2023 para 42,0% em 2025).
3. **Se não ajudar em nenhum** → o resultado forte dos confirmados de 29/08 vinha das 45 semanas
   extras de 2018 que a recaptura do clima liberou, e não do vetor. Negativo confirmado.

**Proibido**, em qualquer desfecho: mudar janela, horizonte, percentil ou margem depois de ver os
p-valores.

## Ressalva registrada antes

Restringir a 2019+ **reduz a amostra** dos notificados de ~553 para ~270 semanas de teste. Perda de
poder é esperada e não pode ser lida como "o efeito sumiu": o desfecho a comparar é a **direção e o
tamanho** do efeito nos dois braços, com n agora equivalente.
