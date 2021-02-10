from enum import Enum


class Estimator(Enum):
    CLASSIFIER = 'CLASSIFIER'
    REGRESSOR = 'REGRESSOR'
    CLUSTERING = 'CLUSTERING'


class Sklearn(Enum):  # TODO 삭제예정
    IRIS = 'iris'
    BOSTON = 'boston'
    DIABETES = 'diabetes'
    BREAST_CANCER = 'breast_cancer'
    WINE = 'wine'
