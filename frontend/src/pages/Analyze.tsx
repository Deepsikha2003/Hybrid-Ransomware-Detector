import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckCircle2, FileUp, Loader2 } from 'lucide-react'
import { api, errMsg } from '../api'
import { Card, ErrorBox } from '../components/Ui'

const STEPS = ['Validate file', 'Extract features', 'Static model', 'Behavioural model', 'Hybrid fusion', 'SHAP explanation']

export default function Analyze() {
  const nav = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [err, setErr] = useState('')
  const [step, setStep] = useState(-1)
  const [preview, setPreview] = useState<any>(null)
  const [over, setOver] = useState(false)

  const run = useCallback(async (f: File) => {
    setErr(''); setPreview(null); setFile(f); setStep(0)
    const ext = f.name.split('.').pop()?.toLowerCase()
    if (!['csv', 'txt', 'log'].includes(ext ?? '')) { setErr('Only CSV, TXT and LOG files are supported.'); setStep(-1); return }
    try {
      const fd = new FormData(); fd.append('file', f)
      const up = (await api.post('/upload', fd)).data
      setPreview(up); setStep(2)
      const tick = setInterval(() => setStep((s) => Math.min(s + 1, 5)), 700)  // visual progress only; the server runs the pipeline in one request
      try {
        const res = (await api.post('/predict', { analysis_id: up.analysis_id })).data
        nav(`/results/${res.id}`)
      } finally { clearInterval(tick) }
    } catch (e) { setErr(errMsg(e)); setStep(-1) }
  }, [nav])

  const onDrop = (e: React.DragEvent) => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files?.[0]; if (f) run(f) }
  const busy = step >= 0

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div><h1 className="text-2xl font-bold">New analysis</h1><p className="text-sm text-muted">Upload extracted feature data (CSV) or Sysmon-style event logs (TXT / LOG). Files are parsed as data and never executed.</p></div>
      <label onDragOver={(e) => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)} onDrop={onDrop}
        className={`glass flex cursor-pointer flex-col items-center justify-center gap-3 border-2 border-dashed p-12 text-center transition ${over ? 'border-neon bg-neon/5' : 'border-line hover:border-neon/50'} ${busy ? 'pointer-events-none opacity-70' : ''}`}>
        <motion.div animate={{ y: over ? -6 : 0 }}><FileUp size={44} className="text-neon" /></motion.div>
        <div className="font-semibold">{file ? file.name : 'Drag & drop a file here, or click to browse'}</div>
        <div className="text-xs text-muted">CSV · TXT · LOG — up to 20 MB</div>
        <input type="file" accept=".csv,.txt,.log" className="hidden" onChange={(e) => e.target.files?.[0] && run(e.target.files[0])} />
      </label>
      {err && <ErrorBox msg={err} />}
      {busy && (
        <Card title="Analysis pipeline">
          <ul className="space-y-2">{STEPS.map((s, i) => (
            <li key={s} className={`flex items-center gap-3 text-sm ${i <= step ? '' : 'text-muted'}`}>
              {i < step ? <CheckCircle2 size={16} className="text-safe" /> : i === step ? <Loader2 size={16} className="animate-spin text-neon" /> : <span className="h-4 w-4 rounded-full border border-line" />}{s}
            </li>))}
          </ul>
          {preview && <p className="mt-4 text-xs text-muted">{preview.rows} row(s) · {preview.columns.length} column(s) detected</p>}
        </Card>
      )}
    </div>
  )
}
