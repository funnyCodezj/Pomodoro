const BASE = 'http://127.0.0.1:8765'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const api = {
  createSession(type, duration) {
    return request('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({ type, duration }),
    })
  },

  getSessions(limit = 100) {
    return request(`/api/sessions?limit=${limit}`)
  },

  getStats() {
    return request('/api/stats')
  },

  getYearlyStats(year) {
    return request(`/api/stats/yearly?year=${year}`)
  },

  getSettings() {
    return request('/api/settings')
  },

  updateSettings(data) {
    return request('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  clearSessions() {
    return request('/api/sessions', { method: 'DELETE' })
  },

  deleteSession(id) {
    return request(`/api/sessions/${id}`, { method: 'DELETE' })
  },
}
