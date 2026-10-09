export type Label = 'Benign' | 'Suspicious' | 'Ransomware'
export interface User { id: number; email: string; full_name: string; role: 'admin' | 'analyst' | 'user' }
export interface Summary {
  id: number; filename: string; file_type: string; size_bytes: number; rows: number; status: string; created_at: string; analyst: string | null
  label: Label | null; threat_level: string | null; confidence: number | null; risk: number | null; static_score: number | null; behavior_score: number | null
}
export interface ShapLocal { feature: string; shap: number; value: number | null }
export interface ShapModel { base_value: number; row_index: number; rows_explained: number; local: ShapLocal[]; summary: { feature: string; importance: number }[] }
export interface Detail extends Summary {
  sha256: string; columns: number; explanation?: string; analyst_notes: string
  weights?: { w_static: number; w_behavior: number }; thresholds?: { t_suspicious: number; t_ransomware: number }
  details?: Record<string, any>
}
export interface FusionConfig { w_static: number; w_behavior: number; t_suspicious: number; t_ransomware: number }
