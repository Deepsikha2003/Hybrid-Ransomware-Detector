import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ShapModel } from '../types'

const tip = { background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 12, fontSize: 12 }

/** Waterfall of local SHAP contributions (log-odds): starts at the base value, ends at the model output f(x). */
export function Waterfall({ data }: { data: ShapModel }) {
  let run = data.base_value
  const rows = data.local.slice(0, 10).map((f) => {
    const start = run; run += f.shap
    return { name: f.feature, base: Math.min(start, run), delta: Math.abs(f.shap), up: f.shap > 0, shap: f.shap, value: f.value }
  })
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, rows.length * 32)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 10, right: 20 }}>
        <XAxis type="number" domain={['auto', 'auto']} tick={{ fill: 'var(--muted)', fontSize: 11 }} />
        <YAxis type="category" dataKey="name" width={150} tick={{ fill: 'var(--fg)', fontSize: 11 }} />
        <Tooltip contentStyle={tip} formatter={(_: any, __: any, p: any) => [`${p.payload.shap > 0 ? '+' : ''}${p.payload.shap.toFixed(3)} (value ${p.payload.value ?? 'missing'})`, 'SHAP']} />
        <Bar dataKey="base" stackId="a" fill="transparent" />
        <Bar dataKey="delta" stackId="a" radius={4}>{rows.map((r, i) => <Cell key={i} fill={r.up ? '#ef4444' : '#22c55e'} />)}</Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Global summary: mean |SHAP| over the most suspicious rows in the upload. */
export function Summary({ data }: { data: ShapModel }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.summary.length * 28)}>
      <BarChart data={data.summary} layout="vertical" margin={{ left: 10, right: 20 }}>
        <XAxis type="number" tick={{ fill: 'var(--muted)', fontSize: 11 }} />
        <YAxis type="category" dataKey="feature" width={150} tick={{ fill: 'var(--fg)', fontSize: 11 }} />
        <Tooltip contentStyle={tip} formatter={(v: number) => v.toFixed(4)} />
        <Bar dataKey="importance" fill="#22d3ee" radius={4} />
      </BarChart>
    </ResponsiveContainer>
  )
}
