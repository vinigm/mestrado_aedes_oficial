"""Recontagem independente (certificacao) das fichas DENGBR de Porto Alegre. Nao importa aedes/ nem experimentos/.

Diferencas deliberadas em relacao ao contador: ano vem de DT_SIN_PRI por fatiamento de texto (nao to_datetime),
codigos normalizados com to_numeric, ID_MUNICIP casado de 3 formas, tambem conta por SEM_PRI e por DT_NOTIFIC.
Grava so contagens agregadas em resultados/notificacoes/certificacao/.
Rodar: PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B resultados/notificacoes/certificacao/recontar_independente.py
"""
import zipfile, pathlib, collections, sys
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parents[3]
ZIPS = RAIZ.parent / "modelagem_aedes" / "dados" / "entradas" / "bases_governo"
SAIDA = pathlib.Path(__file__).resolve().parent
NOMES = [f"DENGBR{a}.csv.zip" for a in range(18, 27)] + ["DENGBR26_atualizado_set26.csv.zip"]
COLS = ["ID_MUNICIP", "CLASSI_FIN", "DT_SIN_PRI", "SEM_PRI", "DT_NOTIFIC", "DT_ENCERRA"]

por_arq_cod = collections.Counter()      # (arq, codigo)
por_arq_ano_cod = collections.Counter()  # (arq, ano_sintoma, codigo)
por_arq_semana_conf = collections.Counter()  # (arq, SEM_PRI) so confirmadas 10/11/12
por_arq_anonot = collections.Counter()   # (arq, ano notificacao)
extra = collections.Counter()            # diagnosticos
maior_enc = {}
variantes_id = collections.Counter()

def cod_norm(s):
    n = pd.to_numeric(s, errors="coerce")
    out = n.astype("Int64").astype(str)
    return out.where(n.notna(), "vazio")

for nome in NOMES:
    with zipfile.ZipFile(ZIPS / nome) as z:
        membro = z.namelist()[0]
        with z.open(membro) as f:
            for ch in pd.read_csv(f, usecols=COLS, dtype=str, chunksize=250_000):
                idm = ch["ID_MUNICIP"].fillna("").str.strip()
                # variantes de codigo que comecam com 431490 (ex.: 7 digitos 4314902)
                v = idm[idm.str.startswith("431490")]
                for k, c in v.value_counts().items():
                    variantes_id[(nome, k)] += int(c)
                sel = ch[pd.to_numeric(idm, errors="coerce") == 431490]
                if sel.empty:
                    continue
                cod = cod_norm(sel["CLASSI_FIN"])
                ano = sel["DT_SIN_PRI"].fillna("").str.strip().str[:4]
                ano = ano.where(ano.str.fullmatch(r"\d{4}"), "sem_data")
                sem = sel["SEM_PRI"].fillna("").str.strip()
                anot = sel["DT_NOTIFIC"].fillna("").str.strip().str[:4]
                enc = pd.to_datetime(sel["DT_ENCERRA"], errors="coerce")
                if enc.notna().any():
                    m = enc.max()
                    maior_enc[nome] = max(maior_enc.get(nome, m), m)
                for c, n in cod.value_counts().items():
                    por_arq_cod[(nome, c)] += int(n)
                for (a, c), n in pd.DataFrame({"a": ano, "c": cod}).value_counts().items():
                    por_arq_ano_cod[(nome, a, c)] += int(n)
                conf = cod.isin(["10", "11", "12"])
                for s, n in sem[conf].value_counts().items():
                    por_arq_semana_conf[(nome, s)] += int(n)
                for a, n in anot.value_counts().items():
                    por_arq_anonot[(nome, a)] += int(n)
                # SEM_PRI vs ano da DT_SIN_PRI (diagnostico de fronteira)
                dif = (sem.str[:4] != ano)
                extra[(nome, "sem_pri_ano_diferente_de_dt_sin_pri")] += int(dif.sum())
    print("ok", nome, flush=True)

def sit(c):
    return {"10": "conf", "11": "conf", "12": "conf", "8": "incl", "vazio": "aberto"}.get(c, "outros")

# por arquivo
linhas = []
for nome in NOMES:
    cont = collections.Counter()
    codigos = {}
    for (a, c), n in por_arq_cod.items():
        if a == nome:
            cont[sit(c)] += n
            codigos[c] = n
    linhas.append(dict(arquivo=nome, total=sum(cont.values()), conf=cont["conf"], incl=cont["incl"],
                       aberto=cont["aberto"], outros=cont["outros"],
                       codigos=";".join(f"{k}={v}" for k, v in sorted(codigos.items())),
                       maior_dt_encerra=str(maior_enc.get(nome, ""))[:10]))
pd.DataFrame(linhas).to_csv(SAIDA / "recontagem_por_arquivo.csv", index=False)

# por ano de sintomas (10 arquivos, DENGBR26 jun fora; set dentro)
cont_ano = collections.defaultdict(collections.Counter)
cont_ano_jun = collections.defaultdict(collections.Counter)
for (a, ano, c), n in por_arq_ano_cod.items():
    if a != "DENGBR26.csv.zip":
        cont_ano[ano][sit(c)] += n
    if a != "DENGBR26_atualizado_set26.csv.zip":
        cont_ano_jun[ano][sit(c)] += n
def tab(d):
    return pd.DataFrame([dict(ano=a, conf=c["conf"], incl=c["incl"], aberto=c["aberto"], outros=c["outros"],
                              total=sum(c.values())) for a, c in sorted(d.items())])
tab(cont_ano).to_csv(SAIDA / "recontagem_por_ano_set.csv", index=False)
tab(cont_ano_jun).to_csv(SAIDA / "recontagem_por_ano_jun.csv", index=False)

# semanas confirmadas: versao jun e versao set (todas as outras iguais)
for rot, excluir in (("jun", "DENGBR26_atualizado_set26.csv.zip"), ("set", "DENGBR26.csv.zip")):
    s = collections.Counter()
    for (a, sem), n in por_arq_semana_conf.items():
        if a != excluir:
            s[sem] += n
    pd.Series(s, name="confirmadas").rename_axis("SEM_PRI").sort_index().to_csv(SAIDA / f"recontagem_semanas_confirmadas_{rot}.csv")

pd.DataFrame([dict(arquivo=a, ano_notificacao=k, fichas=n) for (a, k), n in sorted(por_arq_anonot.items())]).to_csv(
    SAIDA / "recontagem_por_ano_de_notificacao.csv", index=False)
print("variantes ID_MUNICIP iniciadas em 431490:", dict(variantes_id))
print("SEM_PRI-ano != DT_SIN_PRI-ano:", {k[0]: v for k, v in extra.items()})
print(pd.DataFrame(linhas).to_string())
print(tab(cont_ano).to_string())
