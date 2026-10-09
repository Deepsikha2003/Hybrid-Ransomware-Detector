"""Synthetic data generator - for wiring/demo only. NOT a substitute for real ransomware datasets."""
import numpy as np
import pandas as pd


def synthetic(features: list[str], n: int = 3000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, n)
    data = {}
    for i, f in enumerate(features):
        shift = (i % 5 - 2) * 0.6 + 0.8
        data[f] = np.abs(rng.normal(10 + 5 * i, 4 + i, n) + y * shift * (4 + i % 3) * rng.uniform(0.5, 1.5, n))
    df = pd.DataFrame(data)
    df["Label"] = np.where(y == 1, "ransomware", "benign")
    return df
