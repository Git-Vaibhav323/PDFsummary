"use client";

import { TrendingUp } from "lucide-react";

interface FinanceAgentProps {
  onOpenFinanceAgent: () => void;
  disabled?: boolean;
  isProcessing?: boolean;
  processedCount?: number;
}

export default function FinanceAgent({
  onOpenFinanceAgent,
  disabled = false,
  isProcessing = false,
  processedCount = 0,
}: FinanceAgentProps) {
  // Button is clickable when PDF is loaded, processing starts on click
  const isDisabledBtn = disabled;
  const isReady = !isProcessing && processedCount === 10;
  
  return (
    <div className="space-y-2">
      <button
        onClick={onOpenFinanceAgent}
        disabled={isDisabledBtn}
        className={`w-full px-3 py-2 rounded-lg transition-all border font-semibold text-sm flex items-center gap-2 ${
          isProcessing
            ? "bg-blue-500/20 border-blue-500/30 text-blue-400"
            : disabled
            ? "bg-gray-500/20 border-gray-500/30 text-gray-400 cursor-not-allowed"
            : "bg-gradient-to-r from-emerald-500/20 to-teal-500/20 hover:from-emerald-500/30 hover:to-teal-500/30 border-emerald-500/30 hover:border-emerald-500/50 text-foreground hover:shadow-lg"
        }`}
      >
        <span className="text-lg">📊</span>
        <span className="flex-1">Finance Agent</span>
        {isProcessing && (
          <span className="text-xs font-semibold text-blue-400">
            {processedCount}/10
          </span>
        )}
        {!isProcessing && !disabled && !isReady && (
          <span className="text-xs bg-teal-500/30 px-2 py-0.5 rounded text-teal-300">
            Click to analyze
          </span>
        )}
        {isReady && (
          <span className="text-xs bg-emerald-500/30 px-2 py-0.5 rounded text-emerald-300">
            Ready
          </span>
        )}
      </button>
      {isProcessing && (
        <p className="text-xs text-blue-400 text-center py-1">
          Processing financial analysis... {processedCount}/10
        </p>
      )}
      {disabled && (
        <p className="text-xs text-muted-foreground text-center py-1">
          Upload PDF to analyze
        </p>
      )}
    </div>
  );
}
