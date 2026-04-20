import type { MarketType } from '../types'

const styles: Record<MarketType, string> = {
  crypto:
    'border-crypto/40 bg-crypto/[0.07] text-crypto shadow-[0_0_16px_rgba(0,240,255,0.08)]',
  forex:
    'border-forex/40 bg-forex/[0.08] text-forex shadow-[0_0_14px_rgba(157,140,255,0.07)]',
  metals:
    'border-metals/45 bg-metals/[0.09] text-metals shadow-[0_0_16px_rgba(244,193,90,0.08)]',
}

const labels: Record<MarketType, string> = {
  crypto: 'Crypto',
  forex: 'Forex',
  metals: 'Metals',
}

export function MarketTag({ market }: { market: MarketType }) {
  return (
    <span
      className={`inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] transition-colors duration-150 ${styles[market]}`}
    >
      {labels[market]}
    </span>
  )
}
