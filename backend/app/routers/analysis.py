import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..config import settings
from ..database import get_db
from ..deps import audit, current_user, require_roles
from ..ml.features import ALLOWED_EXT, ParseError, parse_upload
from ..ml.pipeline import run_analysis, store
from ..models import AnalysisHistory, Prediction, RiskScore, ThreatReport, User
from ..schemas import NotesIn, PredictIn
from ..services.serializers import detail, summary
from ..services.settings_store import get_fusion_config

router = APIRouter(tags=["analysis"])


def get_visible(db: Session, user: User, analysis_id: int) -> AnalysisHistory:
    a = db.get(AnalysisHistory, analysis_id)
    if not a or (user.role == "user" and a.user_id != user.id):
        raise HTTPException(404, "Analysis not found")  # 404 (not 403) so IDs can't be probed
    return a


def visible_query(db: Session, user: User):
    q = db.query(AnalysisHistory).options(joinedload(AnalysisHistory.prediction), joinedload(AnalysisHistory.risk), joinedload(AnalysisHistory.user))
    return q.filter(AnalysisHistory.user_id == user.id) if user.role == "user" else q


@router.post("/upload", status_code=201)
async def upload(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    name = Path(file.filename or "upload").name[:255]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(415, "Only CSV, TXT and LOG files are accepted")
    limit = settings.max_upload_mb * 1024 * 1024
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    stored = settings.upload_dir / f"{uuid.uuid4().hex}.{ext}"  # server-generated name: never trust the client's
    sha, size = hashlib.sha256(), 0
    with stored.open("wb") as fh:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                fh.close(); stored.unlink(missing_ok=True)
                raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
            sha.update(chunk); fh.write(chunk)
    try:
        df = parse_upload(stored, ext)
    except ParseError as exc:
        stored.unlink(missing_ok=True)
        raise HTTPException(422, str(exc))
    a = AnalysisHistory(user_id=user.id, filename=name, stored_path=str(stored), sha256=sha.hexdigest(), size_bytes=size,
                        file_type=ext, n_rows=len(df), n_cols=df.shape[1])
    db.add(a); db.commit()
    audit(db, request, user, "upload", f"{name} ({size} bytes) id={a.id}")
    preview = df.head(5).astype(object).where(df.head(5).notna(), None).to_dict(orient="records")
    return {"analysis_id": a.id, "filename": name, "size_bytes": size, "rows": len(df), "columns": list(df.columns)[:50], "preview": preview}


@router.post("/predict")
def predict(body: PredictIn, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = get_visible(db, user, body.analysis_id)
    if a.prediction:
        return detail(a)  # idempotent
    if not store.bundles:
        raise HTTPException(503, "No trained models are loaded on the server")
    cfg = get_fusion_config(db)
    try:
        df = parse_upload(Path(a.stored_path), a.file_type)
        res = run_analysis(df, cfg)
    except (ParseError, ValueError) as exc:
        a.status = "failed"; db.commit()
        raise HTTPException(422, str(exc))
    db.add_all([
        Prediction(analysis_id=a.id, label=res["label"], threat_level=res["threat_level"], confidence=res["confidence"],
                   explanation=res["explanation"], shap=res["shap"], details=res["details"]),
        RiskScore(analysis_id=a.id, static_score=res["static_score"], behavior_score=res["behavior_score"], final_score=res["risk"],
                  weights={"w_static": cfg["w_static"], "w_behavior": cfg["w_behavior"]},
                  thresholds={"t_suspicious": cfg["t_suspicious"], "t_ransomware": cfg["t_ransomware"]}),
        ThreatReport(analysis_id=a.id),
    ])
    a.status = "completed"; db.commit(); db.refresh(a)
    audit(db, request, user, "predict", f"id={a.id} label={res['label']} risk={res['risk']:.3f}")
    return detail(a)


@router.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return detail(get_visible(db, user, analysis_id))


@router.post("/analysis/{analysis_id}/notes")
def set_notes(analysis_id: int, body: NotesIn, request: Request, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "analyst"))):
    a = get_visible(db, user, analysis_id)
    if not a.report:
        raise HTTPException(409, "Analysis has not completed")
    a.report.analyst_notes, a.report.updated_by = body.notes, user.id
    db.commit()
    audit(db, request, user, "notes_updated", f"id={a.id}")
    return {"ok": True}


@router.delete("/analysis/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    a = get_visible(db, user, analysis_id)
    Path(a.stored_path).unlink(missing_ok=True)
    db.delete(a); db.commit()
    audit(db, request, user, "analysis_deleted", f"id={analysis_id}")


@router.get("/shap-analysis")
def shap_analysis(analysis_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = get_visible(db, user, analysis_id)
    if not a.prediction:
        raise HTTPException(409, "Analysis has not completed")
    return {"analysis_id": a.id, "explanation": a.prediction.explanation, "shap": a.prediction.shap, "note": "SHAP values are in log-odds (XGBoost margin) space."}


@router.get("/history")
def history(q: str = "", label: str = "", sort: str = Query("new", pattern="^(new|old|risk)$"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
            db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = visible_query(db, user).filter(AnalysisHistory.status == "completed")
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(AnalysisHistory.filename.ilike(like), AnalysisHistory.sha256.ilike(like)))
    if label in ("Benign", "Suspicious", "Ransomware"):
        query = query.join(Prediction).filter(Prediction.label == label)
    total = query.count()
    if sort == "risk":
        query = query.join(RiskScore, isouter=True).order_by(RiskScore.final_score.desc())
    else:
        query = query.order_by(AnalysisHistory.created_at.asc() if sort == "old" else AnalysisHistory.created_at.desc())
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [summary(a) for a in items]}
