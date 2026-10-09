-- Reference DDL (PostgreSQL). The app creates these tables automatically on startup via SQLAlchemy;
-- use this file to review the design or to bootstrap manually / migrate with Alembic.
CREATE TABLE users (
  id            SERIAL PRIMARY KEY,
  email         VARCHAR(255) NOT NULL UNIQUE,
  full_name     VARCHAR(120) NOT NULL DEFAULT '',
  password_hash VARCHAR(255) NOT NULL,
  role          VARCHAR(20)  NOT NULL DEFAULT 'user' CHECK (role IN ('admin','analyst','user')),
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE analysis_history (
  id          SERIAL PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id),
  filename    VARCHAR(255) NOT NULL,
  stored_path VARCHAR(512) NOT NULL,
  sha256      VARCHAR(64)  NOT NULL,
  size_bytes  INTEGER NOT NULL,
  file_type   VARCHAR(8)  NOT NULL,
  n_rows      INTEGER NOT NULL DEFAULT 0,
  n_cols      INTEGER NOT NULL DEFAULT 0,
  status      VARCHAR(16) NOT NULL DEFAULT 'uploaded',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_analysis_user ON analysis_history(user_id);
CREATE INDEX ix_analysis_sha ON analysis_history(sha256);
CREATE INDEX ix_analysis_created ON analysis_history(created_at);

CREATE TABLE predictions (
  id           SERIAL PRIMARY KEY,
  analysis_id  INTEGER NOT NULL UNIQUE REFERENCES analysis_history(id) ON DELETE CASCADE,
  label        VARCHAR(16) NOT NULL CHECK (label IN ('Benign','Suspicious','Ransomware')),
  threat_level VARCHAR(16) NOT NULL,
  confidence   DOUBLE PRECISION NOT NULL,
  explanation  TEXT NOT NULL DEFAULT '',
  shap         JSON,
  details      JSON,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_predictions_label ON predictions(label);

CREATE TABLE risk_scores (
  id             SERIAL PRIMARY KEY,
  analysis_id    INTEGER NOT NULL UNIQUE REFERENCES analysis_history(id) ON DELETE CASCADE,
  static_score   DOUBLE PRECISION,
  behavior_score DOUBLE PRECISION,
  final_score    DOUBLE PRECISION NOT NULL,
  weights        JSON NOT NULL,
  thresholds     JSON NOT NULL
);
CREATE INDEX ix_risk_final ON risk_scores(final_score);

CREATE TABLE threat_reports (
  id            SERIAL PRIMARY KEY,
  analysis_id   INTEGER NOT NULL UNIQUE REFERENCES analysis_history(id) ON DELETE CASCADE,
  analyst_notes TEXT NOT NULL DEFAULT '',
  updated_by    INTEGER REFERENCES users(id),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
  id         SERIAL PRIMARY KEY,
  user_id    INTEGER REFERENCES users(id),
  action     VARCHAR(64) NOT NULL,
  detail     TEXT NOT NULL DEFAULT '',
  ip         VARCHAR(64) NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_action ON audit_logs(action);
CREATE INDEX ix_audit_created ON audit_logs(created_at);

CREATE TABLE model_metadata (
  id         SERIAL PRIMARY KEY,
  name       VARCHAR(32) NOT NULL UNIQUE,       -- 'static' | 'behavior'
  algorithm  VARCHAR(32) NOT NULL DEFAULT 'XGBoost',
  version    VARCHAR(32) NOT NULL DEFAULT '1',
  trained_at VARCHAR(40),
  synthetic  BOOLEAN NOT NULL DEFAULT FALSE,
  metrics    JSON,
  features   JSON
);

CREATE TABLE system_settings (                 -- admin-editable fusion weights + thresholds
  key   VARCHAR(64) PRIMARY KEY,
  value JSON NOT NULL
);
