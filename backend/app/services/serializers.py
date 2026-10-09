from ..models import AnalysisHistory


def summary(a: AnalysisHistory) -> dict:
    p, r = a.prediction, a.risk
    return {
        "id": a.id, "filename": a.filename, "file_type": a.file_type, "size_bytes": a.size_bytes,
        "rows": a.n_rows, "status": a.status, "created_at": a.created_at.isoformat(), "analyst": a.user.email if a.user else None,
        "label": p.label if p else None, "threat_level": p.threat_level if p else None,
        "confidence": p.confidence if p else None, "risk": r.final_score if r else None,
        "static_score": r.static_score if r else None, "behavior_score": r.behavior_score if r else None,
    }


def detail(a: AnalysisHistory) -> dict:
    d = summary(a)
    d["sha256"] = a.sha256
    d["columns"] = a.n_cols
    if a.prediction:
        d["explanation"], d["details"] = a.prediction.explanation, a.prediction.details
    if a.risk:
        d["weights"], d["thresholds"] = a.risk.weights, a.risk.thresholds
    d["analyst_notes"] = a.report.analyst_notes if a.report else ""
    return d
