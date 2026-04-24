import { useState, useEffect, useMemo } from "react";
import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AssetImage } from "@/components/AssetImage";
import { ASSETS } from "@/lib/market-data";
import { Wallet, Plus, Trash2, PieChart } from "lucide-react";

interface Position {
  id: string;
  symbol: string;
  qty: number;
  entryPrice: number;
}

const Portfolio = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [symbol, setSymbol] = useState("BTC/USD");
  const [qty, setQty] = useState("");
  const [price, setPrice] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("mat_portfolio");
    if (saved) {
      try { setPositions(JSON.parse(saved)); } catch (e) {}
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("mat_portfolio", JSON.stringify(positions));
  }, [positions]);

  const addPosition = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol || !qty || !price) return;
    const newPos = { id: crypto.randomUUID(), symbol, qty: Number(qty), entryPrice: Number(price) };
    setPositions([...positions, newPos]);
    setQty(""); setPrice("");
  };

  const removePosition = (id: string) => {
    setPositions(positions.filter(p => p.id !== id));
  };

  const enrichPositions = useMemo(() => {
    return positions.map(pos => {
      const asset = ASSETS.find(a => a.symbol === pos.symbol);
      const currentPrice = asset ? asset.price : pos.entryPrice;
      const currentValue = currentPrice * pos.qty;
      const entryValue = pos.entryPrice * pos.qty;
      const pnl = currentValue - entryValue;
      const pnlPct = (pnl / entryValue) * 100;
      return { ...pos, currentPrice, currentValue, pnl, pnlPct, asset };
    });
  }, [positions]);

  const totalValue = enrichPositions.reduce((s, p) => s + p.currentValue, 0);
  const totalCost = enrichPositions.reduce((s, p) => s + p.entryPrice * p.qty, 0);
  const totalPnl = totalValue - totalCost;
  const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost) * 100 : 0;

  return (
    <TerminalLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
              <Wallet className="h-6 w-6 text-primary" /> Portfolio Tracker
            </h1>
            <p className="text-sm text-muted-foreground mt-1">Local persistent paper-trading and position tracking.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-surface-2/40 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground">Total Value</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-mono font-semibold">${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-2/40 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground">Unrealized P&L</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-3xl font-mono font-semibold ${totalPnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                {totalPnl >= 0 ? '+' : ''}${totalPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <p className={`text-xs mt-1 ${totalPnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                {totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}% All-time
              </p>
            </CardContent>
          </Card>
          <Card className="bg-surface-2/40 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground">Positions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-mono font-semibold text-primary">{positions.length}</div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2 bg-card border-border/60">
            <CardHeader>
              <CardTitle className="text-sm">Current Holdings</CardTitle>
            </CardHeader>
            <CardContent>
              {enrichPositions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
                  <PieChart className="h-10 w-10 opacity-20 mb-3" />
                  <p className="text-sm">No positions yet. Add one below.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="border-border/60 hover:bg-transparent">
                      <TableHead>Asset</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Entry</TableHead>
                      <TableHead className="text-right">Current</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead className="text-right">P&L</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {enrichPositions.map(pos => (
                      <TableRow key={pos.id} className="border-border/40 font-mono text-sm hover:bg-surface-2/30">
                        <TableCell className="font-semibold text-foreground">
                          {pos.symbol}
                          {pos.asset && <Badge variant="outline" className="ml-2 text-[9px] h-4 tracking-wider">{pos.asset.class}</Badge>}
                        </TableCell>
                        <TableCell className="text-right">{pos.qty}</TableCell>
                        <TableCell className="text-right">${pos.entryPrice.toLocaleString()}</TableCell>
                        <TableCell className="text-right">${pos.currentPrice.toLocaleString()}</TableCell>
                        <TableCell className="text-right">${pos.currentValue.toLocaleString()}</TableCell>
                        <TableCell className={`text-right ${pos.pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                          {pos.pnl >= 0 ? '+' : ''}{pos.pnlPct.toFixed(2)}%
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => removePosition(pos.id)}>
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Card className="bg-card border-border/60">
            <CardHeader>
              <CardTitle className="text-sm">Add Position</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={addPosition} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Asset Symbol</label>
                  <select 
                    value={symbol} onChange={e => setSymbol(e.target.value)}
                    className="flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {ASSETS.map(a => <option key={a.symbol} value={a.symbol} className="bg-popover text-popover-foreground">{a.symbol} - {a.name}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Quantity</label>
                  <Input type="number" step="any" placeholder="e.g. 0.5" value={qty} onChange={e => setQty(e.target.value)} required />
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Entry Price</label>
                  <Input type="number" step="any" placeholder="e.g. 64000" value={price} onChange={e => setPrice(e.target.value)} required />
                </div>
                <Button type="submit" className="w-full gap-2">
                  <Plus className="h-4 w-4" /> Add to Portfolio
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </TerminalLayout>
  );
};

export default Portfolio;
