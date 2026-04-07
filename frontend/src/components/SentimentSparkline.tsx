import { useId } from 'react'
import { useTheme } from '../context/ThemeContext'

interface Props {
  values: number[]
  className?: string
}

export function SentimentSparkline({ values, className = '' }: Props) {
  const { theme } = useTheme()
  const gid = useId().replace(/:/g, '')
  if (values.length < 2) return null
  const w = 48
  const h = 14
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w
      const y = h - ((v - min) / range) * (h - 2) - 1
      return `${x},${y}`
    })
    .join(' ')

  const c2 = theme === 'light' ? '#9598a1' : '#787b86'

  return (
    <svg
      width={w}
      height={h}
      className={className}
      viewBox={`0 0 ${w} ${h}`}
      aria-hidden
    >
      <polyline
        fill="none"
        stroke={`url(#${gid})`}
        strokeWidth="1.2"
        points={pts}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#2962ff" />
          <stop offset="100%" stopColor={c2} />
        </linearGradient>
      </defs>
    </svg>
  )
}
