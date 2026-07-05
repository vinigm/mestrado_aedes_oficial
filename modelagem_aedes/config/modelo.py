"""

Diz QUAL modelo (algoritmo) um experimento vai usar, e com quais ajustes.

Antes o projeto estava preso ao LightGBM. Com esta ficha, cada experimento
escolhe o algoritmo que quiser (LightGBM, RandomForest, XGBoost...) sem mudar o
resto do codigo. A unica exigencia e que o modelo siga o jeito padrao do
scikit-learn (tenha os metodos .fit() pra treinar e .predict() pra prever) —
o que LightGBM, XGBoost e os modelos do scikit-learn seguem.

"""

import dataclasses


@dataclasses.dataclass(frozen=True)
class EspecificacaoModelo:
    """

    A ficha de um modelo: o nome, a classe (o algoritmo) e os ajustes dele.

    Attributes:
        nome: Nome curto que identifica o modelo nos resultados (ex.: "lightgbm",
            "random_forest").
        classe: A classe do modelo em si (ex.: LGBMRegressor, RandomForestRegressor).
            E ela que sera criada na hora de treinar.
        parametros: Os ajustes (hiperparametros) daquele modelo. Cada modelo tem
            os seus (o "verbose=-1", por exemplo, so existe no LightGBM), por isso
            cada ficha tem o seu proprio conjunto.

    """

    nome: str
    classe: type
    parametros: dict

    def criar(self):
        """Cria uma instancia nova do modelo, com os ajustes desta ficha."""
        return self.classe(**self.parametros)
