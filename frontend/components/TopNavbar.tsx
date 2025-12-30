"use client";

import { FileText } from "lucide-react";
import StatusBadge from "./StatusBadge";

interface TopNavbarProps {
  isPDFLoaded: boolean;
  isProcessing?: boolean;
}

export default function TopNavbar({
  isPDFLoaded,
  isProcessing = false,
}: TopNavbarProps) {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/95 backdrop-blur-xl supports-[backdrop-filter]:bg-background/80 shadow-sm">
      <div className="container flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 ring-2 ring-primary/10 shadow-sm">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <div className="text-left">
            <h1 className="text-lg font-semibold tracking-tight text-left">PDF Intelligence Assistant</h1>
            <p className="text-xs text-muted-foreground/80 text-left">Enterprise AI Document Assistant</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <StatusBadge isPDFLoaded={isPDFLoaded} isProcessing={isProcessing} />
        </div>
      </div>
    </nav>
  );
}

