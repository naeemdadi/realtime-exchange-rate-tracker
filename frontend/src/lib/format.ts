export function formatAge(seconds: number): string {
  if (seconds < 60) return `${Math.max(0, Math.floor(seconds))}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min`
  if (seconds < 86_400) return `${Math.floor(seconds / 3600)} h`
  return `${Math.floor(seconds / 86_400)} d`
}

export function formatRate(rate: number): string {
  return rate.toLocaleString('en-US', { maximumFractionDigits: rate < 1 ? 6 : 4 })
}

export function formatAmount(amount: number, currency: string): string {
  return amount.toLocaleString('en-US', { style: 'currency', currency, maximumFractionDigits: 2 })
}

const currencyNames = new Intl.DisplayNames(['en'], { type: 'currency' })

export function currencyName(code: string): string {
  return currencyNames.of(code) ?? code
}

export function secondsSince(isoTime: string, now: number): number {
  return (now - new Date(isoTime).getTime()) / 1000
}
