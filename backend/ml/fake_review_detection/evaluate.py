"""Evaluation metrics for the fake-review classifiers."""
from dataclasses import dataclass
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support


@dataclass(frozen=True)
class ClassificationMetrics:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion: np.ndarray

    def report(self) -> str:
        tn, fp, fn, tp = self.confusion.ravel()
        return (
            f"{self.model_name}\n"
            f"  accuracy : {self.accuracy:.4f}\n"
            f"  precision: {self.precision:.4f}  (of reviews flagged fake, how many really were)\n"
            f"  recall   : {self.recall:.4f}  (of actually fake reviews, how many were caught)\n"
            f"  f1       : {self.f1:.4f}\n"
            f"  confusion matrix [tn={tn} fp={fp} fn={fn} tp={tp}]"
        )


def evaluate(model_name: str, y_true: np.ndarray, y_pred: np.ndarray) -> ClassificationMetrics:
    """Binary metrics with the fake class (1) as positive - the class we actually care about catching."""
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", pos_label=1, zero_division=0)
    accuracy = accuracy_score(y_true, y_pred)
    confusion = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return ClassificationMetrics(model_name=model_name, accuracy=accuracy, precision=precision, recall=recall, f1=f1, confusion=confusion)
