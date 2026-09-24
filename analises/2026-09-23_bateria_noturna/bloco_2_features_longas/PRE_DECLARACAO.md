# Pré-declaração — Bloco 2: features longas, refeito sem vazamento

**Escrita em 23/09/2026, antes de rodar.** Mudança posterior vira emenda datada no fim.

## Pergunta
O teste de 30/08/2026 (`analises/2026-08-30_features_longo_prazo/`) sobrevive à correção do vazamento?
Em particular: o ENSO, único sinal positivo do projeto (−7,1% de MAE em h=8), continua lá?

## Por que refazer
O teste original tinha dois defeitos corrigidos depois:
- treino cortado por **posição** (`validos.iloc[:indice_corte]`), não pela data da resposta;
- quantil **0,80**; a referência atual é **0,85**.
Ele está na lista explícita de testes **não refeitos** após 13/09.

## Braços — idênticos aos de 30/08
| Braço | Colunas extras |
|---|---|
| A_referencia | nenhuma |
| A+B_lags_anuais | `casos_lag52`, `casos_lag104`, `vetor_lag52` |
| A+C+D_clima_longo | anomalia de temp/chuva/umidade contra a norma da semana do ano; acúmulo de 8 e 12 semanas |
| A+E_enso | `nino34_anom`, `oni` |
| A+TUDO | os quatro grupos |

As colunas extras entram **por fora** da seleção de clima em todos os braços, para isolar o efeito.

## Métrica, teste, família
- MAE na avaliação (`data_alvo >= 2024-01-01`), Wilcoxon **pareado por `data_alvo`**.
- Família: 4 variantes × 4 horizontes (1, 4, 8, 12) = **16 comparações**, Holm.

## Critério — o mesmo de 30/08, de propósito
Um grupo entra na referência se reduzir o MAE em **h=8 E h=12** com **p de Holm < 0,05** nos dois.

## Trava
A_referencia tem de reproduzir o painel (MAE 98,0/219,7/272,6/278,7). Se não, nada é reportado.

## Proibido
Criar grupos novos depois de ver o resultado. Aceitar o ENSO por horizonte isolado.
