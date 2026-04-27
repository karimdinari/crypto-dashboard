import { useState, useEffect, useRef } from "react";
import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAssets, useLatestStream } from "@/lib/api";
import { AssetImage } from "@/components/AssetImage";
import { Bell, Plus, Trash2, Zap, Loader2, TrendingUp, TrendingDown, Activity, ShieldAlert, ChevronDown, Check } from "lucide-react";

interface Alert {
  id: string;
  symbol: string;
  condition: "above" | "below";
  targetPrice: number;
  initialPrice: number;
}

// ── Custom Asset Selector ──────────────────────────────────────────────────
const AssetSelector = ({
  assets,
  value,
  onChange,
}: {
  assets: { symbol: string; name: string; market: string }[];
  value: string;
  onChange: (sym: string) => void;
}) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const selected = assets.find(a => a.symbol === value);

  const filtered = assets.filter(a =>
    a.symbol.toLowerCase().includes(search.toLowerCase()) ||
    a.name.toLowerCase().includes(search.toLowerCase())
  );

  // Group by market
  const grouped = filtered.reduce<Record<string, typeof assets>>((acc, a) => {
    acc[a.market] = [...(acc[a.market] ?? []), a];
    return acc;
  }, {});

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const marketLabel: Record<string, string> = {
    crypto: "Crypto",
    forex: "Forex",
    metals: "Metals",
  };

  return (
    <div ref={ref} className="relative">
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex h-10 w-full items-center gap-2.5 rounded-md border border-input bg-transparent px-3 text-sm shadow-sm transition-colors hover:bg-surface-2 focus:outline-none focus:ring-1 focus:ring-ring"
      >
        {selected ? (
          <>
            <AssetImage symbol={selected.symbol} name={selected.name} size="xxs" showBorder={false} />
            <span className="font-mono font-medium flex-1 text-left">{selected.symbol}</span>
            <span className="text-xs text-muted-foreground truncate max-w-[100px]">{selected.name}</span>
          </>
        ) : (
          <span className="text-muted-foreground flex-1 text-left">Select asset…</span>
        )}
        <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 mt-1.5 w-full rounded-md border border-border bg-popover shadow-xl overflow-hidden">
          {/* Search */}
          <div className="border-b border-border px-2 py-2">
            <input
              autoFocus
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search assets…"
              className="w-full bg-transparent text-xs outline-none placeholder:text-muted-foreground/50 px-1 py-0.5 font-mono"
            />
          </div>

          {/* Options */}
          <div className="max-h-64 overflow-y-auto">
            {Object.entries(grouped).map(([market, items]) => (
              <div key={market}>
                {/* Group label */}
                <div className="px-3 py-1.5 text-[10px] uppercase tracking-widest text-muted-foreground/60 font-semibold border-b border-border/40 bg-surface/40">
                  {marketLabel[market] ?? market}
                </div>
                {items.map(asset => (
                  <button
                    key={asset.symbol}
                    type="button"
                    onClick={() => { onChange(asset.symbol); setOpen(false); setSearch(""); }}
                    className={`flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-surface-2 ${
                      asset.symbol === value ? "bg-primary/8" : ""
                    }`}
                  >
                    <AssetImage symbol={asset.symbol} name={asset.name} size="xs" showBorder={false} />
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-sm font-medium text-foreground">{asset.symbol}</div>
                      <div className="text-[11px] text-muted-foreground truncate">{asset.name}</div>
                    </div>
                    {asset.symbol === value && (
                      <Check className="h-3.5 w-3.5 text-primary shrink-0" />
                    )}
                  </button>
                ))}
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="py-8 text-center text-xs text-muted-foreground">No assets match "{search}"</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Main Page ──────────────────────────────────────────────────────────────
const Alerts = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [symbol, setSymbol] = useState("");
  const [target, setTarget] = useState("");
  const [condition, setCondition] = useState<"above" | "below">("above");

  const { data: assets = [], isLoading: assetsLoading } = useAssets();
  const { data: streamTicks = [] } = useLatestStream();

  useEffect(() => {
    if (assets.length > 0 && !symbol) setSymbol(assets[0].symbol);
  }, [assets]);

  useEffect(() => {
    const saved = localStorage.getItem("mat_alerts");
    if (saved) { try { setAlerts(JSON.parse(saved)); } catch {} }
  }, []);

  useEffect(() => {
    localStorage.setItem("mat_alerts", JSON.stringify(alerts));
  }, [alerts]);

  const resolvePrice = (sym: string, fallback: number): number => {
    const tick = streamTicks.find(t => t.symbol === sym);
    const asset = assets.find(a => a.symbol === sym);
    return tick?.price ?? asset?.price ?? fallback;
  };

  const addAlert = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol || !target) return;
    const currentPrice = resolvePrice(symbol, Number(target));
    setAlerts(prev => [...prev, {
      id: crypto.randomUUID(),
      symbol,
      condition,
      targetPrice: Number(target),
      initialPrice: currentPrice,
    }]);
    setTarget("");
  };

  const removeAlert = (id: string) => setAlerts(prev => prev.filter(a => a.id !== id));

  const activeAlerts = alerts.map(alert => {
    const currentPrice = resolvePrice(alert.symbol, alert.initialPrice);
    const isTriggered = alert.condition === "above"
      ? currentPrice >= alert.targetPrice
      : currentPrice <= alert.targetPrice;

    let progress = 0;
    if (alert.condition === "above") {
      if (currentPrice >= alert.targetPrice) progress = 100;
      else if (currentPrice <= alert.initialPrice) progress = 0;
      else progress = ((currentPrice - alert.initialPrice) / (alert.targetPrice - alert.initialPrice)) * 100;
    } else {
      if (currentPrice <= alert.targetPrice) progress = 100;
      else if (currentPrice >= alert.initialPrice) progress = 0;
      else progress = ((alert.initialPrice - currentPrice) / (alert.initialPrice - alert.targetPrice)) * 100;
    }

    const distancePct = alert.targetPrice > 0
      ? (((currentPrice - alert.targetPrice) / alert.targetPrice) * 100)
      : 0;

    return { ...alert, currentPrice, isTriggered, progress, distancePct };
  });

  const triggeredCount = activeAlerts.filter(a => a.isTriggered).length;
  const activeCount = alerts.length - triggeredCount;
  const selectedAssetPrice = resolvePrice(symbol, 0);
  const selectedAsset = assets.find(a => a.symbol === symbol);

  return (
    <TerminalLayout>
      <div className="space-y-6">

        {/* ── Header ── */}
        <div className="flex items-start justify-between border-b border-border pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 border border-primary/20">
                <Bell className="h-4 w-4 text-primary" />
              </div>
              Price Alerts
            </h1>
            <p className="text-sm text-muted-foreground mt-1.5">
              Real-time triggers against live stream prices · {alerts.length} alert{alerts.length !== 1 ? "s" : ""} configured
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2">
              <Activity className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Active</span>
              <span className="font-mono text-sm font-semibold">{activeCount}</span>
            </div>
            <div className={`flex items-center gap-2 rounded-md border px-3 py-2 transition-colors ${
              triggeredCount > 0 ? "border-bear/40 bg-bear/10" : "border-border bg-surface"
            }`}>
              <Zap className={`h-3.5 w-3.5 ${triggeredCount > 0 ? "text-bear" : "text-muted-foreground"}`} />
              <span className="text-xs text-muted-foreground">Triggered</span>
              <span className={`font-mono text-sm font-semibold ${triggeredCount > 0 ? "text-bear" : ""}`}>
                {triggeredCount}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* ── Form ── */}
          <div className="space-y-4">
            <Card className="bg-card border-border/60">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-primary" />
                  New Alert
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">

                {/* Asset selector */}
                <div className="space-y-1.5">
                  <label className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">Asset</label>
                  {assetsLoading ? (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground h-10 px-3 rounded-md border border-border">
                      <Loader2 className="h-3 w-3 animate-spin" /> Loading assets…
                    </div>
                  ) : (
                    <AssetSelector assets={assets} value={symbol} onChange={setSymbol} />
                  )}
                </div>

                {/* Condition toggle */}
                <div className="space-y-1.5">
                  <label className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">Condition</label>
                  <div className="grid grid-cols-2 gap-2 p-1 rounded-md border border-border bg-surface">
                    <button
                      type="button"
                      onClick={() => setCondition("above")}
                      className={`flex items-center justify-center gap-1.5 rounded py-2 text-xs font-medium transition-all ${
                        condition === "above"
                          ? "bg-bull/20 text-bull border border-bull/30 shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <TrendingUp className="h-3.5 w-3.5" /> Crosses Above
                    </button>
                    <button
                      type="button"
                      onClick={() => setCondition("below")}
                      className={`flex items-center justify-center gap-1.5 rounded py-2 text-xs font-medium transition-all ${
                        condition === "below"
                          ? "bg-bear/20 text-bear border border-bear/30 shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <TrendingDown className="h-3.5 w-3.5" /> Crosses Below
                    </button>
                  </div>
                </div>

                {/* Target price */}
                <div className="space-y-1.5">
                  <label className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">Target Price</label>
                  <Input
                    type="number"
                    step="any"
                    placeholder="0.00"
                    value={target}
                    onChange={e => setTarget(e.target.value)}
                    className="font-mono"
                  />
                  <div className="flex items-center justify-between pt-1 px-0.5">
                    <span className="text-[10px] text-muted-foreground">Live price</span>
                    <span className="text-[11px] font-mono font-medium text-foreground">
                      {selectedAssetPrice > 0
                        ? selectedAssetPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                        : "—"}
                    </span>
                  </div>
                  {target && selectedAssetPrice > 0 && (
                    <div className="flex items-center justify-between px-0.5">
                      <span className="text-[10px] text-muted-foreground">Distance to target</span>
                      <span className={`text-[11px] font-mono font-medium ${
                        (condition === "above" && Number(target) > selectedAssetPrice) ||
                        (condition === "below" && Number(target) < selectedAssetPrice)
                          ? "text-bull" : "text-bear"
                      }`}>
                        {Math.abs(((Number(target) - selectedAssetPrice) / selectedAssetPrice) * 100).toFixed(2)}%
                      </span>
                    </div>
                  )}
                </div>

                <Button
                  type="button"
                  onClick={(e) => addAlert(e as any)}
                  className="w-full gap-2 mt-2"
                  disabled={!symbol || !target || assetsLoading}
                >
                  <Plus className="h-4 w-4" /> Set Alert
                </Button>
              </CardContent>
            </Card>

            <div className="rounded-md border border-border/40 bg-surface/40 px-3 py-2.5">
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                <span className="text-foreground font-medium">Tip:</span> Set the target price close to the live price for meaningful alerts. Alerts persist in your browser and update every 5 seconds.
              </p>
            </div>
          </div>

          {/* ── Alert Cards ── */}
          <div className="lg:col-span-2 space-y-3">
            {activeAlerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 rounded-lg border border-dashed border-border/40 bg-surface/20">
                <div className="flex h-12 w-12 items-center justify-center rounded-full border border-border/40 bg-surface mb-3">
                  <Bell className="h-5 w-5 text-muted-foreground/40" />
                </div>
                <p className="text-sm font-medium text-muted-foreground">No alerts configured</p>
                <p className="text-xs text-muted-foreground/60 mt-1">Create an alert using the form to get started</p>
              </div>
            ) : (
              activeAlerts.map(alert => {
                const alertAsset = assets.find(a => a.symbol === alert.symbol);
                return (
                  <div
                    key={alert.id}
                    className={`group relative rounded-lg border transition-all duration-300 overflow-hidden ${
                      alert.isTriggered
                        ? "border-primary/40 bg-primary/5 shadow-[0_0_20px_hsl(var(--primary)/0.08)]"
                        : "border-border/60 bg-card hover:border-border"
                    }`}
                  >
                    {/* Left color strip */}
                    <div className={`absolute left-0 top-0 bottom-0 w-[3px] ${
                      alert.isTriggered ? "bg-primary animate-pulse" :
                      alert.condition === "above" ? "bg-bull/50" : "bg-bear/50"
                    }`} />

                    <div className="pl-5 pr-4 py-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">

                          {/* Symbol row with icon */}
                          <div className="flex items-center gap-2.5 mb-2">
                            <AssetImage
                              symbol={alert.symbol}
                              name={alertAsset?.name}
                              size="xs"
                              showBorder={false}
                            />
                            <span className="font-mono font-semibold text-foreground">{alert.symbol}</span>
                            {alertAsset && (
                              <span className="text-[10px] text-muted-foreground">{alertAsset.name}</span>
                            )}

                            {alert.isTriggered ? (
                              <span className="ml-auto inline-flex items-center gap-1 rounded-sm border border-primary/30 bg-primary/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-primary animate-pulse">
                                <Zap className="h-3 w-3" /> Triggered
                              </span>
                            ) : (
                              <span className={`ml-auto inline-flex items-center gap-1 rounded-sm border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                                alert.condition === "above"
                                  ? "border-bull/25 bg-bull/10 text-bull"
                                  : "border-bear/25 bg-bear/10 text-bear"
                              }`}>
                                {alert.condition === "above"
                                  ? <TrendingUp className="h-3 w-3" />
                                  : <TrendingDown className="h-3 w-3" />}
                                {alert.condition === "above" ? "Above" : "Below"} {alert.targetPrice.toLocaleString()}
                              </span>
                            )}
                          </div>

                          {/* Progress bar */}
                          {!alert.isTriggered && (
                            <div className="space-y-1.5 mt-3">
                              <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground">
                                <span>{alert.initialPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                                <span className={alert.condition === "above" ? "text-bull" : "text-bear"}>
                                  {alert.progress.toFixed(0)}% to target
                                </span>
                                <span>{alert.targetPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                              </div>
                              <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-surface-2">
                                <div
                                  className={`h-full rounded-full transition-all duration-500 ${
                                    alert.condition === "above" ? "bg-bull" : "bg-bear"
                                  }`}
                                  style={{ width: `${Math.min(alert.progress, 100)}%` }}
                                />
                              </div>
                            </div>
                          )}

                          {alert.isTriggered && (
                            <p className="text-[11px] text-muted-foreground mt-1">
                              Exceeded target by{" "}
                              <span className="font-mono text-primary font-medium">
                                {Math.abs(alert.distancePct).toFixed(2)}%
                              </span>
                            </p>
                          )}
                        </div>

                        {/* Price + remove */}
                        <div className="flex flex-col items-end gap-3 shrink-0">
                          <div className="text-right">
                            <div className={`font-mono font-semibold text-xl tabular-nums ${
                              alert.isTriggered ? "text-primary" : "text-foreground"
                            }`}>
                              {alert.currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </div>
                            <div className={`text-[10px] font-mono mt-0.5 ${
                              alert.distancePct > 0 ? "text-bull" : "text-bear"
                            }`}>
                              {alert.distancePct > 0 ? "+" : ""}{alert.distancePct.toFixed(2)}% vs target
                            </div>
                          </div>
                          <button
                            onClick={() => removeAlert(alert.id)}
                            className="flex items-center gap-1 rounded px-2 py-1 text-[11px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity hover:text-destructive hover:bg-destructive/10"
                          >
                            <Trash2 className="h-3 w-3" /> Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </TerminalLayout>
  );
};

export default Alerts;