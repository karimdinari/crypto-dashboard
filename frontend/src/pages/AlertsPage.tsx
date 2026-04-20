import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { useData } from '../context/DataContext'
import { MarketTag } from '../components/MarketTag'
import type { MarketType } from '../types'

const STORAGE_KEY = 'mat-price-alerts'

type AlertCondition = 'above' | 'below'

interface PriceAlert {
  id: string
  symbol: string
  market: MarketType
  condition: AlertCondition
  targetPrice: number
  createdAt: string
  triggered: boolean
  triggeredAt?: string
}

function loadAlerts(): PriceAlert[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as PriceAlert[]) : []
  } catch {
    return []
  }
}

function saveAlerts(a: PriceAlert[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(a))
  } catch { /* ignore */ }
}

function fmtPrice(v: number) {
  if (v > 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  if (v > 1) return v.toFixed(4)
  return v.toFixed(6)
}

function progressPct(current: number, target: number, condition: AlertCondition): number {
  if (condition === 'above') {
    return Math.min((current / target) * 100, 100)
  } else {
    if (current === 0) return 100
    return Math.min((target / current) * 100, 100)
  }
}

export function AlertsPage() {
  const { assets } = useData()
  const [alerts, setAlerts] = useState<PriceAlert[]>(loadAlerts)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    symbol: assets[0]?.symbol ?? '',
    condition: 'above' as AlertCondition,
    targetPrice: '',
  })
  const [formError, setFormError] = useState('')
  const [flash, setFlash] = useState<string | null>(null)
  const mounted = useRef(false)
  const prevPrices = useRef<Record<string, number>>({})

  // Persist on change
  useEffect(() => {
    if (mounted.current) saveAlerts(alerts)
    mounted.current = true
  }, [alerts])

  // Price-check: evaluate alerts every time assets change
  useEffect(() => {
    if (!assets.length) return
    setAlerts((prev) =>
      prev.map((alert) => {
        if (alert.triggered) return alert
        const asset = assets.find((a) => a.symbol === alert.symbol)
        if (!asset) return alert
        const price = asset.price
        const hit =
          alert.condition === 'above' ? price >= alert.targetPrice : price <= alert.targetPrice
        if (hit) {
          // Flash the triggered alert
          setFlash(alert.id)
          setTimeout(() => setFlash(null), 3000)
          return { ...alert, triggered: true, triggeredAt: new Date().toISOString() }
        }
        return alert
      }),
    )
    // Track prev prices for arrow direction
    assets.forEach((a) => { prevPrices.current[a.symbol] = a.price })
  }, [assets])

  const getPrice = useCallback(
    (symbol: string) => assets.find((a) => a.symbol === symbol)?.price ?? null,
    [assets],
  )

  const enriched = useMemo(() =>
    alerts.map((a) => ({
      ...a,
      current: getPrice(a.symbol) ?? a.targetPrice,
      progress: progressPct(getPrice(a.symbol) ?? a.targetPrice, a.targetPrice, a.condition),
    })),
    [alerts, getPrice],
  )

  const activeCount    = alerts.filter((a) => !a.triggered).length
  const triggeredCount = alerts.filter((a) => a.triggered).length

  const addAlert = () => {
    setFormError('')
    const tp = parseFloat(form.targetPrice)
    if (!form.symbol) { setFormError('Choose an asset.'); return }
    if (isNaN(tp) || tp <= 0) { setFormError('Enter a valid target price > 0.'); return }
    const asset = assets.find((a) => a.symbol === form.symbol)
    const newAlert: PriceAlert = {
      id: `${Date.now()}`,
      symbol: form.symbol,
      market: (asset?.market ?? 'crypto') as MarketType,
      condition: form.condition,
      targetPrice: tp,
      createdAt: new Date().toISOString(),
      triggered: false,
    }
    setAlerts((prev) => [newAlert, ...prev])
    setForm({ symbol: assets[0]?.symbol ?? '', condition: 'above', targetPrice: '' })
    setShowForm(false)
  }

  const removeAlert = (id: string) => setAlerts((prev) => prev.filter((a) => a.id !== id))

  const clearTriggered = () => setAlerts((prev) => prev.filter((a) => !a.triggered))

  return (
    <PageLayout>
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 animate-fade-up">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-terminal-muted">Price</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-terminal-text">Alerts</h1>
          <p className="mt-1 text-[12px] text-terminal-muted">
            {activeCount} active · {triggeredCount} triggered · evaluated on every data refresh
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
            New alert
          </button>
          {triggeredCount > 0 && (
            <button
              type="button"
              onClick={clearTriggered}
              className="rounded-lg border border-terminal-border px-3 py-2 text-[12px] text-terminal-muted hover:bg-terminal-elevated"
            >
              Clear triggered
            </button>
          )}
          <Link to="/" className="rounded-lg border border-terminal-border px-3 py-2 text-[12px] text-accent hover:bg-terminal-elevated">
            ← Dashboard
          </Link>
        </div>
      </div>

      {/* Summary */}
      <div className="mb-6 grid gap-3 sm:grid-cols-3 animate-fade-up delay-75">
        {[
          { label: 'Active', value: activeCount, cls: 'text-accent', bdr: 'border-accent/20 bg-accent/5' },
          { label: 'Triggered', value: triggeredCount, cls: 'text-up', bdr: 'border-up/20 bg-up/5' },
          { label: 'Total', value: alerts.length, cls: 'text-terminal-text', bdr: 'border-terminal-border bg-terminal-surface' },
        ].map((c) => (
          <div key={c.label} className={`rounded-xl border ${c.bdr} p-4`}>
            <p className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">{c.label}</p>
            <p className={`mt-1 font-mono text-2xl font-bold ${c.cls}`}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* New alert form */}
      {showForm && (
        <div className="mb-6 animate-scale-in rounded-xl border border-accent/25 bg-terminal-surface p-4 shadow-[0_0_32px_rgba(92,225,255,0.06)]">
          <h2 className="mb-4 text-[11px] font-bold uppercase tracking-wide text-terminal-muted">Create alert</h2>
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
            <div className="min-w-[140px]">
              <label className="mb-1.5 block text-[10px] uppercase tracking-wide text-terminal-muted">Condition</label>
              <div className="flex rounded-lg border border-terminal-border bg-terminal-elevated p-0.5">
                {(['above', 'below'] as const).map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, condition: c }))}
                    className={`flex-1 rounded-md px-3 py-1.5 text-[12px] font-semibold capitalize transition ${
                      form.condition === c
                        ? c === 'above'
                          ? 'bg-up/20 text-up'
                          : 'bg-down/20 text-down'
                        : 'text-terminal-muted hover:text-terminal-text'
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex-1 min-w-[140px]">
              <label className="mb-1.5 block text-[10px] uppercase tracking-wide text-terminal-muted">Target price (USD)</label>
              <input
                type="number"
                min="0"
                step="any"
                value={form.targetPrice}
                onChange={(e) => setForm((f) => ({ ...f, targetPrice: e.target.value }))}
                placeholder="90000"
                className="w-full rounded-lg border border-terminal-border bg-terminal-elevated px-3 py-2 font-mono text-[13px] text-terminal-text placeholder:text-terminal-muted/60 focus:border-accent/50 focus:outline-none"
              />
            </div>
            <div className="flex items-end gap-2">
              <button type="button" onClick={addAlert}
                className="rounded-lg bg-accent px-4 py-2 text-[12px] font-bold text-terminal-bg transition hover:opacity-90">
                Set alert
              </button>
              <button type="button" onClick={() => { setShowForm(false); setFormError('') }}
                className="rounded-lg border border-terminal-border px-3 py-2 text-[12px] text-terminal-muted hover:bg-terminal-elevated">
                Cancel
              </button>
            </div>
          </div>
          {formError && <p className="mt-2 text-[11px] text-down">{formError}</p>}
        </div>
      )}

      {/* Empty state */}
      {alerts.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center animate-fade-up">
          <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-2xl border border-terminal-border/60 bg-terminal-surface/60">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.25" className="text-terminal-muted">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-terminal-text">No alerts set</h2>
          <p className="mt-2 max-w-xs text-[13px] text-terminal-muted">
            Create a price alert to be notified when an asset crosses your target.
          </p>
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="mt-5 inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-4 py-2.5 text-[13px] font-semibold text-accent hover:bg-accent/20"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
              <path d="M12 5v14M5 12h14" />
            </svg>
            Create first alert
          </button>
        </div>
      )}

      {/* Alert cards */}
      {alerts.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted animate-fade-up delay-150">
            All alerts
          </h2>
          {enriched.map((a, i) => {
            const isTriggered = a.triggered
            const isFlashing  = flash === a.id
            const pctBar = a.progress
            const barColor = a.condition === 'above'
              ? pctBar >= 100 ? 'bg-up' : 'bg-accent'
              : pctBar >= 100 ? 'bg-up' : 'bg-down'

            return (
              <div
                key={a.id}
                className={`animate-fade-up rounded-xl border p-4 transition delay-${Math.min(i * 75, 450)} ${
                  isFlashing
                    ? 'border-up/60 bg-up/10 shadow-[0_0_32px_rgba(62,232,176,0.25)]'
                    : isTriggered
                      ? 'border-up/25 bg-up/5'
                      : 'border-terminal-border bg-terminal-surface'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                      isTriggered ? 'bg-up/20 text-up' : a.condition === 'above' ? 'bg-accent/15 text-accent' : 'bg-down/15 text-down'
                    }`}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
                        {isTriggered
                          ? <path d="M20 6 9 17l-5-5" />
                          : a.condition === 'above'
                            ? <path d="M12 19V5M5 12l7-7 7 7" />
                            : <path d="M12 5v14M5 12l7 7 7-7" />
                        }
                      </svg>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[13px] font-semibold text-terminal-text">{a.symbol}</span>
                        <MarketTag market={a.market} />
                        {isTriggered && (
                          <span className="rounded-full border border-up/40 bg-up/15 px-2 py-0.5 font-mono text-[10px] font-bold text-up">
                            TRIGGERED
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 text-[11px] text-terminal-muted">
                        Alert{' '}
                        <span className={a.condition === 'above' ? 'text-up' : 'text-down'}>
                          {a.condition}
                        </span>{' '}
                        <span className="font-mono text-terminal-text">${fmtPrice(a.targetPrice)}</span>
                        {a.triggeredAt && (
                          <> · triggered {new Date(a.triggeredAt).toLocaleTimeString()}</>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="font-mono text-[13px] text-accent">${fmtPrice(a.current)}</p>
                      <p className="text-[10px] text-terminal-muted">current</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeAlert(a.id)}
                      className="rounded-lg p-2 text-terminal-muted transition hover:bg-down/15 hover:text-down"
                      aria-label={`Remove alert for ${a.symbol}`}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                        <path d="M18 6 6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-3">
                  <div className="mb-1 flex justify-between text-[10px] text-terminal-muted">
                    <span>Progress to target</span>
                    <span className="font-mono">{Math.min(pctBar, 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-terminal-elevated">
                    <div
                      className={`h-full rounded-full animate-bar-grow ${barColor} transition-all duration-700`}
                      style={{ width: `${Math.min(pctBar, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </PageLayout>
  )
}
