"use client";

import { useState, useRef, useImperativeHandle, forwardRef, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import dynamic from "next/dynamic";

// Dynamically import SimpleChart to avoid SSR issues
const SimpleChart = dynamic(() => import("./SimpleChart"), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-muted/30 h-64 rounded-lg" />,
});

interface FAQItem {
  id: number;
  title: string;
  question: string;
  answer?: string;
  isLoading?: boolean;
}

interface FAQAnswerData {
  answer: string;
  visualization?: string | {
    image_base64?: string;
    markdown?: string;
    chart_type?: string;
    type?: string;
    title?: string;
    labels?: string[];
    values?: number[];
    xAxis?: string;
    yAxis?: string;
    headers?: string[];
    rows?: string[][];
    error?: string;
  } | null;
}

interface FAQAccordionProps {
  onQuestionClick: (question: string) => void;
  onAllAnswered?: (completed: boolean) => void;
  onClose?: () => void;
  initialAnswers?: { [key: number]: FAQAnswerData }; // For restoring answers when reopened
}

const FAQ_QUESTIONS = [
  { id: 1, title: "Company Overview", question: "Summarize the overall financial performance of the company in 1-2 sentences." },
  { id: 2, title: "Revenue Growth", question: "What was the revenue change compared to the previous period? (brief)" },
  { id: 3, title: "Profitability", question: "List key profitability metrics (net profit, operating margin, EBITDA) in one line each." },
  { id: 4, title: "Cost & Expense Structure", question: "What are the top 3 cost components impacting financial performance?" },
  { id: 5, title: "Cash Flow Position", question: "Briefly summarize cash flow from operations, investing, and financing." },
  { id: 6, title: "Debt & Liabilities", question: "What is the current debt position? (summary)" },
  { id: 7, title: "Key Financial Risks", question: "What are the 2-3 main financial risks highlighted?" },
  { id: 8, title: "Segment / Business Unit Performance", question: "Which business segment or region performed best? (brief)" },
  { id: 9, title: "Forward-Looking Guidance", question: "Is there forward-looking guidance provided? (yes/no + brief outlook)" },
  { id: 10, title: "Key Takeaways for Investors", question: "What is the key financial takeaway for investors in 1 sentence?" },
];

const FAQAccordion = forwardRef<any, FAQAccordionProps>(
  ({ onQuestionClick, onAllAnswered, onClose, initialAnswers = {} }, ref) => {
    const [expandedId, setExpandedId] = useState<number | null>(null);
    const [answers, setAnswers] = useState<{ [key: number]: FAQAnswerData }>(initialAnswers);
    
    // Update answers when initialAnswers prop changes (when reopening Finance Agent)
    useEffect(() => {
      if (Object.keys(initialAnswers).length > 0) {
        setAnswers(initialAnswers);
      }
    }, [initialAnswers]);

    // Check if all questions are answered
    const allAnswered = FAQ_QUESTIONS.every((faq) => answers[faq.id]?.answer);

    useEffect(() => {
      onAllAnswered?.(allAnswered);
    }, [allAnswered, onAllAnswered]);

    useImperativeHandle(ref, () => ({
      setAnswer: (id: number, answer: string, visualization?: FAQAnswerData['visualization']) => {
        setAnswers((prev) => ({ ...prev, [id]: { answer, visualization } }));
      },
    }));

    const handleQuestionClick = (question: string, id: number) => {
      setExpandedId(id);
      // Only send to backend if we don't have answer yet
      if (!answers[id]?.answer) {
        onQuestionClick(question);
      }
    };

    return (
      <div className="w-full space-y-2 px-4 py-6 overflow-y-auto scrollbar-thin flex flex-col h-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground">📊 Financial Questions</h2>
          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-1 text-xs bg-card/50 hover:bg-card/70 border border-border/30 rounded transition-colors"
            >
              ✕ Close
            </button>
          )}
        </div>
        
        <div className="space-y-2 flex-1 overflow-y-auto">
          {FAQ_QUESTIONS.map((faq) => (
            <div key={faq.id} className="border border-border/30 rounded-lg overflow-hidden bg-card/50">
              <button
                onClick={() => handleQuestionClick(faq.question, faq.id)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-card/70 transition-colors"
              >
                <div className="flex-1 text-left">
                  <div className="font-semibold text-sm text-foreground">
                    {faq.id}. {faq.title}
                  </div>
                  {!answers[faq.id]?.answer && (
                    <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                      {faq.question}
                    </div>
                  )}
                </div>
                <div className="ml-2 flex items-center gap-2">
                  {expandedId === faq.id ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
              </button>

              {expandedId === faq.id && answers[faq.id]?.answer && (
                <div className="px-4 py-3 bg-card/30 border-t border-border/20">
                  <div className="text-xs text-muted-foreground mb-3 font-semibold">Question:</div>
                  <div className="text-sm text-foreground mb-4 leading-relaxed italic">
                    {faq.question}
                  </div>
                  <div className="text-xs text-muted-foreground mb-2 font-semibold">Answer:</div>
                  <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap mb-4">
                    {answers[faq.id].answer}
                  </div>
                  
                  {/* Display visualization if available */}
                  {answers[faq.id].visualization && !(answers[faq.id].visualization as any)?.error && (
                    <div className="mt-4 rounded-xl border border-border/50 bg-card/80 p-4 shadow-md backdrop-blur-sm">
                      {typeof answers[faq.id].visualization === 'string' ? (
                        // Legacy format: base64 image string
                        <img
                          src={`data:image/png;base64,${answers[faq.id].visualization}`}
                          alt="Chart visualization"
                          className="max-w-full rounded-lg"
                        />
                      ) : (answers[faq.id].visualization as any).labels && (answers[faq.id].visualization as any).values && ((answers[faq.id].visualization as any).chart_type || (answers[faq.id].visualization as any).type) ? (
                        // Chart format: bar, line, pie, or stacked_bar chart
                        <SimpleChart
                          type={((answers[faq.id].visualization as any).chart_type || (answers[faq.id].visualization as any).type) as "bar" | "line" | "pie" | "stacked_bar"}
                          title={(answers[faq.id].visualization as any).title}
                          labels={(answers[faq.id].visualization as any).labels}
                          values={(answers[faq.id].visualization as any).values}
                          groups={(answers[faq.id].visualization as any).groups}
                          xAxis={(answers[faq.id].visualization as any).xAxis}
                          yAxis={(answers[faq.id].visualization as any).yAxis}
                        />
                      ) : ((answers[faq.id].visualization as any).headers && Array.isArray((answers[faq.id].visualization as any).headers) && (answers[faq.id].visualization as any).rows && Array.isArray((answers[faq.id].visualization as any).rows) && (answers[faq.id].visualization as any).headers.length > 0 && (answers[faq.id].visualization as any).rows.length > 0) ? (
                        // Table format: structured data
                        <div className="w-full my-6">
                          {(answers[faq.id].visualization as any).title && (
                            <h3 className="text-xl font-bold mb-4 text-foreground">{(answers[faq.id].visualization as any).title}</h3>
                          )}
                          <div className="rounded-lg overflow-hidden shadow-xl bg-card border border-border/50">
                            <div className="overflow-x-auto">
                              <table className="w-full border-collapse">
                                <thead>
                                  <tr className="bg-muted/50">
                                    {(answers[faq.id].visualization as any).headers.map((header: string, idx: number) => (
                                      <th
                                        key={idx}
                                        className={`px-4 py-3 text-left text-sm font-semibold text-foreground border-b border-border/50 ${
                                          idx > 0 ? 'text-right' : ''
                                        }`}
                                      >
                                        {header}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {(answers[faq.id].visualization as any).rows.map((row: any[], rowIdx: number) => (
                                    <tr
                                      key={rowIdx}
                                      className={`border-b border-border/30 ${
                                        rowIdx % 2 === 0 ? 'bg-card' : 'bg-muted/20'
                                      }`}
                                    >
                                      {row.slice(0, (answers[faq.id].visualization as any).headers.length).map((cell: any, cellIdx: number) => (
                                        <td
                                          key={cellIdx}
                                          className={`px-4 py-2 text-sm text-foreground ${
                                            cellIdx > 0 ? 'text-right' : ''
                                          }`}
                                        >
                                          {cell || '-'}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      ) : (answers[faq.id].visualization as any).markdown ? (
                        // Markdown table format
                        <div className="w-full my-4">
                          {(answers[faq.id].visualization as any).title && (
                            <h3 className="text-lg font-semibold mb-3 text-foreground">{(answers[faq.id].visualization as any).title}</h3>
                          )}
                          <div className="prose prose-sm dark:prose-invert max-w-none">
                            <pre className="whitespace-pre-wrap text-sm bg-muted/30 p-4 rounded-lg overflow-x-auto">
                              {(answers[faq.id].visualization as any).markdown}
                            </pre>
                          </div>
                        </div>
                      ) : (answers[faq.id].visualization as any).image_base64 ? (
                        // Base64 image format
                        <div>
                          {(answers[faq.id].visualization as any).title && (
                            <h3 className="text-lg font-semibold mb-3 text-foreground">{(answers[faq.id].visualization as any).title}</h3>
                          )}
                          <img
                            src={`data:image/png;base64,${(answers[faq.id].visualization as any).image_base64}`}
                            alt={(answers[faq.id].visualization as any).title || "Chart visualization"}
                            className="max-w-full rounded-lg"
                          />
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              )}

              {expandedId === faq.id && !answers[faq.id]?.answer && (
                <div className="px-4 py-3 bg-card/30 border-t border-border/20 text-xs text-muted-foreground italic">
                  Waiting for answer...
                </div>
              )}
            </div>
          ))}
        </div>

        <p className="text-xs text-muted-foreground mt-6 text-center italic">
          Click on any question to view the answer
        </p>
      </div>
    );
  }
);

FAQAccordion.displayName = "FAQAccordion";

export default FAQAccordion;
