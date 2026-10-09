import logging

import joblib

from ..config import settings
from .explain import build_narrative, explain_model
from .features import align
from .fusion import fuse

log = logging.getLogger("rds.ml")
MODEL_FILES = {"static": "static_xgb.joblib", "behavior": "behavior_xgb.joblib"}


class ModelStore:
    """Loads pre-trained bundles from disk. NOTE: joblib uses pickle - only load files you trained/trust."""

    def __init__(self):
        self.bundles: dict[str, dict] = {}

    def load(self) -> None:
        self.bundles.clear()
        for name, fn in MODEL_FILES.items():
            p = settings.model_dir / fn
            if p.exists():
                self.bundles[name] = joblib.load(p)
                log.info("loaded %s model (%d features)", name, len(self.bundles[name]["features"]))
            else:
                log.warning("model file missing: %s (run `python -m app.ml.train`)", p)


store = ModelStore()


def _score(bundle: dict, df):
    X, coverage = align(df, bundle["features"])
    if coverage < settings.min_feature_coverage:
        return None, coverage
    Xi = bundle["imputer"].transform(X.values)
    Xs = bundle["scaler"].transform(Xi)
    proba = bundle["model"].predict_proba(Xs)[:, 1]
    return {"score": float(proba.mean()), "row_scores": proba, "X_raw": X.values, "X_scaled": Xs}, coverage


def run_analysis(df, cfg: dict, explain: bool = True) -> dict:
    if not store.bundles:
        raise RuntimeError("No trained models loaded. Train or copy models into MODEL_DIR first.")
    scores, shap_out, details = {}, {}, {"rows": int(len(df)), "coverage": {}, "models_used": []}
    for name, bundle in store.bundles.items():
        res, cov = _score(bundle, df)
        details["coverage"][name] = round(cov, 3)
        if res is None:
            scores[name] = None
            continue
        scores[name] = res["score"]
        details["models_used"].append(name)
        details[f"{name}_rows_flagged"] = int((res["row_scores"] >= 0.5).sum())
        details[f"{name}_max_row_score"] = float(res["row_scores"].max())
        if explain:
            shap_out[name] = explain_model(bundle, res)
    if not details["models_used"]:
        raise ValueError("Uploaded columns do not match either model's features. Check column names against the feature schema.")
    fused = fuse(scores.get("static"), scores.get("behavior"), cfg)
    return {
        "static_score": scores.get("static"), "behavior_score": scores.get("behavior"), **fused,
        "shap": shap_out, "details": details,
        "explanation": build_narrative(fused["label"], fused["risk"], shap_out),
    }
