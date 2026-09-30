export type Job = {
  id: number
  source: string
  duplicate_sources: string[]
  canonical_url: string
  title: string
  company: string
  country: string
  city: string | null
  location: string
  remote: boolean
  date_posted: string | null
  language_status: string
  experience_min: number | null
  experience_max: number | null
  seniority: string
  role_family: string
  skills: string[]
  matched_skills: string[]
  missing_skills: string[]
  fit_score: number
  eligibility: string
  application_value: string
  score_breakdown: Record<string, number>
  reasons: string[]
  status: string
  first_seen_at: string
}

export type Summary = {
  total: number
  new_today: number
  high_value: number
  applied: number
  countries: Record<string, number>
  roles: Record<string, number>
}

export type SourceHealth = {
  source: string
  status: string
  started_at: string
  finished_at: string | null
  fetched: number
  inserted: number
  eligible: number
  rejected: number
  duplicates: number
  latency_ms: number | null
  error: string | null
}
