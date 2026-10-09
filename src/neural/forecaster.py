"""
Neural Demand Forecaster for Cloud Datacenter Workloads.
Implements a GRU recurrent neural network to predict upcoming
cluster CPU and RAM demands using historical sliding time windows.
Supports both PyTorch training/inference and lightweight zero-dependency
NumPy forward pass inference for ultra-fast serverless (Vercel/Cloud) deployments.
"""
import os
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    nn = None
    TORCH_AVAILABLE = False


if TORCH_AVAILABLE:
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
            last_step = out[:, -1, :]
            preds = self.fc(last_step)
            return preds
else:
    DemandForecasterGRU = None


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def _gru_cell_np(x: np.ndarray, h_prev: np.ndarray, W_ih: np.ndarray, W_hh: np.ndarray, b_ih: np.ndarray, b_hh: np.ndarray) -> np.ndarray:
    """Exact NumPy forward implementation of PyTorch GRU cell."""
    H = len(h_prev)
    gi = x @ W_ih.T + b_ih
    gh = h_prev @ W_hh.T + b_hh
    
    r = _sigmoid(gi[:H] + gh[:H])
    z = _sigmoid(gi[H : 2 * H] + gh[H : 2 * H])
    n = np.tanh(gi[2 * H :] + r * gh[2 * H :])
    return (1.0 - z) * n + z * h_prev


class DemandForecaster:
    """
    Wrapper providing training, testing, persistence, and rolling inference.
    Supports native PyTorch inference and lightweight pure NumPy forward pass.
    """
    def __init__(self, window_size: int = 12, hidden_dim: int = 32):
        self.window_size = window_size
        self.hidden_dim = hidden_dim
        self.is_trained = False
        self.use_numpy_inference = False
        self.numpy_weights: Dict[str, np.ndarray] = {}
        
        if TORCH_AVAILABLE:
            self.model = DemandForecasterGRU(input_dim=2, hidden_dim=hidden_dim)
        else:
            self.model = None

        # Normalization scalers
        self.cpu_max = 1.0
        self.ram_max = 1.0

    def create_dataset(
        self, series: np.ndarray
    ) -> Tuple[Any, Any]:
        """
        Creates (X, y) sliding window pairs from a (T, 2) array.
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for dataset tensor creation and training.")
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
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for model training.")

        torch.manual_seed(42)
        np.random.seed(42)
        
        self.cpu_max = float(np.max(time_series[:, 0])) if np.max(time_series[:, 0]) > 0 else 1.0
        self.ram_max = float(np.max(time_series[:, 1])) if np.max(time_series[:, 1]) > 0 else 1.0

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

        self.model.eval()
        with torch.no_grad():
            preds_scaled = self.model(X_test).numpy()
            y_test_np = y_test.numpy()

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
            # Save standard PyTorch checkpoint
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
            # Also save lightweight NumPy weights for serverless deployment
            npz_path = os.path.splitext(save_path)[0] + "_weights.npz"
            weights_dict = {k: v.cpu().numpy() for k, v in self.model.state_dict().items()}
            np.savez(
                npz_path,
                **weights_dict,
                cpu_max=self.cpu_max,
                ram_max=self.ram_max,
                window_size=self.window_size,
                hidden_dim=self.hidden_dim,
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
        """Loads serialized model weights (supports .pt, .npz, or auto-fallback)."""
        # If model_path is .npz or torch is not available, load via NumPy
        if model_path.endswith(".npz") or not TORCH_AVAILABLE:
            target_npz = model_path if model_path.endswith(".npz") else os.path.splitext(model_path)[0] + "_weights.npz"
            if not os.path.exists(target_npz):
                # Search common directory
                alt = os.path.join(os.path.dirname(model_path), "demand_forecaster_weights.npz")
                if os.path.exists(alt):
                    target_npz = alt
            
            data = np.load(target_npz)
            self.cpu_max = float(data["cpu_max"])
            self.ram_max = float(data["ram_max"])
            self.window_size = int(data["window_size"])
            self.hidden_dim = int(data["hidden_dim"])
            self.numpy_weights = {k: data[k] for k in data.files if k not in ["cpu_max", "ram_max", "window_size", "hidden_dim"]}
            self.use_numpy_inference = True
            self.is_trained = True
            return

        # PyTorch loading
        checkpoint = torch.load(model_path, map_location=torch.device("cpu"))
        self.cpu_max = checkpoint["cpu_max"]
        self.ram_max = checkpoint["ram_max"]
        self.window_size = checkpoint["window_size"]
        self.hidden_dim = checkpoint["hidden_dim"]
        self.model = DemandForecasterGRU(input_dim=2, hidden_dim=self.hidden_dim)
        self.model.load_state_dict(checkpoint["model_state"])
        self.model.eval()
        self.use_numpy_inference = False
        self.is_trained = True

    def _predict_next_numpy(self, scaled_window: np.ndarray) -> np.ndarray:
        """Runs bit-exact NumPy forward pass through GRU + FC layers."""
        W = self.numpy_weights
        H = self.hidden_dim
        
        # Layer 0 GRU
        h0_seq = []
        h_curr0 = np.zeros(H, dtype=np.float32)
        for t in range(len(scaled_window)):
            h_curr0 = _gru_cell_np(
                scaled_window[t], h_curr0,
                W["gru.weight_ih_l0"], W["gru.weight_hh_l0"],
                W["gru.bias_ih_l0"], W["gru.bias_hh_l0"]
            )
            h0_seq.append(h_curr0)
        
        # Layer 1 GRU
        h_curr1 = np.zeros(H, dtype=np.float32)
        for t in range(len(h0_seq)):
            h_curr1 = _gru_cell_np(
                h0_seq[t], h_curr1,
                W["gru.weight_ih_l1"], W["gru.weight_hh_l1"],
                W["gru.bias_ih_l1"], W["gru.bias_hh_l1"]
            )
        
        # FC layers: Linear(32, 16) -> ReLU -> Linear(16, 2)
        fc0 = np.maximum(0, h_curr1 @ W["fc.0.weight"].T + W["fc.0.bias"])
        out = fc0 @ W["fc.2.weight"].T + W["fc.2.bias"]
        return out

    def predict_next(self, history_window: np.ndarray) -> Tuple[float, float]:
        """
        Given the last (window_size, 2) [CPU, RAM] demands, predicts next step (CPU, RAM).
        """
        if not self.is_trained:
            # Fallback to moving average if not trained
            return float(np.mean(history_window[:, 0])), float(np.mean(history_window[:, 1]))

        scaled = np.copy(history_window).astype(np.float32)
        scaled[:, 0] /= self.cpu_max
        scaled[:, 1] /= self.ram_max

        if self.use_numpy_inference or not TORCH_AVAILABLE:
            pred = self._predict_next_numpy(scaled)
            pred_cpu = max(0.0, float(pred[0] * self.cpu_max))
            pred_ram = max(0.0, float(pred[1] * self.ram_max))
            return pred_cpu, pred_ram

        x_tensor = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)
        self.model.eval()
        with torch.no_grad():
            pred = self.model(x_tensor).squeeze(0).numpy()
            pred_cpu = max(0.0, float(pred[0] * self.cpu_max))
            pred_ram = max(0.0, float(pred[1] * self.ram_max))
            return pred_cpu, pred_ram
