import type { Tier } from '../api/rates'
import { APP_COPY } from '../constants/copy'

const TIERS: { value: Tier; label: string }[] = [
  { value: 'free', label: APP_COPY.tierFree },
  { value: 'paid', label: APP_COPY.tierPaid },
]

interface TierToggleProps {
  tier: Tier
  onChange: (tier: Tier) => void
}

export function TierToggle({ tier, onChange }: TierToggleProps) {
  return (
    <div className="tier-toggle" role="group" aria-label={APP_COPY.tierLabel}>
      {TIERS.map(({ value, label }) => (
        <button key={value} type="button" aria-pressed={tier === value} onClick={() => onChange(value)}>
          {label}
        </button>
      ))}
    </div>
  )
}
