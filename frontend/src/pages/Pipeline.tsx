import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { PIPELINE_TASKS } from "@/lib/market-data";
import { cn } from "@/lib/utils";
import { Database, GitBranch, Zap, ArrowRight, CircleCheck, CircleAlert, Radio, Workflow } from "lucide-react";

const TIERS = [
  { key: "Bronze", icon: Database, accent: "text-bronze",  ring: "ring-bronze/30",  bg: "bg-bronze/10",  desc: "Raw ingestion" },
  { key: "Silver", icon: GitBranch, accent: "text-silver", ring: "ring-silver/30", bg: "bg-silver/10",  desc: "Cleaned + features" },
  { key: "Gold",   icon: Zap,      accent: "text-gold",    ring: "ring-gold/30",   bg: "bg-gold/10",    desc: "Marts + signals" },
];

const Pipeline = () => {
  return (
    <TerminalLayout>
      <div className="space-y-4">
        <header className="flex items-end justify-between">
          <div>
            <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Workspace</p>
            <h1 className="text-[22px] font-semibold tracking-tight">Pipeline Monitoring</h1>
          </div>
          <div className="flex items-center gap-2 mono text-[11px]">
            <span className="rounded border border-border bg-surface px-2 py-1 text-muted-foreground">Airflow · v2.9</span>
            <span className="rounded border border-border bg-surface px-2 py-1 text-muted-foreground">Kafka · 3 brokers</span>
            <span className="flex items-center gap-1.5 rounded border border-bull/30 bg-bull/10 px-2 py-1 font-medium text-bull">
              <span className="pulse-dot bg-bull" /> all systems nominal
            </span>
          </div>
        </header>

        {/* Lakehouse flow */}
        <div className="terminal-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <Workflow className="h-4 w-4 text-primary" />
            <h3 className="text-[13px] font-semibold tracking-tight">Lakehouse flow</h3>
            <span className="mono ml-auto text-[10px] uppercase tracking-wider text-muted-foreground">Bronze → Silver → Gold</span>
          </div>
          <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center">
            {TIERS.map((t, idx) => {
              const Icon = t.icon;
              const tasks = PIPELINE_TASKS.filter((x) => x.layer === t.key);
              const ok = tasks.filter((x) => x.status === "ok").length;
              return (
                <div key={t.key} className="flex flex-1 items-center gap-3">
                  <div className={cn("flex-1 rounded-xl border border-border p-4", t.bg)}>
                    <div className="flex items-center gap-2.5">
                      <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg bg-background ring-1", t.ring)}>
                        <Icon className={cn("h-4 w-4", t.accent)} />
                      </div>
                      <div>
                        <p className={cn("text-[13px] font-semibold", t.accent)}>{t.key}</p>
                        <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">{t.desc}</p>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-[11px]">
                      <span className="mono text-muted-foreground">{tasks.length} tasks</span>
                      <span className="mono font-medium text-bull">{ok}/{tasks.length} healthy</span>
                    </div>
                    <div className="mt-1.5 h-1 rounded-full bg-background/60 overflow-hidden">
                      <div className={cn("h-full rounded-full", t.accent.replace("text-", "bg-"))} style={{ width: `${(ok / tasks.length) * 100}%` }} />
                    </div>
                  </div>
                  {idx < TIERS.length - 1 && (
                    <ArrowRight className="hidden h-5 w-5 shrink-0 text-muted-foreground md:block" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Health cards */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Health title="Airflow DAG" value="market_pipeline_v3" status="success" sub="next run · 04m" />
          <Health title="Kafka throughput" value="2.4k msg/s" status="success" sub="lag · 12 ms" />
          <Health title="News ingestor" value="ingest_news_rss" status="warn" sub="retry 1/3 · 11m late" />
          <Health title="Model serving" value="lgbm-v3.2" status="success" sub="p99 · 38 ms" />
        </div>

        {/* Tasks table */}
        <div className="terminal-card overflow-hidden">
          <div className="border-b border-border px-4 py-3 flex items-center gap-2">
            <Radio className="h-3.5 w-3.5 text-primary" />
            <h3 className="text-[13px] font-semibold tracking-tight">Task health</h3>
            <span className="mono ml-auto text-[10px] uppercase tracking-wider text-muted-foreground">{PIPELINE_TASKS.length} tasks</span>
          </div>
          <table className="mono w-full text-[11px]">
            <thead>
              <tr className="text-[9px] uppercase tracking-wider text-muted-foreground">
                <th className="px-4 py-2 text-left">Task</th>
                <th className="px-2 py-2 text-left">Layer</th>
                <th className="px-2 py-2 text-left">Type</th>
                <th className="px-2 py-2 text-left">Status</th>
                <th className="px-2 py-2 text-right">Last run</th>
                <th className="px-4 py-2 text-right">Duration</th>
              </tr>
            </thead>
            <tbody>
              {PIPELINE_TASKS.map((t) => (
                <tr key={t.id} className="border-t border-border/50 transition-colors hover:bg-surface-2/40">
                  <td className="px-4 py-2 font-medium text-foreground">{t.id}</td>
                  <td className={cn("px-2 py-2 font-semibold",
                    t.layer === "Bronze" && "text-bronze",
                    t.layer === "Silver" && "text-silver",
                    t.layer === "Gold" && "text-gold")}>{t.layer}</td>
                  <td className="px-2 py-2 text-muted-foreground">{t.type}</td>
                  <td className="px-2 py-2">
                    {t.status === "ok" ? (
                      <span className="inline-flex items-center gap-1 rounded bg-bull/10 px-1.5 py-0.5 text-bull">
                        <CircleCheck className="h-3 w-3" /> ok
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded bg-metals/15 px-1.5 py-0.5 text-metals">
                        <CircleAlert className="h-3 w-3" /> warn
                      </span>
                    )}
                  </td>
                  <td className="px-2 py-2 text-right text-muted-foreground tabular-nums">{t.lastRun}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{t.duration}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </TerminalLayout>
  );
};

const Health = ({ title, value, status, sub }: { title: string; value: string; status: "success" | "warn"; sub: string }) => (
  <div className="terminal-card p-4">
    <div className="flex items-center justify-between">
      <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">{title}</p>
      <span className={cn("mono rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase",
        status === "success" ? "bg-bull/10 text-bull" : "bg-metals/15 text-metals")}>
        {status === "success" ? "healthy" : "degraded"}
      </span>
    </div>
    <p className="mono mt-2 text-[16px] font-semibold tabular-nums text-foreground">{value}</p>
    <p className="mono mt-1 text-[10px] uppercase tracking-wider text-muted-foreground">{sub}</p>
  </div>
);

export default Pipeline;
