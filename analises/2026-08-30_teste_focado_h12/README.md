# Teste focado em horizonte longo — 30/08/2026

> Regras em [PRE_DECLARACAO.md](PRE_DECLARACAO.md), escritas antes de rodar.
> **EXPLORATORIO, nao confirmatorio** — a hipotese nasceu destes mesmos dados.

**Execucao:** 60 walk-forwards (3 algoritmos × 2 conjuntos × 2 horizontes × 5 sementes), `passo=1`.
**1h53, sem falhas.**

## Resultado — horizonte de 12 semanas

| algoritmo | MAE sem vetor | MAE com vetor | ganho | sementes com ganho | IC exclui zero |
|---|---|---|---|---|---|
| LightGBM | 211,5 | **167,1** | **+44,3** | 5/5 | **5/5** |
| HistGradientBoosting | 214,3 | **179,6** | **+34,7** | 5/5 | **5/5** |
| GradientBoosting | 222,8 | **189,3** | **+33,5** | 5/5 | 0/5 |

## Resultado — horizonte de 8 semanas

| algoritmo | ganho | sementes com ganho |
|---|---|---|
| LightGBM | +3,7 | 5/5 |
| GradientBoosting | −2,2 | 1/5 |
| HistGradientBoosting | −2,0 | 0/5 |

**O efeito e especifico de 12 semanas.** Em 8 semanas ele desaparece e o sinal muda com o algoritmo.

## Veredito: desfecho 1 da pre-declaracao

**0 de 6 comparacoes sobrevivem a Holm(6)** — melhores p brutos 0,027 e 0,031, que sozinhos
passariam, mas multiplicados por 6 viram 0,16.

O que o teste **acrescentou** ao "15 de 15" que ja se sabia:

- ✅ o efeito **nao depende da inicializacao** — 5 sementes, mesmo resultado;
- ✅ **nao e artefato de um algoritmo** — aparece nos tres;
- ✅ o **tamanho** esta medido: 33,5 a 44,3 de MAE sobre uma base de ~215 (15% a 20%);
- ✅ o **IC exclui zero** em 2 dos 3 algoritmos, em todas as sementes;
- ✅ e **especifico do horizonte longo**, onde a autocorrelacao dos casos vai a zero;
- ❌ **nao sobrevive** a correcao para multiplas comparacoes.

## Frase defensavel

> Em horizonte de 12 semanas, o acrescimo das variaveis entomologicas reduziu o MAE em 33,5 a 44,3
> casos, nos tres algoritmos testados e nas cinco inicializacoes. O intervalo de confianca da
> diferenca exclui zero em dois dos tres algoritmos, em todas as sementes. Nenhuma comparacao
> sobreviveu a correcao de Holm sobre seis testes. O efeito e especifico do horizonte longo: em
> oito semanas, desaparece.

## ⚠️ O que tornaria isto confirmatorio

Testar na temporada **2026-2027** — o unico dado que ainda nao existe e, portanto, o unico que a
hipotese nao pode ter sido moldada para caber.

## Achado colateral registrado, NAO adotado

O **LightGBM lidera em h=8 e h=12 no periodo de avaliacao** (167,1 contra 179,6 do HistGB em h=12),
mas e o **pior dos tres na calibracao**, nos quatro horizontes. Inverter a escolha com base na
avaliacao invalidaria o protocolo. Fica como hipotese para teste proprio: **o melhor algoritmo pode
depender do horizonte** — plausivel, ja que horizonte curto e dominado pela autocorrelacao e o
longo pelo clima e pelo vetor.
