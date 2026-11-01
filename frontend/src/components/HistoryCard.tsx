import { useEffect, useState } from 'react'
import type { Tier } from '../api/rates'
import { FRANKFURTER_URL, HISTORY_CURRENCIES, HISTORY_DAYS } from '../constants/config'
import { HISTORY_COPY } from '../constants/copy'
import type { CurrencyPair } from './Converter'
import { Sparkline } from './Sparkline'

// Results are tagged with their pair so a stale response is ignored instead of reset in the effect.
type History = { pairKey: string } & ({ state: 'failed' } | { state: 'ready'; values: number[] })

interface FrankfurterSeries {
  rates: Record<string, Record<string, number>>
}

async function fetchHistory({ from, to }: CurrencyPair, signal: AbortSignal): Promise<number[]> {
  const start = new Date(Date.now() - HISTORY_DAYS * 86_400_000).toISOString().slice(0, 10)
  const response = await fetch(`${FRANKFURTER_URL}/${start}..?base=${from}&symbols=${to}`, { signal })
  if (!response.ok) throw new Error(`History request failed with ${response.status}`)
  const series: FrankfurterSeries = await response.json()
  return Object.keys(series.rates)
    .sort()
    .map((day) => series.rates[day][to])
}

interface HistoryCardProps {
  pair: CurrencyPair
  tier: Tier
  onUpgrade: () => void
}

export function HistoryCard({ pair, tier, onUpgrade }: HistoryCardProps) {
  const [result, setResult] = useState<History | null>(null)
  const pairKey = `${pair.from}-${pair.to}`
  const isSupported = pair.from !== pair.to && HISTORY_CURRENCIES.has(pair.from) && HISTORY_CURRENCIES.has(pair.to)

  useEffect(() => {
    if (!isSupported) return
    const controller = new AbortController()
    fetchHistory(pair, controller.signal)
      .then((values) => setResult({ pairKey, state: 'ready', values }))
      .catch(() => {
        if (!controller.signal.aborted) setResult({ pairKey, state: 'failed' })
      })
    return () => controller.abort()
  }, [pair, pairKey, isSupported])

  const history = result?.pairKey === pairKey ? result : { state: 'loading' as const }
  const isLocked = tier === 'free'

  return (
    <section className="card" aria-labelledby="history-title">
      <h2 id="history-title">{HISTORY_COPY.title(pair.from, pair.to)}</h2>
      <div className={isLocked ? 'history history--locked' : 'history'}>
        <div aria-hidden={isLocked}>
          {!isSupported && <p className="muted">{HISTORY_COPY.unsupported}</p>}
          {isSupported && history.state === 'loading' && <p className="muted">{HISTORY_COPY.loading}</p>}
          {isSupported && history.state === 'failed' && <p className="muted">{HISTORY_COPY.failed}</p>}
          {isSupported && history.state === 'ready' && (
            <Sparkline values={history.values} label={HISTORY_COPY.chartLabel(pair.from, pair.to)} />
          )}
        </div>
        {isLocked && (
          <div className="history__upgrade">
            <h3>{HISTORY_COPY.upgradeTitle}</h3>
            <p>{HISTORY_COPY.upgradeBody}</p>
            <button type="button" onClick={onUpgrade}>
              {HISTORY_COPY.upgradeCta}
            </button>
          </div>
        )}
      </div>
    </section>
  )
}
