import type { Tier } from '../api/rates'

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
export const FRANKFURTER_URL = 'https://api.frankfurter.dev/v1'

export const POLL_INTERVAL_MS: Record<Tier, number> = { free: 30_000, paid: 3_000 }
export const VERIFY_DEBOUNCE_MS = 600
export const HISTORY_DAYS = 30

export const DEFAULT_BASE = 'USD'
export const DEFAULT_PAIR = { from: 'USD', to: 'EUR' }
export const POPULAR_CURRENCIES = ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'AUD', 'CAD', 'CHF', 'SGD', 'AED']

// Currencies the ECB publishes, which is all Frankfurter can chart.
export const HISTORY_CURRENCIES = new Set(
  'AUD BRL CAD CHF CNY CZK DKK EUR GBP HKD HUF IDR ILS INR ISK JPY KRW MXN MYR NOK NZD PHP PLN RON SEK SGD THB TRY USD ZAR'.split(' '),
)
