import { useMemo } from 'react'
import { PageLayout } from '../components/PageLayout'
import { CorrelationHeatmap } from '../components/dashboard/CorrelationHeatmap'
import { useData } from '../context/DataContext'
import { buildAssetCorrelation } from '../lib/correlationMatrix'

export function CorrelationsPage() {
  const { assets } = useData()

  const { labels, matrix, topPos, topNeg } = useMemo(() => {
    const { labels: lb, matrix: mx } = buildAssetCorrelation(assets)
    const pairs: { a: string; b: string; v: number }[] = []
    for (let i = 0; i < mx.length; i++) {
      for (let j = i + 1; j < mx.length; j++) {
        pairs.push({ a: lb[i], b: lb[j], v: mx[i][j] })
      }
    }
    const pos = [...pairs].filter((p) => p.v > 0).sort((x, y) => y.v - x.v).slice(0, 4)
    const neg = [...pairs].filter((p) => p.v < 0).sort((x, y) => x.v - y.v).slice(0, 4)
    return { labels: lb, matrix: mx, topPos: pos, topNeg: neg }
  }, [assets])

  return (
    <PageLayout className="max-w-[1800px]">
      <div className="mb-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-terminal-muted">
          Quant desk
        </p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-terminal-text md:text-3xl">
          Correlations & analytics
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-terminal-muted">
          Cross-asset co-movement for risk and feature design. Replace demo coefficients with your Gold
          correlation or rolling covariance estimates.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-5">
        <div className="xl:col-span-3">
          <CorrelationHeatmap
            labels={labels}
            matrix={matrix}
            title="Correlation matrix"
            subtitle="Symmetric Pearson-style view (synthetic for UI)"
          />
        </div>
        <div className="flex flex-col gap-4 xl:col-span-2">
          <div className="glass-panel rounded-xl border border-up/25 p-4">
            <h2 className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">
              Strongest positive
            </h2>
            <ul className="mt-3 space-y-2">
              {topPos.map((p) => (
                <li
                  key={`${p.a}-${p.b}`}
                  className="flex items-center justify-between rounded-lg border border-terminal-border/50 bg-terminal-bg/40 px-3 py-2 font-mono text-[12px]"
                >
                  <span className="text-terminal-text">
                    {p.a} ↔ {p.b}
                  </span>
                  <span className="text-up">{p.v.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="glass-panel rounded-xl border border-down/25 p-4">
            <h2 className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">
              Strongest negative
            </h2>
            <ul className="mt-3 space-y-2">
              {topNeg.map((p) => (
                <li
                  key={`${p.a}-${p.b}-n`}
                  className="flex items-center justify-between rounded-lg border border-terminal-border/50 bg-terminal-bg/40 px-3 py-2 font-mono text-[12px]"
                >
                  <span className="text-terminal-text">
                    {p.a} ↔ {p.b}
                  </span>
                  <span className="text-down">{p.v.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="glass-panel rounded-xl border border-terminal-border/80 p-4">
            <h2 className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">
              Feature importance (selected)
            </h2>
            <p className="mt-1 text-[11px] text-terminal-muted">
              Pull from your model artifacts; below mirrors the dashboard asset spotlight.
            </p>
            <ul className="mt-3 space-y-2 text-[12px] text-terminal-muted">
              <li className="flex justify-between border-b border-terminal-border/40 py-1">
                <span>Returns & volatility</span>
                <span className="font-mono text-terminal-text">high</span>
              </li>
              <li className="flex justify-between border-b border-terminal-border/40 py-1">
                <span>News sentiment</span>
                <span className="font-mono text-terminal-text">medium</span>
              </li>
              <li className="flex justify-between py-1">
                <span>Cross-asset beta</span>
                <span className="font-mono text-terminal-text">medium</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </PageLayout>
  )
}
