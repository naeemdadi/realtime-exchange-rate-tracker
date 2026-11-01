import { API_URL } from '../constants/config'

export type Tier = 'free' | 'paid'
export type Source = 'coinbase' | 'open-er-api' | 'premium'
export type Freshness = 'fresh' | 'stale' | 'very_stale'

export interface RatesResponse {
  base: string
  rates: Record<string, number>
  fetchedAt: string
  ageSeconds: number
  source: Source
  freshness: Freshness
  tier: Tier
  verified: boolean
}

interface FetchRatesOptions {
  base: string
  tier: Tier
  verify?: boolean
  signal?: AbortSignal
}

export async function fetchRates({ base, tier, verify, signal }: FetchRatesOptions): Promise<RatesResponse> {
  const params = new URLSearchParams({ base, tier })
  if (verify) params.set('verify', 'true')
  const response = await fetch(`${API_URL}/api/rates?${params}`, { signal })
  if (!response.ok) throw new Error(`Rates request failed with ${response.status}`)
  return response.json()
}

// Re-expresses rates against a different base, so cached data still works after a base change.
export function rebase(response: RatesResponse, base: string): Record<string, number> | null {
  const baseRate = response.rates[base]
  if (baseRate === undefined) return null
  return Object.fromEntries(Object.entries(response.rates).map(([code, rate]) => [code, rate / baseRate]))
}
