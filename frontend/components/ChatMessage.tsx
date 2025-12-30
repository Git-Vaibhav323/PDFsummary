"use client";

import { User, Bot } from "lucide-react";
import { formatTimestamp } from "@/lib/utils";

interface ChatMessageProps {
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
  } | null;
  timestamp?: Date;
}

export default function ChatMessage({
  role,
  content,
  visualization,
  timestamp,
}: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className={`flex gap-4 animate-fade-in ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full shadow-sm transition-all ${
          isUser
            ? "bg-primary text-primary-foreground ring-2 ring-primary/20"
            : "bg-gradient-to-br from-muted to-muted/80 text-foreground ring-2 ring-border/50"
        }`}
      >
        {isUser ? (
          <User className="h-4.5 w-4.5" />
        ) : (
          <Bot className="h-4.5 w-4.5" />
        )}
      </div>

      {/* Message Content */}
      <div
        className={`flex flex-1 flex-col gap-2.5 ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`max-w-[80%] rounded-xl px-4 py-3 shadow-sm transition-all ${
            isUser
              ? "bg-primary text-primary-foreground shadow-primary/20"
              : "bg-card border border-border/50 text-foreground shadow-md"
          }`}
        >
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed [text-wrap:pretty]">
            {content}
          </p>
        </div>

        {/* Visualization */}
        {visualization && !isUser && (
          <div className="max-w-[80%] rounded-xl border border-border/50 bg-card/80 p-4 shadow-md backdrop-blur-sm">
            {typeof visualization === 'string' ? (
              // Legacy format: base64 image string
              <img
                src={`data:image/png;base64,${visualization}`}
                alt="Chart visualization"
                className="max-w-full rounded-lg"
              />
            ) : visualization.headers && visualization.rows ? (
              // Table format: structured data (PRIORITY - check this first)
              <div className="w-full my-4">
                {visualization.title && (
                  <h3 className="text-lg font-semibold mb-4 text-foreground">{visualization.title}</h3>
                )}
                <div className="border border-border/60 rounded-lg overflow-hidden shadow-lg bg-card">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-border">
                      <thead className="bg-muted/80">
                        <tr>
                          {visualization.headers.map((header, idx) => {
                            // Detect if column is numeric (check first few rows)
                            const isNumeric = visualization.rows && visualization.rows.length > 0 && 
                              visualization.rows.some(row => {
                                const cell = row[idx];
                                if (!cell || cell === "-" || cell === "") return false;
                                const cellStr = String(cell).replace(/[(),₹$Rs.\s]/g, '');
                                return !isNaN(parseFloat(cellStr)) && isFinite(parseFloat(cellStr));
                              });
                            
                            return (
                              <th 
                                key={idx} 
                                className={`px-6 py-4 text-xs font-bold text-foreground uppercase tracking-wider border-r border-border/50 last:border-r-0 ${
                                  isNumeric ? 'text-right' : 'text-left'
                                }`}
                              >
                                {header.replace(/\*\*/g, '')}
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      <tbody className="bg-card divide-y divide-border/50">
                        {visualization.rows.map((row, rowIdx) => (
                          <tr 
                            key={rowIdx} 
                            className={`transition-colors hover:bg-muted/40 ${
                              rowIdx % 2 === 0 ? "bg-card" : "bg-muted/10"
                            }`}
                          >
                            {row.map((cell, cellIdx) => {
                              // Detect if cell is numeric
                              const cellStr = String(cell).replace(/\*\*/g, '');
                              const isNumeric = cellStr && cellStr !== "-" && cellStr !== "" && 
                                !isNaN(parseFloat(cellStr.replace(/[(),₹$Rs.\s]/g, ''))) && 
                                isFinite(parseFloat(cellStr.replace(/[(),₹$Rs.\s]/g, '')));
                              
                              return (
                                <td 
                                  key={cellIdx} 
                                  className={`px-6 py-4 whitespace-nowrap text-sm text-foreground/90 border-r border-border/30 last:border-r-0 ${
                                    isNumeric ? 'text-right font-mono' : 'text-left'
                                  }`}
                                >
                                  <div className={isNumeric ? '' : 'break-words'}>
                                    {cellStr}
                                  </div>
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : visualization.markdown ? (
              // Table format: markdown table
              <div className="overflow-x-auto w-full">
                <div className="prose prose-sm max-w-none dark:prose-invert bg-muted/30 p-4 rounded-lg">
                  <pre className="whitespace-pre-wrap text-sm overflow-x-auto m-0">
                    {visualization.markdown}
                  </pre>
                </div>
              </div>
            ) : visualization.image_base64 ? (
              // Chart format: base64 image
              <div>
                {visualization.title && (
                  <h3 className="text-lg font-semibold mb-3">{visualization.title}</h3>
                )}
                <img
                  src={`data:image/png;base64,${visualization.image_base64}`}
                  alt={visualization.title || "Chart visualization"}
                  className="max-w-full rounded-lg"
                />
              </div>
            ) : null}
          </div>
        )}

        {/* Timestamp */}
        {timestamp && (
          <span className="text-xs text-muted-foreground/70 px-1">
            {formatTimestamp(timestamp)}
          </span>
        )}
      </div>
    </div>
  );
}

