"use client";

import { FileText } from "lucide-react";
import StatusBadge from "./StatusBadge";

interface TopNavbarProps {
  isPDFLoaded: boolean;
  isProcessing?: boolean;
  activeDocumentsCount?: number;
}

export default function TopNavbar({
  isPDFLoaded,
  isProcessing = false,
  activeDocumentsCount = 0,
}: TopNavbarProps) {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-[#E5E7EB] bg-white shadow-sm">
      <div className="container flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#DBEAFE] ring-2 ring-[#2563EB]/10 shadow-sm">
            <FileText className="h-5 w-5 text-[#2563EB]" />
          </div>
          <div className="text-left">
            <h1 className="text-lg font-semibold tracking-tight text-left text-[#111827]">PDF Intelligence Assistant</h1>
            <p className="text-xs text-[#6B7280] text-left">Enterprise AI Document Assistant</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {activeDocumentsCount > 0 && (
            <div className="text-sm text-[#6B7280]">
              {activeDocumentsCount} document{activeDocumentsCount !== 1 ? "s" : ""} active
            </div>
          )}
          <StatusBadge isPDFLoaded={isPDFLoaded} isProcessing={isProcessing} />
        </div>
      </div>
    </nav>
  );
}

