# Busca aleatória de hiperparâmetros, julgada em 2026

> **Rodada na noite de 25/09/2026**, em 12,6 min com 8 processos. Protocolo em [PRE_DECLARACAO.md](PRE_DECLARACAO.md),
> com emendas. Certificação em [CERTIFICACAO.md](CERTIFICACAO.md). A escolha usou só 2022-2025; o julgamento foi
> em 2026, de janeiro a 19/04, 16 semanas.

> 🚫 **FORA DA AVALIAÇÃO — decisão do Vinicius em 26/09/2026:** 2026 não será usado, e esta busca rodou na tabela
> com 2026. Fica **só como registro**; refazer na tabela oficial antes de citar. O julgamento em 2026 não escolhe
> configuração: num ano calmo ganha quem prevê baixo, como mostra o LightGBM com folhas lineares. Em 2024-2025,
> com a ressalva de que esse período entrou na escolha, em 3 meses a melhor, `LGB_best`, erra **239,6**,
> contra 293,3 do adotado, 254,1 do HistGB folha 20 e **226,8 da régua sazonal**
> (`saidas/descritivo_2024_2025.csv`). **Mesmo com a escolha a seu favor, ela não bate a régua.**

## Em uma frase

**Nenhuma das 120 configurações passou no critério.** A única que erra muito menos em 2026 é o LightGBM com
folhas lineares, mas ele dispara alarme em todas as semanas.

## As vencedoras, escolhidas em 2022-2025

| | Parâmetros | Nota: MAE médio de 1 e 3 meses |
|---|---|---|
| **LightGBM** | taxa 0,022 · 177 árvores · 49 folhas · folha mínima 10 · 92% das colunas · 81% das semanas · `extra_trees` | **160,95** |
| **HistGB** | taxa 0,197 · 239 árvores · 55 folhas · folha mínima 15 · 51% das colunas · profundidade 8 | 161,74 |

## O julgamento em 2026

| Modelo | MAE, 1 mês | MAE, 3 meses | Alarmes falsos em 3 meses, limiar 100 | Maior previsão em 3 meses |
|---|---|---|---|---|
| Cenário adotado | 223,8 | 482,9 | 9 de 16 | 1.117 |
| HistGB folha 20 | 601,0 | 579,0 | 11 | 1.299 |
| Vencedora HistGB | 350,1 | 439,7 | 10 | 1.211 |
| Vencedora LightGBM | 234,0 | 540,9 | 9 | 1.205 |
| **LightGBM com folhas lineares** | **94,2** | **201,6** | **16 de 16** | 208 |
| Régua "o ano passado" | 902,9 | 902,9 | 11 | 2.381 |

Nenhuma semana de 2026 passou de 3 casos confirmados.

- **Critério:** MAE menor **e** menos alarmes falsos **e** p Holm < 0,05. **Ninguém passa.** O menor p Holm foi 0,17.
- **LightGBM com folhas lineares:** as previsões ficam entre ~90 e 210 casos o tempo todo, então o erro é pequeno mas
  passa de 100 em todas as semanas. Ele **não reagiu à calmaria**, só previu valores moderados sempre.
- **A restrição monotônica foi impossível:** o LightGBM 4.6 recusa esse tipo de restrição com perda quantílica.
- ⚠️ **Nota:** o arquivo `saidas/trava_cenario_adotado.json` diz "inválido" por um erro de janela na função de
  trava. Recalculada na janela certa, a trava é **válida**: 97,38 / 211,31 / 270,55 / 279,96. Ver a emenda de
  26/09 01h20.
