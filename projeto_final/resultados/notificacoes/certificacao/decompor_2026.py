"""Decompoe fichas com DT_SIN_PRI em 2026 e em aberto, por arquivo (so contagens)."""
import zipfile, pathlib, collections, pandas as pd
Z = pathlib.Path(__file__).resolve().parents[3].parent / "modelagem_aedes/dados/entradas/bases_governo"
for nome in ["DENGBR24.csv.zip","DENGBR25.csv.zip","DENGBR26.csv.zip","DENGBR26_atualizado_set26.csv.zip"]:
    c = collections.Counter()
    with zipfile.ZipFile(Z/nome) as z, z.open(z.namelist()[0]) as f:
        for ch in pd.read_csv(f, usecols=["ID_MUNICIP","CLASSI_FIN","DT_SIN_PRI"], dtype=str, chunksize=250000):
            s = ch[ch.ID_MUNICIP.str.strip()=="431490"]
            ano = s.DT_SIN_PRI.str[:4]
            cod = s.CLASSI_FIN.fillna("vazio")
            for (a,k),n in pd.DataFrame({"a":ano,"k":cod}).value_counts().items():
                if a in ("2025","2026"): c[(a,k)] += int(n)
    print(nome, dict(sorted(c.items())))
