import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AlertsProvider } from "@/context/AlertsContext";
import Index from "./pages/Index.tsx";
import NotFound from "./pages/NotFound.tsx";
import AssetDetail from "./pages/AssetDetail.tsx";
import News from "./pages/News.tsx";
import Correlations from "./pages/Correlations.tsx";
import Pipeline from "./pages/Pipeline.tsx";
import Streaming from "./pages/Streaming.tsx";
import Portfolio from "./pages/Portfolio.tsx";
import Alerts from "./pages/Alerts.tsx";
import History from "./pages/History.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AlertsProvider>          {/* ← must be inside QueryClientProvider so useAssets/useLatestStream work */}
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/asset/:symbol" element={<AssetDetail />} />
            <Route path="/streaming" element={<Streaming />} />
            <Route path="/news" element={<News />} />
            <Route path="/correlations" element={<Correlations />} />
            <Route path="/history" element={<History />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/settings" element={<Index />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AlertsProvider>
  </QueryClientProvider>
);

export default App;