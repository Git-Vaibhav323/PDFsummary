"use client";

import { User, Bot } from "lucide-react";
import { formatTimestamp } from "@/lib/utils";
import dynamic from "next/dynamic";

// Dynamically import SimpleChart to avoid SSR issues
const SimpleChart = dynamic(() => import("./SimpleChart"), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-muted/30 h-64 rounded-lg" />,
});

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  visualization?: string | {
    image_base64?: string;
    markdown?: string;
    chart_type?: string;
    type?: string; // Support both chart_type and type
    title?: string;
    labels?: string[];
    values?: number[];
    xAxis?: string;
    yAxis?: string;
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
        {visualization && !isUser && !(visualization as any)?.error && (
          <div className="max-w-[80%] rounded-xl border border-border/50 bg-card/80 p-4 shadow-md backdrop-blur-sm">
            {typeof visualization === 'string' ? (
              // Legacy format: base64 image string
              <img
                src={`data:image/png;base64,${visualization}`}
                alt="Chart visualization"
                className="max-w-full rounded-lg"
              />
            ) : visualization.labels && visualization.values && (visualization.chart_type || visualization.type) ? (
              // Chart format: bar, line, pie, or stacked_bar chart using Recharts
              <SimpleChart
                type={(visualization.chart_type || visualization.type) as "bar" | "line" | "pie" | "stacked_bar"}
                title={visualization.title}
                labels={visualization.labels}
                values={visualization.values}
                groups={visualization.groups}
                xAxis={visualization.xAxis}
                yAxis={visualization.yAxis}
              />
            ) : (visualization.headers && Array.isArray(visualization.headers) && visualization.rows && Array.isArray(visualization.rows) && visualization.headers.length > 0 && visualization.rows.length > 0) ? (
              // Table format: structured data (PRIORITY - check this first)
              <div className="w-full my-6">
                {visualization.title && (
                  <h3 className="text-xl font-bold mb-4 text-foreground">{visualization.title}</h3>
                )}
                <div className="rounded-lg overflow-hidden shadow-xl bg-card border border-border/50">
                  <div className="overflow-x-auto">
                    <table className="min-w-full" style={{ borderCollapse: 'collapse' }}>
                      <thead>
                        <tr className="bg-muted/60 border-b border-border">
                          {visualization.headers.map((header: string, idx: number) => {
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
                                className={`px-6 py-3.5 text-sm font-semibold text-foreground border-r border-border/40 last:border-r-0 ${
                                  isNumeric ? 'text-right' : 'text-left'
                                }`}
                                style={{ backgroundColor: 'rgba(var(--muted), 0.6)' }}
                              >
                                {header.replace(/\*\*/g, '')}
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      <tbody>
                        {visualization.rows.map((row: any[], rowIdx: number) => {
                          // Fix row structure: handle misaligned data
                          let fixedRow = [...row];
                          
                          // CRITICAL FIX: Handle Trial Balance format where rows might be ["-", "Account", "Debit", "Credit"]
                          // Expected format: ["Account", "Debit", "Credit"]
                          
                          // Step 1: Remove leading "-" if present and not needed
                          if (fixedRow.length > 0 && fixedRow[0] === "-" && fixedRow.length > visualization.headers.length) {
                            fixedRow = fixedRow.slice(1);
                          }
                          
                          // Step 2: Detect if account name is in wrong position
                          // Pattern: ["-", "AccountName", "Amount1", "Amount2"] -> ["AccountName", "Amount1", "Amount2"]
                          if (fixedRow.length >= 3 && fixedRow[0] === "-") {
                            const secondCol = String(fixedRow[1] || "").trim();
                            const thirdCol = String(fixedRow[2] || "").trim();
                            
                            // Check if second column is account name (contains letters, not just numbers/symbols)
                            const isAccountName = secondCol && 
                              secondCol !== "-" && 
                              /[a-zA-Z]/.test(secondCol) &&
                              !secondCol.match(/^[\d,.\-()$₹\s]+$/);
                            
                            // Check if third column is a number (could be debit)
                            const isNumber = thirdCol && 
                              thirdCol !== "-" && 
                              !isNaN(parseFloat(thirdCol.replace(/[(),₹$Rs.\s]/g, '')));
                            
                            if (isAccountName) {
                              // Restructure: ["-", "Bank", "1,100", ...] -> ["Bank", "1,100", ...]
                              fixedRow = [secondCol, ...fixedRow.slice(2)];
                            }
                          }
                          
                          // Step 3: Handle case where row has extra leading column
                          // If headers are ["Account", "Debit ($)", "Credit ($)"] but row is ["-", "Bank", "1,100"]
                          if (fixedRow.length === visualization.headers.length + 1 && fixedRow[0] === "-") {
                            fixedRow = fixedRow.slice(1);
                          }
                          
                          // Step 4: Ensure row length matches headers exactly
                          // Pad with empty strings if too short, truncate if too long
                          while (fixedRow.length < visualization.headers.length) {
                            fixedRow.push("");
                          }
                          fixedRow = fixedRow.slice(0, visualization.headers.length);
                          
                          // Step 5: Clean up the row - ensure proper format
                          // For Trial Balance: [Account, Debit, Credit]
                          fixedRow = fixedRow.map((cell, idx) => {
                            const cellStr = String(cell || "").trim();
                            // If it's an empty string or just whitespace, return empty string
                            if (!cellStr || cellStr === "" || cellStr.match(/^\s*$/)) {
                              return "";
                            }
                            // Remove markdown formatting
                            return cellStr.replace(/\*\*/g, '');
                          });
                          
                          // Check if this is a totals row (contains "Total" or "Totals")
                          const isTotalRow = fixedRow.some(cell => 
                            String(cell || "").toLowerCase().includes("total")
                          );
                          
                          return (
                            <tr 
                              key={`row-${rowIdx}`} 
                              className={`border-b border-border/30 last:border-b-0 transition-colors hover:bg-muted/20 ${
                                isTotalRow ? 'bg-muted/40 font-semibold' : rowIdx % 2 === 0 ? "bg-card" : "bg-muted/5"
                              }`}
                            >
                              {fixedRow.map((cell: any, cellIdx: number) => {
                                // Detect if cell is numeric
                                const cellStr = String(cell || "").replace(/\*\*/g, '').trim();
                                const isEmpty = !cellStr || cellStr === "-" || cellStr === "";
                                const isNumeric = !isEmpty && 
                                  !isNaN(parseFloat(cellStr.replace(/[(),₹$Rs.\s]/g, ''))) && 
                                  isFinite(parseFloat(cellStr.replace(/[(),₹$Rs.\s]/g, '')));
                                
                                return (
                                  <td 
                                    key={`cell-${rowIdx}-${cellIdx}`} 
                                    className={`px-6 py-3.5 text-sm text-foreground border-r border-border/20 last:border-r-0 ${
                                      isNumeric ? 'text-right font-mono tabular-nums' : 'text-left'
                                    } ${isTotalRow ? 'font-semibold' : ''}`}
                                  >
                                    {isEmpty ? (
                                      <span className="text-muted-foreground/50">—</span>
                                    ) : (
                                      <span className={isTotalRow ? 'text-foreground' : 'text-foreground/90'}>
                                        {cellStr}
                                      </span>
                                    )}
                                  </td>
                                );
                              })}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : visualization.markdown ? (
              // Table format: parse markdown table and render as HTML table
              <div className="w-full my-4">
                {(() => {
                  // Parse markdown table into headers and rows
                  const lines = visualization.markdown.split('\n').filter((line: string) => line.trim());
                  const tableLines = lines.filter((line: string) => line.includes('|'));
                  
                  if (tableLines.length < 2) {
                    // Not a valid table, show as pre
                    return (
                      <div className="prose prose-sm max-w-none dark:prose-invert bg-muted/30 p-4 rounded-lg">
                        <pre className="whitespace-pre-wrap text-sm overflow-x-auto m-0">
                          {visualization.markdown}
                        </pre>
                      </div>
                    );
                  }
                  
                  // Parse headers from first line
                  const headerLine = tableLines[0];
                  const headers = headerLine.split('|')
                    .map((h: string) => h.trim())
                    .filter((h: string) => h && !h.match(/^[\s\-:]+$/));
                  
                  // Skip separator line (contains ---)
                  const dataLines = tableLines.filter((line: string, idx: number) => {
                    if (idx === 0) return false; // Skip header
                    return !line.match(/^\|[\s\-:]+\|/); // Skip separator
                  });
                  
                  // Parse rows - markdown tables have format: | col1 | col2 | col3 |
                  // When split by '|', we get: ["", " col1 ", " col2 ", " col3 ", ""]
                  // So we need to take indices 1 to length-2
                  const rows = dataLines.map((line: string) => {
                    const parts = line.split('|').map((c: string) => c.trim());
                    // Remove first and last empty strings, keep middle parts
                    const cells = parts.slice(1, parts.length - 1);
                    // Ensure we have the right number of cells
                    while (cells.length < headers.length) {
                      cells.push("");
                    }
                    return cells.slice(0, headers.length);
                  }).filter((row: string[]) => {
                    // Filter out separator rows and empty rows
                    const hasContent = row.some((c: string) => c && c.trim() !== '-' && c.trim() !== '');
                    const isSeparator = row.every((c: string) => !c || c.match(/^[\s\-:]+$/));
                    return hasContent && !isSeparator;
                  });
                  
                  if (headers.length === 0 || rows.length === 0) {
                    return (
                      <div className="prose prose-sm max-w-none dark:prose-invert bg-muted/30 p-4 rounded-lg">
                        <pre className="whitespace-pre-wrap text-sm overflow-x-auto m-0">
                          {visualization.markdown}
                        </pre>
                      </div>
                    );
                  }
                  
                  // Extract title if present in markdown (before table)
                  const titleMatch = visualization.markdown.match(/\*\*(.+?)\*\*/);
                  const tableTitle = titleMatch ? titleMatch[1] : visualization.title;
                  
                  return (
                    <div className="w-full my-6">
                      {tableTitle && (
                        <h3 className="text-xl font-bold mb-4 text-foreground">{tableTitle}</h3>
                      )}
                      <div className="rounded-lg overflow-hidden shadow-xl bg-card border border-border/50">
                        <div className="overflow-x-auto">
                          <table className="min-w-full" style={{ borderCollapse: 'collapse' }}>
                            <thead>
                              <tr className="bg-muted/60 border-b border-border">
                                {headers.map((header: string, idx: number) => {
                                  // Detect if column is numeric
                                  const isNumeric = rows.some(row => {
                                    const cell = row[idx];
                                    if (!cell || cell === "-" || cell === "") return false;
                                    const cellStr = String(cell).replace(/[(),₹$Rs.\s]/g, '');
                                    return !isNaN(parseFloat(cellStr)) && isFinite(parseFloat(cellStr));
                                  });
                                  
                                  return (
                                    <th 
                                      key={idx}
                                      className={`px-6 py-3.5 text-sm font-semibold text-foreground border-r border-border/40 last:border-r-0 ${
                                        isNumeric ? 'text-right' : 'text-left'
                                      }`}
                                      style={{ backgroundColor: 'rgba(var(--muted), 0.6)' }}
                                    >
                                      {header.replace(/\*\*/g, '')}
                                    </th>
                                  );
                                })}
                              </tr>
                            </thead>
                            <tbody>
                              {rows.map((row: string[], rowIdx: number) => {
                                // Check if this is a totals row
                                const isTotalRow = row.some(cell => 
                                  String(cell || "").toLowerCase().includes("total")
                                );
                                
                                return (
                                  <tr 
                                    key={rowIdx}
                                    className={`border-b border-border/30 last:border-b-0 transition-colors hover:bg-muted/20 ${
                                      isTotalRow ? 'bg-muted/40 font-semibold' : rowIdx % 2 === 0 ? "bg-card" : "bg-muted/5"
                                    }`}
                                  >
                                    {row.slice(0, headers.length).map((cell: string, cellIdx: number) => {
                                      const cellStr = String(cell || '').replace(/\*\*/g, '').trim();
                                      const isEmpty = !cellStr || cellStr === "-" || cellStr === "";
                                      const isNumeric = !isEmpty && 
                                        !isNaN(parseFloat(cellStr.replace(/[(),₹$Rs.\s,]/g, ''))) && 
                                        isFinite(parseFloat(cellStr.replace(/[(),₹$Rs.\s,]/g, '')));
                                      
                                      return (
                                        <td 
                                          key={cellIdx}
                                          className={`px-6 py-3.5 text-sm text-foreground border-r border-border/20 last:border-r-0 ${
                                            isNumeric ? 'text-right font-mono tabular-nums' : 'text-left'
                                          } ${isTotalRow ? 'font-semibold' : ''}`}
                                        >
                                          {isEmpty ? (
                                            <span className="text-muted-foreground/50">—</span>
                                          ) : (
                                            <span className={isTotalRow ? 'text-foreground' : 'text-foreground/90'}>
                                              {cellStr}
                                            </span>
                                          )}
                                        </td>
                                      );
                                    })}
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  );
                })()}
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


