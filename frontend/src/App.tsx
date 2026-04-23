import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Index from "./pages/Index.tsx";
import NotFound from "./pages/NotFound.tsx";
import AssetDetail from "./pages/AssetDetail.tsx";
import News from "./pages/News.tsx";
import Correlations from "./pages/Correlations.tsx";
import Pipeline from "./pages/Pipeline.tsx";
import Markets from "./pages/Markets.tsx";
import Streaming from "./pages/Streaming.tsx";
import Portfolio from "./pages/Portfolio.tsx";
import Alerts from "./pages/Alerts.tsx";
import Sentiment from "./pages/Sentiment.tsx";
import History from "./pages/History.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/markets" element={<Markets />} />
          <Route path="/asset/:symbol" element={<AssetDetail />} />
          <Route path="/streaming" element={<Streaming />} />
          <Route path="/news" element={<News />} />
          <Route path="/sentiment" element={<Sentiment />} />
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
  </QueryClientProvider>
);

export default App;
