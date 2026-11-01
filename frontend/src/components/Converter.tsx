import { useEffect, useState } from 'react'
import { fetchRates, type Tier } from '../api/rates'
import { VERIFY_DEBOUNCE_MS } from '../constants/config'
import { CONVERTER_COPY } from '../constants/copy'
import { formatAmount } from '../lib/format'
import { CurrencySelect } from './CurrencySelect'

export interface CurrencyPair {
  from: string
  to: string
}

interface ConverterProps {
  rates: Record<string, number>
  currencies: string[]
  tier: Tier
  pair: CurrencyPair
  onPairChange: (pair: CurrencyPair) => void
}

// Tagged with the inputs it was checked for, so edits invalidate it without resetting state.
type Verification = { inputKey: string } & ({ state: 'checking' } | { state: 'verified'; rate: number } | { state: 'unverified' })

export function Converter({ rates, currencies, tier, pair, onPairChange }: ConverterProps) {
  const [amountText, setAmountText] = useState('100')
  const [hasTyped, setHasTyped] = useState(false)
  const [result, setResult] = useState<Verification | null>(null)
  const amount = Number(amountText)
  const isValidAmount = amountText !== '' && Number.isFinite(amount) && amount > 0
  const shouldVerify = tier === 'free' && hasTyped && isValidAmount
  const inputKey = `${amountText}|${pair.from}|${pair.to}`

  // Free users get a premium-checked rate only once they type an amount: that's the
  // high-intent moment worth spending budget on. Paid rates are already premium.
  useEffect(() => {
    if (!shouldVerify) return
    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setResult({ inputKey, state: 'checking' })
      try {
        const response = await fetchRates({ base: pair.from, tier: 'free', verify: true, signal: controller.signal })
        const rate = response.rates[pair.to]
        const verified = response.verified && rate !== undefined
        setResult(verified ? { inputKey, state: 'verified', rate } : { inputKey, state: 'unverified' })
      } catch {
        if (!controller.signal.aborted) setResult({ inputKey, state: 'unverified' })
      }
    }, VERIFY_DEBOUNCE_MS)
    return () => {
      controller.abort()
      window.clearTimeout(timer)
    }
  }, [inputKey, pair.from, pair.to, shouldVerify])

  const verification = shouldVerify && result?.inputKey === inputKey ? result : null
  const rate = verification?.state === 'verified' ? verification.rate : rates[pair.to] / rates[pair.from]

  return (
    <section className="card" aria-labelledby="converter-title">
      <h2 id="converter-title">{CONVERTER_COPY.title}</h2>
      <div className="converter">
        <label className="field">
          <span>{CONVERTER_COPY.amountLabel}</span>
          <input
            type="number"
            inputMode="decimal"
            min="0"
            value={amountText}
            onChange={(event) => {
              setHasTyped(true)
              setAmountText(event.target.value)
            }}
          />
        </label>
        <CurrencySelect
          label={CONVERTER_COPY.fromLabel}
          value={pair.from}
          currencies={currencies}
          onChange={(from) => onPairChange({ ...pair, from })}
        />
        <CurrencySelect
          label={CONVERTER_COPY.toLabel}
          value={pair.to}
          currencies={currencies}
          onChange={(to) => onPairChange({ ...pair, to })}
        />
      </div>
      {isValidAmount && Number.isFinite(rate) && (
        <output className="converter__result">{formatAmount(amount * rate, pair.to)}</output>
      )}
      {verification?.state === 'checking' && <p className="muted">{CONVERTER_COPY.verifying}</p>}
      {verification?.state === 'verified' && <p className="verified">✓ {CONVERTER_COPY.verified}</p>}
    </section>
  )
}
