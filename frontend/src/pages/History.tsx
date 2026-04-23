import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Database, Search } from "lucide-react";
import { CANDLES } from "@/lib/market-data";
import { useState } from "react";

const History = () => {
  const [search, setSearch] = useState("");

  const filteredData = CANDLES.filter(c => 
    new Date(c.t).toLocaleString().toLowerCase().includes(search.toLowerCase())
  );

  return (
    <TerminalLayout>
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-border pb-4 gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
              <Database className="h-6 w-6 text-primary" /> Batch History
            </h1>
            <p className="text-sm text-muted-foreground mt-1">Explore raw historical batch data (OHLCV) stored in the lakehouse.</p>
          </div>
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              type="search" 
              placeholder="Search by date/time..." 
              className="pl-9 bg-surface-2/30"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <Card className="bg-card border-border/60">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">BTC/USD Historical Data</CardTitle>
            <div className="text-xs text-muted-foreground font-mono">Total Records: {CANDLES.length}</div>
          </CardHeader>
          <CardContent>
            <div className="h-[600px] overflow-auto border border-border/40 rounded-md">
              <Table>
                <TableHeader className="sticky top-0 bg-card z-10 shadow-sm">
                  <TableRow className="border-border/60 hover:bg-transparent">
                    <TableHead>Timestamp</TableHead>
                    <TableHead className="text-right">Open</TableHead>
                    <TableHead className="text-right">High</TableHead>
                    <TableHead className="text-right">Low</TableHead>
                    <TableHead className="text-right">Close</TableHead>
                    <TableHead className="text-right">Volume</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredData.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                        No records found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredData.map((row, i) => {
                      const isUp = row.c >= row.o;
                      const date = new Date(row.t);
                      return (
                        <TableRow key={i} className="border-border/40 font-mono text-sm hover:bg-surface-2/30">
                          <TableCell className="text-muted-foreground whitespace-nowrap">
                            {date.toLocaleDateString()} {date.toLocaleTimeString()}
                          </TableCell>
                          <TableCell className="text-right">${row.o.toLocaleString(undefined, { minimumFractionDigits: 2 })}</TableCell>
                          <TableCell className="text-right">${row.h.toLocaleString(undefined, { minimumFractionDigits: 2 })}</TableCell>
                          <TableCell className="text-right">${row.l.toLocaleString(undefined, { minimumFractionDigits: 2 })}</TableCell>
                          <TableCell className={`text-right font-medium ${isUp ? 'text-bull' : 'text-bear'}`}>
                            ${row.c.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </TableCell>
                          <TableCell className="text-right text-muted-foreground">{row.v.toLocaleString()}</TableCell>
                        </TableRow>
                      )
                    })
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </TerminalLayout>
  );
};

export default History;
