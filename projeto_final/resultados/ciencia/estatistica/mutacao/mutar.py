"""Mutacao em copia: aplica cada mutante numa copia do projeto_final e roda so os testes novos."""
import pathlib
import shutil
import subprocess
import sys

ORIGEM = pathlib.Path("/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto/projeto_final")
COPIA = pathlib.Path(__file__).resolve().parent / "mutante"
TESTES = [
    "testes/test_estatistica.py",
    "testes/test_composto.py",
    "testes/test_alarme.py",
    "testes/test_familias.py",
    "testes/test_experimentos_estatistica.py",
    "testes/test_e2_mapeamento_das_folhas.py",
]

MUTANTES = [
    ("M1 sem fator HLN", "aedes/estatistica.py",
     "estatistica_hln = float(estatistica_dm * np.sqrt(argumento_do_fator))", "estatistica_hln = float(estatistica_dm)"),
    ("M2 lag extra no DM", "aedes/estatistica.py",
     "autocovariancias = calcular_autocovariancias(diferencas, horizonte)", "autocovariancias = calcular_autocovariancias(diferencas, horizonte + 1)"),
    ("M3 Holm sem step-down (Bonferroni)", "aedes/estatistica.py",
     "multiplicador = quantidade_de_testes - posicao", "multiplicador = quantidade_de_testes"),
    ("M4 composto usa a data_alvo da propria semana (futuro)", "aedes/composto.py",
     "datas_alvo.searchsorted(data_de_origem, side=\"right\")", "datas_alvo.searchsorted(data_alvo_da_linha, side=\"right\")"),
    ("M5 empate vai para folha 20", "aedes/composto.py",
     "if mae_folha_20 < mae_folha_5:", "if mae_folha_20 <= mae_folha_5:"),
    ("M6 alarme real >=", "aedes/alarme.py",
     "houve_surto = reais > limiar", "houve_surto = reais >= limiar"),
    ("M6b alarme previsto >=", "aedes/alarme.py",
     "disparou_alarme = previstos > limiar", "disparou_alarme = previstos >= limiar"),
    ("M7 e2 troca as folhas", "experimentos/e2_ablacao.py",
     "MODELOS_POR_FOLHA: dict[int, ConfiguracaoModelo] = {5: FOLHA_5, 20: FOLHA_20}", "MODELOS_POR_FOLHA: dict[int, ConfiguracaoModelo] = {5: FOLHA_20, 20: FOLHA_5}"),
    ("M8 veredito com limiar >=", "aedes/familias.py",
     "passa_no_piso = abs(delta) > limiar_do_piso", "passa_no_piso = abs(delta) >= limiar_do_piso"),
    ("M9 piso do composto usa o menor", "aedes/familias.py",
     "return FATOR_DO_PISO_DE_RUIDO * max(pisos_envolvidos)", "return FATOR_DO_PISO_DE_RUIDO * min(pisos_envolvidos)"),
    ("M10 semente do bootstrap 43", "aedes/estatistica.py",
     "SEMENTE_DO_BOOTSTRAP = 42", "SEMENTE_DO_BOOTSTRAP = 43"),
    ("M11 delta com sinal trocado", "aedes/estatistica.py",
     "delta = mae_b - mae_a", "delta = mae_a - mae_b"),
    ("M12 composto com janela N+1", "aedes/composto.py",
     "inicio_da_janela = quantidade_de_pares_conhecidos - semanas_recentes", "inicio_da_janela = quantidade_de_pares_conhecidos - semanas_recentes - 1"),
    ("M13 Holm sobre as 52 juntas", "aedes/familias.py",
     "for familia in dict.fromkeys(nomes_das_familias):", "for familia in [None]:"),
    ("M14 razao invertida", "aedes/alarme.py",
     "return por_notificacao / por_residencia", "return por_residencia / por_notificacao"),
    ("M15 bloco do bootstrap 7", "aedes/estatistica.py",
     "TAMANHO_DO_BLOCO_DO_BOOTSTRAP = 8", "TAMANHO_DO_BLOCO_DO_BOOTSTRAP = 7"),
    ("M16 p bilateral vira unilateral", "aedes/estatistica.py",
     "p_bilateral = float(2.0 * stats.t.sf(abs(estatistica_hln), df=graus_de_liberdade))", "p_bilateral = float(stats.t.sf(abs(estatistica_hln), df=graus_de_liberdade))"),
    ("M17 falsos por ano divide por 2", "aedes/alarme.py",
     "ANOS_DA_AVALIACAO = 1.96", "ANOS_DA_AVALIACAO = 2.0"),
]

def preparar() -> None:
    if COPIA.exists():
        shutil.rmtree(COPIA)
    shutil.copytree(ORIGEM, COPIA, ignore=shutil.ignore_patterns("__pycache__", "parciais", "certificacao"))

resultados = []
for nome, arquivo, antigo, novo in MUTANTES:
    preparar()
    caminho = COPIA / arquivo
    texto = caminho.read_text(encoding="utf-8")
    assert texto.count(antigo) == 1, (nome, texto.count(antigo))
    caminho.write_text(texto.replace(antigo, novo), encoding="utf-8")
    processo = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", *TESTES],
        cwd=COPIA, capture_output=True, text=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "PATH": "/usr/bin:/bin:/Library/Frameworks/Python.framework/Versions/3.14/bin", "HOME": str(pathlib.Path.home())},
    )
    ultima = [linha for linha in processo.stdout.strip().splitlines() if linha.startswith("FAILED")]
    morto = processo.returncode != 0
    resultados.append((nome, "MORTO" if morto else "SOBREVIVEU", ultima[:1]))
    print(nome, "->", "MORTO" if morto else "SOBREVIVEU", ultima[:1], flush=True)
sobreviventes = [r for r in resultados if r[1] == "SOBREVIVEU"]
print(f"\n{len(resultados)} mutantes, {len(sobreviventes)} sobreviventes")
