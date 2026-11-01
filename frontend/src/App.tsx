import { useState } from 'react'
import type { Tier } from './api/rates'
import { Converter, type CurrencyPair } from './components/Converter'
import { CurrencySelect } from './components/CurrencySelect'
import { FreshnessBadge } from './components/FreshnessBadge'
import { HistoryCard } from './components/HistoryCard'
import { RatesTable } from './components/RatesTable'
import { TierToggle } from './components/TierToggle'
import { DEFAULT_BASE, DEFAULT_PAIR } from './constants/config'
import { APP_COPY, FOOTER_COPY } from './constants/copy'
import { useRates } from './hooks/useRates'

export default function App() {
  const [tier, setTier] = useState<Tier>('free')
  const [base, setBase] = useState(DEFAULT_BASE)
  const [pair, setPair] = useState<CurrencyPair>(DEFAULT_PAIR)
  const { latest, rates, status, retry } = useRates(base, tier)
  const currencies = latest ? Object.keys(latest.rates).sort() : [base]

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>{APP_COPY.title}</h1>
          <p className="muted">{APP_COPY.tagline}</p>
        </div>
        <div className="header__controls">
          <CurrencySelect label={APP_COPY.baseLabel} value={base} currencies={currencies} onChange={setBase} />
          <TierToggle tier={tier} onChange={setTier} />
        </div>
      </header>

      <FreshnessBadge latest={latest} status={status} onRetry={retry} />

      {rates && (
        <main className="grid">
          <RatesTable base={base} rates={rates} />
          <div className="stack">
            <Converter rates={rates} currencies={currencies} tier={tier} pair={pair} onPairChange={setPair} />
            <HistoryCard pair={pair} tier={tier} onUpgrade={() => setTier('paid')} />
          </div>
        </main>
      )}

      <footer className="footer muted">
        {FOOTER_COPY.ratesBy} <a href="https://www.exchangerate-api.com">Exchange Rate API</a>.{' '}
        {FOOTER_COPY.historyBy}
      </footer>
    </div>
  )
}
