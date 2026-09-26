# Atualização dos casos confirmados de 2026 (DENGBR26 de setembro)

> 🚫 **REVERTIDA em 26/09/2026, por decisão do Vinicius:** 2026 não entra na avaliação. `tabela_final.csv` e
> `casos_confirmados_poa.csv` voltaram, por cópia dos backups, à versão anterior, idêntica ao commit `544263a`. A
> versão com 2026 está guardada em `versao_com_2026_nao_usada/`. A correção de código continua: um arquivo por ano,
> com teste. ⚠️ Por isso **não rodar `consolidar_sinan` nem `montar.py`**, que puxariam o DENGBR26 novo.
> Certificação da reversão: [`CERTIFICACAO_REVERSAO.md`](CERTIFICACAO_REVERSAO.md).

**Pergunta:** integrar o DENGBR26_atualizado_set26.csv.zip (baixado em 13/09/2026, nunca
integrado) sem contar em dobro e sem mudar 2018-2025.

**Método:** corrigir `preparo/consolidar_sinan.py` para escolher **um arquivo por ano**
(nunca concatenar dois DENGBR do mesmo ano) e rodar só `consolidar_sinan()` + `montar.py`
— sem `preparar_dados.py`, sem baixar nada, sem tocar nos arquivos DENGBR existentes.

**Números-âncora (medidos em 13/09/2026, confirmados aqui):** confirmados de POA em 2026
**12 → 19**; alcance da série **SE 202617 → SE 202628**.

**Decisão:** mudança fica só no código (`preparo/consolidar_sinan.py`) e nos dados
derivados (`casos_confirmados_poa.csv`, `tabela_final.csv`); nenhum arquivo bruto do SINAN
foi apagado, movido ou reprocessado.

**Conclusão:** confirmado — 2018-2025 não mudou em nenhuma coluna; só `casos_confirmados`
de 14 semanas de 2026 (11/01 a 12/07) mudou na `tabela_final`. Detalhe completo, tabela
ano a ano e teste diferencial: [`comparacao.md`](comparacao.md).

**Backups pré-regeneração:** `backup_antes/tabela_final_ANTES.csv` e
`backup_antes/casos_confirmados_poa_ANTES.csv`.

**Teste novo:** `modelagem_aedes/tests/test_consolidar_sinan.py` — falha com a lógica
antiga (glob + concat sem selecionar por ano), passa com a corrigida.
