import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Job, Summary } from '../types'

function Stat({ label, value }: { label: string; value: number }) {
  return <div className="stat-card"><div className="stat-value">{value}</div><div className="muted">{label}</div></div>
}

function JobCard({ job, onChange }: { job: Job; onChange: () => void }) {
  const update = async (status: string) => {
    await api.updateStatus(job.id, status)
    onChange()
  }
  const feedback = async (useful: boolean) => {
    await api.feedback(job.id, useful, useful ? 'good_recommendation' : 'not_relevant')
  }
  return (
    <article className="job-card">
      <div className="job-topline">
        <div>
          <div className="job-title">{job.title}</div>
          <div className="job-meta">{job.company} · {job.location || job.country}</div>
        </div>
        <div className="score">{Math.round(job.fit_score)}</div>
      </div>
      <div className="pill-row">
        <span className={`pill value-${job.application_value.toLowerCase()}`}>{job.application_value} value</span>
        <span className="pill">{job.role_family}</span>
        <span className="pill">{job.language_status.replaceAll('_', ' ')}</span>
        {job.experience_max != null && <span className="pill">{job.experience_min ?? 0}–{job.experience_max} yrs</span>}
      </div>
      {job.reasons[0] && <p className="reason">{job.reasons[0]}</p>}
      <div className="skills-line"><strong>Match:</strong> {job.matched_skills.slice(0, 6).join(', ') || 'General role match'}</div>
      {job.missing_skills.length > 0 && <div className="skills-line muted"><strong>Gaps:</strong> {job.missing_skills.slice(0, 5).join(', ')}</div>}
      <div className="actions">
        <a className="button primary" href={job.canonical_url} target="_blank" rel="noreferrer">Open job</a>
        <button className="button" onClick={() => update('SAVED')}>Save</button>
        <button className="button" onClick={() => update('APPLIED')}>Mark applied</button>
        <button className="button quiet" onClick={() => update('IGNORED')}>Ignore</button>
        <button className="button quiet" onClick={() => feedback(true)}>Good recommendation</button>
        <button className="button quiet" onClick={() => feedback(false)}>Not relevant</button>
      </div>
    </article>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  const load = async () => {
    try {
      const [s, j] = await Promise.all([api.summary(), api.jobs('min_score=65&limit=16')])
      setSummary(s)
      setJobs(j)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const scan = async () => {
    const result = await api.scan()
    setMessage(result.message)
  }

  if (loading) return <div className="page"><div className="empty">Loading JobRadar...</div></div>

  return (
    <div className="page">
      <div className="page-header">
        <div><h1>Job search command center</h1><p>New opportunities across your configured target markets.</p></div>
        <button className="button primary" onClick={scan}>Run scan now</button>
      </div>
      {message && <div className="notice">{message}</div>}
      <div className="stats-grid">
        <Stat label="Eligible jobs" value={summary?.total ?? 0} />
        <Stat label="New in 24h" value={summary?.new_today ?? 0} />
        <Stat label="High application value" value={summary?.high_value ?? 0} />
        <Stat label="Applications marked" value={summary?.applied ?? 0} />
      </div>
      <section className="section">
        <h2>Country coverage</h2>
        <div className="country-grid">
          {Object.entries(summary?.countries ?? {}).map(([country, count]) => <div className="country-card" key={country}><strong>{country}</strong><span>{count} matches</span></div>)}
          {Object.keys(summary?.countries ?? {}).length === 0 && <div className="empty">Run the first scan to populate country results.</div>}
        </div>
      </section>
      <section className="section">
        <div className="section-title"><h2>Best current matches</h2><span className="muted">Sorted by application value and fit</span></div>
        <div className="job-list">
          {jobs.map(job => <JobCard key={job.id} job={job} onChange={load} />)}
          {jobs.length === 0 && <div className="empty">No eligible jobs yet. Run a scan from the top-right button.</div>}
        </div>
      </section>
    </div>
  )
}
