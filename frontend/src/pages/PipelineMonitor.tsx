import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { PIPELINE_LAST_REFRESH } from '../data/mock'
import { useData } from '../context/DataContext'

function fmtRows(n: number | null | undefined) {
  if (n == null) return '—'
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`
  return String(n)
}

function StatusIcon({ exists }: { exists: boolean }) {
  if (exists) {
    return (
      <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-up/20">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-up">
          <path d="M20 6 9 17l-5-5" />
        </svg>
      </span>
    )
  }
  return (
    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-down/20">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-down">
        <path d="M18 6 6 18M6 6l12 12" />
      </svg>
    </span>
  )
}

function LayerBadge({ title }: { title: 'Bronze' | 'Silver' | 'Gold' }) {
  const cls = {
    Bronze: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
    Silver: 'border-slate-400/30 bg-slate-400/10 text-slate-300',
    Gold:   'border-brand/30 bg-brand/10 text-brand',
  }[title]
  return (
    <span className={`rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide ${cls}`}>
      {title}
    </span>
  )
}

function layerOf(id: string): 'Bronze' | 'Silver' | 'Gold' {
  if (id.startsWith('silver')) return 'Silver'
  if (id.startsWith('gold'))   return 'Gold'
  return 'Bronze'
}

export function PipelineMonitor() {
  const { pipeline, refresh, source, loadError } = useData()
  const files = pipeline?.files ?? []

  const layerGroups = [
    { title: 'Bronze' as const, prefix: 'bronze' },
    { title: 'Silver' as const, prefix: 'silver' },
    { title: 'Gold'   as const, prefix: 'gold' },
  ]

  const lastRefresh = pipeline?.last_refresh ?? PIPELINE_LAST_REFRESH

  const totalExisting = files.filter((f) => f.exists).length
  const healthPct = files.length ? Math.round((totalExisting / files.length) * 100) : 0

  return (
    <PageLayout className="page-enter">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 animate-fade-up">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-terminal-muted">Pipeline Monitor</p>
          <h1 className="mt-1 text-2xl font-bold text-terminal-text">Data engineering</h1>
          <p className="mt-1 text-[12px] text-terminal-muted">Bronze → Silver → Gold lakehouse health</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void refresh()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-terminal-border bg-terminal-surface px-3 py-1.5 text-sm text-accent transition hover:bg-terminal-elevated hover:border-accent/40"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
            Refresh
          </button>
          <Link to="/" className="text-sm text-accent hover:underline">← Dashboard</Link>
        </div>
      </div>

      {loadError && (
        <p className="mb-4 animate-fade-up rounded-lg border border-amber-500/35 bg-amber-500/10 px-3 py-2 text-sm text-terminal-text">
          API: {loadError} (showing cached or empty pipeline metadata).
        </p>
      )}

      {/* KPI cards */}
      <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 animate-fade-up delay-75">
        {[
          {
            label: 'Dashboard data',
            value: source === 'live' ? 'Live Parquet' : 'Mock / offline',
            sub: source === 'live' ? 'healthy' : 'fallback',
          },
          {
            label: 'Parquet health',
            value: `${healthPct}%`,
            sub: `${totalExisting}/${files.length} files present`,
          },
          {
            label: 'API generated',
            value: pipeline?.generated_at?.slice(11, 19) ?? '—',
            sub: 'UTC clock',
          },
          {
            label: 'Gold refresh (mtime)',
            value: lastRefresh.slice(11, 19) + 'Z',
            sub: 'market_features',
          },
        ].map((c, i) => (
          <div
            key={c.label}
            className={`animate-scale-in delay-${i * 75} rounded-xl border border-terminal-border bg-terminal-surface p-4`}
          >
            <p className="text-[10px] font-bold uppercase text-terminal-muted">{c.label}</p>
            <p className="mt-1 font-mono text-sm text-terminal-text">{c.value}</p>
            <p
              className={
                c.sub === 'healthy' ? 'text-[11px] text-up'
                : c.sub === 'fallback' ? 'text-[11px] text-amber-400'
                : 'text-[11px] text-terminal-muted'
              }
            >
              {c.sub}
            </p>
          </div>
        ))}
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        {/* Layer summary + file table */}
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 lg:col-span-2 animate-fade-up delay-150">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">Lakehouse layers</h2>

          {/* Layer cards */}
          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            {layerGroups.map((lg, i) => {
              const layerFiles = files.filter((f) => f.id.startsWith(lg.prefix))
              const ok = layerFiles.filter((f) => f.exists).length
              const totalRows = layerFiles.reduce((s, f) => s + (f.rows ?? 0), 0)
              const health = layerFiles.length ? (ok / layerFiles.length) * 100 : 0
              return (
                <div key={lg.title} className={`animate-scale-in delay-${i * 100 + 200} rounded-lg border border-terminal-border bg-terminal-elevated/40 p-3`}>
                  <div className="mb-2 flex items-center justify-between">
                    <LayerBadge title={lg.title} />
                    <span className={`font-mono text-[10px] ${ok === layerFiles.length && layerFiles.length > 0 ? 'text-up' : 'text-terminal-muted'}`}>
                      {ok}/{layerFiles.length}
                    </span>
                  </div>
                  <p className="font-mono text-lg font-bold text-terminal-text">{fmtRows(totalRows || null)}</p>
                  <p className="text-[10px] text-terminal-muted">rows</p>
                  {/* Health bar */}
                  <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-terminal-bg">
                    <div
                      className={`h-full animate-bar-grow rounded-full ${health === 100 ? 'bg-up' : health > 0 ? 'bg-amber-400' : 'bg-terminal-muted'}`}
                      style={{ width: `${health}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>

          {/* File table */}
          {files.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[11px]">
                <thead>
                  <tr className="border-b border-terminal-border text-terminal-muted">
                    <th className="py-2 pr-2">Layer</th>
                    <th className="py-2 pr-2">Rows</th>
                    <th className="py-2 pr-2">mtime (UTC)</th>
                    <th className="py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((f) => (
                    <tr key={f.id} className="border-b border-terminal-border/50 font-mono hover:bg-terminal-elevated/20">
                      <td className="py-1.5 pr-2 text-terminal-text">{f.id}</td>
                      <td className="py-1.5 pr-2">{fmtRows(f.rows)}</td>
                      <td className="py-1.5 pr-2 text-terminal-muted">
                        {f.mtime ? f.mtime.slice(0, 19).replace('T', ' ') : '—'}
                      </td>
                      <td className="py-1.5">
                        <StatusIcon exists={f.exists} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex items-center justify-center py-10 text-center">
              <div>
                <p className="text-[13px] font-semibold text-terminal-text">No pipeline data</p>
                <p className="mt-1 text-[11px] text-terminal-muted">
                  Start the API server to see Parquet file health.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Notes */}
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 animate-fade-up delay-225">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">Quick start</h2>
          <ul className="space-y-3 text-[12px] text-terminal-muted">
            <li className="rounded-lg border border-terminal-border/60 bg-terminal-elevated/30 p-3">
              <p className="font-semibold text-terminal-text">1 · Run API server</p>
              <p className="mt-1 font-mono text-[10px]">cd backend && python scripts/run_dashboard_api.py</p>
            </li>
            <li className="rounded-lg border border-terminal-border/60 bg-terminal-elevated/30 p-3">
              <p className="font-semibold text-terminal-text">2 · Run ingestion</p>
              <p className="mt-1 font-mono text-[10px]">python -m app.ingestion.batch.run_batch_ingestion</p>
            </li>
            <li className="rounded-lg border border-terminal-border/60 bg-terminal-elevated/30 p-3">
              <p className="font-semibold text-terminal-text">3 · Run ETL</p>
              <p className="mt-1 font-mono text-[10px]">Silver → Gold (or trigger Airflow DAG)</p>
            </li>
            <li className="rounded-lg border border-terminal-border/60 bg-terminal-elevated/30 p-3">
              <p className="font-semibold text-terminal-text">4 · Stream (optional)</p>
              <p className="mt-1 font-mono text-[10px]">Start Binance producer + Kafka consumer</p>
            </li>
          </ul>
          <p className="mt-4 text-[10px] text-terminal-muted">
            Row counts from DuckDB <span className="font-mono">COUNT(*)</span> on each Parquet path.
          </p>
        </div>
      </div>
    </PageLayout>
  )
}
