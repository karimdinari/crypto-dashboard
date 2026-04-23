import { useNews,useNewsHistory } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ExternalLink } from "lucide-react";

export const NewsPanel = ({ selectedSymbol }: { selectedSymbol?: string }) => {
  const { data: news } = useNews(20);
  const { data: newsHistory } = useNewsHistory(selectedSymbol || "BTCUSD");

  const displayNews = news && news.length > 0 ? news : newsHistory || [];

  return (
    <div className="terminal-card flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          <h3 className="text-[13px] font-semibold tracking-tight">Live news feed</h3>
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
            {news && news.length > 0 ? "RSS · NLP scored · 12 sources" : `Historical · ${selectedSymbol || "BTCUSD"} · 12 sources`}
          </p>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] font-medium text-bull">
          <span className="pulse-dot bg-bull" /> {news && news.length > 0 ? "streaming" : "historical"}
        </span>
      </div>
      <ul className="flex-1 divide-y divide-border overflow-y-auto">
        {displayNews?.map((n) => {
          const sentClass =
            n.sentiment === "positive" ? "bg-bull/15 text-bull" :
            n.sentiment === "negative" ? "bg-bear/15 text-bear" :
            "bg-muted text-muted-foreground";
          return (
            <li key={n.id} className="group cursor-pointer px-4 py-3 transition-colors hover:bg-surface-2/40"
                onClick={() => window.open(n.url, '_blank')}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="mono inline-flex h-5 items-center rounded border border-border bg-surface px-1.5 text-[9px] font-bold uppercase tracking-wider text-foreground">
                    {n.source}
                  </span>
                  <span className="mono text-[10px] uppercase tracking-wider text-muted-foreground">{n.symbols[0] || "GLOBAL"}</span>
                </div>
                <span className="mono text-[10px] text-muted-foreground">{new Date(n.publishedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <p className="mt-1.5 text-[12.5px] leading-snug text-foreground/95 group-hover:text-foreground">
                {n.headline}
              </p>
              <div className="mt-2 flex items-center gap-2">
                <span className={cn("mono rounded px-1.5 py-0.5 text-[9px] font-semibold", sentClass)}>
                  {n.sentiment.toUpperCase()}
                </span>
                <span className="mono text-[10px] text-muted-foreground">sentiment</span>
                <ExternalLink className="ml-auto h-3 w-3 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
