import axios from "axios";

// Get API URL from environment or default to common ports
const getApiUrl = (): string => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl) {
    console.log(`[API Config] Using NEXT_PUBLIC_API_URL from .env.local: ${envUrl}`);
    return envUrl;
  }
  // Default to 8000, but backend might be on 8001, 8002, etc. if 8000 is in use
  console.warn(`[API Config] NEXT_PUBLIC_API_URL not set, using default: http://localhost:8000`);
  console.warn(`[API Config] Create frontend/.env.local with: NEXT_PUBLIC_API_URL=http://localhost:8001`);
  return "http://localhost:8000";
};

const API_URL = getApiUrl();
console.log(`[API Config] API base URL: ${API_URL}`);

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 600000, // 10 minutes timeout for large file uploads and processing
});

// Add request interceptor to log API calls
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error("[API] Request error:", error);
    return Promise.reject(error);
  }
);

// Add response interceptor to log errors
api.interceptors.response.use(
  (response) => {
    console.log(`[API] ✅ ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    if (error.code === "ECONNREFUSED" || error.code === "ERR_NETWORK" || error.message?.includes("Network Error")) {
      console.error(`[API] ❌ Connection refused to ${API_URL}`);
      console.error(`[API] 💡 Make sure:`);
      console.error(`[API]    1. Backend is running: python run.py`);
      console.error(`[API]    2. Check backend terminal for the port number`);
      console.error(`[API]    3. Update frontend/.env.local with correct port`);
      console.error(`[API]    4. RESTART the frontend after updating .env.local`);
      console.error(`[API]    Current API URL: ${API_URL}`);
    } else if (error.response) {
      console.error(`[API] ❌ ${error.config?.method?.toUpperCase()} ${error.config?.url} - ${error.response.status}: ${error.response.statusText}`);
    } else {
      console.error(`[API] ❌ Error:`, error.message);
    }
    return Promise.reject(error);
  }
);

export interface UploadResponse {
  success: boolean;
  message?: string;
  error?: string;
  pages?: number;
  chunks?: number;
}

export interface ChatResponse {
  answer: string;
  // Backend returns `chart` and `table` fields; map these to `visualization` on the frontend
  chart?: {
    type: string;
    title?: string;
    labels?: string[];
    values?: number[];
    xAxis?: string;
    yAxis?: string;
    headers?: string[];
    rows?: string[][];
  } | null;
  table?: string | null;
  visualization?: {
    image_base64?: string;
    markdown?: string;
    chart_type?: string;
    title?: string;
    headers?: string[];
    rows?: string[][];
    error?: string;
  } | null;
  conversation_id?: string;
}

export interface ChatRequest {
  question: string;
  conversation_id?: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  visualization?: string | null;
  created_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export const apiClient = {
  /**
   * Upload PDF file
   */
  async uploadPDF(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    try {
      console.log(`Uploading PDF to ${API_URL}/upload_pdf`);
      const response = await api.post<UploadResponse>("/upload_pdf", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 600000, // 10 minutes for large file uploads and processing
      });
      console.log("Upload successful:", response.data);
      // Backend returns message, pages, chunks, document_ids - add success flag
      return {
        ...response.data,
        success: true,
      };
    } catch (error: any) {
      console.error("Upload error:", error);
      console.error("Error details:", {
        message: error.message,
        code: error.code,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
      });
      
      // Better error handling
      if (error.code === "ECONNREFUSED" || error.message?.includes("Network Error") || error.code === "ERR_NETWORK") {
        // Try to detect if backend is on a different port
        const commonPorts = [8000, 8001, 8002, 8003];
        const baseUrl = API_URL.replace(/:\d+$/, '');
        let suggestedPort = null;
        
        // Quick check (async, but we'll just suggest)
        for (const port of commonPorts) {
          const testUrl = `${baseUrl}:${port}`;
          if (testUrl !== API_URL) {
            suggestedPort = port;
            break;
          }
        }
        
        let errorMsg = `Cannot connect to backend at ${API_URL}.\n\nPlease ensure:\n1. The FastAPI server is running (run: python run.py in the backend directory)\n2. Check the terminal where you ran 'python run.py' to see which port it's using\n3. If the backend is on a different port, update NEXT_PUBLIC_API_URL in frontend/.env.local\n4. Restart the frontend after updating .env.local (stop with Ctrl+C and run 'npm run dev' again)\n\nCurrent API URL: ${API_URL}`;
        
        if (suggestedPort) {
          errorMsg += `\n\nTip: Try checking if the backend is running on port ${suggestedPort} instead.`;
        }
        
        return {
          success: false,
          error: errorMsg,
        };
      }
      
      if (error.response?.status === 404) {
        // 404 means we connected but endpoint doesn't exist
        // This could mean backend is running on wrong port or route is missing
        const baseUrl = API_URL.replace(/:\d+$/, '');
        return {
          success: false,
          error: `Endpoint not found at ${API_URL}/upload_pdf.\n\nPlease verify:\n1. Backend is running: python run.py\n2. Check which port the backend is using (check the terminal where you ran 'python run.py')\n3. Backend should be accessible at: ${API_URL}/docs\n4. If backend is on a different port, update NEXT_PUBLIC_API_URL in frontend/.env.local\n5. RESTART the frontend after updating .env.local (stop with Ctrl+C and run 'npm run dev' again)\n\nCurrent API URL: ${API_URL}\n\nCommon ports to check: ${baseUrl}:8000, ${baseUrl}:8001, ${baseUrl}:8002`,
        };
      }
      
      if (error.code === "ECONNABORTED" || error.message?.includes("timeout")) {
        return {
          success: false,
          error: "Upload timeout. The file might be too large or the server is taking too long to process.",
        };
      }
      
      return {
        success: false,
        error:
          error.response?.data?.detail ||
          error.response?.data?.message ||
          error.message ||
          `Failed to upload PDF (Status: ${error.response?.status || "unknown"})`,
      };
    }
  },

  /**
   * Send chat message
   */
  async sendMessage(question: string, conversationId?: string): Promise<ChatResponse> {
    try {
      const response = await api.post<ChatResponse>("/chat", {
        question,
        conversation_id: conversationId,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
          error.message ||
          "Failed to send message"
      );
    }
  },

  /**
   * Create a new conversation
   */
  async createConversation(title?: string): Promise<Conversation> {
    try {
      const response = await api.post<Conversation>("/conversations", {
        title,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
          error.message ||
          "Failed to create conversation"
      );
    }
  },

  /**
   * List all conversations
   */
  async listConversations(limit: number = 50): Promise<Conversation[]> {
    try {
      const response = await api.get<{ conversations: Conversation[] }>("/conversations", {
        params: { limit },
      });
      return response.data.conversations;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
          error.message ||
          "Failed to list conversations"
      );
    }
  },

  /**
   * Get a conversation with its messages
   */
  async getConversation(conversationId: string): Promise<ConversationWithMessages> {
    try {
      const response = await api.get<ConversationWithMessages>(`/conversations/${conversationId}`);
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
          error.message ||
          "Failed to get conversation"
      );
    }
  },

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: string): Promise<{ success: boolean; message?: string }> {
    try {
      const response = await api.delete<{ message: string; success: boolean }>(`/conversations/${conversationId}`);
      return {
        success: true,
        message: response.data.message,
      };
    } catch (error: any) {
      return {
        success: false,
        message:
          error.response?.data?.detail ||
          error.message ||
          "Failed to delete conversation",
      };
    }
  },

  /**
   * Remove uploaded file and clear vector store
   */
  async removeFile(): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await api.delete("/remove_file");
      return {
        success: true,
        ...response.data,
      };
    } catch (error: any) {
      console.error("Remove file error:", error);
      return {
        success: false,
        error:
          error.response?.data?.detail ||
          error.response?.data?.message ||
          error.message ||
          "Failed to remove file",
      };
    }
  },

  /**
   * Check API health - tries common ports if default fails
   */
  async checkHealth(): Promise<boolean> {
    // First try the configured URL
    try {
      console.log(`[Health Check] Checking backend at ${API_URL}/health`);
      const response = await api.get("/health", { 
        timeout: 30000, // 30 seconds for health check (allow for cold starts)
        validateStatus: (status) => status < 500 // Don't throw on 4xx/5xx
      });
      if (response.status === 200) {
        console.log("✅ [Health Check] Backend is healthy:", response.data);
        return true;
      } else {
        console.warn(`[Health Check] Backend returned status ${response.status}`);
      }
    } catch (error: any) {
      const errorMsg = error.message || String(error);
      console.warn(`[Health Check] Failed at ${API_URL}:`, errorMsg);
      
      // Check if it's a connection error
      if (error.code === "ECONNREFUSED" || error.code === "ERR_NETWORK" || error.message?.includes("Network Error")) {
        console.warn(`[Health Check] Connection refused - backend may not be running on ${API_URL}`);
      }
    }
    
    // If configured URL fails, try common ports
    const commonPorts = [8000, 8001, 8002, 8003];
    const baseUrl = API_URL.replace(/:\d+$/, ''); // Remove port from URL
    
    for (const port of commonPorts) {
      const testUrl = `${baseUrl}:${port}`;
      // Skip if we already tried this URL
      if (testUrl === API_URL) continue;
      
      try {
        console.log(`[Health Check] Trying ${testUrl}/health...`);
        const testApi = axios.create({
          baseURL: testUrl,
          timeout: 10000, // Longer timeout for alternate ports
        });
        const response = await testApi.get("/health", { 
          timeout: 10000,
          validateStatus: (status) => status < 500
        });
        if (response.status === 200) {
          console.log(`✅ [Health Check] Backend found at ${testUrl}:`, response.data);
          console.warn(`⚠️ [Health Check] Backend is running at ${testUrl} but frontend is configured for ${API_URL}`);
          console.warn(`💡 [Health Check] Update NEXT_PUBLIC_API_URL in frontend/.env.local to: ${testUrl}`);
          console.warn(`🔄 [Health Check] Then restart the frontend: stop with Ctrl+C and run 'npm run dev' again`);
          return true;
        }
      } catch (error: any) {
        // Continue to next port
        continue;
      }
    }
    
    console.error("❌ [Health Check] Backend not found on any common ports:", commonPorts);
    console.error("💡 [Health Check] Make sure the backend is running: python run.py");
    return false;
  },
};

