"""Certificacao de integridade (independente): recalcula manifesto sha256 do codigo antigo. Escopo lido do script do construtor
(pastas, ignorados), codigo proprio. Nao abre arquivos_secretaria_saude_poa nem o CSV da Prefeitura."""
import os, csv, hashlib, sys
RAIZ = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto"
REF = RAIZ + "/analises/2026-10-12_referencia_para_o_pacote"
SKIP_DIRS = {"__pycache__", ".venv", ".pytest_cache", ".git"}
SKIP_PATHS = {"modelagem_aedes/dados/entradas/arquivos_secretaria_saude_poa", "analises/2026-10-12_referencia_para_o_pacote"}
SKIP_FILES = {"analises/2026-09-25_novas_fontes_oficiais/dados/sinan_arboviroses_prefeitura_poa_2010_2022.csv"}
now, pyc = {}, set()
for top in ["modelagem_aedes", "analises", "NOVO_HTML", "Raspagem", "pagina_web"]:
    for dp, dns, fns in os.walk(os.path.join(RAIZ, top)):
        rd = os.path.relpath(dp, RAIZ)
        keep = []
        for d in dns:
            rel = rd + "/" + d
            if d == "__pycache__": pyc.add(rel)
            if d in SKIP_DIRS or rel in SKIP_PATHS: continue
            keep.append(d)
        dns[:] = keep
        for f in fns:
            rel = rd + "/" + f
            if rel in SKIP_FILES: continue
            p = os.path.join(RAIZ, rel)
            if os.path.islink(p) or not os.path.isfile(p): continue
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for ch in iter(lambda: fh.read(1 << 20), b""): h.update(ch)
            now[rel] = (os.path.getsize(p), h.hexdigest())
ant = {}
with open(REF + "/manifesto_codigo_antigo_ANTES.csv", newline="") as fh:
    for r in csv.DictReader(fh): ant[r["caminho"]] = (int(r["bytes"]), r["sha256"])
print("ANTES", len(ant), "AGORA", len(now))
print("removidos:", sorted(set(ant) - set(now)))
print("novos:", sorted(set(now) - set(ant)))
print("alterados:", sorted(k for k in set(ant) & set(now) if ant[k] != now[k]))
ex = set(open(REF + "/pycache_existentes_ANTES.txt").read().split())
print("pycache agora", len(pyc), "antes", len(ex), "novos:", sorted(pyc - ex), "sumidos:", sorted(ex - pyc))
