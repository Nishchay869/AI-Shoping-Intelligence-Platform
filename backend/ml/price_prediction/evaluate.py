"""Evaluation metrics: regression for the expected-future-price output, classification for price-drop probability."""
from dataclasses import dataclass
import numpy as np
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_absolute_percentage_error, precision_recall_fscore_support, root_mean_squared_error


@dataclass(frozen=True)
class RegressionMetrics:
    model_name: str
    mae: float
    rmse: float
    mape: float

    def report(self) -> str:
        return f"{self.model_name}\n  MAE : {self.mae:,.0f} (minor units)\n  RMSE: {self.rmse:,.0f} (minor units)\n  MAPE: {self.mape:.2%}"


@dataclass(frozen=True)
class ClassificationMetrics:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1: float

    def report(self) -> str:
        return f"{self.model_name}\n  accuracy : {self.accuracy:.4f}\n  precision: {self.precision:.4f}\n  recall   : {self.recall:.4f}\n  f1       : {self.f1:.4f}"


def evaluate_regression(model_name: str, y_true: np.ndarray, y_pred: np.ndarray) -> RegressionMetrics:
    return RegressionMetrics(model_name, mean_absolute_error(y_true, y_pred), root_mean_squared_error(y_true, y_pred), mean_absolute_percentage_error(y_true, y_pred))


def evaluate_classification(model_name: str, y_true: np.ndarray, y_pred: np.ndarray) -> ClassificationMetrics:
    """Binary metrics with 'price will drop' (1) as the positive class - the outcome the classifier exists to catch."""
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", pos_label=1, zero_division=0)
    return ClassificationMetrics(model_name, accuracy_score(y_true, y_pred), precision, recall, f1)
