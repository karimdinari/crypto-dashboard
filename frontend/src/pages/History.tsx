import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { useAssets, useHistory, useLatestStream } from "@/lib/api";
import { AssetImage } from "@/components/AssetImage";
import { useState, useMemo } from "react";
import {
  Database, Search, TrendingUp, TrendingDown,
  ChevronLeft, ChevronRight, Download, RefreshCw,
  ArrowUpDown, BarChart3, Calendar as CalendarIcon, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { format } from "date-fns";

const PER_PAGE = 50;

const History = () => {
  const { data: assets = [] }        = useAssets();
  const { data: stream = [] }        = useLatestStream();
  const [symbol,  setSymbol]         = useState("BTC/USD");
  const [startDate, setStartDate]    = useState<Date | undefined>(undefined);
  const [endDate, setEndDate]        = useState<Date | undefined>(undefined);
  const [page,    setPage]           = useState(1);
  const [sortDir, setSortDir]        = useState<"asc" | "desc">("desc");

  const { data: rawCandles = [], isLoading, refetch } = useHistory(symbol);

  const streamTick = stream.find(s =>
    s.symbol.replace(/[/_-]/g, "").toLowerCase() ===
    symbol.replace(/[/_-]/g, "").toLowerCase()
  );

  const candles = useMemo(() => {
    const sorted = [...rawCandles]
      .filter(c => c?.t && isFinite(c.o) && isFinite(c.c))
      .sort((a, b) => {
        const diff = new Date(a.t).getTime() - new Date(b.t).getTime();
        return sortDir === "desc" ? -diff : diff;
      });

    if (!startDate && !endDate) return sorted;
    
    return sorted.filter(c => {
      const candleDate = new Date(c.t);
      if (startDate && candleDate < startDate) return false;
      if (endDate) {
        const endOfDay = new Date(endDate);
        endOfDay.setHours(23, 59, 59, 999);
        if (candleDate > endOfDay) return false;
      }
      return true;
    });
  }, [rawCandles, sortDir, startDate, endDate]);

  const pages     = Math.max(1, Math.ceil(candles.length / PER_PAGE));
  const paginated = candles.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  // Stats from full dataset
  const stats = useMemo(() => {
    if (!rawCandles.length) return null;
    const closes = rawCandles.map(c => c.c).filter(Boolean);
    const high   = Math.max(...rawCandles.map(c => c.h));
    const low    = Math.min(...rawCandles.map(c => c.l));
    const first  = closes[0], last = closes[closes.length - 1];
    const chg    = last - first;
    const chgPct = (chg / first) * 100;
    const totalVol = rawCandles.reduce((s, c) => s + (c.v || 0), 0);
    return { high, low, chg, chgPct, totalVol, count: rawCandles.length };
  }, [rawCandles]);

  const livePrice = streamTick?.price ?? rawCandles[rawCandles.length - 1]?.c ?? null;
  const asset     = assets.find(a => a.symbol === symbol);

  const fmt = (n: number, d = 2) =>
    n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });

  const fmtVol = (n: number) =>
    n >= 1e9 ? `${(n / 1e9).toFixed(2)}B`
    : n >= 1e6 ? `${(n / 1e6).toFixed(2)}M`
    : n >= 1e3 ? `${(n / 1e3).toFixed(2)}K`
    : n.toFixed(2);

  const handleExport = () => {
    const csv = [
      "timestamp,open,high,low,close,volume",
      ...candles.map(c =>
        `${c.t},${c.o},${c.h},${c.l},${c.c},${c.v}`
      ),
    ].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `${symbol.replace("/", "-")}_history.csv`;
    a.click();
  };

  return (
    <TerminalLayout>
      <div className="flex flex-col gap-4">

        {/* ── Header ── */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
              Lakehouse · Bronze→Silver→Gold
            </p>
            <h1 className="mt-1 flex items-center gap-2 text-[22px] font-semibold tracking-tight">
              <Database className="h-5 w-5 text-primary" />
              Batch History
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => refetch()}
              className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground transition-colors hover:text-foreground"
              title="Refresh">
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
            <button onClick={handleExport}
              disabled={candles.length === 0}
              className="mono flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground disabled:opacity-40">
              <Download className="h-3.5 w-3.5" /> Export CSV
            </button>
          </div>
        </div>

        {/* ── Asset selector ── */}
        <div className="flex flex-wrap gap-2">
          {assets.map(a => (
            <button key={a.symbol}
              onClick={() => { setSymbol(a.symbol); setPage(1);  }}
              className={cn(
                "mono flex items-center gap-2 rounded-lg border px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider transition-all",
                symbol === a.symbol
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-border bg-surface text-muted-foreground hover:border-border/80 hover:text-foreground"
              )}>
              <AssetImage symbol={a.symbol} size="xxs" showBorder={false} />
              {a.symbol}
              {symbol === a.symbol && livePrice && (
                <span className="ml-1 tabular-nums">${fmt(livePrice)}</span>
              )}
            </button>
          ))}
        </div>

        {/* ── Stats strip ── */}
        {stats && !isLoading && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5">
            {[
              {
                label: "Live Price",
                value: livePrice ? `$${fmt(livePrice)}` : "—",
                sub: asset ? `${asset.changePct >= 0 ? "+" : ""}${asset.changePct?.toFixed(2)}%` : "",
                accent: asset?.changePct >= 0 ? "text-bull" : "text-bear",
              },
              {
                label: "Period High",
                value: `$${fmt(stats.high)}`,
                sub: "all-time in dataset",
                accent: "text-bull",
              },
              {
                label: "Period Low",
                value: `$${fmt(stats.low)}`,
                sub: "all-time in dataset",
                accent: "text-bear",
              },
              {
                label: "Period Change",
                value: `${stats.chg >= 0 ? "+" : ""}${fmt(stats.chg)}`,
                sub: `${stats.chgPct >= 0 ? "+" : ""}${stats.chgPct.toFixed(2)}%`,
                accent: stats.chg >= 0 ? "text-bull" : "text-bear",
              },
              {
                label: "Total Volume",
                value: fmtVol(stats.totalVol),
                sub: `${stats.count.toLocaleString()} candles`,
                accent: "text-muted-foreground",
              },
            ].map(s => (
              <div key={s.label} className="rounded-xl border border-border bg-surface/40 p-3">
                <p className="mono text-[9px] uppercase tracking-wider text-muted-foreground">{s.label}</p>
                <p className={cn("mono mt-1.5 text-[16px] font-semibold tabular-nums leading-none", s.accent)}>
                  {s.value}
                </p>
                <p className={cn("mono mt-1 text-[10px] tabular-nums", s.accent, "opacity-70")}>{s.sub}</p>
              </div>
            ))}
          </div>
        )}

        {/* ── Table card ── */}
        <div className="terminal-card overflow-hidden">
          {/* Table toolbar */}
          <div className="flex flex-col gap-2 border-b border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-[13px] font-semibold tracking-tight">
                {symbol} · OHLCV Data
              </p>
              <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {candles.length.toLocaleString()} records
                {(startDate || endDate) && ` · ${startDate ? format(startDate, 'MMM d, yyyy') : 'start'} to ${endDate ? format(endDate, 'MMM d, yyyy') : 'end'}`}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <button className="mono flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-1.5 text-[11px] uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground">
                    <CalendarIcon className="h-3.5 w-3.5" />
                    {startDate && endDate
                      ? `${format(startDate, 'MMM d')} → ${format(endDate, 'MMM d')}`
                      : startDate
                      ? `From ${format(startDate, 'MMM d')}`
                      : 'Select Period'}
                  </button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="end">
                  <Calendar
                    mode="range"
                    selected={{
                      from: startDate,
                      to: endDate,
                    }}
                    onSelect={(range) => {
                      setStartDate(range?.from);
                      setEndDate(range?.to);
                      setPage(1);
                    }}
                  />
                </PopoverContent>
              </Popover>
              
              {(startDate || endDate) && (
                <button
                  onClick={() => {
                    setStartDate(undefined);
                    setEndDate(undefined);
                    setPage(1);
                  }}
                  className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground hover:text-foreground"
                  title="Clear date filter"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Loading */}
          {isLoading && (
            <div className="flex h-48 items-center justify-center gap-3">
              <RefreshCw className="h-5 w-5 animate-spin text-primary" />
              <span className="mono text-[11px] uppercase tracking-wider text-muted-foreground">
                Loading {symbol} history…
              </span>
            </div>
          )}

          {/* Table */}
          {!isLoading && (
            <div className="overflow-x-auto">
              <table className="mono w-full text-[12px]">
                <thead>
                  <tr className="border-b border-border bg-surface/40 text-[9px] uppercase tracking-wider text-muted-foreground">
                    <th className="px-4 py-2.5 text-left">
                      <button
                        onClick={() => { setSortDir(d => d === "desc" ? "asc" : "desc"); setPage(1); }}
                        className="flex items-center gap-1 hover:text-foreground transition-colors">
                        Timestamp <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </th>
                    <th className="px-3 py-2.5 text-right">Open</th>
                    <th className="px-3 py-2.5 text-right">High</th>
                    <th className="px-3 py-2.5 text-right">Low</th>
                    <th className="px-3 py-2.5 text-right">Close</th>
                    <th className="px-3 py-2.5 text-right">Change</th>
                    <th className="px-4 py-2.5 text-right">Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {paginated.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="h-32 text-center text-muted-foreground">
                        No records found
                      </td>
                    </tr>
                  ) : (
                    paginated.map((row, i) => {
                      const isUp   = row.c >= row.o;
                      const chg    = row.c - row.o;
                      const chgPct = (chg / row.o) * 100;
                      const date   = new Date(row.t);
                      const isPrefix = symbol.startsWith("XAG") || symbol.includes("USD") && !symbol.startsWith("BTC") && !symbol.startsWith("ETH") && !symbol.startsWith("XAU");
                      const prefix = symbol.startsWith("BTC") || symbol.startsWith("ETH") ? "$" : "";

                      return (
                        <tr key={i}
                          className="group border-b border-border/40 transition-colors hover:bg-surface-2/30">
                          {/* Timestamp */}
                          <td className="whitespace-nowrap px-4 py-2 text-muted-foreground">
                            <span className="text-foreground/70">
                              {date.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}
                            </span>
                            <span className="ml-2 text-muted-foreground/60">
                              {date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                            </span>
                          </td>
                          {/* OHLC */}
                          <td className="px-3 py-2 text-right tabular-nums text-foreground/70">{prefix}{fmt(row.o)}</td>
                          <td className="px-3 py-2 text-right tabular-nums text-bull">{prefix}{fmt(row.h)}</td>
                          <td className="px-3 py-2 text-right tabular-nums text-bear">{prefix}{fmt(row.l)}</td>
                          <td className={cn("px-3 py-2 text-right tabular-nums font-semibold", isUp ? "text-bull" : "text-bear")}>
                            {prefix}{fmt(row.c)}
                          </td>
                          {/* Change */}
                          <td className={cn("px-3 py-2 text-right tabular-nums", isUp ? "text-bull" : "text-bear")}>
                            <span className="flex items-center justify-end gap-1">
                              {isUp
                                ? <TrendingUp className="h-3 w-3 opacity-70" />
                                : <TrendingDown className="h-3 w-3 opacity-70" />}
                              {isUp ? "+" : ""}{chgPct.toFixed(2)}%
                            </span>
                          </td>
                          {/* Volume */}
                          <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">
                            {fmtVol(row.v)}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {!isLoading && pages > 1 && (
            <div className="flex items-center justify-between border-t border-border px-4 py-3">
              <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
                Page {page} of {pages} · {candles.length.toLocaleString()} rows
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                  className="mono rounded border border-border bg-surface px-2 py-1 text-[10px] text-muted-foreground disabled:opacity-40 hover:text-foreground">
                  First
                </button>
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="flex h-7 w-7 items-center justify-center rounded border border-border bg-surface text-muted-foreground disabled:opacity-40 hover:text-foreground">
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                {/* Page numbers */}
                {Array.from({ length: Math.min(5, pages) }, (_, i) => {
                  let p: number;
                  if (pages <= 5) {
                    p = i + 1;
                  } else if (page <= 3) {
                    p = i + 1;
                  } else if (page >= pages - 2) {
                    p = pages - 4 + i;
                  } else {
                    p = page - 2 + i;
                  }
                  return (
                    <button key={p} onClick={() => setPage(p)}
                      className={cn(
                        "mono h-7 w-7 rounded border text-[10px] transition-colors",
                        p === page
                          ? "border-primary/40 bg-primary/10 text-primary"
                          : "border-border bg-surface text-muted-foreground hover:text-foreground"
                      )}>
                      {p}
                    </button>
                  );
                })}
                <button
                  onClick={() => setPage(p => Math.min(pages, p + 1))}
                  disabled={page === pages}
                  className="flex h-7 w-7 items-center justify-center rounded border border-border bg-surface text-muted-foreground disabled:opacity-40 hover:text-foreground">
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setPage(pages)}
                  disabled={page === pages}
                  className="mono rounded border border-border bg-surface px-2 py-1 text-[10px] text-muted-foreground disabled:opacity-40 hover:text-foreground">
                  Last
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </TerminalLayout>
  );
};

export default History;