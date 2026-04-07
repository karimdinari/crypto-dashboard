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

export function PipelineMonitor() {
  const { pipeline, refresh, source, loadError } = useData()
  const files = pipeline?.files ?? []

  const layerGroups = [
    { title: 'Bronze', prefix: 'bronze' },
    { title: 'Silver', prefix: 'silver' },
    { title: 'Gold', prefix: 'gold' },
  ]

  const lastRefresh = pipeline?.last_refresh ?? PIPELINE_LAST_REFRESH

  return (
    <PageLayout>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-terminal-muted">
            Pipeline Monitor
          </p>
          <h1 className="mt-1 text-2xl font-bold text-terminal-text">
            Data engineering
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void refresh()}
            className="rounded-lg border border-terminal-border bg-terminal-surface px-3 py-1.5 text-sm text-accent hover:bg-terminal-elevated"
          >
            Refresh
          </button>
          <Link to="/" className="text-sm text-accent hover:underline">
            ← Market Terminal
          </Link>
        </div>
      </div>

      {loadError && (
        <p className="mb-4 rounded-lg border border-amber-500/35 bg-amber-500/10 px-3 py-2 text-sm text-terminal-text">
          API: {loadError} (showing cached or empty pipeline metadata).
        </p>
      )}

      <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: 'Dashboard data',
            value: source === 'live' ? 'Live Parquet' : 'Mock / offline',
            sub: source === 'live' ? 'healthy' : 'fallback',
          },
          {
            label: 'Parquet layers',
            value: String(files.filter((f) => f.exists).length),
            sub: `${files.length} paths tracked`,
          },
          {
            label: 'API generated',
            value: pipeline?.generated_at?.slice(11, 19) ?? '—',
            sub: 'UTC clock',
          },
          {
            label: 'Gold refresh (file mtime)',
            value: lastRefresh.slice(11, 19) + 'Z',
            sub: 'market_features',
          },
        ].map((c) => (
          <div
            key={c.label}
            className="rounded-xl border border-terminal-border bg-terminal-surface p-4"
          >
            <p className="text-[10px] font-bold uppercase text-terminal-muted">
              {c.label}
            </p>
            <p className="mt-1 font-mono text-sm text-terminal-text">{c.value}</p>
            <p
              className={
                c.sub === 'healthy' || c.sub === 'fallback'
                  ? c.sub === 'healthy'
                    ? 'text-[11px] text-up'
                    : 'text-[11px] text-amber-400'
                  : 'text-[11px] text-terminal-muted'
              }
            >
              {c.sub}
            </p>
          </div>
        ))}
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4 lg:col-span-2">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Lakehouse files (row counts)
          </h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {layerGroups.map((lg) => {
              const layerFiles = files.filter((f) => f.id.startsWith(lg.prefix))
              const totalRows = layerFiles.reduce((s, f) => s + (f.rows ?? 0), 0)
              return (
                <div
                  key={lg.title}
                  className="rounded-lg border border-terminal-border bg-terminal-elevated/40 p-3"
                >
                  <p className="text-[10px] text-terminal-muted">{lg.title}</p>
                  <p className="font-mono text-lg text-terminal-text">
                    {fmtRows(totalRows || null)}
                  </p>
                  <p className="text-[10px] text-terminal-muted">
                    {layerFiles.filter((f) => f.exists).length}/{layerFiles.length}{' '}
                    files present
                  </p>
                </div>
              )
            })}
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-[11px]">
              <thead>
                <tr className="border-b border-terminal-border text-terminal-muted">
                  <th className="py-2 pr-2">Layer</th>
                  <th className="py-2 pr-2">Rows</th>
                  <th className="py-2 pr-2">mtime (UTC)</th>
                  <th className="py-2">OK</th>
                </tr>
              </thead>
              <tbody>
                {files.map((f) => (
                  <tr
                    key={f.id}
                    className="border-b border-terminal-border/50 font-mono"
                  >
                    <td className="py-1.5 pr-2 text-terminal-text">{f.id}</td>
                    <td className="py-1.5 pr-2">{fmtRows(f.rows)}</td>
                    <td className="py-1.5 pr-2 text-terminal-muted">
                      {f.mtime ? f.mtime.slice(0, 19).replace('T', ' ') : '—'}
                    </td>
                    <td className="py-1.5">
                      {f.exists ? (
                        <span className="text-up">yes</span>
                      ) : (
                        <span className="text-down">no</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="rounded-xl border border-terminal-border bg-terminal-surface p-4">
          <h2 className="mb-3 text-xs font-bold uppercase text-terminal-muted">
            Notes
          </h2>
          <ul className="space-y-2 text-xs text-terminal-muted">
            <li>
              Run <span className="font-mono text-terminal-text">python scripts/run_dashboard_api.py</span>{' '}
              from <span className="font-mono">backend/</span> while using{' '}
              <span className="font-mono">npm run dev</span> (Vite proxies{' '}
              <span className="font-mono">/api</span>).
            </li>
            <li>
              Streaming ticks: <span className="font-mono">GET /api/stream/latest</span>{' '}
              (optional Kafka Bronze).
            </li>
          </ul>
        </div>
      </div>

      <p className="text-center text-[11px] text-terminal-muted">
        Row counts come from DuckDB <span className="font-mono">COUNT(*)</span> on each Parquet path.
      </p>
    </PageLayout>
  )
}
