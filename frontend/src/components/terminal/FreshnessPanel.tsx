import { Database, GitBranch, Zap, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

const TIERS = [
  { key: "Bronze", icon: Database, color: "bg-bronze",  textColor: "text-bronze",  count: "4 sources",  freshness: "12s",  load: 84 },
  { key: "Silver", icon: GitBranch, color: "bg-silver", textColor: "text-silver",  count: "8 transforms", freshness: "2m",  load: 62 },
  { key: "Gold",   icon: Zap,      color: "bg-gold",    textColor: "text-gold",    count: "5 marts",   freshness: "5m",  load: 41 },
];

export const FreshnessPanel = () => {
  return (
    <div className="terminal-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-[13px] font-semibold tracking-tight">Data freshness</h3>
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">Lakehouse · batch + streaming</p>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] font-medium text-bull">
          <Clock className="h-3 w-3" /> on schedule
        </span>
      </div>

      <div className="space-y-2">
        {TIERS.map((t) => {
          const Icon = t.icon;
          return (
            <div key={t.key} className="rounded-lg border border-border bg-surface-2/40 p-3">
              <div className="flex items-center gap-3">
                <div className={cn("flex h-8 w-8 items-center justify-center rounded-md", t.color, "bg-opacity-15")}>
                  <Icon className={cn("h-4 w-4", t.textColor)} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className={cn("text-[12px] font-semibold", t.textColor)}>{t.key}</span>
                    <span className="mono text-[11px] tabular-nums text-foreground">{t.freshness}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-2">
                    <div className="h-1 flex-1 overflow-hidden rounded-full bg-surface-3">
                      <div className={cn("h-full rounded-full", t.color)} style={{ width: `${t.load}%` }} />
                    </div>
                    <span className="mono w-[68px] text-right text-[10px] uppercase tracking-wider text-muted-foreground">{t.count}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
