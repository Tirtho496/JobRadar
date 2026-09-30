import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Settings() {
  const [data, setData] = useState<any>(null)
  useEffect(() => { api.profile().then(setData) }, [])
  if (!data) return <div className="page"><div className="empty">Loading configuration...</div></div>
  const c = data.candidate
  return <div className="page">
    <div className="page-header"><div><h1>Search profile</h1><p>This configuration is stored in YAML so you can change targets without editing application code.</p></div></div>
    <section className="panel"><h2>{c.headline}</h2><p>{c.summary}</p><div className="pill-row">{c.skills.map((skill: string) => <span className="pill" key={skill}>{skill}</span>)}</div></section>
    <section className="section"><h2>Target markets</h2><div className="country-grid">{Object.entries(data.locations.countries).map(([country, cfg]: any) => <div className="country-card" key={country}><strong>{country}</strong><span>{cfg.cities.join(', ')}</span></div>)}</div></section>
    <section className="section"><h2>Eligibility policy</h2><div className="panel compact"><div>Experience ceiling: {c.constraints.max_required_years} years</div><div>Borderline ceiling: {c.constraints.borderline_required_years} years</div><div>Senior titles rejected: {c.constraints.reject_senior_titles ? 'Yes' : 'No'}</div><div>English compatibility required: {c.constraints.require_english_compatible ? 'Yes' : 'No'}</div></div></section>
    <section className="section"><h2>Configuration files</h2><p className="muted">Edit <code>config/profile.yaml</code>, <code>config/locations.yaml</code>, <code>config/companies.yaml</code> and <code>config/sources.yaml</code>, then restart the backend.</p></section>
  </div>
}
