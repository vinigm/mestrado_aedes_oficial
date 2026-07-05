# Testes do modelagem_aedes

Dois niveis: testes rapidos de unidade (rodam em segundos) e uma validacao
end-to-end lenta (roda os modelos de verdade, leva minutos).

## Testes rapidos (unidade)

Nao treinam modelo — checam as pecas puras (montagem, features, metricas, McNemar).
Cada arquivo roda sozinho **ou** sob pytest.

Sozinho (sem dependencia extra):

```bash
cd modelagem_aedes
python tests/test_montagem.py     # tabela_final reconstruida == a salva (byte a byte)
python tests/test_features.py     # lags/media movel/sazonalidade por bloco
python tests/test_metricas.py     # metricas de classificacao vs sklearn
python tests/test_mcnemar.py      # McNemar (binomial exato / qui-quadrado) vs scipy
```

Todos de uma vez, com pytest:

```bash
cd modelagem_aedes
pytest tests -q
```

O que cada um garante:

- **test_montagem** — o upstream (`montar.py`) reproduz exatamente a `tabela_final`
  que os experimentos consomem. E o teste mais importante do dia a dia: se a
  montagem mudar sem querer, ele acusa.
- **test_features** — lags e medias moveis nao atravessam o gap entre os blocos
  (Marilia x raspagem); `construir_features_temporais` nao muta a entrada.
- **test_metricas** — F1/AUC/bal_acc batem com o sklearn; precisao/sensib/espec
  viram NaN (nao 0) quando o denominador e zero.
- **test_mcnemar** — contagens, escolha do teste e p-valores batem com o scipy.

## Validacao end-to-end (LENTA, opt-in)

`validar_experimentos.py` roda cada experimento pelo `main.py` e compara com os
CSVs de resultados ja salvos. Leva minutos (LightGBM de verdade), por isso o nome
nao comeca com `test_` — o pytest nao o coleta. Rode a mao so ao mexer no motor
ou nas features:

```bash
cd modelagem_aedes
python tests/validar_experimentos.py
```

- Deteccao (`n_jobs=1`, deterministica) -> espera-se **IDENTICO** byte a byte.
- Regressao (`n_jobs=-1`) tem ruido de thread -> reporta `max|dMAE|`/`max|dR2|`
  em vez de exigir igualdade exata (diferenca minuscula = ruido, nao erro).

O script faz backup dos CSVs de referencia num diretorio temporario e os
**restaura ao final**, entao rodar a validacao nunca perde a referencia.
