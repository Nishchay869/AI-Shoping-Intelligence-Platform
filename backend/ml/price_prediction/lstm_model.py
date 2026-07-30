"""LSTM: learns short-term sequential patterns directly from an ordered window of recent daily feature
vectors - complementary to Prophet's global additive decomposition and to XGBoost, which sees each row as
an independent flat feature vector with no notion of order. A recent run of increasing discount frequency
followed by a dip, for instance, is a *sequence* pattern the LSTM's recurrent state can pick up on that a
tree split on the same features, evaluated one row at a time, cannot represent as directly.
"""
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

SEQUENCE_LENGTH = 30


class PriceLSTM(nn.Module):
    def __init__(self, n_features: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_size=n_features, hidden_size=hidden_size, num_layers=num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0.0)
        self.head = nn.Sequential(nn.Linear(hidden_size, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, (hidden, _) = self.lstm(x)
        return self.head(hidden[-1]).squeeze(-1)


def make_sequences(feature_matrix: np.ndarray, targets: np.ndarray, sequence_length: int = SEQUENCE_LENGTH) -> tuple[np.ndarray, np.ndarray]:
    """Slide a `sequence_length`-row window over feature_matrix; targets[i] is the label for the window ending at row i."""
    sequences, labels = [], []
    for end in range(sequence_length - 1, len(feature_matrix)):
        if np.isnan(targets[end]): continue
        window = feature_matrix[end - sequence_length + 1: end + 1]
        if np.isnan(window).any(): continue
        sequences.append(window)
        labels.append(targets[end])
    return np.array(sequences, dtype=np.float32), np.array(labels, dtype=np.float32)


class LSTMPricePredictor:
    """A small sklearn-like wrapper: standardizes features/target, trains PriceLSTM, predicts in original price units."""

    def __init__(self, sequence_length: int = SEQUENCE_LENGTH, epochs: int = 60, lr: float = 1e-3, batch_size: int = 32, seed: int = 42):
        self.sequence_length = sequence_length
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.seed = seed
        self.model: PriceLSTM | None = None

    def fit(self, feature_matrix: np.ndarray, targets: np.ndarray) -> "LSTMPricePredictor":
        torch.manual_seed(self.seed)
        self.feature_mean = np.nanmean(feature_matrix, axis=0)
        self.feature_std = np.nanstd(feature_matrix, axis=0) + 1e-6
        self.target_mean = float(np.nanmean(targets))
        self.target_std = float(np.nanstd(targets) + 1e-6)

        normalized_features = (feature_matrix - self.feature_mean) / self.feature_std
        normalized_targets = (targets - self.target_mean) / self.target_std
        sequences, labels = make_sequences(normalized_features, normalized_targets, self.sequence_length)

        self.model = PriceLSTM(n_features=sequences.shape[2])
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        loss_fn = nn.MSELoss()
        loader = DataLoader(TensorDataset(torch.from_numpy(sequences), torch.from_numpy(labels)), batch_size=self.batch_size, shuffle=True)

        self.model.train()
        for _ in range(self.epochs):
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                loss = loss_fn(self.model(batch_x), batch_y)
                loss.backward()
                optimizer.step()
        return self

    def predict(self, sequences: np.ndarray) -> np.ndarray:
        """sequences: (n_samples, sequence_length, n_features) raw-scale windows, each ending at its prediction point."""
        normalized = (sequences - self.feature_mean) / self.feature_std
        self.model.eval()
        with torch.no_grad():
            prediction = self.model(torch.from_numpy(normalized.astype(np.float32))).numpy()
        return prediction * self.target_std + self.target_mean
