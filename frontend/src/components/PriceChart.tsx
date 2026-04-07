import { useEffect, useRef, useState } from 'react'
import {
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
      volUp: 'rgba(8, 153, 129, 0.4)',
      volDown: 'rgba(242, 54, 69, 0.4)',
    }
  }
  return {
    bg: '#0f0f0f',
    text: '#b2b5be',
    grid: '#363c4e',
    border: '#363a45',
    crosshair: 'rgba(117, 134, 150, 0.45)',
    up: '#26a69a',
    down: '#ef5350',
    ma20: '#2962ff',
    ma50: '#fbc02d',
    line: '#2962ff',
    volUp: 'rgba(38, 166, 154, 0.45)',
    volDown: 'rgba(239, 83, 80, 0.45)',
  }
}

const CHART_POLL_MS = 45_000

function formatChartFootnote(iso: string | undefined): string {
  if (!iso) return ''
  const neat = iso.replace('T', ' ').replace('+00:00', '').slice(0, 16)
  return `Last candle ends ${neat} UTC · Silver batch OHLCV. This chart reloads from the API every ~${CHART_POLL_MS / 1000}s. After you run ingestion + Silver, wait until a new 1h bar closes (usually the next hour) or you may still see the same last time. Kafka strip = tick prices only.`
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

export function PriceChart() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { selectedSymbol, timeframe, chartStyle } = useTerminal()
  const { theme } = useTheme()
  const { getAsset } = useData()
  const asset = getAsset(selectedSymbol)
  const [chartFootnote, setChartFootnote] = useState<string | null>(null)
  const chartRefreshGen = useChartAutoRefresh()

  useEffect(() => {
    const el = containerRef.current
    if (!el || !asset) return

    setChartFootnote(null)
    const pal = chartPalette(theme)
    let alive = true

    const chart: IChartApi = createChart(el, {
      layout: {
        background: { type: ColorType.Solid, color: pal.bg },
        textColor: pal.text,
        fontSize: 11,
        fontFamily: "'Roboto Mono', monospace",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: pal.grid },
        horzLines: { color: pal.grid },
      },
      crosshair: {
        vertLine: {
          color: pal.crosshair,
          labelBackgroundColor: pal.border,
        },
        horzLine: {
          color: pal.crosshair,
          labelBackgroundColor: pal.border,
        },
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
          if (asset.price > 10) return p.toFixed(3)
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
        const q = new URLSearchParams({
          symbol: selectedSymbol,
          timeframe,
          _t: String(Date.now()),
        })
        const r = await fetch(`/api/chart?${q.toString()}`, { cache: 'no-store' })
        if (r.ok) {
          const data = (await r.json()) as ChartApiPayload
          if (data.candles?.length) {
            candles = data.candles
            volumes = data.volumes
            ma20 = data.ma20
            ma50 = data.ma50
            lastBarIso = data.last_bar_time_utc
          }
        }
      } catch {
        /* mock fallback */
      }

      if (!alive) return

      if (!candles?.length) {
        const b = buildSeries(asset.symbol, asset.price, timeframe)
        candles = b.candles
        volumes = b.volumes.map((v) => ({ time: v.time, value: v.value }))
        ma20 = b.ma20
        ma50 = b.ma50
        setChartFootnote(
          'Synthetic demo candles (chart API unavailable or empty).',
        )
      } else if (lastBarIso) {
        setChartFootnote(formatChartFootnote(lastBarIso))
      } else {
        setChartFootnote(null)
      }

      if (!alive) return

      if (chartStyle === 'candle') {
        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: pal.up,
          downColor: pal.down,
          borderUpColor: pal.up,
          borderDownColor: pal.down,
          wickUpColor: pal.up,
          wickDownColor: pal.down,
        })
        candleSeries.setData(
          candles.map((c) => ({
            time: c.time as Time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          })),
        )

        const ma20Series = chart.addSeries(LineSeries, {
          color: pal.ma20,
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
        })
        ma20Series.setData(
          (ma20 ?? []).map((p) => ({
            time: p.time as Time,
            value: p.value,
          })),
        )

        const ma50Series = chart.addSeries(LineSeries, {
          color: pal.ma50,
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
        })
        ma50Series.setData(
          (ma50 ?? []).map((p) => ({
            time: p.time as Time,
            value: p.value,
          })),
        )
      } else {
        const lineSeries = chart.addSeries(LineSeries, {
          color: pal.line,
          lineWidth: 2,
          priceLineVisible: true,
        })
        lineSeries.setData(
          candles.map((c) => ({
            time: c.time as Time,
            value: c.close,
          })),
        )
      }

      const volSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: '',
      })
      volSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.85, bottom: 0 },
      })
      volSeries.setData(
        (volumes ?? []).map((v, i) => ({
          time: v.time as Time,
          value: v.value,
          color:
            candles[i] && candles[i].close >= candles[i].open
              ? pal.volUp
              : pal.volDown,
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
      <div
        ref={containerRef}
        className="min-h-[280px] w-full flex-1 md:min-h-[380px]"
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
