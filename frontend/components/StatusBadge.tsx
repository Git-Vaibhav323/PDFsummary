"use client";

import { Badge } from "./ui/badge";
import { Loader2, CheckCircle2, XCircle, AlertCircle } from "lucide-react";

interface StatusBadgeProps {
  isPDFLoaded: boolean;
  isProcessing?: boolean;
  hasError?: boolean;
}

export default function StatusBadge({
  isPDFLoaded,
  isProcessing = false,
  hasError = false,
}: StatusBadgeProps) {
  if (hasError) {
    return (
      <Badge variant="destructive" className="gap-1.5 px-3 py-1.5 shadow-sm">
        <AlertCircle className="h-3.5 w-3.5" />
        <span className="font-medium">Error</span>
      </Badge>
    );
  }

  if (isProcessing) {
    return (
      <Badge variant="warning" className="gap-1.5 px-3 py-1.5 shadow-sm">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        <span className="font-medium">Processing</span>
      </Badge>
    );
  }

  if (isPDFLoaded) {
    return (
      <Badge variant="success" className="gap-1.5 px-3 py-1.5 shadow-sm">
        <CheckCircle2 className="h-3.5 w-3.5" />
        <span className="font-medium">Ready</span>
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="gap-1.5 px-3 py-1.5 border-border/50">
      <XCircle className="h-3.5 w-3.5" />
      <span className="font-medium">No PDF</span>
    </Badge>
  );
}

