import type { Job, Summary } from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) }
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  summary: () => request<Summary>('/api/summary'),
  digest: (hours = 24) => request<any>(`/api/digest?hours=${hours}`),
  jobs: (params = '') => request<Job[]>(`/api/jobs${params ? `?${params}` : ''}`),
  tracker: (status = '') => request<Job[]>(`/api/jobs/tracker${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  updateStatus: (id: number, status: string) => request<Job>(`/api/jobs/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  feedback: (id: number, useful: boolean, reason?: string) => request(`/api/jobs/${id}/feedback`, { method: 'POST', body: JSON.stringify({ useful, reason }) }),
  skills: () => request<any>('/api/analytics/skills'),
  sources: () => request<any>('/api/system/sources'),
  scan: () => request<any>('/api/ingest/run', { method: 'POST' }),
  modelLab: () => request<any>('/api/model-lab'),
  runEvaluation: () => request<any>('/api/model-lab/run', { method: 'POST' }),
  profile: () => request<any>('/api/settings/profile')
}
