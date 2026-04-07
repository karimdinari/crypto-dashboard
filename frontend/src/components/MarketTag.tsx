import type { MarketType } from '../types'

const styles: Record<MarketType, string> = {
  crypto: 'bg-terminal-elevated text-crypto border-terminal-border',
  forex: 'bg-terminal-elevated text-forex border-terminal-border',
  metals: 'bg-terminal-elevated text-metals border-terminal-border',
}

const labels: Record<MarketType, string> = {
  crypto: 'Crypto',
  forex: 'Forex',
  metals: 'Metals',
}

export function MarketTag({ market }: { market: MarketType }) {
  return (
    <span
      className={`inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide transition-colors duration-150 ${styles[market]}`}
    >
      {labels[market]}
    </span>
  )
}
