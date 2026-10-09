from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import audit, current_user
from ..models import User
from ..services.reports import build_csv, build_pdf
from ..services.serializers import summary
from .analysis import get_visible, visible_query
from fastapi import HTTPException

router = APIRouter(tags=["reports"])


def _ready(db, user, analysis_id):
    a = get_visible(db, user, analysis_id)
    if not (a.prediction and a.risk):
        raise HTTPException(409, "Analysis has not completed")
    return a


@router.get("/reports")
def list_reports(db: Session = Depends(get_db), user: User = Depends(current_user)):
    items = [a for a in visible_query(db, user).all() if a.report and a.prediction]
    items.sort(key=lambda a: a.created_at, reverse=True)
    return [{**summary(a), "has_notes": bool(a.report.analyst_notes)} for a in items[:200]]


@router.get("/reports/{analysis_id}/pdf")
def pdf(analysis_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = _ready(db, user, analysis_id)
    audit(db, request, user, "report_pdf", f"id={a.id}")
    return Response(build_pdf(a), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="report_{a.id}.pdf"'})


@router.get("/reports/{analysis_id}/csv")
def csv_report(analysis_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = _ready(db, user, analysis_id)
    audit(db, request, user, "report_csv", f"id={a.id}")
    return Response(build_csv(a), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="report_{a.id}.csv"'})
