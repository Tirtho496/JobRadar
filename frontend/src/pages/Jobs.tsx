import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { Job } from '../types'

const values = ['', 'HIGH', 'MEDIUM', 'LOW']
const statuses = ['', 'NEW', 'SAVED', 'APPLYING', 'APPLIED', 'INTERVIEW', 'REJECTED', 'OFFER']

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [countries, setCountries] = useState<string[]>([''])
  const [country, setCountry] = useState('')
  const [value, setValue] = useState('')
  const [minScore, setMinScore] = useState(50)
  const [query, setQuery] = useState('')
  const [status, setStatusFilter] = useState('')
  const [newOnly, setNewOnly] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    const params = new URLSearchParams({ min_score: String(minScore), limit: '300' })
    if (country) params.set('country', country)
    if (value) params.set('application_value', value)
    if (status) params.set('status', status)
    if (newOnly) params.set('new_since_hours', '24')
    try { setJobs(await api.jobs(params.toString())); setError('') } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
  }

  useEffect(() => {
    api.profile().then(data => {
      const configured = Object.keys(data.locations?.countries ?? {})
      setCountries(['', ...configured, ...(data.locations?.remote_eu ? ['EU Remote'] : [])])
    }).catch(() => setCountries(['']))
  }, [])

  useEffect(() => { load() }, [country, value, status, newOnly, minScore])

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim()
    if (!q) return jobs
    return jobs.filter(job => `${job.title} ${job.company} ${job.skills.join(' ')}`.toLowerCase().includes(q))
  }, [jobs, query])

  const setStatus = async (job: Job, nextStatus: string) => { await api.updateStatus(job.id, nextStatus); await load() }

  return <div className="page">
    <div className="page-header"><div><h1>Jobs</h1><p>Only active jobs that pass the configured eligibility filters.</p></div></div>
    <div className="filter-bar">
      <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search title, company or skill" />
      <select value={country} onChange={e => setCountry(e.target.value)}>{countries.map(c => <option key={c} value={c}>{c || 'All countries'}</option>)}</select>
      <select value={value} onChange={e => setValue(e.target.value)}>{values.map(v => <option key={v} value={v}>{v || 'All application values'}</option>)}</select>
      <select value={status} onChange={e => setStatusFilter(e.target.value)}>{statuses.map(v => <option key={v} value={v}>{v || 'All statuses'}</option>)}</select>
      <label className="check-label"><input type="checkbox" checked={newOnly} onChange={e => setNewOnly(e.target.checked)} /> New in 24h</label>
      <label className="range-label">Minimum fit {minScore}<input type="range" min="50" max="95" value={minScore} onChange={e => setMinScore(Number(e.target.value))} /></label>
    </div>
    {error && <div className="notice error">{error}</div>}
    <div className="table-wrap">
      <table>
        <thead><tr><th>Fit</th><th>Role</th><th>Company</th><th>Location</th><th>Language</th><th>Experience</th><th>Value</th><th>Actions</th></tr></thead>
        <tbody>
          {filtered.map(job => <tr key={job.id}>
            <td><span className="score small">{Math.round(job.fit_score)}</span></td>
            <td><a className="table-title" href={job.canonical_url} target="_blank" rel="noreferrer">{job.title}</a><div className="muted tiny">{job.role_family}</div></td>
            <td>{job.company}<div className="muted tiny">{job.source}</div></td>
            <td>{job.location || job.country}</td>
            <td>{job.language_status.replaceAll('_', ' ')}</td>
            <td>{job.experience_max == null ? 'Not explicit' : `${job.experience_min ?? 0}–${job.experience_max} yrs`}</td>
            <td><span className={`pill value-${job.application_value.toLowerCase()}`}>{job.application_value}</span></td>
            <td className="row-actions"><button onClick={() => setStatus(job, 'SAVED')}>Save</button><button onClick={() => setStatus(job, 'APPLIED')}>Applied</button><button onClick={() => setStatus(job, 'IGNORED')}>Ignore</button></td>
          </tr>)}
        </tbody>
      </table>
      {filtered.length === 0 && <div className="empty">No jobs match these filters.</div>}
    </div>
  </div>
}
