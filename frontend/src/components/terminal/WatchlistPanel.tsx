import { useState } from "react";
import { ChevronDown, ChevronRight, Plus, MoreHorizontal, LayoutGrid, Edit3, Circle, ExternalLink, Zap } from "lucide-react";
import { ASSETS } from "@/lib/market-data";
import { cn } from "@/lib/utils";

export const WatchlistPanel = () => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    crypto: true,
    forex: true,
    metals: true
  });

  const [activeAsset, setActiveAsset] = useState(ASSETS.find(a => a.symbol === "XAU/USD") || ASSETS[0]);

  const toggleGroup = (group: string) => {
    setExpanded(prev => ({ ...prev, [group]: !prev[group] }));
  };

  const groups = [
    { id: "crypto", label: "CRYPTO", items: ASSETS.filter(a => a.class === "crypto") },
    { id: "forex", label: "FOREX", items: ASSETS.filter(a => a.class === "forex") },
    { id: "metals", label: "METALS", items: ASSETS.filter(a => a.class === "metals") },
  ];

  return (
    <div className="flex flex-col h-full rounded-xl border border-border/60 bg-surface-2/40 overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/60 bg-card">
        <h2 className="text-sm font-semibold tracking-tight flex items-center gap-2 cursor-pointer hover:text-primary transition-colors">
          Watchlist <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </h2>
        <div className="flex items-center gap-3 text-muted-foreground">
          <Plus className="h-4 w-4 cursor-pointer hover:text-foreground" />
          <LayoutGrid className="h-4 w-4 cursor-pointer hover:text-foreground" />
          <MoreHorizontal className="h-4 w-4 cursor-pointer hover:text-foreground" />
        </div>
      </div>

      {/* Table Header */}
      <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr] px-4 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border/40 bg-surface-2/20">
        <div>Symbol</div>
        <div className="text-right">Last</div>
        <div className="text-right">Chg</div>
        <div className="text-right">Chg%</div>
      </div>

      {/* Watchlist Scrollable Area */}
      <div className="flex-1 overflow-y-auto min-h-[300px] border-b border-border/60">
        {groups.map(group => (
          <div key={group.id} className="mb-1">
            <div
              className="flex items-center gap-2 px-2 py-1.5 cursor-pointer hover:bg-surface-2/40 text-muted-foreground"
              onClick={() => toggleGroup(group.id)}
            >
              {expanded[group.id] ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              <span className="text-[10px] uppercase font-semibold tracking-wider">{group.label}</span>
            </div>

            {expanded[group.id] && (
              <div className="flex flex-col">
                {group.items.map(asset => {
                  const isUp = asset.change >= 0;
                  const isActive = activeAsset.symbol === asset.symbol;
                  return (
                    <div
                      key={asset.symbol}
                      onClick={() => setActiveAsset(asset)}
                      className={cn(
                        "grid grid-cols-[1.5fr_1fr_1fr_1fr] px-4 py-1.5 text-[12px] font-mono items-center cursor-pointer transition-colors border-y border-transparent",
                        isActive ? "bg-surface-2/80 border-border/60 rounded" : "hover:bg-surface-2/40"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        {asset.class === 'crypto' && <span className="h-1.5 w-1.5 rounded-full bg-crypto shadow-[0_0_8px_hsl(var(--crypto))]" />}
                        {asset.class === 'forex' && <span className="h-1.5 w-1.5 rounded-full bg-forex shadow-[0_0_8px_hsl(var(--forex))]" />}
                        {asset.class === 'metals' && <span className="h-1.5 w-1.5 rounded-full bg-metals shadow-[0_0_8px_hsl(var(--metals))]" />}
                        <span className="font-sans font-semibold tracking-tight text-foreground">{asset.symbol.split('/')[0]}</span>
                      </div>
                      <div className="text-right text-foreground">{asset.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                      <div className={cn("text-right", isUp ? "text-bull" : "text-bear")}>
                        {isUp ? "+" : ""}{(asset.price * (asset.change / 100)).toFixed(2)}
                      </div>
                      <div className={cn("text-right", isUp ? "text-bull" : "text-bear")}>
                        {isUp ? "+" : ""}{asset.change.toFixed(2)}%
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Asset Detail Card (Bottom) */}
      <div className="p-4 bg-card shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20 text-primary">
              <Circle className="h-3 w-3 fill-current" />
            </div>
            <h3 className="font-semibold tracking-tight">{activeAsset.symbol.split('/')[0]}</h3>
          </div>
          <div className="flex items-center gap-3 text-muted-foreground">
            <LayoutGrid className="h-4 w-4 cursor-pointer hover:text-foreground" />
            <Edit3 className="h-4 w-4 cursor-pointer hover:text-foreground" />
            <MoreHorizontal className="h-4 w-4 cursor-pointer hover:text-foreground" />
          </div>
        </div>

        <div className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
          CFD on {activeAsset.name} (US$) <ExternalLink className="inline h-3 w-3 ml-0.5" /> • TVC<br />
          Commodity • Cfd
        </div>

        <div className="mb-4">
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-mono font-bold tracking-tight text-foreground">
              {activeAsset.price.toLocaleString(undefined, { minimumFractionDigits: 3 })}
            </span>
            <span className="text-[10px] font-semibold text-muted-foreground">USD</span>
          </div>
          <div className={cn("text-[13px] font-mono font-medium flex items-center gap-2 mt-0.5", activeAsset.change >= 0 ? "text-bull" : "text-bear")}>
            <span>{activeAsset.change >= 0 ? "+" : ""}{(activeAsset.price * (activeAsset.change / 100)).toFixed(3)}</span>
            <span>{activeAsset.change >= 0 ? "+" : ""}{activeAsset.change.toFixed(2)}%</span>
          </div>
          <div className="flex items-center gap-1.5 mt-1.5 text-[11px] text-bull">
            <span className="h-1.5 w-1.5 rounded-full bg-bull shadow-[0_0_8px_hsl(var(--bull))]" /> Market Open
          </div>
        </div>

        {/* News Flash */}
        <div className="rounded-md border border-border/60 bg-surface-2/40 p-2.5 flex gap-2 items-start cursor-pointer hover:bg-surface-2/60 transition-colors mb-4">
          <Zap className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
          <div className="text-[11px]">
            <span className="text-muted-foreground">5 mins ago • </span>
            <span className="text-foreground leading-tight">{activeAsset.name} tests major resistance levels amid changing macro conditions...</span>
          </div>
          <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0 mt-1" />
        </div>

        {/* Performance Grid */}
        <div className="space-y-1.5">
          <h4 className="text-[11px] font-semibold tracking-tight text-foreground mb-2">Performance</h4>
          <div className="grid grid-cols-3 gap-1.5">
            {[
              { label: "1W", val: 1.74 },
              { label: "1M", val: 3.71 },
              { label: "3M", val: -1.36 },
              { label: "6M", val: 17.85 },
              { label: "YTD", val: 11.78 },
              { label: "1Y", val: 44.81 },
            ].map(perf => (
              <div key={perf.label} className={cn(
                "flex flex-col items-center justify-center p-1.5 rounded border border-border/40",
                perf.val >= 0 ? "bg-bull/10 text-bull" : "bg-bear/10 text-bear"
              )}>
                <span className="text-[11px] font-mono font-medium">{perf.val > 0 ? "+" : ""}{perf.val}%</span>
                <span className="text-[9px] uppercase tracking-wider text-muted-foreground mt-0.5">{perf.label}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
