# Que limiar de surto serve para uma cidade com série curta?

> **Varredura de literatura em 26/09/2026**, a pedido do Vinicius. Três ângulos independentes em
> paralelo, mais uma síntese cética que cruzou os três. Nenhum modelo rodado, nenhum dado tocado.
> Fato e hipótese rotulados; fonte obrigatória por número.

---

## A pergunta

O Vinicius levantou uma hipótese: **Porto Rico teria criado seu sistema de limiares sem série histórica
longa**, ao contrário de Singapura, e por isso o método serviria para Porto Alegre, que também tem série
curta. Junto, propôs ancorar os limiares no Plano Municipal de Contingência de 2026.

---

## 1. 🚫 A premissa não se sustenta — e o inverso é que é verdade

**FATO.** Porto Rico tem vigilância contínua de dengue **desde 1986**, com o CDC Dengue Branch em San
Juan. O limiar epidêmico deles é o **percentil 75 de uma regressão binomial negativa ajustada a
~38,5 anos** de casos confirmados e prováveis, 86.282 casos de 1986 a 2024.

- Fonte: **MMWR mm7405a1**, *Dengue Outbreak and Response — Puerto Rico, 2024*, 20/02/2025, lido via
  PMC12370255. O preprint do método é **medRxiv 10.1101/2024.10.22.24315684**; o texto completo deu 403 e
  **não foi lido** — só o resumo.
- Em jan/2024 os casos semanais cruzaram esse limiar; a emergência foi declarada em mar/2024. O ano
  fechou com **6.291 casos e 11 óbitos**.
- **Detalhe do método:** a binomial negativa é ajustada sobre a série INTEIRA, sem excluir anos
  epidêmicos — ao contrário do canal endêmico clássico, que exclui.

**Leitura.** O método de Porto Rico é **estruturalmente igual ao MEM do InfoDengue**: percentil sobre
histórico. Ele não resolve série curta; ele exige série longa, mais longa que a de Singapura.

## 2. A contradição de fundo

- Todo limiar derivado do histórico — Porto Rico, MEM, canal endêmico — precisa de **anos NÃO
  epidêmicos** para calibrar o percentil do que é "normal".
- Porto Alegre tem **4 temporadas úteis, todas com epidemia** (2022-2025). A base é **curta E
  contaminada**.
- É exatamente o que já medimos aqui, em 25/09:
  - o canal endêmico dá limite **0** em muitas semanas fora da temporada;
  - o corte do MEM no InfoDengue **sobe de 6 para 94 casos/semana** entre 2010-2021 e 2025.
- **Conclusão:** série curta **quebra** esse tipo de método, não o valida.

## 3. ✅ Para onde a literatura aponta

Dois instrumentos que **não exigem histórico longo**:

### 3.1 Taxa fixa por população, sem linha de base

- **FATO.** Limiares fixos de incidência já são usados em área de invasão da dengue: **México ≥2 por
  100 mil/ano** e **Brasil ≥20 por 100 mil**. Fonte: *Nature Communications* 2024,
  `s41467-024-48465-0`.
- É a lógica do **Plano Municipal de Contingência de 2026** da SMS-POA, com os patamares de
  **140 · 421 · 702** casos/semana. A proposta do Vinicius cai aqui, e é a parte certa da ideia.

### 3.2 🟢 Aceleração de transmissão — o achado da varredura

- **FATO.** Regra: razão entre a **média móvel de 4 semanas** e a **de 26 semanas**; alarme quando passa
  de **1,33**. Fonte: **PMC13228775**, lido na íntegra.
- Testada em **8 países**, incluindo Singapura. Contra o canal endêmico:

  | Métrica | Aceleração | Canal endêmico |
  |---|---|---|
  | Sensibilidade | **100%** | 30% |
  | Antecedência média | **6,9 semanas** | 1,6 semanas |

- **Por que interessa aqui:** roda no mesmo arquivo semanal que já temos, precisa de **26 semanas** de
  história, e não de anos. Mede **aceleração**, não nível — então não depende de saber o que é "normal".
- ⚠️ **HIPÓTESE, não fato, para Porto Alegre:** o 1,33 foi calibrado em países endêmicos. Precisa ser
  medido aqui antes de qualquer afirmação.

## 4. 🔴 O aviso que vem dos nossos próprios dados

Em 25/09 testamos uma regra importada, a da Malásia — "acima do canal e crescendo". Ela foi **a pior de
todas** em Porto Alegre: Youden **−0,05** em 3 meses. Os próprios autores avisavam que não transferia.

**Consequência para a aceleração de transmissão:** ela é candidata forte, mas entra como **régua a
testar**, nunca como método adotado por citação. O precedente da Malásia é evidência direta de que
regra importada pode não transferir para cá.

## 5. O que ficou sem verificação

- **O limiar oficial do Ministério da Saúde** — as buscas deram 100 e 300 por 100 mil, sem fonte
  primária legível. PDFs do CONASS e do Guia de Vigilância vieram binários e não extraíveis.
  ⚠️ **Não citar esse número até ler a fonte.**
- **A janela real do InfoDengue em produção** — os três ângulos discordaram: 10, 14 e "de 3 a 16 anos",
  com o MEM recomendando ~6 temporadas. Não resolvido.
- **O texto completo do preprint de Porto Rico** e o método de Burkina Faso: bloqueio 403 e loop de
  redirecionamento. Não contornados.
- Nenhum ângulo achou **método validado de alarme com apenas 2 episódios**, que é a situação de Porto
  Alegre. Também não acharam framework aceito de validação para esse caso.

## 6. O que isso muda para a tese

- **O argumento fica mais forte, não mais fraco.** Em vez de "adaptamos o método de Porto Rico", a
  afirmação passa a ser: *os métodos padrão da vigilância pressupõem décadas de história; Porto Alegre
  está na fronteira de expansão da dengue e não as tem; medimos o que acontece quando se aplica mesmo
  assim, e propomos o substituto*.
- É um gap real: nenhum dos três ângulos achou literatura de alarme para cidade onde a dengue é nova.

## 7. Como foi feito

- Três agentes Sonnet independentes, raciocínio alto, em paralelo, mais um cético que cruzou os três e
  recebeu ordem de apontar discordâncias.
- Regras dadas a todos: fato separado de hipótese, fonte obrigatória por número, declarar explicitamente
  o que não conseguiu ler, nunca contornar bloqueio anti-robô, nunca estimar.
- Resultado bruto dos 4 agentes no journal da execução `wf_4abca939-850`.
