import { useState } from "react";
import { useAssets, useLatestStream } from "@/lib/api";
import { cn } from "@/lib/utils";
import { AssetImage } from "@/components/AssetImage";

export const TickerTape = () => {
  const { data: assets } = useAssets();
  const { data: stream } = useLatestStream();
  const [paused, setPaused] = useState(false);

  const items = (assets ?? []).map((a) => {
    const tick = stream?.find((s) => s.symbol === a.symbol);
    return {
      symbol: a.symbol,
      market: a.market,
      price: tick?.price ?? a.price,
      changePct: a.changePct,
    };
  });

  if (items.length === 0) return null;

  const looped = [...items, ...items, ...items];

  return (
    <div
      className="relative flex h-9 shrink-0 items-center overflow-hidden border-b border-border bg-surface-2/60 cursor-default"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Edge fades */}
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-20 bg-gradient-to-r from-background to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-20 bg-gradient-to-l from-background to-transparent" />

      {/* Ticker strip — always animate-ticker, only pause via style */}
      <div
        className="animate-ticker flex w-max items-center gap-8 whitespace-nowrap px-6"
        style={{
          animationPlayState: paused ? "paused" : "running",
          transition: "opacity 150ms ease",
          opacity: paused ? 0.85 : 1,
        }}
      >
        {looped.map((a, i) => {
          const up = a.changePct >= 0;
          const isForexOrSilver = a.market === "forex" || a.symbol.startsWith("XAG");
          return (
            <div
              key={i}
              className="flex items-center gap-2 text-[12px] transition-opacity duration-150"
            >
              <AssetImage symbol={a.symbol} size="xxs" showBorder={false} />
              <span className="mono font-medium tracking-tight text-foreground">
                {a.symbol}
              </span>
              <span className="mono text-muted-foreground tabular-nums">
                {isForexOrSilver
                  ? a.price.toFixed(4)
                  : a.price.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
              </span>
              <span
                className={cn(
                  "mono text-[11px] font-medium tabular-nums",
                  up ? "text-bull" : "text-bear"
                )}
              >
                {up ? "▲" : "▼"} {Math.abs(a.changePct).toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};