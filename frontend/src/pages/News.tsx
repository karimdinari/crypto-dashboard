import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { NEWS } from "@/lib/market-data";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell } from "recharts";
import { Filter, Search } from "lucide-react";
import { cn } from "@/lib/utils";

const DAILY = Array.from({ length: 14 }).map((_, i) => ({
  d: `D-${13 - i}`,
  pos: Math.floor(Math.random() * 30) + 20,
  neu: Math.floor(Math.random() * 15) + 10,
  neg: Math.floor(Math.random() * 18) + 5,
}));

const News = () => {
  return (
    <TerminalLayout>
      <div className="space-y-4">
        <header>
          <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Workspace</p>
          <h1 className="text-[22px] font-semibold tracking-tight">News & Sentiment</h1>
        </header>

        {/* filters */}
        <div className="terminal-card flex flex-wrap items-center gap-2 p-3">
          <div className="relative flex flex-1 items-center min-w-[220px]">
            <Search className="absolute left-3 h-3.5 w-3.5 text-muted-foreground" />
            <input className="mono h-9 w-full rounded-md border border-border bg-surface pl-9 text-[12px] outline-none" placeholder="Search headlines…" />
          </div>
          {["All","Crypto","Forex","Metals","Macro"].map((f, i) => (
            <button key={f} className={cn("mono rounded-md border px-2.5 py-1.5 text-[10px] uppercase tracking-wider",
              i === 0 ? "border-primary/40 bg-primary/10 text-primary" : "border-border bg-surface text-muted-foreground")}>{f}</button>
          ))}
          <button className="mono ml-auto flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
            <Filter className="h-3 w-3" /> Date range · 7d
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* Distribution bars */}
          <div className="terminal-card p-4 lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-[13px] font-semibold tracking-tight">Daily news activity</h3>
                <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">Volume by sentiment · last 14 days</p>
              </div>
              <div className="flex items-center gap-3 text-[10px] mono uppercase tracking-wider text-muted-foreground">
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-bull" />pos</span>
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-neutral" />neu</span>
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-bear" />neg</span>
              </div>
            </div>
            <div className="h-[280px]">
              <ResponsiveContainer>
                <BarChart data={DAILY} margin={{ top: 10, right: 10, bottom: 0, left: -8 }} barCategoryGap={6}>
                  <CartesianGrid stroke="hsl(var(--grid-line))" strokeDasharray="2 4" vertical={false} />
                  <XAxis dataKey="d" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }} />
                  <Bar dataKey="pos" stackId="a" fill="hsl(var(--bull))" radius={[0,0,0,0]} />
                  <Bar dataKey="neu" stackId="a" fill="hsl(var(--neutral))" />
                  <Bar dataKey="neg" stackId="a" fill="hsl(var(--bear))" radius={[3,3,0,0]}>
                    {DAILY.map((_, i) => <Cell key={i} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Sentiment distribution */}
          <div className="terminal-card p-4">
            <h3 className="text-[13px] font-semibold tracking-tight">Sentiment distribution</h3>
            <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground mb-4">By asset · 24h</p>
            {[
              { asset: "BTC", pos: 72, neg: 12 },
              { asset: "ETH", pos: 64, neg: 18 },
              { asset: "EUR", pos: 38, neg: 41 },
              { asset: "GBP", pos: 31, neg: 48 },
              { asset: "XAU", pos: 58, neg: 22 },
              { asset: "XAG", pos: 61, neg: 19 },
            ].map((r) => (
              <div key={r.asset} className="mb-2">
                <div className="flex justify-between text-[11px]">
                  <span className="mono text-foreground">{r.asset}</span>
                  <span className="mono text-muted-foreground">{r.pos}% / {r.neg}%</span>
                </div>
                <div className="mt-1 flex h-1.5 overflow-hidden rounded-full bg-surface-2">
                  <div className="bg-bull" style={{ width: `${r.pos}%` }} />
                  <div className="bg-neutral" style={{ width: `${100 - r.pos - r.neg}%` }} />
                  <div className="bg-bear" style={{ width: `${r.neg}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Article feed */}
        <div className="terminal-card overflow-hidden">
          <div className="border-b border-border px-4 py-3">
            <h3 className="text-[13px] font-semibold tracking-tight">Article feed</h3>
            <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">{NEWS.length} matches · NLP scored · Bronze layer</p>
          </div>
          <table className="mono w-full text-[12px]">
            <thead>
              <tr className="text-[9px] uppercase tracking-wider text-muted-foreground">
                <th className="px-4 py-2 text-left">Time</th>
                <th className="px-2 py-2 text-left">Source</th>
                <th className="px-2 py-2 text-left">Asset</th>
                <th className="px-2 py-2 text-left">Headline</th>
                <th className="px-4 py-2 text-right">Sentiment</th>
              </tr>
            </thead>
            <tbody>
              {NEWS.concat(NEWS).map((n, i) => {
                const sent = n.sentiment > 0.2 ? "text-bull" : n.sentiment < -0.2 ? "text-bear" : "text-muted-foreground";
                return (
                  <tr key={i} className="border-t border-border/50 transition-colors hover:bg-surface-2/40">
                    <td className="px-4 py-2 text-muted-foreground">{n.time}</td>
                    <td className="px-2 py-2"><span className="rounded border border-border bg-surface px-1.5 py-0.5 text-[9px] font-bold uppercase">{n.badge}</span></td>
                    <td className="px-2 py-2 text-muted-foreground">{n.asset}</td>
                    <td className="px-2 py-2 font-sans text-foreground/95">{n.title}</td>
                    <td className={`px-4 py-2 text-right font-semibold ${sent}`}>{n.sentiment > 0 ? "+" : ""}{n.sentiment.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </TerminalLayout>
  );
};

export default News;
