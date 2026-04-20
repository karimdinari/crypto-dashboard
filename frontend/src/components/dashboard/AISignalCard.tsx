import { Link } from 'react-router-dom'
import type { Asset, PredictionSignal } from '../../types'

function ConfidenceRing({ value, signal }: { value: number; signal: PredictionSignal }) {
  const r = 36
  const circ = 2 * Math.PI * r
  const dash = circ * value
  const color = signal === 'BUY' ? '#3ee8b0' : signal === 'SELL' ? '#ff6b6b' : '#8892a8'
  const glow = signal === 'BUY'
    ? '0 0 20px rgba(62,232,176,0.5)'
    : signal === 'SELL'
      ? '0 0 20px rgba(255,107,107,0.45)'
      : 'none'
  return (
    <svg width={88} height={88} viewBox="0 0 88 88" className="shrink-0" aria-hidden>
      <circle cx={44} cy={44} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={8} />
      <circle
        cx={44} cy={44} r={r} fill="none"
        stroke={color} strokeWidth={8}
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        transform="rotate(-90 44 44)"
        style={{ filter: glow !== 'none' ? `drop-shadow(${glow})` : undefined, transition: 'stroke-dasharray 1s ease' }}
      />
      <text x={44} y={40} textAnchor="middle" fill={color} fontSize={11} fontWeight={700} fontFamily="IBM Plex Mono">
        {(value * 100).toFixed(0)}%
      </text>
      <text x={44} y={54} textAnchor="middle" fill="rgba(136,146,168,0.9)" fontSize={9}>
        conf
      </text>
    </svg>
  )
}

function ProbBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-[10px]">
        <span className="text-terminal-muted">{label}</span>
        <span className="font-mono" style={{ color }}>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-terminal-bg">
        <div className="h-full animate-bar-grow rounded-full" style={{ width: `${value * 100}%`, background: color }} />
      </div>
    </div>
  )
}

const SIGNAL_CFG = {
  BUY:  { bg: 'from-up/10 to-transparent', border: 'border-up/30', text: 'text-up', label: 'BUY', glow: 'shadow-[0_0_32px_rgba(62,232,176,0.18)]' },
  SELL: { bg: 'from-down/10 to-transparent', border: 'border-down/30', text: 'text-down', label: 'SELL', glow: 'shadow-[0_0_32px_rgba(255,107,107,0.15)]' },
  HOLD: { bg: 'from-terminal-elevated/40 to-transparent', border: 'border-terminal-border', text: 'text-terminal-muted', label: 'HOLD', glow: '' },
}

export function AISignalCard({ asset }: { asset: Asset }) {
  const cfg = SIGNAL_CFG[asset.prediction]
  return (
    <div className={`rounded-xl border bg-gradient-to-b p-4 ${cfg.bg} ${cfg.border} ${cfg.glow}`}>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-terminal-muted">AI Signal</p>
        <span className={`font-mono text-[10px] text-terminal-muted`}>{asset.modelVersion}</span>
      </div>
      <div className="flex items-center gap-4">
        <ConfidenceRing value={asset.confidence} signal={asset.prediction} />
        <div className="min-w-0 flex-1">
          <div className={`mb-1 font-display text-3xl font-black tracking-tight ${cfg.text}`}>
            {cfg.label}
          </div>
          <p className="mb-3 text-[11px] text-terminal-muted">{asset.symbol} · {asset.name}</p>
          <div className="space-y-2">
            <ProbBar label="P(up)" value={asset.probUp} color="#3ee8b0" />
            <ProbBar label="P(down)" value={asset.probDown} color="#ff6b6b" />
          </div>
        </div>
      </div>
      {asset.anomalies.length > 0 && (
        <div className="mt-3 rounded-lg border border-amber-500/20 bg-amber-500/8 px-3 py-2">
          <p className="text-[10px] font-semibold text-amber-300">
            ⚠ {asset.anomalies[0]}
          </p>
        </div>
      )}
      <Link to="/signals" className="mt-3 inline-flex items-center gap-1 text-[11px] font-medium text-accent hover:underline">
        Full signals desk
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </Link>
    </div>
  )
}
