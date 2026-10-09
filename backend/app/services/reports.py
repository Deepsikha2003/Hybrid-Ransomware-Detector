import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models import AnalysisHistory


def _f(v, pct=False):
    return "n/a" if v is None else (f"{v * 100:.1f}%" if pct else f"{v:.4f}")


def build_csv(a: AnalysisHistory) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["file_name", "timestamp", "static_score", "behavior_score", "risk_score", "classification", "threat_level", "confidence", "analyst_notes", "top_shap_features"])
    p, r = a.prediction, a.risk
    shap = (p.shap or {}) if p else {}
    top = "; ".join(f"{k}:{x['feature']}={x['shap']:+.3f}" for k, e in shap.items() for x in e["local"][:5])
    notes = (a.report.analyst_notes if a.report else "").replace("\n", " ")
    # prefix formula-trigger characters so spreadsheet apps don't execute user-controlled text
    safe = lambda s: ("'" + s) if s and s[0] in "=+-@" else s
    w.writerow([safe(a.filename), a.created_at.isoformat(), _f(r.static_score), _f(r.behavior_score), _f(r.final_score), p.label, p.threat_level, _f(p.confidence), safe(notes), top])
    return buf.getvalue()


def build_pdf(a: AnalysisHistory) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    ss = getSampleStyleSheet()
    p, r = a.prediction, a.risk
    esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    story = [Paragraph("Hybrid Ransomware Detection System", ss["Title"]), Paragraph("Threat Analysis Report", ss["Heading2"]), Spacer(1, 6)]
    rows = [["File", esc(a.filename)], ["SHA-256", a.sha256], ["Analysed", a.created_at.strftime("%Y-%m-%d %H:%M UTC")],
            ["Static score", _f(r.static_score)], ["Behavioural score", _f(r.behavior_score)], ["Final risk score", _f(r.final_score)],
            ["Classification", p.label], ["Threat level", p.threat_level], ["Confidence", _f(p.confidence, pct=True)],
            ["Weights", f"static {r.weights['w_static']:.2f} / behaviour {r.weights['w_behavior']:.2f}"],
            ["Thresholds", f"suspicious >= {r.thresholds['t_suspicious']:.2f}, ransomware >= {r.thresholds['t_ransomware']:.2f}"]]
    t = Table(rows, colWidths=[45 * mm, 120 * mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke), ("FONTSIZE", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [t, Spacer(1, 10), Paragraph("Why this classification?", ss["Heading3"]), Paragraph(esc(p.explanation), ss["BodyText"])]
    for key, e in (p.shap or {}).items():
        story += [Spacer(1, 8), Paragraph(f"SHAP - {key} model (top local contributions, log-odds)", ss["Heading4"])]
        data = [["Feature", "Value", "SHAP"]] + [[x["feature"], "missing" if x["value"] is None else f"{x['value']:.4g}", f"{x['shap']:+.4f}"] for x in e["local"][:10]]
        tt = Table(data, colWidths=[85 * mm, 40 * mm, 40 * mm])
        tt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("FONTSIZE", (0, 0), (-1, -1), 8)]))
        story.append(tt)
    notes = a.report.analyst_notes if a.report else ""
    story += [Spacer(1, 10), Paragraph("Analyst notes", ss["Heading3"]), Paragraph(esc(notes) or "<i>None</i>", ss["BodyText"])]
    doc.build(story)
    return buf.getvalue()
