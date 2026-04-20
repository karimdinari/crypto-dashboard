import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { useData } from '../context/DataContext'
import { MarketTag } from '../components/MarketTag'
import { AnimatedNumber } from '../components/AnimatedNumber'
import type { MarketType } from '../types'

const STORAGE_KEY = 'mat-portfolio-positions'

interface Position {
  id: string
  symbol: string
  name: string
  market: MarketType
  quantity: number
  entryPrice: number
  addedAt: string
}

function loadPositions(): Position[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as Position[]) : []
  } catch {
    return []
  }
}

function savePositions(p: Position[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p))
  } catch { /* ignore */ }
}

function DonutChart({ segments }: { segments: { label: string; value: number; color: string }[] }) {
  const total = segments.reduce((s, g) => s + g.value, 0) || 1
  const r = 70
  const cx = 88
  const cy = 88
  const circumference = 2 * Math.PI * r

  let cumulative = 0
  const arcs = segments.map((seg) => {
    const pct = seg.value / total
    const offset = circumference * (1 - cumulative)
    cumulative += pct
    return { ...seg, dasharray: `${circumference * pct} ${circumference * (1 - pct)}`, offset }
  })

  return (
    <svg width={176} height={176} viewBox="0 0 176 176" className="mx-auto">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--app-terminal-elevated)" strokeWidth="18" />
      {arcs.map((a) => (
        <circle
          key={a.label}
          className="donut-segment animate-donut-draw"
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={a.color}
          strokeWidth="18"
          strokeDasharray={a.dasharray}
          strokeDashoffset={a.offset}
          strokeLinecap="butt"
          transform={`rotate(-90 ${cx} ${cy})`}
        />
      ))}
      <text x={cx} y={cy - 6} textAnchor="middle" fill="var(--app-terminal-text)" fontSize="13" fontWeight="700" fontFamily="IBM Plex Mono">
        {segments.length}
      </text>
      <text x={cx} y={cy + 12} textAnchor="middle" fill="var(--app-terminal-muted)" fontSize="10">
        assets
      </text>
    </svg>
  )
}

const MARKET_COLORS: Record<MarketType, string> = {
  crypto: 'var(--app-crypto)',
  forex: 'var(--app-forex)',
  metals: 'var(--app-metals)',
}

export function PortfolioTracker() {
  const { assets } = useData()
  const [positions, setPositions] = useState<Position[]>(loadPositions)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ symbol: assets[0]?.symbol ?? '', quantity: '', entryPrice: '' })
  const [formError, setFormError] = useState('')
  const mounted = useRef(false)

  useEffect(() => {
    if (mounted.current) savePositions(positions)
    mounted.current = true
  }, [positions])

  const getPrice = useCallback(
    (symbol: string) => assets.find((a) => a.symbol === symbol)?.price ?? null,
    [assets],
  )

  const enriched = useMemo(() =>
    positions.map((p) => {
      const current = getPrice(p.symbol) ?? p.entryPrice
      const asset = assets.find((a) => a.symbol === p.symbol)
      const value = current * p.quantity
      const cost = p.entryPrice * p.quantity
      const pnl = value - cost
      const pnlPct = cost > 0 ? (pnl / cost) * 100 : 0
      return { ...p, current, value, cost, pnl, pnlPct, market: (asset?.market ?? p.market) as MarketType }
    }),
    [positions, getPrice, assets],
  )

  const totalValue = enriched.reduce((s, p) => s + p.value, 0)
  const totalCost  = enriched.reduce((s, p) => s + p.cost, 0)
  const totalPnl   = totalValue - totalCost
  const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost) * 100 : 0

  const bestPos  = enriched.reduce<typeof enriched[0] | null>((b, p) => (!b || p.pnlPct > b.pnlPct ? p : b), null)
  const worstPos = enriched.reduce<typeof enriched[0] | null>((b, p) => (!b || p.pnlPct < b.pnlPct ? p : b), null)

  const donutSegs = (['crypto', 'forex', 'metals'] as MarketType[]).map((m) => ({
    label: m,
    value: enriched.filter((p) => p.market === m).reduce((s, p) => s + p.value, 0),
    color: MARKET_COLORS[m],
  })).filter((s) => s.value > 0)

  const addPosition = () => {
    setFormError('')
    const qty = parseFloat(form.quantity)
    const ep  = parseFloat(form.entryPrice)
    if (!form.symbol) { setFormError('Choose an asset.'); return }
    if (isNaN(qty) || qty <= 0) { setFormError('Enter a valid quantity > 0.'); return }
    if (isNaN(ep)  || ep <= 0) { setFormError('Enter a valid entry price > 0.'); return }
    const asset = assets.find((a) => a.symbol === form.symbol)
    const newPos: Position = {
      id: `${Date.now()}`,
      symbol: form.symbol,
      name: asset?.name ?? form.symbol,
      market: (asset?.market ?? 'crypto') as MarketType,
      quantity: qty,
      entryPrice: ep,
      addedAt: new Date().toISOString(),
    }
    setPositions((prev) => [newPos, ...prev])
    setForm({ symbol: assets[0]?.symbol ?? '', quantity: '', entryPrice: '' })
    setShowForm(false)
  }

  const removePosition = (id: string) =>
    setPositions((prev) => prev.filter((p) => p.id !== id))

  return (
    <PageLayout>
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 animate-fade-up">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-terminal-muted">Portfolio</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-terminal-text">Tracker</h1>
          <p className="mt-1 text-[12px] text-terminal-muted">
            Positions valued at live prices · stored locally
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-[12px] font-semibold text-accent transition hover:bg-accent/20"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
              <path d="M12 5v14M5 12h14" />
            </svg>
            Add position
          </button>
          <Link to="/" className="rounded-lg border border-terminal-border px-3 py-2 text-[12px] text-accent hover:bg-terminal-elevated">
            ← Dashboard
          </Link>
        </div>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="mb-6 animate-scale-in rounded-xl border border-accent/25 bg-terminal-surface p-4 shadow-[0_0_32px_rgba(92,225,255,0.06)]">
          <h2 className="mb-4 text-[11px] font-bold uppercase tracking-wide text-terminal-muted">New position</h2>
          <div className="flex flex-wrap gap-3">
            <div className="flex-1 min-w-[140px]">
              <label className="mb-1.5 block text-[10px] uppercase tracking-wide text-terminal-muted">Asset</label>
              <select
                value={form.symbol}
                onChange={(e) => setForm((f) => ({ ...f, symbol: e.target.value }))}
                className="w-full rounded-lg border border-terminal-border bg-terminal-elevated px-3 py-2 text-[13px] text-terminal-text focus:border-accent/50 focus:outline-none"
              >
                {assets.map((a) => (
                  <option key={a.symbol} value={a.symbol}>{a.symbol}</option>
                ))}
              </select>
            </div>
            <div className="flex-1 min-w-[120px]">
              <label className="mb-1.5 block text-[10px] uppercase tracking-wide text-terminal-muted">Quantity</label>
              <input
                type="number"
                min="0"
                step="any"
                value={form.quantity}
                onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
                placeholder="0.5"
                className="w-full rounded-lg border border-terminal-border bg-terminal-elevated px-3 py-2 font-mono text-[13px] text-terminal-text placeholder:text-terminal-muted/60 focus:border-accent/50 focus:outline-none"
              />
            </div>
            <div className="flex-1 min-w-[140px]">
              <label className="mb-1.5 block text-[10px] uppercase tracking-wide text-terminal-muted">Entry price (USD)</label>
              <input
                type="number"
                min="0"
                step="any"
                value={form.entryPrice}
                onChange={(e) => setForm((f) => ({ ...f, entryPrice: e.target.value }))}
                placeholder="80000"
                className="w-full rounded-lg border border-terminal-border bg-terminal-elevated px-3 py-2 font-mono text-[13px] text-terminal-text placeholder:text-terminal-muted/60 focus:border-accent/50 focus:outline-none"
              />
            </div>
            <div className="flex items-end gap-2">
              <button
                type="button"
                onClick={addPosition}
                className="rounded-lg bg-accent px-4 py-2 text-[12px] font-bold text-terminal-bg transition hover:opacity-90"
              >
                Add
              </button>
              <button
                type="button"
                onClick={() => { setShowForm(false); setFormError('') }}
                className="rounded-lg border border-terminal-border px-3 py-2 text-[12px] text-terminal-muted hover:bg-terminal-elevated"
              >
                Cancel
              </button>
            </div>
          </div>
          {formError && <p className="mt-2 text-[11px] text-down">{formError}</p>}
        </div>
      )}

      {/* Empty state */}
      {positions.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center animate-fade-up">
          <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-2xl border border-terminal-border/60 bg-terminal-surface/60">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.25" className="text-terminal-muted">
              <path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z" />
              <path d="M16 3H8a2 2 0 0 0-2 2v2h12V5a2 2 0 0 0-2-2z" />
              <circle cx="16" cy="14" r="1" fill="currentColor" stroke="none" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-terminal-text">No positions yet</h2>
          <p className="mt-2 max-w-xs text-[13px] text-terminal-muted">
            Add your first position to track value and P&L against live market data.
          </p>
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="mt-5 inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-4 py-2.5 text-[13px] font-semibold text-accent hover:bg-accent/20"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
              <path d="M12 5v14M5 12h14" />
            </svg>
            Add first position
          </button>
        </div>
      )}

      {positions.length > 0 && (
        <>
          {/* Summary cards */}
          <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                label: 'Total value',
                value: `$${totalValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
                sub: `Cost basis $${totalCost.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
                tone: 'text-terminal-text',
              },
              {
                label: 'Unrealised P&L',
                value: `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
                sub: `${totalPnlPct >= 0 ? '+' : ''}${totalPnlPct.toFixed(2)}% overall`,
                tone: totalPnl >= 0 ? 'text-up' : 'text-down',
              },
              {
                label: 'Best performer',
                value: bestPos ? bestPos.symbol : '—',
                sub: bestPos ? `+${bestPos.pnlPct.toFixed(2)}%` : '—',
                tone: 'text-up',
              },
              {
                label: 'Worst performer',
                value: worstPos ? worstPos.symbol : '—',
                sub: worstPos ? `${worstPos.pnlPct.toFixed(2)}%` : '—',
                tone: worstPos && worstPos.pnlPct < 0 ? 'text-down' : 'text-terminal-muted',
              },
            ].map((c, i) => (
              <div
                key={c.label}
                className={`animate-fade-up rounded-xl border border-terminal-border bg-terminal-surface p-4 delay-${i * 75}`}
              >
                <p className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">{c.label}</p>
                <p className={`mt-1.5 font-mono text-xl font-semibold ${c.tone}`}>{c.value}</p>
                <p className="mt-0.5 text-[11px] text-terminal-muted">{c.sub}</p>
              </div>
            ))}
          </div>

          {/* Donut + positions table */}
          <div className="mb-6 grid gap-4 lg:grid-cols-[220px_1fr]">
            {/* Donut */}
            <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 animate-fade-up">
              <h2 className="mb-3 text-[10px] font-bold uppercase tracking-wide text-terminal-muted">Allocation</h2>
              <DonutChart segments={donutSegs} />
              <div className="mt-4 space-y-1.5">
                {donutSegs.map((s) => (
                  <div key={s.label} className="flex items-center justify-between text-[11px]">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                      <span className="capitalize text-terminal-muted">{s.label}</span>
                    </span>
                    <span className="font-mono text-terminal-text">
                      {((s.value / totalValue) * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Positions table */}
            <div className="rounded-xl border border-terminal-border bg-terminal-surface animate-fade-up overflow-hidden">
              <div className="border-b border-terminal-border/60 bg-terminal-elevated/30 px-4 py-3">
                <h2 className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">
                  Positions ({positions.length})
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-[12px]">
                  <thead className="border-b border-terminal-border/60 text-terminal-muted">
                    <tr>
                      <th className="px-4 py-2.5 font-medium">Asset</th>
                      <th className="px-4 py-2.5 font-medium">Qty</th>
                      <th className="px-4 py-2.5 font-medium">Entry</th>
                      <th className="px-4 py-2.5 font-medium">Current</th>
                      <th className="px-4 py-2.5 font-medium">Value</th>
                      <th className="px-4 py-2.5 font-medium">P&L</th>
                      <th className="px-4 py-2.5 font-medium">P&L %</th>
                      <th className="px-2 py-2.5" />
                    </tr>
                  </thead>
                  <tbody className="font-mono">
                    {enriched.map((p) => (
                      <tr
                        key={p.id}
                        className="border-b border-terminal-border/40 transition hover:bg-terminal-elevated/30 animate-row-in"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-terminal-text">{p.symbol}</span>
                            <MarketTag market={p.market} />
                          </div>
                          <p className="text-[10px] text-terminal-muted">{p.name}</p>
                        </td>
                        <td className="px-4 py-3 text-terminal-text">{p.quantity}</td>
                        <td className="px-4 py-3 text-terminal-muted">
                          ${p.entryPrice > 10 ? p.entryPrice.toLocaleString(undefined, { maximumFractionDigits: 2 }) : p.entryPrice.toFixed(4)}
                        </td>
                        <td className="px-4 py-3 text-accent">
                          <AnimatedNumber
                            value={p.current}
                            decimals={p.current > 10 ? 2 : 4}
                            prefix="$"
                            formatFn={p.current > 100 ? (v) => `$${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : undefined}
                          />
                        </td>
                        <td className="px-4 py-3 text-terminal-text">
                          ${p.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className={`px-4 py-3 ${p.pnl >= 0 ? 'text-up' : 'text-down'}`}>
                          {p.pnl >= 0 ? '+' : ''}${Math.abs(p.pnl).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className={`px-4 py-3 font-semibold ${p.pnlPct >= 0 ? 'text-up' : 'text-down'}`}>
                          {p.pnlPct >= 0 ? '+' : ''}{p.pnlPct.toFixed(2)}%
                        </td>
                        <td className="px-2 py-3">
                          <button
                            type="button"
                            onClick={() => removePosition(p.id)}
                            className="rounded p-1 text-terminal-muted transition hover:bg-down/15 hover:text-down"
                            aria-label={`Remove ${p.symbol}`}
                          >
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                              <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                            </svg>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </PageLayout>
  )
}
