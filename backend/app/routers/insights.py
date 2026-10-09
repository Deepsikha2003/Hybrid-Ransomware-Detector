from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import current_user
from ..ml.pipeline import store
from ..models import ModelMetadata, User
from ..services.serializers import summary
from .analysis import visible_query

router = APIRouter(tags=["insights"])

# Figures reported in the research study this project is based on (shown alongside live metrics).
REPORTED = [
    {"model": "Random Forest", "dataset": "Behavioral", "accuracy": 0.938},
    {"model": "SVM", "dataset": "Static", "accuracy": 0.9949},
    {"model": "XGBoost", "dataset": "Static", "accuracy": 0.9988},
    {"model": "XGBoost", "dataset": "Behavioral", "accuracy": 0.9809},
]


def _completed(db, user):
    return [a for a in visible_query(db, user).all() if a.status == "completed" and a.prediction and a.risk]


def _live_accuracy():
    accs = [b["metrics"]["accuracy"] for b in store.bundles.values()]
    return sum(accs) / len(accs) if accs else None


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    items = sorted(_completed(db, user), key=lambda a: a.created_at, reverse=True)
    counts = defaultdict(int)
    for a in items:
        counts[a.prediction.label] += 1
    avg = sum(a.risk.final_score for a in items) / len(items) if items else 0.0
    return {
        "total": len(items), "benign": counts["Benign"], "suspicious": counts["Suspicious"], "ransomware": counts["Ransomware"],
        "avg_risk": avg, "detection_accuracy": _live_accuracy(),
        "models_loaded": list(store.bundles), "synthetic_models": any(b.get("synthetic") for b in store.bundles.values()),
        "recent": [summary(a) for a in items[:8]],
    }


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), user: User = Depends(current_user)):
    items = sorted(_completed(db, user), key=lambda a: a.created_at)
    dist = defaultdict(int)
    daily = defaultdict(list)
    for a in items:
        dist[a.prediction.label] += 1
        daily[a.created_at.strftime("%Y-%m-%d")].append(a.risk.final_score)
    return {
        "distribution": [{"name": k, "value": dist[k]} for k in ("Benign", "Suspicious", "Ransomware")],
        "risk_trend": [{"date": d, "avg_risk": sum(v) / len(v), "max_risk": max(v), "count": len(v)} for d, v in sorted(daily.items())][-30:],
        "confidence": [{"id": a.id, "confidence": a.prediction.confidence, "static": a.risk.static_score, "behavior": a.risk.behavior_score} for a in items[-30:]],
        "timeline": [summary(a) for a in reversed(items[-20:])],
    }


@router.get("/threat-feed")
def threat_feed(db: Session = Depends(get_db), user: User = Depends(current_user)):
    items = sorted(_completed(db, user), key=lambda a: a.created_at, reverse=True)[:15]
    return [{"id": a.id, "time": a.created_at.isoformat(), "filename": a.filename, "label": a.prediction.label, "level": a.prediction.threat_level, "risk": a.risk.final_score} for a in items]


@router.get("/model-performance")
def model_performance(db: Session = Depends(get_db)):
    live = []
    for name, b in store.bundles.items():
        live.append({"name": name, "algorithm": "XGBoost", "synthetic": bool(b.get("synthetic")), "trained_at": b.get("trained_at"),
                     "n_features": len(b["features"]), **b["metrics"]})
    return {"reported": REPORTED, "live": live}
