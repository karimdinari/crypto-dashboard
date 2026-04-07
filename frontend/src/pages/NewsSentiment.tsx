import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { NEWS } from '../data/mock'
import { useData } from '../context/DataContext'
import { useTerminal } from '../context/TerminalContext'
import type { NewsItem, SentimentLabel } from '../types'
import { SentimentSparkline } from '../components/SentimentSparkline'
import { MarketTag } from '../components/MarketTag'

export function NewsSentiment() {
  const { selectedSymbol } = useTerminal()
  const { assets } = useData()
  const [tableNews, setTableNews] = useState<NewsItem[]>(NEWS)

  useEffect(() => {
    let c = false
    fetch('/api/news?limit=100')
      .then((r) => (r.ok ? r.json() : []))
      .then((rows: unknown) => {
        if (c) return
        if (Array.isArray(rows) && rows.length > 0) setTableNews(rows as NewsItem[])
        else setTableNews(NEWS)
      })
      .catch(() => {
        if (!c) setTableNews(NEWS)
      })
    return () => {
      c = true
    }
  }, [])

  const sentimentMix = useMemo(() => {
    let pos = 0
    let neg = 0
    let neu = 0
    for (const n of tableNews) {
      const s = n.sentiment as SentimentLabel
      if (s === 'positive') pos += 1
      else if (s === 'negative') neg += 1
      else neu += 1
    }
    const t = pos + neg + neu || 1
    return {
      posPct: Math.round((pos / t) * 100),
      negPct: Math.round((neg / t) * 100),
    }
  }, [tableNews])

  const byAsset = assets.map((a) => ({
    symbol: a.symbol,
    market: a.market,
    score: a.sentimentScore,
    articles: a.newsCount24h,
  }))

  const keywords = [
    { term: 'rates', count: 42 },
    { term: 'ETF', count: 38 },
    { term: 'inflation', count: 31 },
    { term: 'halving', count: 28 },
    { term: 'ECB', count: 22 },
  ]

  return (
    <PageLayout>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-terminal-muted">
            News & Sentiment
          </p>
          <h1 className="mt-1 text-2xl font-bold text-terminal-text">
            Research desk
          </h1>
        </div>
        <Link to="/" className="text-sm text-accent hover:underline">
          ← Market Terminal
        </Link>
      </div>

      <p className="mb-4 text-sm text-terminal-muted">
        Focus symbol from terminal:{' '}
        <span className="font-mono text-accent">{selectedSymbol}</span>
      </p>

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 lg:col-span-2">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Sentiment by asset
          </h2>
          <div className="space-y-2">
            {byAsset.map((row) => (
              <div
                key={row.symbol}
                className="flex items-center gap-3 rounded-lg border border-terminal-border bg-terminal-elevated/30 px-3 py-2"
              >
                <span className="w-20 font-mono text-sm">{row.symbol}</span>
                <MarketTag market={row.market} />
                <div className="flex flex-1 items-center gap-2">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-terminal-bg">
                    <div
                      className={`h-full rounded-full ${row.score >= 0 ? 'bg-up' : 'bg-down'}`}
                      style={{
                        width: `${Math.min(100, Math.abs(row.score) * 100 + 50)}%`,
                        marginLeft: row.score < 0 ? 'auto' : undefined,
                      }}
                    />
                  </div>
                  <span className="w-12 font-mono text-xs text-terminal-text">
                    {row.score >= 0 ? '+' : ''}
                    {row.score.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Positive vs negative (24h)
          </h2>
          <div className="flex h-40 flex-col justify-end gap-1">
            <div className="flex h-full gap-2">
              <div className="flex flex-1 flex-col justify-end rounded-t bg-up/30">
                <div
                  className="rounded-t bg-up"
                  style={{ height: `${sentimentMix.posPct}%` }}
                  title="positive"
                />
              </div>
              <div className="flex flex-1 flex-col justify-end rounded-t bg-down/30">
                <div
                  className="rounded-t bg-down"
                  style={{ height: `${sentimentMix.negPct}%` }}
                  title="negative"
                />
              </div>
            </div>
            <div className="flex justify-between text-[10px] text-terminal-muted">
              <span>Positive {sentimentMix.posPct}%</span>
              <span>Negative {sentimentMix.negPct}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Article volume by day (mock)
          </h2>
          <div className="flex h-32 items-end gap-1">
            {[40, 55, 48, 62, 58, 71, 65].map((h, i) => (
              <div key={i} className="flex flex-1 flex-col justify-end">
                <div
                  className="rounded-t bg-accent/50"
                  style={{ height: `${h}%` }}
                />
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Top keywords / themes
          </h2>
          <ul className="space-y-2">
            {keywords.map((k) => (
              <li
                key={k.term}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-terminal-text">{k.term}</span>
                <span className="font-mono text-terminal-muted">
                  {k.count}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
        <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
          Latest headlines
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-terminal-border text-terminal-muted">
                <th className="pb-2 pr-4">Headline</th>
                <th className="pb-2 pr-4">Source</th>
                <th className="pb-2 pr-4">Sentiment</th>
                <th className="pb-2">Spark</th>
              </tr>
            </thead>
            <tbody>
              {tableNews.map((n) => (
                <tr
                  key={n.id}
                  className="border-b border-terminal-border/60 hover:bg-terminal-elevated/40"
                >
                  <td className="py-2 pr-4 font-medium text-terminal-text">
                    {n.headline}
                  </td>
                  <td className="py-2 pr-4 text-terminal-muted">{n.source}</td>
                  <td className="py-2 pr-4 capitalize text-terminal-text">
                    {n.sentiment}
                  </td>
                  <td className="py-2">
                    <SentimentSparkline values={n.spark} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="mt-4 text-center text-[11px] text-terminal-muted">
        Compare crypto / forex / metals by wiring segment filters to your
        warehouse.
      </p>
    </PageLayout>
  )
}
