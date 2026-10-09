import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { useAuth } from '../auth'
import Layout, { PublicShell } from '../components/Layout'
import { Card, Empty, pct } from '../components/Ui'

const tip = { background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 12, fontSize: 12 }

function ConfusionMatrix({ m }: { m: number[][] }) {
  const labels = [['TN', 'FP'], ['FN', 'TP']]
  const max = Math.max(...m.flat(), 1)
  return (
    <div className="mx-auto grid max-w-xs grid-cols-2 gap-2 text-center">
      {m.map((row, i) => row.map((v, j) => (
        <div key={`${i}${j}`} className="rounded-xl p-4" style={{ background: `rgba(${i === j ? '34,211,238' : '239,68,68'},${0.12 + 0.6 * (v / max)})` }}>
          <div className="text-2xl font-bold">{v}</div><div className="text-xs text-muted">{labels[i][j]}</div></div>)))}
    </div>
  )
}

export default function Performance() {
  const { user } = useAuth()
  const { data } = useQuery({ queryKey: ['perf'], queryFn: async () => (await api.get('/model-performance')).data })
  const body = (
    <div className="mx-auto max-w-6xl space-y-6 px-5 py-6">
      <div><h1 className="text-2xl font-bold">Model performance</h1><p className="text-sm text-muted">Comparison of classifiers and live metrics of the models currently deployed.</p></div>
      <Card title="Model comparison (reported in the research study)">
        <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="text-left text-xs uppercase text-muted"><tr><th className="pb-2">Model</th><th>Dataset</th><th>Accuracy</th></tr></thead>
          <tbody>{data?.reported.map((r: any) => (<tr key={r.model + r.dataset} className="border-t border-line"><td className="py-2">{r.model}</td><td>{r.dataset}</td><td className="font-semibold text-neon">{(r.accuracy * 100).toFixed(2)}%</td></tr>))}</tbody></table></div>
      </Card>
      {!data?.live.length && <Card><Empty>No models loaded on the server. Train models to see live precision, recall, F1, ROC and confusion matrices.</Empty></Card>}
      {data?.live.map((m: any) => (
        <div key={m.name} className="space-y-4">
          <h2 className="text-lg font-semibold capitalize">Deployed {m.name} model (XGBoost) {m.synthetic && <span className="ml-2 rounded-full bg-warn/15 px-2 py-0.5 text-xs text-warn">synthetic demo data</span>}</h2>
          <div className="grid gap-4 sm:grid-cols-5">
            {[['Accuracy', m.accuracy], ['Precision', m.precision], ['Recall', m.recall], ['F1 score', m.f1], ['ROC AUC', m.roc_auc]].map(([k, v]) => (
              <div key={k as string} className="glass p-4 text-center"><div className="text-xs uppercase text-muted">{k}</div><div className="mt-1 text-2xl font-bold text-neon">{pct(v as number, 2)}</div></div>))}
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <Card title="Confusion matrix (hold-out)"><ConfusionMatrix m={m.confusion_matrix} /></Card>
            <Card title="ROC curve"><ResponsiveContainer width="100%" height={240}><LineChart data={m.roc.fpr.map((x: number, i: number) => ({ fpr: x, tpr: m.roc.tpr[i] }))}><CartesianGrid stroke="var(--line)" /><XAxis dataKey="fpr" type="number" domain={[0, 1]} tick={{ fill: 'var(--muted)', fontSize: 11 }} /><YAxis domain={[0, 1]} tick={{ fill: 'var(--muted)', fontSize: 11 }} /><Tooltip contentStyle={tip} formatter={(v: number) => v.toFixed(3)} /><Line dataKey="tpr" stroke="#22d3ee" dot={false} strokeWidth={2} /></LineChart></ResponsiveContainer></Card>
            <Card title="Feature importance"><ResponsiveContainer width="100%" height={260}><BarChart data={m.feature_importance.slice(0, 10)} layout="vertical" margin={{ left: 10 }}><XAxis type="number" tick={{ fill: 'var(--muted)', fontSize: 11 }} /><YAxis type="category" dataKey="feature" width={130} tick={{ fill: 'var(--fg)', fontSize: 10 }} /><Tooltip contentStyle={tip} /><Bar dataKey="importance" fill="#22d3ee" radius={4} /></BarChart></ResponsiveContainer></Card>
          </div>
        </div>
      ))}
    </div>
  )
  return user ? <Layout>{body}</Layout> : <PublicShell>{body}</PublicShell>
}
