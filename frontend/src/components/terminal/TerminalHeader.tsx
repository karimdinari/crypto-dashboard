import { Search, Bell, RefreshCw, Command, ChevronDown, Globe2 } from "lucide-react";

export const TerminalHeader = () => {
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  return (
    <header className="relative flex h-14 shrink-0 items-center gap-3 border-b border-border bg-surface/50 px-4 backdrop-blur-xl lg:px-6">
      {/* Mobile brand */}
      <div className="flex items-center gap-2 lg:hidden">
        <div className="relative flex h-7 w-7 items-center justify-center">
          <span className="absolute inset-0 rounded-md bg-gradient-to-br from-crypto via-forex to-metals" />
          <span className="absolute inset-[2px] rounded-[5px] bg-background" />
          <span className="relative mono text-[10px] font-bold brand-mark">M</span>
        </div>
        <span className="text-sm font-semibold brand-mark">MAT/01</span>
      </div>

      {/* Page title + market session */}
      <div className="hidden flex-col leading-tight md:flex">
        <div className="flex items-center gap-2">
          <h1 className="text-[13px] font-semibold tracking-tight">Market Analytics Terminal</h1>
          <span className="mono rounded border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-[0.18em] text-primary">v3.2</span>
        </div>
        <p className="mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
          Multi-asset · Real-time · Predictive intelligence
        </p>
      </div>

      <div className="mx-3 hidden h-7 w-px bg-border md:block" />

      {/* Global market session */}
      <div className="hidden items-center gap-3 md:flex">
        <SessionBadge label="LDN" status="open" />
        <SessionBadge label="NY" status="open" />
        <SessionBadge label="TKY" status="closed" />
      </div>

      {/* Search */}
      <div className="ml-auto flex max-w-md flex-1 items-center">
        <div className="group relative flex w-full items-center">
          <Search className="absolute left-3 h-3.5 w-3.5 text-muted-foreground" />
          <input
            placeholder="Search asset, news, signal…"
            className="mono h-9 w-full rounded-md border border-border bg-surface pl-9 pr-16 text-[12px] tracking-tight outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-primary/50 focus:shadow-[0_0_0_3px_hsl(var(--primary)/0.12)]"
          />
          <kbd className="mono pointer-events-none absolute right-2 inline-flex items-center gap-1 rounded border border-border bg-surface-2 px-1.5 py-0.5 text-[9px] text-muted-foreground">
            <Command className="h-2.5 w-2.5" /> K
          </kbd>
        </div>
      </div>

      {/* Right cluster */}
      <div className="flex items-center gap-2">
        <PipelineHealth />
        <div className="hidden items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1.5 md:flex">
          <RefreshCw className="h-3 w-3 text-muted-foreground" />
          <span className="mono text-[11px] text-muted-foreground">UTC</span>
          <span className="mono text-[11px] font-medium num">{now}</span>
        </div>
        <button className="relative flex h-9 w-9 items-center justify-center rounded-md border border-border bg-surface text-muted-foreground transition-colors hover:text-foreground">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-bear shadow-[0_0_8px_hsl(var(--bear))]" />
        </button>
        <button className="flex items-center gap-2 rounded-md border border-border bg-surface px-2 py-1.5 transition-colors hover:bg-surface-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-sm bg-gradient-to-br from-forex via-crypto to-metals text-[10px] font-bold text-background">
            JT
          </div>
          <span className="hidden text-[12px] font-medium md:inline">J. Trader</span>
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        </button>
      </div>
    </header>
  );
};

const SessionBadge = ({ label, status }: { label: string; status: "open" | "closed" }) => (
  <div className="flex items-center gap-1.5">
    <span className={`h-1.5 w-1.5 rounded-full ${status === "open" ? "bg-bull shadow-[0_0_8px_hsl(var(--bull))]" : "bg-muted"}`} />
    <span className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
  </div>
);

const PipelineHealth = () => (
  <div className="hidden items-center gap-1 rounded-md border border-border bg-surface px-2 py-1.5 lg:flex">
    <Globe2 className="mr-0.5 h-3 w-3 text-muted-foreground" />
    <span className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Pipelines</span>
    <span className="mx-1 h-3 w-px bg-border" />
    <Tier label="B" color="bg-bronze" />
    <Tier label="S" color="bg-silver" />
    <Tier label="G" color="bg-gold" />
  </div>
);

const Tier = ({ label, color }: { label: string; color: string }) => (
  <span className={`mono inline-flex h-4 w-4 items-center justify-center rounded-sm text-[9px] font-bold text-background ${color}`}>{label}</span>
);
