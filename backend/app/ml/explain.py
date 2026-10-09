import numpy as np

try:  # optional: `pip install shap`. Without it we use XGBoost's built-in TreeSHAP (same exact values).
    import shap
except Exception:  # noqa: BLE001
    shap = None


def _shap_values(model, X):
    if shap is not None:
        ex = shap.TreeExplainer(model)
        sv = np.asarray(ex.shap_values(X))
        if sv.ndim == 3:
            sv = sv[..., -1]
        return sv, float(np.ravel(ex.expected_value)[-1])
    import xgboost as xgb
    contrib = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)  # last column = bias/base value
    return contrib[:, :-1], float(contrib[0, -1])


def _fmt(v):
    return "missing" if v is None else (f"{v:.4g}")


def explain_model(bundle: dict, res: dict, top_n: int = 12, max_rows: int = 200) -> dict:
    """SHAP (TreeExplainer) on the scaled matrix. Values are in log-odds space.
    Local explanation = the most suspicious row; summary = mean |SHAP| over the most suspicious rows."""
    idx = np.argsort(-res["row_scores"])[:max_rows]
    sv, base = _shap_values(bundle["model"], res["X_scaled"][idx])
    feats = bundle["features"]
    local, raw = sv[0], res["X_raw"][idx[0]]
    order = np.argsort(-np.abs(local))[:top_n]
    mean_abs = np.abs(sv).mean(axis=0)
    s_order = np.argsort(-mean_abs)[:top_n]
    return {
        "base_value": base,
        "row_index": int(idx[0]), "rows_explained": int(len(idx)),
        "local": [{"feature": feats[i], "shap": float(local[i]), "value": None if np.isnan(raw[i]) else float(raw[i])} for i in order],
        "summary": [{"feature": feats[i], "importance": float(mean_abs[i])} for i in s_order],
    }


def build_narrative(label: str, risk: float, shap_out: dict) -> str:
    names = {"static": "Static model", "behavior": "Behavioural model"}
    up = label != "Benign"
    parts = []
    for key, e in shap_out.items():
        picks = [f for f in e["local"] if (f["shap"] > 0) == up][:3]
        if picks:
            parts.append(f"{names[key]} - " + ", ".join(f"{p['feature']} ({_fmt(p['value'])})" for p in picks))
    head = f"This file was classified as {label} with a fused risk score of {risk:.2f}."
    if not parts:
        return head
    verb = "pushed the risk up" if up else "pulled the risk down"
    return f"{head} Top features that {verb}: " + "; ".join(parts) + "."
