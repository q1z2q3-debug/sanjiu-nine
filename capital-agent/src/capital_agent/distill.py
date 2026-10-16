import time
import numpy as np

class NumpyMLP:
    def __init__(self, in_dim, h1=32, h2=16, seed=42):
        rng = np.random.default_rng(seed)
        self.W1 = rng.standard_normal((in_dim, h1)).astype(np.float32) * 0.1
        self.b1 = np.zeros(h1, dtype=np.float32)
        self.W2 = rng.standard_normal((h1, h2)).astype(np.float32) * 0.1
        self.b2 = np.zeros(h2, dtype=np.float32)
        self.W3 = rng.standard_normal((h2, 1)).astype(np.float32) * 0.1
        self.b3 = np.zeros(1, dtype=np.float32)

    @staticmethod
    def _relu(x): return np.maximum(0, x)

    @staticmethod
    def _sigmoid(x): return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))

    def forward(self, X):
        a1 = self._relu(X @ self.W1 + self.b1)
        a2 = self._relu(a1 @ self.W2 + self.b2)
        return self._sigmoid(a2 @ self.W3 + self.b3).squeeze(-1)

    def train_step(self, X, y, lr=0.01):
        n = X.shape[0]
        z1 = X @ self.W1 + self.b1; a1 = self._relu(z1)
        z2 = a1 @ self.W2 + self.b2; a2 = self._relu(z2)
        z3 = a2 @ self.W3 + self.b3; yh = self._sigmoid(z3).squeeze(-1)
        eps = 1e-7
        loss = -np.mean(y * np.log(yh + eps) + (1 - y) * np.log(1 - yh + eps))
        dz3 = (yh - y).reshape(-1, 1) / n
        dW3 = a2.T @ dz3; db3 = dz3.sum(axis=0)
        da2 = dz3 @ self.W3.T; dz2 = da2 * (z2 > 0)
        dW2 = a1.T @ dz2; db2 = dz2.sum(axis=0)
        da1 = dz2 @ self.W2.T; dz1 = da1 * (z1 > 0)
        dW1 = X.T @ dz1; db1 = dz1.sum(axis=0)
        self.W3 -= lr * dW3; self.b3 -= lr * db3
        self.W2 -= lr * dW2; self.b2 -= lr * db2
        self.W1 -= lr * dW1; self.b1 -= lr * db1
        return float(loss)

    def save(self, path):
        np.savez(path, W1=self.W1, b1=self.b1, W2=self.W2, b2=self.b2,
                 W3=self.W3, b3=self.b3)

    def load(self, path):
        d = np.load(path)
        self.W1, self.b1 = d["W1"], d["b1"]
        self.W2, self.b2 = d["W2"], d["b2"]
        self.W3, self.b3 = d["W3"], d["b3"]


class LocalPolicyModel:
    """用 27 维 one-hot（每维3态）+ 数据增强的蒸馏模型。"""

    def __init__(self, memory, hidden=(64, 32)):
        self.mem = memory
        self.net = NumpyMLP(in_dim=54, h1=hidden[0], h2=hidden[1])  # 9*3 * 2
        self.trained_samples = 0
        self.last_loss = None

    @staticmethod
    def _onehot(trit: str) -> np.ndarray:
        out = np.zeros(27, dtype=np.float32)
        for i, c in enumerate(trit):
            out[i * 3 + int(c)] = 1.0
        return out

    def pair_features(self, trit, action):
        return np.concatenate([self._onehot(trit), self._onehot(action)])

    @staticmethod
    def _perturb(trit, rng):
        i = int(rng.integers(0, 9))
        c = str(int(rng.integers(0, 3)))
        return trit[:i] + c + trit[i+1:]

    def export_dataset(self, augment=True, noise=2):
        rows = self.mem.conn.execute(
            "SELECT trit,action,success,total FROM policies WHERE total >= 1"
        ).fetchall()
        X, y = [], []
        rng = np.random.default_rng(42)
        for r in rows:
            X.append(self.pair_features(r["trit"], r["action"]))
            y.append(r["success"] / max(1, r["total"]))
            if augment:
                for _ in range(noise):
                    t2 = self._perturb(r["trit"], rng)
                    a2 = self._perturb(r["action"], rng)
                    X.append(self.pair_features(t2, a2))
                    y.append((r["success"] / max(1, r["total"])) * 0.9)
        if not X:
            return np.zeros((0, 54), dtype=np.float32), np.zeros((0,), dtype=np.float32)
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def train(self, epochs=80, lr=0.02, batch_size=64):
        X, y = self.export_dataset()
        if len(X) == 0:
            return {"trained": False, "reason": "no_data"}
        losses = []
        for _ in range(epochs):
            idx = np.random.permutation(len(X))
            ep = 0.0
            for i in range(0, len(X), batch_size):
                b = idx[i:i+batch_size]
                ep += self.net.train_step(X[b], y[b], lr=lr) * len(b)
            losses.append(ep / len(X))
        self.trained_samples = len(X)
        self.last_loss = losses[-1]
        return {"trained": True, "samples": len(X),
                "first_loss": round(losses[0], 4),
                "final_loss": round(losses[-1], 4)}

    def rank_actions(self, trit, candidates):
        if not candidates:
            return []
        X = np.stack([self.pair_features(trit, c) for c in candidates])
        scores = self.net.forward(X)
        return sorted(zip(candidates, scores.tolist()), key=lambda x: -x[1])

    def save(self, path):
        self.net.save(path)

    def load(self, path):
        self.net.load(path)
