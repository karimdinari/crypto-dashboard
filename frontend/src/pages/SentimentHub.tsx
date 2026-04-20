import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { NEWS } from '../data/mock'
import { useData } from '../context/DataContext'
import type { NewsItem, SentimentLabel } from '../types'

export function SentimentHub() {
  const { assets } = useData()
  const [rows, setRows] = useState<NewsItem[]>(NEWS)

  useEffect(() => {
    let c = false
    fetch('/api/news?limit=200')
      .then((r) => (r.ok ? r.json() : []))
      .then((data: unknown) => {
        if (c) return
        if (Array.isArray(data) && data.length > 0) setRows(data as NewsItem[])
        else setRows(NEWS)
      })
      .catch(() => {
        if (!c) setRows(NEWS)
      })
    return () => {
      c = true
    }
  }, [])

  const mix = useMemo(() => {
    let pos = 0
    let neg = 0
    let neu = 0
    for (const n of rows) {
      if (n.sentiment === 'positive') pos += 1
      else if (n.sentiment === 'negative') neg += 1
      else neu += 1
    }
    const t = pos + neg + neu || 1
    return {
      pos,
      neg,
      neu,
      posPct: (pos / t) * 100,
      negPct: (neg / t) * 100,
      neuPct: (neu / t) * 100,
      avg:
        rows.reduce((s, n) => {
          const v: Record<SentimentLabel, number> = {
            positive: 1,
            neutral: 0,
            negative: -1,
          }
          return s + v[n.sentiment]
        }, 0) / (rows.length || 1),
    }
  }, [rows])

  return (
    <PageLayout className="max-w-[1800px]">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-terminal-muted">
            NLP layer
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-terminal-text md:text-3xl">
            Sentiment intelligence
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-terminal-muted">
            Headline-level scores from the news ingestion path, blended with market features in Gold for
            downstream models.
          </p>
        </div>
        <Link
          to="/news"
          className="rounded-lg border border-terminal-border bg-terminal-elevated px-3 py-2 text-[12px] font-medium text-accent hover:border-accent/40"
        >
          Full news desk →
        </Link>
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-4">
        {[
          { label: 'Positive', value: mix.pos, pct: mix.posPct, color: 'text-up', bar: 'bg-up/80' },
          { label: 'Neutral', value: mix.neu, pct: mix.neuPct, color: 'text-terminal-muted', bar: 'bg-terminal-muted/60' },
          { label: 'Negative', value: mix.neg, pct: mix.negPct, color: 'text-down', bar: 'bg-down/80' },
          {
            label: 'Avg score',
            value: null,
            sub: `${mix.avg >= 0 ? '+' : ''}${mix.avg.toFixed(2)}`,
            color: 'text-terminal-text',
            bar: null,
          },
        ].map((c) => (
          <div key={c.label} className="glass-panel rounded-xl border border-terminal-border/80 p-4">
            <p className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">{c.label}</p>
            {c.value != null ? (
              <>
                <p className={`mt-2 text-3xl font-bold tabular-nums ${c.color}`}>{c.value}</p>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-terminal-bg">
                  {c.bar && (
                    <div className={`h-full rounded-full ${c.bar}`} style={{ width: `${c.pct}%` }} />
                  )}
                </div>
                <p className="mt-1 font-mono text-[11px] text-terminal-muted">{c.pct.toFixed(0)}% of sample</p>
              </>
            ) : (
              <p className={`mt-2 font-mono text-3xl font-bold tabular-nums ${c.color}`}>{c.sub}</p>
            )}
          </div>
        ))}
      </div>

      <div className="glass-panel rounded-xl border border-terminal-border/80 p-4">
        <h2 className="text-xs font-bold uppercase tracking-wide text-terminal-muted">By asset (24h)</h2>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {assets.map((a) => (
            <div
              key={a.symbol}
              className="flex items-center justify-between rounded-lg border border-terminal-border/60 bg-terminal-bg/50 px-3 py-2"
            >
              <span className="font-mono text-sm text-terminal-text">{a.symbol}</span>
              <span
                className={`font-mono text-sm font-semibold ${
                  a.sentimentScore >= 0.1 ? 'text-up' : a.sentimentScore <= -0.1 ? 'text-down' : 'text-terminal-muted'
                }`}
              >
                {a.sentimentScore >= 0 ? '+' : ''}
                {a.sentimentScore.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </PageLayout>
  )
}
