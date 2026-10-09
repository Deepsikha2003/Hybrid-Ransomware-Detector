import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, Cpu, FileSearch, Gauge as GaugeIcon, Layers, Lock, Radar, ShieldCheck } from 'lucide-react'
import { PublicShell } from '../components/Layout'

const floaters = [
  { Icon: Lock, x: '8%', y: '22%', d: 0 }, { Icon: ShieldCheck, x: '86%', y: '18%', d: 1 }, { Icon: Radar, x: '12%', y: '70%', d: 2 },
  { Icon: Cpu, x: '82%', y: '66%', d: 0.5 }, { Icon: FileSearch, x: '48%', y: '8%', d: 1.5 },
]
const stages = [
  { Icon: FileSearch, t: 'Static Analysis', d: 'PE headers, DLL imports, section entropy — inspected before execution (XGBoost).' },
  { Icon: Cpu, t: 'Behavioural Analysis', d: 'Process, file, registry and network events from Sysmon-style telemetry (XGBoost).' },
  { Icon: Layers, t: 'Hybrid Fusion', d: 'Final Risk = 0.6 × Static + 0.4 × Behaviour. Weights and thresholds are admin-configurable.' },
  { Icon: GaugeIcon, t: 'Risk Engine', d: 'Benign < 0.40 ≤ Suspicious < 0.80 ≤ Ransomware, with threat level and confidence.' },
  { Icon: Brain, t: 'Explainable AI', d: 'SHAP shows exactly which features drove each verdict.' },
]

export default function Landing() {
  return (
    <PublicShell>
      <section className="relative overflow-hidden px-6 pb-24 pt-16 text-center">
        <div className="grid-bg absolute inset-0 -z-10" />
        <motion.div className="absolute left-1/2 top-0 -z-10 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-neon/20 blur-[120px]" animate={{ scale: [1, 1.15, 1] }} transition={{ duration: 8, repeat: Infinity }} />
        {floaters.map(({ Icon, x, y, d }, i) => (
          <motion.div key={i} className="absolute -z-10 hidden text-neon/40 md:block" style={{ left: x, top: y }} animate={{ y: [0, -18, 0], rotate: [0, 6, 0] }} transition={{ duration: 6, repeat: Infinity, delay: d }}><Icon size={38} /></motion.div>
        ))}
        <motion.svg initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} viewBox="0 0 120 140" className="mx-auto mb-6 h-28 drop-shadow-[0_0_24px_rgba(34,211,238,.6)]">
          <path d="M60 6 L108 24 V68 C108 100 86 124 60 134 C34 124 12 100 12 68 V24 Z" fill="rgba(34,211,238,.08)" stroke="#22d3ee" strokeWidth="3" />
          <rect x="40" y="62" width="40" height="32" rx="5" fill="none" stroke="#22d3ee" strokeWidth="3" />
          <path d="M46 62 V52 a14 14 0 0 1 28 0 V62" fill="none" stroke="#22d3ee" strokeWidth="3" />
          <circle cx="60" cy="78" r="4" fill="#22d3ee" />
        </motion.svg>
        <motion.h1 initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="mx-auto max-w-4xl text-4xl font-extrabold tracking-tight sm:text-6xl">
          Hybrid <span className="bg-gradient-to-r from-neon to-blue-500 bg-clip-text text-transparent">Ransomware</span> Detection System
        </motion.h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-muted">AI-Powered Threat Intelligence Using Hybrid Machine Learning</p>
        <div className="mt-9 flex flex-wrap justify-center gap-3">
          <Link to="/analyze" className="btn-primary">Start Analysis</Link>
          <a href="#architecture" className="btn-ghost">View Architecture</a>
          <Link to="/performance" className="btn-ghost">Model Performance</Link>
        </div>
      </section>

      <section id="architecture" className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="mb-2 text-center text-3xl font-bold">How it works</h2>
        <p className="mb-10 text-center text-muted">Behaviour and structure instead of signatures — so novel variants are still caught.</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {stages.map(({ Icon, t, d }, i) => (
            <motion.div key={t} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }} className="glass glass-hover p-5">
              <div className="mb-3 inline-flex rounded-xl bg-neon/10 p-2.5 text-neon"><Icon size={20} /></div>
              <div className="text-xs font-semibold text-neon">STEP {i + 1}</div>
              <h3 className="mb-1 font-semibold">{t}</h3><p className="text-sm text-muted">{d}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </PublicShell>
  )
}
