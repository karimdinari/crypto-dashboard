import { useMemo } from "react";
import { useNews } from "@/lib/api";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

export const SentimentPanel = () => {
  const { data: news } = useNews(100);

  const { stats, chartData, score } = useMemo(() => {
    if (!news || news.length === 0) {
      return { 
        stats: { pos: 0, neu: 0, neg: 0, total: 0 }, 
        chartData: [], 
        score: 0 
      };
    }
    const pos = news.filter(n => n.sentiment === "positive").length;
    const neu = news.filter(n => n.sentiment === "neutral").length;
    const neg = news.filter(n => n.sentiment === "negative").length;
    const total = news.length;
    const score = (pos - neg) / total;

    return {
      stats: { pos, neu, neg, total },
      chartData: [
        { name: "Positive", value: pos, color: "hsl(var(--bull))" },
        { name: "Neutral",  value: neu, color: "hsl(var(--neutral))" },
        { name: "Negative", value: neg, color: "hsl(var(--bear))" },
      ],
      score
    };
  }, [news]);

  if (!news) return null;

  return (
    <div className="terminal-card p-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-[13px] font-semibold tracking-tight">Market sentiment</h3>
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">NLP · last 24h · {stats.total} articles</p>
        </div>
        <span className={cn("mono rounded px-1.5 py-0.5 text-[10px] font-semibold", 
          score > 0 ? "bg-bull/10 text-bull" : "bg-bear/10 text-bear")}>
          {score > 0 ? "+" : ""}{score.toFixed(2)} avg
        </span>
      </div>

      <div className="mt-2 flex items-center gap-4">
        <div className="relative h-[110px] w-[110px] shrink-0">
          <ResponsiveContainer>
            <PieChart>
              <Pie data={chartData} dataKey="value" innerRadius={36} outerRadius={52} paddingAngle={3} stroke="none" isAnimationActive={false}>
                {chartData.map((d) => <Cell key={d.name} fill={d.color} />)}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className={cn("mono text-[18px] font-bold leading-none", score > 0 ? "text-bull" : "text-bear")}>
              {score > 0 ? "+" : ""}{(score * 100).toFixed(0)}
            </span>
            <span className="mono text-[9px] uppercase tracking-wider text-muted-foreground">
              {score > 0 ? "bullish" : "bearish"}
            </span>
          </div>
        </div>
        <div className="flex-1 space-y-2">
          {chartData.map((d) => (
            <div key={d.name}>
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-sm" style={{ background: d.color }} />
                  <span className="text-foreground/90">{d.name}</span>
                </span>
                <span className="mono tabular-nums text-muted-foreground">{d.value}</span>
              </div>
              <div className="mt-1 h-1 overflow-hidden rounded-full bg-surface-2">
                <div className="h-full rounded-full" style={{ width: `${(d.value / (stats.total || 1)) * 100}%`, background: d.color }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

import { cn } from "@/lib/utils";
