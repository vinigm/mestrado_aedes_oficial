"""Recalculo independente de r = confirmados POA por notificacao / por residencia (sintomas 2018-2023)."""
import zipfile, json, sys
import pandas as pd

BASE = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto/"
ZIPS = BASE + "modelagem_aedes/dados/entradas/bases_governo/DENGBR{:02d}.csv.zip"
COLS = ["ID_MUNICIP", "ID_MN_RESI", "CLASSI_FIN", "DT_SIN_PRI"]
res = {}
for aa in range(18, 25):
    nome = ZIPS.format(aa)
    cont = {}  # (ano_sintoma) -> [notif, resid, ambos]
    ficha_total = 0
    with zipfile.ZipFile(nome) as z:
        assert len(z.namelist()) == 1
        with z.open(z.namelist()[0]) as f:
            for ch in pd.read_csv(f, usecols=COLS, dtype=str, chunksize=400_000):
                ficha_total += len(ch)
                conf = ch["CLASSI_FIN"].str.strip().isin(["10", "11", "12"])
                ano = ch["DT_SIN_PRI"].str.strip().str[:4]
                n = conf & (ch["ID_MUNICIP"].str.strip() == "431490")
                r = conf & (ch["ID_MN_RESI"].str.strip() == "431490")
                for a in sorted(set(ano[n | r].dropna())):
                    m = ano == a
                    c = cont.setdefault(a, [0, 0, 0])
                    c[0] += int((n & m).sum()); c[1] += int((r & m).sum()); c[2] += int((n & r & m).sum())
    res[2000 + aa] = {"linhas": ficha_total, "por_ano_sintoma": cont}
    print(aa, ficha_total, {k: v for k, v in sorted(cont.items())}, flush=True)
json.dump(res, open("razao_por_arquivo_e_ano.json", "w"), indent=1)

def soma(arqs):
    n = r = 0
    for a in arqs:
        for ano, (cn, cr, _) in res[a]["por_ano_sintoma"].items():
            if ano in {"2018", "2019", "2020", "2021", "2022", "2023"}:
                n += cn; r += cr
    return n, r
for rot, arqs in [("18-24", range(2018, 2025)), ("18-23", range(2018, 2024))]:
    n, r = soma(arqs)
    print(rot, "num", n, "den", r, "r", n / r, "L", 421 * n / r)
