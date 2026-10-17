"""Confere os dois MANIFESTOs do gabarito (sha256 + bytes) e se ha arquivos nao listados."""
import csv, hashlib, os
GD = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto/projeto_final/testes/referencia_antiga"
listados = set()
for m in ("MANIFESTO.csv", "MANIFESTO_E6_E7.csv"):
    rows = list(csv.DictReader(open(f"{GD}/{m}", newline="")))
    col = "arquivo" if "arquivo" in rows[0] else list(rows[0])[0]
    ruins = []
    for r in rows:
        p = f"{GD}/{r[col]}"
        listados.add(r[col])
        if not os.path.isfile(p) or os.path.getsize(p) != int(r["bytes"]) or hashlib.sha256(open(p, "rb").read()).hexdigest() != r["sha256"]:
            ruins.append(r[col])
    print(m, "linhas", len(rows), "divergentes", ruins)
extras = sorted(f for f in os.listdir(GD) if f not in listados and not f.startswith("MANIFESTO"))
print("nao listados:", extras)
