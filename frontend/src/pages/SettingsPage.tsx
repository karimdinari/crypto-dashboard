import { PageLayout } from '../components/PageLayout'
import { useTheme } from '../context/ThemeContext'
import { useData } from '../context/DataContext'

export function SettingsPage() {
  const { theme, toggleTheme } = useTheme()
  const { source, loadError, refresh } = useData()

  return (
    <PageLayout className="max-w-3xl">
      <div className="mb-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-terminal-muted">
          Workspace
        </p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-terminal-text">Settings</h1>
        <p className="mt-2 text-sm text-terminal-muted">
          Appearance and connection status for the Market Analytics Terminal frontend.
        </p>
      </div>

      <div className="space-y-4">
        <div className="glass-panel rounded-xl border border-terminal-border/80 p-4">
          <h2 className="text-xs font-bold uppercase tracking-wide text-terminal-muted">Appearance</h2>
          <p className="mt-1 text-[13px] text-terminal-muted">
            Dark terminal is the default; light mode is available for presentations.
          </p>
          <button
            type="button"
            onClick={toggleTheme}
            className="mt-4 rounded-lg border border-terminal-border bg-terminal-elevated px-4 py-2 text-[13px] font-medium text-terminal-text transition hover:border-accent/40"
          >
            Switch to {theme === 'dark' ? 'light' : 'dark'} theme
          </button>
        </div>

        <div className="glass-panel rounded-xl border border-terminal-border/80 p-4">
          <h2 className="text-xs font-bold uppercase tracking-wide text-terminal-muted">API</h2>
          <dl className="mt-3 space-y-2 text-[13px]">
            <div className="flex justify-between gap-4 border-b border-terminal-border/50 py-2">
              <dt className="text-terminal-muted">Data source</dt>
              <dd className="font-mono text-terminal-text">{source === 'live' ? 'live Parquet API' : 'mock'}</dd>
            </div>
            <div className="flex justify-between gap-4 py-2">
              <dt className="text-terminal-muted">Last error</dt>
              <dd className="max-w-[60%] text-right font-mono text-[12px] text-terminal-text">
                {loadError ?? '—'}
              </dd>
            </div>
          </dl>
          <button
            type="button"
            onClick={() => void refresh()}
            className="mt-4 rounded-lg border border-accent/35 bg-accent/10 px-4 py-2 text-[13px] font-semibold text-accent hover:bg-accent/20"
          >
            Re-fetch assets & pipeline
          </button>
        </div>
      </div>
    </PageLayout>
  )
}
