interface Props {
  className?: string
  lines?: number
  /** width fractions for each line, e.g. ['full', '3/4', '1/2'] */
  widths?: string[]
}

function shimmerCls() {
  return 'relative overflow-hidden rounded bg-terminal-elevated/60 before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.6s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/[0.06] before:to-transparent'
}

export function SkeletonLine({ w = 'full' }: { w?: string }) {
  return <div className={`h-3 w-${w} ${shimmerCls()}`} />
}

export function SkeletonCard({ className = '', lines = 3, widths }: Props) {
  const ws = widths ?? (['full', '3/4', '1/2'].slice(0, lines))
  return (
    <div className={`rounded-xl border border-terminal-border/60 bg-terminal-surface/50 p-4 ${className}`}>
      <div className="space-y-3">
        {ws.map((w, i) => (
          <SkeletonLine key={i} w={w} />
        ))}
      </div>
    </div>
  )
}

export function SkeletonAssetRow() {
  return (
    <div className="flex items-center justify-between border-b border-terminal-border/30 px-3 py-2.5">
      <div className={`h-3 w-20 ${shimmerCls()}`} />
      <div className={`h-3 w-14 ${shimmerCls()}`} />
      <div className={`h-3 w-10 ${shimmerCls()}`} />
    </div>
  )
}

export function SkeletonChart() {
  return (
    <div className={`h-full min-h-[280px] w-full ${shimmerCls()} rounded-none`}>
      <div className="flex h-full flex-col items-center justify-center gap-3 opacity-40">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.25" className="text-terminal-muted">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
        <p className="font-mono text-[11px] text-terminal-muted">Loading chart data…</p>
      </div>
    </div>
  )
}
