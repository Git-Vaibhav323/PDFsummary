"use client";

import { useState } from "react";
import { Settings, Trash2, ChevronDown, ChevronUp, FileText, Activity, X, LayoutDashboard, MessageSquare, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import UploadCard from "./UploadCard";
import StatusBadge from "./StatusBadge";
import DocumentList from "./DocumentList";
import { formatFileSize } from "@/lib/utils";

type SidebarTab = "chat" | "dashboard";

interface SidebarProps {
  isPDFLoaded: boolean;
  isProcessing?: boolean;
  onUploadSuccess: (fileName?: string, fileSize?: number, documentId?: string) => void;
  onUploadError: (error: string) => void;
  onClearChat: () => void;
  onRemoveFile?: () => void;
  onOpenFinanceAgent?: () => void;
  messageCount: number;
  uploadedFileName?: string;
  uploadedFileSize?: number;
  children?: React.ReactNode;
  selectedDocumentIds?: string[];
  onDocumentSelect?: (documentId: string) => void;
  onDocumentDelete?: (documentId: string) => void;
  documentRefreshTrigger?: number;
  activeTab?: SidebarTab;
  onTabChange?: (tab: SidebarTab) => void;
  isDashboardGenerating?: boolean;
  isDashboardReady?: boolean;
  onCreateDashboard?: () => void;
}

export default function Sidebar({
  isPDFLoaded,
  isProcessing = false,
  onUploadSuccess,
  onUploadError,
  onClearChat,
  onRemoveFile,
  onOpenFinanceAgent,
  messageCount,
  uploadedFileName,
  uploadedFileSize,
  children,
  selectedDocumentIds = [],
  onDocumentSelect,
  onDocumentDelete,
  documentRefreshTrigger,
  activeTab = "chat",
  onTabChange,
  isDashboardGenerating = false,
  isDashboardReady = false,
  onCreateDashboard,
}: SidebarProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <aside className="flex h-[calc(100vh-4rem)] w-80 flex-col gap-6 border-r border-border bg-[#F3F4F6] shadow-md">
      {/* Tab Navigation */}
      <div className="flex border-b border-border bg-white">
        <button
          onClick={() => onTabChange?.("chat")}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "chat"
              ? "bg-white text-[#111827] border-b-2 border-[#2563EB]"
              : "text-[#6B7280] hover:text-[#111827] hover:bg-[#F8FAFC]"
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          Chat
        </button>
        <button
          onClick={() => onTabChange?.("dashboard")}
          disabled={!isPDFLoaded || selectedDocumentIds.length === 0}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "dashboard"
              ? "bg-white text-[#111827] border-b-2 border-[#2563EB]"
              : "text-[#6B7280] hover:text-[#111827] hover:bg-[#F8FAFC] disabled:opacity-50 disabled:cursor-not-allowed"
          }`}
        >
          <LayoutDashboard className="h-4 w-4" />
          Dashboard
          {isDashboardGenerating && (
            <span className="absolute top-1 right-1 h-2 w-2 bg-[#2563EB] rounded-full animate-pulse" title="Generating..." />
          )}
          {isDashboardReady && !isDashboardGenerating && (
            <span className="absolute top-1 right-1 h-2 w-2 bg-[#16A34A] rounded-full" title="Ready" />
          )}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-6 bg-[#F3F4F6]">
      {/* Document Upload Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-2">
          <FileText className="h-4 w-4 text-[#6B7280]" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">
            Upload Document
          </h2>
        </div>
        <UploadCard
          onUploadSuccess={onUploadSuccess}
          onUploadError={onUploadError}
        />
      </div>

      {/* Documents List Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-2">
          <FileText className="h-4 w-4 text-[#6B7280]" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">
            Documents ({selectedDocumentIds.length > 0 ? `${selectedDocumentIds.length} selected` : "All"})
          </h2>
        </div>
        <DocumentList
          selectedDocumentIds={selectedDocumentIds}
          onDocumentSelect={onDocumentSelect}
          onDocumentDelete={onDocumentDelete}
          refreshTrigger={documentRefreshTrigger}
        />
      </div>

      {/* Create Dashboard Section */}
      {isPDFLoaded && selectedDocumentIds.length > 0 && !isProcessing && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-2">
            <LayoutDashboard className="h-4 w-4 text-[#6B7280]" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">
              Dashboard
            </h2>
          </div>
          <Card className="border-[#E5E7EB] bg-white shadow-sm">
            <CardContent className="p-4">
              <div className="space-y-3">
                {!isDashboardReady && !isDashboardGenerating && (
                  <Button
                    onClick={onCreateDashboard}
                    className="w-full bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-semibold shadow-md"
                    size="lg"
                  >
                    <LayoutDashboard className="h-4 w-4 mr-2" />
                    Create Dashboard
                  </Button>
                )}
                {isDashboardGenerating && (
                  <div className="flex items-center gap-2 text-sm text-[#6B7280]">
                    <Loader2 className="h-4 w-4 animate-spin text-[#2563EB]" />
                    <span>Generating dashboard...</span>
                  </div>
                )}
                {isDashboardReady && !isDashboardGenerating && (
                  <div className="flex items-center gap-2 text-sm text-[#16A34A]">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Dashboard ready</span>
                  </div>
                )}
                {isPDFLoaded && (
                  <div className="pt-2 border-t border-[#E5E7EB]">
                    <p className="text-xs text-[#6B7280]">
                      {selectedDocumentIds.length} document{selectedDocumentIds.length !== 1 ? "s" : ""} selected
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Status Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-2">
          <Activity className="h-4 w-4 text-[#6B7280]" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">
            Status
          </h2>
        </div>
        <Card className="border-[#E5E7EB] bg-white shadow-sm">
          <CardContent className="p-4">
            <div className="space-y-3">
              <StatusBadge isPDFLoaded={isPDFLoaded} isProcessing={isProcessing} />
              {isPDFLoaded && (
                <div className="pt-2 border-t border-[#E5E7EB]">
                  <p className="text-xs text-[#6B7280]">
                    {messageCount} message{messageCount !== 1 ? "s" : ""} in conversation
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Content based on active tab */}
      {activeTab === "chat" ? (
        <>
          {/* Conversation History Section */}
          {children}
        </>
      ) : (
        <>
          {/* Dashboard will be rendered in main content area */}
          <div className="text-center py-8 text-muted-foreground">
            <LayoutDashboard className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">Dashboard content will appear in the main panel</p>
          </div>
        </>
      )}

      {/* Actions Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-2">
          <Settings className="h-4 w-4 text-[#6B7280]" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">
            Actions
          </h2>
        </div>
        <div className="space-y-2">
          <Button
            variant="outline"
            className="w-full justify-start border-[#E5E7EB] bg-white hover:bg-[#F8FAFC] hover:border-[#6B7280] text-[#111827]"
            onClick={onClearChat}
            disabled={messageCount === 0}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Clear Chat
          </Button>

          <Button
            variant="ghost"
            className="w-full justify-between hover:bg-[#F8FAFC] text-[#111827]"
            onClick={() => setIsSettingsOpen(!isSettingsOpen)}
          >
            <div className="flex items-center">
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </div>
            {isSettingsOpen ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>

          {isSettingsOpen && (
            <Card className="mt-2 border-[#E5E7EB] bg-white shadow-sm">
              <CardContent className="p-4">
                <div className="space-y-4 text-sm">
                  <div>
                    <p className="font-medium text-[#111827]">API Endpoint</p>
                    <p className="mt-1 text-xs text-[#6B7280] font-mono">
                      {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      </div>
    </aside>
  );
}


