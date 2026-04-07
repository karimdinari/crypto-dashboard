import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  PIPELINE_LAST_REFRESH as MOCK_PIPELINE_REFRESH,
  newsForSymbol,
} from '../data/mock'
import { useData } from '../context/DataContext'
import { useTerminal } from '../context/TerminalContext'
import { useTheme } from '../context/ThemeContext'
import { PriceChart } from '../components/PriceChart'
import { MarketTag } from '../components/MarketTag'
import { SentimentSparkline } from '../components/SentimentSparkline'
import type {
  Asset,
  NewsItem,
  PredictionSignal,
  SentimentLabel,
  Timeframe,
} from '../types'

const timeframes: Timeframe[] = ['1H', '4H', '1D', '1W']

function sentimentDot(s: SentimentLabel) {
  const map = {
    positive: 'bg-up shadow-[0_0_6px_rgba(38,166,154,0.45)]',
    neutral: 'bg-terminal-muted',
    negative: 'bg-down shadow-[0_0_6px_rgba(239,83,80,0.4)]',
  }
  const label =
    s === 'positive' ? 'Positive sentiment' : s === 'negative' ? 'Negative sentiment' : 'Neutral sentiment'
  return (
    <span
      role="img"
      aria-label={label}
      className={`inline-block h-2 w-2 shrink-0 rounded-full ${map[s]}`}
    />
  )
}

function predBadge(p: PredictionSignal) {
  const map = {
    BUY: 'border-accent/50 bg-accent/15 text-accent',
    SELL: 'border-down/45 bg-down/12 text-down',
    HOLD: 'border-terminal-border bg-terminal-elevated text-terminal-muted',
  }
  return (
    <span
      className={`rounded border px-2.5 py-0.5 text-xs font-bold tracking-wide ${map[p]}`}
    >
      {p}
    </span>
  )
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function ohlcFromAsset(asset: Asset) {
  const c = asset.price
  const drift = asset.changePct / 100
  const o = c / (1 + drift * 0.35)
  const w = Math.max(c * 0.0005, Math.abs(drift) * c * 0.25)
  const h = Math.max(o, c) + w * 0.55
  const l = Math.min(o, c) - w * 0.55
  return { o, h, l, c }
}

function fmtPx(asset: Asset, v: number) {
  if (asset.price > 500)
    return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  if (asset.price > 10) return v.toFixed(3)
  return v.toFixed(5)
}

function performanceForSymbol(symbol: string) {
  let h = 0
  for (let i = 0; i < symbol.length; i++) {
    h = (Math.imul(31, h) + symbol.charCodeAt(i)) | 0
  }
  const u = (i: number) =>
    ((Math.abs(Math.sin(h * 0.1 + i * 1.7)) * 100) % 14) - 5.5
  return [
    { k: '1W', pct: u(1) },
    { k: '1M', pct: u(2) },
    { k: '3M', pct: u(3) },
    { k: '6M', pct: u(4) },
    { k: 'YTD', pct: u(5) },
    { k: '1Y', pct: u(6) },
  ] as const
}

function RsiGauge({ value }: { value: number }) {
  const { theme } = useTheme()
  const clamped = Math.min(100, Math.max(0, value))
  const rot = (clamped / 100) * 180 - 90
  const arc =
    theme === 'light'
      ? 'conic-gradient(from 180deg at 50% 100%, #f23645 0deg, #9598a1 72deg, #089981 180deg)'
      : 'conic-gradient(from 180deg at 50% 100%, #ef5350 0deg, #787b86 72deg, #26a69a 180deg)'
  return (
    <div className="relative mx-auto h-16 w-28">
      <div
        className="absolute inset-0 rounded-t-full border border-terminal-border bg-terminal-bg"
        style={{
          background: arc,
          maskImage: 'radial-gradient(transparent 55%, black 56%)',
          WebkitMaskImage: 'radial-gradient(transparent 55%, black 56%)',
        }}
      />
      <div
        className="absolute bottom-0 left-1/2 h-[46%] w-0.5 origin-bottom bg-terminal-text shadow"
        style={{ transform: `translateX(-50%) rotate(${rot}deg)` }}
      />
      <p className="absolute bottom-1 left-0 right-0 text-center font-mono text-xs text-terminal-text">
        {value.toFixed(1)}
      </p>
    </div>
  )
}

function MacdSparkline({ macd, signal }: { macd: number; signal: number }) {
  const { theme } = useTheme()
  const sigColor = theme === 'light' ? '#9598a1' : '#787b86'
  const pts = Array.from({ length: 14 }, (_, i) => {
    const t = i / 13
    return macd * (0.3 + t * 0.7) + Math.sin(i * 0.6) * (Math.abs(macd) * 0.08)
  })
  const sigPts = Array.from({ length: 14 }, (_, i) => {
    const t = i / 13
    return signal * (0.4 + t * 0.6)
  })
  const w = 120
  const h = 40
  const all = [...pts, ...sigPts]
  const min = Math.min(...all)
  const max = Math.max(...all)
  const r = max - min || 1
  const line = (arr: number[]) =>
    arr
      .map((v, i) => {
        const x = (i / (arr.length - 1)) * w
        const y = h - 4 - ((v - min) / r) * (h - 8)
        return `${x},${y}`
      })
      .join(' ')
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="mx-auto">
      <polyline
        fill="none"
        stroke="#2962ff"
        strokeWidth="1.5"
        points={line(pts)}
      />
      <polyline
        fill="none"
        stroke={sigColor}
        strokeWidth="1"
        strokeDasharray="3 2"
        points={line(sigPts)}
      />
    </svg>
  )
}

export function MarketTerminal() {
  const {
    selectedSymbol,
    setSelectedSymbol,
    timeframe,
    setTimeframe,
    marketFilter,
    setMarketFilter,
    chartStyle,
    setChartStyle,
    watchlistQuery,
    setWatchlistQuery,
  } = useTerminal()

  const {
    assets,
    getAsset,
    source,
    loadError,
    pipeline,
    refresh,
    kafkaStreamTicks,
    kafkaStreamUpdatedAt,
    getKafkaPrice,
  } = useData()
  const [headlines, setHeadlines] = useState<NewsItem[]>([])
  const [clock, setClock] = useState(() => new Date())

  useEffect(() => {
    const id = window.setInterval(() => setClock(new Date()), 1000)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    let cancelled = false
    const url = `/api/news?symbol=${encodeURIComponent(selectedSymbol)}&limit=12`
    fetch(url)
      .then((r) => (r.ok ? r.json() : []))
      .then((rows: unknown) => {
        if (cancelled) return
        if (Array.isArray(rows) && rows.length > 0) {
          setHeadlines(rows as NewsItem[])
        } else {
          setHeadlines(newsForSymbol(selectedSymbol))
        }
      })
      .catch(() => {
        if (!cancelled) setHeadlines(newsForSymbol(selectedSymbol))
      })
    return () => {
      cancelled = true
    }
  }, [selectedSymbol])

  const asset = getAsset(selectedSymbol)
  const news = headlines.length ? headlines : newsForSymbol(selectedSymbol)
  const pipelineRefresh =
    pipeline?.last_refresh ?? MOCK_PIPELINE_REFRESH
  const livePx = asset
    ? (getKafkaPrice(asset.symbol) ?? asset.price)
    : null
  const ohlc = asset ? ohlcFromAsset(asset) : null
  const perf = asset ? performanceForSymbol(asset.symbol) : []
  const spread = livePx != null ? Math.max(livePx * 0.00002, 0.01) : 0
  const bid = livePx != null ? livePx - spread : 0
  const ask = livePx != null ? livePx + spread : 0

  const filtered = assets.filter((a) => {
    if (marketFilter !== 'all' && a.market !== marketFilter) return false
    const q = watchlistQuery.trim().toLowerCase()
    if (
      q &&
      !a.symbol.toLowerCase().includes(q) &&
      !a.name.toLowerCase().includes(q)
    )
      return false
    return true
  })

  const gainer = [...assets].sort((a, b) => b.changePct - a.changePct)[0]
  const loser = [...assets].sort((a, b) => a.changePct - b.changePct)[0]
  const avgSent =
    assets.length > 0
      ? assets.reduce((s, a) => s + a.sentimentScore, 0) / assets.length
      : 0
  const newsCount = assets.reduce((s, a) => s + a.newsCount24h, 0)

  const marketOpen = true

  if (!asset || !ohlc) return null

  const topStory = news[0]

  return (
    <div className="mx-auto max-w-[1600px] px-3 py-4 md:px-5">
      {(loadError || source === 'mock') && (
        <div
          className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-[11px] text-terminal-text"
          role="status"
        >
          <span>
            Data:{' '}
            <span className="font-mono font-semibold">
              {source === 'live' ? 'live Parquet' : 'mock fallback'}
            </span>
            {loadError ? ` — ${loadError}` : ''}
          </span>
          <button
            type="button"
            onClick={() => void refresh()}
            className="rounded-md border border-terminal-border bg-terminal-surface px-2 py-1 font-medium text-accent hover:bg-terminal-elevated"
          >
            Retry API
          </button>
        </div>
      )}
      <div className="mb-4 flex flex-col gap-3 border-b border-terminal-border pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px]">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 ${
              marketOpen
                ? 'border-up/30 bg-up/10 text-up'
                : 'border-terminal-border text-terminal-muted'
            }`}
          >
            <span
              className={`inline-block h-2 w-2 shrink-0 rounded-full ${marketOpen ? 'bg-up' : 'bg-terminal-muted'}`}
              aria-hidden
            />
            <span className="text-terminal-text">
              {marketOpen ? 'Market open' : 'Market closed'}
            </span>
          </span>
          <span className="hidden text-terminal-muted sm:inline" aria-hidden>
            ·
          </span>
          <span className="text-terminal-muted">
            Last pipeline sync{' '}
            <time
              className="font-mono text-terminal-text"
              dateTime={pipelineRefresh}
            >
              {formatTime(pipelineRefresh)}
            </time>
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div
            className="flex rounded-lg border border-terminal-border bg-terminal-surface p-0.5 shadow-sm"
            role="group"
            aria-label="Chart timeframe"
          >
            {timeframes.map((tf) => (
              <button
                key={tf}
                type="button"
                onClick={() => setTimeframe(tf)}
                aria-pressed={timeframe === tf}
                className={`min-h-9 min-w-[2.75rem] rounded-md px-2.5 py-1.5 font-mono text-[11px] font-medium transition-colors duration-150 ${
                  timeframe === tf
                    ? 'bg-terminal-elevated text-terminal-text shadow-sm ring-1 ring-accent/60'
                    : 'text-terminal-muted hover:bg-terminal-elevated/60 hover:text-terminal-text'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
          <div
            className="flex rounded-lg border border-terminal-border bg-terminal-surface p-0.5 shadow-sm"
            role="group"
            aria-label="Chart type"
          >
            <button
              type="button"
              onClick={() => setChartStyle('candle')}
              aria-pressed={chartStyle === 'candle'}
              className={`min-h-9 rounded-md px-3 py-1.5 text-[11px] font-medium transition-colors duration-150 ${
                chartStyle === 'candle'
                  ? 'bg-terminal-elevated text-terminal-text shadow-sm'
                  : 'text-terminal-muted hover:bg-terminal-elevated/60 hover:text-terminal-text'
              }`}
            >
              Candles
            </button>
            <button
              type="button"
              onClick={() => setChartStyle('line')}
              aria-pressed={chartStyle === 'line'}
              className={`min-h-9 rounded-md px-3 py-1.5 text-[11px] font-medium transition-colors duration-150 ${
                chartStyle === 'line'
                  ? 'bg-terminal-elevated text-terminal-text shadow-sm'
                  : 'text-terminal-muted hover:bg-terminal-elevated/60 hover:text-terminal-text'
              }`}
            >
              Line
            </button>
          </div>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {[
          { label: 'Tracked', value: String(assets.length) },
          {
            label: 'Top gainer',
            value: gainer.symbol,
            sub: `+${gainer.changePct.toFixed(2)}%`,
            up: true,
          },
          {
            label: 'Top loser',
            value: loser.symbol,
            sub: `${loser.changePct.toFixed(2)}%`,
            up: false,
          },
          {
            label: 'Avg sentiment',
            value: avgSent >= 0 ? `+${avgSent.toFixed(2)}` : avgSent.toFixed(2),
          },
          { label: 'News 24h', value: String(newsCount) },
          {
            label: 'Pipeline',
            value: source === 'live' ? 'OK' : 'Mock',
            sub: 'Bronze→Gold',
          },
        ].map((k) => (
          <div
            key={k.label}
            className="rounded-md border border-terminal-border bg-terminal-surface px-2.5 py-2 transition-colors duration-150 hover:border-terminal-muted"
          >
            <p className="text-[9px] font-medium uppercase tracking-wide text-terminal-muted">
              {k.label}
            </p>
            <p className="font-mono text-xs font-semibold text-terminal-text">
              {k.value}
            </p>
            {'sub' in k && k.sub && (
              <p
                className={`text-[10px] ${'up' in k && k.up ? 'text-up' : 'up' in k && !k.up ? 'text-down' : 'text-terminal-muted'}`}
              >
                {k.sub}
              </p>
            )}
          </div>
        ))}
      </div>

      {kafkaStreamTicks.length > 0 ? (
        <div
          className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-1.5 rounded-lg border border-emerald-500/35 bg-emerald-500/[0.07] px-3 py-2"
          role="status"
          aria-label="Kafka stream latest ticks"
        >
          <span className="text-[10px] font-bold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">
            Kafka stream
          </span>
          <span className="text-[10px] text-terminal-muted">
            Last write to{' '}
            <span className="font-mono text-terminal-text">market_stream</span>
            {kafkaStreamUpdatedAt
              ? ` · UI ${formatTime(kafkaStreamUpdatedAt)}`
              : ''}
          </span>
          <div className="flex w-full flex-wrap gap-x-3 gap-y-1 font-mono text-[11px] text-terminal-text sm:w-auto">
            {kafkaStreamTicks.map((t) => (
              <span key={t.symbol}>
                <span className="text-terminal-muted">{t.symbol}</span>{' '}
                {t.price > 100
                  ? t.price.toLocaleString(undefined, { maximumFractionDigits: 2 })
                  : t.price.toFixed(4)}
              </span>
            ))}
          </div>
        </div>
      ) : (
        source === 'live' && (
          <p className="mb-4 text-[10px] text-terminal-muted">
            Kafka UI: start{' '}
            <span className="font-mono">docker compose up -d</span>,{' '}
            <span className="font-mono">stream_producer</span> +{' '}
            <span className="font-mono">stream_consumer</span> — then prices here
            refresh from <span className="font-mono">/api/stream/latest</span>.
          </p>
        )
      )}

      {/* TradingView-style: main chart + right rail */}
      <div className="flex min-h-[min(720px,calc(100vh-11rem))] flex-col overflow-hidden rounded-lg border border-terminal-border bg-terminal-bg shadow-sm xl:flex-row">
        <section
          className="flex min-h-0 min-w-0 flex-1 flex-col"
          aria-label="Price chart and controls"
        >
          <div className="border-b border-terminal-border bg-terminal-bg px-3 py-3 md:px-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-lg font-bold tracking-tight text-terminal-text">
                    {asset.symbol}
                  </h1>
                  <span className="rounded bg-terminal-surface px-1.5 py-0.5 font-mono text-[11px] text-terminal-muted">
                    {timeframe}
                  </span>
                  {predBadge(asset.prediction)}
                  <span className="font-mono text-[10px] text-terminal-muted">
                    ML {(asset.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="mt-0.5 text-[12px] text-terminal-muted">
                  {asset.name}
                </p>
                <p className="mt-1 font-mono text-[11px] text-terminal-muted">
                  O {fmtPx(asset, ohlc.o)} · H {fmtPx(asset, ohlc.h)} · L{' '}
                  {fmtPx(asset, ohlc.l)} · C {fmtPx(asset, livePx ?? ohlc.c)}
                  {getKafkaPrice(asset.symbol) != null && (
                    <span className="ml-1 text-[10px] text-emerald-600 dark:text-emerald-400">
                      (stream)
                    </span>
                  )}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <div className="hidden items-center gap-1.5 sm:flex" aria-hidden>
                  <button
                    type="button"
                    tabIndex={-1}
                    className="rounded-md border border-down/40 bg-down/15 px-2.5 py-1.5 font-mono text-[11px] font-semibold text-down opacity-90"
                  >
                    SELL {fmtPx(asset, bid)}
                  </button>
                  <button
                    type="button"
                    tabIndex={-1}
                    className="rounded-md border border-accent/45 bg-accent/15 px-2.5 py-1.5 font-mono text-[11px] font-semibold text-accent opacity-90"
                  >
                    BUY {fmtPx(asset, ask)}
                  </button>
                </div>
                <div className="text-right">
                  <p className="font-mono text-xl font-semibold leading-tight text-terminal-text md:text-2xl">
                    {livePx != null && livePx > 100
                      ? livePx.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })
                      : (livePx ?? 0).toFixed(5)}
                  </p>
                  <p
                    className={
                      asset.changePct >= 0
                        ? 'font-mono text-sm text-up'
                        : 'font-mono text-sm text-down'
                    }
                  >
                    {asset.changePct >= 0 ? '+' : ''}
                    {asset.changePct.toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="relative min-h-[280px] flex-1 md:min-h-[380px]">
            <PriceChart />
            <div className="pointer-events-none absolute right-2 top-10 flex flex-col items-end gap-0.5">
              <span className="pointer-events-auto rounded-sm border border-accent/35 bg-terminal-surface/95 px-1.5 py-0.5 font-mono text-[10px] text-accent">
                MA 20
              </span>
              <span className="pointer-events-auto rounded-sm border border-metals/40 bg-terminal-surface/95 px-1.5 py-0.5 font-mono text-[10px] text-metals">
                MA 50
              </span>
            </div>
          </div>

          <div
            className="flex flex-wrap items-center justify-between gap-2 border-t border-terminal-border bg-terminal-surface px-2 py-2"
            role="toolbar"
            aria-label="Chart range (demo)"
          >
            <div className="flex flex-wrap gap-0.5">
              {(['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y'] as const).map(
                (r) => (
                  <button
                    key={r}
                    type="button"
                    title="Connect historical data to enable range shortcuts"
                    className="min-h-8 rounded-md px-2 py-1 font-mono text-[10px] text-terminal-muted transition-colors duration-150 hover:bg-terminal-elevated hover:text-terminal-text"
                  >
                    {r}
                  </button>
                ),
              )}
            </div>
            <span className="font-mono text-[10px] tabular-nums text-terminal-muted">
              <time dateTime={clock.toISOString()}>
                {clock.toISOString().slice(11, 19)} UTC
              </time>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2 border-t border-terminal-border bg-terminal-bg px-3 py-2">
            <Link
              to="/news"
              className="rounded-md px-1.5 py-1 text-[11px] text-accent underline-offset-2 transition-colors hover:underline"
            >
              News & Sentiment
            </Link>
            <span className="text-terminal-border" aria-hidden>
              |
            </span>
            <Link
              to="/prediction"
              className="rounded-md px-1.5 py-1 text-[11px] text-accent underline-offset-2 transition-colors hover:underline"
            >
              Prediction Lab
            </Link>
          </div>
        </section>

        <aside
          className="flex w-full flex-col border-t border-terminal-border bg-terminal-surface xl:w-[300px] xl:shrink-0 xl:border-l xl:border-t-0 xl:max-h-[calc(100vh-9rem)]"
          aria-label="Watchlist and headlines"
        >
          <div className="border-b border-terminal-border p-2">
            <p className="text-[10px] font-bold uppercase tracking-wider text-terminal-muted">
              Watchlist
            </p>
            <input
              type="search"
              placeholder="Search symbol…"
              value={watchlistQuery}
              onChange={(e) => setWatchlistQuery(e.target.value)}
              aria-label="Filter watchlist by symbol or name"
              autoComplete="off"
              className="mt-1.5 w-full rounded-md border border-terminal-border bg-terminal-bg px-2.5 py-2 font-mono text-[11px] text-terminal-text placeholder:text-terminal-muted transition-colors duration-150 focus:border-accent"
            />
            <div
              className="mt-2 flex flex-wrap gap-1"
              role="group"
              aria-label="Market filter"
            >
              {(['all', 'crypto', 'forex', 'metals'] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMarketFilter(m)}
                  aria-pressed={marketFilter === m}
                  className={`min-h-8 rounded-md px-2 py-1 text-[9px] font-semibold uppercase transition-colors duration-150 ${
                    marketFilter === m
                      ? 'bg-terminal-elevated text-terminal-text ring-1 ring-accent/50'
                      : 'text-terminal-muted hover:bg-terminal-elevated/50 hover:text-terminal-text'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto">
            <table className="w-full table-fixed text-left text-[11px]">
              <thead className="sticky top-0 z-10 border-b border-terminal-border bg-terminal-surface">
                <tr className="text-terminal-muted">
                  <th className="py-1.5 pl-2 font-normal">Symbol</th>
                  <th className="py-1.5 pr-1 text-right font-normal">Last</th>
                  <th className="w-14 py-1.5 pr-2 text-right font-normal">
                    Chg%
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td
                      colSpan={3}
                      className="px-3 py-8 text-center text-[11px] leading-relaxed text-terminal-muted"
                    >
                      No symbols match your search or filter.
                      <br />
                      <button
                        type="button"
                        onClick={() => {
                          setWatchlistQuery('')
                          setMarketFilter('all')
                        }}
                        className="mt-2 text-accent underline-offset-2 hover:underline"
                      >
                        Clear filters
                      </button>
                    </td>
                  </tr>
                ) : (
                  filtered.map((a) => (
                    <tr
                      key={a.symbol}
                      tabIndex={0}
                      aria-selected={selectedSymbol === a.symbol}
                      className={`cursor-pointer border-b border-terminal-border/40 font-mono outline-none transition-colors duration-150 hover:bg-terminal-elevated focus-visible:bg-terminal-elevated focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent/50 ${
                        selectedSymbol === a.symbol
                          ? 'bg-terminal-elevated/80'
                          : ''
                      }`}
                      onClick={() => setSelectedSymbol(a.symbol)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          setSelectedSymbol(a.symbol)
                        }
                      }}
                    >
                      <td className="py-2 pl-2">
                        <span className="text-terminal-text">{a.symbol}</span>
                      </td>
                      <td className="truncate py-2 pr-1 text-right tabular-nums text-terminal-text">
                        {(() => {
                          const px = getKafkaPrice(a.symbol) ?? a.price
                          return px > 100
                            ? px.toLocaleString(undefined, {
                                maximumFractionDigits: 2,
                              })
                            : px.toFixed(4)
                        })()}
                      </td>
                      <td
                        className={`py-2 pr-2 text-right tabular-nums ${
                          a.changePct >= 0 ? 'text-up' : 'text-down'
                        }`}
                      >
                        {a.changePct >= 0 ? '+' : ''}
                        {a.changePct.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="border-t border-terminal-border p-2">
            <div className="mb-2 flex items-center justify-between gap-2">
              <div>
                <p className="font-mono text-sm font-semibold text-terminal-text">
                  {asset.symbol}
                </p>
                <p className="text-[10px] text-terminal-muted">{asset.name}</p>
              </div>
              <MarketTag market={asset.market} />
            </div>
            <p
              className={`font-mono text-xl font-semibold ${
                asset.changePct >= 0 ? 'text-up' : 'text-down'
              }`}
            >
              {livePx != null && livePx > 100
                ? livePx.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })
                : (livePx ?? 0).toFixed(4)}{' '}
              <span className="text-sm">
                ({asset.changePct >= 0 ? '+' : ''}
                {asset.changePct.toFixed(2)}%)
              </span>
            </p>

            <p className="mb-1.5 mt-3 text-[10px] font-bold uppercase text-terminal-muted">
              Performance
            </p>
            <div className="grid grid-cols-3 gap-1">
              {perf.map((cell) => (
                <div
                  key={cell.k}
                  className="rounded border border-terminal-border bg-terminal-bg px-1.5 py-1.5 text-center"
                >
                  <p
                    className={`font-mono text-xs font-semibold ${
                      cell.pct >= 0 ? 'text-up' : 'text-down'
                    }`}
                  >
                    {cell.pct >= 0 ? '+' : ''}
                    {cell.pct.toFixed(2)}%
                  </p>
                  <p className="text-[9px] text-terminal-muted">{cell.k}</p>
                </div>
              ))}
            </div>

            {topStory && (
              <a
                href={topStory.url}
                onClick={(e) => e.preventDefault()}
                className="mt-2 flex items-center gap-2 rounded-lg border px-2 py-2.5 transition-colors duration-150"
                style={{
                  background: 'var(--app-news-bg)',
                  borderColor: 'var(--app-news-border)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'var(--app-news-hover)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'var(--app-news-bg)'
                }}
              >
                <span
                  className="text-lg"
                  style={{ color: 'var(--app-news-icon)' }}
                  aria-hidden
                >
                  ⚡
                </span>
                <p className="line-clamp-2 flex-1 text-[11px] leading-snug text-terminal-text">
                  {topStory.headline}
                </p>
              </a>
            )}

            <p className="mb-1 mt-3 text-[10px] font-bold uppercase text-terminal-muted">
              Headlines
            </p>
            <ul className="max-h-48 space-y-1.5 overflow-y-auto pr-0.5">
              {news.slice(0, 8).map((item) => (
                <li key={item.id}>
                  <a
                    href={item.url}
                    onClick={(e) => e.preventDefault()}
                    className="block rounded-md border border-transparent px-1.5 py-1.5 transition-colors duration-150 hover:border-terminal-border hover:bg-terminal-elevated/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
                  >
                    <div className="flex items-start gap-1.5">
                      {sentimentDot(item.sentiment)}
                      <span className="line-clamp-2 text-[11px] leading-tight text-terminal-text">
                        {item.headline}
                      </span>
                    </div>
                    <div className="mt-0.5 flex items-center justify-between pl-3">
                      <span className="text-[9px] text-terminal-muted">
                        {item.source}
                      </span>
                      <SentimentSparkline values={item.spark} />
                    </div>
                  </a>
                </li>
              ))}
            </ul>

            <Link
              to="/asset"
              className="mt-3 block w-full rounded-md border border-terminal-border py-2.5 text-center text-[11px] font-medium text-accent transition-colors duration-150 hover:bg-terminal-elevated"
            >
              More details →
            </Link>
          </div>
        </aside>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-3">
        <div className="rounded-lg border border-terminal-border bg-terminal-surface p-4 shadow-sm">
          <h2 className="mb-2 text-[10px] font-bold uppercase tracking-wider text-terminal-muted">
            Technical indicators
          </h2>
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center">
              <p className="mb-1 text-[9px] uppercase text-terminal-muted">
                RSI
              </p>
              <RsiGauge value={asset.rsi} />
            </div>
            <div className="col-span-2">
              <p className="mb-1 text-center text-[9px] uppercase text-terminal-muted">
                MACD vs signal
              </p>
              <MacdSparkline macd={asset.macd} signal={asset.macdSignal} />
              <p className="mt-1 text-center font-mono text-[10px] text-terminal-muted">
                Vol {asset.volatility.toFixed(2)}% · MA20{' '}
                {asset.ma20.toFixed(2)} · MA50 {asset.ma50.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-terminal-border bg-terminal-surface p-4 shadow-sm">
          <h2 className="mb-2 text-[10px] font-bold uppercase tracking-wider text-terminal-muted">
            Prediction summary
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            {predBadge(asset.prediction)}
            <div>
              <p className="text-[10px] text-terminal-muted">Next move</p>
              <p className="font-mono text-xs text-terminal-text">
                P(up) {(asset.probUp * 100).toFixed(0)}% · P(down){' '}
                {(asset.probDown * 100).toFixed(0)}%
              </p>
            </div>
          </div>
          <p className="mt-1.5 font-mono text-[10px] text-terminal-muted">
            {asset.modelVersion}
          </p>
          <p className="mb-1 mt-2 text-[9px] uppercase text-terminal-muted">
            Top features
          </p>
          <div className="space-y-1">
            {asset.topFeatures.map((f) => (
              <div key={f.name} className="flex items-center gap-2">
                <div className="h-1 flex-1 overflow-hidden bg-terminal-bg">
                  <div
                    className="h-full bg-accent"
                    style={{ width: `${f.weight * 400}%` }}
                  />
                </div>
                <span className="w-24 shrink-0 truncate text-right font-mono text-[9px] text-terminal-muted">
                  {f.name}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-terminal-border bg-terminal-surface p-4 shadow-sm">
          <h2 className="mb-2 text-[10px] font-bold uppercase tracking-wider text-terminal-muted">
            Market micro summary
          </h2>
          <dl className="grid grid-cols-2 gap-1.5 text-[11px]">
            <div className="rounded-md border border-terminal-border bg-terminal-bg px-2 py-1.5">
              <dt className="text-terminal-muted">Latest return</dt>
              <dd
                className={`font-mono font-semibold ${asset.lastReturn >= 0 ? 'text-up' : 'text-down'}`}
              >
                {(asset.lastReturn * 100).toFixed(2)}%
              </dd>
            </div>
            <div className="rounded-md border border-terminal-border bg-terminal-bg px-2 py-1.5">
              <dt className="text-terminal-muted">Volume</dt>
              <dd className="font-mono text-terminal-text">{asset.volume}</dd>
            </div>
            <div className="rounded-md border border-terminal-border bg-terminal-bg px-2 py-1.5">
              <dt className="text-terminal-muted">Sentiment</dt>
              <dd className="font-mono text-terminal-text">
                {asset.sentimentScore >= 0 ? '+' : ''}
                {asset.sentimentScore.toFixed(2)}
              </dd>
            </div>
            <div className="rounded-md border border-terminal-border bg-terminal-bg px-2 py-1.5">
              <dt className="text-terminal-muted">Articles</dt>
              <dd className="font-mono text-terminal-text">
                {asset.newsCount24h}
              </dd>
            </div>
          </dl>
          <p className="mt-2 text-[9px] uppercase text-terminal-muted">
            Anomalies
          </p>
          <ul className="mt-0.5 space-y-0.5 text-[11px] text-terminal-text">
            {asset.anomalies.length ? (
              asset.anomalies.map((x) => (
                <li key={x} className="flex gap-1 text-terminal-muted">
                  <span className="text-metals">▸</span>
                  {x}
                </li>
              ))
            ) : (
              <li className="text-terminal-muted">None</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  )
}
