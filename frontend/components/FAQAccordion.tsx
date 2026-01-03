"use client";

import { useState, useRef, useImperativeHandle, forwardRef, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

interface FAQItem {
  id: number;
  title: string;
  question: string;
  answer?: string;
  isLoading?: boolean;
}

interface FAQAccordionProps {
  onQuestionClick: (question: string) => void;
  onAllAnswered?: (completed: boolean) => void;
  onClose?: () => void;
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
  ({ onQuestionClick, onAllAnswered, onClose }, ref) => {
    const [expandedId, setExpandedId] = useState<number | null>(null);
    const [answers, setAnswers] = useState<{ [key: number]: string }>({});

    // Check if all questions are answered
    const allAnswered = FAQ_QUESTIONS.every((faq) => answers[faq.id]);

    useEffect(() => {
      onAllAnswered?.(allAnswered);
    }, [allAnswered, onAllAnswered]);

    useImperativeHandle(ref, () => ({
      setAnswer: (id: number, answer: string) => {
        setAnswers((prev) => ({ ...prev, [id]: answer }));
      },
    }));

    const handleQuestionClick = (question: string, id: number) => {
      setExpandedId(id);
      // Only send to backend if we don't have answer yet
      if (!answers[id]) {
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
                  {!answers[faq.id] && (
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

              {expandedId === faq.id && answers[faq.id] && (
                <div className="px-4 py-3 bg-card/30 border-t border-border/20">
                  <div className="text-xs text-muted-foreground mb-3 font-semibold">Question:</div>
                  <div className="text-sm text-foreground mb-4 leading-relaxed italic">
                    {faq.question}
                  </div>
                  <div className="text-xs text-muted-foreground mb-2 font-semibold">Answer:</div>
                  <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap max-h-[400px] overflow-y-auto scrollbar-thin">
                    {answers[faq.id]}
                  </div>
                </div>
              )}

              {expandedId === faq.id && !answers[faq.id] && (
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
