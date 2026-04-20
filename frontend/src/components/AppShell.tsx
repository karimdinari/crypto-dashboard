import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { useData } from '../context/DataContext'
import { useTerminal } from '../context/TerminalContext'
import type { Asset } from '../types'

const navItems = [
  { to: '/', label: 'Dashboard', end: true, icon: 'grid' },
  { to: '/markets', label: 'Markets', icon: 'layers' },
  { to: '/streaming', label: 'Streaming', icon: 'pulse' },
  { to: '/news', label: 'News', icon: 'feed' },
  { to: '/sentiment', label: 'Sentiment', icon: 'chart' },
  { to: '/correlations', label: 'Correlations', icon: 'matrix' },
  { to: '/signals', label: 'Signals', icon: 'signal' },
  { to: '/portfolio', label: 'Portfolio', icon: 'wallet' },
  { to: '/alerts', label: 'Alerts', icon: 'bell' },
  { to: '/pipeline', label: 'Pipeline', icon: 'flow' },
  { to: '/settings', label: 'Settings', icon: 'gear' },
] as const

function NavIcon({ name }: { name: (typeof navItems)[number]['icon'] }) {
  const cls = 'h-4 w-4 shrink-0 opacity-90'
  switch (name) {
    case 'grid':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M4 4h7v7H4V4zm9 0h7v7h-7V4zM4 13h7v7H4v-7zm9 0h7v7h-7v-7z" />
        </svg>
      )
    case 'layers':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
      )
    case 'pulse':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
      )
    case 'feed':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16" />
          <circle cx="5" cy="19" r="1" fill="currentColor" stroke="none" />
        </svg>
      )
    case 'chart':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M3 3v18h18M7 16l4-4 4 4 5-6" />
        </svg>
      )
    case 'matrix':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z" />
        </svg>
      )
    case 'signal':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2.1 2.1m8.6 8.6l2.1 2.1M5.6 18.4l2.1-2.1m8.6-8.6l2.1-2.1" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      )
    case 'wallet':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z" />
          <path d="M16 3H8a2 2 0 0 0-2 2v2h12V5a2 2 0 0 0-2-2z" />
          <circle cx="16" cy="14" r="1" fill="currentColor" stroke="none" />
        </svg>
      )
    case 'bell':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
      )
    case 'flow':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M4 8h4l2-3h8v12H10l-2-3H4V8zm16 4h2v4h-2" />
        </svg>
      )
    case 'gear':
      return (
        <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.14.31.22.65.22 1v.09a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      )
    default:
      return null
  }
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'
  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-terminal-border/80 bg-terminal-elevated/80 text-terminal-muted transition hover:border-terminal-muted hover:text-terminal-text"
      title={isDark ? 'Light workspace' : 'Dark terminal'}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-pressed={!isDark}
    >
      {isDark ? (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
        </svg>
      ) : (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  )
}

function formatClock(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return '—'
  }
}

function tickerColor(asset: Asset) {
  if (asset.market === 'crypto') return 'text-crypto'
  if (asset.market === 'forex') return 'text-forex'
  return 'text-metals'
}

function PriceTicker({ assets }: { assets: Asset[] }) {
  if (!assets.length) return null
  // Duplicate for seamless scroll
  const items = [...assets, ...assets]

  return (
    <div className="overflow-hidden border-t border-white/[0.04] bg-black/20" aria-hidden>
      <div className="ticker-track py-1">
        {items.map((a, i) => (
          <span
            key={`${a.symbol}-${i}`}
            className="mx-4 inline-flex items-center gap-2 whitespace-nowrap font-mono text-[11px]"
          >
            <span className={`font-semibold ${tickerColor(a)}`}>{a.symbol}</span>
            <span className="text-terminal-text">
              {a.price > 100
                ? a.price.toLocaleString(undefined, { maximumFractionDigits: 2 })
                : a.price.toFixed(4)}
            </span>
            <span className={a.changePct >= 0 ? 'text-up' : 'text-down'}>
              {a.changePct >= 0 ? '▲' : '▼'} {Math.abs(a.changePct).toFixed(2)}%
            </span>
            <span className="text-terminal-border">·</span>
          </span>
        ))}
      </div>
    </div>
  )
}

function SidebarNav({
  onNavigate,
  mobile,
}: {
  onNavigate?: () => void
  mobile?: boolean
}) {
  return (
    <nav
      className={`flex flex-col gap-0.5 ${mobile ? 'p-3' : 'px-2 py-3'}`}
      aria-label="Workspace"
    >
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={'end' in item ? item.end : false}
          onClick={onNavigate}
          className={({ isActive }) =>
            [
              'group flex items-center gap-3 rounded-lg px-2.5 py-2 text-[13px] font-medium transition-colors',
              isActive
                ? 'bg-terminal-elevated text-terminal-text shadow-[inset_0_0_0_1px_rgba(0,240,255,0.22),0_0_24px_rgba(0,240,255,0.06)]'
                : 'text-terminal-muted hover:bg-terminal-elevated/60 hover:text-terminal-text',
            ].join(' ')
          }
        >
          <NavIcon name={item.icon} />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { terminalSearch, setTerminalSearch } = useTerminal()
  const { refresh, source, pipeline, loadError, assets, kafkaStreamTicks } = useData()
  const [refreshing, setRefreshing] = useState(false)

  const pipelineOk = source === 'live' && !loadError
  const lastGen = pipeline?.generated_at

  const n = assets.length || 1
  const avgDelta = assets.reduce((s, a) => s + a.changePct, 0) / n
  const breadth = assets.filter((a) => a.changePct >= 0).length
  const tone =
    avgDelta > 0.25
      ? { label: 'Risk-on', cls: 'text-up' }
      : avgDelta < -0.25
        ? { label: 'Defensive', cls: 'text-amber-300/95' }
        : { label: 'Balanced', cls: 'text-terminal-muted' }

  const onRefresh = () => {
    setRefreshing(true)
    void refresh().finally(() => setRefreshing(false))
  }

  return (
    <div className="mat-canvas">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <div className="mat-stack flex min-h-screen">
      {/* Desktop sidebar */}
      <aside
        className="sticky top-0 z-30 hidden h-screen w-[228px] shrink-0 flex-col border-r border-white/[0.06] bg-[var(--app-sidebar)] lg:flex"
        aria-label="Primary navigation"
      >
        <div className="border-b border-white/[0.06] px-4 py-5">
          <div className="flex items-center gap-3">
            <div
              className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-xl font-display text-sm font-bold tracking-tight text-white shadow-[0_0_28px_rgba(0,240,255,0.25)]"
              style={{
                background:
                  'linear-gradient(145deg, rgba(0,240,255,0.35) 0%, rgba(157,140,255,0.35) 50%, rgba(244,193,90,0.25) 100%)',
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)',
              }}
              aria-hidden
            >
              <svg width="26" height="26" viewBox="0 0 32 32" fill="none" className="opacity-95">
                <path d="M16 2 28 9v14L16 30 4 23V9L16 2z" stroke="currentColor" strokeWidth="1.25" className="text-white/90" />
                <path d="M16 8v16M10 12h12M10 20h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="text-white" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="font-display truncate text-[10px] font-semibold uppercase tracking-[0.18em] text-terminal-muted">
                Market Analytics
              </p>
              <p className="font-display truncate text-[15px] font-bold tracking-tight text-terminal-text">Terminal</p>
            </div>
          </div>
          <p className="mt-3 text-[10px] leading-relaxed text-terminal-muted/85">
            Intelligence-grade multi-asset coverage · lakehouse + ML
          </p>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <SidebarNav />
        </div>
        <div className="border-t border-terminal-border/60 p-3 text-[10px] leading-snug text-terminal-muted">
          Historical + live data · NLP sentiment · ML signals
        </div>
      </aside>

      {/* Mobile drawer backdrop */}
      {mobileOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          aria-label="Close menu"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-[min(280px,88vw)] transform border-r border-terminal-border/80 bg-[var(--app-sidebar)] shadow-2xl transition-transform duration-200 ease-out lg:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between border-b border-terminal-border/60 px-3 py-3">
          <span className="text-sm font-bold text-terminal-text">Navigate</span>
          <button
            type="button"
            className="rounded-lg p-2 text-terminal-muted hover:bg-terminal-elevated hover:text-terminal-text"
            onClick={() => setMobileOpen(false)}
            aria-label="Close navigation"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="overflow-y-auto">
          <SidebarNav mobile onNavigate={() => setMobileOpen(false)} />
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 border-b border-white/[0.06] bg-terminal-bg/80 backdrop-blur-xl">
          <div className="flex flex-wrap items-center gap-3 px-3 py-2.5 md:px-4 lg:px-5">
            <button
              type="button"
              className="rounded-lg p-2 text-terminal-muted hover:bg-terminal-elevated lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <div className="min-w-0 flex-1 lg:max-w-[min(420px,40%)]">
              <h1 className="font-display truncate text-[14px] font-semibold tracking-tight text-terminal-text md:text-[15px]">
                Market Analytics Terminal
              </h1>
              <p className="hidden text-[10px] text-terminal-muted sm:block lg:hidden">
                Cross-asset intelligence
              </p>
            </div>

            <div className="flex min-w-0 flex-1 flex-col gap-1.5 sm:flex-row sm:items-center lg:contents">
              <label className="relative min-w-0 flex-1 lg:max-w-md">
                <span className="sr-only">Global symbol search</span>
                <svg
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-terminal-muted"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden
                >
                  <circle cx="11" cy="11" r="7" />
                  <path d="m20 20-3-3" />
                </svg>
                <input
                  type="search"
                  value={terminalSearch}
                  onChange={(e) => setTerminalSearch(e.target.value)}
                  placeholder="Search BTC/USD, XAU/USD, headlines…"
                  autoComplete="off"
                  className="w-full rounded-lg border border-white/[0.08] bg-terminal-bg/90 py-2 pl-9 pr-3 text-[13px] text-terminal-text placeholder:text-terminal-muted/80 focus:border-crypto/40 focus:outline-none focus:ring-1 focus:ring-crypto/25"
                />
              </label>

              <div className="flex flex-wrap items-center gap-2 sm:ml-auto lg:ml-0">
                <div
                  className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${
                    pipelineOk
                      ? 'border-up/35 bg-up/10 text-up'
                      : 'border-amber-500/40 bg-amber-500/10 text-amber-200'
                  }`}
                  title="API + Parquet pipeline"
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${pipelineOk ? 'animate-pulse bg-up shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 'bg-amber-400'}`}
                  />
                  {pipelineOk ? 'Pipeline healthy' : 'Degraded / mock'}
                </div>

                <div className="hidden items-center gap-1.5 rounded-lg border border-terminal-border/60 bg-terminal-elevated/50 px-2 py-1 font-mono text-[10px] text-terminal-muted sm:flex">
                  <span className="text-[9px] uppercase tracking-wide">API</span>
                  <time dateTime={lastGen}>{lastGen ? formatClock(lastGen) : '—'}</time>
                </div>

                <button
                  type="button"
                  onClick={() => void onRefresh()}
                  disabled={refreshing}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-terminal-border/80 bg-terminal-elevated/80 px-2.5 py-1.5 text-[11px] font-semibold text-terminal-text transition hover:border-accent/40 hover:text-accent disabled:opacity-60"
                >
                  <svg
                    className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden
                  >
                    <path d="M23 4v6h-6M1 20v-6h6" />
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                  </svg>
                  Refresh
                </button>

                <ThemeToggle />
              </div>
            </div>
          </div>

          <div className="mat-pulse-line" />

          {/* Live price ticker strip */}
          <PriceTicker assets={assets} />

          <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 border-t border-white/[0.04] bg-black/20 px-3 py-1.5 text-[11px] md:px-5">
            <span className="font-display text-[9px] font-bold uppercase tracking-[0.22em] text-terminal-muted">
              Global pulse
            </span>
            <span className={`font-semibold ${tone.cls}`}>{tone.label}</span>
            <span className="text-terminal-muted">
              Breadth{' '}
              <span className="font-mono text-terminal-text">
                {breadth}/{n}
              </span>
            </span>
            <span className="text-terminal-muted">
              Avg Δ{' '}
              <span className={`font-mono ${avgDelta >= 0 ? 'text-up' : 'text-down'}`}>
                {avgDelta >= 0 ? '+' : ''}
                {avgDelta.toFixed(2)}%
              </span>
            </span>
            <span
              className={
                kafkaStreamTicks.length
                  ? 'font-mono text-crypto'
                  : 'font-mono text-terminal-muted'
              }
            >
              {kafkaStreamTicks.length
                ? `Stream · ${kafkaStreamTicks.length} live`
                : 'Stream · standby'}
            </span>
            <span className="ml-auto hidden font-mono text-[10px] text-terminal-muted/90 sm:inline">
              {source === 'live' ? 'Parquet API' : 'Demo data'}
            </span>
          </div>
        </header>

        <main id="main-content" className="flex-1 outline-none" tabIndex={-1}>
          <Outlet />
        </main>

        <footer className="border-t border-white/[0.06] px-4 py-2.5 text-center text-[10px] text-terminal-muted/85 md:px-6">
          Market Analytics Terminal · Bronze / Silver / Gold lakehouse · Kafka · Airflow · Lightweight Charts™
        </footer>
      </div>
      </div>
    </div>
  )
}
