import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Download, FileText } from 'lucide-react'
import { api, download, errMsg } from '../api'
import { useAuth } from '../auth'
import Gauge from '../components/Gauge'
import { Summary as ShapSummary, Waterfall } from '../components/ShapCharts'
import { Card, ErrorBox, LABEL_COLOR, LabelBadge, LevelBadge, num, pct } from '../components/Ui'
import type { Detail, ShapModel } from '../types'

export default function Results() {
  const { id } = useParams(); const { user } = useAuth(); const qc = useQueryClient()
  const q = useQuery({ queryKey: ['analysis', id], queryFn: async () => (await api.get(`/analysis/${id}`)).data as Detail })
  const shap = useQuery({ queryKey: ['shap', id], queryFn: async () => (await api.get('/shap-analysis', { params: { analysis_id: id } })).data, enabled: !!q.data?.label })
  const [notes, setNotes] = useState<string | null>(null)
  const save = useMutation({ mutationFn: async () => api.post(`/analysis/${id}/notes`, { notes: notes ?? '' }), onSuccess: () => qc.invalidateQueries({ queryKey: ['analysis', id] }) })
  const [tab, setTab] = useState<'static' | 'behavior'>('static')

  if (q.isLoading) return <div className="text-muted">Loading…</div>
  if (q.error || !q.data) return <ErrorBox msg={errMsg(q.error)} />
  const d = q.data
  if (!d.label) return <ErrorBox msg="This analysis has not completed." />
  const color = LABEL_COLOR[d.label]
  const models = Object.keys(shap.data?.shap ?? {}) as ('static' | 'behavior')[]
  const active = (models.includes(tab) ? tab : models[0]) as 'static' | 'behavior'
  const sm: ShapModel | undefined = shap.data?.shap?.[active]
  const canNote = user?.role === 'admin' || user?.role === 'analyst'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div><h1 className="text-2xl font-bold">Analysis result</h1><p className="text-sm text-muted break-all">{d.filename}</p></div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => download(`/reports/${d.id}/pdf`, `report_${d.id}.pdf`)}><FileText size={15} />Export PDF</button>
          <button className="btn-ghost" onClick={() => download(`/reports/${d.id}/csv`, `report_${d.id}.csv`)}><Download size={15} />Export CSV</button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Final risk" className="lg:col-span-1"><Gauge value={d.risk ?? 0} tSusp={d.thresholds?.t_suspicious} tRansom={d.thresholds?.t_ransomware} color={color} />
          <div className="mt-2 text-center"><div className="text-2xl font-extrabold" style={{ color }}>{d.label}</div></div></Card>
        <Card title="Verdict" className="lg:col-span-2">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 text-sm">
            <div><dt className="text-muted">Risk score</dt><dd className="text-xl font-bold">{num(d.risk, 2)}</dd></div>
            <div><dt className="text-muted">Prediction</dt><dd className="mt-1"><LabelBadge label={d.label} /></dd></div>
            <div><dt className="text-muted">Threat level</dt><dd className="mt-1"><LevelBadge level={d.threat_level} /></dd></div>
            <div><dt className="text-muted">Confidence</dt><dd className="text-xl font-bold">{pct(d.confidence)}</dd></div>
            <div><dt className="text-muted">Static score</dt><dd className="text-xl font-bold">{num(d.static_score, 3)}</dd></div>
            <div><dt className="text-muted">Behavioural score</dt><dd className="text-xl font-bold">{num(d.behavior_score, 3)}</dd></div>
          </dl>
          {(d.static_score == null || d.behavior_score == null) && <p className="mt-4 rounded-lg border border-warn/40 bg-warn/10 p-2 text-xs text-warn">Only one model could score this file (the uploaded columns did not match the other model's features), so the final score uses that model alone.</p>}
          <p className="mt-4 text-xs text-muted">Fusion: static {d.weights?.w_static.toFixed(2)} / behaviour {d.weights?.w_behavior.toFixed(2)} · thresholds {d.thresholds?.t_suspicious.toFixed(2)} / {d.thresholds?.t_ransomware.toFixed(2)}</p>
        </Card>
      </div>

      <Card title="File information">
        <dl className="grid gap-4 text-sm sm:grid-cols-4">
          <div><dt className="text-muted">Name</dt><dd className="break-all">{d.filename}</dd></div>
          <div><dt className="text-muted">Type / size</dt><dd>{d.file_type.toUpperCase()} · {(d.size_bytes / 1024).toFixed(1)} KB</dd></div>
          <div><dt className="text-muted">Rows × columns</dt><dd>{d.rows} × {d.columns}</dd></div>
          <div><dt className="text-muted">Analysed</dt><dd>{new Date(d.created_at).toLocaleString()}</dd></div>
          <div className="sm:col-span-4"><dt className="text-muted">SHA-256</dt><dd className="break-all font-mono text-xs">{d.sha256}</dd></div>
        </dl>
      </Card>

      <Card title={`Why was this file classified as ${d.label.toLowerCase()}?`}>
        <p className="leading-relaxed">{d.explanation}</p>
      </Card>

      {sm && (
        <div className="space-y-4">
          {models.length > 1 && <div className="flex gap-2">{models.map((m) => <button key={m} onClick={() => setTab(m)} className={active === m ? 'btn-primary' : 'btn-ghost'}>{m === 'static' ? 'Static model' : 'Behavioural model'}</button>)}</div>}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="SHAP waterfall (local, log-odds)"><Waterfall data={sm} /><p className="mt-2 text-xs text-muted">Red pushes toward ransomware, green toward benign. Explains the most suspicious row (#{sm.row_index + 1}).</p></Card>
            <Card title="SHAP summary (mean |SHAP|)"><ShapSummary data={sm} /><p className="mt-2 text-xs text-muted">Across the {sm.rows_explained} most suspicious row(s).</p></Card>
          </div>
        </div>
      )}

      <Card title="Analyst notes">
        {canNote ? (<><textarea className="input min-h-28" value={notes ?? d.analyst_notes} onChange={(e) => setNotes(e.target.value)} maxLength={5000} />
          <div className="mt-3 flex items-center gap-3"><button className="btn-primary" disabled={save.isPending} onClick={() => save.mutate()}>Save notes</button>{save.isSuccess && <span className="text-xs text-safe">Saved</span>}{save.isError && <span className="text-xs text-danger">{errMsg(save.error)}</span>}</div></>)
          : <p className="text-sm text-muted whitespace-pre-wrap">{d.analyst_notes || 'No notes. Analysts and admins can add notes.'}</p>}
      </Card>
    </div>
  )
}
