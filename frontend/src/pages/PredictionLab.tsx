import { Fragment } from 'react'
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

export function PredictionLab() {
  const { selectedSymbol } = useTerminal()
  const { assets } = useData()

  const signals = [
    { asset: 'BTC/USD', sig: 'BUY' as const, conf: 0.78, at: '16:38 UTC' },
    { asset: 'GBP/USD', sig: 'SELL' as const, conf: 0.66, at: '15:55 UTC' },
    { asset: 'ETH/USD', sig: 'HOLD' as const, conf: 0.55, at: '15:40 UTC' },
    { asset: 'XAU/USD', sig: 'BUY' as const, conf: 0.71, at: '14:22 UTC' },
  ]

  const confusion = [
    [118, 12, 8],
    [14, 96, 18],
    [9, 15, 142],
  ]

  return (
    <PageLayout>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-terminal-muted">
            Prediction Lab
          </p>
          <h1 className="mt-1 text-2xl font-bold text-terminal-text">
            ML layer
          </h1>
        </div>
        <Link to="/" className="text-sm text-accent hover:underline">
          ← Market Terminal
        </Link>
      </div>

      <p className="mb-6 text-sm text-terminal-muted">
        Selected from terminal:{' '}
        <span className="font-mono text-accent">{selectedSymbol}</span>
      </p>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Prediction by asset
          </h2>
          <div className="space-y-2">
            {assets.map((a) => (
              <div
                key={a.symbol}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-terminal-border px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm">{a.symbol}</span>
                  <MarketTag market={a.market} />
                </div>
                <span
                  className={`rounded border px-2 py-0.5 text-xs font-bold ${signalStyle(a.prediction)}`}
                >
                  {a.prediction}
                </span>
                <span className="font-mono text-xs text-terminal-muted">
                  {(a.confidence * 100).toFixed(0)}% conf
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Model performance (mock)
          </h2>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg bg-terminal-elevated/50 p-3">
              <dt className="text-terminal-muted">Accuracy</dt>
              <dd className="font-mono text-lg text-terminal-text">0.84</dd>
            </div>
            <div className="rounded-lg bg-terminal-elevated/50 p-3">
              <dt className="text-terminal-muted">F1 (macro)</dt>
              <dd className="font-mono text-lg text-terminal-text">0.79</dd>
            </div>
            <div className="rounded-lg bg-terminal-elevated/50 p-3">
              <dt className="text-terminal-muted">AUC</dt>
              <dd className="font-mono text-lg text-terminal-text">0.88</dd>
            </div>
            <div className="rounded-lg bg-terminal-elevated/50 p-3">
              <dt className="text-terminal-muted">Calibration</dt>
              <dd className="font-mono text-lg text-terminal-text">ECE 0.04</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Feature importance (global)
          </h2>
          <div className="space-y-2">
            {[
              { n: 'RSI momentum', w: 0.22 },
              { n: 'News sentiment', w: 0.19 },
              { n: 'Volatility regime', w: 0.16 },
              { n: 'Cross-asset beta', w: 0.14 },
              { n: 'Macro surprise index', w: 0.11 },
            ].map((f) => (
              <div key={f.n} className="flex items-center gap-2">
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-terminal-bg">
                  <div
                    className="h-full rounded-full bg-purple-500"
                    style={{ width: `${f.w * 400}%` }}
                  />
                </div>
                <span className="w-40 text-right font-mono text-[10px] text-terminal-muted">
                  {f.n}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Confusion matrix (mock)
          </h2>
          <p className="mb-2 text-[10px] text-terminal-muted">
            Rows: actual · Cols: predicted (Sell / Hold / Buy)
          </p>
          <div className="grid grid-cols-4 gap-1 font-mono text-[11px]">
            <div />
            <div className="p-2 text-center text-terminal-muted">Sell</div>
            <div className="p-2 text-center text-terminal-muted">Hold</div>
            <div className="p-2 text-center text-terminal-muted">Buy</div>
            {['Sell', 'Hold', 'Buy'].map((label, i) => (
              <Fragment key={label}>
                <div className="flex items-center text-terminal-muted">
                  {label}
                </div>
                {confusion[i].map((cell, j) => (
                  <div
                    key={j}
                    className="rounded border border-terminal-border bg-terminal-elevated p-2 text-center text-terminal-text"
                  >
                    {cell}
                  </div>
                ))}
              </Fragment>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
        <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
          Recent generated signals
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-terminal-border text-terminal-muted">
                <th className="pb-2 pr-4">Asset</th>
                <th className="pb-2 pr-4">Signal</th>
                <th className="pb-2 pr-4">Confidence</th>
                <th className="pb-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s) => (
                <tr key={s.at + s.asset} className="border-b border-terminal-border/60">
                  <td className="py-2 pr-4 font-mono">{s.asset}</td>
                  <td className="py-2 pr-4">
                    <span
                      className={`rounded border px-2 py-0.5 font-bold ${signalStyle(s.sig)}`}
                    >
                      {s.sig}
                    </span>
                  </td>
                  <td className="py-2 pr-4 font-mono">
                    {(s.conf * 100).toFixed(0)}%
                  </td>
                  <td className="py-2 text-terminal-muted">{s.at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[11px] text-terminal-muted">
          Success rate (recent paper trades, mock):{' '}
          <span className="font-mono text-up">61%</span> over last 50 signals.
        </p>
      </div>
    </PageLayout>
  )
}
