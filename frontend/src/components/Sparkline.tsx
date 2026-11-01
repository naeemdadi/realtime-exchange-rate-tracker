import { HISTORY_COPY } from '../constants/copy'

const WIDTH = 300
const HEIGHT = 80

interface SparklineProps {
  values: number[]
  label: string
}

export function Sparkline({ values, label }: SparklineProps) {
  if (values.length < 2) return null
  const min = Math.min(...values)
  const range = Math.max(...values) - min || 1
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * WIDTH
      const y = HEIGHT - ((value - min) / range) * HEIGHT
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
  const change = (values[values.length - 1] - values[0]) / values[0]
  const changeText = `${change >= 0 ? '+' : ''}${(change * 100).toFixed(2)}%`

  return (
    <figure className="sparkline">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={label} preserveAspectRatio="none">
        <polyline points={points} fill="none" stroke="currentColor" strokeWidth="2" vectorEffect="non-scaling-stroke" />
      </svg>
      <figcaption className={change >= 0 ? 'up' : 'down'}>{HISTORY_COPY.change(changeText)}</figcaption>
    </figure>
  )
}
