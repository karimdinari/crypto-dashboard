import { useId } from 'react'
import { useTheme } from '../context/ThemeContext'

interface Props {
  values: number[]
  className?: string
}

export function SentimentSparkline({ values, className = '' }: Props) {
  const { theme } = useTheme()
  const gid = useId().replace(/:/g, '')
  const fillId = `${gid}-fill`
  if (values.length < 2) return null
  const w = 48
  const h = 14
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  
  const ptCoords = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w
    const y = h - ((v - min) / range) * (h - 2) - 1
    return { x, y }
  })
  
  const pts = ptCoords.map((p) => `${p.x},${p.y}`).join(' ')
  const fillPts = `0,${h} ${pts} ${w},${h}` // Close path for the area fill

  const c2 = theme === 'light' ? '#9598a1' : '#787b86'

  return (
    <svg
      width={w}
      height={h}
      className={`overflow-visible ${className}`}
      viewBox={`0 0 ${w} ${h}`}
      aria-hidden
    >
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#2962ff" />
          <stop offset="100%" stopColor={c2} />
        </linearGradient>
        <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#2962ff" stopOpacity="0.25" />
          <stop offset="100%" stopColor={c2} stopOpacity="0.0" />
        </linearGradient>
      </defs>
      <polygon
        fill={`url(#${fillId})`}
        points={fillPts}
        className="animate-fade-in"
      />
      <polyline
        fill="none"
        stroke={`url(#${gid})`}
        strokeWidth="1.2"
        points={pts}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray="100"
        strokeDashoffset="100"
        className="animate-donut-draw"
      />
    </svg>
  )
}
