from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin | analyst | user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    file_type: Mapped[str] = mapped_column(String(8))
    n_rows: Mapped[int] = mapped_column(Integer, default=0)
    n_cols: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="uploaded")  # uploaded | completed | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    user: Mapped[User] = relationship()
    prediction: Mapped[Optional["Prediction"]] = relationship(back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    risk: Mapped[Optional["RiskScore"]] = relationship(back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    report: Mapped[Optional["ThreatReport"]] = relationship(back_populates="analysis", uselist=False, cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analysis_history.id", ondelete="CASCADE"), unique=True)
    label: Mapped[str] = mapped_column(String(16), index=True)  # Benign | Suspicious | Ransomware
    threat_level: Mapped[str] = mapped_column(String(16))  # Low | Medium | High | Critical
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, default="")
    shap: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    analysis: Mapped[AnalysisHistory] = relationship(back_populates="prediction")


class RiskScore(Base):
    __tablename__ = "risk_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analysis_history.id", ondelete="CASCADE"), unique=True)
    static_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    behavior_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_score: Mapped[float] = mapped_column(Float, index=True)
    weights: Mapped[dict] = mapped_column(JSON)
    thresholds: Mapped[dict] = mapped_column(JSON)
    analysis: Mapped[AnalysisHistory] = relationship(back_populates="risk")


class ThreatReport(Base):
    __tablename__ = "threat_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analysis_history.id", ondelete="CASCADE"), unique=True)
    analyst_notes: Mapped[str] = mapped_column(Text, default="")
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    analysis: Mapped[AnalysisHistory] = relationship(back_populates="report")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    ip: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


class ModelMetadata(Base):
    __tablename__ = "model_metadata"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)  # static | behavior
    algorithm: Mapped[str] = mapped_column(String(32), default="XGBoost")
    version: Mapped[str] = mapped_column(String(32), default="1")
    trained_at: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    features: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
