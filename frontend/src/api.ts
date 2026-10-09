import axios from 'axios'

export const api = axios.create({ baseURL: '/api' })
api.interceptors.request.use((c) => {
  const t = localStorage.getItem('token')
  if (t) c.headers.Authorization = `Bearer ${t}`
  return c
})
api.interceptors.response.use((r) => r, (e) => {
  if (e.response?.status === 401 && !String(e.config?.url).startsWith('/auth/')) {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }
  return Promise.reject(e)
})

export const errMsg = (e: any): string => {
  const d = e?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x: any) => x.msg).join('; ')
  return d ?? e?.message ?? 'Request failed'
}

export async function download(path: string, filename: string) {
  const r = await api.get(path, { responseType: 'blob' })
  const url = URL.createObjectURL(r.data)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}
