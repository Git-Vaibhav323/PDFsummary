"use client";

import { useState, useCallback, useEffect } from "react";
import TopNavbar from "@/components/TopNavbar";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import ConversationHistory from "@/components/ConversationHistory";
import { apiClient, ChatResponse } from "@/lib/api";
import { Card } from "@/components/ui/card";

interface Message {
  role: "user" | "assistant";
  content: string;
  visualization?: string | {
    image_base64?: string;
    markdown?: string;
    chart_type?: string;
    title?: string;
    headers?: string[];
    rows?: string[][];
    error?: string;
  };
  timestamp: Date;
}

export default function Home() {
  const [isPDFLoaded, setIsPDFLoaded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | undefined>();
  const [uploadedFileSize, setUploadedFileSize] = useState<number | undefined>();
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>();

  const handleUploadSuccess = useCallback((fileName?: string, fileSize?: number) => {
    setIsPDFLoaded(true);
    setMessages([]);
    setError(null);
    setUploadedFileName(fileName);
    setUploadedFileSize(fileSize);
    setCurrentConversationId(undefined); // Reset conversation on new upload
  }, []);

  const handleUploadError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setIsPDFLoaded(false);
  }, []);

  const handleSendMessage = useCallback(
    async (question: string) => {
      if (!isPDFLoaded) {
        setError("Please upload and process a PDF first");
        return;
      }

      // Add user message
      const userMessage: Message = {
        role: "user",
        content: question,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response: ChatResponse = await apiClient.sendMessage(question, currentConversationId);
        
        // Update conversation ID if a new one was created
        if (response.conversation_id && response.conversation_id !== currentConversationId) {
          setCurrentConversationId(response.conversation_id);
        }

        // Add assistant message
        // DEBUG: Log visualization object
        console.log("Response visualization:", response.visualization);
        console.log("Has headers:", response.visualization?.headers);
        console.log("Has rows:", response.visualization?.rows);
        
        const assistantMessage: Message = {
          role: "assistant",
          content: response.answer,
          visualization: response.visualization || undefined,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err: any) {
        const errorMessage: Message = {
          role: "assistant",
          content: `Error: ${err.message || "Failed to get response"}`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        setError(err.message || "Failed to get response");
      } finally {
        setIsLoading(false);
      }
    },
    [isPDFLoaded, currentConversationId]
  );

  const handleClearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setCurrentConversationId(undefined);
  }, []);

  const handleNewConversation = useCallback(() => {
    setMessages([]);
    setError(null);
    setCurrentConversationId(undefined);
  }, []);

  const handleSelectConversation = useCallback(async (conversationId: string) => {
    if (conversationId === currentConversationId) {
      return; // Already selected
    }

    setIsLoading(true);
    setError(null);
    try {
      const conversation = await apiClient.getConversation(conversationId);
      
      // Convert conversation messages to Message format
      const loadedMessages: Message[] = conversation.messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        visualization: msg.visualization || undefined,
        timestamp: new Date(msg.created_at),
      }));

      setMessages(loadedMessages);
      setCurrentConversationId(conversationId);
    } catch (err: any) {
      setError(err.message || "Failed to load conversation");
      console.error("Failed to load conversation:", err);
    } finally {
      setIsLoading(false);
    }
  }, [currentConversationId]);

  const handleRemoveFile = useCallback(async () => {
    try {
      const result = await apiClient.removeFile();
      if (result.success) {
        setIsPDFLoaded(false);
        setMessages([]);
        setError(null);
        setUploadedFileName(undefined);
        setUploadedFileSize(undefined);
        setCurrentConversationId(undefined);
      } else {
        setError(result.error || "Failed to remove file");
      }
    } catch (err: any) {
      setError(err.message || "Failed to remove file");
    }
  }, []);

  // Check backend health on mount (silently, don't show error immediately)
  useEffect(() => {
    const checkBackend = async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      console.log(`[Frontend] Checking backend connection at ${apiUrl}...`);
      console.log(`[Frontend] Environment variable NEXT_PUBLIC_API_URL: ${process.env.NEXT_PUBLIC_API_URL || "not set (using default)"}`);
      
      const isHealthy = await apiClient.checkHealth();
      if (!isHealthy) {
        // Only log to console, don't show error banner immediately
        console.error("❌ [Frontend] Backend server is not reachable!");
        console.warn("📝 [Frontend] Steps to fix:");
        console.warn("   1. Make sure the backend is running: python run.py");
        console.warn("   2. Check the backend terminal to see which port it's using");
        console.warn("   3. Update NEXT_PUBLIC_API_URL in frontend/.env.local to match");
        console.warn("   4. Restart the frontend: stop with Ctrl+C, then run 'npm run dev' again");
        console.warn(`   5. Current configured URL: ${apiUrl}`);
      } else {
        console.log("✅ [Frontend] Backend is healthy and reachable!");
      }
    };
    
    // Wait a bit before checking to allow backend to start
    const timeoutId = setTimeout(checkBackend, 1000);
    return () => clearTimeout(timeoutId);
  }, []);

  return (
    <div className="flex h-screen flex-col">
      <TopNavbar isPDFLoaded={isPDFLoaded} isProcessing={isProcessing} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          isPDFLoaded={isPDFLoaded}
          isProcessing={isProcessing}
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
          onClearChat={handleClearChat}
          onRemoveFile={handleRemoveFile}
          messageCount={messages.length}
          uploadedFileName={uploadedFileName}
          uploadedFileSize={uploadedFileSize}
        >
          <ConversationHistory
            currentConversationId={currentConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            isPDFLoaded={isPDFLoaded}
          />
        </Sidebar>
        <main className="flex flex-1 flex-col overflow-hidden min-h-0">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            isPDFLoaded={isPDFLoaded}
            onSuggestionClick={handleSendMessage}
          />
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={!isPDFLoaded || isLoading}
          />
        </main>
      </div>
      {error && (
        <div className="border-t border-destructive/20 bg-destructive/5 p-4">
          <Card className="border-destructive/20 bg-destructive/10">
            <div className="flex items-center gap-3 p-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-destructive/20">
                <span className="text-destructive">!</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-destructive">Error</p>
                <p className="text-xs text-destructive/80">{error}</p>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

