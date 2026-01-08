"use client";

import { useState, useEffect, useCallback } from "react";
import { FileText, X, CheckCircle2, Loader2, Trash2 } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { apiClient } from "@/lib/api";
import { formatFileSize } from "@/lib/utils";

interface Document {
  id: string;
  name: string;
  filename: string;
  upload_time: string;
  chunks_count: number;
  pages_count: number;
  status: string;
}

interface DocumentListProps {
  onDocumentSelect?: (documentId: string) => void;
  onDocumentDelete?: (documentId: string) => void;
  selectedDocumentIds?: string[];
  refreshTrigger?: number; // Trigger to refresh document list
}

export default function DocumentList({
  onDocumentSelect,
  onDocumentDelete,
  selectedDocumentIds = [],
  refreshTrigger,
}: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());

  const loadDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.listDocuments();
      setDocuments(response.documents || []);
    } catch (error: any) {
      console.error("Failed to load documents:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
    // Only refresh on mount - no periodic polling
  }, [loadDocuments]);
  
  // Refresh when refreshTrigger changes (e.g., after upload)
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      loadDocuments();
    }
  }, [refreshTrigger, loadDocuments]);

  const handleDelete = useCallback(
    async (documentId: string, e: React.MouseEvent) => {
      e.stopPropagation();
      
      if (!confirm("Are you sure you want to delete this document?")) {
        return;
      }

      setDeletingIds((prev) => new Set(prev).add(documentId));
      try {
        await apiClient.deleteDocument(documentId);
        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
        onDocumentDelete?.(documentId);
      } catch (error: any) {
        console.error("Failed to delete document:", error);
        alert("Failed to delete document: " + (error.message || "Unknown error"));
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev);
          next.delete(documentId);
          return next;
        });
      }
    },
    [onDocumentDelete]
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <Card className="border-[#E5E7EB] bg-white shadow-sm">
        <CardContent className="p-4">
          <p className="text-xs text-[#6B7280] text-center">
            No documents uploaded yet
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => {
        const isSelected = selectedDocumentIds.includes(doc.id);
        const isDeleting = deletingIds.has(doc.id);

        return (
          <Card
            key={doc.id}
            className={`cursor-pointer transition-all border-[#E5E7EB] bg-white shadow-sm hover:bg-[#F8FAFC] hover:border-[#2563EB] ${
              isSelected ? "ring-2 ring-[#2563EB]/50 border-[#2563EB]/30" : ""
            }`}
            onClick={() => onDocumentSelect?.(doc.id)}
          >
            <CardContent className="p-3">
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#DBEAFE]">
                  <FileText className="h-4 w-4 text-[#2563EB]" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium text-[#111827]">
                      {doc.name || doc.filename}
                    </p>
                    {isSelected && (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-[#2563EB]" />
                    )}
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-[#6B7280]">
                    <span>{doc.pages_count} pages</span>
                    <span>•</span>
                    <span>{doc.chunks_count} chunks</span>
                    <span>•</span>
                    <span>{formatDate(doc.upload_time)}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0 hover:bg-destructive/20 hover:text-destructive"
                  onClick={(e) => handleDelete(doc.id, e)}
                  disabled={isDeleting}
                  title="Delete document"
                >
                  {isDeleting ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

