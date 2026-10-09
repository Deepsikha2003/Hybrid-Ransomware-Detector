import { ReactNode } from 'react'
import { motion } from 'framer-motion'

export const LABEL_COLOR: Record<string, string> = { Benign: '#22c55e', Suspicious: '#eab308', Ransomware: '#ef4444' }
export const LEVEL_COLOR: Record<string, string> = { Low: '#22c55e', Medium: '#eab308', High: '#f97316', Critical: '#ef4444' }
export const pct = (v: number | null | undefined, d = 1) => (v == null ? '—' : `${(v * 100).toFixed(d)}%`)
export const num = (v: number | null | undefined, d = 3) => (v == null ? '—' : v.toFixed(d))

export function Badge({ text, color }: { text: string; color: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold" style={{ color, background: `${color}1f`, border: `1px solid ${color}55` }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />{text}
    </span>
  )
}
export const LabelBadge = ({ label }: { label: string | null }) => (label ? <Badge text={label} color={LABEL_COLOR[label]} /> : <span className="text-muted">—</span>)
export const LevelBadge = ({ level }: { level: string | null }) => (level ? <Badge text={level} color={LEVEL_COLOR[level]} /> : <span className="text-muted">—</span>)

export function Card({ title, children, className = '', action }: { title?: string; children: ReactNode; className?: string; action?: ReactNode }) {
  return (
    <div className={`glass p-5 ${className}`}>
      {(title || action) && <div className="mb-4 flex items-center justify-between"><h3 className="text-sm font-semibold tracking-wide text-muted uppercase">{title}</h3>{action}</div>}
      {children}
    </div>
  )
}

export function StatCard({ label, value, icon, color = '#22d3ee', delay = 0 }: { label: string; value: ReactNode; icon: ReactNode; color?: string; delay?: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.4 }} className="glass glass-hover p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted uppercase tracking-wide">{label}</span>
        <span className="rounded-lg p-2" style={{ color, background: `${color}1a` }}>{icon}</span>
      </div>
      <div className="mt-3 text-3xl font-bold" style={{ color }}>{value}</div>
    </motion.div>
  )
}

export const Empty = ({ children }: { children: ReactNode }) => <div className="py-10 text-center text-sm text-muted">{children}</div>
export const ErrorBox = ({ msg }: { msg: string }) => <div className="rounded-xl border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{msg}</div>
