"""

Testes dos calculos que dizem se o alarme de surto acertou ou errou (avaliacao.metricas).

Compara os resultados com o sklearn (uma biblioteca pronta e confiavel) nos casos que tem
as duas classes (deu surto e nao deu surto). Tambem confere o que acontece nos casos
esquisitos, tipo quando uma conta que ia dividir por zero tem que dar "sem resultado" (NaN)
em vez de dar erro. Os testes rodam rapido. Pra rodar: python tests/test_metricas.py
(ou pytest).

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score

from avaliacao import metricas



def test_caso_comum_bate_com_sklearn():
    y_real = [0, 1, 0, 1, 1, 0]
    y_previsto = [0, 1, 1, 1, 0, 0]
    probabilidade = [0.1, 0.9, 0.6, 0.8, 0.3, 0.2]
    calculado = metricas.calcular_metricas_classificacao(y_real, y_previsto, probabilidade)
    assert calculado["f1"] == f1_score(y_real, y_previsto)
    assert calculado["bal_acc"] == balanced_accuracy_score(y_real, y_previsto)
    assert calculado["auc"] == roc_auc_score(y_real, probabilidade)
    assert calculado["n"] == len(y_real)
    assert calculado["tp"] + calculado["fn"] == calculado["n_pos"]



def test_nenhum_positivo_previsto_precisao_nan():
    calculado = metricas.calcular_metricas_classificacao(
        [0, 1, 0, 1], [0, 0, 0, 0], [0.1, 0.2, 0.3, 0.4]
    )
    # nao previu nenhum positivo -> a conta da precisao ia dividir por zero -> vira NaN (sem resultado).
    assert np.isnan(calculado["precisao"])
    # tem casos positivos de verdade, mas nenhum foi encontrado -> sensibilidade fica 0.
    assert calculado["sensib"] == 0.0



def test_uma_classe_real_sem_auc_e_sensib_nan():
    calculado = metricas.calcular_metricas_classificacao(
        [0, 0, 0], [0, 0, 1], [0.1, 0.2, 0.9]
    )
    # so tem uma classe nos dados reais -> AUC nao da pra calcular, entao nem aparece no resultado.
    assert "auc" not in calculado
    assert "ap" not in calculado
    # nao tem nenhum caso positivo de verdade -> sensibilidade vira NaN (sem resultado).
    assert np.isnan(calculado["sensib"])



def test_probabilidade_ausente_sem_auc():
    calculado = metricas.calcular_metricas_classificacao([0, 1, 0, 1], [0, 1, 1, 0], None)
    assert "auc" not in calculado
    assert "ap" not in calculado



def test_ordem_das_chaves_estavel():
    calculado = metricas.calcular_metricas_classificacao([0, 1], [0, 1], [0.2, 0.8])
    chaves_esperadas = [
        "n", "n_pos", "tp", "fp", "fn", "tn",
        "sensib", "espec", "precisao", "f1", "bal_acc", "auc", "ap",
    ]
    assert list(calculado.keys()) == chaves_esperadas



if __name__ == "__main__":
    testes = [
        valor
        for nome, valor in sorted(globals().items())
        if nome.startswith("test_") and callable(valor)
    ]
    for teste in testes:
        teste()
        print("OK:", teste.__name__)
    print(f"\n{len(testes)} teste(s) passaram")
