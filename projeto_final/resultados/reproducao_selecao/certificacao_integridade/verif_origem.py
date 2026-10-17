"""Cada copia do gabarito E6/E7 tem o mesmo sha256 do original no manifesto ANTES do codigo antigo?"""
import csv
R = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto"
ant = {r["caminho"]: r["sha256"] for r in csv.DictReader(open(R + "/analises/2026-10-12_referencia_para_o_pacote/manifesto_codigo_antigo_ANTES.csv", newline=""))}
for r in csv.DictReader(open(R + "/projeto_final/testes/referencia_antiga/MANIFESTO_E6_E7.csv", newline="")):
    print(r["arquivo"], "ok" if ant.get(r["origem"]) == r["sha256"] else f"DIVERGE/ausente ({r['origem']})")
