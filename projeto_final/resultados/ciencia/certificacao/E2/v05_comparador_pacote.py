"""COMPARADOR (objeto sob teste): importa aedes.bracos SO para extrair as matrizes e as colunas que o
pacote gera e compara com a receita independente (minha_receita). Nao e parte da receita independente.
Item 1 (vazamento de bloco) e item 2 (linhas e valores das matrizes)."""
import json
import numpy as np, pandas as pd
import minha_receita as R
import sys
sys.path.insert(0, str(R.RAIZ))
from aedes.bracos import montar_matriz_do_braco, nomes_das_variaveis_do_braco, NOMES_DOS_BRACOS, BRACOS
from aedes.configuracao import CONFIGURACAO_DADOS, CONFIGURACAO_VARIAVEIS
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes

out = {}
t_meu = R.carregar_tabela_cortada()
t_pac = aplicar_corte_de_maturidade(montar_tabela_a_partir_dos_bytes(R.CAMINHO_TABELA.read_bytes(), CONFIGURACAO_DADOS), CONFIGURACAO_DADOS)
out["tabela_cortada_meu_igual_pacote"] = bool(t_meu.equals(t_pac)) if list(t_meu.columns) == list(t_pac.columns) else "colunas diferem"
out["casos_cortados_iguais"] = bool(np.array_equal(t_meu[R.COL_CASOS].values, t_pac[R.COL_CASOS].values, equal_nan=True))
# item 1: blocos por braco
leaks = []
cols_por_braco = {}
for b in NOMES_DOS_BRACOS:
    cp = nomes_das_variaveis_do_braco(b, CONFIGURACAO_VARIAVEIS)
    cm = R.colunas_do_braco(b)
    cols_por_braco[b] = cp
    if cp != cm:
        leaks.append((b, "colunas diferem da definicao pre-declarada", sorted(set(cp) ^ set(cm))))
    if not all(k in cp for k in R.BLOCO_K):
        leaks.append((b, "falta calendario"))
    tem_casos = [c for c in cp if c.startswith("casos")]
    tem_vetor = [c for c in cp if c.startswith("aedes_") or c == "vetor_mm4"]
    tem_clima = [c for c in cp if c in R.BLOCO_M]
    esperado = dict(completo=(1, 1, 1), sem_casos=(0, 1, 1), sem_clima=(1, 0, 1), sem_vetor=(1, 1, 0), so_casos=(1, 0, 0),
                    so_clima=(0, 1, 0), so_vetor=(0, 0, 1), so_calendario=(0, 0, 0))[b]
    obs = (int(bool(tem_casos)), int(bool(tem_clima)), int(bool(tem_vetor)))
    if obs != esperado or (tem_casos and len(tem_casos) != 6) or (tem_clima and len(tem_clima) != 6) or (tem_vetor and len(tem_vetor) != 6):
        leaks.append((b, "presenca/contagem de bloco errada", obs, len(tem_casos), len(tem_clima), len(tem_vetor)))
out["colunas_por_braco"] = {b: len(c) for b, c in cols_por_braco.items()}
out["vazamentos_de_bloco"] = leaks
# item 2: matrizes (todos os 8 bracos x 12 h) pacote x minha receita, bit a bit
dif = []
for b in NOMES_DOS_BRACOS:
    for h in range(1, 13):
        mp = montar_matriz_do_braco(t_pac, h, b, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
        mm = R.matriz_do_braco(t_meu, h, b)
        if list(mp.columns) != list(mm.columns) or len(mp) != len(mm):
            dif.append((b, h, "colunas/linhas", list(mp.columns), list(mm.columns), len(mp), len(mm)))
            continue
        for c in mp.columns:
            a1, a2 = mp[c].values, mm[c].values
            if a1.dtype.kind == "M":
                iguais = bool((a1 == a2).all())
            else:
                iguais = bool(np.array_equal(a1.view(np.int64) if a1.dtype == np.float64 else a1, a2.view(np.int64) if a2.dtype == np.float64 else a2))
            if not iguais:
                dif.append((b, h, c))
out["matrizes_diferentes_bit_a_bit"] = dif
out["n_matrizes_comparadas"] = len(NOMES_DOS_BRACOS) * 12
json.dump(out, open("v05_resultado.json", "w"), indent=1, default=str)
for k, v in out.items():
    print(k, "=", v)
