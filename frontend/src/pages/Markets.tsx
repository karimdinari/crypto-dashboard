import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { AssetImage } from "@/components/AssetImage";
import { ASSETS } from "@/lib/market-data";
import { Sparkline } from "@/components/terminal/Sparkline";
import { Search, ArrowRight } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

const Markets = () => {
  const [search, setSearch] = useState("");
  
  const filteredAssets = ASSETS.filter(a => 
    a.symbol.toLowerCase().includes(search.toLowerCase()) || 
    a.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <TerminalLayout>
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-border pb-4 gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">Markets Directory</h1>
            <p className="text-sm text-muted-foreground mt-1">Browse and search the complete multi-asset universe.</p>
          </div>
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              type="search" 
              placeholder="Search symbol or name..." 
              className="pl-9 bg-surface-2/30"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <Card className="bg-card border-border/60">
          <CardHeader>
            <CardTitle className="text-sm">Asset Universe</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow className="border-border/60 hover:bg-transparent">
                  <TableHead>Asset</TableHead>
                  <TableHead>Class</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">24h Change</TableHead>
                  <TableHead className="w-[150px] text-right">Trend (24h)</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAssets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      No assets found matching "{search}".
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredAssets.map(asset => (
                    <TableRow key={asset.symbol} className="border-border/40 hover:bg-surface-2/30 transition-colors">
                      <TableCell>
                        <Link to={`/asset/${asset.symbol.replace("/", "-")}`} className="flex items-center gap-2 font-semibold text-foreground hover:text-primary transition-colors">
                          <AssetImage symbol={asset.symbol} size="sm" showBorder={false} />
                          <div>
                            <div>{asset.symbol}</div>
                            <div className="text-xs text-muted-foreground font-normal">{asset.name}</div>
                          </div>
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={`text-[10px] uppercase tracking-wider ${asset.class === 'crypto' ? 'text-crypto border-crypto/30 bg-crypto/5' : asset.class === 'forex' ? 'text-forex border-forex/30 bg-forex/5' : 'text-metals border-metals/30 bg-metals/5'}`}>
                          {asset.class}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        ${asset.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 })}
                      </TableCell>
                      <TableCell className={`text-right font-mono text-sm ${asset.change >= 0 ? 'text-bull' : 'text-bear'}`}>
                        {asset.change >= 0 ? '+' : ''}{asset.change.toFixed(2)}%
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="h-8 w-full">
                          <Sparkline data={asset.spark} color={asset.change >= 0 ? "hsl(var(--bull))" : "hsl(var(--bear))"} />
                        </div>
                      </TableCell>
                      <TableCell>
                        <Link to={`/asset/${asset.symbol.replace("/", "-")}`} className="text-muted-foreground hover:text-foreground">
                          <ArrowRight className="h-4 w-4" />
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </TerminalLayout>
  );
};

export default Markets;
