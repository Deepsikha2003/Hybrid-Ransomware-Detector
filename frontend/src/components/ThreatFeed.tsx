import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Empty, LabelBadge, num } from './Ui'

/** Live feed of the most recent verdicts (polls every 5 s). */
export default function ThreatFeed() {
  const { data } = useQuery({ queryKey: ['feed'], queryFn: async () => (await api.get('/threat-feed')).data as any[], refetchInterval: 5000 })
  if (!data?.length) return <Empty>No analyses yet.</Empty>
  return (
    <ul className="space-y-2 max-h-80 overflow-auto pr-1">
      {data.map((e) => (
        <li key={e.id}>
          <Link to={`/results/${e.id}`} className="flex items-center justify-between gap-3 rounded-xl border border-line px-3 py-2 text-sm hover:border-neon/40">
            <div className="min-w-0"><div className="truncate font-medium">{e.filename}</div><div className="text-xs text-muted">{new Date(e.time).toLocaleString()} · risk {num(e.risk, 2)}</div></div>
            <LabelBadge label={e.label} />
          </Link>
        </li>
      ))}
    </ul>
  )
}
