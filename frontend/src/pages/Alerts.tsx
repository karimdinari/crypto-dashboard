import { useState, useEffect } from "react";
import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ASSETS } from "@/lib/market-data";
import { Bell, Plus, Trash2, Zap } from "lucide-react";

interface Alert {
  id: string;
  symbol: string;
  condition: "above" | "below";
  targetPrice: number;
  initialPrice: number;
}

const Alerts = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [symbol, setSymbol] = useState("BTC/USD");
  const [target, setTarget] = useState("");
  const [condition, setCondition] = useState<"above" | "below">("above");

  useEffect(() => {
    const saved = localStorage.getItem("mat_alerts");
    if (saved) {
      try { setAlerts(JSON.parse(saved)); } catch (e) {}
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("mat_alerts", JSON.stringify(alerts));
  }, [alerts]);

  const addAlert = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol || !target) return;
    const asset = ASSETS.find(a => a.symbol === symbol);
    if (!asset) return;
    
    const newAlert: Alert = {
      id: crypto.randomUUID(),
      symbol,
      condition,
      targetPrice: Number(target),
      initialPrice: asset.price
    };
    setAlerts([...alerts, newAlert]);
    setTarget("");
  };

  const removeAlert = (id: string) => {
    setAlerts(alerts.filter(a => a.id !== id));
  };

  const activeAlerts = alerts.map(alert => {
    const asset = ASSETS.find(a => a.symbol === alert.symbol);
    const currentPrice = asset ? asset.price : alert.initialPrice;
    
    const isTriggered = alert.condition === "above" 
      ? currentPrice >= alert.targetPrice
      : currentPrice <= alert.targetPrice;
      
    // Calculate progress (0 to 100%)
    let progress = 0;
    if (alert.condition === "above") {
      if (currentPrice >= alert.targetPrice) progress = 100;
      else if (currentPrice <= alert.initialPrice) progress = 0;
      else progress = ((currentPrice - alert.initialPrice) / (alert.targetPrice - alert.initialPrice)) * 100;
    } else {
      if (currentPrice <= alert.targetPrice) progress = 100;
      else if (currentPrice >= alert.initialPrice) progress = 0;
      else progress = ((alert.initialPrice - currentPrice) / (alert.initialPrice - alert.targetPrice)) * 100;
    }

    return { ...alert, currentPrice, isTriggered, progress };
  });

  const triggeredCount = activeAlerts.filter(a => a.isTriggered).length;

  return (
    <TerminalLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
              <Bell className="h-6 w-6 text-primary" /> Price Alerts
            </h1>
            <p className="text-sm text-muted-foreground mt-1">Cross-asset local alert triggers.</p>
          </div>
          <div className="flex gap-4">
            <div className="text-center">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Active</p>
              <p className="font-mono text-xl">{alerts.length - triggeredCount}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Triggered</p>
              <p className="font-mono text-xl text-primary">{triggeredCount}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="bg-card border-border/60 h-fit">
            <CardHeader>
              <CardTitle className="text-sm">Create Alert</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={addAlert} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Asset Symbol</label>
                  <select 
                    value={symbol} onChange={e => setSymbol(e.target.value)}
                    className="flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                  >
                    {ASSETS.map(a => <option key={a.symbol} value={a.symbol} className="bg-popover text-popover-foreground">{a.symbol}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Condition</label>
                  <div className="grid grid-cols-2 gap-2">
                    <Button 
                      type="button" 
                      variant={condition === "above" ? "default" : "outline"}
                      onClick={() => setCondition("above")}
                      className={condition === "above" ? "bg-bull hover:bg-bull/90 text-bull-foreground" : ""}
                    >
                      Crosses Above
                    </Button>
                    <Button 
                      type="button" 
                      variant={condition === "below" ? "default" : "outline"}
                      onClick={() => setCondition("below")}
                      className={condition === "below" ? "bg-bear hover:bg-bear/90 text-bear-foreground" : ""}
                    >
                      Crosses Below
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Target Price</label>
                  <Input type="number" step="any" placeholder="Target value..." value={target} onChange={e => setTarget(e.target.value)} required />
                  <p className="text-[10px] text-muted-foreground text-right">Current: {ASSETS.find(a => a.symbol === symbol)?.price}</p>
                </div>
                <Button type="submit" className="w-full gap-2">
                  <Plus className="h-4 w-4" /> Set Alert
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="lg:col-span-2 space-y-3">
            {activeAlerts.length === 0 ? (
              <Card className="border-dashed border-border/40 bg-transparent flex flex-col items-center justify-center h-48">
                <Bell className="h-8 w-8 text-muted-foreground/30 mb-2" />
                <p className="text-sm text-muted-foreground">No alerts set.</p>
              </Card>
            ) : (
              activeAlerts.map(alert => (
                <Card key={alert.id} className={`border-l-4 transition-colors ${alert.isTriggered ? 'border-l-primary bg-primary/5' : 'border-l-muted bg-card'}`}>
                  <div className="p-4 flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="font-semibold text-foreground">{alert.symbol}</span>
                        {alert.isTriggered ? (
                          <Badge variant="default" className="bg-primary text-primary-foreground text-[10px] uppercase h-5 animate-pulse">
                            <Zap className="h-3 w-3 mr-1" /> Triggered
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px] uppercase h-5">Active</Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Alert me when price goes <strong className={alert.condition === 'above' ? 'text-bull' : 'text-bear'}>{alert.condition}</strong> {alert.targetPrice.toLocaleString()}
                      </p>
                      
                      {!alert.isTriggered && (
                        <div className="mt-3 flex items-center gap-3">
                          <span className="text-[10px] font-mono text-muted-foreground">{alert.initialPrice}</span>
                          <Progress value={alert.progress} className="h-1.5 flex-1 bg-surface-2" />
                          <span className="text-[10px] font-mono text-muted-foreground">{alert.targetPrice}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="ml-6 flex flex-col items-end gap-2">
                      <div className="font-mono font-medium text-lg">
                        {alert.currentPrice.toLocaleString()}
                      </div>
                      <Button variant="ghost" size="sm" className="h-7 px-2 text-xs text-muted-foreground hover:text-destructive" onClick={() => removeAlert(alert.id)}>
                        <Trash2 className="h-3 w-3 mr-1" /> Remove
                      </Button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>
    </TerminalLayout>
  );
};

export default Alerts;
