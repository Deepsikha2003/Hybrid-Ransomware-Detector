import { ReactNode, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Activity, History, LayoutDashboard, LogOut, Menu, Moon, Settings, Shield, Sun, UploadCloud, X, BarChart3 } from 'lucide-react'
import { useAuth } from '../auth'

export function ThemeToggle() {
  const [dark, setDark] = useState(document.documentElement.classList.contains('dark'))
  const toggle = () => {
    const next = !dark
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('theme', next ? 'dark' : 'light')
    setDark(next)
  }
  return <button onClick={toggle} className="btn-ghost !p-2" aria-label="Toggle theme">{dark ? <Sun size={16} /> : <Moon size={16} />}</button>
}

export const Logo = () => (
  <Link to="/" className="flex items-center gap-2 font-bold"><Shield className="text-neon" size={22} /><span>HRDS<span className="text-neon">.</span>ai</span></Link>
)

export function PublicShell({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-6 py-4"><Logo />
        <div className="flex items-center gap-2"><ThemeToggle />
          {user ? <Link to="/dashboard" className="btn-primary">Dashboard</Link> : <><Link to="/login" className="btn-ghost">Sign in</Link><Link to="/signup" className="btn-primary">Get started</Link></>}
        </div>
      </header>
      {children}
    </div>
  )
}

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const items = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/analyze', label: 'New Analysis', icon: UploadCloud },
    { to: '/history', label: 'History', icon: History },
    { to: '/performance', label: 'Model Performance', icon: BarChart3 },
    ...(user?.role === 'admin' ? [{ to: '/admin', label: 'Administration', icon: Settings }] : []),
  ]
  const side = (
    <nav className="flex h-full flex-col p-4">
      <div className="mb-8 px-2"><Logo /></div>
      <div className="space-y-1">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} onClick={() => setOpen(false)} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-neon/10 text-neon' : 'text-muted hover:text-fg hover:bg-card'}`}>
            <Icon size={17} />{label}
          </NavLink>
        ))}
      </div>
      <div className="mt-auto space-y-3">
        <div className="glass p-3 text-xs"><div className="font-semibold truncate">{user?.full_name}</div><div className="truncate text-muted">{user?.email}</div><div className="mt-1 uppercase tracking-wide text-neon">{user?.role}</div></div>
        <button onClick={() => { logout(); nav('/') }} className="btn-ghost w-full"><LogOut size={15} />Sign out</button>
      </div>
    </nav>
  )
  return (
    <div className="min-h-screen lg:flex">
      <aside className="hidden w-64 shrink-0 border-r border-line lg:block sticky top-0 h-screen">{side}</aside>
      {open && <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setOpen(false)}><aside className="h-full w-64 bg-bg" onClick={(e) => e.stopPropagation()}>{side}</aside></div>}
      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-between border-b border-line px-5 py-3">
          <button className="lg:hidden btn-ghost !p-2" onClick={() => setOpen(!open)} aria-label="Menu">{open ? <X size={16} /> : <Menu size={16} />}</button>
          <div className="hidden items-center gap-2 text-xs text-muted lg:flex"><Activity size={14} className="text-safe" />System operational</div>
          <ThemeToggle />
        </header>
        <main className="mx-auto max-w-7xl p-5 lg:p-8">{children}</main>
      </div>
    </div>
  )
}
