import type { Asset } from '../../types'

function RsiArc({ rsi }: { rsi: number }) {
  const pct = rsi / 100
  const r = 28; const circ = 2 * Math.PI * r
  const color = rsi > 70 ? '#ff6b6b' : rsi < 30 ? '#3ee8b0' : rsi > 55 ? '#3ee8b0' : rsi < 45 ? '#ff6b6b' : '#8892a8'
  const label = rsi > 70 ? 'Overbought' : rsi < 30 ? 'Oversold' : 'Neutral'
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={66} height={66} viewBox="0 0 66 66" aria-hidden>
        <circle cx={33} cy={33} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={6}/>
        <circle cx={33} cy={33} r={r} fill="none" stroke={color} strokeWidth={6}
          strokeDasharray={`${circ * pct} ${circ * (1 - pct)}`}
          strokeLinecap="round" transform="rotate(-90 33 33)"
          style={{ filter: `drop-shadow(0 0 6px ${color}80)` }}
        />
        <text x={33} y={37} textAnchor="middle" fill={color} fontSize={11} fontWeight={700} fontFamily="IBM Plex Mono">{rsi.toFixed(0)}</text>
      </svg>
      <p className="text-[9px] uppercase tracking-wide text-terminal-muted">{label}</p>
    </div>
  )
}

function MetricTile({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="rounded-lg border border-white/[0.06] bg-black/25 px-3 py-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] hover:bg-black/35 transition">
      <p className="text-[9px] uppercase tracking-widest text-terminal-muted">{label}</p>
      <p className={`mt-1 font-mono text-[13px] font-semibold ${tone}`}>{value}</p>
    </div>
  )
}

function fmt(asset: Asset, v: number) {
  if (asset.price > 500) return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  if (asset.price > 10) return v.toFixed(3)
  return v.toFixed(5)
}

export function TechnicalPanel({ asset }: { asset: Asset }) {
  const deltaVsMa30 = ((asset.price - asset.ma30) / asset.ma30) * 100
  const macdSign = asset.macd >= asset.macdSignal

  const tiles = [
    { label: 'Last Return',  value: `${asset.lastReturn >= 0 ? '+' : ''}${(asset.lastReturn * 100).toFixed(2)}%`, tone: asset.lastReturn >= 0 ? 'text-up' : 'text-down' },
    { label: 'MA 7',         value: fmt(asset, asset.ma7),  tone: 'text-terminal-text' },
    { label: 'MA 20',        value: fmt(asset, asset.ma20), tone: 'text-terminal-text' },
    { label: 'MA 30',        value: fmt(asset, asset.ma30), tone: 'text-terminal-text' },
    { label: 'MA 50',        value: fmt(asset, asset.ma50), tone: 'text-terminal-text' },
    { label: 'Δ vs MA30',    value: `${deltaVsMa30 >= 0 ? '+' : ''}${deltaVsMa30.toFixed(2)}%`, tone: deltaVsMa30 >= 0 ? 'text-up' : 'text-down' },
    { label: 'Volatility',   value: `${asset.volatility.toFixed(2)}%`, tone: 'text-metals' },
    { label: 'MACD',         value: asset.macd.toFixed(4),  tone: macdSign ? 'text-up' : 'text-down' },
  ]

  return (
    <div className="glass-panel rounded-xl border border-white/[0.07] p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="font-display text-[10px] font-bold uppercase tracking-[0.2em] text-terminal-muted">Technical insight</h3>
          <p className="mt-0.5 text-[11px] text-terminal-muted/80">Gold feature layer · {asset.symbol}</p>
        </div>
        <RsiArc rsi={asset.rsi} />
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {tiles.map(t => <MetricTile key={t.label} {...t} />)}
      </div>

      {/* MA comparison bar */}
      <div className="mt-4">
        <p className="mb-2 text-[9px] uppercase tracking-wide text-terminal-muted">Price vs Moving Averages</p>
        <div className="space-y-1.5">
          {[
            { label: 'vs MA7',  val: ((asset.price - asset.ma7)  / asset.ma7)  * 100 },
            { label: 'vs MA20', val: ((asset.price - asset.ma20) / asset.ma20) * 100 },
            { label: 'vs MA50', val: ((asset.price - asset.ma50) / asset.ma50) * 100 },
          ].map(m => (
            <div key={m.label} className="flex items-center gap-2 text-[10px]">
              <span className="w-12 shrink-0 text-terminal-muted">{m.label}</span>
              <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-terminal-bg">
                <div className="absolute left-1/2 top-0 h-full w-px bg-terminal-border/60" />
                <div
                  className={`absolute top-0 h-full animate-bar-grow rounded-full ${m.val >= 0 ? 'left-1/2 bg-up' : 'right-1/2 bg-down'}`}
                  style={{ width: `${Math.min(Math.abs(m.val) * 3, 50)}%` }}
                />
              </div>
              <span className={`w-14 text-right font-mono ${m.val >= 0 ? 'text-up' : 'text-down'}`}>
                {m.val >= 0 ? '+' : ''}{m.val.toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
