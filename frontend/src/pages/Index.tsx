import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { MarketSummaryCards } from "@/components/terminal/MarketSummaryCards";
import { MainChart } from "@/components/terminal/MainChart";
import { IndicatorPanel } from "@/components/terminal/IndicatorPanel";
import { SignalCard } from "@/components/terminal/SignalCard";
import { SentimentPanel } from "@/components/terminal/SentimentPanel";
import { NewsPanel } from "@/components/terminal/NewsPanel";
import { StreamingPanel } from "@/components/terminal/StreamingPanel";
import { ASSETS } from "@/lib/market-data";
import { useAssets, useHistory, useLatestStream } from "@/lib/api";
import { useMemo, useState } from "react";



const Index = () => {
  const { data: assets, isLoading } = useAssets();

  // Use BTC/USD as the default asset for the home page chart
  const defaultSymbol = ASSETS.find((a) => a.symbol === "BTC/USD")?.symbol ?? ASSETS[0].symbol;
  const [selectedSymbol, setSelectedSymbol] = useState(defaultSymbol);
  const currentAsset = ASSETS.find((a) => a.symbol === selectedSymbol) ?? ASSETS[0];

  const { data: historyData = [] } = useHistory(selectedSymbol);
  const { data: stream } = useLatestStream();

  const latestTick = useMemo(() => {
    const normalize = (value: string) => value.replace(/[/_-]/g, "").toLowerCase();
    const symbolKey = normalize(selectedSymbol);
    return stream?.find((tick) => normalize(tick.symbol) === symbolKey) ?? null;
  }, [selectedSymbol, stream]);

  if (isLoading || !assets) {
    return (
      <TerminalLayout>
        <div className="flex h-[80vh] items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <p className="mono animate-pulse text-[12px] uppercase tracking-[0.2em] text-muted-foreground">Initialising Terminal...</p>
          </div>
        </div>
      </TerminalLayout>
    );
  }

  const breadth = assets.filter((a) => a.changePct >= 0).length;
  const total = assets.length;
  const avg = total > 0 ? assets.reduce((s, a) => s + a.changePct, 0) / total : 0;

  return (
    <TerminalLayout>
      <div className="space-y-4">
        {/* Full Width Top Section */}
        {/* Signature hero strip */}
        <section className="relative overflow-hidden rounded-xl border border-border bg-card hairline-top">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,hsl(190_95%_55%/0.18),transparent_55%),radial-gradient(ellipse_at_top_right,hsl(258_90%_66%/0.16),transparent_55%),radial-gradient(ellipse_at_bottom_right,hsl(42_95%_58%/0.10),transparent_55%)]" />
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />

          <div className="relative grid grid-cols-1 gap-4 p-5 md:grid-cols-4 md:items-center">
            <div className="md:col-span-2">
              <p className="mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">Today · multi-asset terminal</p>
              <h1 className="mt-1.5 text-[22px] font-semibold leading-tight tracking-tight">
                Markets are <span className={avg >= 0 ? "text-bull" : "text-bear"}>{avg >= 0 ? "expanding" : "compressing"}</span>{" "}
                <span className="text-muted-foreground">across</span>{" "}
                <span className="brand-mark">3 asset classes</span>
              </h1>
              <p className="mono mt-1 text-[11px] text-muted-foreground">
                Bronze→Silver→Gold pipelines · Kafka streaming · NLP sentiment · ensemble predictions
              </p>
            </div>
            <HeroStat label="Breadth" value={`${breadth}/${total}`} accent="text-bull" sub="advancing" />
            <HeroStat label="Avg Δ" value={`${avg >= 0 ? "+" : ""}${avg.toFixed(2)}%`} accent={avg >= 0 ? "text-bull" : "text-bear"} sub="cross-asset" />
          </div>
        </section>

        {/* Hero summary cards */}
        <MarketSummaryCards />

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_360px] xl:items-start">
  {/* LEFT COLUMN */}
  <div className="min-w-0 space-y-4">
    <div className="h-[550px]">
      <MainChart
        symbol={selectedSymbol}
        candles={historyData}
        livePrice={latestTick?.price ?? null}
        marketClass={currentAsset.class}
        assets={ASSETS}
        onAssetChange ={setSelectedSymbol}
      />
    </div>
    <IndicatorPanel />
      <div className="space-y-4">
    <StreamingPanel />
  </div>
  </div>
  

  {/* RIGHT STICKY RAIL */}
  <aside className="hidden xl:block xl:self-start">
<div className="sticky top-20 h-[1084px] overflow-y-auto space-y-4 pr-1">      <SignalCard />
      <SentimentPanel />
      <NewsPanel selectedSymbol={selectedSymbol} />
    </div>
  </aside>


</div>
</div>
    </TerminalLayout>
  );
};


const HeroStat = ({ label, value, accent, sub }: { label: string; value: string; accent: string; sub: string }) => (
  <div className="rounded-lg border border-border/70 bg-surface-2/40 p-3 backdrop-blur">
    <p className="mono text-[9.5px] uppercase tracking-[0.22em] text-muted-foreground">{label}</p>
    <p className={`mono mt-1 text-[20px] font-semibold leading-none num ${accent}`}>{value}</p>
    <p className="mono mt-1.5 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{sub}</p>
  </div>
);

export default Index;
