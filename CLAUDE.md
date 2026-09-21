# Pesquisa de Mestrado — Aedes aegypti / Dengue em Porto Alegre

Índice e invariantes do projeto. Muda raro. **Atualizado em 13/09/2026.**

@PENDENCIAS.md

---

## Os quatro documentos vivos

| Documento | Responde | Muda | Carregado |
|---|---|---|---|
| **CLAUDE.md** (este) | Onde fica o quê, e o que nunca se faz | raro | sempre |
| **[PENDENCIAS.md](PENDENCIAS.md)** | O que está em aberto e quem destrava | a cada entrega | sempre (`@import`) |
| **[ESTADO.md](ESTADO.md)** | O que o sistema É hoje | semanal | sob demanda |
| **[HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md)** | O que já foi perguntado, medido e concluído | a cada teste | sob demanda |

Contexto profundo (PEP, referências, artigos, histórico dos dados): pasta **`../Contexto/`**.

---

## O que é este projeto

Mestrado no PPGC/UFRGS (início set/2025, orientador Prof. Weverton Cordeiro): modelo preditivo usando a
série de captura de mosquitos das armadilhas do MI-Aedes em Porto Alegre.

**Pergunta da tese:** quanto vale a rede de armadilhas para a vigilância de dengue em Porto Alegre?
⏳ O eixo está em revisão desde 13/09/2026 — ver [ESTADO.md](ESTADO.md) §4.

---

## Invariantes (valem sempre, sem exceção)

### Dados

- **`brutos_secretaria/` é datalake: SOMENTE LEITURA.** Contém nome e telefone de morador nos arquivos
  de 2012–2020.
  - ⚠️ **Como a proteção funciona de fato:** a pasta está **DENTRO** do repositório, em
    `modelagem_aedes/dados/entradas/arquivos_secretaria_saude_poa/`. O que impede o vazamento é a
    **linha 55 do `.gitignore`**, que ignora a pasta inteira (0 arquivos rastreados lá).
    **Nunca remover essa linha.** O `../BACKUP_DADOS_VITAIS` guarda uma cópia, não é a proteção.

- **Os dados de captura são insubstituíveis.** O portal MI-Aedes só expõe a semana corrente. Nunca
  `rm`/`mv` destrutivo nesses caminhos — só `cp`.

- **Nada de deletar base antiga.** Marília e raspagem de 2025 são validação cruzada.

- Correções nos dados acontecem no **script gerador**, nunca editando planilha à mão.

### Método

- **Honestidade estatística é inegociável.** Não escrever "significativo" ou "comprovado" sem sobreviver
  a correção de múltiplas comparações. Hoje sobrevive **um** resultado, e ele é negativo —
  ver [ESTADO.md](ESTADO.md) §3.3.

- **Fato ≠ hipótese**, sempre rotulado, em documento e em slide.

- **Toda rodada nova exige pré-declaração escrita ANTES**: hipótese, métrica, critério de decisão e
  família de correção múltipla. Mudança posterior vira **emenda datada**, nunca edição silenciosa.

- **Todo walk-forward corta o treino pela data da RESPOSTA**, nunca pela da pergunta. A regra vive em
  `modelagem_aedes/motor/corte_temporal.py`. Ver [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md) §6.1.

- **Comparação entre modelos é pareada** por `data_alvo`, ou não vale.

- Mudança em dado ou pipeline exige **certificação adversarial** por agente independente que tente
  reprovar, medindo do zero. Teste verde não substitui.

- Análises novas vão para pasta datada (`analises/AAAA-MM-DD_descricao/`) **com README**
  contando pergunta, método, números-âncora e conclusão.

### Execução

- **Rodada longa de CPU (>15–30 min): avisar antes, com estimativa, e esperar o ok do Vinicius.**
  Estimar medindo uma célula, nunca por analogia com outra rodada.
- Processo demorado roda com `nohup` + log + polling. Nunca em foreground.
- Publicar o site após mexer no painel é pré-autorizado (commit restrito a `pagina_web/` + `docs/`).
  ⚠️ **Suspenso desde 13/09/2026:** o painel tem números errados — ver [ESTADO.md](ESTADO.md) §5.
- Código Python segue `~/.claude/PADRAO-CODIGO-PYTHON.md` (leitura obrigatória antes de escrever código).

---

## Mapa rápido

- `modelagem_aedes/` — o pipeline (config, acesso, dominio, motor, avaliacao, preparo, tests).
- `pagina_web/` → gera `docs/` — o painel do GitHub Pages.
- `Raspagem/` — o scraper semanal (manual) e seus arquivos brutos.
- `analises/` — uma pasta datada por teste, cada uma com README e pré-declaração.
- `../Contexto/` — o contexto organizado para IA.
- `../BACKUP_DADOS_VITAIS_captura_mosquitos/` — cópias dos dados insubstituíveis.

✅ **Desde 13/09/2026 os quatro documentos vivos moram DENTRO do repositório**, aqui em `Meu_Projeto/`,
com histórico versionado. Na raiz `Pesquisa/` ficou um `CLAUDE.md` de 6 linhas que só aponta para cá.

⚠️ **A pasta `../Contexto/` continua fora do git**, sem histórico.
