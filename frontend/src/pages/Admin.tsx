import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, errMsg } from '../api'
import { Card, ErrorBox } from '../components/Ui'
import type { FusionConfig } from '../types'

export default function Admin() {
  const qc = useQueryClient()
  const cfg = useQuery({ queryKey: ['cfg'], queryFn: async () => (await api.get('/admin/fusion-config')).data as FusionConfig })
  const users = useQuery({ queryKey: ['users'], queryFn: async () => (await api.get('/admin/users')).data as any[] })
  const logs = useQuery({ queryKey: ['audit'], queryFn: async () => (await api.get('/admin/audit-logs', { params: { limit: 100 } })).data as any[] })
  const [f, setF] = useState<FusionConfig | null>(null)
  useEffect(() => { if (cfg.data) setF(cfg.data) }, [cfg.data])

  const save = useMutation({ mutationFn: async () => (await api.put('/admin/fusion-config', f)).data, onSuccess: () => { qc.invalidateQueries({ queryKey: ['cfg'] }); qc.invalidateQueries({ queryKey: ['audit'] }) } })
  const role = useMutation({ mutationFn: async (v: { id: number; role: string; is_active: boolean }) => api.put(`/admin/users/${v.id}`, { role: v.role, is_active: v.is_active }), onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); qc.invalidateQueries({ queryKey: ['audit'] }) } })
  const reload = useMutation({ mutationFn: async () => api.post('/admin/reload-models') })

  const num = (k: keyof FusionConfig) => (
    <div key={k}><label className="label">{k.replace('_', ' ')}</label><input className="input" type="number" step="0.01" min="0" max="1" value={f?.[k] ?? ''} onChange={(e) => setF({ ...f!, [k]: parseFloat(e.target.value) })} /></div>)

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Administration</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Fusion & thresholds">
          {f && <div className="grid grid-cols-2 gap-4">{(['w_static', 'w_behavior', 't_suspicious', 't_ransomware'] as const).map(num)}</div>}
          <p className="mt-3 text-xs text-muted">Final = w_static × Static + w_behavior × Behaviour (weights are normalised to sum to 1). Benign &lt; suspicious ≤ Suspicious &lt; ransomware ≤ Ransomware. Applies to new analyses only.</p>
          <div className="mt-4 flex items-center gap-3"><button className="btn-primary" disabled={save.isPending} onClick={() => save.mutate()}>Save</button>{save.isSuccess && <span className="text-xs text-safe">Saved</span>}</div>
          {save.isError && <div className="mt-3"><ErrorBox msg={errMsg(save.error)} /></div>}
        </Card>
        <Card title="Models">
          <p className="mb-3 text-sm text-muted">After copying new <code>*_xgb.joblib</code> files into the server's model directory, reload them without restarting.</p>
          <button className="btn-ghost" onClick={() => reload.mutate()} disabled={reload.isPending}>Reload models</button>
          {reload.isSuccess && <span className="ml-3 text-xs text-safe">Reloaded: {(reload.data as any).data.loaded.join(', ') || 'none'}</span>}
        </Card>
      </div>

      <Card title="Users & roles">
        <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="text-left text-xs uppercase text-muted"><tr><th className="pb-2">User</th><th>Role</th><th>Active</th></tr></thead>
          <tbody>{users.data?.map((u) => (<tr key={u.id} className="border-t border-line"><td className="py-2"><div>{u.full_name}</div><div className="text-xs text-muted">{u.email}</div></td>
            <td><select className="input !w-auto !py-1" value={u.role} onChange={(e) => role.mutate({ id: u.id, role: e.target.value, is_active: u.is_active })}><option value="user">User</option><option value="analyst">Security Analyst</option><option value="admin">Admin</option></select></td>
            <td><input type="checkbox" checked={u.is_active} onChange={(e) => role.mutate({ id: u.id, role: u.role, is_active: e.target.checked })} /></td></tr>))}</tbody></table></div>
        {role.isError && <div className="mt-3"><ErrorBox msg={errMsg(role.error)} /></div>}
      </Card>

      <Card title="Audit trail">
        <div className="max-h-96 overflow-auto"><table className="w-full text-sm"><thead className="sticky top-0 bg-bg text-left text-xs uppercase text-muted"><tr><th className="pb-2">Time</th><th>User</th><th>Action</th><th>Detail</th><th>IP</th></tr></thead>
          <tbody>{logs.data?.map((l) => (<tr key={l.id} className="border-t border-line align-top"><td className="py-1.5 pr-3 whitespace-nowrap text-muted">{new Date(l.time).toLocaleString()}</td><td className="pr-3">{l.user ?? '—'}</td><td className="pr-3 font-mono text-xs text-neon">{l.action}</td><td className="pr-3 break-all text-muted">{l.detail}</td><td className="text-muted">{l.ip}</td></tr>))}</tbody></table></div>
      </Card>
    </div>
  )
}
