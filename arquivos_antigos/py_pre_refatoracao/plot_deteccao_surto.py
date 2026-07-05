"""Figura do Modelo 6 (deteccao de surto).
Painel A = viabilidade (InfoDengue 2010-26): F1 do LGBM vs baselines por horizonte.
Painel B = lift do vetor (tabela_final): F1 sazonal / so-clima / clima+vetor por horizonte.
Le: Bases de dados/tabela_modelagem/deteccao_surto_resultados.csv
Salva: deteccao_surto.png (ao lado deste script)."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def achar_raiz(marcador="Raspagem"):
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / marcador).is_dir():
            return p
    raise FileNotFoundError("raiz nao encontrada")

RAIZ = achar_raiz()
res = pd.read_csv(RAIZ / "Bases de dados" / "tabela_modelagem" / "deteccao_surto_resultados.csv")
PCTL = 90

fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))

a = res[(res.exp == "A_infodengue") & (res.pctl == PCTL)]
ax = axes[0]
for modelo, cor in [("clima+AR_LGBM", "#1f77b4"), ("persistencia", "#7f7f7f"), ("sazonal", "#ff7f0e")]:
    s = a[a.modelo == modelo].sort_values("h")
    ax.plot(s["h"], s["f1"], marker="o", label=modelo, color=cor)
ax.set_title(f"A) Viabilidade — InfoDengue 2010-26 (surto = P{PCTL})\nF1 de deteccao por horizonte")
ax.set_xlabel("horizonte (semanas a frente)"); ax.set_ylabel("F1"); ax.set_xticks([4, 8, 12])
ax.set_ylim(0, 1); ax.grid(alpha=.3); ax.legend(fontsize=8)
for x, lab in [(4, "1 mes"), (8, "2 meses"), (12, "3 meses")]:
    ax.annotate(lab, (x, .02), ha="center", fontsize=7, color="gray")

b = res[(res.exp == "B_tabela_final") & (res.pctl == PCTL)]
ax = axes[1]
for modelo, cor in [("sazonal", "#ff7f0e"), ("so-clima", "#2ca02c"), ("clima+vetor", "#d62728")]:
    s = b[b.modelo == modelo].sort_values("h")
    ax.plot(s["h"], s["f1"], marker="o", label=modelo, color=cor)
ax.set_title(f"B) Lift do vetor na deteccao — tabela_final (surto = P{PCTL})\nF1: so-clima vs clima+VETOR")
ax.set_xlabel("horizonte (semanas a frente)"); ax.set_ylabel("F1"); ax.set_xticks([4, 8, 12])
ax.set_ylim(0, 1); ax.grid(alpha=.3); ax.legend(fontsize=8)

plt.tight_layout()
OUT = Path(__file__).parent / "deteccao_surto.png"
plt.savefig(OUT, dpi=130, bbox_inches="tight")
print("figura salva:", OUT)
