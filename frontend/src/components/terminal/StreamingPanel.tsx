import { TICKS } from "@/lib/market-data";
import { cn } from "@/lib/utils";
import { Radio } from "lucide-react";

export const StreamingPanel = () => {
  return (
    <div className="terminal-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Radio className="h-3.5 w-3.5 text-primary" />
          <h3 className="text-[13px] font-semibold tracking-tight">Live ticks · Kafka</h3>
          <span className="mono rounded bg-primary/10 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider text-primary">market.ticks.v1</span>
        </div>
        <div className="flex items-center gap-3 text-[11px]">
          <span className="mono text-muted-foreground">~ <span className="text-foreground">2.4k</span>/s</span>
          <span className="flex items-center gap-1 font-medium text-bull">
            <span className="pulse-dot bg-bull" /> consuming
          </span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="mono w-full text-[11px]">
          <thead>
            <tr className="text-[9px] uppercase tracking-wider text-muted-foreground">
              <th className="px-4 py-2 text-left font-medium">Time</th>
              <th className="px-3 py-2 text-left font-medium">Symbol</th>
              <th className="px-3 py-2 text-left font-medium">Venue</th>
              <th className="px-3 py-2 text-right font-medium">Price</th>
              <th className="px-3 py-2 text-right font-medium">Δ%</th>
              <th className="px-4 py-2 text-right font-medium">Topic</th>
            </tr>
          </thead>
          <tbody>
            {TICKS.map((t, i) => {
              const up = t.delta >= 0;
              return (
                <tr key={t.id} className={cn("border-t border-border/50", i === 0 && "bg-primary/5")}>
                  <td className="px-4 py-1.5 text-muted-foreground">{t.ts}</td>
                  <td className="px-3 py-1.5">
                    <span className="inline-flex items-center gap-1.5">
                      <span className={cn("h-1.5 w-1.5 rounded-full",
                        t.class === "crypto" && "bg-crypto",
                        t.class === "forex" && "bg-forex",
                        t.class === "metals" && "bg-metals")} />
                      <span className="font-medium text-foreground">{t.symbol}</span>
                    </span>
                  </td>
                  <td className="px-3 py-1.5 text-muted-foreground">{t.venue}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{t.price}</td>
                  <td className={cn("px-3 py-1.5 text-right tabular-nums font-medium", up ? "text-bull" : "text-bear")}>
                    {up ? "+" : ""}{t.delta.toFixed(3)}
                  </td>
                  <td className="px-4 py-1.5 text-right text-muted-foreground">market.{t.class}.{t.symbol.toLowerCase().replace("/", "")}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
