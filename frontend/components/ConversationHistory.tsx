"use client";

import { useState, useEffect } from "react";
import { MessageSquare, Plus, Trash2, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { apiClient, Conversation } from "@/lib/api";

interface ConversationHistoryProps {
  currentConversationId?: string;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  isPDFLoaded: boolean;
}

export default function ConversationHistory({
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  isPDFLoaded,
}: ConversationHistoryProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  const loadConversations = async () => {
    if (!isPDFLoaded) {
      setConversations([]);
      return;
    }
    
    setIsLoading(true);
    try {
      const data = await apiClient.listConversations(50);
      setConversations(data);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
    // Refresh conversations every 5 seconds
    const interval = setInterval(loadConversations, 5000);
    return () => clearInterval(interval);
  }, [isPDFLoaded]);

  const handleDelete = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this conversation?")) {
      return;
    }

    setIsDeleting(conversationId);
    try {
      await apiClient.deleteConversation(conversationId);
      setConversations((prev) => prev.filter((c) => c.id !== conversationId));
      if (currentConversationId === conversationId) {
        onNewConversation();
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
      alert("Failed to delete conversation");
    } finally {
      setIsDeleting(null);
    }
  };


  if (!isPDFLoaded) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-2">
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Conversations
          </h2>
        </div>
        <Card className="border-border/50 bg-card/50 shadow-sm">
          <div className="p-4 text-center">
            <p className="text-xs text-muted-foreground">
              Upload a PDF to start conversations
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Conversations
          </h2>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onNewConversation}
          className="h-6 w-6 p-0"
          title="New conversation"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <Button
        variant="outline"
        className="w-full justify-start border-border/50 bg-card/50 hover:bg-card hover:border-border"
        onClick={onNewConversation}
      >
        <Plus className="mr-2 h-4 w-4" />
        New Conversation
      </Button>

      {isLoading ? (
        <Card className="border-border/50 bg-card/50 shadow-sm">
          <div className="p-4 text-center">
            <Loader2 className="h-4 w-4 animate-spin mx-auto text-muted-foreground" />
          </div>
        </Card>
      ) : conversations.length === 0 ? (
        <Card className="border-border/50 bg-card/50 shadow-sm">
          <div className="p-4 text-center">
            <p className="text-xs text-muted-foreground">
              No conversations yet
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-1 max-h-[400px] overflow-y-auto scrollbar-thin">
          {conversations.map((conversation) => (
            <Card
              key={conversation.id}
              className={`cursor-pointer border-border/50 transition-colors ${
                currentConversationId === conversation.id
                  ? "bg-primary/10 border-primary/50"
                  : "bg-card/50 hover:bg-card hover:border-border"
              }`}
              onClick={() => onSelectConversation(conversation.id)}
            >
              <div className="p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {conversation.title}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <p className="text-xs text-muted-foreground">
                        {conversation.message_count} message{conversation.message_count !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDelete(conversation.id, e)}
                    disabled={isDeleting === conversation.id}
                    className="flex h-6 w-6 items-center justify-center rounded-md hover:bg-destructive/20 text-muted-foreground hover:text-destructive transition-colors shrink-0 disabled:opacity-50"
                    title="Delete conversation"
                  >
                    {isDeleting === conversation.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

