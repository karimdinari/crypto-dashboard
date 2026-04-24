import { useAssets, useLatestStream } from "@/lib/api";
import { cn } from "@/lib/utils";
import { AssetImage } from "@/components/AssetImage";

export const TickerTape = () => {
  const { data: assets } = useAssets();
  const { data: stream } = useLatestStream();

  // Merge stream prices into assets for the most live price possible
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

  // Triple the array for seamless looping
  const looped = [...items, ...items, ...items];

  return (
    <div className="relative flex h-9 shrink-0 items-center overflow-hidden border-b border-border bg-surface-2/60">
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-background to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-background to-transparent" />
      <div className="animate-ticker flex w-max items-center gap-8 whitespace-nowrap px-6">
        {looped.map((a, i) => {
          const up = a.changePct >= 0;
          const isForexOrSilver = a.market === "forex" || a.symbol.startsWith("XAG");
          return (
            <div key={i} className="flex items-center gap-2 text-[12px]">
              <AssetImage symbol={a.symbol} size="xxs" showBorder={false} />
              <span className="mono font-medium tracking-tight text-foreground">{a.symbol}</span>
              <span className="mono text-muted-foreground">
                {isForexOrSilver
                  ? a.price.toFixed(4)
                  : a.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className={cn("mono text-[11px] font-medium", up ? "text-bull" : "text-bear")}>
                {up ? "▲" : "▼"} {Math.abs(a.changePct).toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};