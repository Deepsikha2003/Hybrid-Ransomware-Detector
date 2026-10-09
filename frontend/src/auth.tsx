import { createContext, ReactNode, useContext, useEffect, useState } from 'react'
import { api } from './api'
import type { User } from './types'

interface Ctx { user: User | null; loading: boolean; login: (email: string, password: string) => Promise<void>; signup: (email: string, full_name: string, password: string) => Promise<void>; logout: () => void }
const AuthCtx = createContext<Ctx>(null as unknown as Ctx)
export const useAuth = () => useContext(AuthCtx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(!!localStorage.getItem('token'))

  useEffect(() => {
    if (!localStorage.getItem('token')) return
    api.get('/auth/me').then((r) => setUser(r.data)).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false))
  }, [])

  const accept = (d: { access_token: string; user: User }) => { localStorage.setItem('token', d.access_token); setUser(d.user) }
  const value: Ctx = {
    user, loading,
    login: async (email, password) => accept((await api.post('/auth/login', { email, password })).data),
    signup: async (email, full_name, password) => accept((await api.post('/auth/signup', { email, full_name, password })).data),
    logout: () => { localStorage.removeItem('token'); setUser(null) },
  }
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}
