"use client";

import { useState } from "react";
import { Settings, Trash2, ChevronDown, ChevronUp, FileText, Activity, X } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import UploadCard from "./UploadCard";
import StatusBadge from "./StatusBadge";
import { formatFileSize } from "@/lib/utils";

interface SidebarProps {
  isPDFLoaded: boolean;
  isProcessing?: boolean;
  onUploadSuccess: (fileName?: string, fileSize?: number) => void;
  onUploadError: (error: string) => void;
  onClearChat: () => void;
  onRemoveFile?: () => void;
  messageCount: number;
  uploadedFileName?: string;
  uploadedFileSize?: number;
  children?: React.ReactNode;
}

export default function Sidebar({
  isPDFLoaded,
  isProcessing = false,
  onUploadSuccess,
  onUploadError,
  onClearChat,
  onRemoveFile,
  messageCount,
  uploadedFileName,
  uploadedFileSize,
  children,
}: SidebarProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <aside className="flex h-[calc(100vh-4rem)] w-80 flex-col gap-6 border-r border-border/50 bg-gradient-to-b from-card/50 to-card/30 p-6 shadow-lg backdrop-blur-sm overflow-y-auto scrollbar-thin">
      {/* Document Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Document
          </h2>
        </div>
        <UploadCard
          onUploadSuccess={onUploadSuccess}
          onUploadError={onUploadError}
        />
        
        {/* File Metadata */}
        {uploadedFileName && (
          <Card className="border-border/50 bg-card/50 shadow-sm">
            <CardContent className="p-4">
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">
                      {uploadedFileName}
                    </p>
                    {uploadedFileSize && (
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(uploadedFileSize)}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-green-500/20">
                      <div className="h-2 w-2 rounded-full bg-green-500" />
                    </div>
                    {onRemoveFile && (
                      <button
                        onClick={onRemoveFile}
                        className="flex h-6 w-6 items-center justify-center rounded-md hover:bg-destructive/20 text-muted-foreground hover:text-destructive transition-colors"
                        title="Remove file"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Status Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-2">
          <Activity className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Status
          </h2>
        </div>
        <Card className="border-border/50 bg-card/50 shadow-sm">
          <CardContent className="p-4">
            <div className="space-y-3">
              <StatusBadge isPDFLoaded={isPDFLoaded} isProcessing={isProcessing} />
              {isPDFLoaded && (
                <div className="pt-2 border-t border-border/50">
                  <p className="text-xs text-muted-foreground">
                    {messageCount} message{messageCount !== 1 ? "s" : ""} in conversation
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Conversation History Section */}
      {children}

      {/* Actions Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-2">
          <Settings className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Actions
          </h2>
        </div>
        <div className="space-y-2">
          <Button
            variant="outline"
            className="w-full justify-start border-border/50 bg-card/50 hover:bg-card hover:border-border"
            onClick={onClearChat}
            disabled={messageCount === 0}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Clear Chat
          </Button>

          <Button
            variant="ghost"
            className="w-full justify-between hover:bg-card/50"
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
            <Card className="mt-2 border-border/50 bg-card/30 shadow-sm">
              <CardContent className="p-4">
                <div className="space-y-4 text-sm">
                  <div>
                    <p className="font-medium text-foreground">API Endpoint</p>
                    <p className="mt-1 text-xs text-muted-foreground font-mono">
                      {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </aside>
  );
}


