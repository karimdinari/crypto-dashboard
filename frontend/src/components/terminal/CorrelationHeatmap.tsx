import { CORR_ASSETS, CORR_MATRIX } from "@/lib/market-data";

const colorFor = (v: number) => {
  // -1 → bear red, 0 → muted, +1 → bull green
  const abs = Math.abs(v);
  const hue = v >= 0 ? 145 : 0;
  const sat = 70;
  const lit = 50 - abs * 20; // stronger = darker
  const alpha = 0.15 + abs * 0.6;
  return `hsl(${hue} ${sat}% ${lit}% / ${alpha})`;
};

export const CorrelationHeatmap = ({ compact = false }: { compact?: boolean }) => {
  return (
    <div className="terminal-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-[13px] font-semibold tracking-tight">Correlation matrix</h3>
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">30d · pearson · cross-asset</p>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <span className="flex items-center gap-1 mono uppercase tracking-wider text-muted-foreground">
            <span className="h-2 w-3 rounded-sm bg-bear/70" />−1
          </span>
          <span className="flex items-center gap-1 mono uppercase tracking-wider text-muted-foreground">
            <span className="h-2 w-3 rounded-sm bg-bull/70" />+1
          </span>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-border">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="bg-surface-2/50" />
              {CORR_ASSETS.map((a) => (
                <th key={a} className="mono bg-surface-2/50 px-2 py-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  {a}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CORR_MATRIX.map((row, i) => (
              <tr key={i}>
                <th className="mono bg-surface-2/50 px-2 py-1.5 text-left text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  {CORR_ASSETS[i]}
                </th>
                {row.map((v, j) => (
                  <td
                    key={j}
                    className="mono border-l border-t border-border/40 text-center text-[11px] tabular-nums transition-colors"
                    style={{ background: colorFor(v), padding: compact ? "8px" : "12px 8px" }}
                  >
                    <span className={v >= 0 ? "text-bull" : "text-bear"}>
                      {v.toFixed(2)}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
