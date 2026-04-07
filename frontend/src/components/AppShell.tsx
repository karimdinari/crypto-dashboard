import { NavLink, Outlet } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'

const nav = [
  { to: '/', label: 'Market Terminal', end: true },
  { to: '/asset', label: 'Asset Analysis' },
  { to: '/news', label: 'News & Sentiment' },
  { to: '/prediction', label: 'Prediction Lab' },
  { to: '/pipeline', label: 'Pipeline Monitor' },
]

const navBtn =
  'rounded-md px-2.5 py-2 text-xs font-medium transition-colors duration-150 active:scale-[0.98] md:py-1.5'

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-terminal-border bg-terminal-elevated text-terminal-muted transition-all duration-150 hover:border-terminal-muted hover:text-terminal-text active:scale-95 md:h-9 md:w-9"
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-pressed={!isDark}
    >
      {isDark ? (
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden
        >
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
        </svg>
      ) : (
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden
        >
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  )
}

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <header className="sticky top-0 z-50 border-b border-terminal-border bg-terminal-surface/95 backdrop-blur-md supports-[backdrop-filter]:bg-terminal-surface/80">
        <div className="mx-auto flex max-w-[1800px] flex-wrap items-center justify-between gap-3 px-3 py-2.5 md:px-4">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-gradient-to-br from-brand to-amber-600 text-xs font-bold text-white shadow-sm">
              T
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-terminal-muted">
                Tigre Analytics
              </p>
              <p className="truncate text-sm font-semibold leading-tight text-terminal-text md:text-base">
                Multi-Market Terminal
              </p>
            </div>
          </div>
          <div className="flex w-full min-w-0 flex-[1_1_100%] items-center gap-2 sm:w-auto sm:flex-[unset] md:min-w-0">
            <ThemeToggle />
            <nav
              className="flex min-w-0 flex-1 flex-nowrap items-center gap-0.5 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] sm:flex-initial sm:flex-wrap sm:overflow-visible sm:pb-0 [&::-webkit-scrollbar]:hidden"
              aria-label="Primary"
            >
              {nav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    [
                      navBtn,
                      'shrink-0 whitespace-nowrap',
                      isActive
                        ? 'bg-terminal-elevated text-terminal-text ring-1 ring-accent/50'
                        : 'text-terminal-muted hover:bg-terminal-elevated/80 hover:text-terminal-text',
                    ].join(' ')
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </header>
      <main id="main-content" className="flex-1 outline-none" tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="border-t border-terminal-border bg-terminal-surface px-4 py-3 text-center text-[10px] leading-relaxed text-terminal-muted md:px-6">
        Charts by{' '}
        <a
          href="https://www.tradingview.com/"
          target="_blank"
          rel="noreferrer"
          className="text-accent underline-offset-2 hover:underline"
        >
          TradingView
        </a>{' '}
        Lightweight Charts™ · Demo UI · connect your data pipeline
      </footer>
    </div>
  )
}
