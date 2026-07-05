"""Figura headline: sem ENSO + alvo com corte de maturidade -> o vetor carrega o horizonte longo."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def achar_raiz(marcador="Raspagem"):
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / marcador).is_dir():
            return p
    raise FileNotFoundError("raiz nao encontrada")


TAB = achar_raiz() / "Bases de dados" / "tabela_modelagem"
df = pd.read_csv(TAB / "clima_enxuto_maturidade_resultados.csv")
r2 = df.pivot(index="h", columns="conjunto", values="R2")
mae = df.pivot(index="h", columns="conjunto", values="MAE")
lift = ((mae["M0_clima6"] - mae["M1_clima6_vetor"]) / mae["M0_clima6"] * 100)

fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
ax[0].plot(r2.index, r2["M0_clima6"], "o-", color="tab:blue", label="M0: só clima (sem ENSO)")
ax[0].plot(r2.index, r2["M1_clima6_vetor"], "o-", color="tab:green", label="M1: clima + vetor")
ax[0].axhline(0, color="k", lw=0.8, ls="--")
ax[0].axvspan(5.5, 12.5, color="tab:green", alpha=0.08)
ax[0].annotate("1,5–3 meses:\nclima sozinho ~0,08\nvetor segura ~0,35", (10, 0.62),
               fontsize=9, color="dimgray", ha="center")
ax[0].set_title("R² × horizonte (sem ENSO, alvo maduro)")
ax[0].set_xlabel("semanas à frente"); ax[0].set_ylabel("R²")
ax[0].legend(loc="upper right", fontsize=9); ax[0].grid(alpha=0.3)

cores = ["tab:green" if v > 0 else "tab:red" for v in lift]
ax[1].bar(lift.index, lift, color=cores)
ax[1].axhline(0, color="k", lw=0.8)
ax[1].axvspan(5.5, 12.5, color="tab:green", alpha=0.08)
ax[1].set_title("Lift marginal do vetor (% redução do MAE)")
ax[1].set_xlabel("semanas à frente"); ax[1].set_ylabel("lift %"); ax[1].grid(alpha=0.3)
plt.tight_layout()
out = Path.cwd() / "lift_maturidade.png"
plt.savefig(out, dpi=110, bbox_inches="tight")
print("salvo:", out)
