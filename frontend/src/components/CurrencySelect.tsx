import { currencyName } from '../lib/format'

interface CurrencySelectProps {
  label: string
  value: string
  currencies: string[]
  onChange: (code: string) => void
}

export function CurrencySelect({ label, value, currencies, onChange }: CurrencySelectProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {currencies.map((code) => (
          <option key={code} value={code}>
            {code} · {currencyName(code)}
          </option>
        ))}
      </select>
    </label>
  )
}
