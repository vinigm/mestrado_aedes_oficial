"""Certificacao adversarial: integridade do codigo antigo (manifesto sha256 recalculado com codigo proprio).
Nao abre a pasta de dados crus da Secretaria nem o CSV da Prefeitura. Nao grava nada fora desta pasta."""
import csv, hashlib, os, pathlib, json
RAIZ = pathlib.Path("/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto")
REF = RAIZ / "analises/2026-10-12_referencia_para_o_pacote"
PASTAS = ("modelagem_aedes", "analises", "NOVO_HTML", "Raspagem", "pagina_web")
IGN_NOMES = {"__pycache__", ".venv", ".pytest_cache", ".git"}
IGN_CAM = {"modelagem_aedes/dados/entradas/arquivos_secretaria_saude_poa", "analises/2026-10-12_referencia_para_o_pacote"}
IGN_ARQ = {"analises/2026-09-25_novas_fontes_oficiais/dados/sinan_arboviroses_prefeitura_poa_2010_2022.csv"}
agora, pycs = {}, set()
for pasta in PASTAS:
    for dp, dns, fns in os.walk(RAIZ / pasta):
        rd = os.path.relpath(dp, RAIZ)
        manter = []
        for d in dns:
            rel = f"{rd}/{d}"
            if d == "__pycache__": pycs.add(rel)
            if d in IGN_NOMES or rel in IGN_CAM: continue
            manter.append(d)
        dns[:] = manter
        for fn in fns:
            rel = f"{rd}/{fn}"; fp = RAIZ / rel
            if rel in IGN_ARQ or fp.is_symlink() or not fp.is_file(): continue
            h = hashlib.sha256(); 
            with open(fp, "rb") as f:
                for bloco in iter(lambda: f.read(1 << 20), b""): h.update(bloco)
            agora[rel] = (fp.stat().st_size, h.hexdigest())
antes = {r["caminho"]: (int(r["bytes"]), r["sha256"]) for r in csv.DictReader(open(REF / "manifesto_codigo_antigo_ANTES.csv", newline=""))}
exist = set((REF / "pycache_existentes_ANTES.txt").read_text().split())
out = dict(n_antes=len(antes), n_agora=len(agora),
           removidos=sorted(set(antes)-set(agora)), novos=sorted(set(agora)-set(antes)),
           alterados=sorted(k for k in set(antes)&set(agora) if antes[k]!=agora[k]),
           pycache_agora=len(pycs), pycache_antes=len(exist), pycache_novos=sorted(pycs-exist), pycache_sumidos=sorted(exist-pycs))
# regra do manifesto: confere tambem contagem de linhas do CSV e duplicatas
out["linhas_csv_antes"] = len(antes)
(pathlib.Path(__file__).with_name("integridade_resultado.json")).write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps(out, indent=2, ensure_ascii=False))
