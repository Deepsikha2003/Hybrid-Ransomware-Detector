"""Hybrid risk fusion: Final = w_static * Static + w_behavior * Behavior (configurable)."""
DEFAULT_CONFIG = {"w_static": 0.6, "w_behavior": 0.4, "t_suspicious": 0.40, "t_ransomware": 0.80}


def validate_config(cfg: dict) -> dict:
    out = {k: float(cfg.get(k, v)) for k, v in DEFAULT_CONFIG.items()}
    if out["w_static"] < 0 or out["w_behavior"] < 0 or out["w_static"] + out["w_behavior"] <= 0:
        raise ValueError("Weights must be non-negative and not both zero.")
    total = out["w_static"] + out["w_behavior"]
    out["w_static"], out["w_behavior"] = out["w_static"] / total, out["w_behavior"] / total
    if not (0 < out["t_suspicious"] < out["t_ransomware"] <= 1):
        raise ValueError("Thresholds must satisfy 0 < suspicious < ransomware <= 1.")
    return out


def classify(risk: float, cfg: dict) -> tuple[str, str]:
    """Return (label, threat_level). 'High' is the upper half of the Suspicious band (orange on the gauge)."""
    ts, tr = cfg["t_suspicious"], cfg["t_ransomware"]
    if risk >= tr:
        return "Ransomware", "Critical"
    if risk >= ts:
        return "Suspicious", "High" if risk >= (ts + tr) / 2 else "Medium"
    return "Benign", "Low"


def fuse(static: float | None, behavior: float | None, cfg: dict) -> dict:
    parts = [(cfg["w_static"], static), (cfg["w_behavior"], behavior)]
    parts = [(w, s) for w, s in parts if s is not None]
    if not parts:
        raise ValueError("No model produced a score for this file.")
    total = sum(w for w, _ in parts) or 1.0
    risk = min(max(sum(w * s for w, s in parts) / total, 0.0), 1.0)
    label, level = classify(risk, cfg)
    base = max(risk, 1 - risk)
    agreement = 1 - abs(static - behavior) if static is not None and behavior is not None else 1.0
    confidence = base * (0.7 + 0.3 * agreement)  # certainty of the verdict, discounted when the two models disagree
    return {"risk": risk, "label": label, "threat_level": level, "confidence": confidence, "single_model": len(parts) == 1}
