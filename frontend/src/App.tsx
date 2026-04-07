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

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <DataProvider>
          <TerminalProvider>
            <Routes>
              <Route element={<AppShell />}>
                <Route path="/" element={<MarketTerminal />} />
                <Route path="/asset" element={<AssetAnalysis />} />
                <Route path="/news" element={<NewsSentiment />} />
                <Route path="/prediction" element={<PredictionLab />} />
                <Route path="/pipeline" element={<PipelineMonitor />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </TerminalProvider>
        </DataProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
