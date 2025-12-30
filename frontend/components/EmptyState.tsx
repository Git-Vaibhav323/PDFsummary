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
        <Card className="max-w-md border-border/50 bg-card/50 p-8 shadow-lg">
          <div className="mb-6 flex justify-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-muted to-muted/50 ring-2 ring-border/50">
              <FileQuestion className="h-10 w-10 text-muted-foreground" />
            </div>
          </div>
          <h3 className="mb-3 text-xl font-semibold tracking-tight">No PDF Uploaded</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Upload a PDF document from the sidebar to start asking questions and
            getting AI-powered answers.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto overflow-x-hidden p-12 text-center min-h-0 scrollbar-thin">
      <Card className="max-w-2xl w-full border-border/50 bg-card/50 p-10 shadow-lg">
        <div className="mb-6 flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-primary/10 ring-2 ring-primary/20">
            <MessageSquare className="h-10 w-10 text-primary" />
          </div>
        </div>
        <h3 className="mb-3 text-xl font-semibold tracking-tight">Start a Conversation</h3>
        <p className="mb-8 text-sm leading-relaxed text-muted-foreground">
          Ask questions about your PDF document. The AI will analyze the content
          and provide detailed answers with visualizations when applicable.
        </p>
        <div className="flex flex-col gap-3">
          <Button
            variant="outline"
            className="group justify-start border-border/50 bg-card/50 text-left hover:bg-card hover:border-border hover:shadow-md transition-all"
            onClick={() => onSuggestionClick?.("Summarize this document")}
          >
            <Sparkles className="mr-3 h-4 w-4 text-primary group-hover:scale-110 transition-transform" />
            <div className="flex-1">
              <p className="font-medium">Summarize this document</p>
              <p className="text-xs text-muted-foreground">Get a comprehensive overview</p>
            </div>
          </Button>
          <Button
            variant="outline"
            className="group justify-start border-border/50 bg-card/50 text-left hover:bg-card hover:border-border hover:shadow-md transition-all"
            onClick={() => onSuggestionClick?.("Extract key skills and qualifications")}
          >
            <Sparkles className="mr-3 h-4 w-4 text-primary group-hover:scale-110 transition-transform" />
            <div className="flex-1">
              <p className="font-medium">Extract key skills</p>
              <p className="text-xs text-muted-foreground">Identify important qualifications</p>
            </div>
          </Button>
          <Button
            variant="outline"
            className="group justify-start border-border/50 bg-card/50 text-left hover:bg-card hover:border-border hover:shadow-md transition-all"
            onClick={() => onSuggestionClick?.("Give a section-wise overview")}
          >
            <Sparkles className="mr-3 h-4 w-4 text-primary group-hover:scale-110 transition-transform" />
            <div className="flex-1">
              <p className="font-medium">Section-wise overview</p>
              <p className="text-xs text-muted-foreground">Break down by document sections</p>
            </div>
          </Button>
        </div>
      </Card>
    </div>
  );
}

