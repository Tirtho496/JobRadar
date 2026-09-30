import { useEffect, useState } from 'react'
import { api } from '../api'

export default function ModelLab() {
  const [data, setData] = useState<any>(null)
  const [running, setRunning] = useState(false)
  const load = () => api.modelLab().then(setData)
  useEffect(() => { load() }, [])
  const run = async () => { setRunning(true); try { await api.runEvaluation(); await load() } finally { setRunning(false) } }
  return <div className="page">
    <div className="page-header"><div><h1>Model lab</h1><p>Benchmark the active local embedding model against the deterministic fallback.</p></div><button className="button primary" onClick={run} disabled={running}>{running ? 'Running evaluation' : 'Run evaluation'}</button></div>
    <div className="notice"><strong>Active model:</strong> {data?.active_model ?? 'loading'}. Results are only shown after a real benchmark run; JobRadar does not ship fabricated performance numbers.</div>
    <div className="table-wrap"><table><thead><tr><th>Model</th><th>Dataset</th><th>Precision@10</th><th>NDCG@10</th><th>Mean latency</th><th>Run</th></tr></thead><tbody>{(data?.results ?? []).map((row: any) => <tr key={row.id}><td>{row.model_name}</td><td>{row.dataset_name}</td><td>{row.precision_at_10?.toFixed(3)}</td><td>{row.ndcg_at_10?.toFixed(3)}</td><td>{row.mean_latency_ms?.toFixed(1)} ms</td><td>{new Date(row.created_at).toLocaleString()}</td></tr>)}</tbody></table>{!data?.results?.length && <div className="empty">No benchmark has been run yet.</div>}</div>
  </div>
}
