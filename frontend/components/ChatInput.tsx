"use client";

import { useState, KeyboardEvent } from "react";
import { Send, HelpCircle } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSendMessage,
  disabled = false,
  placeholder = "Ask a question about your document...",
}: ChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="sticky bottom-0 z-40 border-t border-border/50 bg-background/95 backdrop-blur-xl supports-[backdrop-filter]:bg-background/80 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)]">
      <div className="container mx-auto max-w-4xl p-6">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              className="rounded-xl border-border/50 bg-card/50 px-4 py-6 text-base shadow-sm focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary/50 disabled:opacity-50 disabled:cursor-not-allowed"
            />
            {disabled && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 cursor-help">
                      <HelpCircle className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Please upload and process a PDF first</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
          <Button
            onClick={handleSend}
            disabled={disabled || !message.trim()}
            size="icon"
            className="rounded-xl h-12 w-12 shadow-md hover:shadow-lg transition-all disabled:opacity-60 shrink-0 flex items-center justify-center"
            type="button"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
        <p className="mt-3 text-xs text-muted-foreground/70 text-center">
          Press <kbd className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">Enter</kbd> to send,{" "}
          <kbd className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}

