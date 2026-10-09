"""Train the Static and Behavioural XGBoost models.

  python -m app.ml.train --static-csv data/static.csv --behavior-csv data/behavior.csv --label-col Label
  python -m app.ml.train --demo        # SYNTHETIC data, for wiring/demo only - not real detection performance
"""
import argparse
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ..config import settings
from .features import BEHAVIOR_FEATURES, STATIC_FEATURES
from .synthetic import synthetic

BENIGN_WORDS = ("benign", "legit", "normal", "clean", "good")


def to_binary(y: pd.Series) -> np.ndarray:
    if pd.api.types.is_numeric_dtype(y):
        return (y.astype(float) > 0).astype(int).values
    return (~y.astype(str).str.lower().str.contains("|".join(BENIGN_WORDS))).astype(int).values


def clean(df: pd.DataFrame, label_col: str) -> tuple[pd.DataFrame, np.ndarray]:
    df = df.replace([np.inf, -np.inf], np.nan).drop_duplicates().dropna(subset=[label_col]).reset_index(drop=True)
    y = to_binary(df[label_col])
    X = df.drop(columns=[label_col]).apply(pd.to_numeric, errors="coerce")
    X = X.dropna(axis=1, how="all")  # non-numeric / empty columns are dropped
    return X, y


def train_one(X: pd.DataFrame, y: np.ndarray, name: str, top_k: int = 30, seed: int = 42, synthetic: bool = False) -> dict:
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=seed)
    # feature selection: drop (near-)constant columns, then keep top_k by a quick XGBoost importance
    imp0 = SimpleImputer(strategy="median").fit(X_tr)
    vt = VarianceThreshold(1e-12).fit(imp0.transform(X_tr))
    cols = list(X.columns[vt.get_support()])
    spw = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))
    mk = lambda: XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                               eval_metric="logloss", scale_pos_weight=spw, random_state=seed, n_jobs=-1)
    quick = mk().fit(imp0.transform(X_tr)[:, vt.get_support()], y_tr)
    keep = [cols[i] for i in np.argsort(-quick.feature_importances_)[:top_k] if quick.feature_importances_[i] > 0] or cols[:top_k]
    # final preprocessing + model on selected features
    imputer = SimpleImputer(strategy="median").fit(X_tr[keep])
    scaler = StandardScaler().fit(imputer.transform(X_tr[keep]))
    f = lambda d: scaler.transform(imputer.transform(d[keep]))
    model = mk().fit(f(X_tr), y_tr)
    proba, pred = model.predict_proba(f(X_te))[:, 1], model.predict(f(X_te))
    fpr, tpr, _ = roc_curve(y_te, proba)
    sel = np.linspace(0, len(fpr) - 1, min(100, len(fpr))).astype(int)
    metrics = {
        "accuracy": accuracy_score(y_te, pred), "precision": precision_score(y_te, pred, zero_division=0),
        "recall": recall_score(y_te, pred, zero_division=0), "f1": f1_score(y_te, pred, zero_division=0),
        "roc_auc": roc_auc_score(y_te, proba), "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
        "roc": {"fpr": fpr[sel].tolist(), "tpr": tpr[sel].tolist()},
        "feature_importance": sorted(({"feature": k, "importance": float(v)} for k, v in zip(keep, model.feature_importances_)), key=lambda d: -d["importance"])[:15],
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
    }
    bundle = {"name": name, "model": model, "imputer": imputer, "scaler": scaler, "features": keep, "metrics": metrics,
              "synthetic": synthetic, "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, settings.model_dir / f"{name}_xgb.joblib")
    (settings.model_dir / f"{name}_metrics.json").write_text(json.dumps({k: v for k, v in bundle.items() if k in ("name", "metrics", "synthetic", "trained_at", "features")}, indent=2))
    print(f"[{name}] acc={metrics['accuracy']:.4f} prec={metrics['precision']:.4f} rec={metrics['recall']:.4f} f1={metrics['f1']:.4f} auc={metrics['roc_auc']:.4f}")
    return bundle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--static-csv"); ap.add_argument("--behavior-csv")
    ap.add_argument("--label-col", default="Label"); ap.add_argument("--top-k", type=int, default=30)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        for name, feats in (("static", STATIC_FEATURES), ("behavior", BEHAVIOR_FEATURES)):
            X, y = clean(synthetic(feats), "Label")
            train_one(X, y, name, top_k=a.top_k, synthetic=True)
        return
    if not (a.static_csv or a.behavior_csv):
        ap.error("provide --static-csv and/or --behavior-csv, or --demo")
    for name, path in (("static", a.static_csv), ("behavior", a.behavior_csv)):
        if path:
            X, y = clean(pd.read_csv(path, low_memory=False), a.label_col)
            train_one(X, y, name, top_k=a.top_k)


if __name__ == "__main__":
    main()
