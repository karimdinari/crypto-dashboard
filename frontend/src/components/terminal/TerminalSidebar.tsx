import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard, LineChart, Radio, Newspaper, Smile,
  Grid3x3, Brain, Workflow, Settings, Wallet, Bell, Database
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/",              label: "Dashboard",     icon: LayoutDashboard, kbd: "D" },
  { to: "/markets",       label: "Markets",       icon: LineChart,       kbd: "M" },
  { to: "/streaming",     label: "Streaming",     icon: Radio,           kbd: "S" },
  { to: "/news",          label: "News",          icon: Newspaper,       kbd: "N" },
  { to: "/correlations",  label: "Correlations",  icon: Grid3x3,         kbd: "C" },
  { to: "/history",       label: "Batch History", icon: Database,        kbd: "H" },
  { to: "/portfolio",     label: "Portfolio",     icon: Wallet,          kbd: "O" },
  { to: "/alerts",        label: "Alerts",        icon: Bell,            kbd: "L" },
  { to: "/pipeline",      label: "Pipeline",      icon: Workflow,        kbd: "P" },
];

export const TerminalSidebar = () => {
  const { pathname } = useLocation();
  return (
    <aside className="hidden w-[244px] shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
      {/* Brand */}
      <div className="flex h-14 items-center gap-3 border-b border-sidebar-border px-5">
        <BrandMark />
        <div className="flex flex-col leading-none">
          <span className="text-[14px] font-semibold tracking-tight brand-mark">MAT/01</span>
          <span className="mono text-[9px] uppercase tracking-[0.22em] text-sidebar-foreground/55">Market Terminal</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2.5 py-4">
        <p className="mono px-2 pb-2 text-[10px] uppercase tracking-[0.22em] text-sidebar-foreground/40">Workspaces</p>
        <ul className="space-y-0.5">
          {NAV.map(({ to, label, icon: Icon, kbd }) => {
            const active = to === "/" ? pathname === "/" : pathname.startsWith(to);
            return (
              <li key={to}>
                <NavLink
                  to={to}
                  className={cn(
                    "group relative flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium transition-colors",
                    active
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                  )}
                >
                  {active && <span className="absolute inset-y-1.5 left-0 w-[2px] rounded-full bg-primary shadow-[0_0_12px_hsl(var(--primary))]" />}
                  <Icon className={cn("h-4 w-4 shrink-0", active ? "text-primary" : "text-sidebar-foreground/65 group-hover:text-sidebar-accent-foreground")} />
                  <span className="truncate">{label}</span>
                  <kbd className="mono ml-auto hidden rounded border border-sidebar-border bg-sidebar-accent/50 px-1 text-[9px] text-sidebar-foreground/55 group-hover:inline">{kbd}</kbd>
                </NavLink>
              </li>
            );
          })}
        </ul>

        <p className="mono mt-6 px-2 pb-2 text-[10px] uppercase tracking-[0.22em] text-sidebar-foreground/40">System</p>
        <ul className="space-y-0.5">
          <li>
            <NavLink to="/settings" className="group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground">
              <Settings className="h-4 w-4 text-sidebar-foreground/65" />
              Settings
            </NavLink>
          </li>
        </ul>

        
      </nav>

      {/* Footer status */}
      <div className="border-t border-sidebar-border p-3">
        <div className="rounded-md border border-sidebar-border/70 bg-sidebar-accent/30 p-2.5">
          <div className="flex items-center justify-between">
            <span className="mono text-[10px] uppercase tracking-[0.18em] text-sidebar-foreground/60">Cluster</span>
            <span className="flex items-center gap-1.5 text-[11px] font-medium text-bull">
              <span className="pulse-dot bg-bull" /> Healthy
            </span>
          </div>
          <div className="mono mt-1.5 flex justify-between text-[10px] text-sidebar-foreground/55">
            <span>kafka-prod-eu</span>
            <span>v3.2.1</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

const BrandMark = () => (
  <div className="relative flex h-8 w-8 items-center justify-center">
    <span className="absolute inset-0 rounded-md bg-gradient-to-br from-crypto via-forex to-metals opacity-90" />
    <span className="absolute inset-[2px] rounded-[5px] bg-sidebar" />
    <svg viewBox="0 0 24 24" className="relative h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 17 L8 11 L12 14 L16 6 L21 12" stroke="hsl(var(--crypto))" />
      <circle cx="16" cy="6" r="1.6" fill="hsl(var(--metals))" stroke="hsl(var(--metals))" />
    </svg>
  </div>
);
