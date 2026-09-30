import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Market() {
  const [data, setData] = useState<any>(null)
  useEffect(() => { api.skills().then(setData) }, [])
  return <div className="page">
    <div className="page-header"><div><h1>Skills market</h1><p>Demand signals extracted from jobs that already passed your eligibility filters.</p></div></div>
    {!data ? <div className="empty">Loading skill intelligence...</div> : <>
      <div className="stats-grid two"><div className="stat-card"><div className="stat-value">{data.total_jobs}</div><div className="muted">Relevant jobs analyzed</div></div><div className="stat-card"><div className="stat-value">{data.top_gaps.length}</div><div className="muted">Priority gaps surfaced</div></div></div>
      <section className="section"><h2>Highest-value skill gaps</h2><div className="gap-grid">{data.top_gaps.map((item: any) => <div className="gap-card" key={item.skill}><strong>{item.skill}</strong><span>{item.jobs} relevant jobs</span></div>)}</div></section>
      <section className="section"><h2>Demand table</h2><div className="table-wrap"><table><thead><tr><th>Skill</th><th>Relevant jobs</th><th>Current profile</th></tr></thead><tbody>{data.skills.map((item: any) => <tr key={item.skill}><td>{item.skill}</td><td>{item.jobs}</td><td>{item.owned ? 'Covered' : 'Gap'}</td></tr>)}</tbody></table></div></section>
    </>}
  </div>
}
