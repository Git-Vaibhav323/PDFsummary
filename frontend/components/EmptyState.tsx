"use client";

import { MessageSquare, FileQuestion, Sparkles } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";

interface EmptyStateProps {
  isPDFLoaded: boolean;
  onSuggestionClick?: (question: string) => void;
}

export default function EmptyState({
  isPDFLoaded,
  onSuggestionClick,
}: EmptyStateProps) {
  if (!isPDFLoaded) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto overflow-x-hidden p-12 text-center min-h-0">
        <Card className="max-w-md border-[#E5E7EB] bg-white p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
          <div className="mb-6 flex justify-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-[#F3F4F6] ring-2 ring-[#E5E7EB]">
              <FileQuestion className="h-10 w-10 text-[#6B7280]" />
            </div>
          </div>
          <h3 className="mb-3 text-xl font-semibold tracking-tight text-[#111827]">No PDF Uploaded</h3>
          <p className="text-sm leading-relaxed text-[#6B7280]">
            Upload a PDF document from the sidebar to start asking questions and
            getting AI-powered answers.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto overflow-x-hidden p-12 text-center min-h-0 scrollbar-thin">
      <Card className="max-w-2xl w-full border-[#E5E7EB] bg-white p-10 shadow-[0_1px_3px_rgba(0,0,0,0.08)] rounded-xl">
        <div className="mb-6 flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-[#DBEAFE] ring-2 ring-[#2563EB]/20">
            <MessageSquare className="h-10 w-10 text-[#2563EB]" />
          </div>
        </div>
        <h3 className="mb-3 text-xl font-semibold tracking-tight text-[#111827]">Start a Conversation</h3>
        <p className="mb-8 text-sm leading-relaxed text-[#6B7280]">
          Ask questions about your PDF document. The AI will analyze the content
          and provide detailed answers with visualizations when applicable.
        </p>
        <div className="flex flex-col gap-3">
          <Button
            variant="outline"
            className="group justify-start border-[#E5E7EB] bg-white text-left hover:bg-[#F8FAFC] hover:border-[#2563EB] hover:shadow-md transition-all text-[#111827]"
            onClick={() => onSuggestionClick?.("Summarize this document")}
          >
            <Sparkles className="mr-3 h-4 w-4 text-[#2563EB] group-hover:scale-110 transition-transform" />
            <div className="flex-1">
              <p className="font-medium">Summarize this document</p>
              <p className="text-xs text-[#6B7280]">Get a comprehensive overview</p>
            </div>
          </Button>
          <Button
            variant="outline"
            className="group justify-start border-[#E5E7EB] bg-white text-left hover:bg-[#F8FAFC] hover:border-[#2563EB] hover:shadow-md transition-all text-[#111827]"
            onClick={() => onSuggestionClick?.("Extract key skills and qualifications")}
          >
            <Sparkles className="mr-3 h-4 w-4 text-[#2563EB] group-hover:scale-110 transition-transform" />
            <div className="flex-1">
              <p className="font-medium">Extract key skills</p>
              <p className="text-xs text-[#6B7280]">Identify important qualifications</p>
            </div>
          </Button>
          <Button
            variant="outline"
            className="group justify-start border-[#E5E7EB] bg-white text-left hover:bg-[#F8FAFC] hover:border-[#2563EB] hover:shadow-md transition-all text-[#111827]"
            onClick={() => onSuggestionClick?.("Give a section-wise overview")}
          >
            <Sparkles className="mr-3 h-4 w-4 text-[#2563EB] group-hover:scale-110 transition-transform" />
            <div className="flex-1">
              <p className="font-medium">Section-wise overview</p>
              <p className="text-xs text-[#6B7280]">Break down by document sections</p>
            </div>
          </Button>
        </div>
      </Card>
    </div>
  );
}

