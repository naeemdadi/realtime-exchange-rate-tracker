import type { Source } from '../api/rates'

export const APP_COPY = {
  title: 'FX Tracker',
  tagline: 'Currency rates you can trust, for travel, freelance work and small business.',
  baseLabel: 'Base currency',
  tierLabel: 'Plan',
  tierFree: 'Free',
  tierPaid: 'Paid (demo)',
}

export const FRESHNESS_COPY = {
  regionLabel: 'Data freshness',
  updatedAgo: (age: string) => `Updated ${age} ago`,
  via: (source: string) => `via ${source}`,
  stale: 'Rates may be slightly behind. Showing the latest we have.',
  veryStale: 'Rates may be outdated. Showing the last known rates.',
  offline: "Can't reach the rates service right now. Showing the last known rates.",
  cached: 'Showing rates from your last visit while we reconnect.',
  connecting: 'Connecting to the rates service…',
  unavailable: "Rates are temporarily unavailable. We'll keep trying.",
  retry: 'Try again',
}

export const SOURCE_LABELS: Record<Source, string> = {
  coinbase: 'Coinbase',
  'open-er-api': 'ExchangeRate-API (daily)',
  premium: 'Premium feed',
}

export const TABLE_COPY = {
  title: 'Popular rates',
  currencyColumn: 'Currency',
  rateColumn: (base: string) => `1 ${base} =`,
}

export const CONVERTER_COPY = {
  title: 'Convert',
  amountLabel: 'Amount',
  fromLabel: 'From',
  toLabel: 'To',
  verifying: 'Checking against the premium feed…',
  verified: 'Verified against the premium feed just now',
}

export const HISTORY_COPY = {
  title: (from: string, to: string) => `30-day trend: ${from} → ${to}`,
  chartLabel: (from: string, to: string) => `30-day ${from} to ${to} trend`,
  change: (percent: string) => `${percent} over 30 days`,
  unsupported: 'History is not available for this currency pair yet.',
  failed: 'Could not load history right now.',
  loading: 'Loading history…',
  upgradeTitle: 'See 30-day trends with Paid',
  upgradeBody: 'Spot the best day to convert. Paid also gets live rates and guaranteed uptime.',
  upgradeCta: 'Try Paid for $9/month',
}

export const FOOTER_COPY = {
  ratesBy: 'Rates by Coinbase and',
  historyBy: 'History by Frankfurter (European Central Bank).',
}
