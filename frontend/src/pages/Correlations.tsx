import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { CorrelationHeatmap } from "@/components/terminal/CorrelationHeatmap";
import { TrendingUp, TrendingDown } from "lucide-react";

const TOP_POS = [
  { a: "XAU", b: "XAG", v: 0.82 },
  { a: "BTC", b: "ETH", v: 0.78 },
  { a: "EUR", b: "GBP", v: 0.64 },
  { a: "BTC", b: "XAU", v: 0.31 },
];
const TOP_NEG = [
  { a: "GBP", b: "XAU", v: -0.22 },
  { a: "EUR", b: "XAU", v: -0.18 },
  { a: "GBP", b: "XAG", v: -0.14 },
  { a: "EUR", b: "XAG", v: -0.11 },
];

const Correlations = () => {
  return (
    <TerminalLayout>
      <div className="space-y-4">
        <header>
          <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Workspace</p>
          <h1 className="text-[22px] font-semibold tracking-tight">Correlations & Analytics</h1>
        </header>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr]">
          <CorrelationHeatmap />
          <div className="space-y-4">
            <Pair title="Strongest positive" rows={TOP_POS} positive />
            <Pair title="Strongest negative" rows={TOP_NEG} positive={false} />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[
            { k: "MA7 / MA30 cross",     v: "0.31", note: "+12% MoM" },
            { k: "Realized volatility",  v: "0.22", note: "stable" },
            { k: "News sentiment 24h",   v: "0.19", note: "+4% MoM" },
            { k: "Cross-asset corr",     v: "0.14", note: "−2% MoM" },
          ].map((f) => (
            <div key={f.k} className="terminal-card p-4">
              <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">{f.k}</p>
              <p className="mono mt-2 text-[24px] font-semibold tabular-nums text-primary">{f.v}</p>
              <p className="mono mt-1 text-[10px] uppercase tracking-wider text-muted-foreground">{f.note}</p>
              <div className="mt-3 h-1 rounded-full bg-surface-2">
                <div className="h-full rounded-full bg-primary" style={{ width: `${parseFloat(f.v) * 250}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </TerminalLayout>
  );
};

const Pair = ({ title, rows, positive }: { title: string; rows: { a: string; b: string; v: number }[]; positive: boolean }) => {
  const Icon = positive ? TrendingUp : TrendingDown;
  return (
    <div className="terminal-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-[13px] font-semibold tracking-tight">{title}</h3>
        <Icon className={positive ? "h-4 w-4 text-bull" : "h-4 w-4 text-bear"} />
      </div>
      <ul className="space-y-2">
        {rows.map((r) => (
          <li key={`${r.a}-${r.b}`} className="flex items-center gap-3">
            <span className="mono w-[80px] text-[12px] font-medium tracking-tight">{r.a} / {r.b}</span>
            <div className="h-1.5 flex-1 rounded-full bg-surface-2 overflow-hidden">
              <div className={positive ? "h-full bg-bull" : "h-full bg-bear"} style={{ width: `${Math.abs(r.v) * 100}%` }} />
            </div>
            <span className={`mono w-[52px] text-right text-[11px] tabular-nums font-semibold ${positive ? "text-bull" : "text-bear"}`}>
              {r.v > 0 ? "+" : ""}{r.v.toFixed(2)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Correlations;
