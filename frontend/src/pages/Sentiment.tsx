import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { SentimentPanel } from "@/components/terminal/SentimentPanel";
import { NewsPanel } from "@/components/terminal/NewsPanel";
import { Smile } from "lucide-react";

const Sentiment = () => {
  return (
    <TerminalLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
              <Smile className="h-6 w-6 text-primary" /> Market Sentiment
            </h1>
            <p className="text-sm text-muted-foreground mt-1">NLP-driven news sentiment scoring and aggregate market mood.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-1 space-y-4">
            <SentimentPanel />
            <div className="rounded-xl border border-border/60 bg-surface-2/20 p-5">
              <h3 className="text-sm font-semibold mb-2">How it works</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Our pipeline continuously ingests RSS feeds from major financial outlets. Each headline is processed through an NLP model fine-tuned for financial sentiment, producing a score from -1.0 (bearish) to +1.0 (bullish).
              </p>
            </div>
          </div>
          <div className="lg:col-span-2">
            <NewsPanel />
          </div>
        </div>
      </div>
    </TerminalLayout>
  );
};

export default Sentiment;
