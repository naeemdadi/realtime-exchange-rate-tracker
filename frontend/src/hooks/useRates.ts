import { useEffect, useState } from 'react'
import { fetchRates, rebase, type RatesResponse, type Tier } from '../api/rates'
import { POLL_INTERVAL_MS } from '../constants/config'

const STORAGE_KEY = 'fx-tracker:last-rates'

export type RatesStatus = 'connecting' | 'live' | 'cached' | 'offline' | 'unavailable'

function readStoredRates(): RatesResponse | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as RatesResponse) : null
  } catch {
    return null
  }
}

function storeRates(response: RatesResponse): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(response))
  } catch {
    // Storage is a convenience for instant first paint; losing it is harmless.
  }
}

export function useRates(base: string, tier: Tier) {
  const [latest, setLatest] = useState<RatesResponse | null>(readStoredRates)
  const [isFromStorage, setIsFromStorage] = useState(latest !== null)
  const [lastFetchFailed, setLastFetchFailed] = useState(false)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let timer: number | undefined

    const load = async () => {
      try {
        const response = await fetchRates({ base, tier, signal: controller.signal })
        if (controller.signal.aborted) return
        setLatest(response)
        setIsFromStorage(false)
        setLastFetchFailed(false)
        storeRates(response)
      } catch {
        if (controller.signal.aborted) return
        setLastFetchFailed(true)
      }
      timer = window.setTimeout(load, POLL_INTERVAL_MS[tier])
    }

    load()
    return () => {
      controller.abort()
      window.clearTimeout(timer)
    }
  }, [base, tier, retryCount])

  let status: RatesStatus
  if (!latest) status = lastFetchFailed ? 'unavailable' : 'connecting'
  else if (lastFetchFailed) status = 'offline'
  else if (isFromStorage) status = 'cached'
  else status = 'live'

  return {
    latest,
    rates: latest ? rebase(latest, base) : null,
    status,
    retry: () => setRetryCount((count) => count + 1),
  }
}
