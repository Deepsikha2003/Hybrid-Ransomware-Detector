import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Area, CartesianGrid, ComposedChart, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AlertTriangle, CheckCircle2, FileSearch, Gauge as G, ShieldAlert, Target, UploadCloud } from 'lucide-react'
import { api } from '../api'
import { Card, Empty, LABEL_COLOR, LabelBadge, LevelBadge, StatCard, num, pct } from '../components/Ui'
import ThreatFeed from '../components/ThreatFeed'
import type { Summary } from '../types'

const tip = { background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 12, fontSize: 12 }
const axis = { fill: 'var(--muted)', fontSize: 11 }

export default function Dashboard() {
  const d = useQuery({ queryKey: ['dash'], queryFn: async () => (await api.get('/dashboard')).data, refetchInterval: 15000 })
  const a = useQuery({ queryKey: ['analytics'], queryFn: async () => (await api.get('/analytics')).data, refetchInterval: 15000 })
  const s = d.data
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-2xl font-bold">Security Overview</h1><p className="text-sm text-muted">Hybrid static + behavioural detection across your analyses</p></div>
        <Link to="/analyze" className="btn-primary"><UploadCloud size={16} />New analysis</Link>
      </div>
      {s && !s.models_loaded.length && <div className="rounded-xl border border-warn/40 bg-warn/10 p-3 text-sm text-warn">No trained models are loaded on the server — run the training command from the README before analysing files.</div>}
      {s?.synthetic_models && <div className="rounded-xl border border-warn/40 bg-warn/10 p-3 text-sm text-warn">Demo models trained on synthetic data are loaded. Verdicts are for demonstration only; train on your real datasets for genuine detection.</div>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <StatCard label="Files scanned" value={s?.total ?? '—'} icon={<FileSearch size={18} />} delay={0} />
        <StatCard label="Benign" value={s?.benign ?? '—'} icon={<CheckCircle2 size={18} />} color="#22c55e" delay={0.05} />
        <StatCard label="Suspicious" value={s?.suspicious ?? '—'} icon={<AlertTriangle size={18} />} color="#eab308" delay={0.1} />
        <StatCard label="Ransomware" value={s?.ransomware ?? '—'} icon={<ShieldAlert size={18} />} color="#ef4444" delay={0.15} />
        <StatCard label="Avg risk" value={s ? num(s.avg_risk, 2) : '—'} icon={<G size={18} />} color="#f97316" delay={0.2} />
        <StatCard label="Model accuracy" value={pct(s?.detection_accuracy)} icon={<Target size={18} />} delay={0.25} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Threat distribution">
          {a.data && a.data.distribution.some((x: any) => x.value) ? (
            <ResponsiveContainer width="100%" height={240}><PieChart><Pie data={a.data.distribution} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3}>{a.data.distribution.map((x: any) => <Cell key={x.name} fill={LABEL_COLOR[x.name]} />)}</Pie><Tooltip contentStyle={tip} /><Legend /></PieChart></ResponsiveContainer>
          ) : <Empty>No data yet</Empty>}
        </Card>
        <Card title="Risk trend (daily)" className="lg:col-span-2">
          {a.data?.risk_trend.length ? (
            <ResponsiveContainer width="100%" height={240}><ComposedChart data={a.data.risk_trend}><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22d3ee" stopOpacity={0.5} /><stop offset="100%" stopColor="#22d3ee" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="var(--line)" /><XAxis dataKey="date" tick={axis} /><YAxis domain={[0, 1]} tick={axis} /><Tooltip contentStyle={tip} /><Area type="monotone" dataKey="avg_risk" name="Avg risk" stroke="#22d3ee" fill="url(#g)" /><Line type="monotone" dataKey="max_risk" name="Max risk" stroke="#ef4444" dot={false} /></ComposedChart></ResponsiveContainer>
          ) : <Empty>No data yet</Empty>}
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Model confidence" className="lg:col-span-2">
          {a.data?.confidence.length ? (
            <ResponsiveContainer width="100%" height={230}><LineChart data={a.data.confidence}><CartesianGrid stroke="var(--line)" /><XAxis dataKey="id" tick={axis} /><YAxis domain={[0, 1]} tick={axis} /><Tooltip contentStyle={tip} /><Legend /><Line dataKey="confidence" name="Confidence" stroke="#22d3ee" /><Line dataKey="static" name="Static" stroke="#eab308" dot={false} connectNulls /><Line dataKey="behavior" name="Behaviour" stroke="#f97316" dot={false} connectNulls /></LineChart></ResponsiveContainer>
          ) : <Empty>No data yet</Empty>}
        </Card>
        <Card title="Real-time threat feed"><ThreatFeed /></Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Recent analyses" action={<Link to="/history" className="text-xs text-neon">View all</Link>}>
          {s?.recent.length ? (
            <div className="overflow-x-auto"><table className="w-full text-sm"><tbody>
              {s.recent.map((r: Summary) => (<tr key={r.id} className="border-t border-line"><td className="py-2 pr-2"><Link className="hover:text-neon" to={`/results/${r.id}`}>{r.filename}</Link></td><td className="pr-2 text-muted">{num(r.risk, 2)}</td><td><LabelBadge label={r.label} /></td></tr>))}
            </tbody></table></div>
          ) : <Empty>Upload a file to get started</Empty>}
        </Card>
        <Card title="Threat timeline">
          {a.data?.timeline.length ? (
            <ol className="relative space-y-3 border-l border-line pl-5 max-h-72 overflow-auto">
              {a.data.timeline.map((t: Summary) => (<li key={t.id}><span className="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full" style={{ background: LABEL_COLOR[t.label ?? 'Benign'] }} /><div className="flex flex-wrap items-center gap-2 text-sm"><LevelBadge level={t.threat_level} /><Link to={`/results/${t.id}`} className="hover:text-neon">{t.filename}</Link></div><div className="text-xs text-muted">{new Date(t.created_at).toLocaleString()}</div></li>))}
            </ol>
          ) : <Empty>No events yet</Empty>}
        </Card>
      </div>
    </div>
  )
}
