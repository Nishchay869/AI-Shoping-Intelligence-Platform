"""XGBoost: two heads on the same engineered tabular feature set - a regressor for expected future price and
a classifier for probability of a price drop. Trees pick up the nonlinear feature interactions (e.g. "high
recent discount frequency AND an upcoming sale event" being a much stronger drop signal than either alone)
that Prophet's additive structure and a single LSTM regression head don't directly represent, and give a
well-calibrated `predict_proba` for the drop-probability output specifically.
"""
import numpy as np
from xgboost import XGBClassifier, XGBRegressor


def train_price_regressor(X_train: np.ndarray, y_train: np.ndarray, seed: int = 42) -> XGBRegressor:
    model = XGBRegressor(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9, random_state=seed, n_jobs=-1)
    model.fit(X_train, y_train)
    return model


def train_price_drop_classifier(X_train: np.ndarray, y_train: np.ndarray, seed: int = 42) -> XGBClassifier:
    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)  # counteract class imbalance directly in the loss
    model = XGBClassifier(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9, scale_pos_weight=scale_pos_weight, eval_metric="logloss", random_state=seed, n_jobs=-1)
    model.fit(X_train, y_train)
    return model
