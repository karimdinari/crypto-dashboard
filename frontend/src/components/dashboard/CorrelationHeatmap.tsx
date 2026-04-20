import { useState } from 'react'

type Props = {
  labels: string[]
  matrix: number[][]
  title?: string
  subtitle?: string
  compact?: boolean
}

function heatColor(v: number) {
  if (v >= 0.85) return 'rgba(34, 211, 238, 0.60)'
  if (v >= 0.55) return 'rgba(34, 211, 238, 0.35)'
  if (v >= 0.35) return 'rgba(139, 92, 246, 0.45)'
  if (v >= 0.1)  return 'rgba(148, 163, 184, 0.22)'
  if (v >= 0)    return 'rgba(148, 163, 184, 0.14)'
  if (v >= -0.35) return 'rgba(251, 191, 36, 0.28)'
  return 'rgba(239, 83, 80, 0.50)'
}

function heatLabel(v: number) {
  if (v >= 0.85) return 'Strong positive'
  if (v >= 0.35) return 'Moderate positive'
  if (v >= 0)    return 'Neutral'
  if (v >= -0.35) return 'Moderate negative'
  return 'Strong negative'
}

export function CorrelationHeatmap({
  labels,
  matrix,
  title = 'Cross-asset correlation',
  subtitle = 'Gold-layer feature correlations (demo matrix)',
  compact,
}: Props) {
  const [tooltip, setTooltip] = useState<{
    row: string
    col: string
    value: number
    x: number
    y: number
  } | null>(null)

  const n = labels.length
  const cell = compact ? 28 : 36
  const pad  = 74
  const w    = pad + n * cell
  const h    = pad + n * cell

  const legendStops = [
    { pct: 0,   color: 'rgba(239,83,80,0.7)',   label: '−1' },
    { pct: 25,  color: 'rgba(251,191,36,0.5)',  label: '−0.5' },
    { pct: 50,  color: 'rgba(148,163,184,0.3)', label: '0' },
    { pct: 75,  color: 'rgba(139,92,246,0.6)',  label: '+0.5' },
    { pct: 100, color: 'rgba(34,211,238,0.8)',  label: '+1' },
  ]

  return (
    <div className="rounded-xl border border-white/[0.08] bg-gradient-to-b from-terminal-surface/80 to-terminal-bg/90 p-3 shadow-[0_12px_48px_rgba(0,0,0,0.5)] backdrop-blur-md">
      <div className="mb-2 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h3 className="text-[10px] font-bold uppercase tracking-[0.14em] text-terminal-muted">{title}</h3>
          <p className="text-[11px] text-terminal-muted/90">{subtitle}</p>
        </div>
      </div>

      {/* Heatmap SVG */}
      <div className="relative overflow-x-auto">
        <svg
          width={w}
          height={h}
          viewBox={`0 0 ${w} ${h}`}
          className="mx-auto cursor-crosshair font-mono text-[9px]"
          role="img"
          aria-label="Correlation heatmap between assets"
          onMouseLeave={() => setTooltip(null)}
        >
          <defs>
            <filter id="hm-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="1.4" result="b" />
              <feMerge>
                <feMergeNode in="b" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Row labels */}
          {labels.map((lb, i) => (
            <text
              key={`r-${lb}`}
              x={pad - 8}
              y={pad + i * cell + cell / 2 + 3}
              textAnchor="end"
              fill="var(--app-terminal-muted)"
              fontSize={compact ? 8 : 9}
            >
              {lb.replace('/USD', '')}
            </text>
          ))}

          {/* Column labels */}
          {labels.map((lb, j) => (
            <text
              key={`c-${lb}`}
              x={pad + j * cell + cell / 2}
              y={pad - 12}
              textAnchor="middle"
              fill="var(--app-terminal-muted)"
              fontSize={compact ? 8 : 9}
            >
              {lb.replace('/USD', '')}
            </text>
          ))}

          {/* Cells */}
          {matrix.flatMap((row, i) =>
            row.map((v, j) => {
              const isHigh = Math.abs(v) > 0.5
              const isDiag = i === j
              return (
                <g
                  key={`${i}-${j}`}
                  filter={isHigh ? 'url(#hm-glow)' : undefined}
                  onMouseEnter={(e) => {
                    const svgEl = (e.currentTarget as SVGGElement).closest('svg')
                    const rect = svgEl?.getBoundingClientRect()
                    setTooltip({
                      row: labels[i],
                      col: labels[j],
                      value: v,
                      x: e.clientX - (rect?.left ?? 0),
                      y: e.clientY - (rect?.top ?? 0),
                    })
                  }}
                >
                  <rect
                    x={pad + j * cell + 1}
                    y={pad + i * cell + 1}
                    width={cell - 2}
                    height={cell - 2}
                    rx={5}
                    fill={heatColor(v)}
                    stroke={isDiag ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.06)'}
                    strokeWidth={isDiag ? 1.5 : 1}
                    className="transition-opacity hover:opacity-90"
                  />
                  <text
                    x={pad + j * cell + cell / 2}
                    y={pad + i * cell + cell / 2 + 3}
                    textAnchor="middle"
                    fill={isDiag ? 'var(--app-terminal-text)' : 'var(--app-terminal-text)'}
                    fontSize={compact ? 8 : 9}
                    fontWeight={isDiag ? '700' : '400'}
                  >
                    {v.toFixed(2)}
                  </text>
                </g>
              )
            }),
          )}
        </svg>

        {/* Hover tooltip */}
        {tooltip && (
          <div
            className="pointer-events-none absolute z-10 rounded-lg border border-terminal-border bg-terminal-surface/95 px-3 py-2 shadow-xl backdrop-blur-sm"
            style={{
              left: tooltip.x + 12,
              top: tooltip.y - 40,
              transform: 'translateY(-50%)',
              maxWidth: '200px',
            }}
          >
            <p className="font-mono text-[11px] font-semibold text-terminal-text">
              {tooltip.row.replace('/USD', '')} / {tooltip.col.replace('/USD', '')}
            </p>
            <p className="font-mono text-[13px] font-bold" style={{ color: heatColor(tooltip.value).replace('0.', '1.') }}>
              {tooltip.value.toFixed(4)}
            </p>
            <p className="text-[10px] text-terminal-muted">{heatLabel(tooltip.value)}</p>
          </div>
        )}
      </div>

      {/* Color legend */}
      <div className="mt-3 flex items-center gap-2">
        <span className="text-[9px] text-terminal-muted">−1</span>
        <div className="relative h-2 flex-1 overflow-hidden rounded-full">
          <div
            className="h-full w-full rounded-full"
            style={{
              background: `linear-gradient(to right, ${legendStops.map((s) => `${s.color} ${s.pct}%`).join(', ')})`,
            }}
          />
        </div>
        <span className="text-[9px] text-terminal-muted">+1</span>
      </div>
      <div className="mt-1 flex justify-between px-0.5 text-[8px] text-terminal-muted/70">
        <span>Neg</span>
        <span>Neutral</span>
        <span>Pos</span>
      </div>
    </div>
  )
}
