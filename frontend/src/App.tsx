import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import { Forgot, Login, Reset, Signup } from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Analyze from './pages/Analyze'
import Results from './pages/Results'
import History from './pages/History'
import Performance from './pages/Performance'
import Admin from './pages/Admin'

function Protected({ roles }: { roles?: string[] }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-10 text-muted">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />
  return <Layout><Outlet /></Layout>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot" element={<Forgot />} />
      <Route path="/reset-password" element={<Reset />} />
      <Route path="/performance" element={<Performance />} />
      <Route element={<Protected />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/results/:id" element={<Results />} />
        <Route path="/history" element={<History />} />
      </Route>
      <Route element={<Protected roles={['admin']} />}>
        <Route path="/admin" element={<Admin />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
