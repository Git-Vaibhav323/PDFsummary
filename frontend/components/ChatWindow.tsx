"use client";

import ChatMessage from "./ChatMessage";
import LoadingIndicator from "./LoadingIndicator";
import EmptyState from "./EmptyState";

interface Message {
  role: "user" | "assistant";
  content: string;
  visualization?: string | {
    image_base64?: string;
    markdown?: string;
    chart_type?: string;
    title?: string;
    headers?: string[];
    rows?: string[][];
    error?: string;
  };
  timestamp: Date;
}

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  isPDFLoaded: boolean;
  onSuggestionClick?: (question: string) => void;
}

export default function ChatWindow({
  messages,
  isLoading,
  isPDFLoaded,
  onSuggestionClick,
}: ChatWindowProps) {
  // No auto-scroll - user controls scrolling manually

  if (messages.length === 0 && !isLoading) {
    return <EmptyState isPDFLoaded={isPDFLoaded} onSuggestionClick={onSuggestionClick} />;
  }

  return (
    <div className="flex flex-1 w-full flex-col bg-gradient-to-b from-background via-background to-muted/20 min-h-0 overflow-hidden">
      <div 
        className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin p-8 min-h-0"
        style={{ 
          WebkitOverflowScrolling: 'touch',
        }}
      >
        <div className="mx-auto max-w-4xl space-y-8">
          {messages.map((message, index) => (
            <ChatMessage key={index} {...message} />
          ))}
          {isLoading && <LoadingIndicator />}
        </div>
      </div>
    </div>
  );
}

