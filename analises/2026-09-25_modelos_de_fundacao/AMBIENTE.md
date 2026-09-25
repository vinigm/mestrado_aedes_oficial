# Ambiente dos modelos de fundação

> Montado em **25/09/2026**, com autorização do Vinicius para os downloads. Vive **fora** do Google Drive e
> fora do repositório, para não sincronizar ~3,4 GB. Este arquivo é o que permite remontar tudo do zero.

---

## Por que um ambiente separado

- O pipeline do projeto roda no **Python 3.14** do sistema. PyTorch e Chronos entrariam nele com dezenas de
  dependências e poderiam mudar versões que o pipeline usa.
- Um ambiente isolado garante que **nada do pipeline muda**. O script desta pasta é o único que usa este
  ambiente.

---

## Onde está cada coisa

| O quê | Caminho | Tamanho |
|---|---|---|
| Ambiente Python 3.12.13 | `~/.venvs/aedes_modelos_fundacao/` | 977 MB |
| Pesos do Chronos-2 | `~/.cache/huggingface/hub/models--amazon--chronos-2/` | 912 MB |
| Pesos do Chronos-Bolt base | `~/.cache/huggingface/hub/models--amazon--chronos-bolt-base/` | 1,5 GB |
| Versões exatas de cada pacote | [`requisitos_travados.txt`](requisitos_travados.txt) | 54 pacotes |

### Versões que importam

| Pacote | Versão |
|---|---|
| `chronos-forecasting` | 2.3.2 |
| `torch` | 2.14.0 |
| `transformers` | 5.17.0 |
| `numpy` | 2.5.3 |
| `pandas` | 3.0.6 |
| `scipy` | 1.18.1 |

### Revisão dos pesos no HuggingFace

- `amazon/chronos-2` — revisão `29ec3766d36d6f73f0696f85560a422f50e8498c`
- `amazon/chronos-bolt-base` — revisão `5d9f166d69f47aef3401367a7b842e78fe97b121`

---

## Como remontar

```bash
uv venv ~/.venvs/aedes_modelos_fundacao --python 3.12
```

```bash
uv pip install --python ~/.venvs/aedes_modelos_fundacao/bin/python -r requisitos_travados.txt
```

Os pesos baixam sozinhos na primeira chamada de `from_pretrained`. Para fixar a mesma revisão, passar
`revision=` com o hash acima.

---

## Conferências feitas na instalação

- **Instalação:** 8 s com `uv`.
- **Carga dos modelos:** 18 s o Chronos-2, 27 s o Bolt, na primeira vez, incluindo o download.
- **Uma previsão de 12 semanas:** ~0,5 s em CPU.
- **Determinismo:** a mesma série prevista duas vezes deu resultado **idêntico** nos dois modelos.
- **Quantis:** o Chronos-2 prevê 21 quantis nativos, **incluindo o 0,85**. O Bolt prevê 0,1 a 0,9; o 0,85
  sai por interpolação da própria biblioteca.
- **Covariáveis:** o Chronos-2 aceita `past_covariates`, séries conhecidas só até a origem. O Bolt não aceita.

---

## Para apagar

O ambiente e os pesos não fazem parte do projeto. Apagar as três pastas da tabela acima devolve o disco.
Os resultados desta análise ficam nesta pasta e não dependem deles para ser lidos.
