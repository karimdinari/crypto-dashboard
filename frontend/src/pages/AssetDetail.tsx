import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { MainChart } from "@/components/terminal/MainChart";
import { IndicatorPanel } from "@/components/terminal/IndicatorPanel";
import { NewsPanel } from "@/components/terminal/NewsPanel";
import { SignalCard } from "@/components/terminal/SignalCard";
import { SentimentPanel } from "@/components/terminal/SentimentPanel";
import { AssetImage } from "@/components/AssetImage";
import { ASSETS } from "@/lib/market-data";
import { useHistory, useLatestStream } from "@/lib/api";
import { useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";

const AssetDetail = () => {
  const { symbol } = useParams();
  const a = ASSETS.find((x) => x.symbol.toLowerCase() === symbol?.toLowerCase()) ?? ASSETS[0];

  const navigate = useNavigate();
  const { data: historyData = [] } = useHistory(a.symbol);
  const { data: stream } = useLatestStream();

  const latestTick = useMemo(() => {
    const normalize = (value: string) => value.replace(/[/_-]/g, "").toLowerCase();
    const symbolKey = normalize(a.symbol);
    return stream?.find((tick) => normalize(tick.symbol) === symbolKey) ?? null;
  }, [a.symbol, stream]);

  return (
    <TerminalLayout>
      <div className="space-y-4">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex items-end gap-4">
            <AssetImage symbol={a.symbol} name={a.name} size="lg" />
            <div>
              <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Asset detail</p>
              <h1 className="text-[22px] font-semibold tracking-tight">{a.symbol} <span className="text-muted-foreground">· {a.name}</span></h1>
            </div>
          </div>
          <div className="flex items-center gap-2 mono text-[11px] text-muted-foreground">
            <span className="rounded border border-border bg-surface px-2 py-1">Class · {a.class}</span>
            <span className="rounded border border-border bg-surface px-2 py-1">Universe · G10 + Top-20</span>
            <span className="rounded border border-border bg-surface px-2 py-1">Updated · live</span>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
          <div className="space-y-4">
            <div className="h-[520px]">
              <MainChart
                assets={ASSETS}
                selectedSymbol={a.symbol}
                symbol={a.symbol}
                candles={historyData}
                livePrice={latestTick?.price ?? null}
                marketClass={a.class}
                onAssetChange={(symbol) => navigate(`/asset/${encodeURIComponent(symbol)}`)}
              />
            </div>
            <IndicatorPanel />
          </div>
          <div className="space-y-4">
            <SignalCard />
            <SentimentPanel />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2 terminal-card p-4">
            <h3 className="text-[13px] font-semibold tracking-tight">Indicator history (30d)</h3>
            <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground mb-3">Returns · MA7 · MA30 · Volatility · Δprice</p>
            <table className="mono w-full text-[11px]">
              <thead>
                <tr className="text-[9px] uppercase tracking-wider text-muted-foreground">
                  <th className="px-2 py-2 text-left">Date</th>
                  <th className="px-2 py-2 text-right">Close</th>
                  <th className="px-2 py-2 text-right">Return</th>
                  <th className="px-2 py-2 text-right">MA7</th>
                  <th className="px-2 py-2 text-right">MA30</th>
                  <th className="px-2 py-2 text-right">σ</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 10 }).map((_, i) => {
                  const ret = +(Math.random() * 4 - 1.5).toFixed(2);
                  const up = ret >= 0;
                  return (
                    <tr key={i} className="border-t border-border/50">
                      <td className="px-2 py-1.5 text-muted-foreground">2026-04-{String(20 - i).padStart(2,"0")}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums">{(a.price * (1 + (Math.random()-0.5)*0.04)).toFixed(2)}</td>
                      <td className={`px-2 py-1.5 text-right tabular-nums font-medium ${up ? "text-bull" : "text-bear"}`}>{up?"+":""}{ret}%</td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-muted-foreground">{(a.price * 0.998).toFixed(2)}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-muted-foreground">{(a.price * 0.992).toFixed(2)}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-metals">{(Math.random()*1.5+0.5).toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <NewsPanel selectedSymbol={a.symbol} />
        </div>
      </div>
    </TerminalLayout>
  );
};

export default AssetDetail;
