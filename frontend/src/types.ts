export type MarketType = 'crypto' | 'forex' | 'metals'

export type PredictionSignal = 'BUY' | 'SELL' | 'HOLD'

export type SentimentLabel = 'positive' | 'neutral' | 'negative'

export interface Asset {
  symbol: string
  name: string
  market: MarketType
  price: number
  changePct: number
  volume: string
  rsi: number
  macd: number
  macdSignal: number
  volatility: number
  ma20: number
  ma50: number
  prediction: PredictionSignal
  confidence: number
  sentimentScore: number
  newsCount24h: number
  lastReturn: number
  anomalies: string[]
  topFeatures: { name: string; weight: number }[]
  modelVersion: string
  probUp: number
  probDown: number
}

export interface NewsItem {
  id: string
  headline: string
  source: string
  publishedAt: string
  sentiment: SentimentLabel
  url: string
  symbols: string[]
  spark: number[]
}

export type Timeframe = '1H' | '4H' | '1D' | '1W'

/** Latest tick per symbol from `GET /api/stream/latest` (Kafka consumer → Bronze Parquet). */
export interface KafkaStreamTick {
  symbol: string
  market_type: string
  price: number
  source: string
  timestamp: string
  ingestion_time: string
}
