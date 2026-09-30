import { useEffect, useState } from 'react'
import { api } from '../api'
import type { SourceHealth } from '../types'

export default function System() {
  const [data, setData] = useState<{ingestion_running: boolean, sources: SourceHealth[]} | null>(null)
  const [message, setMessage] = useState('')
  const load = () => api.sources().then(setData)
  useEffect(() => { load(); const id = setInterval(load, 8000); return () => clearInterval(id) }, [])
  const scan = async () => { const result = await api.scan(); setMessage(result.message); await load() }
  return <div className="page">
    <div className="page-header"><div><h1>System health</h1><p>Collector status, throughput, duplicates and graceful-degradation visibility.</p></div><button className="button primary" disabled={data?.ingestion_running} onClick={scan}>{data?.ingestion_running ? 'Scan running' : 'Run scan'}</button></div>
    {message && <div className="notice">{message}</div>}
    <div className="table-wrap"><table><thead><tr><th>Source</th><th>Status</th><th>Fetched</th><th>New</th><th>Eligible</th><th>Rejected</th><th>Duplicates</th><th>Latency</th><th>Error</th></tr></thead><tbody>
      {(data?.sources ?? []).map(source => <tr key={source.source}><td>{source.source}</td><td><span className={`status status-${source.status.toLowerCase()}`}>{source.status}</span></td><td>{source.fetched}</td><td>{source.inserted}</td><td>{source.eligible}</td><td>{source.rejected}</td><td>{source.duplicates}</td><td>{source.latency_ms ? `${Math.round(source.latency_ms)} ms` : '—'}</td><td className="error-cell">{source.error || '—'}</td></tr>)}
    </tbody></table>{!data?.sources.length && <div className="empty">No collector runs yet.</div>}</div>
  </div>
}
