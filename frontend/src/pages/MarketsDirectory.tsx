import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { MarketTag } from '../components/MarketTag'
import { useData } from '../context/DataContext'
import { useTerminal } from '../context/TerminalContext'
import type { MarketType } from '../types'

const groups: { key: MarketType; title: string; desc: string; accent: string }[] = [
  {
    key: 'crypto',
    title: 'Crypto',
    desc: 'Digital assets · on-chain + macro beta',
    accent: 'border-crypto/40 shadow-[0_0_24px_rgba(34,211,238,0.08)]',
  },
  {
    key: 'forex',
    title: 'Forex',
    desc: 'G10 majors · policy & carry',
    accent: 'border-forex/40 shadow-[0_0_24px_rgba(167,139,250,0.08)]',
  },
  {
    key: 'metals',
    title: 'Precious metals',
    desc: 'Gold & silver · real yields',
    accent: 'border-metals/45 shadow-[0_0_24px_rgba(251,191,36,0.08)]',
  },
]

export function MarketsDirectory() {
  const { assets } = useData()
  const { setSelectedSymbol } = useTerminal()

  return (
    <PageLayout className="max-w-[1800px]">
      <div className="mb-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-terminal-muted">
          Universe
        </p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-terminal-text md:text-3xl">
          Markets
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-terminal-muted">
          Cross-asset coverage aligned with the lakehouse: batch OHLCV in Silver, enriched features in
          Gold, and Kafka ticks for live monitoring.
        </p>
      </div>

      <div className="space-y-8">
        {groups.map((g) => {
          const rows = assets.filter((a) => a.market === g.key)
          return (
            <section key={g.key}>
              <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
                <div>
                  <h2 className="flex items-center gap-2 text-lg font-bold text-terminal-text">
                    {g.title}
                    <MarketTag market={g.key} />
                  </h2>
                  <p className="text-[13px] text-terminal-muted">{g.desc}</p>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {rows.map((a) => (
                  <Link
                    key={a.symbol}
                    to="/"
                    onClick={() => setSelectedSymbol(a.symbol)}
                    className={`glass-panel rounded-xl border p-4 transition hover:border-accent/30 ${g.accent}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-mono text-base font-semibold text-terminal-text">{a.symbol}</p>
                        <p className="text-[12px] text-terminal-muted">{a.name}</p>
                      </div>
                      <span
                        className={`font-mono text-sm font-semibold ${
                          a.changePct >= 0 ? 'text-up' : 'text-down'
                        }`}
                      >
                        {a.changePct >= 0 ? '+' : ''}
                        {a.changePct.toFixed(2)}%
                      </span>
                    </div>
                    <p className="mt-3 font-mono text-xl font-semibold text-terminal-text">
                      {a.price > 500
                        ? a.price.toLocaleString(undefined, { maximumFractionDigits: 2 })
                        : a.price.toFixed(a.price > 10 ? 3 : 5)}
                    </p>
                    <p className="mt-2 text-[11px] text-terminal-muted">
                      Open terminal →{' '}
                      <span className="text-accent">live chart & signals</span>
                    </p>
                  </Link>
                ))}
              </div>
            </section>
          )
        })}
      </div>
    </PageLayout>
  )
}
