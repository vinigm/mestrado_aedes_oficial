# pagina_web

Painel do projeto em HTML — uma visão mais amigável que o MLflow, feita para
**apresentar** (ex.: para o orientador) e para **acompanhar** os modelos que vão
sendo treinados.

É uma pasta **independente**: lê a pasta `mlruns/` do `modelagem_aedes` direto
(sem depender do MLflow instalado) e escreve páginas HTML soltas, que você abre
no navegador ou manda por email. Nada de servidor.

## Como usar

```bash
cd pagina_web
python3 gerar.py
```

Depois abra **`site/index.html`** no navegador.

Treinou um modelo novo? Rode o experimento e gere o painel de novo:

```bash
cd ../modelagem_aedes
python3 main.py --experimento cidade_regressao_rf   # (versiona no MLflow)
cd ../pagina_web
python3 gerar.py                                     # atualiza o painel
```

## As páginas

- **Início** — visão geral, indicadores e atalhos.
- **Objetivo** — a pergunta central da pesquisa e como as previsões são testadas.
- **Dados** — as fontes usadas (mosquito, clima, casos, El Niño) e o que sai da junção.
- **Resultados** — o painel dos experimentos: um cartão por cenário, com a tabela
  comparando os modelos, um gráfico por horizonte e os detalhes de cada modelo.

Essas quatro são fixas. Além delas, você pode ir **criando páginas novas** sozinho.

## Adicionar uma página nova (sem mexer em código)

O site do projeto é feito pra crescer. Para criar uma página:

1. Crie um arquivo `.md` na pasta **`paginas/`** (ex.: `paginas/20_cronograma.md`).
2. Rode `python3 gerar.py`.
3. Pronto — a página aparece **sozinha no menu** do topo.

O arquivo é escrito em **Markdown** (texto com marquinhas simples). Nas primeiras
linhas você pode pôr, de forma opcional:

```
titulo: Cronograma          # o nome que aparece no menu
ordem: 20                   # posição no menu (menor vem antes)

## Um subtítulo
Um parágrafo com **negrito**, *itálico*, `código` e um [link](resultados.html).

- item de lista
- outro item

> uma citação em destaque
```

Marquinhas que funcionam: `##`/`###` (subtítulos), `- ` (lista), `1. ` (lista
numerada), `**negrito**`, `*itálico*`, `` `código` ``, `[texto](link)`,
`![descrição](imagem.png)`, `>` (citação) e `---` (linha divisória).

> Dica: comece os subtítulos com `##` (não `#`), porque o título grande da página
> já vem do `titulo:`. Há um exemplo pronto em `paginas/10_metodo.md` — pode
> editar ou apagar.

## Os arquivos

| Arquivo | O que faz |
|---|---|
| `gerar.py` | o comando: lê o MLflow, monta as páginas e grava em `site/` |
| `conteudo.py` | os **textos** (objetivo, fontes de dados, nome bonito dos cenários) — edite aqui |
| `paginas/` | suas **páginas novas** em Markdown (uma por arquivo `.md`) |
| `leitor_mlflow.py` | lê a pasta `mlruns/` (Python puro, sem depender do MLflow) |
| `markdown_simples.py` | traduz o Markdown das páginas extras em HTML |
| `site/` | a **saída** — as páginas HTML prontas (é o que você abre) |

Para mudar um texto, edite `conteudo.py` e rode `python gerar.py` de novo.
