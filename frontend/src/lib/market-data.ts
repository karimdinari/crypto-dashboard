// Mock data for the Market Analytics Terminal
// All values are illustrative only.

export type AssetClass = "crypto" | "forex" | "metals";
export type Signal = "BUY" | "SELL" | "HOLD";

export interface Asset {
  symbol: string;
  name: string;
  class: AssetClass;
  price: number;
  change: number; // percent
  spark: number[];
}

export const ASSETS: Asset[] = [
  { symbol: "BTC/USD", name: "Bitcoin",   class: "crypto", price: 67432.18, change:  2.84, spark: gen(40, 65000, 70000) },
  { symbol: "ETH/USD", name: "Ethereum",  class: "crypto", price:  3521.74, change:  1.62, spark: gen(40, 3300, 3600) },
  { symbol: "EUR/USD", name: "Euro",      class: "forex",  price:  1.0842,  change: -0.21, spark: gen(40, 1.075, 1.09) },
  { symbol: "GBP/USD", name: "Sterling",  class: "forex",  price:  1.2671,  change:  0.34, spark: gen(40, 1.255, 1.275) },
  { symbol: "XAU/USD", name: "Gold",      class: "metals", price:  2384.55, change:  0.92, spark: gen(40, 2340, 2400) },
  { symbol: "XAG/USD", name: "Silver",    class: "metals", price:    28.41, change: -0.47, spark: gen(40, 27.8, 29.1) },
];

function gen(n: number, min: number, max: number): number[] {
  const out: number[] = [];
  let v = (min + max) / 2;
  for (let i = 0; i < n; i++) {
    v += (Math.random() - 0.5) * (max - min) * 0.08;
    v = Math.max(min, Math.min(max, v));
    out.push(+v.toFixed(4));
  }
  return out;
}

// Candle series for the central chart (BTC/USD style)
export const CANDLES = (() => {
  const out: { t: string; o: number; h: number; l: number; c: number; v: number }[] = [];
  let p = 66800;
  for (let i = 0; i < 80; i++) {
    const o = p;
    const c = +(o + (Math.random() - 0.45) * 280).toFixed(2);
    const h = +Math.max(o, c, o + Math.random() * 180).toFixed(2);
    const l = +Math.min(o, c, o - Math.random() * 180).toFixed(2);
    const v = +(Math.random() * 800 + 200).toFixed(0);
    p = c;
    const d = new Date(Date.now() - (80 - i) * 60_000 * 15);
    out.push({ t: d.toISOString(), o, h, l, c, v });
  }
  return out;
})();

// Line series derived from candles for area chart
export const PRICE_SERIES = CANDLES.map((c, i) => ({
  i,
  t: new Date(c.t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  price: c.c,
  ma7: 0,
  ma30: 0,
}));

// fill MAs
for (let i = 0; i < PRICE_SERIES.length; i++) {
  const w7 = PRICE_SERIES.slice(Math.max(0, i - 6), i + 1);
  const w30 = PRICE_SERIES.slice(Math.max(0, i - 29), i + 1);
  PRICE_SERIES[i].ma7 = +(w7.reduce((a, b) => a + b.price, 0) / w7.length).toFixed(2);
  PRICE_SERIES[i].ma30 = +(w30.reduce((a, b) => a + b.price, 0) / w30.length).toFixed(2);
}

export const NEWS = [
  { id: 1, source: "Bloomberg",  badge: "BBG", time: "2m",  title: "Fed minutes hint at extended pause as inflation cools below forecast", sentiment: 0.42, asset: "FOREX" },
  { id: 2, source: "Reuters",    badge: "RTR", time: "8m",  title: "ETF inflows accelerate — institutional BTC allocation hits new quarterly high", sentiment: 0.71, asset: "BTC" },
  { id: 3, source: "FT",         badge: "FT",  time: "14m", title: "Gold tests resistance at $2,400 as central banks expand reserves", sentiment: 0.55, asset: "XAU" },
  { id: 4, source: "CoinDesk",   badge: "CD",  time: "22m", title: "Ethereum L2 throughput up 38% week-on-week, fees stabilize", sentiment: 0.38, asset: "ETH" },
  { id: 5, source: "WSJ",        badge: "WSJ", time: "31m", title: "Sterling slips on softer UK retail data; gilt yields ease", sentiment: -0.34, asset: "GBP" },
  { id: 6, source: "Kitco",      badge: "KTC", time: "47m", title: "Silver industrial demand surges on solar manufacturing pipeline", sentiment: 0.61, asset: "XAG" },
  { id: 7, source: "Bloomberg",  badge: "BBG", time: "1h",  title: "ECB officials split on timing of next rate move, sources say", sentiment: -0.12, asset: "EUR" },
  { id: 8, source: "Reuters",    badge: "RTR", time: "1h",  title: "Crypto open interest reaches multi-month peak across major venues", sentiment: 0.48, asset: "BTC" },
];

export const TICKS = Array.from({ length: 14 }, (_, i) => {
  const a = ASSETS[i % ASSETS.length];
  const dir = Math.random() > 0.5 ? 1 : -1;
  return {
    id: i,
    symbol: a.symbol,
    class: a.class,
    price: +(a.price * (1 + dir * Math.random() * 0.001)).toFixed(a.symbol.includes("/USD") && a.class === "forex" ? 5 : 2),
    delta: +(dir * Math.random() * 0.12).toFixed(3),
    venue: ["BINANCE", "COINBASE", "OANDA", "LMAX", "KRAKEN"][i % 5],
    ts: new Date(Date.now() - i * 1700).toLocaleTimeString([], { hour12: false }),
  };
});

// Correlation matrix (symmetric)
export const CORR_ASSETS = ["BTC", "ETH", "EUR", "GBP", "XAU", "XAG"];
export const CORR_MATRIX: number[][] = [
  [ 1.00,  0.78,  0.12, -0.05,  0.31,  0.24],
  [ 0.78,  1.00,  0.18, -0.02,  0.27,  0.21],
  [ 0.12,  0.18,  1.00,  0.64, -0.18, -0.11],
  [-0.05, -0.02,  0.64,  1.00, -0.22, -0.14],
  [ 0.31,  0.27, -0.18, -0.22,  1.00,  0.82],
  [ 0.24,  0.21, -0.11, -0.14,  0.82,  1.00],
];

export const PIPELINE_TASKS = [
  { id: "ingest_binance",   layer: "Bronze", status: "ok",   lastRun: "12s",  duration: "0.8s",  type: "stream" },
  { id: "ingest_oanda_fx",  layer: "Bronze", status: "ok",   lastRun: "08s",  duration: "1.1s",  type: "stream" },
  { id: "ingest_metals",    layer: "Bronze", status: "ok",   lastRun: "04m",  duration: "3.2s",  type: "batch"  },
  { id: "ingest_news_rss",  layer: "Bronze", status: "warn", lastRun: "11m",  duration: "12.4s", type: "batch"  },
  { id: "clean_dedupe",     layer: "Silver", status: "ok",   lastRun: "02m",  duration: "8.6s",  type: "batch"  },
  { id: "feature_returns",  layer: "Silver", status: "ok",   lastRun: "02m",  duration: "4.1s",  type: "batch"  },
  { id: "feature_indicators",layer:"Silver", status: "ok",   lastRun: "02m",  duration: "5.7s",  type: "batch"  },
  { id: "sentiment_score",  layer: "Silver", status: "ok",   lastRun: "03m",  duration: "11.2s", type: "batch"  },
  { id: "agg_correlations", layer: "Gold",   status: "ok",   lastRun: "05m",  duration: "2.3s",  type: "batch"  },
  { id: "model_predictions",layer: "Gold",   status: "ok",   lastRun: "05m",  duration: "6.8s",  type: "batch"  },
  { id: "publish_signals",  layer: "Gold",   status: "ok",   lastRun: "05m",  duration: "0.9s",  type: "batch"  },
];

export const SIGNAL = {
  asset: "BTC/USD",
  direction: "BUY" as Signal,
  confidence: 0.78,
  horizon: "4H",
  model: "lgbm-v3.2 · ensemble",
  features: [
    { name: "MA7 / MA30 cross",     weight: 0.31 },
    { name: "Realized volatility",  weight: 0.22 },
    { name: "News sentiment (24h)", weight: 0.19 },
    { name: "Cross-asset corr",     weight: 0.14 },
    { name: "Order-flow imbalance", weight: 0.14 },
  ],
};
