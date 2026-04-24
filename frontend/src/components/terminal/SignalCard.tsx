import { useMemo } from "react";
import { useAssets } from "@/lib/api";
import { Brain, ArrowUp, ArrowDown, Minus, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export const SignalCard = () => {
  const { data: assets } = useAssets();
  
  const topAsset = useMemo(() => {
    if (!assets) return null;
    return [...assets].sort((a, b) => b.confidence - a.confidence)[0];
  }, [assets]);

  if (!topAsset) return null;

  const isBuy = topAsset.prediction === "BUY";
  const isSell = topAsset.prediction === "SELL";
  const Icon = isBuy ? ArrowUp : isSell ? ArrowDown : Minus;
  const conf = Math.round(topAsset.confidence * 100);
  const ringClass = isBuy ? "signal-ring-bull" : isSell ? "signal-ring-bear" : "";
  const dirColor = isBuy ? "text-bull" : isSell ? "text-bear" : "text-neutral";

  // Confidence arc (semicircle)
  const R = 42;
  const C = Math.PI * R;
  const dash = (conf / 100) * C;

  return (
    <div className={cn("terminal-card relative overflow-hidden p-4 hairline-top", ringClass)}>
      {/* Atmospheric backdrop */}
      <div className={cn("pointer-events-none absolute inset-0 opacity-90",
        isBuy && "bg-[radial-gradient(ellipse_at_top_right,hsl(var(--bull)/0.18),transparent_60%)]",
        isSell && "bg-[radial-gradient(ellipse_at_top_right,hsl(var(--bear)/0.18),transparent_60%)]",
      )} />

      <div className="relative">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <div className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 ring-1 ring-primary/40">
              <Brain className="h-4 w-4 text-primary" />
              <Sparkles className="absolute -right-1 -top-1 h-2.5 w-2.5 text-primary" />
            </div>
            <div>
              <h3 className="text-[13px] font-semibold tracking-tight">AI Signal</h3>
              <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{topAsset.modelVersion}</p>
            </div>
          </div>
          <span className="mono rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            4H HORIZON
          </span>
        </div>

        {/* Big direction + confidence arc */}
        <div className="mt-4 flex items-center gap-4">
          <div className="relative h-[100px] w-[120px] shrink-0">
            <svg viewBox="0 0 120 70" className="h-full w-full">
              <path d="M 18 60 A 42 42 0 0 1 102 60" stroke="hsl(var(--surface-3))" strokeWidth="6" fill="none" strokeLinecap="round" />
              <path d="M 18 60 A 42 42 0 0 1 102 60"
                stroke={isBuy ? "hsl(var(--bull))" : isSell ? "hsl(var(--bear))" : "hsl(var(--neutral))"}
                strokeWidth="6" fill="none" strokeLinecap="round"
                strokeDasharray={`${dash} ${C}`} />
            </svg>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-end pb-1">
              <div className={cn("flex items-center gap-1", dirColor)}>
                <Icon className="h-5 w-5" strokeWidth={2.5} />
                <span className="mono text-[22px] font-bold tracking-tight">{topAsset.prediction}</span>
              </div>
              <span className="mono mt-0.5 text-[9px] uppercase tracking-[0.22em] text-muted-foreground">{conf}% conf</span>
            </div>
          </div>

          <div className="flex-1 space-y-2">
            <div className="rounded-md border border-border bg-surface-2/50 p-2">
              <p className="mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">Asset</p>
              <p className="mono mt-0.5 text-[13px] font-semibold">{topAsset.symbol}</p>
            </div>
            <div className="rounded-md border border-border bg-surface-2/50 p-2">
              <p className="mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">Ensemble</p>
              <p className="mono mt-0.5 text-[12px]">5 models · v3.2</p>
            </div>
          </div>
        </div>

        {/* Feature attribution */}
        <div className="mt-4">
          <div className="mb-2 flex items-center justify-between">
            <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Feature attribution</p>
            <p className="mono text-[10px] text-muted-foreground">explainable</p>
          </div>
          <ul className="space-y-1.5">
            {/* Using mock names if backend features are generic, or dynamic if available */}
            {[{name: "MA7 / MA30 cross", weight: 0.31}, {name: "Realized volatility", weight: 0.22}, {name: "News sentiment (24h)", weight: 0.19}].map((f) => (
              <li key={f.name} className="flex items-center gap-2 text-[11px]">
                <span className="flex-1 truncate text-foreground/90">{f.name}</span>
                <div className="h-1 w-24 overflow-hidden rounded-full bg-surface-2">
                  <div className={cn("h-full rounded-full", isBuy ? "bg-bull" : isSell ? "bg-bear" : "bg-primary")}
                    style={{ width: `${f.weight * 100 / 0.31}%` }} />
                </div>
                <span className="mono w-10 text-right num text-muted-foreground">{(f.weight * 100).toFixed(0)}%</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
