import { useEffect, useMemo, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { AssetImage } from "@/components/AssetImage";
import {
  Maximize2, Settings2, Camera, Crosshair,
  LineChart as LineIcon, CandlestickChart, Activity,
  Bell, Plus, Check,
} from "lucide-react";

const TIMEFRAMES = ["1m", "5m", "15m", "1H", "4H", "1D", "1W"];
const CHART_TYPES = [
  { id: "candles", icon: CandlestickChart, label: "Candles" },
  { id: "line",    icon: LineIcon,         label: "Line"    },
  { id: "area",    icon: Activity,         label: "Area"    },
];
const ALL_INDICATORS = [
  { id: "ma7",    label: "MA 7",            color: "text-metals"           },
  { id: "ma30",   label: "MA 30",           color: "text-forex"            },
  { id: "volume", label: "Volume",          color: "text-muted-foreground" },
  { id: "bb",     label: "Bollinger Bands", color: "text-primary"          },
  { id: "vwap",   label: "VWAP",            color: "text-bull"             },
];

type Candle = { t: string; o: number; h: number; l: number; c: number; v: number };
type AssetOption = { symbol: string; marketClass?: "crypto" | "forex" | "metals" };

type MainChartRealProps = {
  symbol?: string;
  candles?: Candle[];
  livePrice?: number | null;
  marketClass?: "crypto" | "forex" | "metals";
  assets?: AssetOption[];
  selectedSymbol?: string;
  onAssetChange?: (symbol: string) => void;
};

const VISIBLE_CANDLES = 31;

export const MainChart = ({
  symbol = "BTC/USD",
  candles: rawCandles = [],
  livePrice = null,
  marketClass = "crypto",
  assets,
  selectedSymbol,
  onAssetChange,
}: MainChartRealProps) => {
  // ── UI state ──────────────────────────────────────────────────────────────
  const [tf,                setTf]               = useState("1D");
  const [chartType,         setChartType]        = useState("candles");
  const [offset,            setOffset]           = useState(0);
  const [hover,             setHover]            = useState<{ i: number; x: number; y: number } | null>(null);
  const [crosshair,         setCrosshair]        = useState(true);
  const [fullscreen,        setFullscreen]       = useState(false);
  const [alertPx,           setAlertPx]          = useState<number | null>(null);
  const [toast,             setToast]            = useState<string | null>(null);
  const [showSettings,      setShowSettings]     = useState(false);
  const [showIndicatorMenu, setShowIndicatorMenu]= useState(false);
  const [enabled,           setEnabled]          = useState<Record<string, boolean>>({
    ma7: true, ma30: true, volume: true, bb: false, vwap: false,
  });

  const dragRef = useRef<{ x: number; offset: number } | null>(null);
  const svgRef  = useRef<SVGSVGElement>(null);

  // ── Candle processing ─────────────────────────────────────────────────────
  const candles = useMemo(() =>
    [...(rawCandles || [])]
      .filter((c) => c?.t && Number.isFinite(c.o) && Number.isFinite(c.h) && Number.isFinite(c.l) && Number.isFinite(c.c))
      .sort((a, b) => new Date(a.t).getTime() - new Date(b.t).getTime()),
  [rawCandles]);

  const maxOffset = Math.max(0, candles.length - VISIBLE_CANDLES);

  useEffect(() => { setOffset(0); setHover(null); }, [symbol, tf]);
  useEffect(() => { if (offset > maxOffset) setOffset(maxOffset); }, [offset, maxOffset]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setFullscreen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const start          = Math.max(0, candles.length - VISIBLE_CANDLES - offset);
  const visibleCandles = candles.slice(start, start + VISIBLE_CANDLES);

  // ── Indicators ────────────────────────────────────────────────────────────
  const { min, max, ma7, ma30, vMax, bbU, bbL, vwap } = useMemo(() => {
    if (!visibleCandles.length)
      return { min: 0, max: 1, ma7: [] as number[], ma30: [] as number[], vMax: 1, bbU: [] as number[], bbL: [] as number[], vwap: [] as number[] };

    let mn = Infinity, mx = -Infinity, vmx = 0;
    for (const c of visibleCandles) {
      if (c.l < mn) mn = c.l;
      if (c.h > mx) mx = c.h;
      if (c.v > vmx) vmx = c.v;
    }
    const pad    = Math.max((mx - mn) * 0.08, 0.0001);
    const closes = visibleCandles.map((c) => c.c);

    const m7  = closes.map((_, i) => { const w = closes.slice(Math.max(0, i - 6),  i + 1); return w.reduce((a, b) => a + b, 0) / w.length; });
    const m30 = closes.map((_, i) => { const w = closes.slice(Math.max(0, i - 29), i + 1); return w.reduce((a, b) => a + b, 0) / w.length; });

    // Bollinger (20, 2)
    const bU: number[] = [], bL: number[] = [];
    closes.forEach((_, i) => {
      const w    = closes.slice(Math.max(0, i - 19), i + 1);
      const mean = w.reduce((a, b) => a + b, 0) / w.length;
      const sd   = Math.sqrt(w.reduce((a, b) => a + (b - mean) ** 2, 0) / w.length);
      bU.push(mean + 2 * sd); bL.push(mean - 2 * sd);
    });

    // VWAP
    let cumPV = 0, cumV = 0;
    const vw = visibleCandles.map((c) => {
      cumPV += ((c.h + c.l + c.c) / 3) * c.v; cumV += c.v;
      return cumPV / (cumV || 1);
    });

    return { min: mn - pad, max: mx + pad, ma7: m7, ma30: m30, vMax: vmx || 1, bbU: bU, bbL: bL, vwap: vw };
  }, [visibleCandles]);

  // ── Layout ────────────────────────────────────────────────────────────────
  const W       = 1000;
  const H       = 360;
  const VOL_H   = enabled.volume ? 70 : 0;
  const GAP     = enabled.volume ? 8  : 0;
  const PRICE_H = H - VOL_H - GAP;
  const PAD_R   = 64;
  const innerW  = W - PAD_R;
  const N       = visibleCandles.length || 1;
  const slot    = innerW / N;
  const cw      = Math.max(2, slot * 0.7);

  const yPrice = (p: number) => ((max - p) / (max - min || 1)) * PRICE_H;
  const yVol   = (v: number) => PRICE_H + GAP + (1 - v / vMax) * VOL_H;

  const last             = visibleCandles[visibleCandles.length - 1];
  const displayLastClose = livePrice && livePrice > 0 ? livePrice : last?.c ?? 0;
  const hovered          = hover ? visibleCandles[hover.i] : last;
  const up               = displayLastClose >= (last?.o ?? displayLastClose);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!crosshair || !visibleCandles.length) { setHover(null); return; }
    const r = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width)  * W;
    const y = ((e.clientY - r.top)  / r.height) * H;
    if (x > innerW) { setHover(null); return; }
    setHover({ i: Math.min(N - 1, Math.max(0, Math.floor(x / slot))), x, y });
  };

  const onPointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    dragRef.current = { x: e.clientX, offset };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!dragRef.current) return;
    const candleDelta = Math.round(-(e.clientX - dragRef.current.x) / 18);
    setOffset(Math.min(maxOffset, Math.max(0, dragRef.current.offset + candleDelta)));
  };
  const onPointerUp = (e: React.PointerEvent<SVGSVGElement>) => {
    dragRef.current = null;
    try { e.currentTarget.releasePointerCapture(e.pointerId); } catch {}
  };

  // ── Ticks ─────────────────────────────────────────────────────────────────
  const yTicks = useMemo(() => {
    const ticks: number[] = [];
    const step = (max - min) / 6 || 1;
    for (let i = 0; i <= 6; i++) ticks.push(min + step * i);
    return ticks;
  }, [min, max]);

  const xTicks = useMemo(() => {
    if (!visibleCandles.length) return [];
    const step = Math.max(1, Math.ceil(visibleCandles.length / 7));
    return Array.from({ length: Math.floor(visibleCandles.length / step) }, (_, k) => {
      const i = k * step;
      const d = new Date(visibleCandles[i].t);
      return { i, label: d.toLocaleDateString([], { month: "short", day: "numeric" }) };
    });
  }, [visibleCandles]);

  const fmt = (n: number) =>
    n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  // ── Toolbar actions ───────────────────────────────────────────────────────
  const flash = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2200);
  };

  const snapshot = () => {
    const svg = svgRef.current;
    if (!svg) return;
    const xml   = new XMLSerializer().serializeToString(svg);
    const svg64 = btoa(unescape(encodeURIComponent(xml)));
    const img   = new Image();
    img.onload  = () => {
      const canvas = document.createElement("canvas");
      canvas.width = W * 2; canvas.height = H * 2;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = "#000";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      const a = document.createElement("a");
      a.download = `${symbol.replace("/", "-")}_${Date.now()}.png`;
      a.href = canvas.toDataURL("image/png");
      a.click();
      flash("Snapshot saved");
    };
    img.src = `data:image/svg+xml;base64,${svg64}`;
  };

  const placeAlert = () => {
    if (!hover) { flash("Hover the chart first, then click Bell"); return; }
    const px = min + (1 - hover.y / PRICE_H) * (max - min);
    setAlertPx(px);
    flash(`Alert set at ${fmt(px)}`);
  };

  // ── Empty state ───────────────────────────────────────────────────────────
  if (!visibleCandles.length) {
    return (
      <div className="terminal-card flex h-full items-center justify-center bg-background text-sm text-muted-foreground">
        No chart data available
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className={cn(
      "terminal-card flex h-full flex-col overflow-hidden bg-background",
      fullscreen && "fixed inset-3 z-50 h-auto shadow-2xl"
    )}>

      {/* ── Top bar ───────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 border-b border-border bg-surface/60 px-3 py-2">
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-1.5 rounded-md border border-border bg-surface-2 px-2 py-1 hover:bg-surface-3">
            <AssetImage symbol={symbol} size="xs" showBorder={false} />
            <span className="mono text-[12px] font-semibold tracking-tight">{symbol}</span>
          </button>

        </div>

        {/* OHLC strip */}
        <div className="mono hidden items-center gap-3 text-[11px] md:flex">
          <span className="text-muted-foreground">O <span className={cn(hovered?.c >= hovered?.o ? "text-bull" : "text-bear")}>{fmt(hovered?.o ?? 0)}</span></span>
          <span className="text-muted-foreground">H <span className="text-bull">{fmt(hovered?.h ?? 0)}</span></span>
          <span className="text-muted-foreground">L <span className="text-bear">{fmt(hovered?.l ?? 0)}</span></span>
          <span className="text-muted-foreground">C <span className={cn(hovered?.c >= hovered?.o ? "text-bull" : "text-bear")}>{fmt(hovered?.c ?? 0)}</span></span>
          <span className={cn("text-[11px]", hovered?.c >= hovered?.o ? "text-bull" : "text-bear")}>
            {hovered?.c >= hovered?.o ? "+" : ""}
            {((hovered?.c ?? 0) - (hovered?.o ?? 0)).toFixed(2)}
            {" "}({(((hovered?.c ?? 0) - (hovered?.o ?? 0)) / (hovered?.o || 1) * 100).toFixed(2)}%)
          </span>
        </div>

        {/* Right controls */}
        <div className="ml-auto flex items-center gap-1">
          {CHART_TYPES.map((t) => (
            <button key={t.id} onClick={() => setChartType(t.id)} title={t.label}
              className={cn("flex h-7 w-7 items-center justify-center rounded border transition-colors",
                chartType === t.id
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-border bg-surface text-muted-foreground hover:text-foreground")}>
              <t.icon className="h-3.5 w-3.5" />
            </button>
          ))}

          <button onClick={() => setOffset(0)}
            className="mono hidden rounded border border-border bg-surface px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground sm:inline-flex">
            Last month
          </button>

          <div className="mx-1 h-5 w-px bg-border" />

          {/* Crosshair toggle */}
          <ToolBtn active={crosshair} onClick={() => setCrosshair(v => !v)} title="Toggle crosshair">
            <Crosshair className="h-3.5 w-3.5" />
          </ToolBtn>

          {/* Bell — place price alert */}
          <ToolBtn active={alertPx !== null} onClick={placeAlert} title="Set price alert">
            <Bell className="h-3.5 w-3.5" />
          </ToolBtn>

          {/* Camera — snapshot PNG */}
          <ToolBtn onClick={snapshot} title="Save snapshot as PNG">
            <Camera className="h-3.5 w-3.5" />
          </ToolBtn>

          {/* Settings — indicator toggles */}
          <div className="relative">
            <ToolBtn
              active={showSettings}
              onClick={() => { setShowSettings(v => !v); setShowIndicatorMenu(false); }}
              title="Indicator settings"
            >
              <Settings2 className="h-3.5 w-3.5" />
            </ToolBtn>
            {showSettings && (
              <div className="absolute right-0 top-9 z-30 w-52 rounded-lg border border-border bg-popover p-2 shadow-elevated">
                <p className="mono mb-1 px-1 text-[9px] uppercase tracking-wider text-muted-foreground">Overlays</p>
                {ALL_INDICATORS.map((ind) => (
                  <button key={ind.id}
                    onClick={() => setEnabled(e => ({ ...e, [ind.id]: !e[ind.id] }))}
                    className="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-[12px] hover:bg-surface-2">
                    <span className={cn(ind.color)}>{ind.label}</span>
                    {enabled[ind.id] && <Check className="h-3.5 w-3.5 text-primary" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Fullscreen */}
          <ToolBtn active={fullscreen} onClick={() => setFullscreen(v => !v)} title="Toggle fullscreen">
            <Maximize2 className="h-3.5 w-3.5" />
          </ToolBtn>
        </div>
      </div>

      {/* ── Toolbar ───────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border bg-surface/40 px-3 py-1.5">
        {/* Timeframes */}
        <div className="flex items-center gap-0.5">
          {TIMEFRAMES.map((t) => (
            <button key={t} onClick={() => setTf(t)}
              className={cn("mono rounded px-2 py-1 text-[10px] font-medium uppercase tracking-wider transition-colors",
                tf === t ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-surface-2 hover:text-foreground")}>
              {t}
            </button>
          ))}
        </div>
        <div className="mx-1 h-4 w-px bg-border" />

        {/* Active indicators — click to remove */}
        <div className="flex items-center gap-1">
          {ALL_INDICATORS.filter(i => enabled[i.id]).map(ind => (
            <button key={ind.id}
              onClick={() => setEnabled(e => ({ ...e, [ind.id]: false }))}
              title="Click to remove"
              className={cn("mono rounded border border-border bg-surface px-2 py-1 text-[10px] font-medium uppercase tracking-wider hover:border-bear/40 hover:text-bear", ind.color)}>
              {ind.label}
            </button>
          ))}

          {/* + Indicator picker */}
          <div className="relative">
            <button
              onClick={() => { setShowIndicatorMenu(v => !v); setShowSettings(false); }}
              className="mono rounded border border-dashed border-border bg-transparent px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground hover:text-foreground">
              + Indicator
            </button>
            {showIndicatorMenu && (
              <div className="absolute left-0 top-9 z-30 w-52 rounded-lg border border-border bg-popover p-2 shadow-elevated">
                {ALL_INDICATORS.map(ind => (
                  <button key={ind.id}
                    onClick={() => setEnabled(e => ({ ...e, [ind.id]: !e[ind.id] }))}
                    className="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-[12px] hover:bg-surface-2">
                    <span className={cn(ind.color)}>{ind.label}</span>
                    {enabled[ind.id] && <Check className="h-3.5 w-3.5 text-primary" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="ml-auto rounded border border-border bg-surface/80 px-2 py-1">
          <span className="mono text-[9px] uppercase tracking-wider text-muted-foreground">
            {offset === 0 ? "Last 31 candles" : `${offset} candles back`} · drag left for history
          </span>
        </div>
      </div>

      {/* Asset tabs (optional) */}
      {assets?.length ? (
        <div className="flex items-center gap-2 border-b border-border bg-surface/40 px-3 py-2">
          {assets.map((asset) => {
            const isActive = asset.symbol.toLowerCase() === selectedSymbol?.toLowerCase();
            return (
              <button key={asset.symbol} type="button"
                onClick={() => onAssetChange?.(asset.symbol)}
                className={cn("mono flex items-center gap-1.5 rounded border px-2 py-1 text-[10px] font-medium uppercase tracking-wider transition-colors",
                  isActive
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-surface text-muted-foreground hover:border-primary hover:text-foreground")}>
                <AssetImage symbol={asset.symbol} size="xxs" showBorder={false} />
                {asset.symbol}
              </button>
            );
          })}
        </div>
      ) : null}

      {/* ── Chart SVG ─────────────────────────────────────────────────────── */}
      <div className="relative flex-1 touch-pan-y bg-background">
        <svg ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="h-full w-full cursor-grab active:cursor-grabbing"
          onMouseMove={onMove}
          onMouseLeave={() => setHover(null)}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          {/* Grid */}
          {yTicks.map((p, i) => (
            <line key={`gh-${i}`} x1={0} x2={innerW} y1={yPrice(p)} y2={yPrice(p)}
              stroke="hsl(var(--grid-line))" strokeWidth={0.5} strokeDasharray="2 4" />
          ))}
          {xTicks.map((t) => (
            <line key={`gv-${t.i}`} x1={t.i * slot + cw / 2} x2={t.i * slot + cw / 2}
              y1={0} y2={PRICE_H} stroke="hsl(var(--grid-line))" strokeWidth={0.5} strokeDasharray="2 4" />
          ))}

          {/* Bollinger bands */}
          {enabled.bb && bbU.length > 0 && (
            <>
              <polygon
                points={`${bbU.map((v, i) => `${i * slot + slot / 2},${yPrice(v)}`).join(" ")} ${bbL.map((v, i) => `${i * slot + slot / 2},${yPrice(v)}`).reverse().join(" ")}`}
                fill="hsl(var(--primary))" opacity={0.06} />
              <polyline points={bbU.map((v, i) => `${i * slot + slot / 2},${yPrice(v)}`).join(" ")}
                fill="none" stroke="hsl(var(--primary))" strokeWidth={0.8} opacity={0.6} />
              <polyline points={bbL.map((v, i) => `${i * slot + slot / 2},${yPrice(v)}`).join(" ")}
                fill="none" stroke="hsl(var(--primary))" strokeWidth={0.8} opacity={0.6} />
            </>
          )}

          {/* Volume */}
          {enabled.volume && visibleCandles.map((c, i) => {
            const x  = i * slot + (slot - cw) / 2;
            const y  = yVol(c.v);
            const bh = PRICE_H + GAP + VOL_H - y;
            return (
              <rect key={`v-${i}`} x={x} y={y} width={cw} height={Math.max(1, bh)}
                fill={c.c >= c.o ? "hsl(var(--bull))" : "hsl(var(--bear))"} opacity={0.35} />
            );
          })}

          {/* Candles */}
          {chartType === "candles" && visibleCandles.map((c, i) => {
            const x     = i * slot + slot / 2;
            const isUp  = c.c >= c.o;
            const color = isUp ? "hsl(var(--bull))" : "hsl(var(--bear))";
            const bodyT = yPrice(Math.max(c.o, c.c));
            const bodyB = yPrice(Math.min(c.o, c.c));
            return (
              <g key={`c-${i}`}>
                <line x1={x} x2={x} y1={yPrice(c.h)} y2={yPrice(c.l)} stroke={color} strokeWidth={1} />
                <rect x={x - cw / 2} y={bodyT} width={cw} height={Math.max(1, bodyB - bodyT)}
                  fill={color} stroke={color} />
              </g>
            );
          })}

          {/* Line / Area */}
          {(chartType === "line" || chartType === "area") && (() => {
            const pts = visibleCandles.map((c, i) => `${i * slot + slot / 2},${yPrice(c.c)}`).join(" ");
            return (
              <>
                {chartType === "area" && (
                  <>
                    <defs>
                      <linearGradient id="areaFillReal" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="hsl(var(--primary))" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0}    />
                      </linearGradient>
                    </defs>
                    <polygon points={`0,${PRICE_H} ${pts} ${innerW},${PRICE_H}`} fill="url(#areaFillReal)" />
                  </>
                )}
                <polyline points={pts} fill="none" stroke="hsl(var(--primary))" strokeWidth={1.6} />
              </>
            );
          })()}

          {/* MA7 */}
          {enabled.ma7 && (
            <polyline points={ma7.map((v, i) => `${i * slot + slot / 2},${yPrice(v)}`).join(" ")}
              fill="none" stroke="hsl(var(--metals))" strokeWidth={1.2} opacity={0.9} />
          )}
          {/* MA30 */}
          {enabled.ma30 && (
            <polyline points={ma30.map((v, i) => `${i * slot + slot / 2},${yPrice(v)}`).join(" ")}
              fill="none" stroke="hsl(var(--forex))" strokeWidth={1.2} strokeDasharray="3 3" opacity={0.9} />
          )}
          {/* VWAP */}
          {enabled.vwap && (
            <polyline points={vwap.map((v, i) => `${i * slot + slot / 2},${yPrice(v)}`).join(" ")}
              fill="none" stroke="hsl(var(--bull))" strokeWidth={1.2} strokeDasharray="5 2" opacity={0.85} />
          )}

          {/* Last price dashed line */}
          <line x1={0} x2={innerW} y1={yPrice(displayLastClose)} y2={yPrice(displayLastClose)}
            stroke={up ? "hsl(var(--bull))" : "hsl(var(--bear))"}
            strokeWidth={0.8} strokeDasharray="3 3" opacity={0.7} />

          {/* Alert line */}
          {alertPx !== null && alertPx >= min && alertPx <= max && (
            <g>
              <line x1={0} x2={innerW} y1={yPrice(alertPx)} y2={yPrice(alertPx)}
                stroke="hsl(var(--metals))" strokeWidth={0.8} strokeDasharray="2 2" />
              <rect x={innerW + 2} y={yPrice(alertPx) - 8} width={PAD_R - 4} height={16} rx={2}
                fill="hsl(var(--metals))" />
              <text x={innerW + 6} y={yPrice(alertPx) + 3}
                fill="black" fontSize={9} fontFamily="JetBrains Mono" fontWeight={700}>
                {fmt(alertPx)}
              </text>
            </g>
          )}

          {/* Y-axis */}
          <rect x={innerW} y={0} width={PAD_R} height={H} fill="hsl(var(--background))" />
          {yTicks.map((p, i) => (
            <text key={`yt-${i}`} x={innerW + 6} y={yPrice(p) + 3}
              fill="hsl(var(--muted-foreground))" fontSize={9} fontFamily="JetBrains Mono">
              {fmt(p)}
            </text>
          ))}
          <g>
            <rect x={innerW + 2} y={yPrice(displayLastClose) - 8} width={PAD_R - 4} height={16} rx={2}
              fill={up ? "hsl(var(--bull))" : "hsl(var(--bear))"} />
            <text x={innerW + 6} y={yPrice(displayLastClose) + 3}
              fill="white" fontSize={9} fontFamily="JetBrains Mono" fontWeight={600}>
              {fmt(displayLastClose)}
            </text>
          </g>

          {/* X-axis */}
          <line x1={0} x2={innerW} y1={PRICE_H} y2={PRICE_H} stroke="hsl(var(--border))" strokeWidth={0.5} />
          {xTicks.map((t) => (
            <text key={`xt-${t.i}`} x={t.i * slot + slot / 2} y={H - 4}
              fill="hsl(var(--muted-foreground))" fontSize={9} fontFamily="JetBrains Mono"
              textAnchor="middle">
              {t.label}
            </text>
          ))}

          {/* Crosshair */}
          {crosshair && hover && (
            <g pointerEvents="none">
              <line x1={hover.i * slot + slot / 2} x2={hover.i * slot + slot / 2}
                y1={0} y2={H - 14}
                stroke="hsl(var(--muted-foreground))" strokeWidth={0.6} strokeDasharray="3 3" />
              <line x1={0} x2={innerW} y1={hover.y} y2={hover.y}
                stroke="hsl(var(--muted-foreground))" strokeWidth={0.6} strokeDasharray="3 3" />
              {hover.y < PRICE_H && (
                <g>
                  <rect x={innerW + 2} y={hover.y - 8} width={PAD_R - 4} height={16} rx={2}
                    fill="hsl(var(--surface-3))" stroke="hsl(var(--border))" />
                  <text x={innerW + 6} y={hover.y + 3}
                    fill="hsl(var(--foreground))" fontSize={9} fontFamily="JetBrains Mono">
                    {fmt(min + (1 - hover.y / PRICE_H) * (max - min))}
                  </text>
                </g>
              )}
            </g>
          )}
        </svg>

        {/* Watermark */}
        <div className="pointer-events-none absolute bottom-8 left-4 mono text-[42px] font-bold uppercase tracking-tight text-foreground/[0.04]">
          {symbol}
        </div>

        {/* Live badge */}
        <div className="absolute right-20 top-2 flex items-center gap-1.5 rounded border border-bull/30 bg-bull/10 px-2 py-0.5">
          <span className="pulse-dot bg-bull" />
          <span className="mono text-[9px] uppercase tracking-wider text-bull">live</span>
        </div>

        {/* Navigation hint */}
        <div className="absolute bottom-2 left-4 rounded border border-border bg-surface/80 px-2 py-1">
          <span className="mono text-[9px] uppercase tracking-wider text-muted-foreground">
            {offset === 0 ? "Last 31 candles" : `${offset} candles back`} · drag left for history
          </span>
        </div>

        {/* Toast */}
        {toast && (
          <div className="animate-fade-in absolute bottom-2 right-4 rounded border border-primary/40 bg-primary/10 px-3 py-1.5">
            <span className="mono text-[10px] uppercase tracking-wider text-primary">{toast}</span>
          </div>
        )}
      </div>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-4 border-t border-border bg-surface/40 px-3 py-1.5">
        <Legend color="hsl(var(--bull))"  label="Bull" swatch="square" />
        <Legend color="hsl(var(--bear))"  label="Bear" swatch="square" />
        {enabled.ma7   && <Legend color="hsl(var(--metals))"  label="MA7"      />}
        {enabled.ma30  && <Legend color="hsl(var(--forex))"   label="MA30" dashed />}
        {enabled.vwap  && <Legend color="hsl(var(--bull))"    label="VWAP" dashed />}
        {enabled.bb    && <Legend color="hsl(var(--primary))" label="BB(20,2)" />}
        <span className="mono ml-auto text-[10px] uppercase tracking-wider text-muted-foreground">
          real data · default view = last month · drag/swipe for older candles
        </span>
      </div>
    </div>
  );
};

// ─── Sub-components ───────────────────────────────────────────────────────────
const ToolBtn = ({
  children, onClick, title, active,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  title?: string;
  active?: boolean;
}) => (
  <button onClick={onClick} title={title}
    className={cn("flex h-7 w-7 items-center justify-center rounded border transition-colors",
      active
        ? "border-primary/40 bg-primary/10 text-primary"
        : "border-border bg-surface text-muted-foreground hover:text-foreground")}>
    {children}
  </button>
);

const Legend = ({
  color, label, dashed, swatch,
}: {
  color: string; label: string; dashed?: boolean; swatch?: "line" | "square";
}) => (
  <div className="flex items-center gap-1.5">
    {swatch === "square" ? (
      <span className="inline-block h-2 w-2 rounded-sm" style={{ background: color }} />
    ) : (
      <span className="inline-block h-0.5 w-4"
        style={{ background: dashed ? "transparent" : color, borderTop: dashed ? `1.5px dashed ${color}` : undefined }} />
    )}
    <span className="mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
  </div>
);