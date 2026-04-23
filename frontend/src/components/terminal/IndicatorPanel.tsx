import { TrendingUp, Activity, BarChart3, Zap } from "lucide-react";
import { Sparkline } from "./Sparkline";
import { cn } from "@/lib/utils";
import { ASSETS } from "@/lib/market-data";

const INDICATORS = [
  { label: "Returns 24h",   value: "+2.84%", trend: "up",   icon: TrendingUp, accent: "text-bull" },
  { label: "MA7 / MA30",    value: "↑ cross", trend: "up",  icon: Activity,   accent: "text-bull" },
  { label: "Volatility 7d", value: "1.42σ",  trend: "up",   icon: BarChart3,  accent: "text-metals" },
  { label: "Δ Price 1h",    value: "+118.2", trend: "up",   icon: Zap,        accent: "text-bull" },
];

export const IndicatorPanel = () => {
  const spark = ASSETS[0].spark;
  return (
    <div className="terminal-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-[13px] font-semibold tracking-tight">Technical indicators</h3>
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">BTC/USD · feature engineering · gold layer</p>
        </div>
        <span className="mono rounded bg-bull/10 px-1.5 py-0.5 text-[10px] font-medium text-bull">3 / 4 bullish</span>
      </div>
      <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
        {INDICATORS.map((i) => {
          const Icon = i.icon;
          return (
            <div key={i.label} className="rounded-lg border border-border bg-surface-2/60 p-3">
              <div className="flex items-center justify-between">
                <span className="mono text-[10px] uppercase tracking-wider text-muted-foreground">{i.label}</span>
                <Icon className={cn("h-3.5 w-3.5", i.accent)} />
              </div>
              <p className={cn("mono mt-1 text-[16px] font-semibold tabular-nums", i.accent)}>{i.value}</p>
              <div className="mt-1.5 h-6">
                <Sparkline data={spark} color={i.accent.includes("bull") ? "hsl(var(--bull))" : "hsl(var(--metals))"} height={24} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
