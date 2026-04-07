import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { ASSETS } from '../data/mock'
import { useData } from './DataContext'
import type { MarketType, Timeframe } from '../types'

export type ChartStyle = 'candle' | 'line'

interface TerminalState {
  selectedSymbol: string
  setSelectedSymbol: (s: string) => void
  timeframe: Timeframe
  setTimeframe: (t: Timeframe) => void
  marketFilter: MarketType | 'all'
  setMarketFilter: (m: MarketType | 'all') => void
  chartStyle: ChartStyle
  setChartStyle: (c: ChartStyle) => void
  watchlistQuery: string
  setWatchlistQuery: (q: string) => void
}

const TerminalContext = createContext<TerminalState | null>(null)

export function TerminalProvider({ children }: { children: ReactNode }) {
  const { assets } = useData()
  const [selectedSymbol, setSelectedSymbol] = useState(ASSETS[0].symbol)
  const [timeframe, setTimeframe] = useState<Timeframe>('1D')
  const [marketFilter, setMarketFilter] = useState<MarketType | 'all'>('all')
  const [chartStyle, setChartStyle] = useState<ChartStyle>('candle')
  const [watchlistQuery, setWatchlistQuery] = useState('')

  useEffect(() => {
    if (!assets.length) return
    if (!assets.some((a) => a.symbol === selectedSymbol)) {
      setSelectedSymbol(assets[0].symbol)
    }
  }, [assets, selectedSymbol])

  const setSymbol = useCallback((s: string) => {
    setSelectedSymbol(s)
  }, [])

  const value = useMemo(
    () => ({
      selectedSymbol,
      setSelectedSymbol: setSymbol,
      timeframe,
      setTimeframe,
      marketFilter,
      setMarketFilter,
      chartStyle,
      setChartStyle,
      watchlistQuery,
      setWatchlistQuery,
    }),
    [
      selectedSymbol,
      setSymbol,
      timeframe,
      marketFilter,
      chartStyle,
      watchlistQuery,
    ],
  )

  return (
    <TerminalContext.Provider value={value}>{children}</TerminalContext.Provider>
  )
}

export function useTerminal() {
  const ctx = useContext(TerminalContext)
  if (!ctx) {
    throw new Error('useTerminal must be used within TerminalProvider')
  }
  return ctx
}
