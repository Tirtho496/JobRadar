import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Job } from '../types'

export default function Digest() {
  const [hours, setHours] = useState(24)
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState('')
  const load = async () => {
    try { setData(await api.digest(hours)); setError('') }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to load digest') }
  }
  useEffect(() => { load() }, [hours])
  return <div className="page">
    <div className="page-header"><div><h1>Daily digest</h1><p>New eligible opportunities grouped by country, with highest application value first.</p></div><select value={hours} onChange={e => setHours(Number(e.target.value))}><option value={24}>Last 24 hours</option><option value={48}>Last 48 hours</option><option value={168}>Last 7 days</option></select></div>
    {error && <div className="notice error">{error}</div>}
    {data && <div className="notice"><strong>{data.total}</strong> new eligible jobs in this window.</div>}
    {Object.entries(data?.countries ?? {}).map(([country, rows]) => <section className="section" key={country}><div className="section-title"><h2>{country}</h2><span className="muted">{(rows as Job[]).length} shown</span></div><div className="table-wrap"><table><thead><tr><th>Fit</th><th>Role</th><th>Company</th><th>Location</th><th>Value</th><th>Match</th></tr></thead><tbody>{(rows as Job[]).map(job => <tr key={job.id}><td><span className="score small">{Math.round(job.fit_score)}</span></td><td><a className="table-title" href={job.canonical_url} target="_blank" rel="noreferrer">{job.title}</a></td><td>{job.company}</td><td>{job.location || job.country}</td><td><span className={`pill value-${job.application_value.toLowerCase()}`}>{job.application_value}</span></td><td className="muted tiny">{job.matched_skills.slice(0, 5).join(', ') || job.role_family}</td></tr>)}</tbody></table></div></section>)}
    {data && data.total === 0 && <div className="empty">No new eligible jobs in this window. The next scheduled scan will update this view.</div>}
  </div>
}
