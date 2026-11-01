import { HttpResponse, http } from 'msw'
import { setupServer } from 'msw/node'
import type { RatesResponse, Tier } from '../api/rates'
import { API_URL, FRANKFURTER_URL } from '../constants/config'

const USD_RATES = { USD: 1, EUR: 0.9, GBP: 0.75, INR: 95, JPY: 150 }

export function ratesResponse(tier: Tier, base = 'USD'): RatesResponse {
  const baseRate = USD_RATES[base as keyof typeof USD_RATES]
  return {
    base,
    rates: Object.fromEntries(Object.entries(USD_RATES).map(([code, rate]) => [code, rate / baseRate])),
    fetchedAt: new Date().toISOString(),
    ageSeconds: 0,
    source: tier === 'paid' ? 'premium' : 'coinbase',
    freshness: 'fresh',
    tier,
    verified: false,
  }
}

export const ratesHandler = http.get(`${API_URL}/api/rates`, ({ request }) => {
  const params = new URL(request.url).searchParams
  return HttpResponse.json(ratesResponse(params.get('tier') as Tier, params.get('base') ?? 'USD'))
})

export const failingRatesHandler = http.get(`${API_URL}/api/rates`, () =>
  HttpResponse.json({ error: 'No exchange rate source is reachable' }, { status: 503 }),
)

const historyHandler = http.get(`${FRANKFURTER_URL}/*`, () =>
  HttpResponse.json({ rates: { '2026-10-01': { EUR: 0.88 }, '2026-10-15': { EUR: 0.89 }, '2026-10-30': { EUR: 0.9 } } }),
)

export const server = setupServer(ratesHandler, historyHandler)
