# NOVO_HTML — o site reconstruído do zero

Criado em **22/09/2026**, para a banca do seminário de andamento.

> ⚠️ **O site antigo não é tocado.** `pagina_web/` e `docs/` seguem funcionando e
> publicados. Este é um site paralelo, gerado em `NOVO_HTML/saida/`. A migração
> para `docs/` é uma decisão posterior, quando todas as páginas estiverem prontas.

---

## Por que existe

O site antigo foi feito para o autor **acompanhar** a própria pesquisa. O novo é
feito para um **professor de banca que nunca viu o projeto** abrir o link e
entender em poucos minutos.

O que muda, concretamente:

- **Dois níveis de navegação** (menu primário escuro + menu secundário com as
  seções da página), no lugar de uma árvore de 15 itens com nome interno.
- **Zero jargão de projeto** no texto visível — sem "cenário principal 2",
  sem `cidade_surto_notificados`, sem `h=12`.
- **Acentuação completa**. O site antigo foi escrito sem acento.
- **Nenhum número solto.** Toda afirmação numérica sai de
  [`numeros_do_projeto.py`](numeros_do_projeto.py), que copia o
  [`ESTADO.md`](../ESTADO.md). Se divergirem, o `ESTADO.md` vence.
- **Fato e hipótese sempre rotulados**, com cor diferente.

---

## Como gerar

```bash
cd NOVO_HTML && python3 gerar.py
```

A saída vai para `NOVO_HTML/saida/`. Abra `saida/index.html` no navegador.

---

## Os arquivos

| Arquivo | O que faz |
|---|---|
| `gerar.py` | o comando: monta todas as páginas e copia as figuras |
| `tema.py` | a folha de estilo inteira e o JS de navegação |
| `layout.py` | a casca das páginas e os blocos reutilizáveis |
| `navegacao.py` | **o mapa do site** — páginas e seções de cada uma |
| `numeros_do_projeto.py` | **a fonte única dos números**, copiada do `ESTADO.md` |
| `icones.py` | os ícones SVG da navegação |
| `paginas/inicio.py` | a porta de entrada da banca |
| `paginas/dados.py` | as quatro fontes e as limitações |
| `paginas/metodologia.py` | walk-forward, corte pela resposta e dicionário |
| `saida/` | o HTML gerado |

---

## Como acrescentar uma página

1. Declare a página e suas seções em **`navegacao.py`**, com âncora e título.
2. Crie **`paginas/<chave>.py`** expondo exatamente duas funções:
   - `montar_metricas() -> list[layout.Metrica]`
   - `montar_corpo() -> str`
3. Registre o módulo em `MODULOS_POR_PAGINA`, em **`gerar.py`**.
4. Rode `python3 gerar.py`.

Os dois menus absorvem a página nova sozinhos.

---

## Regras que valem para todo texto deste site

- **Número novo entra primeiro em `numeros_do_projeto.py`**, nunca direto na
  frase. Se o número não existe lá, ele não vai para o site.
- **Nada é chamado de significativo** sem sobreviver à correção de múltiplas
  comparações. Hoje sobrevive **um** resultado, e ele é negativo.
- **Observação visual não é resultado medido.** A defasagem entre a curva do
  vetor e a curva dos casos é visível nos gráficos, mas ainda não foi
  quantificada — e o site diz isso com todas as letras.
- **Datas sempre absolutas** (21/09/2026), nunca relativas.

---

## O que ainda falta

- ⏳ Páginas de **Resultados** e **Próximos passos** (o eixo proposto em
  21/09/2026: prever a proliferação do vetor como causa, não o surto).
- ⏳ Página-**roteiro** para o e-mail que o orientador vai mandar a Mariana e
  Rodrigo Mansilha.
- ⏳ Decidir a **migração** para `docs/` e o destino das páginas antigas que
  ainda exibem números anteriores à correção de 13/09/2026.
