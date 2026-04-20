import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PIPELINE_LAST_REFRESH as MOCK_PIPELINE_REFRESH, newsForSymbol } from '../data/mock'
import { useData } from '../context/DataContext'
import { useTerminal } from '../context/TerminalContext'
import { PriceChart } from '../components/PriceChart'
import { MarketTag } from '../components/MarketTag'
import { SentimentSparkline } from '../components/SentimentSparkline'
import { CorrelationHeatmap } from '../components/dashboard/CorrelationHeatmap'
import { AISignalCard } from '../components/dashboard/AISignalCard'
import { TechnicalPanel } from '../components/dashboard/TechnicalPanel'
import { buildAssetCorrelation } from '../lib/correlationMatrix'
import type { Asset, NewsItem, SentimentLabel } from '../types'

const PINNED = ['BTC/USD', 'ETH/USD', 'EUR/USD', 'GBP/USD', 'XAU/USD', 'XAG/USD'] as const
const timeframes = ['1H', '4H', '1D', '1W'] as const

function sentimentDot(s: SentimentLabel) {
  const map = {
    positive: 'bg-up shadow-[0_0_6px_rgba(52,211,153,0.45)]',
    neutral: 'bg-terminal-muted',
    negative: 'bg-down shadow-[0_0_6px_rgba(248,113,113,0.4)]',
  }
  return <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${map[s]}`} aria-hidden />
}

function watchlistAccent(m: Asset['market'], active: boolean) {
  const base = 'border-l-2 '
  if (m === 'crypto') return base + (active ? 'border-l-crypto' : 'border-l-crypto/25')
  if (m === 'forex') return base + (active ? 'border-l-forex' : 'border-l-forex/25')
  return base + (active ? 'border-l-metals' : 'border-l-metals/25')
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function ohlcFromAsset(asset: Asset) {
  const c = asset.price; const drift = asset.changePct / 100
  const o = c / (1 + drift * 0.35)
  const w = Math.max(c * 0.0005, Math.abs(drift) * c * 0.25)
  return { o, h: Math.max(o, c) + w * 0.55, l: Math.min(o, c) - w * 0.55, c }
}

function fmtPx(asset: Asset, v: number) {
  if (asset.price > 500) return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  if (asset.price > 10) return v.toFixed(3)
  return v.toFixed(5)
}

function groupSummary(assets: Asset[], market: Asset['market']) {
  const g = assets.filter((a) => a.market === market)
  if (!g.length) return { avg: 0, n: 0 }
  return { avg: g.reduce((s, a) => s + a.changePct, 0) / g.length, n: g.length }
}

export function MarketTerminal() {
  const {
    selectedSymbol, setSelectedSymbol, timeframe, setTimeframe,
    marketFilter, setMarketFilter, chartStyle, setChartStyle, terminalSearch,
  } = useTerminal()

  const {
    assets, getAsset, source, loadError, pipeline, refresh,
    kafkaStreamTicks, kafkaStreamUpdatedAt, getKafkaPrice,
  } = useData()

  const [headlines, setHeadlines] = useState<NewsItem[]>([])
  const [clock, setClock] = useState(() => new Date())

  useEffect(() => {
    const id = window.setInterval(() => setClock(new Date()), 1000)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    let cancelled = false
    fetch(`/api/news?symbol=${encodeURIComponent(selectedSymbol)}&limit=24`)
      .then((r) => (r.ok ? r.json() : []))
      .then((rows) => {
        if (!cancelled) setHeadlines(Array.isArray(rows) && rows.length > 0 ? rows : newsForSymbol(selectedSymbol))
      })
      .catch(() => { if (!cancelled) setHeadlines(newsForSymbol(selectedSymbol)) })
    return () => { cancelled = true }
  }, [selectedSymbol])

  const asset = getAsset(selectedSymbol)
  const news = headlines.length ? headlines : newsForSymbol(selectedSymbol)
  const pipelineRefresh = pipeline?.last_refresh ?? MOCK_PIPELINE_REFRESH
  const livePx = asset ? (getKafkaPrice(asset.symbol) ?? asset.price) : null
  const ohlc = asset ? ohlcFromAsset(asset) : null

  const q = terminalSearch.trim().toLowerCase()
  const filtered = useMemo(() => {
    const list = assets.filter((a) => {
      if (marketFilter !== 'all' && a.market !== marketFilter) return false
      return !(q && !a.symbol.toLowerCase().includes(q) && !a.name.toLowerCase().includes(q))
    })
    const pinIndex = (s: string) => { const i = PINNED.indexOf(s as any); return i === -1 ? 999 : i }
    return list.sort((a, b) => pinIndex(a.symbol) - pinIndex(b.symbol) || a.symbol.localeCompare(b.symbol))
  }, [assets, marketFilter, q])

  const cryptoG = groupSummary(assets, 'crypto')
  const forexG = groupSummary(assets, 'forex')
  const metalsG = groupSummary(assets, 'metals')

  const avgSent = assets.length ? assets.reduce((s, a) => s + a.sentimentScore, 0) / assets.length : 0
  const newsCount = assets.reduce((s, a) => s + a.newsCount24h, 0)

  const sentMix = useMemo(() => {
    let pos = 0; let neg = 0; let neu = 0
    for (const n of news) {
      if (n.sentiment === 'positive') pos++
      else if (n.sentiment === 'negative') neg++
      else neu++
    }
    const t = pos + neg + neu || 1
    return { pos, neg, neu, posPct: (pos / t) * 100, negPct: (neg / t) * 100, neuPct: (neu / t) * 100 }
  }, [news])

  const corr = useMemo(() => buildAssetCorrelation(assets), [assets])

  if (!asset || !ohlc) return null

  return (
    <div className="relative z-10 mx-auto max-w-[1920px] px-3 py-4 md:px-5 lg:py-6 page-enter">
      {(loadError || source === 'mock') && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-amber-500/35 bg-amber-500/10 px-3 py-2.5 text-[12px] text-terminal-text">
          <span>Data: <span className="font-mono font-semibold">{source === 'live' ? 'live Parquet' : 'mock fallback'}</span>{loadError ? ` — ${loadError}` : ''}</span>
          <button type="button" onClick={() => void refresh()} className="rounded-lg border border-terminal-border bg-terminal-surface px-2.5 py-1 font-medium text-accent hover:bg-terminal-elevated">Retry API</button>
        </div>
      )}

      {/* Hero */}
      <section className="mat-hero-deck mb-6 p-5 md:p-7 lg:p-8 animate-fade-up">
        <div className="relative z-10 grid gap-8 lg:grid-cols-12 lg:items-end">
          <div className="lg:col-span-5">
            <p className="font-display text-[10px] font-bold uppercase tracking-[0.28em] text-crypto/90">Market Analytics Terminal</p>
            <h1 className="font-display mt-3 text-2xl font-bold leading-[1.15] tracking-tight text-terminal-text md:text-3xl lg:text-[2rem]">
              Intelligence at
              <span className="block bg-gradient-to-r from-crypto via-terminal-text to-forex bg-clip-text text-transparent">market speed</span>
            </h1>
            <p className="mt-4 max-w-md text-[13px] leading-relaxed text-terminal-muted">
              Live energy from Kafka, depth from Silver & Gold, and model signals — one surface for crypto, forex, and precious metals.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:col-span-7">
            {[
              { t: 'Crypto', sub: `${cryptoG.n} pairs · electric tape`, avg: cryptoG.avg, strip: 'mat-strip-crypto', fg: 'text-crypto' },
              { t: 'Forex',  sub: `${forexG.n} majors · precision`, avg: forexG.avg, strip: 'mat-strip-forex',  fg: 'text-forex' },
              { t: 'Metals', sub: `${metalsG.n} spot · carry & flows`, avg: metalsG.avg, strip: 'mat-strip-metals', fg: 'text-metals' },
            ].map(c => (
              <div key={c.t} className={`rounded-xl border border-white/[0.07] p-4 ${c.strip} transition hover:border-white/12`}>
                <p className={`font-display text-[10px] font-bold uppercase tracking-[0.18em] ${c.fg}`}>{c.t}</p>
                <p className="mt-1 text-[11px] text-terminal-muted/90">{c.sub}</p>
                <p className={`mt-3 font-mono text-2xl font-semibold tabular-nums ${c.avg >= 0 ? 'text-up' : 'text-down'}`}>
                  {c.avg >= 0 ? '+' : ''}{c.avg.toFixed(2)}%
                </p>
              </div>
            ))}
          </div>
        </div>
        <div className="relative z-10 mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-white/[0.06] pt-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-up/40 bg-up/12 px-3 py-1.5 text-[11px] font-medium text-up">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-up shadow-[0_0_10px_rgba(62,232,176,0.7)]" />
              Markets active
            </span>
            <span className="rounded-full border border-white/[0.08] bg-black/25 px-3 py-1.5 font-mono text-[11px] text-terminal-muted">
              Sync <time className="text-terminal-text">{formatTime(pipelineRefresh)}</time>
            </span>
            <span className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold ${kafkaStreamTicks.length ? 'border-crypto/45 bg-crypto/12 text-crypto shadow-[0_0_20px_rgba(0,240,255,0.12)]' : 'border-white/10 text-terminal-muted'}`}>
              Kafka {kafkaStreamTicks.length ? 'streaming' : 'standby'}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-display text-[10px] font-bold uppercase tracking-[0.2em] text-terminal-muted">Narrative sentiment</p>
              <p className="font-mono text-xl font-semibold text-terminal-text">{avgSent >= 0 ? '+' : ''}{avgSent.toFixed(2)}</p>
            </div>
            <p className="text-right text-[11px] text-terminal-muted">
              {newsCount} stories/24h · <Link to="/news" className="text-accent hover:underline">research desk →</Link>
            </p>
          </div>
        </div>
      </section>

      {/* 3-Column Layout */}
      <div className="flex flex-col xl:flex-row gap-4 min-h-[800px]">
        {/* Left Column: Watchlist */}
        <aside className="w-full xl:w-[280px] shrink-0 flex flex-col rounded-xl border border-white/[0.07] bg-terminal-surface/35 glass-panel overflow-hidden animate-slide-right delay-75">
          <div className="p-3 border-b border-white/[0.06]">
            <p className="font-display text-[10px] font-bold uppercase tracking-[0.2em] text-terminal-muted">Watchlist</p>
            <div className="mt-2 flex gap-1">
              {(['all', 'crypto', 'forex', 'metals'] as const).map((m) => (
                <button key={m} onClick={() => setMarketFilter(m)}
                  className={`flex-1 rounded-md py-1.5 text-[10px] font-semibold uppercase transition ${
                    marketFilter === m ? 'bg-terminal-elevated text-terminal-text ring-1 ring-accent/40' : 'text-terminal-muted hover:bg-terminal-elevated/50'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            <table className="w-full text-left text-[11px]">
              <thead className="sticky top-0 bg-terminal-surface/95 backdrop-blur z-10 border-b border-terminal-border/60">
                <tr className="text-terminal-muted"><th className="py-2 pl-3 font-normal">Symbol</th><th className="py-2 pr-1 text-right font-normal">Last</th><th className="py-2 pr-3 text-right font-normal">Chg%</th></tr>
              </thead>
              <tbody>
                {filtered.map((a) => {
                  const active = selectedSymbol === a.symbol
                  const px = getKafkaPrice(a.symbol) ?? a.price
                  return (
                    <tr key={a.symbol} onClick={() => setSelectedSymbol(a.symbol)}
                      className={`cursor-pointer border-b border-terminal-border/30 font-mono transition hover:bg-terminal-elevated/50 ${watchlistAccent(a.market, active)} ${active ? 'bg-terminal-elevated/80' : ''}`}
                    >
                      <td className="py-2 pl-3 text-terminal-text">{a.symbol}</td>
                      <td className="py-2 pr-1 text-right">{px > 100 ? px.toLocaleString(undefined, { maximumFractionDigits: 2 }) : px.toFixed(4)}</td>
                      <td className={`py-2 pr-3 text-right ${a.changePct >= 0 ? 'text-up' : 'text-down'}`}>{a.changePct >= 0 ? '+' : ''}{a.changePct.toFixed(2)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </aside>

        {/* Center Column: Chart & Technicals */}
        <section className="flex-1 flex flex-col min-w-0 gap-4 animate-fade-up delay-150">
          <div className="flex-1 flex flex-col rounded-xl border border-white/[0.08] bg-terminal-bg/90 shadow-[0_24px_64px_rgba(0,0,0,0.45)] overflow-hidden">
            <div className="p-3 md:p-4 border-b border-white/[0.06] bg-gradient-to-b from-terminal-elevated/40 to-terminal-bg/95">
              <div className="flex flex-wrap justify-between items-start gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-display text-2xl font-bold text-terminal-text">{asset.symbol}</h2>
                    <MarketTag market={asset.market} />
                  </div>
                  <p className="mt-1 text-[12px] text-terminal-muted">{asset.name}</p>
                  <p className="mt-1 font-mono text-[11px] text-terminal-muted">
                    O {fmtPx(asset, ohlc.o)} · H {fmtPx(asset, ohlc.h)} · L {fmtPx(asset, ohlc.l)} · C {fmtPx(asset, livePx ?? ohlc.c)}
                    {getKafkaPrice(asset.symbol) != null && <span className="ml-1 text-crypto">stream</span>}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-2xl font-semibold text-terminal-text">
                    {livePx != null && livePx > 100 ? livePx.toLocaleString(undefined, { maximumFractionDigits: 2 }) : (livePx ?? 0).toFixed(5)}
                  </p>
                  <p className={`font-mono text-sm ${asset.changePct >= 0 ? 'text-up' : 'text-down'}`}>
                    {asset.changePct >= 0 ? '+' : ''}{asset.changePct.toFixed(2)}%
                  </p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2 items-center">
                <div className="flex rounded-lg border border-terminal-border/80 bg-terminal-surface/50 p-0.5">
                  {timeframes.map(tf => (
                    <button key={tf} onClick={() => setTimeframe(tf)}
                      className={`px-3 py-1.5 rounded-md font-mono text-[11px] font-medium transition ${timeframe === tf ? 'bg-terminal-elevated text-terminal-text ring-1 ring-accent/50' : 'text-terminal-muted hover:text-terminal-text'}`}>
                      {tf}
                    </button>
                  ))}
                </div>
                <div className="ml-auto font-mono text-[10px] text-terminal-muted">
                  <time>{clock.toISOString().slice(11, 19)} UTC</time>
                </div>
              </div>
            </div>
            <div className="flex-1 min-h-[400px] mat-chart-well">
              <PriceChart />
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <TechnicalPanel asset={asset} />
            <CorrelationHeatmap labels={corr.labels} matrix={corr.matrix} compact />
          </div>
        </section>

        {/* Right Column: Intelligence & Stream */}
        <aside className="w-full xl:w-[340px] shrink-0 flex flex-col gap-4 animate-slide-left delay-225">
          <AISignalCard asset={asset} />

          {/* Sentiment Summary */}
          <div className="glass-panel rounded-xl border border-white/[0.07] p-4">
            <p className="font-display text-[10px] font-bold uppercase tracking-[0.2em] text-terminal-muted">News Sentiment</p>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
              <div className="rounded-lg bg-black/25 py-2 border border-white/[0.04]">
                <p className="font-mono text-lg font-semibold text-up">{sentMix.pos}</p>
                <p className="text-[9px] text-terminal-muted">POS</p>
              </div>
              <div className="rounded-lg bg-black/25 py-2 border border-white/[0.04]">
                <p className="font-mono text-lg font-semibold text-terminal-muted">{sentMix.neu}</p>
                <p className="text-[9px] text-terminal-muted">NEU</p>
              </div>
              <div className="rounded-lg bg-black/25 py-2 border border-white/[0.04]">
                <p className="font-mono text-lg font-semibold text-down">{sentMix.neg}</p>
                <p className="text-[9px] text-terminal-muted">NEG</p>
              </div>
            </div>
          </div>

          {/* Live Headlines */}
          <div className="glass-panel flex flex-col rounded-xl border border-terminal-border/80 flex-1 min-h-[300px] overflow-hidden">
            <div className="border-b border-terminal-border/60 px-3 py-2 flex justify-between items-center">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-terminal-muted">Live Headlines</p>
              <span className="flex h-2 w-2 relative"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span></span>
            </div>
            <ul className="flex-1 overflow-y-auto">
              {news.slice(0, 8).map((item) => (
                <li key={item.id} className="border-b border-terminal-border/40">
                  <a href={item.url} onClick={e => e.preventDefault()} className="block px-3 py-3 transition hover:bg-terminal-elevated/40">
                    <div className="flex gap-2">
                      <div className="mt-1.5">{sentimentDot(item.sentiment)}</div>
                      <span className="text-[12px] leading-snug text-terminal-text">{item.headline}</span>
                    </div>
                    <div className="mt-2 pl-4 flex items-center justify-between">
                      <span className="text-[9px] uppercase text-terminal-muted/80">{item.source}</span>
                      <SentimentSparkline values={item.spark} />
                    </div>
                  </a>
                </li>
              ))}
            </ul>
            <Link to="/news" className="border-t border-terminal-border/60 py-2.5 text-center text-[11px] font-medium text-accent hover:bg-terminal-elevated/30">
              All news →
            </Link>
          </div>
        </aside>
      </div>
    </div>
  )
}
