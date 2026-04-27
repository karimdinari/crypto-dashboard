import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { StreamingPanel } from "@/components/terminal/StreamingPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Radio, Server, Activity, Database } from "lucide-react";

const Streaming = () => {
  return (
    <TerminalLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
              <Radio className="h-6 w-6 text-primary" /> Streaming Hub
            </h1>
            <p className="text-sm text-muted-foreground mt-1">Live Kafka data ingestion and raw tick monitor.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-surface-2/40 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Server className="h-3 w-3" /> Connection Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-semibold text-bull flex items-center gap-2">
                <span className="pulse-dot bg-bull" /> Connected
              </div>
              <p className="text-xs text-muted-foreground mt-1 font-mono">wss://stream.market-analytics.net</p>
            </CardContent>
          </Card>

          <Card className="bg-surface-2/40 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Activity className="h-3 w-3" /> Throughput
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-mono font-semibold text-foreground">
                2,419 <span className="text-sm text-muted-foreground font-sans">msg/sec</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">Peak: 3,842 msg/sec</p>
            </CardContent>
          </Card>

          <Card className="bg-surface-2/40 border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Database className="h-3 w-3" /> Bronze Layer
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-mono font-semibold text-foreground">
                14.2 <span className="text-sm text-muted-foreground font-sans">GB</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">Ingested today (rolling 24h)</p>
            </CardContent>
          </Card>
        </div>

        <div className="h-[600px] overflow-hidden rounded-xl border border-border/80">
          <StreamingPanel />
        </div>
      </div>
    </TerminalLayout>
  );
};

export default Streaming;
