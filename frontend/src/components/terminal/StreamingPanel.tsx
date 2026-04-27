import { useLatestStream } from "@/lib/api";
import { cn } from "@/lib/utils";
import { AssetImage } from "@/components/AssetImage";
import { Radio } from "lucide-react";

export const StreamingPanel = () => {
  const { data: latestStream } = useLatestStream();

  return (
    <div className="terminal-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Radio className="h-3.5 w-3.5 text-primary" />
          <h3 className="text-[13px] font-semibold tracking-tight">Live ticks</h3>
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
              <th className="px-4 py-2 text-right font-medium">Type</th>
            </tr>
          </thead>
          <tbody>
            {latestStream?.map((t, i) => {
              const marketClass = (t.market_type?.toLowerCase() || "crypto") as "crypto" | "forex" | "metals";
              const formattedTime = new Date(t.timestamp).toLocaleTimeString();
              return (
                <tr key={`${t.symbol}-${t.timestamp}`} className={cn("border-t border-border/50", i === 0 && "bg-primary/5")}>
                  <td className="px-4 py-1.5 text-muted-foreground">{formattedTime}</td>
                  <td className="px-3 py-1.5">
                    <span className="inline-flex items-center gap-1.5">
                      <AssetImage symbol={t.symbol} size="xs" showBorder={false} />
                      <span className="font-medium text-foreground">{t.symbol}</span>
                    </span>
                  </td>
                  <td className="px-3 py-1.5 text-muted-foreground">{t.source}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{t.price}</td>
                  <td className="px-4 py-1.5 text-right text-muted-foreground">{t.market_type}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
