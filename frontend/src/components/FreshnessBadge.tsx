import type { Freshness, RatesResponse } from '../api/rates'
import { FRESHNESS_COPY, SOURCE_LABELS } from '../constants/copy'
import { useNow } from '../hooks/useNow'
import type { RatesStatus } from '../hooks/useRates'
import { formatAge, secondsSince } from '../lib/format'

interface FreshnessBadgeProps {
  latest: RatesResponse | null
  status: RatesStatus
  onRetry: () => void
}

function messageFor(status: RatesStatus, freshness: Freshness): string | null {
  if (status === 'offline') return FRESHNESS_COPY.offline
  if (status === 'cached') return FRESHNESS_COPY.cached
  if (freshness === 'stale') return FRESHNESS_COPY.stale
  if (freshness === 'very_stale') return FRESHNESS_COPY.veryStale
  return null
}

export function FreshnessBadge({ latest, status, onRetry }: FreshnessBadgeProps) {
  const now = useNow()

  if (!latest) {
    if (status === 'connecting') {
      return (
        <div role="status" aria-label={FRESHNESS_COPY.regionLabel} className="freshness freshness--neutral">
          {FRESHNESS_COPY.connecting}
        </div>
      )
    }
    return (
      <div role="alert" className="freshness freshness--very_stale">
        <span>{FRESHNESS_COPY.unavailable}</span>
        <button type="button" onClick={onRetry}>
          {FRESHNESS_COPY.retry}
        </button>
      </div>
    )
  }

  // Data we couldn't refresh is never shown as green, whatever the server said at the time.
  const tone = status !== 'live' && latest.freshness === 'fresh' ? 'stale' : latest.freshness
  const message = messageFor(status, latest.freshness)

  return (
    <div role="status" aria-label={FRESHNESS_COPY.regionLabel} className={`freshness freshness--${tone}`}>
      <span className="freshness__dot" aria-hidden="true" />
      <span>
        {FRESHNESS_COPY.updatedAgo(formatAge(secondsSince(latest.fetchedAt, now)))}{' '}
        <span className="muted">{FRESHNESS_COPY.via(SOURCE_LABELS[latest.source])}</span>
      </span>
      {message && <p className="freshness__message">{message}</p>}
    </div>
  )
}
