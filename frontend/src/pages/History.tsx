import { useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Download, Search } from 'lucide-react'
import { api, download } from '../api'
import { Card, Empty, LabelBadge, LevelBadge, num, pct } from '../components/Ui'
import type { Summary } from '../types'

export default function History() {
  const [q, setQ] = useState(''), [label, setLabel] = useState(''), [sort, setSort] = useState('new'), [page, setPage] = useState(1)
  const { data, isFetching } = useQuery({
    queryKey: ['history', q, label, sort, page], placeholderData: keepPreviousData,
    queryFn: async () => (await api.get('/history', { params: { q, label, sort, page, page_size: 15 } })).data as { total: number; items: Summary[] },
  })
  const pages = Math.max(1, Math.ceil((data?.total ?? 0) / 15))
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Detection history</h1>
      <Card>
        <div className="mb-4 flex flex-wrap gap-3">
          <div className="relative min-w-52 flex-1"><Search size={15} className="absolute left-3 top-3 text-muted" /><input className="input !pl-9" placeholder="Search file name or SHA-256…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} /></div>
          <select className="input !w-auto" value={label} onChange={(e) => { setLabel(e.target.value); setPage(1) }}><option value="">All verdicts</option><option>Benign</option><option>Suspicious</option><option>Ransomware</option></select>
          <select className="input !w-auto" value={sort} onChange={(e) => setSort(e.target.value)}><option value="new">Newest</option><option value="old">Oldest</option><option value="risk">Highest risk</option></select>
        </div>
        {data?.items.length ? (
          <div className="overflow-x-auto"><table className={`w-full text-sm ${isFetching ? 'opacity-60' : ''}`}>
            <thead className="text-left text-xs uppercase text-muted"><tr><th className="pb-2">File</th><th>Risk</th><th>Verdict</th><th>Level</th><th>Confidence</th><th>When</th><th /></tr></thead>
            <tbody>{data.items.map((r) => (
              <tr key={r.id} className="border-t border-line"><td className="py-2.5 pr-3"><Link to={`/results/${r.id}`} className="hover:text-neon">{r.filename}</Link></td><td>{num(r.risk, 2)}</td><td><LabelBadge label={r.label} /></td><td><LevelBadge level={r.threat_level} /></td><td>{pct(r.confidence)}</td><td className="text-muted">{new Date(r.created_at).toLocaleString()}</td>
                <td><button title="Export CSV" className="p-1 text-muted hover:text-neon" onClick={() => download(`/reports/${r.id}/csv`, `report_${r.id}.csv`)}><Download size={15} /></button></td></tr>))}</tbody>
          </table></div>
        ) : <Empty>No matching analyses.</Empty>}
        <div className="mt-4 flex items-center justify-between text-sm text-muted"><span>{data?.total ?? 0} result(s)</span>
          <div className="flex items-center gap-2"><button className="btn-ghost !py-1" disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</button><span>{page} / {pages}</span><button className="btn-ghost !py-1" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button></div></div>
      </Card>
    </div>
  )
}
