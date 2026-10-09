import { FormEvent, ReactNode, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, errMsg } from '../api'
import { useAuth } from '../auth'
import { Logo, ThemeToggle } from '../components/Layout'
import { ErrorBox } from '../components/Ui'

function Shell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="grid min-h-screen place-items-center px-4">
      <div className="absolute right-4 top-4"><ThemeToggle /></div>
      <div className="glass w-full max-w-md p-8"><div className="mb-6 flex justify-center"><Logo /></div><h1 className="mb-6 text-center text-xl font-bold">{title}</h1>{children}</div>
    </div>
  )
}
const Field = ({ label, ...p }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) => (<div><label className="label">{label}</label><input className="input" required {...p} /></div>)

function useSubmit(fn: () => Promise<string | void>) {
  const [err, setErr] = useState(''), [info, setInfo] = useState(''), [busy, setBusy] = useState(false)
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setErr(''); setInfo(''); setBusy(true)
    try { const m = await fn(); if (m) setInfo(m) } catch (x) { setErr(errMsg(x)) } finally { setBusy(false) }
  }
  return { err, info, busy, submit }
}

export function Login() {
  const { login } = useAuth(); const nav = useNavigate()
  const [email, setEmail] = useState(''), [pw, setPw] = useState('')
  const { err, busy, submit } = useSubmit(async () => { await login(email, pw); nav('/dashboard') })
  return (
    <Shell title="Sign in">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
        <Field label="Password" type="password" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="current-password" />
        {err && <ErrorBox msg={err} />}
        <button className="btn-primary w-full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        <div className="flex justify-between text-sm text-muted"><Link to="/forgot" className="hover:text-neon">Forgot password?</Link><Link to="/signup" className="hover:text-neon">Create account</Link></div>
      </form>
    </Shell>
  )
}

export function Signup() {
  const { signup } = useAuth(); const nav = useNavigate()
  const [f, setF] = useState({ name: '', email: '', pw: '' })
  const { err, busy, submit } = useSubmit(async () => { await signup(f.email, f.name, f.pw); nav('/dashboard') })
  return (
    <Shell title="Create your account">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Full name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
        <Field label="Email" type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} />
        <Field label="Password (min 8 characters)" type="password" minLength={8} value={f.pw} onChange={(e) => setF({ ...f, pw: e.target.value })} autoComplete="new-password" />
        {err && <ErrorBox msg={err} />}
        <button className="btn-primary w-full" disabled={busy}>Create account</button>
        <p className="text-center text-sm text-muted">Have an account? <Link to="/login" className="text-neon">Sign in</Link></p>
      </form>
    </Shell>
  )
}

export function Forgot() {
  const [email, setEmail] = useState(''); const [token, setToken] = useState('')
  const { err, info, busy, submit } = useSubmit(async () => {
    const r = await api.post('/auth/forgot-password', { email })
    if (r.data.dev_token) setToken(r.data.dev_token)
    return r.data.message
  })
  return (
    <Shell title="Reset password">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        {err && <ErrorBox msg={err} />}
        {info && <div className="rounded-xl border border-safe/40 bg-safe/10 px-3 py-2 text-sm text-safe">{info}</div>}
        {token && <Link to={`/reset-password?token=${token}`} className="block text-center text-xs text-warn underline">Development mode: open reset page</Link>}
        <button className="btn-primary w-full" disabled={busy}>Send reset link</button>
        <p className="text-center text-sm"><Link to="/login" className="text-muted hover:text-neon">Back to sign in</Link></p>
      </form>
    </Shell>
  )
}

export function Reset() {
  const [sp] = useSearchParams(); const nav = useNavigate()
  const [pw, setPw] = useState('')
  const { err, busy, submit } = useSubmit(async () => { await api.post('/auth/reset-password', { token: sp.get('token') ?? '', new_password: pw }); nav('/login') })
  return (
    <Shell title="Choose a new password">
      <form onSubmit={submit} className="space-y-4">
        <Field label="New password" type="password" minLength={8} value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="new-password" />
        {err && <ErrorBox msg={err} />}
        <button className="btn-primary w-full" disabled={busy}>Update password</button>
      </form>
    </Shell>
  )
}
