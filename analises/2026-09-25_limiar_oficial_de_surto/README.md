# Critério oficial de surto de dengue em Porto Alegre

> **25/09/2026.** Pergunta do Vinicius: de onde vem o limiar de 100 casos por semana? Detalhe em
> [criterio_oficial.md](criterio_oficial.md) e [verificacao.md](verificacao.md).

## Resposta curta

- **Os 100 casos são convenção do projeto**, sem base oficial.
- **O Plano Municipal de Contingência de Arboviroses 2026 da SMS-POA**, de dez/2025, Quadro 1, p. 15, usa
  incidência semanal de confirmados:

  | Estágio | Critério, resumido | Em casos por semana, pop. 1.404.269 |
  |---|---|---|
  | Normalidade | confirmados abaixo do Limite de Alerta, **ou** abaixo de 10 por 100 mil, nas 4 últimas semanas | abaixo de **140** |
  | Mobilização | acima do Limite de Alerta em pelo menos 1 das 4 semanas **e** acima de 10 por 100 mil, entre outras combinações | acima de **140** |
  | Alerta | entre o Limite de Alerta e o Limite Superior Endêmico em 3 das 4 semanas **e** acima de 30 por 100 mil; **ou** sorotipo novo; **ou** 1 óbito | acima de **421** |
  | Epidemia | acima do Limite Superior Endêmico nas 4 semanas **e** acima de 50 por 100 mil em pelo menos 1; **ou** mais de 1 óbito | acima de **702** |

  - ✅ **Conferido pelo Vinicius no PDF**, em 25/09/2026. A primeira versão deste README listava 3 níveis e
    omitia a **Mobilização**.
  - ⚠️ **O plano nunca declara a unidade dos limiares 10, 30 e 50.** Ler como "por 100 mil habitantes, por semana"
    é a convenção nacional, e é **inferência**. A conversão em casos por semana depende dela.
  - **Limite Superior Endêmico:** média móvel da incidência de prováveis no RS + 2 desvios-padrão.
  - **Limite de Alerta:** 45% abaixo do Limite Superior Endêmico.
  - PDF local: `Artigos de referencia/2026_Plano_Municipal_de_Contingencia_Arboviroses.docx_0.pdf`.
- **Os 100 casos do projeto ficam abaixo até do teto de Normalidade do plano**, 140.
- **O InfoDengue e o Estado usam limiares móveis**, recalculados com a história recente, sem número fixo:
  - InfoDengue, medido nos nossos dados: o corte pré-epidêmico subiu de 6 casos por semana, até 2021, para 94,
    em 2025;
  - Estado: limite superior endêmico = média móvel + 2 desvios-padrão.

## O que mais o plano traz

Resumo com página e citação em [plano_municipal_2026_resumo.md](plano_municipal_2026_resumo.md). Os pontos que
importam ao projeto:

- **Testagem encolhe quando a epidemia cresce:**
  - em Normalidade e Mobilização, testam viajantes, pessoas com comorbidades, gestantes, crianças menores de 5
    anos e idosos acima de 60, além dos grupos B e C;
  - em Alerta e Epidemia, só viajantes, gestantes e idosos acima de 60.
  - **Inferência:** isso ajuda a explicar a queda da taxa de confirmação em 2024-2025.
- **NS1 negativo não descarta dengue,** e o plano não diz para onde o caso vai. A palavra "inconclusivo" não
  aparece no documento.
- **Índice oficial do mosquito, o IMFA,** fêmeas por armadilha vistoriada: Satisfatório < 0,15 · Moderado 0,15 a
  0,30 · Alerta 0,30 a 0,6 · **Crítico > 0,6**. Ele dispara o fumacê em volta dos casos.
  - ⏳ **Conferir** se a coluna `aedes_aegypti_por_armadilha` do projeto é o IMFA. Se for, o mosquito ficou em
    nível Crítico por meses em 2026, **sem epidemia**.
- **Sorotipos:** DENV-1 predominante; DENV-2 desde 2023; 2 casos importados de DENV-3 em 2025. O plano é de
  dez/2025 e **não fala de 2026**.
- **A MosquiTRAP identifica sorotipo nos mosquitos capturados.** É uma possível fonte de vigilância do vírus no
  mosquito.
- **Confirmados do plano**, provavelmente por residência: 2022 5.144 · 2023 6.461 · 2024 17.686 · 2025 21.329,
  parcial até 20/11/2025.
