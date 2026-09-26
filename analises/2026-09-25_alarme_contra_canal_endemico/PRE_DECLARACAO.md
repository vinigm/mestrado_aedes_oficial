# Pré-declaração — o alarme do modelo contra o canal endêmico

> **Escrita em 25/09/2026, antes de calcular qualquer canal ou alarme.** Autorizada pelo Vinicius em
> 25/09/2026 ("pode rodar, vamos ver o que conseguimos"). Mudança posterior vira **emenda datada** no fim.
>
> ⚠️ **Rodada exploratória.** As previsões de 2024+ já foram vistas em outras métricas. Nenhum modelo é
> treinado: só se leem previsões existentes e se calcula estatística dos anos passados.

---

## 1. Pergunta

**O alarme do modelo, emitido 1 e 3 meses antes, acerta as semanas de surto melhor que as regras que a
vigilância já tem sem modelo?**

- **O que o dado mostra** (13/09/2026): o cenário adotado pega **76,9%** das semanas de surto com 3 meses
  de antecedência, com **81,1%** de precisão. **Nunca foi comparado com uma regra simples.**
- **Referências do método:**
  - canal endêmico em escala log com regra de crescimento: Singh et al. 2026, *Tropical Medicine and
    Infectious Disease*, DOI 10.3390/tropicalmed11080231;
  - canal por percentil 75: sistema de limiares do CDC Dengue Branch para Porto Rico, medRxiv
    10.1101/2024.10.22.24315684.
- **Adaptação necessária a Porto Alegre:** o canal clássico exclui os anos de epidemia, mas aqui os únicos
  anos sem epidemia, 2018-2021, têm quase zero caso. **Todos os anos anteriores entram**, e isso é
  declarado como adaptação.

---

## 2. Duas definições de semana de surto

| Evento | Definição | Por quê |
|---|---|---|
| **E_100** | `real > 100` casos | a definição de 13/09, para ligar com os 76,9% |
| **E_canal** | `real` acima do **limite superior do canal em log** da semana epidemiológica | a definição da vigilância, pelo método de Singh et al. 2026 |

### Os três canais, fixados antes

Para a semana epidemiológica `w` de um ano `Y`, com os casos de `w` em todos os anos anteriores
disponíveis, a partir de 2018 e com **no mínimo 3 anos**:

| Canal | Limite superior |
|---|---|
| **C_log**, Singh et al. 2026 | `expm1(média + 2·DP de log1p(casos))` |
| C_conv, convencional | `média + 2·DP dos casos` |
| C_p75, Porto Rico | percentil 75 empírico dos casos. Simplificação declarada: o artigo usa binomial negativa |

- **Principal:** C_log. **Secundários, descritivos:** C_conv e C_p75.
- Os valores de `w` em anos anteriores têm, na origem, ao menos 40 semanas de idade: já eram conhecidos.

---

## 3. As regras de alarme

Todas são emitidas na semana de origem `t`, para a semana `t + h`.

| Regra | Alarme para `t+h` quando | O que representa |
|---|---|---|
| **M_adotado** | previsão do cenário adotado em `t+h` passa do limite do evento | o modelo |
| **M_folha20** | previsão do HistGB folha 20 em `t+h` passa do limite | o modelo com folha 20 |
| **R_hoje** | `real[t]` passa do limite da semana `t` | o que a vigilância já sabe sem modelo: a situação de hoje |
| **R_hoje_crescendo** | `real[t]` passa do limite **e** `real[t] > real[t−1]` | a regra de alerta de Singh et al. 2026 |
| **R_ano_passado** | `real[t+h−52]` passa do limite da semana `t+h` | a mesma semana do ano anterior |

- O limite depende do evento: **100** em E_100; o limite do C_log em E_canal.
- Previsões: as do bloco 7 da bateria noturna, `referencia` e `HistGB_folha20_M1`, nos mesmos pares
  `(h, data_alvo)`.

---

## 4. Métricas

- **Sensibilidade:** das semanas de surto, quantas tiveram alarme.
- **Precisão:** dos alarmes, quantos eram surto.
- **Especificidade:** das semanas calmas, quantas ficaram sem alarme.
- **Alarmes falsos por ano:** semanas com alarme e sem surto, por ano de avaliação.
- **Índice de Youden** = sensibilidade + especificidade − 1. É o **resumo principal**, o mesmo usado por
  Singh et al. 2026.
- Horizontes **1, 4, 8 e 12 semanas**. **Decisão em 4 e 12.** Avaliação `data_alvo ≥ 2024-01-01`.
  Calibração epidêmica 2022-2023 só descritiva.

### Trava, antes de ler resultado

O cenário adotado, com a definição e o script de 13/09, tem de reproduzir: **h=12: sensibilidade 76,9%,
precisão 81,1%, 2,3 falsos por ano · h=4: 97,1%, 94,3%, 0,7 falsos por ano**. Se não reproduzir,
investiga-se antes de ler qualquer outro número.

### Teste

- McNemar exato, pareado por semana, sobre acerto ou erro da classificação: cada modelo contra
  **R_hoje** e contra **R_ano_passado**, em h=4 e h=12, nos eventos E_100 e E_canal.
- Família: 2 modelos × 2 regras × 2 horizontes × 2 eventos = **16 comparações**, Holm sobre 16.
- ⚠️ Há só **2 episódios de surto** na avaliação e 30 a 40 semanas de surto. O poder do teste é baixo;
  a leitura principal é descritiva.

---

## 5. Critérios de decisão

- **O alarme do modelo vence o canal** se, em **h=12** e no evento **E_canal**, o Youden do modelo for maior
  que o de **R_hoje** e o de **R_ano_passado**, e o McNemar contra R_hoje tiver **p Holm < 0,05**.
- **Leitura descritiva forte:** Youden maior que as duas regras em h=12 nos dois eventos, sem significância.
- Nada muda a referência. Um resultado positivo é hipótese para 2026-2027.

---

## 6. Ameaças já conhecidas

- **Dois episódios na avaliação.** Qualquer métrica por episódio não vale.
- **O canal de 2025 inclui 2024**, a maior temporada até então, e fica alto. O de 2024 inclui 2022 e 2023.
  O desenho favorece que 2024 apareça como surto e 2025 menos.
- **O limiar de 100 casos é convenção do projeto**, não corte epidemiológico validado.
- **O modelo prevê o quantil 0,85**, por cima de propósito. Isso ajuda a sensibilidade e pode custar
  precisão.

---

## Emendas

Nenhuma até agora.
