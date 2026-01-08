"use client";

import { useState, useRef, useCallback } from "react";
import { Upload, FileText, X, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { formatFileSize } from "@/lib/utils";
import { apiClient } from "@/lib/api";

interface UploadCardProps {
  onUploadSuccess: (fileName?: string, fileSize?: number, documentId?: string) => void;
  onUploadError: (error: string) => void;
}

export default function UploadCard({
  onUploadSuccess,
  onUploadError,
}: UploadCardProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback((selectedFile: File) => {
    if (selectedFile.type !== "application/pdf") {
      onUploadError("Please upload a PDF file");
      return;
    }
    setFile(selectedFile);
  }, [onUploadError]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        handleFileSelect(droppedFile);
      }
    },
    [handleFileSelect]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        handleFileSelect(selectedFile);
      }
    },
    [handleFileSelect]
  );

  const handleProcessPDF = useCallback(async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      console.log("[UploadCard] Starting PDF upload...");
      
      // Simulate progress - slower and more realistic
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 85) {
            clearInterval(progressInterval);
            return 85; // Stop at 85% to show we're waiting for server
          }
          return prev + 5;
        });
      }, 500);

      console.log("[UploadCard] Calling API...");
      const startTime = Date.now();
      const result = await apiClient.uploadPDF(file);
      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`[UploadCard] Upload completed in ${duration}s`);

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (result.success) {
        console.log("[UploadCard] Upload successful, notifying parent...");
        setTimeout(() => {
          const fileName = file.name;
          const fileSize = file.size;
          const documentId = (result as any).document_id; // Get document ID from response
          setFile(null);
          setUploadProgress(0);
          setIsUploading(false);
          onUploadSuccess(fileName, fileSize, documentId);
        }, 500);
      } else {
        console.error("[UploadCard] Upload failed:", result.error);
        setIsUploading(false);
        setUploadProgress(0);
        onUploadError(result.error || "Failed to upload PDF");
      }
    } catch (error: any) {
      console.error("[UploadCard] Upload error:", error);
      setIsUploading(false);
      setUploadProgress(0);
      const errorMsg = error.code === 'ECONNABORTED' 
        ? "Upload timed out. The file might be too large or the server is busy. Please try again."
        : error.message || "Failed to upload PDF";
      onUploadError(errorMsg);
    }
  }, [file, onUploadSuccess, onUploadError]);

  const handleRemoveFile = useCallback(() => {
    setFile(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  return (
    <Card className="border-[#E5E7EB] bg-white shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-semibold text-[#111827]">Upload PDF</CardTitle>
        <CardDescription className="text-xs text-[#6B7280]">
          Upload a PDF document to start asking questions
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Drag & Drop Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all duration-200 ${
            isDragging
              ? "border-[#2563EB] bg-[#DBEAFE] shadow-md"
              : "border-[#E5E7EB] bg-[#F8FAFC] hover:border-[#2563EB] hover:bg-[#F3F4F6]"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileInputChange}
            className="hidden"
          />

          {!file ? (
            <>
              <Upload className="mb-4 h-12 w-12 text-[#6B7280]" />
              <p className="mb-2 text-sm font-medium text-[#111827]">
                Drag and drop your PDF here
              </p>
              <p className="mb-4 text-xs text-[#6B7280]">
                or click to browse
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="border-[#2563EB] text-[#2563EB] hover:bg-[#2563EB] hover:text-white font-semibold"
              >
                Browse Files
              </Button>
            </>
          ) : (
            <div className="flex w-full items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#DBEAFE]">
                <FileText className="h-5 w-5 text-[#2563EB]" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[#111827]">{file.name}</p>
                <p className="text-xs text-[#6B7280]">
                  {formatFileSize(file.size)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleRemoveFile}
                disabled={isUploading}
                className="hover:bg-[#FEE2E2] hover:text-[#DC2626]"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Upload Progress */}
        {isUploading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#6B7280]">Uploading...</span>
              <span className="text-[#6B7280]">{uploadProgress}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-[#E5E7EB]">
              <div
                className="h-full bg-[#2563EB] transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Process Button */}
        <Button
          className="w-full font-semibold shadow-md hover:shadow-lg transition-shadow bg-[#16A34A] hover:bg-[#15803D] text-white"
          onClick={handleProcessPDF}
          disabled={!file || isUploading}
          size="lg"
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            "Process PDF"
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

