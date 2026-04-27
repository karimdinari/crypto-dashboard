import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useAssets, useLatestStream } from "@/lib/api";

interface Alert {
  id: string;
  symbol: string;
  condition: "above" | "below";
  targetPrice: number;
  initialPrice: number;
}

interface AlertsContextValue {
  alerts: Alert[];
  triggeredCount: number;
}

const AlertsContext = createContext<AlertsContextValue>({ alerts: [], triggeredCount: 0 });

export const AlertsProvider = ({ children }: { children: ReactNode }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const { data: streamTicks = [] } = useLatestStream();   // real-time prices, refetches every 5s
  const { data: assets = [] } = useAssets();              // fallback snapshot + metadata

  // Sync alerts from localStorage (cross-tab + same-tab writes from Alerts page)
  useEffect(() => {
    const load = () => {
      try {
        const saved = localStorage.getItem("mat_alerts");
        if (saved) setAlerts(JSON.parse(saved));
      } catch {}
    };
    load();
    window.addEventListener("storage", load);
    // Poll every 2s to catch same-tab writes (Alerts page writing to localStorage)
    const interval = setInterval(load, 2000);
    return () => {
      window.removeEventListener("storage", load);
      clearInterval(interval);
    };
  }, []);

  const triggeredCount = alerts.filter(alert => {
    const tick = streamTicks.find(t => t.symbol === alert.symbol);
    const asset = assets.find(a => a.symbol === alert.symbol);
    const currentPrice = tick?.price ?? asset?.price ?? alert.initialPrice;
    return alert.condition === "above"
      ? currentPrice >= alert.targetPrice
      : currentPrice <= alert.targetPrice;
  }).length;

  return (
    <AlertsContext.Provider value={{ alerts, triggeredCount }}>
      {children}
    </AlertsContext.Provider>
  );
};

export const useAlertsContext = () => useContext(AlertsContext);