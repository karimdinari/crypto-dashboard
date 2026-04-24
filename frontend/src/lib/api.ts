import { useQuery } from "@tanstack/react-query";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export interface AssetOut {
  symbol: string;
  name: string;
  market: "crypto" | "forex" | "metals";
  price: number;
  changePct: number;
  volume: string;
  rsi: number;
  macd: number;
  macdSignal: number;
  volatility: number;
  ma7: number;
  ma30: number;
  ma20: number;
  ma50: number;
  prediction: "BUY" | "SELL" | "HOLD";
  confidence: number;
  sentimentScore: number;
  newsCount24h: number;
  lastReturn: number;
  anomalies: string[];
  modelVersion: string;
  probUp: number;
  probDown: number;
  spark?: number[]; // Frontend-only decoration
}

export interface StreamTickOut {
  symbol: string;
  market_type: string;
  price: number;
  source: string;
  timestamp: string;
  ingestion_time: string;
}

export interface NewsItemOut {
  id: string;
  headline: string;
  source: string;
  publishedAt: string;
  sentiment: "positive" | "negative" | "neutral";
  url: string;
  symbols: string[];
  spark: number[];
}

export interface SignalRowOut {
  asset: string;
  sig: "BUY" | "SELL" | "HOLD";
  conf: number;
  at: string;
}

export interface PipelineStatus {
  last_updated: string;
  bronze_files: number;
  silver_files: number;
  gold_files: number;
  status: "Healthy" | "Degraded" | "Offline";
}

export interface OHLCVOut {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
}

// Fetchers
const fetchAssets = async (): Promise<AssetOut[]> => {
  const res = await fetch(`${API_BASE_URL}/assets`);
  if (!res.ok) throw new Error("Failed to fetch assets");
  return res.json();
};

const fetchLatestStream = async (): Promise<StreamTickOut[]> => {
  const res = await fetch(`${API_BASE_URL}/stream/latest`);
  if (!res.ok) throw new Error("Failed to fetch stream");
  return res.json();
};

const fetchNews = async (limit = 100): Promise<NewsItemOut[]> => {
  const res = await fetch(`${API_BASE_URL}/news?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch news");
  return res.json();
};

const fetchNewsForAsset = async (symbol: string, limit = 50): Promise<NewsItemOut[]> => {
  const res = await fetch(`${API_BASE_URL}/news?symbol=${encodeURIComponent(symbol)}&limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch news for asset");
  return res.json();
}

const fetchNewsHistory = async (symbol: string): Promise<NewsItemOut[]> => {
  const cleanSymbol = symbol.replace(/\//g, "").replace(/_/g, "").replace(/-/g, "");
  const res = await fetch(`${API_BASE_URL}/news/history/${encodeURIComponent(cleanSymbol)}`);
  if (!res.ok) throw new Error("Failed to fetch news history for asset");
  return res.json();
}

const fetchSignals = async (): Promise<SignalRowOut[]> => {
  const res = await fetch(`${API_BASE_URL}/signals/recent`);
  if (!res.ok) throw new Error("Failed to fetch signals");
  return res.json();
};

const fetchPipeline = async (): Promise<PipelineStatus> => {
  const res = await fetch(`${API_BASE_URL}/pipeline`);
  if (!res.ok) throw new Error("Failed to fetch pipeline");
  return res.json();
};

const fetchHistory = async (symbol: string): Promise<OHLCVOut[]> => {
  const cleanSymbol = symbol.replace(/\//g, "").replace(/_/g, "").replace(/-/g, "");
  const res = await fetch(`${API_BASE_URL}/history/${encodeURIComponent(cleanSymbol)}`);
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
};

// React Query Hooks
export const useAssets = () => useQuery({ queryKey: ["assets"], queryFn: fetchAssets });
export const useLatestStream = () => useQuery({ queryKey: ["stream"], queryFn: fetchLatestStream, refetchInterval: 5000 });
export const useNews = (limit?: number) => useQuery({ queryKey: ["news", limit], queryFn: () => fetchNews(limit) });
export const useNewsForAsset = (symbol: string, limit?: number) => useQuery({ queryKey: ["news", symbol, limit], queryFn: () => fetchNewsForAsset(symbol, limit) });
export const useNewsHistory = (symbol: string) => useQuery({ queryKey: ["newsHistory", symbol], queryFn: () => fetchNewsHistory(symbol) });
export const useSignals = () => useQuery({ queryKey: ["signals"], queryFn: fetchSignals });
export const usePipeline = () => useQuery({ queryKey: ["pipeline"], queryFn: fetchPipeline });
export const useHistory = (symbol: string) => useQuery({ queryKey: ["history", symbol], queryFn: () => fetchHistory(symbol) });
