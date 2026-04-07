import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { useTerminal } from '../context/TerminalContext'
import { useData } from '../context/DataContext'
import { PriceChart } from '../components/PriceChart'
import { MarketTag } from '../components/MarketTag'
import { SentimentSparkline } from '../components/SentimentSparkline'

function miniBars(values: number[]) {
  const max = Math.max(...values, 0.001)
  return (
    <div className="flex h-12 items-end gap-0.5">
      {values.map((v, i) => (
        <div
          key={i}
          className="flex-1 rounded-t bg-gradient-to-t from-accent/40 to-accent"
          style={{ height: `${(v / max) * 100}%`, minHeight: '4px' }}
        />
      ))}
    </div>
  )
}

export function AssetAnalysis() {
  const { selectedSymbol, setSelectedSymbol } = useTerminal()
  const { getAsset, assets } = useData()
  const asset = getAsset(selectedSymbol)

  const volRoll = [2.1, 2.4, 2.0, 2.8, 2.3, 2.5, 2.2, 2.6]
  const sentimentSeries = [0.1, 0.15, 0.2, 0.08, 0.25, 0.3, 0.35, 0.42]
  const corrPoints = [0.2, 0.35, 0.28, 0.5, 0.45, 0.62, 0.55, 0.7]

  if (!asset) return null

  return (
    <PageLayout>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-terminal-muted">
            Asset Analysis
          </p>
          <h1 className="mt-1 flex flex-wrap items-center gap-3 text-2xl font-bold text-terminal-text">
            <span className="font-mono">{asset.symbol}</span>
            <MarketTag market={asset.market} />
          </h1>
        </div>
        <Link
          to="/"
          className="text-sm text-accent hover:underline"
        >
          ← Market Terminal
        </Link>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {assets.map((a) => (
            <button
              key={a.symbol}
              type="button"
              onClick={() => setSelectedSymbol(a.symbol)}
              className={`rounded-lg border px-3 py-1.5 font-mono text-xs ${
                selectedSymbol === a.symbol
                  ? 'border-accent bg-accent/15 text-accent'
                  : 'border-terminal-border text-terminal-muted hover:border-terminal-text'
              }`}
            >
              {a.symbol}
            </button>
          ))}
      </div>

      <div className="mb-6 min-h-[380px] rounded-xl border border-terminal-border bg-terminal-surface p-4">
        <p className="mb-2 text-[10px] font-bold uppercase text-terminal-muted">
          Multi-timeframe price (uses terminal timeframe)
        </p>
        <PriceChart />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-2 text-xs font-bold uppercase text-terminal-muted">
            Rolling volatility
          </h2>
          {miniBars(volRoll)}
          <p className="mt-2 font-mono text-[11px] text-terminal-muted">
            8-period mock roll · wire to your features
          </p>
        </div>
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-2 text-xs font-bold uppercase text-terminal-muted">
            Sentiment over time
          </h2>
          <SentimentSparkline
            values={sentimentSeries}
            className="h-8 w-full max-w-[200px]"
          />
          <p className="mt-2 font-mono text-[11px] text-terminal-muted">
            Aggregated NLP score (demo)
          </p>
        </div>
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 md:col-span-2 lg:col-span-1">
          <h2 className="mb-2 text-xs font-bold uppercase text-terminal-muted">
            Price vs sentiment (correlation sketch)
          </h2>
          <SentimentSparkline values={corrPoints} className="h-10 w-full" />
          <p className="mt-2 text-[11px] text-terminal-muted">
            Overlay real correlation from your Silver/Gold tables.
          </p>
        </div>
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 md:col-span-2">
          <h2 className="mb-2 text-xs font-bold uppercase text-terminal-muted">
            Return distribution (mock)
          </h2>
          <div className="flex h-24 items-end gap-1">
            {[
              2, 5, 12, 28, 45, 38, 22, 14, 8, 4, 2, 1, 3, 6, 4, 2, 1, 0.5,
            ].map((h, i) => (
              <div
                key={i}
                className="flex-1 rounded-t bg-sky-500/40"
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </div>
      </div>
    </PageLayout>
  )
}
