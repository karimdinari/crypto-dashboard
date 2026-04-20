import { Fragment, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { useData } from '../context/DataContext'
import { useTerminal } from '../context/TerminalContext'
import { MarketTag } from '../components/MarketTag'
import type { PredictionSignal } from '../types'

function signalStyle(p: PredictionSignal) {
  if (p === 'BUY') return 'text-up border-up/40 bg-up/10'
  if (p === 'SELL') return 'text-down border-down/40 bg-down/10'
  return 'text-terminal-muted border-terminal-border bg-terminal-elevated'
}

function signalGlow(p: PredictionSignal) {
  if (p === 'BUY') return 'shadow-[0_0_16px_rgba(62,232,176,0.2)]'
  if (p === 'SELL') return 'shadow-[0_0_16px_rgba(255,107,107,0.15)]'
  return ''
}

function ConfidenceBar({ value, signal }: { value: number; signal: PredictionSignal }) {
  const mounted = useRef(false)
  const [width, setWidth] = useState(0)

  useEffect(() => {
    if (mounted.current) return
    mounted.current = true
    const t = requestAnimationFrame(() => setWidth(value * 100))
    return () => cancelAnimationFrame(t)
  }, [value])

  const color = signal === 'BUY' ? 'bg-up' : signal === 'SELL' ? 'bg-down' : 'bg-terminal-muted'
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-terminal-elevated">
      <div
        className={`h-full rounded-full ${color} transition-all duration-1000 ease-out`}
        style={{ width: `${width}%` }}
      />
    </div>
  )
}

function FeatureBar({ weight, delay }: { weight: number; delay: number }) {
  const [w, setW] = useState(0)
  useEffect(() => {
    const t = setTimeout(() => setW(weight * 100), delay)
    return () => clearTimeout(t)
  }, [weight, delay])
  return (
    <div className="h-2 flex-1 overflow-hidden rounded-full bg-terminal-bg">
      <div
        className="h-full rounded-full bg-gradient-to-r from-forex to-accent transition-all duration-1000 ease-out"
        style={{ width: `${w}%` }}
      />
    </div>
  )
}

const confusion = [
  [118, 12, 8],
  [14, 96, 18],
  [9, 15, 142],
]

// Global aggregated features (static demo)
const GLOBAL_FEATURES = [
  { n: 'RSI momentum', w: 0.22 },
  { n: 'News sentiment', w: 0.19 },
  { n: 'Volatility regime', w: 0.16 },
  { n: 'Cross-asset beta', w: 0.14 },
  { n: 'Macro surprise index', w: 0.11 },
]

export function PredictionLab() {
  const { selectedSymbol } = useTerminal()
  const { assets } = useData()

  const selectedAsset = assets.find((a) => a.symbol === selectedSymbol)

  return (
    <PageLayout className="page-enter">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-terminal-muted">ML signals</p>
          <h1 className="mt-1 text-2xl font-bold text-terminal-text">Model outputs</h1>
          <p className="mt-1 text-[12px] text-terminal-muted">
            Selected:{' '}
            <span className="font-mono text-accent">{selectedSymbol}</span>
          </p>
        </div>
        <Link to="/" className="text-sm text-accent hover:underline">
          ← Dashboard
        </Link>
      </div>

      {/* Selected asset signal spotlight */}
      {selectedAsset && (
        <div className={`mb-6 animate-fade-up rounded-xl border p-5 ${signalGlow(selectedAsset.prediction)} ${
          selectedAsset.prediction === 'BUY'
            ? 'border-up/30 bg-gradient-to-r from-up/5 to-transparent'
            : selectedAsset.prediction === 'SELL'
              ? 'border-down/30 bg-gradient-to-r from-down/5 to-transparent'
              : 'border-terminal-border bg-terminal-surface'
        }`}>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className={`flex h-14 w-14 items-center justify-center rounded-xl border text-lg font-bold ${signalStyle(selectedAsset.prediction)}`}>
                {selectedAsset.prediction}
              </div>
              <div>
                <p className="font-mono text-[13px] font-semibold text-terminal-text">{selectedAsset.symbol}</p>
                <p className="text-[11px] text-terminal-muted">{selectedAsset.name}</p>
                <div className="mt-1 flex items-center gap-2">
                  <MarketTag market={selectedAsset.market} />
                  <span className="font-mono text-[11px] text-terminal-muted">{selectedAsset.modelVersion}</span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              {[
                { label: 'Confidence', value: `${(selectedAsset.confidence * 100).toFixed(0)}%`, cls: 'text-terminal-text' },
                { label: 'P(up)',      value: `${(selectedAsset.probUp * 100).toFixed(0)}%`,    cls: 'text-up' },
                { label: 'P(down)',   value: `${(selectedAsset.probDown * 100).toFixed(0)}%`,  cls: 'text-down' },
              ].map((m) => (
                <div key={m.label}>
                  <p className="font-mono text-xl font-bold {m.cls} {m.cls}">{m.value}</p>
                  <p className="text-[10px] text-terminal-muted">{m.label}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4">
            <p className="mb-1.5 text-[10px] uppercase tracking-wide text-terminal-muted">
              Confidence ({(selectedAsset.confidence * 100).toFixed(0)}%)
            </p>
            <ConfidenceBar value={selectedAsset.confidence} signal={selectedAsset.prediction} />
          </div>
          {selectedAsset.topFeatures.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-[10px] uppercase tracking-wide text-terminal-muted">Top features</p>
              <div className="space-y-1.5">
                {selectedAsset.topFeatures.map((f, i) => (
                  <div key={f.name} className="flex items-center gap-2">
                    <FeatureBar weight={f.weight * 5} delay={i * 100 + 200} />
                    <span className="w-40 text-right font-mono text-[10px] text-terminal-muted">{f.name}</span>
                    <span className="w-8 text-right font-mono text-[10px] text-accent">{(f.weight * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        {/* All assets signals */}
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 animate-fade-up delay-75">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">Prediction by asset</h2>
          <div className="space-y-2">
            {assets.map((a, i) => (
              <div
                key={a.symbol}
                className={`animate-fade-up delay-${Math.min(i * 75, 450)} flex flex-wrap items-center justify-between gap-2 rounded-lg border border-terminal-border/60 px-3 py-2 transition hover:bg-terminal-elevated/40`}
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[13px] font-semibold text-terminal-text">{a.symbol}</span>
                  <MarketTag market={a.market} />
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-24">
                    <ConfidenceBar value={a.confidence} signal={a.prediction} />
                  </div>
                  <span className={`rounded border px-2 py-0.5 text-xs font-bold ${signalStyle(a.prediction)} ${signalGlow(a.prediction)}`}>
                    {a.prediction}
                  </span>
                  <span className="w-10 text-right font-mono text-[11px] text-terminal-muted">
                    {(a.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model performance */}
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 animate-fade-up delay-150">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">Model performance (demo)</h2>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            {[
              { label: 'Accuracy', value: '0.84' },
              { label: 'F1 (macro)', value: '0.79' },
              { label: 'AUC', value: '0.88' },
              { label: 'Calibration', value: 'ECE 0.04' },
            ].map((m, i) => (
              <div key={m.label} className={`animate-scale-in delay-${i * 75 + 200} rounded-lg bg-terminal-elevated/50 p-3`}>
                <dt className="text-[11px] text-terminal-muted">{m.label}</dt>
                <dd className="font-mono text-xl font-bold text-terminal-text">{m.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        {/* Feature importance */}
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 animate-fade-up delay-225">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">Feature importance (global)</h2>
          <div className="space-y-3">
            {GLOBAL_FEATURES.map((f, i) => (
              <div key={f.n} className="flex items-center gap-3">
                <span className="w-36 shrink-0 text-[11px] text-terminal-muted">{f.n}</span>
                <FeatureBar weight={f.w * 5} delay={i * 120 + 400} />
                <span className="w-8 text-right font-mono text-[11px] text-accent">{(f.w * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Confusion matrix */}
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 animate-fade-up delay-300">
          <h2 className="mb-1 text-xs font-bold uppercase text-terminal-muted">Confusion matrix (demo)</h2>
          <p className="mb-3 text-[10px] text-terminal-muted">Rows: actual · Cols: predicted (Sell / Hold / Buy)</p>
          <div className="grid grid-cols-4 gap-1 font-mono text-[11px]">
            <div />
            <div className="p-2 text-center text-terminal-muted">Sell</div>
            <div className="p-2 text-center text-terminal-muted">Hold</div>
            <div className="p-2 text-center text-terminal-muted">Buy</div>
            {['Sell', 'Hold', 'Buy'].map((label, i) => (
              <Fragment key={label}>
                <div className="flex items-center text-[11px] text-terminal-muted">{label}</div>
                {confusion[i].map((cell, j) => (
                  <div
                    key={j}
                    className={`animate-scale-in rounded-lg border px-2 py-2 text-center font-semibold transition delay-${(i * 3 + j) * 50 + 300} ${
                      i === j
                        ? 'border-up/35 bg-up/10 text-up'
                        : 'border-terminal-border bg-terminal-elevated text-terminal-muted'
                    }`}
                  >
                    {cell}
                  </div>
                ))}
              </Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Recent signals table */}
      <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 animate-fade-up delay-375">
        <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">Live signals</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-terminal-border text-terminal-muted">
                <th className="pb-2 pr-4">Asset</th>
                <th className="pb-2 pr-4">Signal</th>
                <th className="pb-2 pr-4">Confidence</th>
                <th className="pb-2 pr-4">P(up)</th>
                <th className="pb-2">P(down)</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((a, i) => (
                <tr key={a.symbol} className={`animate-row-in border-b border-terminal-border/60 delay-${Math.min(i * 75, 525)}`}>
                  <td className="py-2 pr-4">
                    <span className="font-mono font-semibold text-terminal-text">{a.symbol}</span>
                  </td>
                  <td className="py-2 pr-4">
                    <span className={`rounded border px-2 py-0.5 font-bold ${signalStyle(a.prediction)} ${signalGlow(a.prediction)}`}>
                      {a.prediction}
                    </span>
                  </td>
                  <td className="py-2 pr-4 font-mono text-terminal-text">{(a.confidence * 100).toFixed(0)}%</td>
                  <td className="py-2 pr-4 font-mono text-up">{(a.probUp * 100).toFixed(0)}%</td>
                  <td className="py-2 font-mono text-down">{(a.probDown * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[11px] text-terminal-muted">
          Signals derived from Gold layer features · model: <span className="font-mono text-terminal-text">{assets[0]?.modelVersion ?? 'xgb-v2'}</span>
        </p>
      </div>
    </PageLayout>
  )
}
