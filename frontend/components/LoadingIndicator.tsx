"use client";

import { Bot } from "lucide-react";

export default function LoadingIndicator() {
  return (
    <div className="flex gap-4 animate-fade-in">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/80 ring-2 ring-border/50 shadow-sm">
        <Bot className="h-4.5 w-4.5 text-foreground animate-pulse" />
      </div>
      <div className="flex flex-1 items-center">
        <div className="rounded-xl border border-border/50 bg-card/80 px-4 py-3 shadow-sm">
          <div className="flex gap-1.5">
            <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.3s]" />
            <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.15s]" />
            <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60" />
          </div>
        </div>
      </div>
    </div>
  );
}

