"""
Neural Demand Forecaster for Cloud Datacenter Workloads.
Implements a PyTorch GRU recurrent neural network to predict upcoming
cluster CPU and RAM demands using historical sliding time windows.
"""
import os
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional


class DemandForecasterGRU(nn.Module):
    """
    GRU sequence model predicting future cluster resource demand.
    Input shape: (batch_size, window_size, 2) [CPU, RAM]
    Output shape: (batch_size, 2) [Predicted CPU, Predicted RAM]
    """
    def __init__(self, input_dim: int = 2, hidden_dim: int = 32, num_layers: int = 2):
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.1 if num_layers > 1 else 0.0,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.gru(x)
        # Take the hidden representation from the last time step
        last_step = out[:, -1, :]
        preds = self.fc(last_step)
        return preds


class DemandForecaster:
    """
    Wrapper providing training, testing, persistence, and rolling inference.
    """
    def __init__(self, window_size: int = 12, hidden_dim: int = 32):
        self.window_size = window_size
        self.hidden_dim = hidden_dim
        self.model = DemandForecasterGRU(input_dim=2, hidden_dim=hidden_dim)
        self.is_trained = False
        # Normalization scalers
        self.cpu_max = 1.0
        self.ram_max = 1.0

    def create_dataset(
        self, series: np.ndarray
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Creates (X, y) sliding window pairs from a (T, 2) array.
        """
        X, y = [], []
        for i in range(len(series) - self.window_size):
            X.append(series[i : i + self.window_size])
            y.append(series[i + self.window_size])
        return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

    def train_model(
        self,
        time_series: np.ndarray,
        epochs: int = 50,
        lr: float = 0.005,
        save_path: Optional[str] = None,
        results_csv_path: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Trains model on a (T, 2) time series [CPU demand, RAM demand].
        Evaluates on held-out test split and computes MAE & RMSE.
        """
        torch.manual_seed(42)
        np.random.seed(42)
        
        self.cpu_max = float(np.max(time_series[:, 0])) if np.max(time_series[:, 0]) > 0 else 1.0
        self.ram_max = float(np.max(time_series[:, 1])) if np.max(time_series[:, 1]) > 0 else 1.0

        # Min-max scale
        scaled_series = np.copy(time_series)
        scaled_series[:, 0] /= self.cpu_max
        scaled_series[:, 1] /= self.ram_max

        X, y = self.create_dataset(scaled_series)
        n = len(X)
        if n < 20:
            raise ValueError(f"Time series too short for training: {n} samples.")

        train_size = int(n * 0.70)
        val_size = int(n * 0.15)
        test_size = n - train_size - val_size

        X_train, y_train = X[:train_size], y[:train_size]
        X_val, y_val = X[train_size : train_size + val_size], y[train_size : train_size + val_size]
        X_test, y_test = X[train_size + val_size :], y[train_size + val_size :]

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            out = self.model(X_train)
            loss = criterion(out, y_train)
            loss.backward()
            optimizer.step()

        # Evaluate on test set
        self.model.eval()
        with torch.no_grad():
            preds_scaled = self.model(X_test).numpy()
            y_test_np = y_test.numpy()

            # Rescale back to physical units
            preds_cpu = preds_scaled[:, 0] * self.cpu_max
            preds_ram = preds_scaled[:, 1] * self.ram_max
            actual_cpu = y_test_np[:, 0] * self.cpu_max
            actual_ram = y_test_np[:, 1] * self.ram_max

            mae_cpu = float(np.mean(np.abs(preds_cpu - actual_cpu)))
            rmse_cpu = float(np.sqrt(np.mean((preds_cpu - actual_cpu) ** 2)))
            mae_ram = float(np.mean(np.abs(preds_ram - actual_ram)))
            rmse_ram = float(np.sqrt(np.mean((preds_ram - actual_ram) ** 2)))

        self.is_trained = True

        if save_path:
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            torch.save(
                {
                    "model_state": self.model.state_dict(),
                    "cpu_max": self.cpu_max,
                    "ram_max": self.ram_max,
                    "window_size": self.window_size,
                    "hidden_dim": self.hidden_dim,
                },
                save_path,
            )

        if results_csv_path:
            os.makedirs(os.path.dirname(os.path.abspath(results_csv_path)), exist_ok=True)
            df_eval = pd.DataFrame({
                "test_step": np.arange(len(actual_cpu)),
                "actual_cpu": actual_cpu,
                "predicted_cpu": preds_cpu,
                "actual_ram": actual_ram,
                "predicted_ram": preds_ram,
            })
            df_eval.to_csv(results_csv_path, index=False)

        metrics = {
            "mae_cpu": round(mae_cpu, 4),
            "rmse_cpu": round(rmse_cpu, 4),
            "mae_ram": round(mae_ram, 4),
            "rmse_ram": round(rmse_ram, 4),
            "test_samples": len(actual_cpu),
        }
        return metrics

    def load_model(self, model_path: str) -> None:
        """Loads serialized model weights and scaling parameters."""
        checkpoint = torch.load(model_path, map_location=torch.device("cpu"))
        self.cpu_max = checkpoint["cpu_max"]
        self.ram_max = checkpoint["ram_max"]
        self.window_size = checkpoint["window_size"]
        self.hidden_dim = checkpoint["hidden_dim"]
        self.model = DemandForecasterGRU(input_dim=2, hidden_dim=self.hidden_dim)
        self.model.load_state_dict(checkpoint["model_state"])
        self.model.eval()
        self.is_trained = True

    def predict_next(self, history_window: np.ndarray) -> Tuple[float, float]:
        """
        Given the last (window_size, 2) [CPU, RAM] demands, predicts next step (CPU, RAM).
        """
        if not self.is_trained:
            # Fallback to moving average if not trained
            return float(np.mean(history_window[:, 0])), float(np.mean(history_window[:, 1]))

        scaled = np.copy(history_window)
        scaled[:, 0] /= self.cpu_max
        scaled[:, 1] /= self.ram_max

        x_tensor = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)
        self.model.eval()
        with torch.no_grad():
            pred = self.model(x_tensor).squeeze(0).numpy()
            pred_cpu = max(0.0, float(pred[0] * self.cpu_max))
            pred_ram = max(0.0, float(pred[1] * self.ram_max))
            return pred_cpu, pred_ram
