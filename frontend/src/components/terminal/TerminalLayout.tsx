import { ReactNode } from "react";
import { TerminalSidebar } from "./TerminalSidebar";
import { TerminalHeader } from "./TerminalHeader";
import { TickerTape } from "./TickerTape";

export const TerminalLayout = ({ children }: { children: ReactNode }) => {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <TerminalSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TerminalHeader />
        <TickerTape />
        <main className="flex-1 overflow-y-auto px-4 pb-8 pt-4 lg:px-6">
          <div className="animate-fade-in mx-auto w-full max-w-[1600px]">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
