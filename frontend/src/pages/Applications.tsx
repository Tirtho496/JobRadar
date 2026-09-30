import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Job } from '../types'

const stages = ['SAVED', 'APPLYING', 'APPLIED', 'INTERVIEW', 'REJECTED', 'OFFER']

export default function Applications() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [stage, setStage] = useState('')
  const [error, setError] = useState('')
  const load = async () => {
    try { setJobs(await api.tracker(stage)); setError('') }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to load application tracker') }
  }
  useEffect(() => { load() }, [stage])
  const move = async (job: Job, status: string) => { await api.updateStatus(job.id, status); await load() }
  return <div className="page">
    <div className="page-header"><div><h1>Applications</h1><p>Track saved opportunities and every application stage, including jobs that later expire.</p></div></div>
    <div className="filter-bar"><select value={stage} onChange={e => setStage(e.target.value)}><option value="">All tracked stages</option>{stages.map(s => <option key={s}>{s}</option>)}</select></div>
    {error && <div className="notice error">{error}</div>}
    <div className="table-wrap"><table><thead><tr><th>Role</th><th>Company</th><th>Country</th><th>Fit</th><th>Stage</th><th>Move to</th></tr></thead><tbody>
      {jobs.map(job => <tr key={job.id}><td><a className="table-title" href={job.canonical_url} target="_blank" rel="noreferrer">{job.title}</a></td><td>{job.company}</td><td>{job.country}</td><td>{Math.round(job.fit_score)}</td><td><span className="pill">{job.status}</span></td><td><select value={job.status} onChange={e => move(job, e.target.value)}>{stages.map(s => <option key={s}>{s}</option>)}</select></td></tr>)}
    </tbody></table>{jobs.length === 0 && <div className="empty">No tracked applications yet. Save a job or mark it applied from Dashboard or Jobs.</div>}</div>
  </div>
}
