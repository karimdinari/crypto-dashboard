import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { DataProvider } from './context/DataContext'
import { TerminalProvider } from './context/TerminalContext'
import { AppShell } from './components/AppShell'
import { MarketTerminal } from './pages/MarketTerminal'
import { AssetAnalysis } from './pages/AssetAnalysis'
import { NewsSentiment } from './pages/NewsSentiment'
import { PredictionLab } from './pages/PredictionLab'
import { PipelineMonitor } from './pages/PipelineMonitor'
import { MarketsDirectory } from './pages/MarketsDirectory'
import { StreamingHub } from './pages/StreamingHub'
import { SentimentHub } from './pages/SentimentHub'
import { CorrelationsPage } from './pages/CorrelationsPage'
import { SettingsPage } from './pages/SettingsPage'
import { PortfolioTracker } from './pages/PortfolioTracker'
import { AlertsPage } from './pages/AlertsPage'

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <DataProvider>
          <TerminalProvider>
            <Routes>
              <Route element={<AppShell />}>
                <Route path="/" element={<MarketTerminal />} />
                <Route path="/markets" element={<MarketsDirectory />} />
                <Route path="/streaming" element={<StreamingHub />} />
                <Route path="/news" element={<NewsSentiment />} />
                <Route path="/sentiment" element={<SentimentHub />} />
                <Route path="/correlations" element={<CorrelationsPage />} />
                <Route path="/signals" element={<PredictionLab />} />
                <Route path="/prediction" element={<Navigate to="/signals" replace />} />
                <Route path="/pipeline" element={<PipelineMonitor />} />
                <Route path="/portfolio" element={<PortfolioTracker />} />
                <Route path="/alerts" element={<AlertsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/asset" element={<AssetAnalysis />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </TerminalProvider>
        </DataProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
