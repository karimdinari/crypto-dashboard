/**
 * ArticleReader
 * =============
 * Full-screen slide-in drawer that fetches and renders scraped article content
 * inline inside your app — no new tab, no iframe, no CORS issues.
 *
 * Usage:
 *   <ArticleReader url={item.url} title={item.title} onClose={() => setReader(null)} />
 */

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import {
  X, ExternalLink, BookOpen, Clock, User,
  Loader2, AlertCircle, ChevronLeft, Copy, Check,
  ZoomIn, ZoomOut, Globe,
} from "lucide-react";

interface ArticleData {
  url:        string;
  title:      string;
  author:     string;
  source:     string;
  image:      string | null;
  content:    string;
  text:       string;
  word_count: number;
  read_mins:  number;
  success:    boolean;
  error:      string | null;
}

interface ArticleReaderProps {
  url:      string;
  title:    string;
  source?:  string;
  onClose:  () => void;
}

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export const ArticleReader = ({ url, title, source, onClose }: ArticleReaderProps) => {
  
  const [data,     setData]     = useState<ArticleData | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [fontSize, setFontSize] = useState(15);
  const [copied,   setCopied]   = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const proxyImage = (url: string) =>
  `${API_BASE}/news/image?url=${encodeURIComponent(url)}`;

  // Fetch article on mount
  useEffect(() => {
    setLoading(true);
    setData(null);
    fetch(`${API_BASE}/news/article?url=${encodeURIComponent(url)}`)
      .then((r) => r.json())
      .then((d: ArticleData) => setData(d))
      .catch(() =>
        setData({
          url, title, author: "", source: source ?? "",
          image: null, content: "", text: "",
          word_count: 0, read_mins: 0,
          success: false, error: "Failed to fetch article",
        })
      )
      .finally(() => setLoading(false));
  }, [url]);

  // Close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const copyText = () => {
    if (data?.text) {
      navigator.clipboard.writeText(data.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Drawer — slides in from right */}
      <div className={cn(
        "fixed inset-y-0 right-0 z-50 flex w-full flex-col bg-background shadow-2xl",
        "sm:w-[680px] lg:w-[760px]",
        "border-l border-border",
        "animate-in slide-in-from-right duration-300"
      )}>

        {/* ── Top bar ── */}
        <div className="flex items-center gap-3 border-b border-border bg-surface/80 px-4 py-3 backdrop-blur">
          <button
            onClick={onClose}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground transition-colors hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          <div className="flex min-w-0 flex-1 items-center gap-2">
            <Globe className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <span className="mono truncate text-[11px] text-muted-foreground">
              {data?.source || source || new URL(url).hostname.replace("www.", "")}
            </span>
          </div>

          {/* Font size controls */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setFontSize(s => Math.max(12, s - 1))}
              className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground hover:text-foreground"
              title="Decrease font size"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="mono w-8 text-center text-[10px] text-muted-foreground">{fontSize}</span>
            <button
              onClick={() => setFontSize(s => Math.min(22, s + 1))}
              className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground hover:text-foreground"
              title="Increase font size"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="h-4 w-px bg-border" />

          {/* Copy */}
          <button
            onClick={copyText}
            disabled={!data?.text}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground hover:text-foreground disabled:opacity-40"
            title="Copy article text"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-bull" /> : <Copy className="h-3.5 w-3.5" />}
          </button>

          {/* Open in new tab */}
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground hover:text-foreground"
            title="Open original article"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>

          {/* Close */}
          <button
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* ── Scrollable content ── */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto">

          {/* Loading */}
          {loading && (
            <div className="flex h-64 flex-col items-center justify-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Fetching article…
              </p>
            </div>
          )}

          {/* Error */}
          {!loading && data && !data.success && (
            <div className="flex flex-col items-center gap-4 px-8 py-16 text-center">
              <AlertCircle className="h-10 w-10 text-bear/60" />
              <div>
                <p className="font-semibold text-foreground">Could not extract article</p>
                <p className="mono mt-1 text-[11px] text-muted-foreground">{data.error}</p>
              </div>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="mono flex items-center gap-1.5 rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-[11px] uppercase tracking-wider text-primary hover:bg-primary/15"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                Open in browser instead
              </a>
            </div>
          )}

          {/* Article content */}
          {!loading && data?.success && (
            <article className="mx-auto max-w-[640px] px-6 py-8">

              {/* Hero image */}
              {data.image && (
                <div className="mb-6 overflow-hidden rounded-lg border border-border">
                  <img
                    src={proxyImage(data.image)}
                    alt={data.title}
                    className="h-[220px] w-full object-cover"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                  />
                </div>
              )}

              {/* Source badge */}
              <div className="mb-3 flex items-center gap-2">
                <span className="mono inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-2 py-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                  <BookOpen className="h-3 w-3" />
                  {data.source}
                </span>
                {data.read_mins > 0 && (
                  <span className="mono flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {data.read_mins} min read
                  </span>
                )}
                {data.word_count > 0 && (
                  <span className="mono text-[10px] text-muted-foreground">
                    · {data.word_count.toLocaleString()} words
                  </span>
                )}
              </div>

              {/* Title */}
              <h1 className="text-[22px] font-bold leading-tight tracking-tight text-foreground">
                {data.title || title}
              </h1>

              {/* Author */}
              {data.author && (
                <div className="mono mt-2 flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <User className="h-3 w-3" />
                  {data.author}
                </div>
              )}

              <div className="my-5 h-px bg-border" />

              {/* Article body */}
              <div
                className="article-body prose-custom"
                style={{ fontSize: `${fontSize}px` }}
                dangerouslySetInnerHTML={{ __html: data.content }}
              />

              {/* Bottom CTA */}
              <div className="mt-8 rounded-lg border border-border bg-surface/60 p-4">
                <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  Extracted via reader mode · original source
                </p>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mono mt-2 flex items-center gap-1.5 text-[12px] text-primary hover:underline"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  {url}
                </a>
              </div>
            </article>
          )}
        </div>
      </div>
    </>
  );
};