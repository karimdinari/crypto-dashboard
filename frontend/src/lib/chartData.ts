import type { Timeframe } from '../types'

function hashSeed(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = (Math.imul(31, h) + s.charCodeAt(i)) | 0
  }
  return Math.abs(h) + 1
}

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const barsForTf: Record<Timeframe, number> = {
  '1H': 48,
  '4H': 42,
  '1D': 60,
  '1W': 52,
}

const secondsPerBar: Record<Timeframe, number> = {
  '1H': 3600,
  '4H': 14400,
  '1D': 86400,
  '1W': 604800,
}

export interface Candle {
  time: number
  open: number
  high: number
  low: number
  close: number
}

export interface VolumeBar {
  time: number
  value: number
  color: string
}

/** JSON shape from `GET /api/chart` (Silver OHLCV, resampled). */
export type ChartApiCandle = Candle

export interface ChartApiLinePoint {
  time: number
  value: number
}

export interface ChartApiVolume {
  time: number
  value: number
}

export interface ChartApiPayload {
  candles: ChartApiCandle[]
  volumes: ChartApiVolume[]
  ma20: ChartApiLinePoint[]
  ma50: ChartApiLinePoint[]
  /** ISO-8601 UTC — newest bar in Silver (batch); chart cannot extend past this until ingestion runs again. */
  last_bar_time_utc?: string
  source?: string
}

export function buildSeries(
  symbol: string,
  basePrice: number,
  timeframe: Timeframe,
): { candles: Candle[]; volumes: VolumeBar[]; ma20: { time: number; value: number }[]; ma50: { time: number; value: number }[] } {
  const rand = mulberry32(hashSeed(symbol))
  const n = barsForTf[timeframe]
  const step = secondsPerBar[timeframe]
  const now = Math.floor(Date.now() / 1000)
  const start = now - n * step

  const candles: Candle[] = []
  let price = basePrice * (0.92 + rand() * 0.16)

  for (let i = 0; i < n; i++) {
    const t = start + i * step
    const vol = rand() * 0.02 + 0.005
    const drift = (rand() - 0.48) * vol * price
    const open = price
    const close = Math.max(price * 0.97, price + drift)
    const high = Math.max(open, close) * (1 + rand() * vol * 0.5)
    const low = Math.min(open, close) * (1 - rand() * vol * 0.5)
    candles.push({
      time: t,
      open,
      high,
      low,
      close,
    })
    price = close
  }

  const volumes: VolumeBar[] = candles.map((c) => ({
    time: c.time,
    value: rand() * 1e6 + 2e5,
    color:
      c.close >= c.open
        ? 'rgba(38, 166, 154, 0.45)'
        : 'rgba(239, 83, 80, 0.45)',
  }))

  const ma = (period: number) => {
    const out: { time: number; value: number }[] = []
    for (let i = period - 1; i < candles.length; i++) {
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += candles[i - j].close
      }
      out.push({ time: candles[i].time, value: sum / period })
    }
    return out
  }

  return {
    candles,
    volumes,
    ma20: ma(20),
    ma50: ma(50),
  }
}
