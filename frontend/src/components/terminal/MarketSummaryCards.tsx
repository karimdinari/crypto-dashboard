import { useAssets } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Bitcoin, Banknote, Coins, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { AssetImage } from "@/components/AssetImage";
import { Sparkline } from "./Sparkline";

const GROUPS = [
  { key: "crypto" as const, label: "Crypto",          tag: "Electric · 24/7", icon: Bitcoin,  accent: "text-crypto", ring: "ring-crypto/30",  aura: "aura-crypto", dot: "bg-crypto",  desc: "BTC · ETH · L2" },
  { key: "forex"  as const, label: "Foreign Exchange",tag: "Calm · Macro",    icon: Banknote, accent: "text-forex",  ring: "ring-forex/30",   aura: "aura-forex",  dot: "bg-forex",   desc: "EUR · GBP · DXY" },
  { key: "metals" as const, label: "Precious Metals", tag: "Premium · Reserve",icon: Coins,   accent: "text-metals", ring: "ring-metals/30",  aura: "aura-metals", dot: "bg-metals",  desc: "XAU · XAG" },
];

export const MarketSummaryCards = () => {
  const { data: assets } = useAssets();
  if (!assets) return null;

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {GROUPS.map((g) => {
        const groupAssets = assets.filter((a) => a.market === g.key);
        const avg = groupAssets.length > 0 ? groupAssets.reduce((s, a) => s + a.changePct, 0) / groupAssets.length : 0;
        const up = avg >= 0;
        const Icon = g.icon;
        return (
          <div key={g.key} className="group relative overflow-hidden rounded-xl border border-border bg-card p-4 shadow-card transition-all hover:border-border/80 hover:shadow-elevated hairline-top">
            {/* Class aura */}
            <div className={cn("pointer-events-none absolute inset-0 opacity-80", g.aura)} />
            {/* Top accent line */}
            <div className={cn("pointer-events-none absolute inset-x-0 top-0 h-px",
              g.key === "crypto" && "bg-gradient-to-r from-transparent via-crypto/60 to-transparent",
              g.key === "forex"  && "bg-gradient-to-r from-transparent via-forex/60 to-transparent",
              g.key === "metals" && "bg-gradient-to-r from-transparent via-metals/60 to-transparent",
            )} />

            <div className="relative flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className={cn("relative flex h-10 w-10 items-center justify-center rounded-lg bg-surface-2 ring-1", g.ring)}>
                  <Icon className={cn("h-4.5 w-4.5", g.accent)} />
                  <span className={cn("absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full ring-2 ring-card", g.dot)} />
                </div>
                <div>
                  <p className="text-[13px] font-semibold leading-tight">{g.label}</p>
                  <p className="mono text-[9.5px] uppercase tracking-[0.18em] text-muted-foreground">{g.tag}</p>
                </div>
              </div>
              <div className={cn("flex items-center gap-0.5 rounded-md px-1.5 py-1 text-[11px] font-semibold mono num",
                up ? "bg-bull/10 text-bull ring-1 ring-bull/20" : "bg-bear/10 text-bear ring-1 ring-bear/20")}>
                {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                {up ? "+" : ""}{avg.toFixed(2)}%
              </div>
            </div>

            <div className="relative mt-4 space-y-2">
              {groupAssets.map((a) => {
                const aUp = a.changePct >= 0;
                return (
                  <div key={a.symbol} className="flex items-center gap-3 rounded-md px-1 py-0.5 transition-colors hover:bg-surface-2/40">
                    <AssetImage symbol={a.symbol} size="sm" showBorder={false} />
                    <span className="mono w-[52px] text-[11px] font-medium tracking-tight text-foreground/95">{a.symbol}</span>
                    <div className="flex-1">
                      <Sparkline data={a.spark || []} color={aUp ? "hsl(var(--bull))" : "hsl(var(--bear))"} />
                    </div>
                    <span className="mono w-[80px] text-right text-[11px] num">
                      {a.market === "forex" ? a.price.toFixed(4) : a.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span className={cn("mono w-[52px] text-right text-[11px] font-semibold num", aUp ? "text-bull" : "text-bear")}>
                      {aUp ? "+" : ""}{a.changePct.toFixed(2)}%
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Footer meta */}
            <div className="relative mt-3 flex items-center justify-between border-t border-border/60 pt-2">
              <span className="mono text-[9.5px] uppercase tracking-[0.18em] text-muted-foreground">{g.desc}</span>
              <span className="mono flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <span className="pulse-dot bg-bull" /> live
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
