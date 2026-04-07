import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { ASSETS as MOCK_ASSETS, PIPELINE_LAST_REFRESH as MOCK_REFRESH } from '../data/mock'
import type { Asset, KafkaStreamTick } from '../types'
import { fetchJson } from '../lib/api'

export type DataSource = 'live' | 'mock'

export type PipelineFileInfo = {
  id: string
  path: string
  exists: boolean
  rows: number | null
  mtime: string | null
}

export type PipelineStatus = {
  last_refresh: string
  generated_at: string
  files: PipelineFileInfo[]
}

type DataState = {
  assets: Asset[]
  source: DataSource
  pipeline: PipelineStatus | null
  loadError: string | null
  refresh: () => Promise<void>
  getAsset: (symbol: string) => Asset | undefined
  /** Kafka → `market_stream.parquet` → API; polled ~20s */
  kafkaStreamTicks: KafkaStreamTick[]
  kafkaStreamUpdatedAt: string | null
  getKafkaPrice: (symbol: string) => number | undefined
}

const DataContext = createContext<DataState | null>(null)

function normalizeStreamTick(row: Record<string, unknown>): KafkaStreamTick {
  return {
    symbol: String(row.symbol),
    market_type: String(row.market_type),
    price: Number(row.price),
    source: String(row.source),
    timestamp: String(row.timestamp),
    ingestion_time: String(row.ingestion_time),
  }
}

function normalizeAsset(row: Record<string, unknown>): Asset {
  return {
    symbol: String(row.symbol),
    name: String(row.name),
    market: row.market as Asset['market'],
    price: Number(row.price),
    changePct: Number(row.changePct),
    volume: String(row.volume),
    rsi: Number(row.rsi),
    macd: Number(row.macd),
    macdSignal: Number(row.macdSignal),
    volatility: Number(row.volatility),
    ma20: Number(row.ma20),
    ma50: Number(row.ma50),
    prediction: row.prediction as Asset['prediction'],
    confidence: Number(row.confidence),
    sentimentScore: Number(row.sentimentScore),
    newsCount24h: Number(row.newsCount24h),
    lastReturn: Number(row.lastReturn),
    anomalies: Array.isArray(row.anomalies) ? (row.anomalies as string[]) : [],
    topFeatures: Array.isArray(row.topFeatures)
      ? (row.topFeatures as { name: string; weight: number }[])
      : [],
    modelVersion: String(row.modelVersion),
    probUp: Number(row.probUp),
    probDown: Number(row.probDown),
  }
}

/** How often to refetch Kafka-backed ticks (`/api/stream/latest`). */
const STREAM_POLL_MS = 5_000

export function DataProvider({ children }: { children: ReactNode }) {
  const [assets, setAssets] = useState<Asset[]>(MOCK_ASSETS)
  const [source, setSource] = useState<DataSource>('mock')
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [kafkaStreamTicks, setKafkaStreamTicks] = useState<KafkaStreamTick[]>([])
  const [kafkaStreamUpdatedAt, setKafkaStreamUpdatedAt] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoadError(null)
    try {
      const rawAssets = await fetchJson<Record<string, unknown>[]>('/api/assets')
      let pipe: PipelineStatus | null = null
      try {
        pipe = await fetchJson<PipelineStatus>('/api/pipeline')
      } catch {
        pipe = null
      }
      if (Array.isArray(rawAssets) && rawAssets.length > 0) {
        setAssets(rawAssets.map(normalizeAsset))
        setSource('live')
      } else {
        setAssets(MOCK_ASSETS)
        setSource('mock')
        setLoadError('No rows in /api/assets — run ingestion + Silver + Gold.')
      }
      if (pipe) setPipeline(pipe)
    } catch (e) {
      setAssets(MOCK_ASSETS)
      setSource('mock')
      setLoadError(e instanceof Error ? e.message : 'API unreachable')
      try {
        const pipe = await fetchJson<PipelineStatus>('/api/pipeline')
        setPipeline(pipe)
      } catch {
        setPipeline({
          last_refresh: MOCK_REFRESH,
          generated_at: new Date().toISOString(),
          files: [],
        })
      }
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    let cancelled = false
    const pull = async () => {
      try {
        const r = await fetch('/api/stream/latest')
        if (!r.ok) return
        const raw = (await r.json()) as unknown
        if (cancelled || !Array.isArray(raw)) return
        const ticks = raw
          .filter((x): x is Record<string, unknown> => x !== null && typeof x === 'object')
          .map(normalizeStreamTick)
          .filter((t) => t.symbol && Number.isFinite(t.price))
        setKafkaStreamTicks(ticks)
        setKafkaStreamUpdatedAt(new Date().toISOString())
      } catch {
        if (!cancelled) {
          setKafkaStreamTicks([])
        }
      }
    }
    void pull()
    const id = window.setInterval(pull, STREAM_POLL_MS)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  const getAsset = useCallback(
    (symbol: string) => assets.find((a) => a.symbol === symbol),
    [assets],
  )

  const getKafkaPrice = useCallback(
    (symbol: string) => kafkaStreamTicks.find((t) => t.symbol === symbol)?.price,
    [kafkaStreamTicks],
  )

  const value = useMemo(
    () => ({
      assets,
      source,
      pipeline,
      loadError,
      refresh,
      getAsset,
      kafkaStreamTicks,
      kafkaStreamUpdatedAt,
      getKafkaPrice,
    }),
    [
      assets,
      source,
      pipeline,
      loadError,
      refresh,
      getAsset,
      kafkaStreamTicks,
      kafkaStreamUpdatedAt,
      getKafkaPrice,
    ],
  )

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export function useData() {
  const ctx = useContext(DataContext)
  if (!ctx) {
    throw new Error('useData must be used within DataProvider')
  }
  return ctx
}
