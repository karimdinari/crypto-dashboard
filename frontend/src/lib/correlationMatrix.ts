import type { Asset } from '../types'

/** Deterministic pseudo-correlation in [-1, 1] for UI demo (wire to Gold layer later). */
function pairCorr(a: Asset, b: Asset): number {
  if (a.symbol === b.symbol) return 1
  let h = 0
  const key = `${a.symbol}|${b.symbol}`
  for (let i = 0; i < key.length; i++) h = (Math.imul(31, h) + key.charCodeAt(i)) | 0
  const base = (Math.abs(Math.sin(h * 0.01)) * 2 - 1) * 0.65
  const same = a.market === b.market ? 0.28 : 0
  const dir = Math.sign(a.changePct) === Math.sign(b.changePct) ? 0.12 : -0.08
  return Math.max(-1, Math.min(1, base + same + dir))
}

export function buildAssetCorrelation(assets: Asset[]) {
  const labels = assets.map((x) => x.symbol)
  const n = assets.length
  const matrix: number[][] = Array.from({ length: n }, () => Array(n).fill(0))
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      matrix[i][j] = pairCorr(assets[i], assets[j])
    }
  }
  return { labels, matrix }
}
