import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { useNews, useLatestStream, useNewsHistory } from "@/lib/api";
import { ArticleReader } from "@/components/terminal/ArticaleReader";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  Bookmark,
  Brain,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  ExternalLink,
  Filter,
  Flame,
  Globe2,
  Newspaper,
  Pause,
  Play,
  Radio,
  Search,
  SlidersHorizontal,
  TrendingUp,
  Volume2,
  VolumeX,
  BookOpen,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useMemo, useRef, useState, type ComponentType } from "react";

type Tab = "streaming" | "historical";

type NewsItem = {
  id: string;
  uiKey: string;
  source: string;
  badge: string;
  time: string;
  title: string;
  sentiment: number;
  asset: string;
  isLive?: boolean;
  body?: string;
  arrivedAt?: number;
  symbols: string[];
  url: string;
};

const FILTERS = ["All", "Crypto", "Forex", "Metals", "Macro", "Earnings"] as const;
const normalizeNewsUrl = (raw: unknown): string => {
  if (!raw) return "";

  if (typeof raw === "string") {
    const trimmed = raw.trim();

    // Case 1: normal URL
    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
      return trimmed;
    }

    // Case 2: backend accidentally returned JSON string in url
    if (trimmed.startsWith("{")) {
      try {
        const parsed = JSON.parse(trimmed);
        if (typeof parsed?.url === "string") {
          return parsed.url;
        }
      } catch {
        return "";
      }
    }

    return "";
  }

  // Case 3: backend returned an object instead of a string
  if (typeof raw === "object" && raw !== null && "url" in raw) {
    const nested = (raw as { url?: unknown }).url;
    return typeof nested === "string" ? nested : "";
  }

  return "";
};

const News = () => {
  const { data: newsData = [] } = useNews(100);
  const { data: streamData = [] } = useLatestStream();
  const [tab, setTab] = useState<Tab>("streaming");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("All");
  const [query, setQuery] = useState("");
  const [streaming, setStreaming] = useState(true);
  const [muted, setMuted] = useState(true);
  const [selected, setSelected] = useState<NewsItem | null>(null);
  const [feed, setFeed] = useState<NewsItem[]>([]);
  const [readerUrl, setReaderUrl] = useState<string | null>(null);
 


  // Transform API news data to NewsItem format
const transformedNews = useMemo(() => {
  return newsData.map((n, index) => {
    const publishedAt = n.publishedAt || "";
    const symbolPart = (n.symbols || []).join("-");
    const sourcePart = n.source || "unknown";

    return {
      id: n.id,
      uiKey: `${n.id}-${publishedAt}-${symbolPart}-${sourcePart}-${index}`,
      source: n.source,
      badge: n.source.slice(0, 3).toUpperCase(),
      title: n.headline,
      sentiment:
        n.sentiment === "positive" ? 0.72 : n.sentiment === "negative" ? -0.65 : 0.15,
      asset: n.symbols[0] || "MULTI",
      symbols: n.symbols,
      url: normalizeNewsUrl(n.url),
      time: new Date(n.publishedAt).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      arrivedAt: new Date(n.publishedAt).getTime(),
    };
  });
}, [newsData]);

  // Populate feed on load
  useEffect(() => {
    if (transformedNews.length > 0 && feed.length === 0) {
      setFeed(transformedNews.slice(0, 40));
    }
  }, [transformedNews, feed.length]);

  // Age "now" labels
  useEffect(() => {
    const interval = setInterval(() => {
      setFeed((prev) =>
        prev.map((n) => {
          if (!n.arrivedAt) return n;
          const sec = Math.floor((Date.now() - n.arrivedAt) / 1000);
          if (sec < 5) return { ...n, time: "now" };
          if (sec < 60) return { ...n, time: `${sec}s` };
          return { ...n, time: `${Math.floor(sec / 60)}m` };
        })
      );
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const source = tab === "streaming" ? feed : transformedNews;

  const filtered = useMemo(() => {
    return source.filter((n) => {
      const matchesQ = !query || n.title.toLowerCase().includes(query.toLowerCase());
      const matchesF =
        filter === "All" ||
        (filter === "Crypto" && ["BTC", "ETH"].includes(n.asset)) ||
        (filter === "Forex" && ["EUR", "GBP", "FOREX"].includes(n.asset)) ||
        (filter === "Metals" && ["XAU", "XAG"].includes(n.asset)) ||
        (filter === "Macro" && n.asset === "FOREX") ||
        (filter === "Earnings" && false);
      return matchesQ && matchesF;
    });
  }, [source, query, filter]);

  // Calculate statistics
  const stats = useMemo(() => {
    const pos = filtered.filter((n) => n.sentiment > 0.2).length;
    const neg = filtered.filter((n) => n.sentiment < -0.2).length;
    const avg =
      filtered.length
        ? filtered.reduce((a, b) => a + b.sentiment, 0) / filtered.length
        : 0;
    return { pos, neg, neu: filtered.length - pos - neg, avg };
  }, [filtered]);

  // Generate daily sentiment data from real news
  const DAILY = useMemo(() => {
    return Array.from({ length: 14 }).map((_, i) => {
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() - (13 - i));
      const dayNews = transformedNews.filter((n) => {
        const newsDate = new Date(n.arrivedAt || 0);
        return newsDate.toDateString() === targetDate.toDateString();
      });

      return {
        d: `D-${13 - i}`,
        pos: dayNews.filter((n) => n.sentiment > 0.2).length,
        neu: dayNews.filter((n) => n.sentiment > -0.2 && n.sentiment <= 0.2).length,
        neg: dayNews.filter((n) => n.sentiment <= -0.2).length,
      };
    });
  }, [transformedNews]);

  // Generate pulse data from news volume
  const PULSE = useMemo(() => {
    return Array.from({ length: 30 }).map((_, i) => ({
      t: i,
      v: Math.max(5, Math.round(transformedNews.length * 1.5 + Math.random() * 10)),
    }));
  }, [transformedNews]);

  // Extract unique assets from news
  const ASSETS = useMemo(() => {
    const assetMap: Record<string, { pos: number; neg: number }> = {};
    transformedNews.forEach((n) => {
      if (!assetMap[n.asset]) assetMap[n.asset] = { pos: 0, neg: 0 };
      if (n.sentiment > 0.2) assetMap[n.asset].pos++;
      else if (n.sentiment < -0.2) assetMap[n.asset].neg++;
    });

    return Object.entries(assetMap)
      .map(([asset, counts]) => {
        const total = counts.pos + counts.neg;
        return {
          asset,
          pos: total > 0 ? Math.round((counts.pos / total) * 100) : 0,
          neg: total > 0 ? Math.round((counts.neg / total) * 100) : 0,
        };
      })
      .slice(0, 6);
  }, [transformedNews]);

  // Extract unique sources
  const SOURCES = useMemo(() => {
    const sourceMap: Record<string, number> = {};
    transformedNews.forEach((n) => {
      sourceMap[n.source] = (sourceMap[n.source] || 0) + 1;
    });
    return Object.entries(sourceMap)
      .map(([source, count]) => source)
      .slice(0, 6);
  }, [transformedNews]);
return (
    <TerminalLayout>
      <div className="space-y-4">
        {/* Hero */}
        <section className="relative overflow-hidden rounded-xl border border-border bg-card p-5 hairline-top">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,hsl(var(--forex)/0.13),transparent_50%),radial-gradient(ellipse_at_bottom_right,hsl(var(--metals)/0.11),transparent_52%)]" />
          <div className="relative grid gap-4 lg:grid-cols-[1fr_1.1fr] lg:items-end">
            <div>
              <p className="mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
                News workspace · NLP intelligence
              </p>
              <h1 className="mt-2 text-[24px] font-semibold leading-tight tracking-tight">
                Real-time wire and historical archive in one console.
              </h1>
              <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
                Stream low-latency headlines or pivot to the searchable archive — every story is NLP-scored,
                entity-tagged, and linked to the underlying market.
              </p>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <NewsKpi icon={Newspaper} label="Matches" value={String(filtered.length)} tone="text-primary" />
              <NewsKpi icon={Brain} label="Avg NLP" value={`${stats.avg >= 0 ? "+" : ""}${stats.avg.toFixed(2)}`} tone={stats.avg >= 0 ? "text-bull" : "text-bear"} />
              <NewsKpi icon={TrendingUp} label="Bullish" value={String(stats.pos)} tone="text-bull" />
              <NewsKpi icon={Flame} label="Bearish" value={String(stats.neg)} tone="text-bear" />
            </div>
          </div>
        </section>

        {/* Tabs + global controls */}
        <div className="terminal-card flex flex-wrap items-center gap-2 p-2">
          <div className="flex rounded-md border border-border bg-surface p-0.5">
            <TabBtn active={tab === "streaming"} onClick={() => setTab("streaming")} icon={Radio}>
              Streaming
              {tab === "streaming" && streaming && <span className="pulse-dot ml-1.5 bg-bull" />}
            </TabBtn>
            <TabBtn active={tab === "historical"} onClick={() => setTab("historical")} icon={Calendar}>
              Historical
            </TabBtn>
          </div>

          <div className="relative flex flex-1 items-center min-w-[220px]">
            <Search className="absolute left-3 h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="mono h-9 w-full rounded-md border border-border bg-surface pl-9 pr-3 text-[12px] outline-none transition-colors focus:border-primary/50"
              placeholder={tab === "streaming" ? "Filter live wire…" : "Search archive…"}
            />
          </div>

          {tab === "streaming" ? (
            <>
              <button
                onClick={() => setStreaming((s) => !s)}
                className={cn(
                  "mono flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[10px] uppercase tracking-wider transition-colors",
                  streaming
                    ? "border-bull/40 bg-bull/10 text-bull"
                    : "border-border bg-surface text-muted-foreground hover:text-foreground"
                )}
              >
                {streaming ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
                {streaming ? "Pause" : "Resume"}
              </button>
              <button
                onClick={() => setMuted((m) => !m)}
                className="mono flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground"
              >
                {muted ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3" />}
                {muted ? "Muted" : "Alerts"}
              </button>
            </>
          ) : (
            <button className="mono flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground">
              <Calendar className="h-3 w-3" /> Last 7 days
            </button>
          )}
        </div>

        {/* Category chips */}
        <div className="flex flex-wrap items-center gap-1.5">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "mono rounded-md border px-2.5 py-1 text-[10px] uppercase tracking-wider transition-all",
                filter === f
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-border bg-surface text-muted-foreground hover:text-foreground"
              )}
            >
              {f}
            </button>
          ))}
          <span className="mono ml-2 text-[10px] uppercase tracking-wider text-muted-foreground">
            · {filtered.length} results
          </span>
          <button className="mono ml-auto flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
            <SlidersHorizontal className="h-3 w-3" /> Advanced
          </button>
        </div>
        {/* Reader drawer (inline) */}
        {selected && <ReaderPanel item={selected} onClose={() => setSelected(null)} onOpenReader={setReaderUrl} />}

        {/* Mode-specific body */}
        {tab === "streaming" ? (
          <StreamingView
            items={filtered}
            streaming={streaming}
            onSelect={setSelected}
            selectedId={selected?.id}
            sources={SOURCES}
          />
        ) : (
          <HistoricalView
            items={filtered}
            onSelect={setSelected}
            selectedId={selected?.id}
            daily={DAILY}
            assets={ASSETS}
          />
        )}
      </div>
      {readerUrl && (
        <ArticleReader
          url={readerUrl}
          title={selected?.title ?? ""}
          source={selected?.source}
          onClose={() => setReaderUrl(null)}
        />
      )}
    </TerminalLayout>
  );
};

export default News;

/* ─────────────── Streaming view ─────────────── */
const StreamingView = ({
  items,
  streaming,
  onSelect,
  selectedId,
  sources,
}: {
  items: NewsItem[];
  streaming: boolean;
  onSelect: (n: NewsItem) => void;
  selectedId?: string;
  sources: string[];
}) => {
  const trendingTags = useMemo(() => {
    const tagMap: Record<string, number> = {};
    items.forEach((item) => {
      item.symbols.forEach((sym) => {
        tagMap[`#${sym}`] = (tagMap[`#${sym}`] || 0) + 1;
      });
    });
    return Object.entries(tagMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 7)
      .map(([tag, count]) => ({
        t: tag,
        n: count,
        tone:
          items.filter((i) => i.symbols.includes(tag.slice(1))).some((i) => i.sentiment > 0.2)
            ? "text-bull"
            : "text-bear",
      }));
  }, [items]);

  const sourceMix = useMemo(() => {
    const sourceMap: Record<string, number> = {};
    items.forEach((item) => {
      sourceMap[item.source] = (sourceMap[item.source] || 0) + 1;
    });
    const total = items.length;
    return Object.entries(sourceMap)
      .map(([source, count]) => ({
        s: source,
        pct: total > 0 ? Math.round((count / total) * 100) : 0,
      }))
      .sort((a, b) => b.pct - a.pct)
      .slice(0, 6);
  }, [items]);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
      {/* Live wire */}
      <div className="terminal-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div>
            <h3 className="text-[13px] font-semibold tracking-tight">Live wire</h3>
            <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
              API stream · {sources.length} sources · {items.length} entries
            </p>
          </div>
          <span
            className={cn(
              "mono flex items-center gap-1.5 text-[11px] font-medium",
              streaming ? "text-bull" : "text-muted-foreground"
            )}
          >
            <span className={cn("pulse-dot", streaming ? "bg-bull" : "bg-muted-foreground")} />
            {streaming ? "streaming" : "paused"}
          </span>
        </div>
        <ul className="max-h-[680px] divide-y divide-border overflow-y-auto">
          {items.map((n) => {
            const isPos = n.sentiment > 0.2;
            const isNeg = n.sentiment < -0.2;
            const sentClass = isPos
              ? "bg-bull/15 text-bull border-bull/20"
              : isNeg
              ? "bg-bear/15 text-bear border-bear/20"
              : "bg-muted text-muted-foreground border-border";
            return (
              <li
                key={n.uiKey}
                onClick={() => onSelect(n)}
                className={cn(
                  "group relative cursor-pointer px-4 py-3 transition-colors hover:bg-surface-2/40",
                  selectedId === n.id && "bg-surface-2/60"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="mono inline-flex h-5 items-center rounded border border-border bg-surface px-1.5 text-[9px] font-bold uppercase tracking-wider">
                      {n.badge}
                    </span>
                    <span className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
                      {n.asset}
                    </span>
                  </div>
                  <span className="mono flex items-center gap-1 text-[10px] text-muted-foreground">
                    <Clock className="h-2.5 w-2.5" />
                    {n.time}
                  </span>
                </div>
                <p className="mt-1.5 text-[13px] leading-snug text-foreground/95 group-hover:text-foreground">
                  {n.title}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <span className={cn("mono rounded border px-1.5 py-0.5 text-[9px] font-semibold", sentClass)}>
                    {n.sentiment > 0 ? "+" : ""}
                    {n.sentiment.toFixed(2)}
                  </span>
                  <span className="mono text-[10px] text-muted-foreground">NLP</span>
                  <span className="mono text-[10px] text-muted-foreground">· {n.source}</span>
                  <a href={n.url} target="_blank" rel="noopener noreferrer" className="ml-auto">
                    <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                  </a>
                </div>
              </li>
            );
          })}
          {items.length === 0 && (
            <li className="px-4 py-12 text-center">
              <p className="mono text-[11px] uppercase tracking-wider text-muted-foreground">
                No headlines match current filters
              </p>
            </li>
          )}
        </ul>
      </div>

      {/* Sidebar */}
      <div className="space-y-4">
        <div className="terminal-card p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-[13px] font-semibold tracking-tight">Trending tags</h3>
            <span className="mono text-[10px] uppercase tracking-wider text-bull">+ live</span>
          </div>
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground mb-3">
            Last {items.length} stories
          </p>
          <div className="flex flex-wrap gap-1.5">
            {trendingTags.map((t) => (
              <span
                key={t.t}
                className={cn(
                  "mono inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-1 text-[10px]",
                  t.tone
                )}
              >
                {t.t} <span className="text-muted-foreground">{t.n}</span>
              </span>
            ))}
          </div>
        </div>

        <div className="terminal-card p-4">
          <h3 className="text-[13px] font-semibold tracking-tight">Source mix</h3>
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground mb-3">
            Active providers
          </p>
          <div className="space-y-1.5">
            {sourceMix.map((s) => (
              <div key={s.s} className="flex items-center gap-2">
                <Globe2 className="h-3 w-3 text-muted-foreground" />
                <span className="mono flex-1 text-[11px] text-foreground/90">{s.s}</span>
                <div className="h-1 w-16 overflow-hidden rounded-full bg-surface-2">
                  <div className="h-full bg-primary" style={{ width: `${s.pct}%` }} />
                </div>
                <span className="mono w-7 text-right text-[10px] text-muted-foreground">{s.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

/* ─────────────── Historical view ─────────────── */
const HistoricalView = ({
  items,
  onSelect,
  selectedId,
  daily,
  assets,
}: {
  items: NewsItem[];
  onSelect: (n: NewsItem) => void;
  selectedId?: string;
  daily: Array<{ d: string; pos: number; neu: number; neg: number }>;
  assets: Array<{ asset: string; pos: number; neg: number }>;
}) => {
  const [page, setPage] = useState(1);
  const PER = 10;
  const pages = Math.max(1, Math.ceil(items.length / PER));
  const slice = items.slice((page - 1) * PER, page * PER);

  return (
    <div className="space-y-4">
      {/* Charts row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="terminal-card p-4 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="text-[13px] font-semibold tracking-tight">Daily news activity</h3>
              <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
                Volume by sentiment · last 14 days
              </p>
            </div>
            <div className="flex items-center gap-3 text-[10px] mono uppercase tracking-wider text-muted-foreground">
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-bull" />pos</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-neutral" />neu</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-bear" />neg</span>
            </div>
          </div>
          <div className="h-[260px]">
            <ResponsiveContainer>
              <BarChart data={daily} margin={{ top: 10, right: 10, bottom: 0, left: -8 }} barCategoryGap={6}>
                <CartesianGrid stroke="hsl(var(--grid-line))" strokeDasharray="2 4" vertical={false} />
                <XAxis dataKey="d" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }} />
                <Bar dataKey="pos" stackId="a" fill="hsl(var(--bull))" />
                <Bar dataKey="neu" stackId="a" fill="hsl(var(--neutral))" />
                <Bar dataKey="neg" stackId="a" fill="hsl(var(--bear))" radius={[3, 3, 0, 0]}>
                  {daily.map((_, i) => <Cell key={i} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="terminal-card p-4">
          <h3 className="text-[13px] font-semibold tracking-tight">Sentiment by asset</h3>
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground mb-4">
            Aggregate · 7d
          </p>
          {assets.map((r) => (
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

      {/* Archive table */}
      <div className="terminal-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div>
            <h3 className="text-[13px] font-semibold tracking-tight">Archive feed</h3>
            <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {items.length} matches · NLP scored · Bronze layer
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button className="mono flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
              <Filter className="h-3 w-3" /> Sort: Newest
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="mono w-full text-[12px]">
            <thead>
              <tr className="text-[9px] uppercase tracking-wider text-muted-foreground">
                <th className="px-4 py-2 text-left">Time</th>
                <th className="px-2 py-2 text-left">Source</th>
                <th className="px-2 py-2 text-left">Asset</th>
                <th className="px-2 py-2 text-left">Headline</th>
                <th className="px-4 py-2 text-right">Sentiment</th>
                <th className="px-4 py-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {slice.map((n) => {
                const sent = n.sentiment > 0.2 ? "text-bull" : n.sentiment < -0.2 ? "text-bear" : "text-muted-foreground";
                return (
                  <tr key={n.uiKey} className="border-t border-border/50 transition-colors hover:bg-surface-2/40">
                    <td className="px-4 py-2 text-muted-foreground">{n.time}</td>
                    <td className="px-2 py-2">
                      <span className="rounded border border-border bg-surface px-1.5 py-0.5 text-[9px] font-bold uppercase">
                        {n.badge}
                      </span>
                    </td>
                    <td className="px-2 py-2 text-muted-foreground">{n.asset}</td>
                    <td
                      className="px-2 py-2 font-sans text-foreground/95 cursor-pointer"
                      onClick={() => onSelect(n)}
                    >
                      {n.title}
                    </td>
                    <td className={`px-4 py-2 text-right font-semibold ${sent}`}>
                      {n.sentiment > 0 ? "+" : ""}{n.sentiment.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <a href={n.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-3 w-3 text-muted-foreground hover:text-foreground" />
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-border px-4 py-2.5">
          <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
            Page {page} of {pages}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="mono flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-1 text-[10px] uppercase tracking-wider text-muted-foreground disabled:opacity-40 hover:text-foreground"
            >
              <ChevronLeft className="h-3 w-3" /> Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(pages, p + 1))}
              disabled={page === pages}
              className="mono flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-1 text-[10px] uppercase tracking-wider text-muted-foreground disabled:opacity-40 hover:text-foreground"
            >
              Next <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ─────────────── Reader panel ─────────────── */
const ReaderPanel = ({ item, onClose, onOpenReader }: { item: NewsItem; onClose: () => void; onOpenReader: (url: string) => void }) => {
  const sentClass =
    item.sentiment > 0.2 ? "bg-bull/15 text-bull border-bull/30"
    : item.sentiment < -0.2 ? "bg-bear/15 text-bear border-bear/30"
    : "bg-muted text-muted-foreground border-border";
  return (
    <div className="terminal-card animate-in fade-in slide-in-from-bottom-2 duration-300 p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="mono rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] font-bold uppercase">
            {item.badge}
          </span>
          <span className="mono text-[11px] uppercase tracking-wider text-muted-foreground">
            {item.source} · {item.asset} · {item.time}
          </span>
          <span className={cn("mono rounded border px-1.5 py-0.5 text-[10px] font-semibold", sentClass)}>
            NLP {item.sentiment > 0 ? "+" : ""}{item.sentiment.toFixed(2)}
          </span>
        </div>
        <button
          onClick={onClose}
          className="mono rounded-md border border-border bg-surface px-2 py-1 text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground"
        >
          Close
        </button>
      </div>
      <h2 className="mt-3 text-[18px] font-semibold leading-snug tracking-tight">
        {item.title}
      </h2>
      <p className="mt-2 max-w-3xl text-[13px] leading-relaxed text-muted-foreground">
        {item.body ??
          "Full article body would render here, with NLP-extracted entities, related signals, and historical context for the affected market."}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
      <button
        disabled={!normalizeNewsUrl(item.url)}
        onClick={() => {
          const cleanUrl = normalizeNewsUrl(item.url);
          if (cleanUrl) onOpenReader(cleanUrl);
        }}
        className="mono flex items-center gap-1.5 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-primary hover:bg-primary/15 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <BookOpen className="h-3 w-3" /> Open reader
      </button>
        <button className="mono flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
          <Bookmark className="h-3 w-3" /> Save
        </button>
        <button className="mono flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
          <TrendingUp className="h-3 w-3" /> View asset
        </button>
      </div>
    </div>
  );
};

/* ─────────────── Helpers ─────────────── */
const TabBtn = ({
  active,
  onClick,
  icon: Icon,
  children,
}: {
  active: boolean;
  onClick: () => void;
  icon: ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) => (
  <button
    onClick={onClick}
    className={cn(
      "mono flex items-center gap-1.5 rounded px-3 py-1.5 text-[11px] uppercase tracking-wider transition-colors",
      active
        ? "bg-primary/15 text-primary"
        : "text-muted-foreground hover:text-foreground"
    )}
  >
    <Icon className="h-3 w-3" />
    {children}
  </button>
);

const NewsKpi = ({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
  tone: string;
}) => (
  <div className="rounded-lg border border-border/70 bg-surface-2/50 p-3">
    <div className="flex items-center justify-between">
      <p className="mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">{label}</p>
      <Icon className={cn("h-3.5 w-3.5", tone)} />
    </div>
    <p className={cn("mono mt-2 text-[19px] font-semibold tabular-nums", tone)}>{value}</p>
  </div>
);
