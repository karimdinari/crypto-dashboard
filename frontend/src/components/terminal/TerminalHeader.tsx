import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Search, Bell, RefreshCw, Command, ChevronDown, Zap, TrendingUp, TrendingDown, ArrowRight, BellOff } from "lucide-react";
import { Link } from "react-router-dom";
import { useAlertsContext } from "@/context/AlertsContext";
import { AssetImage } from "@/components/AssetImage";
import { useAssets, useLatestStream } from "@/lib/api";

// ── Notification Dropdown (portaled to body) ──────────────────────────────
const AlertsDropdown = ({
  anchorRef,
  onClose,
}: {
  anchorRef: React.RefObject<HTMLDivElement>;
  onClose: () => void;
}) => {
  const { alerts } = useAlertsContext();
  const { data: assets = [] } = useAssets();
  const { data: streamTicks = [] } = useLatestStream();
  const [pos, setPos] = useState({ top: 0, right: 0 });

  // Position relative to the bell button
  useEffect(() => {
    if (!anchorRef.current) return;
    const rect = anchorRef.current.getBoundingClientRect();
    setPos({
      top: rect.bottom + 8,
      right: window.innerWidth - rect.right,
    });
  }, []);

  const resolvePrice = (sym: string, fallback: number) => {
    const tick = streamTicks.find(t => t.symbol === sym);
    const asset = assets.find(a => a.symbol === sym);
    return tick?.price ?? asset?.price ?? fallback;
  };

  const enriched = alerts
    .map(alert => {
      const currentPrice = resolvePrice(alert.symbol, alert.initialPrice);
      const isTriggered =
        alert.condition === "above"
          ? currentPrice >= alert.targetPrice
          : currentPrice <= alert.targetPrice;
      const distancePct =
        alert.targetPrice > 0
          ? ((currentPrice - alert.targetPrice) / alert.targetPrice) * 100
          : 0;
      const asset = assets.find(a => a.symbol === alert.symbol);
      return { ...alert, currentPrice, isTriggered, distancePct, asset };
    })
    .sort((a, b) => Number(b.isTriggered) - Number(a.isTriggered));

  const triggeredAlerts = enriched.filter(a => a.isTriggered);
  const activeAlerts = enriched.filter(a => !a.isTriggered);

  return createPortal(
    <>
      {/* Full-screen invisible backdrop */}
      <div className="fixed inset-0 z-[9998]" onClick={onClose} />

      {/* Dropdown panel */}
      <div
        style={{ position: "fixed", top: pos.top, right: pos.right, zIndex: 9999 }}
        className="w-[360px] rounded-xl border border-border bg-popover shadow-2xl overflow-hidden"
        // CSS animation via inline style since we can't use Tailwind animate here safely
        onAnimationEnd={undefined}
      >
        <style>{`
          @keyframes matDropIn {
            from { opacity: 0; transform: translateY(-10px) scale(0.96); }
            to   { opacity: 1; transform: translateY(0)    scale(1);    }
          }
          .mat-drop-in { animation: matDropIn 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
          @keyframes matRowIn {
            from { opacity: 0; transform: translateX(6px); }
            to   { opacity: 1; transform: translateX(0);   }
          }
          .mat-row-in { animation: matRowIn 0.22s cubic-bezier(0.16, 1, 0.3, 1) both; }
        `}</style>

        <div className="mat-drop-in">
          {/* ── Header ── */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface/80 backdrop-blur">
            <div className="flex items-center gap-2">
              <Bell className="h-3.5 w-3.5 text-primary" />
              <span className="text-sm font-semibold">Alerts</span>
              {triggeredAlerts.length > 0 && (
                <span className="flex items-center justify-center h-4 min-w-4 rounded-full bg-bear px-1 text-[9px] font-bold text-white animate-pulse">
                  {triggeredAlerts.length}
                </span>
              )}
            </div>
            <Link
              to="/alerts"
              onClick={onClose}
              className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-primary transition-colors"
            >
              Manage <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {/* ── Content ── */}
          <div className="max-h-[420px] overflow-y-auto">
            {enriched.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 gap-2">
                <BellOff className="h-8 w-8 text-muted-foreground/20" />
                <p className="text-xs text-muted-foreground">No alerts configured</p>
                <Link
                  to="/alerts"
                  onClick={onClose}
                  className="text-[11px] text-primary hover:underline mt-1"
                >
                  Create your first alert →
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-border/50">

                {/* Triggered */}
                {triggeredAlerts.length > 0 && (
                  <div>
                    <div className="px-4 py-1.5 bg-bear/8 border-b border-bear/15">
                      <span className="text-[10px] uppercase tracking-widest font-semibold text-bear flex items-center gap-1.5">
                        <Zap className="h-3 w-3" /> Triggered
                      </span>
                    </div>
                    {triggeredAlerts.map((alert, i) => (
                      <div
                        key={alert.id}
                        className="mat-row-in flex items-center gap-3 px-4 py-3 bg-primary/[0.03] hover:bg-primary/[0.07] transition-colors"
                        style={{ animationDelay: `${i * 0.05}s` }}
                      >
                        <AssetImage symbol={alert.symbol} name={alert.asset?.name} size="xs" showBorder={false} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 mb-0.5">
                            <span className="font-mono text-sm font-semibold">{alert.symbol}</span>
                            <span className="inline-flex items-center gap-0.5 rounded-sm bg-primary/15 border border-primary/20 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-primary animate-pulse">
                              <Zap className="h-2.5 w-2.5" /> Hit
                            </span>
                          </div>
                          <p className="text-[11px] text-muted-foreground">
                            {alert.condition === "above"
                              ? <span className="text-bull font-medium">↑ Above </span>
                              : <span className="text-bear font-medium">↓ Below </span>
                            }
                            <span className="font-mono">{alert.targetPrice.toLocaleString()}</span>
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="font-mono text-sm font-semibold text-primary tabular-nums">
                            {alert.currentPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                          </div>
                          <div className={`text-[10px] font-mono ${alert.distancePct > 0 ? "text-bull" : "text-bear"}`}>
                            {alert.distancePct > 0 ? "+" : ""}{alert.distancePct.toFixed(2)}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Watching */}
                {activeAlerts.length > 0 && (
                  <div>
                    {triggeredAlerts.length > 0 && (
                      <div className="px-4 py-1.5 bg-surface/60 border-b border-border/40">
                        <span className="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground">
                          Watching
                        </span>
                      </div>
                    )}
                    {activeAlerts.map((alert, i) => {
                      let progress = 0;
                      if (alert.condition === "above") {
                        if (alert.currentPrice > alert.initialPrice)
                          progress = ((alert.currentPrice - alert.initialPrice) / (alert.targetPrice - alert.initialPrice)) * 100;
                      } else {
                        if (alert.currentPrice < alert.initialPrice)
                          progress = ((alert.initialPrice - alert.currentPrice) / (alert.initialPrice - alert.targetPrice)) * 100;
                      }
                      progress = Math.min(Math.max(progress, 0), 100);

                      return (
                        <div
                          key={alert.id}
                          className="mat-row-in px-4 py-3 hover:bg-surface-2/50 transition-colors"
                          style={{ animationDelay: `${(i + triggeredAlerts.length) * 0.05 + 0.05}s` }}
                        >
                          <div className="flex items-center gap-3">
                            <AssetImage symbol={alert.symbol} name={alert.asset?.name} size="xs" showBorder={false} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-1.5">
                                <div className="flex items-center gap-1.5">
                                  <span className="font-mono text-sm font-medium">{alert.symbol}</span>
                                  {alert.condition === "above"
                                    ? <TrendingUp className="h-3 w-3 text-bull" />
                                    : <TrendingDown className="h-3 w-3 text-bear" />
                                  }
                                </div>
                                <span className="font-mono text-xs tabular-nums text-foreground">
                                  {alert.currentPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] font-mono text-muted-foreground/50 shrink-0 w-14 truncate">
                                  {alert.targetPrice.toLocaleString()}
                                </span>
                                <div className="relative flex-1 h-1 rounded-full bg-surface-2 overflow-hidden">
                                  <div
                                    className={`h-full rounded-full transition-all duration-700 ${
                                      alert.condition === "above" ? "bg-bull/70" : "bg-bear/70"
                                    }`}
                                    style={{ width: `${progress}%` }}
                                  />
                                </div>
                                <span className="text-[10px] font-mono text-muted-foreground/50 shrink-0 w-7 text-right">
                                  {progress.toFixed(0)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Footer ── */}
          {enriched.length > 0 && (
            <div className="border-t border-border px-4 py-2.5 bg-surface/60 flex items-center justify-between">
              <span className="text-[11px] text-muted-foreground">
                {enriched.length} alert{enriched.length !== 1 ? "s" : ""} · live prices
              </span>
              <Link
                to="/alerts"
                onClick={onClose}
                className="text-[11px] text-primary hover:underline flex items-center gap-1"
              >
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
        </div>
      </div>
    </>,
    document.body
  );
};

// ── Terminal Header ───────────────────────────────────────────────────────
export const TerminalHeader = () => {
  const { triggeredCount } = useAlertsContext();
  const [bellOpen, setBellOpen] = useState(false);
  const bellRef = useRef<HTMLDivElement>(null);
  const [now, setNow] = useState(
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })
  );

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="relative flex h-14 shrink-0 items-center gap-3 border-b border-border bg-surface/50 px-4 backdrop-blur-xl lg:px-6">
      {/* Mobile brand */}
      <div className="flex items-center gap-2 lg:hidden">
        <div className="relative flex h-7 w-7 items-center justify-center">
          <span className="absolute inset-0 rounded-md bg-gradient-to-br from-crypto via-forex to-metals" />
          <span className="absolute inset-[2px] rounded-[5px] bg-background" />
          <span className="relative mono text-[10px] font-bold brand-mark">M</span>
        </div>
        <span className="text-sm font-semibold brand-mark">MAT/01</span>
      </div>

      {/* Page title */}
      <div className="hidden flex-col leading-tight md:flex">
        <div className="flex items-center gap-2">
          <h1 className="text-[13px] font-semibold tracking-tight">Market Analytics Terminal</h1>
          <span className="mono rounded border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-[0.18em] text-primary">v3.2</span>
        </div>
        <p className="mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
          Multi-asset · Real-time · Predictive intelligence
        </p>
      </div>

      <div className="mx-3 hidden h-7 w-px bg-border md:block" />

      {/* Search */}
      <div className="ml-auto flex max-w-md flex-1 items-center">
        <div className="group relative flex w-full items-center">
          <Search className="absolute left-3 h-3.5 w-3.5 text-muted-foreground" />
          <input
            placeholder="Search asset, news, signal…"
            className="mono h-9 w-full rounded-md border border-border bg-surface pl-9 pr-16 text-[12px] tracking-tight outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-primary/50 focus:shadow-[0_0_0_3px_hsl(var(--primary)/0.12)]"
          />
          <kbd className="mono pointer-events-none absolute right-2 inline-flex items-center gap-1 rounded border border-border bg-surface-2 px-1.5 py-0.5 text-[9px] text-muted-foreground">
            <Command className="h-2.5 w-2.5" /> K
          </kbd>
        </div>
      </div>

      {/* Right cluster */}
      <div className="flex items-center gap-2">
        <div className="hidden items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 md:flex">
          <RefreshCw className="h-3 w-3 text-muted-foreground" />
          <span className="mono text-[11px] text-muted-foreground">UTC</span>
          <span className="mono text-[11px] font-medium num">{now}</span>
        </div>

        {/* Bell */}
        <div ref={bellRef} className="relative">
          <button
            onClick={() => setBellOpen(o => !o)}
            className={`relative flex h-9 w-9 items-center justify-center rounded-md border transition-all duration-150 ${
              bellOpen
                ? "border-primary/40 bg-primary/10 text-primary"
                : "border-border bg-surface text-muted-foreground hover:text-foreground"
            }`}
          >
            <Bell className={`h-4 w-4 transition-transform duration-200 ${bellOpen ? "scale-110" : ""}`} />
            {triggeredCount > 0 ? (
              <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-bear px-1 text-[9px] font-bold text-white shadow-[0_0_8px_hsl(var(--bear))] animate-pulse">
                {triggeredCount}
              </span>
            ) : (
              <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-muted" />
            )}
          </button>

          {bellOpen && (
            <AlertsDropdown anchorRef={bellRef} onClose={() => setBellOpen(false)} />
          )}
        </div>

        <button className="flex items-center gap-2 rounded-md border border-border bg-surface px-2 py-1.5 transition-colors hover:bg-surface-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-sm bg-gradient-to-br from-forex via-crypto to-metals text-[10px] font-bold text-background">
            JT
          </div>
          <span className="hidden text-[12px] font-medium md:inline">J. Trader</span>
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        </button>
      </div>
    </header>
  );
};

const SessionBadge = ({ label, status }: { label: string; status: "open" | "closed" }) => (
  <div className="flex items-center gap-1.5">
    <span className={`h-1.5 w-1.5 rounded-full ${status === "open" ? "bg-bull shadow-[0_0_8px_hsl(var(--bull))]" : "bg-muted"}`} />
    <span className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
  </div>
);

const Tier = ({ label, color }: { label: string; color: string }) => (
  <span className={`mono inline-flex h-4 w-4 items-center justify-center rounded-sm text-[9px] font-bold text-background ${color}`}>{label}</span>
);