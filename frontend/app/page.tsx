"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import TopNavbar from "@/components/TopNavbar";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import ConversationHistory from "@/components/ConversationHistory";
import FinancialDashboard from "@/components/FinancialDashboard";
import { apiClient, ChatResponse } from "@/lib/api";
import { Card } from "@/components/ui/card";

interface Message {
  role: "user" | "assistant";
  content: string;
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
  // Load conversation ID from localStorage on mount to restore chat history
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('currentConversationId');
        return saved || undefined;
      } catch (e) {
        return undefined;
      }
    }
    return undefined;
  });
  const [sessionId, setSessionId] = useState<string | undefined>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('sessionId');
        return saved || undefined;
      } catch (e) {
        return undefined;
      }
    }
    return undefined;
  });
  // CRITICAL: Initialize selectedDocumentIds as empty - MUST be empty on every reload
  // Force clear immediately - no persistence
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>(() => {
    // Synchronously clear on initialization
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('selectedDocumentIds');
        sessionStorage.removeItem('selectedDocumentIds');
      } catch (e) {
        // Ignore
      }
    }
    return [];
  });
  const [showFinancialDashboard, setShowFinancialDashboard] = useState(false);
  const [dashboardDocumentIds, setDashboardDocumentIds] = useState<string[]>([]);
  const [dashboardCompanyName, setDashboardCompanyName] = useState<string | undefined>();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [isDashboardGenerating, setIsDashboardGenerating] = useState(false);
  const [isDashboardReady, setIsDashboardReady] = useState(false);
  const [conversationRefreshTrigger, setConversationRefreshTrigger] = useState(0);
  const [documentRefreshTrigger, setDocumentRefreshTrigger] = useState(0);
  const [sidebarTab, setSidebarTab] = useState<"chat" | "dashboard">("chat");

  const handleUploadSuccess = useCallback(async (fileName?: string, fileSize?: number, documentId?: string) => {
    setIsPDFLoaded(true);
    setError(null);
    setUploadedFileName(fileName);
    setUploadedFileSize(fileSize);
    
    // Automatically select the uploaded document
    if (documentId) {
      setSelectedDocumentIds((prev) => {
        if (!prev.includes(documentId)) {
          return [...prev, documentId];
        }
        return prev;
      });
    }
    
    // Trigger document list refresh
    setDocumentRefreshTrigger((prev) => prev + 1);
  }, []);

  const handleUploadError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setIsPDFLoaded(false);
  }, []);

  const handleSendMessage = useCallback(
    async (question: string, useWebSearch?: boolean) => {
      if (!isPDFLoaded) {
        setError("Please upload and process a PDF first");
        return;
      }

        // Add user message to chat
        const userMessage: Message = {
          role: "user",
          content: question,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
      
      setIsLoading(true);
      setError(null);

      try {
        // Use session ID or conversation ID for session management
        const effectiveSessionId = sessionId || currentConversationId;
        
        const response: ChatResponse = await apiClient.sendMessage(
          question,
          currentConversationId,
          effectiveSessionId,
          selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
          useWebSearch  // Pass web search preference
        );
        
        // Update conversation ID if a new one was created
        if (response.conversation_id && response.conversation_id !== currentConversationId) {
          setCurrentConversationId(response.conversation_id);
          // Persist to localStorage
          if (typeof window !== 'undefined') {
            try {
              localStorage.setItem('currentConversationId', response.conversation_id);
            } catch (e) {
              console.warn("Failed to save conversation ID to localStorage:", e);
            }
          }
          // Also set session ID if not already set
          if (!sessionId) {
            setSessionId(response.conversation_id);
            if (typeof window !== 'undefined') {
              try {
                localStorage.setItem('sessionId', response.conversation_id);
              } catch (e) {
                console.warn("Failed to save session ID to localStorage:", e);
              }
            }
          }
          // Trigger conversation list refresh
          setConversationRefreshTrigger(Date.now());
        } else if (response.conversation_id) {
          // Existing conversation - ensure it's persisted
          if (typeof window !== 'undefined') {
            try {
              localStorage.setItem('currentConversationId', response.conversation_id);
            } catch (e) {
              console.warn("Failed to save conversation ID to localStorage:", e);
            }
          }
          // Trigger silent refresh to update message count
          setConversationRefreshTrigger(Date.now());
        }

        // Add assistant message
        // Map backend response to the UI's `visualization` shape
        let visualization = undefined;

        // PRIORITY 1: Check if visualization field exists (current backend format)
        if (response.visualization) {
          // Check for error first
          if (response.visualization.error) {
            console.warn("Visualization error from backend:", response.visualization.error);
            visualization = undefined; // Don't render error
          } else if (response.visualization.headers && response.visualization.rows) {
            // Table format with headers and rows
            visualization = {
              chart_type: response.visualization.chart_type || 'table',
              type: response.visualization.chart_type || 'table',
              headers: response.visualization.headers,
              rows: response.visualization.rows,
              title: response.visualization.title,
              markdown: response.visualization.markdown, // Keep markdown if available
            };
          } else if (response.visualization.labels && response.visualization.values) {
            // Chart format with labels and values
            visualization = {
              chart_type: response.visualization.chart_type || response.visualization.type,
              type: response.visualization.chart_type || response.visualization.type,
              title: response.visualization.title,
              labels: response.visualization.labels,
              values: response.visualization.values,
              groups: response.visualization.groups,  // For stacked bar charts
              xAxis: response.visualization.xAxis,
              yAxis: response.visualization.yAxis,
            };
          } else if (response.visualization.markdown) {
            // Markdown table
            visualization = {
              markdown: response.visualization.markdown,
              chart_type: 'table',
            };
          } else if (response.visualization.image_base64) {
            // Base64 image
            visualization = {
              image_base64: response.visualization.image_base64,
              title: response.visualization.title,
            };
          }
        }
        
        // PRIORITY 2: Check chart field (alternative format)
        if (!visualization && response.chart) {
          if (response.chart.type === 'table' && response.chart.headers && response.chart.rows) {
            visualization = {
              chart_type: 'table',
              headers: response.chart.headers,
              rows: response.chart.rows,
              title: response.chart.title || undefined,
            };
          } else if (response.chart.type && response.chart.labels && response.chart.values) {
            visualization = {
              chart_type: response.chart.type,
              type: response.chart.type,
              title: response.chart.title || undefined,
              labels: response.chart.labels,
              values: response.chart.values,
              xAxis: response.chart.xAxis,
              yAxis: response.chart.yAxis,
            };
          }
        }
        
        // PRIORITY 3: Check table field (markdown string)
        if (!visualization && response.table) {
          visualization = { 
            markdown: response.table,
            chart_type: 'table',
          };
        }

        console.log("=== FULL API RESPONSE ===");
        console.log(JSON.stringify(response, null, 2));
        console.log("=== CHART DATA ===");
        console.log(response.chart);
        console.log("=== TABLE DATA ===");
        console.log(response.table);
        console.log("=== MAPPED VISUALIZATION ===");
        console.log(visualization);
        
        // CRITICAL DEBUG: Log what we're about to send to ChatMessage
        if (visualization) {
          console.log("✅ Visualization will be rendered");
          if (visualization.headers) console.log(`  - Headers: ${visualization.headers.length} columns`);
          if (visualization.rows) console.log(`  - Rows: ${visualization.rows.length} rows`);
          if (visualization.labels) console.log(`  - Labels: ${visualization.labels.length} items`);
          if (visualization.values) console.log(`  - Values: ${visualization.values.length} items`);
        } else {
          console.warn("❌ No visualization data to render!");
        }

        const assistantMessage: Message = {
          role: "assistant",
          content: response.answer,
          visualization: visualization || undefined,
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
    [isPDFLoaded, currentConversationId, sessionId, selectedDocumentIds]
  );

  const handleClearChat = useCallback(async () => {
    // Clear messages from current conversation if it exists
    if (currentConversationId) {
      try {
        await apiClient.clearConversationMessages(currentConversationId);
        console.log(`[Chat Memory] ✅ Cleared messages from conversation ${currentConversationId}`);
      } catch (err) {
        console.error("Failed to clear conversation messages:", err);
        // Fallback to clearing memory
        try {
          await apiClient.clearMemory();
        } catch (e) {
          console.error("Failed to clear memory:", e);
        }
      }
    } else {
      // No conversation ID, just clear memory
      try {
        await apiClient.clearMemory();
      } catch (err) {
        console.error("Failed to clear memory:", err);
      }
    }
    
    // Clear UI state
    setMessages([]);
    setError(null);
    // Don't reset conversation ID - allow continuing same conversation
  }, [currentConversationId]);

  const handleNewConversation = useCallback(async () => {
    setMessages([]);
    setError(null);
    setCurrentConversationId(undefined);
    setSessionId(undefined);
    
    // Clear conversation ID from localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('currentConversationId');
        localStorage.removeItem('sessionId');
      } catch (e) {
        console.warn("Failed to clear conversation ID from localStorage:", e);
      }
    }
    
    setShowFinancialDashboard(false); // Close Financial Dashboard when starting new conversation
    setDashboardDocumentIds([]);
    setDashboardCompanyName(undefined);
    setDashboardData(null);
    setIsDashboardReady(false);
    setIsDashboardGenerating(false);
    setSidebarTab("chat"); // Switch back to chat tab
    // Clear memory on backend
    try {
      await apiClient.clearMemory();
    } catch (err) {
      console.error("Failed to clear memory:", err);
    }
    // Trigger conversation list refresh
    setConversationRefreshTrigger(Date.now());
  }, []);

  // CRITICAL: Clear selected documents on EVERY page reload/mount
  // This MUST be the first useEffect to run - ensures clean state
  useEffect(() => {
    // ALWAYS clear on mount - no conditions, no ref checks
    // This ensures selected documents are cleared on every page reload
    setSelectedDocumentIds([]);
    
    // Also clear from any potential storage (defensive)
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('selectedDocumentIds');
        sessionStorage.removeItem('selectedDocumentIds');
      } catch (e) {
        // Ignore storage errors
      }
    }
    
    console.log("[Page Reload] ✅ FORCE CLEARED selected documents - starting with empty selection");
    
    // Double-check clear after a short delay to catch any race conditions
    const timeoutId = setTimeout(() => {
      setSelectedDocumentIds((prev) => {
        if (prev.length > 0) {
          console.log("[Page Reload] ⚠️ Found selected documents after clear, clearing again:", prev);
          return [];
        }
        return prev;
      });
    }, 50);
    
    return () => clearTimeout(timeoutId);
  }, []); // Empty deps = run only on mount/reload

  // Load conversation messages on mount if currentConversationId exists
  useEffect(() => {
    const loadCurrentConversation = async () => {
      // Load conversation if we have an ID and PDF is loaded
      // Remove messages.length === 0 check to allow reloading even if messages exist
      if (currentConversationId && isPDFLoaded) {
        try {
          console.log(`[Chat Memory] Loading conversation: ${currentConversationId}`);
          const conversation = await apiClient.getConversation(currentConversationId);
          console.log(`[Chat Memory] Loaded ${conversation.messages.length} messages`);
          const loadedMessages: Message[] = conversation.messages.map((msg) => {
            let visualization = undefined;
            if (msg.visualization) {
              try {
                const vizData = typeof msg.visualization === 'string' 
                  ? JSON.parse(msg.visualization) 
                  : msg.visualization;
                
                if (vizData.headers && vizData.rows) {
                  visualization = {
                    chart_type: vizData.chart_type || 'table',
                    type: vizData.type || 'table',
                    headers: vizData.headers,
                    rows: vizData.rows,
                    title: vizData.title,
                    markdown: vizData.markdown,
                  };
                } else if (vizData.labels && vizData.values) {
                  visualization = {
                    chart_type: vizData.chart_type || vizData.type,
                    type: vizData.type,
                    title: vizData.title,
                    labels: vizData.labels,
                    values: vizData.values,
                    xAxis: vizData.xAxis,
                    yAxis: vizData.yAxis,
                  };
                } else if (vizData.markdown) {
                  visualization = {
                    markdown: vizData.markdown,
                    chart_type: 'table',
                  };
                }
              } catch (e) {
                console.warn("Failed to parse visualization:", e);
              }
            }
            
            return {
              role: msg.role,
              content: msg.content,
              visualization,
              timestamp: new Date(msg.created_at),
            };
          });
          
          setMessages(loadedMessages);
          setSessionId(currentConversationId);
          console.log(`[Chat Memory] ✅ Successfully loaded conversation with ${loadedMessages.length} messages`);
        } catch (err: any) {
          console.error("[Chat Memory] ❌ Failed to load current conversation:", err);
          // If conversation doesn't exist, clear the stored ID
          if (err.message?.includes('not found') || err.message?.includes('404')) {
            console.log("[Chat Memory] Conversation not found, clearing stored ID");
            setCurrentConversationId(undefined);
            if (typeof window !== 'undefined') {
              try {
                localStorage.removeItem('currentConversationId');
                localStorage.removeItem('sessionId');
              } catch (e) {
                // Ignore
              }
            }
          }
        }
      }
    };
    
    loadCurrentConversation();
  }, [currentConversationId, isPDFLoaded]); // Only run when currentConversationId or isPDFLoaded changes

  const handleSelectConversation = useCallback(async (conversationId: string) => {
    if (conversationId === currentConversationId) {
      return; // Already selected
    }

    setShowFinancialDashboard(false); // Close Financial Dashboard when selecting conversation
    // Keep dashboard data but reset ready state
    setIsDashboardReady(false);
    setIsDashboardGenerating(false);
    setSidebarTab("chat"); // Switch back to chat tab
    setIsLoading(true);
    setError(null);
    
    // Persist conversation ID to localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('currentConversationId', conversationId);
        localStorage.setItem('sessionId', conversationId);
      } catch (e) {
        console.warn("Failed to save conversation ID to localStorage:", e);
      }
    }
    
    try {
      const conversation = await apiClient.getConversation(conversationId);
      
      // Convert conversation messages to Message format
      const loadedMessages: Message[] = conversation.messages.map((msg) => {
        let visualization = undefined;
        if (msg.visualization) {
          try {
            const vizData = typeof msg.visualization === 'string' 
              ? JSON.parse(msg.visualization) 
              : msg.visualization;
            
            if (vizData.headers && vizData.rows) {
              visualization = {
                chart_type: vizData.chart_type || 'table',
                type: vizData.type || 'table',
                headers: vizData.headers,
                rows: vizData.rows,
                title: vizData.title,
                markdown: vizData.markdown,
              };
            } else if (vizData.labels && vizData.values) {
              visualization = {
                chart_type: vizData.chart_type || vizData.type,
                type: vizData.type,
                title: vizData.title,
                labels: vizData.labels,
                values: vizData.values,
                xAxis: vizData.xAxis,
                yAxis: vizData.yAxis,
              };
            } else if (vizData.markdown) {
              visualization = {
                markdown: vizData.markdown,
                chart_type: 'table',
              };
            }
          } catch (e) {
            console.warn("Failed to parse visualization:", e);
          }
        }
        return {
          role: msg.role,
          content: msg.content,
          visualization,
          timestamp: new Date(msg.created_at),
        };
      });

      setMessages(loadedMessages);
      setCurrentConversationId(conversationId);
      setSessionId(conversationId); // Use conversation ID as session ID
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

  // Extract company name from filename
  const extractCompanyName = (filename: string): string | undefined => {
    // Try to extract company name from filename patterns
    // e.g., "IndianOil_Annual_Report_2022.pdf" -> "IndianOil"
    const patterns = [
      /^([A-Z][a-zA-Z]+)/,  // First capitalized word
      /([A-Z][a-zA-Z]+).*Annual/,  // Word before "Annual"
      /([A-Z][a-zA-Z]+).*Report/,  // Word before "Report"
    ];
    
    for (const pattern of patterns) {
      const match = filename.match(pattern);
      if (match && match[1]) {
        return match[1];
      }
    }
    
    return undefined;
  };

  // Generate dashboard in background when documents are selected
  const generateDashboardInBackground = useCallback(async (documentIds: string[]) => {
    setIsDashboardGenerating(true);
    setIsDashboardReady(false);
    setDashboardData(null);
    setError(null); // Clear previous errors
    
    try {
      const documents = await apiClient.listDocuments();
      const firstDoc = documents.documents?.find((d: any) => documentIds.includes(d.id));
      const companyName = firstDoc ? extractCompanyName(firstDoc.filename?.toLowerCase() || "") : undefined;
      
      setDashboardCompanyName(companyName);
      setDashboardDocumentIds(documentIds);
      
      // Generate dashboard data in background (API checks cache first)
      const data = await apiClient.generateFinancialDashboard(documentIds, companyName);
      setDashboardData(data);
      setIsDashboardReady(true);
      setError(null); // Clear any previous errors
    } catch (err: any) {
      console.error("Error generating dashboard:", err);
      const errorMessage = err.message || "Failed to generate dashboard";
      setError(errorMessage);
      setIsDashboardReady(false);
      // Set dashboard data with error so component can display it
      setDashboardData({ error: errorMessage });
    } finally {
      setIsDashboardGenerating(false);
    }
  }, []);

  // Manual dashboard creation handler
  const handleCreateDashboard = useCallback(() => {
    if (selectedDocumentIds.length === 0) {
      setError("Please select at least one document to create dashboard");
      return;
    }
    
    // Clear previous dashboard data and start fresh generation
    setDashboardData(null);
    setIsDashboardReady(false);
    generateDashboardInBackground(selectedDocumentIds);
  }, [selectedDocumentIds, generateDashboardInBackground]);

  const handleOpenFinancialDashboard = useCallback(() => {
    // Just show the dashboard if data is ready, otherwise trigger generation
    if (selectedDocumentIds.length === 0) {
      setError("Please select at least one document");
      return;
    }
    
    if (!isDashboardReady && !isDashboardGenerating) {
      // If not ready and not generating, start generation
      generateDashboardInBackground(selectedDocumentIds);
    }
    
    setShowFinancialDashboard(true);
  }, [selectedDocumentIds, isDashboardReady, isDashboardGenerating, generateDashboardInBackground]);

  const handleDocumentSelect = useCallback((documentId: string) => {
    // Update selection for multi-document queries
    // Dashboard will be cleared when selection changes (user needs to recreate)
    setSelectedDocumentIds((prev) => {
      const newSelection = prev.includes(documentId)
        ? prev.filter((id) => id !== documentId)
        : [...prev, documentId];
      
      // Clear dashboard if selection changes (user needs to recreate)
      if (JSON.stringify([...newSelection].sort()) !== JSON.stringify([...prev].sort())) {
        setDashboardData(null);
        setIsDashboardReady(false);
        setIsDashboardGenerating(false);
        setDashboardDocumentIds([]);
      }
      
      return newSelection;
    });
  }, []);

  const handleDocumentDelete = useCallback((documentId: string) => {
    setSelectedDocumentIds((prev) => {
      // If no documents selected and PDF was loaded, update state
      if (prev.length === 1 && prev[0] === documentId) {
        setIsPDFLoaded(false);
        setUploadedFileName(undefined);
        setUploadedFileSize(undefined);
      }
      
      // Clear dashboard when document is deleted
      setDashboardData(null);
      setIsDashboardReady(false);
      setIsDashboardGenerating(false);
      setDashboardDocumentIds([]);
      
      return prev.filter((id) => id !== documentId);
    });
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

  // Finance Agent processing now happens on button click, not on PDF upload
  
  return (
    <div className="flex h-screen flex-col">
      <TopNavbar 
        isPDFLoaded={isPDFLoaded} 
        isProcessing={isProcessing}
        activeDocumentsCount={selectedDocumentIds.length}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          isPDFLoaded={isPDFLoaded}
          isProcessing={isProcessing}
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
          onClearChat={handleClearChat}
          onRemoveFile={handleRemoveFile}
          onOpenFinanceAgent={handleOpenFinancialDashboard}
          messageCount={messages.length}
          uploadedFileName={uploadedFileName}
          uploadedFileSize={uploadedFileSize}
          selectedDocumentIds={selectedDocumentIds}
          onDocumentSelect={handleDocumentSelect}
          onDocumentDelete={handleDocumentDelete}
          documentRefreshTrigger={documentRefreshTrigger}
          activeTab={sidebarTab}
          isDashboardGenerating={isDashboardGenerating}
          isDashboardReady={isDashboardReady}
          onCreateDashboard={handleCreateDashboard}
          onTabChange={(tab) => {
            setSidebarTab(tab);
            if (tab === "dashboard" && selectedDocumentIds.length > 0) {
              // Show dashboard when user clicks Dashboard tab
              handleOpenFinancialDashboard();
            } else if (tab === "chat") {
              // Hide dashboard when switching back to chat (but keep data)
              setShowFinancialDashboard(false);
            }
          }}
          key={`doc-list-${selectedDocumentIds.length}`}
        >
          <ConversationHistory
            currentConversationId={currentConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            isPDFLoaded={isPDFLoaded}
            refreshTrigger={conversationRefreshTrigger}
          />
        </Sidebar>
        <main className="flex flex-1 flex-col overflow-hidden min-h-0 bg-white">
          {sidebarTab === "dashboard" && selectedDocumentIds.length > 0 ? (
            <FinancialDashboard
              documentIds={dashboardDocumentIds.length > 0 ? dashboardDocumentIds : selectedDocumentIds}
              companyName={dashboardCompanyName}
              dashboardData={dashboardData}
              isGenerating={isDashboardGenerating}
              isReady={isDashboardReady}
              onClose={() => {
                setSidebarTab("chat");
                setShowFinancialDashboard(false);
              }}
            />
          ) : (
            <>
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
            </>
          )}
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

