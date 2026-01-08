"use client";

import { useState, KeyboardEvent } from "react";
import { Send, HelpCircle, Globe } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";

interface ChatInputProps {
  onSendMessage: (message: string, useWebSearch?: boolean) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSendMessage,
  disabled = false,
  placeholder = "Ask a question about your document...",
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [useWebSearch, setUseWebSearch] = useState<boolean | undefined>(undefined); // undefined = auto-detect

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim(), useWebSearch);
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
    <div className="sticky bottom-0 z-40 border-t border-[#E5E7EB] bg-white shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)]">
      <div className="container mx-auto max-w-4xl p-6">
        {/* Web Search Toggle */}
        <div className="mb-3 flex items-center justify-end gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 cursor-help">
                  <Globe className="h-4 w-4 text-[#6B7280]" />
                  <Label htmlFor="web-search-toggle" className="text-xs text-[#6B7280] cursor-pointer">
                    Web Search
                  </Label>
                  <div className="flex items-center gap-1.5">
                    <span className={`text-xs ${useWebSearch === false ? 'text-[#111827] font-medium' : 'text-[#6B7280]'}`}>Off</span>
                    <Switch
                      id="web-search-toggle"
                      checked={useWebSearch === true}
                      onCheckedChange={(checked) => {
                        // Three states: undefined (auto), false (off), true (on)
                        if (checked) {
                          setUseWebSearch(true);
                        } else {
                          // If currently true and unchecked, go to false
                          // If currently undefined and unchecked, stay undefined (auto)
                          setUseWebSearch(useWebSearch === true ? false : undefined);
                        }
                      }}
                      disabled={disabled}
                      className="scale-75 data-[state=checked]:bg-[#2563EB] data-[state=unchecked]:bg-[#E5E7EB]"
                    />
                    <span className={`text-xs ${useWebSearch === true ? 'text-[#111827] font-medium' : 'text-[#6B7280]'}`}>On</span>
                    {useWebSearch === undefined && (
                      <span className="text-xs text-[#6B7280]/60">(Auto)</span>
                    )}
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs bg-white border-[#E5E7EB] text-[#111827]">
                <p className="text-xs">
                  <strong>Auto:</strong> Web search when needed (low document confidence, time-sensitive queries)<br/>
                  <strong>On:</strong> Always include web search results<br/>
                  <strong>Off:</strong> Only use uploaded documents
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              className="rounded-xl border-[#E5E7EB] bg-white px-4 py-6 text-base shadow-sm focus-visible:ring-2 focus-visible:ring-[#2563EB]/20 focus-visible:border-[#2563EB]/50 disabled:opacity-50 disabled:cursor-not-allowed text-[#111827] placeholder:text-[#6B7280]"
            />
            {disabled && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 cursor-help">
                      <HelpCircle className="h-4 w-4 text-[#6B7280]" />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent className="bg-white border-[#E5E7EB] text-[#111827]">
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
            className="rounded-xl h-12 w-12 shadow-md hover:shadow-lg transition-all disabled:opacity-60 shrink-0 flex items-center justify-center bg-[#2563EB] hover:bg-[#1D4ED8] text-white"
            type="button"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
        <p className="mt-3 text-xs text-[#6B7280]/70 text-center">
          Press <kbd className="px-1.5 py-0.5 rounded bg-[#F3F4F6] text-xs font-mono text-[#111827]">Enter</kbd> to send,{" "}
          <kbd className="px-1.5 py-0.5 rounded bg-[#F3F4F6] text-xs font-mono text-[#111827]">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}

