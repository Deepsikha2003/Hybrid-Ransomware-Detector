import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

const R = 80, C = 100
const pt = (v: number, r = R) => [C - r * Math.cos(Math.PI * v), C - r * Math.sin(Math.PI * v)]
const arc = (a: number, b: number) => {
  const [x1, y1] = pt(a), [x2, y2] = pt(b)
  return `M ${x1} ${y1} A ${R} ${R} 0 0 1 ${x2} ${y2}`
}

/** Semicircular risk gauge. Bands follow the admin-configured thresholds; the needle animates to `value` (0..1). */
export default function Gauge({ value, tSusp = 0.4, tRansom = 0.8, label, color }: { value: number; tSusp?: number; tRansom?: number; label?: string; color: string }) {
  const mid = (tSusp + tRansom) / 2
  const bands: [number, number, string][] = [[0, tSusp, '#22c55e'], [tSusp, mid, '#eab308'], [mid, tRansom, '#f97316'], [tRansom, 1, '#ef4444']]
  const v = Math.min(Math.max(value, 0), 1)

  // Needle position (0..1): plain requestAnimationFrame tween, tip computed with sin/cos.
  const [pos, setPos] = useState(0)
  useEffect(() => {
    let raf = 0
    const t0 = performance.now() + 300, dur = 1300
    const step = (now: number) => {
      const t = Math.min(Math.max((now - t0) / dur, 0), 1)
      setPos(v * (1 - Math.pow(1 - t, 3)))   // ease-out
      if (t < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [v])
  const [tx, ty] = pt(pos, 68)

  return (
    <div className="mx-auto w-full max-w-sm">
      <svg viewBox="0 0 200 120" className="w-full overflow-visible" role="img" aria-label={`Risk score ${v.toFixed(2)}`}>
        <path d={arc(0, 1)} stroke="var(--line)" strokeWidth="16" fill="none" />
        {bands.map(([a, b, c]) => (
          <motion.path key={c} d={arc(a, b)} stroke={c} strokeWidth="14" fill="none" opacity={0.9}
            initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.9 }} />
        ))}
        <line x1={C} y1={C} x2={tx} y2={ty} stroke={color} strokeWidth="3" strokeLinecap="round" />
        <circle cx={tx} cy={ty} r="4" fill={color} />
        <circle cx={C} cy={C} r="7" fill={color} />
        <text x="100" y="86" textAnchor="middle" fontSize="22" fontWeight="700" fill={color}>{v.toFixed(2)}</text>
        <text x="100" y="116" textAnchor="middle" fontSize="9" fill="var(--muted)">{label ?? 'RISK SCORE'}</text>
      </svg>
    </div>
  )
}