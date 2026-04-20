import { Link } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { useData } from '../context/DataContext'

function formatTs(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return iso
  }
}

function latency(ts: string, ingestion: string): string {
  try {
    const ms = new Date(ingestion).getTime() - new Date(ts).getTime()
    if (ms < 0) return '—'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  } catch {
    return '—'
  }
}

export function StreamingHub() {
  const { kafkaStreamTicks, kafkaStreamUpdatedAt, source } = useData()

  const live = kafkaStreamTicks.length > 0

  return (
    <PageLayout className="max-w-[1800px] page-enter">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div className="animate-fade-up">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-terminal-muted">Real-time</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-terminal-text md:text-3xl">
            Kafka streaming
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-terminal-muted">
            Latest ticks persisted to Bronze (<span className="font-mono">market_stream</span>) and
            exposed via <span className="font-mono">GET /api/stream/latest</span>. Pair with Airflow
            batch layers for a full hybrid architecture.
          </p>
        </div>
        <Link
          to="/pipeline"
          className="animate-slide-right rounded-lg border border-terminal-border bg-terminal-elevated px-3 py-2 text-[12px] font-medium text-accent hover:border-accent/40"
        >
          Pipeline layers →
        </Link>
      </div>

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <div className={`glass-panel animate-fade-up rounded-xl border p-4 ${live ? 'border-up/30' : 'border-terminal-border/80'}`}>
          <p className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">Stream state</p>
          <p className={`mt-1 flex items-center gap-2 text-lg font-semibold ${live ? 'text-up' : 'text-terminal-muted'}`}>
            {live && <span className="inline-block h-2 w-2 rounded-full bg-up animate-pulse shadow-[0_0_8px_rgba(62,232,176,0.7)]" />}
            {live ? 'Receiving ticks' : 'Idle / offline'}
          </p>
          <p className="mt-1 text-[11px] text-terminal-muted">
            UI poll · 5s · {source === 'live' ? 'API up' : 'mock assets'}
          </p>
        </div>
        <div className="glass-panel animate-fade-up delay-75 rounded-xl border border-terminal-border/80 p-4 sm:col-span-2">
          <p className="text-[10px] font-bold uppercase tracking-wide text-terminal-muted">Last consumer write</p>
          <p className="mt-1 font-mono text-sm text-terminal-text">
            {kafkaStreamUpdatedAt ? formatTs(kafkaStreamUpdatedAt) : '—'}
          </p>
          <p className="mt-1 text-[11px] text-terminal-muted">
            Timestamp reflects when the dashboard last successfully polled the stream endpoint.
          </p>
        </div>
      </div>

      <div className="glass-panel animate-fade-up delay-150 overflow-hidden rounded-xl border border-terminal-border/80">
        <div className="border-b border-terminal-border/60 bg-terminal-elevated/40 px-4 py-3 flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wide text-terminal-muted">Live tick log</h2>
          {live && (
            <span className="flex items-center gap-1.5 rounded-full border border-up/30 bg-up/10 px-2.5 py-1 text-[11px] font-semibold text-up">
              <span className="h-1.5 w-1.5 rounded-full bg-up animate-pulse" />
              {kafkaStreamTicks.length} ticks
            </span>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-[12px]">
            <thead className="border-b border-terminal-border/60 text-terminal-muted">
              <tr>
                <th className="px-4 py-2.5 font-medium">Symbol</th>
                <th className="px-4 py-2.5 font-medium">Price</th>
                <th className="px-4 py-2.5 font-medium">Market</th>
                <th className="px-4 py-2.5 font-medium">Source</th>
                <th className="px-4 py-2.5 font-medium">Event time</th>
                <th className="px-4 py-2.5 font-medium">Latency</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {kafkaStreamTicks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-16 text-center">
                    <div className="flex flex-col items-center gap-4">
                      {/* Animated Kafka icon */}
                      <div className="relative flex h-16 w-16 items-center justify-center">
                        <span className="absolute h-16 w-16 rounded-full border-2 border-accent/20 animate-ping" />
                        <span className="absolute h-10 w-10 rounded-full border border-accent/30 animate-ping animation-delay-300" />
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-terminal-muted">
                          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-[13px] font-semibold text-terminal-text">Waiting for stream data</p>
                        <p className="mt-1 text-[11px] text-terminal-muted">
                          Start Kafka producer/consumer and ensure{' '}
                          <span className="text-terminal-text">/api/stream/latest</span> returns data.
                        </p>
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                kafkaStreamTicks.map((t, i) => (
                  <tr
                    key={`${t.symbol}-${t.timestamp}`}
                    className={`animate-row-in border-b border-terminal-border/40 transition hover:bg-terminal-elevated/30 delay-${Math.min(i * 30, 300)}`}
                  >
                    <td className="px-4 py-2 font-semibold text-terminal-text">{t.symbol}</td>
                    <td className="px-4 py-2 text-accent">
                      {t.price > 100
                        ? t.price.toLocaleString(undefined, { maximumFractionDigits: 2 })
                        : t.price.toFixed(4)}
                    </td>
                    <td className="px-4 py-2 text-terminal-muted">{t.market_type}</td>
                    <td className="px-4 py-2 text-forex/90">{t.source}</td>
                    <td className="px-4 py-2 text-terminal-muted">{formatTs(t.timestamp)}</td>
                    <td className="px-4 py-2 text-terminal-muted">{latency(t.timestamp, t.ingestion_time)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </PageLayout>
  )
}
