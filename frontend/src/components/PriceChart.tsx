import { useEffect, useRef, useState } from 'react'
import {
  AreaSeries,
  BaselineSeries,
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  LineSeries,
  type IChartApi,
  type Time,
} from 'lightweight-charts'
import { useData } from '../context/DataContext'
import { useTerminal } from '../context/TerminalContext'
import { useTheme } from '../context/ThemeContext'
import { buildSeries, type ChartApiPayload } from '../lib/chartData'

function chartPalette(theme: 'dark' | 'light') {
  if (theme === 'light') {
    return {
      bg: '#ffffff',
      text: '#131722',
      grid: '#e0e3eb',
      border: '#d1d4dc',
      crosshair: 'rgba(19, 23, 34, 0.12)',
      up: '#089981',
      down: '#f23645',
      ma20: '#2962ff',
      ma50: '#f57c00',
      line: '#2962ff',
      area: '#2962ff',
      volUp: 'rgba(8, 153, 129, 0.4)',
      volDown: 'rgba(242, 54, 69, 0.4)',
    }
  }
  return {
    bg: '#06070b',
    text: '#b2b5be',
    grid: '#363c4e',
    border: '#363a45',
    crosshair: 'rgba(117, 134, 150, 0.45)',
    up: '#26a69a',
    down: '#ef5350',
    ma20: '#2962ff',
    ma50: '#fbc02d',
    line: '#5ce1ff',
    area: '#5ce1ff',
    volUp: 'rgba(38, 166, 154, 0.45)',
    volDown: 'rgba(239, 83, 80, 0.45)',
  }
}

const CHART_POLL_MS = 45_000

const CHART_STYLES = [
  { key: 'candle',   label: 'Candles' },
  { key: 'line',     label: 'Line' },
  { key: 'area',     label: 'Area' },
  { key: 'baseline', label: 'Baseline' },
] as const

function formatChartFootnote(iso: string | undefined): string {
  if (!iso) return ''
  const neat = iso.replace('T', ' ').replace('+00:00', '').slice(0, 16)
  return `Last candle ends ${neat} UTC · Silver batch OHLCV. Reloads every ~${CHART_POLL_MS / 1000}s. After running ingestion + Silver, wait until a new bar closes.`
}

function useChartAutoRefresh(): number {
  const [gen, setGen] = useState(0)
  useEffect(() => {
    const tick = () => setGen((g) => g + 1)
    const id = window.setInterval(tick, CHART_POLL_MS)
    const onFocus = () => tick()
    window.addEventListener('focus', onFocus)
    return () => {
      window.clearInterval(id)
      window.removeEventListener('focus', onFocus)
    }
  }, [])
  return gen
}

function ChartLoadingSkeleton() {
  return (
    <div className="flex min-h-[280px] w-full flex-1 flex-col items-center justify-center gap-3 bg-[#06070b] md:min-h-[380px]">
      <svg
        width="36" height="36" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1.25"
        className="animate-pulse text-terminal-muted"
      >
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
      <p className="font-mono text-[11px] text-terminal-muted animate-pulse">Loading chart…</p>
    </div>
  )
}

export function PriceChart() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { selectedSymbol, timeframe, chartStyle, setChartStyle } = useTerminal()
  const { theme } = useTheme()
  const { getAsset } = useData()
  const asset = getAsset(selectedSymbol)
  const [chartFootnote, setChartFootnote] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const chartRefreshGen = useChartAutoRefresh()

  useEffect(() => {
    const el = containerRef.current
    if (!el || !asset) return

    setChartFootnote(null)
    setLoading(true)
    const pal = chartPalette(theme)
    let alive = true

    const chart: IChartApi = createChart(el, {
      layout: {
        background: { type: ColorType.Solid, color: pal.bg },
        textColor: pal.text,
        fontSize: 11,
        fontFamily: "'IBM Plex Mono', monospace",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: pal.grid },
        horzLines: { color: pal.grid },
      },
      crosshair: {
        vertLine: { color: pal.crosshair, labelBackgroundColor: pal.border },
        horzLine: { color: pal.crosshair, labelBackgroundColor: pal.border },
      },
      rightPriceScale: {
        borderColor: pal.border,
        scaleMargins: { top: 0.08, bottom: 0.22 },
      },
      timeScale: {
        borderColor: pal.border,
        timeVisible: true,
        secondsVisible: false,
      },
      localization: {
        priceFormatter: (p: number) => {
          if (asset.price > 500) return p.toFixed(2)
          if (asset.price > 10)  return p.toFixed(3)
          return p.toFixed(5)
        },
      },
    })

    const ro = new ResizeObserver(() => {
      if (!containerRef.current) return
      const { width, height } = containerRef.current.getBoundingClientRect()
      chart.applyOptions({ width, height })
    })
    ro.observe(el)

    ;(async () => {
      let candles: ChartApiPayload['candles'] | null = null
      let volumes: ChartApiPayload['volumes'] | null = null
      let ma20: ChartApiPayload['ma20'] | null = null
      let ma50: ChartApiPayload['ma50'] | null = null
      let lastBarIso: string | undefined

      try {
        const q = new URLSearchParams({ symbol: selectedSymbol, timeframe, _t: String(Date.now()) })
        const r = await fetch(`/api/chart?${q.toString()}`, { cache: 'no-store' })
        if (r.ok) {
          const data = (await r.json()) as ChartApiPayload
          if (data.candles?.length) {
            candles  = data.candles
            volumes  = data.volumes
            ma20     = data.ma20
            ma50     = data.ma50
            lastBarIso = data.last_bar_time_utc
          }
        }
      } catch { /* mock fallback */ }

      if (!alive) return
      setLoading(false)

      if (!candles?.length) {
        const b = buildSeries(asset.symbol, asset.price, timeframe)
        candles  = b.candles
        volumes  = b.volumes.map((v) => ({ time: v.time, value: v.value }))
        ma20     = b.ma20
        ma50     = b.ma50
        setChartFootnote('Synthetic demo candles (chart API unavailable or empty).')
      } else if (lastBarIso) {
        setChartFootnote(formatChartFootnote(lastBarIso))
      } else {
        setChartFootnote(null)
      }

      if (!alive || !candles?.length) return

      // ─── Render chosen chart style ───
      if (chartStyle === 'candle') {
        const cs = chart.addSeries(CandlestickSeries, {
          upColor: pal.up, downColor: pal.down,
          borderUpColor: pal.up, borderDownColor: pal.down,
          wickUpColor: pal.up, wickDownColor: pal.down,
        })
        cs.setData(candles.map((c) => ({ time: c.time as Time, open: c.open, high: c.high, low: c.low, close: c.close })))

        const m20 = chart.addSeries(LineSeries, { color: pal.ma20, lineWidth: 1, priceLineVisible: false, lastValueVisible: false })
        m20.setData((ma20 ?? []).map((p) => ({ time: p.time as Time, value: p.value })))

        const m50 = chart.addSeries(LineSeries, { color: pal.ma50, lineWidth: 1, priceLineVisible: false, lastValueVisible: false })
        m50.setData((ma50 ?? []).map((p) => ({ time: p.time as Time, value: p.value })))

      } else if (chartStyle === 'area') {
        const as = chart.addSeries(AreaSeries, {
          lineColor: pal.area,
          topColor: `${pal.area}55`,
          bottomColor: `${pal.area}00`,
          lineWidth: 2,
          priceLineVisible: true,
        })
        as.setData(candles.map((c) => ({ time: c.time as Time, value: c.close })))

      } else if (chartStyle === 'baseline') {
        const baseValue = candles[0]?.close ?? asset.price
        const bs = chart.addSeries(BaselineSeries, {
          baseValue: { type: 'price', price: baseValue },
          topLineColor: pal.up,
          topFillColor1: `${pal.up}40`,
          topFillColor2: `${pal.up}00`,
          bottomLineColor: pal.down,
          bottomFillColor1: `${pal.down}00`,
          bottomFillColor2: `${pal.down}30`,
          lineWidth: 2,
        })
        bs.setData(candles.map((c) => ({ time: c.time as Time, value: c.close })))

      } else {
        // line
        const ls = chart.addSeries(LineSeries, { color: pal.line, lineWidth: 2, priceLineVisible: true })
        ls.setData(candles.map((c) => ({ time: c.time as Time, value: c.close })))
      }

      // Volume histogram (always shown)
      const vs = chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: '' })
      vs.priceScale().applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } })
      vs.setData(
        (volumes ?? []).map((v, i) => ({
          time: v.time as Time,
          value: v.value,
          color: candles![i] && candles![i].close >= candles![i].open ? pal.volUp : pal.volDown,
        })),
      )

      chart.timeScale().fitContent()
    })()

    return () => {
      alive = false
      ro.disconnect()
      chart.remove()
    }
  }, [asset, selectedSymbol, timeframe, chartStyle, theme, chartRefreshGen])

  if (!asset) return null
  const bg = chartPalette(theme).bg

  return (
    <div className="flex min-h-0 w-full flex-1 flex-col">
      {/* Chart style selector */}
      <div className="flex items-center gap-1 border-b border-terminal-border/60 bg-terminal-surface/80 px-3 py-1.5">
        {CHART_STYLES.map((s) => (
          <button
            key={s.key}
            type="button"
            onClick={() => setChartStyle(s.key)}
            className={`rounded px-2.5 py-1 text-[11px] font-semibold transition ${
              chartStyle === s.key
                ? 'bg-accent/20 text-accent'
                : 'text-terminal-muted hover:bg-terminal-elevated hover:text-terminal-text'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Chart container */}
      {loading && <ChartLoadingSkeleton />}
      <div
        ref={containerRef}
        className={`min-h-[280px] w-full flex-1 md:min-h-[380px] ${loading ? 'hidden' : ''}`}
        style={{ background: bg }}
      />

      {chartFootnote ? (
        <p
          className="shrink-0 border-t border-terminal-border/60 bg-terminal-surface/90 px-3 py-2 text-[10px] leading-snug text-terminal-muted"
          role="note"
        >
          {chartFootnote}
        </p>
      ) : null}
    </div>
  )
}
