import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { CorrelationHeatmap } from "@/components/terminal/CorrelationHeatmap";
import { useCorrelations } from "@/lib/api";
import { useMemo, useState } from "react";
import { TrendingUp, TrendingDown, Minus, Info, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Symbol display names ──────────────────────────────────────────────────────
const SYMBOL_NAMES: Record<string, string> = {
  "BTC/USD": "Bitcoin",
  "ETH/USD": "Ethereum",
  "XAU/USD": "Gold",
  "XAG/USD": "Silver",
  "EUR/USD": "Euro",
  "GBP/USD": "GBP",
};

const FEATURE_DRIVERS = [
  { k: "MA7 / MA30 cross",    v: 0.31, desc: "Short-term vs long-term moving average crossover signal" },
  { k: "Realized volatility", v: 0.22, desc: "How much prices swung in the past 30 days"              },
  { k: "News sentiment 24h",  v: 0.19, desc: "Average NLP score of news articles in the last 24 hours"},
  { k: "Cross-asset corr",    v: 0.14, desc: "How closely all assets move together"                   },
];

// ── Helpers ───────────────────────────────────────────────────────────────────
function shortName(symbol: string): string {
  return symbol.replace("/USD", "").replace("/", "");
}

function fullName(symbol: string): string {
  return SYMBOL_NAMES[symbol] ?? shortName(symbol);
}

function getLabel(v: number) {
  if (v >= 0.8)  return { text: "Move together almost always", emoji: "🔗", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" };
  if (v >= 0.6)  return { text: "Usually move together",       emoji: "↗",  color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" };
  if (v >= 0.3)  return { text: "Somewhat related",            emoji: "〜", color: "text-yellow-400",  bg: "bg-yellow-500/10 border-yellow-500/20"  };
  if (v >= 0.1)  return { text: "Weakly related",              emoji: "·",  color: "text-zinc-400",    bg: "bg-zinc-500/10 border-zinc-500/20"      };
  if (v > -0.1)  return { text: "No real relationship",        emoji: "○",  color: "text-zinc-500",    bg: "bg-zinc-500/10 border-zinc-500/20"      };
  if (v >= -0.3) return { text: "Slightly opposite",           emoji: "↙",  color: "text-orange-400",  bg: "bg-orange-500/10 border-orange-500/20"  };
  return         { text: "Often move opposite",                emoji: "↔",  color: "text-red-400",     bg: "bg-red-500/10 border-red-500/20"        };
}

function getStrength(v: number): string {
  const a = Math.abs(v);
  if (a >= 0.8) return "Very Strong";
  if (a >= 0.6) return "Strong";
  if (a >= 0.4) return "Moderate";
  if (a >= 0.2) return "Weak";
  return "Negligible";
}

function getTip(aFull: string, bFull: string, v: number): string {
  const abs = Math.abs(v);
  const dir = v > 0 ? "same direction" : "opposite directions";
  if (abs >= 0.7)
    return `When ${aFull} goes up, ${bFull} almost always goes up too. They move in the ${dir}. Holding both offers little diversification.`;
  if (abs >= 0.4)
    return `${aFull} and ${bFull} often move in the ${dir}, but not always. There is some diversification benefit to holding both.`;
  if (abs <= 0.15)
    return `${aFull} and ${bFull} move independently of each other. Holding both is a good way to spread risk.`;
  return `${aFull} and ${bFull} tend to move in ${dir}. The relationship is ${getStrength(v).toLowerCase()}.`;
}

// ── Main page ─────────────────────────────────────────────────────────────────
const Correlations = () => {
  const { data: raw = [], isLoading } = useCorrelations();
  const [showMatrix,   setShowMatrix]   = useState(false);
  const [expandedPair, setExpandedPair] = useState<string | null>(null);

  // Normalise + sort by absolute correlation descending
  const pairs = useMemo(() =>
    [...raw]
      .filter(p => p.symbol_1 !== p.symbol_2)
      .map(p => ({
        key:    `${p.symbol_1}__${p.symbol_2}`,
        s1:     p.symbol_1,
        s2:     p.symbol_2,
        a:      shortName(p.symbol_1),
        b:      shortName(p.symbol_2),
        aFull:  fullName(p.symbol_1),
        bFull:  fullName(p.symbol_2),
        v:      Number(p.correlation_value.toFixed(3)),
      }))
      .sort((a, b) => b.v - a.v),
  [raw]);

  const positive = pairs.filter(p => p.v >= 0.1);
  const negative = pairs.filter(p => p.v < -0.1);
  const neutral  = pairs.filter(p => p.v >= -0.1 && p.v < 0.1);

  return (
    <TerminalLayout>
      <div className="space-y-6">

        {/* Hero */}
        <section className="relative overflow-hidden rounded-xl border border-border bg-card p-5">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,hsl(var(--primary)/0.12),transparent_55%)]" />
          <div className="relative">
            <p className="mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
              Correlations · Plain English · {pairs.length} pairs
            </p>
            <h1 className="mt-1.5 text-[22px] font-semibold leading-tight tracking-tight">
              How do your assets move together?
            </h1>
            <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
              When one asset goes up, does another follow? Understanding this helps you spread risk
              and avoid holding assets that all crash at the same time.
            </p>
          </div>
        </section>

        {/* Loading */}
        {isLoading && (
          <div className="flex h-40 items-center justify-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="mono text-[11px] uppercase tracking-wider text-muted-foreground">
              Loading correlation data…
            </span>
          </div>
        )}

        {/* Pair list */}
        {!isLoading && pairs.length > 0 && (
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-[14px] font-semibold tracking-tight">Asset Relationships</h2>
              <span className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {pairs.length} pairs · live from Gold layer
              </span>
            </div>

            <div className="space-y-2">
              {pairs.map((pair) => {
                const open  = expandedPair === pair.key;
                const label = getLabel(pair.v);
                const pct   = Math.abs(pair.v) * 100;

                return (
                  <div key={pair.key}
                    className={cn(
                      "rounded-xl border transition-all duration-200",
                      open
                        ? "border-border bg-surface/80"
                        : "border-border/60 bg-surface/40 hover:border-border hover:bg-surface/60"
                    )}>

                    {/* Row */}
                    <button
                      className="flex w-full items-center gap-4 px-4 py-3 text-left"
                      onClick={() => setExpandedPair(open ? null : pair.key)}
                    >
                      {/* Asset badges */}
                      <div className="flex w-[160px] shrink-0 items-center gap-2">
                        <span className="mono rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] font-bold">{pair.a}</span>
                        <span className="text-[11px] text-muted-foreground">&</span>
                        <span className="mono rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] font-bold">{pair.b}</span>
                      </div>

                      {/* Diverging bar */}
                      <div className="flex flex-1 items-center gap-3">
                        <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-surface-2">
                          <div
                            className={cn(
                              "absolute h-full rounded-full transition-all duration-500",
                              pair.v >= 0 ? "bg-emerald-500/70" : "bg-red-500/70"
                            )}
                            style={
                              pair.v >= 0
                                ? { left: "50%", width: `${pct / 2}%` }
                                : { right: "50%", width: `${pct / 2}%` }
                            }
                          />
                          <div className="absolute left-1/2 top-0 h-full w-px bg-border" />
                        </div>
                        <span className={cn("mono w-12 shrink-0 text-right text-[12px] font-semibold tabular-nums", label.color)}>
                          {pair.v > 0 ? "+" : ""}{pair.v.toFixed(2)}
                        </span>
                      </div>

                      {/* Label badge */}
                      <div className={cn("hidden shrink-0 items-center gap-1.5 rounded-md border px-2 py-1 text-[10px] font-medium sm:flex", label.bg, label.color)}>
                        <span>{label.emoji}</span>
                        <span className="mono uppercase tracking-wide">{label.text}</span>
                      </div>

                      {open ? <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />}
                    </button>

                    {/* Expanded */}
                    {open && (
                      <div className="border-t border-border/50 px-4 py-4">
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                          <div className="sm:col-span-2">
                            <p className="mono mb-1 text-[9px] uppercase tracking-wider text-muted-foreground">What this means</p>
                            <p className="text-[13px] leading-relaxed text-foreground/90">
                              {getTip(pair.aFull, pair.bFull, pair.v)}
                            </p>
                          </div>
                          <div className="space-y-3">
                            <div>
                              <p className="mono text-[9px] uppercase tracking-wider text-muted-foreground">Strength</p>
                              <p className={cn("mono mt-0.5 text-[13px] font-semibold", label.color)}>{getStrength(pair.v)}</p>
                            </div>
                            <div>
                              <p className="mono text-[9px] uppercase tracking-wider text-muted-foreground">Direction</p>
                              <p className="mono mt-0.5 text-[13px] font-semibold text-foreground">
                                {pair.v >= 0 ? "↑ Same direction" : "↓ Opposite direction"}
                              </p>
                            </div>
                            <div>
                              <p className="mono text-[9px] uppercase tracking-wider text-muted-foreground">Score</p>
                              <p className={cn("mono mt-0.5 text-[18px] font-bold tabular-nums", label.color)}>
                                {pair.v > 0 ? "+" : ""}{pair.v.toFixed(2)}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Diversification tip */}
                        <div className={cn("mt-3 rounded-lg border px-3 py-2.5 text-[12px] leading-relaxed", label.bg, label.color)}>
                          <span className="mono font-semibold uppercase tracking-wider">💡 Tip: </span>
                          {Math.abs(pair.v) >= 0.7
                            ? `${pair.a} and ${pair.b} are highly correlated. Holding both doesn't spread your risk much — they'll likely rise and fall together.`
                            : Math.abs(pair.v) <= 0.2
                            ? `${pair.a} and ${pair.b} move independently. Including both genuinely spreads your risk.`
                            : `${pair.a} and ${pair.b} have a moderate relationship. Holding both provides partial diversification.`
                          }
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && pairs.length === 0 && (
          <div className="flex h-40 items-center justify-center rounded-xl border border-border bg-surface/40">
            <p className="mono text-[11px] uppercase tracking-wider text-muted-foreground">
              No correlation data available yet — run your Gold pipeline first
            </p>
          </div>
        )}

        {/* Summary buckets */}
        {pairs.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <SummaryBucket
              title="Move Together"
              subtitle="Positive correlation"
              pairs={positive}
              color="text-emerald-400"
              bg="bg-emerald-500/10 border-emerald-500/20"
              icon={<TrendingUp className="h-4 w-4" />}
              tip="These pairs offer little diversification — when one drops, the other likely drops too."
            />
            <SummaryBucket
              title="Independent"
              subtitle="No clear relationship"
              pairs={neutral}
              color="text-zinc-400"
              bg="bg-zinc-500/10 border-zinc-500/20"
              icon={<Minus className="h-4 w-4" />}
              tip="Great for diversification — these assets move on their own factors."
            />
            <SummaryBucket
              title="Move Opposite"
              subtitle="Negative correlation"
              pairs={negative}
              color="text-red-400"
              bg="bg-red-500/10 border-red-500/20"
              icon={<TrendingDown className="h-4 w-4" />}
              tip="Holding oppositely correlated assets can act as a natural hedge."
            />
          </div>
        )}

        {/* Explainer */}
        <div className="rounded-xl border border-border bg-surface/40 p-5">
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
            <div>
              <h3 className="text-[13px] font-semibold tracking-tight">How to read correlation scores</h3>
              <p className="mt-1 max-w-2xl text-[12px] leading-relaxed text-muted-foreground">
                Correlation is a number between <strong className="text-foreground">−1</strong> and <strong className="text-foreground">+1</strong>.{" "}
                Near <strong className="text-emerald-400">+1</strong> = assets move together.
                Near <strong className="text-red-400">−1</strong> = they move opposite.
                Near <strong className="text-zinc-400">0</strong> = independent.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  { range: "+0.7 to +1.0", label: "Move together",    cls: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
                  { range: "+0.3 to +0.7", label: "Somewhat related", cls: "text-yellow-400 border-yellow-500/30 bg-yellow-500/10"   },
                  { range: "−0.3 to +0.3", label: "Independent",      cls: "text-zinc-400 border-zinc-500/30 bg-zinc-500/10"         },
                  { range: "−1.0 to −0.3", label: "Move opposite",    cls: "text-red-400 border-red-500/30 bg-red-500/10"            },
                ].map(b => (
                  <span key={b.range} className={cn("mono rounded-md border px-2.5 py-1 text-[10px]", b.cls)}>
                    <strong>{b.range}</strong> · {b.label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Advanced matrix toggle */}
        <div>
          <button
            onClick={() => setShowMatrix(v => !v)}
            className="mono flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-[11px] uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground"
          >
            {showMatrix ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            {showMatrix ? "Hide" : "Show"} correlation matrix (advanced view)
          </button>

          {showMatrix && (
            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr]">
              <CorrelationHeatmap />
              <FeatureDrivers />
            </div>
          )}
        </div>

      </div>
    </TerminalLayout>
  );
};

// ── Summary bucket ────────────────────────────────────────────────────────────
const SummaryBucket = ({
  title, subtitle, pairs, color, bg, icon, tip,
}: {
  title: string; subtitle: string;
  pairs: { a: string; b: string; aFull: string; bFull: string; v: number }[];
  color: string; bg: string; icon: React.ReactNode; tip: string;
}) => (
  <div className={cn("rounded-xl border p-4", bg)}>
    <div className="mb-3 flex items-center justify-between">
      <div>
        <p className={cn("text-[13px] font-semibold", color)}>{title}</p>
        <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">{subtitle}</p>
      </div>
      <span className={color}>{icon}</span>
    </div>
    {pairs.length === 0 ? (
      <p className="mono text-[11px] text-muted-foreground">None in current data</p>
    ) : (
      <ul className="space-y-1.5">
        {pairs.slice(0, 5).map(p => (
          <li key={`${p.a}-${p.b}`} className="mono flex items-center justify-between text-[11px]">
            <span className="text-foreground/80">{p.aFull} / {p.bFull}</span>
            <span className={cn("font-semibold tabular-nums", color)}>
              {p.v > 0 ? "+" : ""}{p.v.toFixed(2)}
            </span>
          </li>
        ))}
        {pairs.length > 5 && (
          <li className="mono text-[10px] text-muted-foreground">+{pairs.length - 5} more</li>
        )}
      </ul>
    )}
    <p className="mt-3 border-t border-current/10 pt-3 text-[11px] leading-relaxed text-muted-foreground">{tip}</p>
  </div>
);

// ── Feature drivers ───────────────────────────────────────────────────────────
const FeatureDrivers = () => (
  <div className="terminal-card p-4">
    <h3 className="mb-1 text-[13px] font-semibold tracking-tight">What drives these correlations?</h3>
    <p className="mono mb-3 text-[10px] uppercase tracking-wider text-muted-foreground">Model feature attribution</p>
    <div className="space-y-3">
      {FEATURE_DRIVERS.map(f => (
        <div key={f.k}>
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[12px] font-medium text-foreground">{f.k}</p>
              <p className="mono text-[10px] text-muted-foreground">{f.desc}</p>
            </div>
            <span className="mono shrink-0 text-[11px] font-semibold tabular-nums text-primary">{f.v.toFixed(2)}</span>
          </div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-2">
            <div className="h-full rounded-full bg-primary/70 transition-all duration-700"
              style={{ width: `${f.v * 250}%` }} />
          </div>
        </div>
      ))}
    </div>
  </div>
);

export default Correlations;