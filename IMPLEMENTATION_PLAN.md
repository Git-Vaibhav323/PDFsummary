# Enterprise RAG Chatbot - Implementation Plan

## Current State Analysis
- ✅ Basic RAG pipeline working
- ✅ Single document upload
- ✅ OpenAI embeddings with smart batching (300k token limit)
- ✅ Finance agent with FAQ questions
- ✅ Chart/table generation
- ✅ Conversation storage (conversations.db)
- ⚠️ Memory system exists but limited
- ⚠️ Single document mode (overwrites on upload)
- ❌ No multi-document support
- ❌ No conversational context in queries
- ❌ No web search integration
- ❌ Finance agent state issues on reload

## Phase 1: Multi-Document Support (PRIORITY 1)
### Backend Changes
1. **Document Storage Model** - `app/database/documents.py`
   - Create documents table (id, name, upload_time, chunks_count, status)
   - Track multiple documents with unique IDs
   - Add document metadata to embeddings

2. **Vector Store Enhancement** - `app/rag/vector_store.py`
   - Modify to support multiple documents
   - Add document_id filter to retrieval
   - Cross-document search capability

3. **API Routes** - `app/api/routes.py`
   - Change `/upload_pdf` to append, not replace
   - Add `/documents` GET endpoint (list all docs)
   - Add `/documents/{id}` DELETE endpoint
   - Add `/documents/clear` to clear all

### Frontend Changes
1. **Document List Component** - `frontend/components/DocumentList.tsx`
   - Show all uploaded documents
   - Delete individual documents
   - Active/selected state

2. **Upload Component** - Update to show multiple files

## Phase 2: Conversational Context (PRIORITY 1 - CRITICAL)
### Backend Changes
1. **Enhanced Memory System** - `app/rag/memory.py`
   - Store last 10 turns per session
   - Add context injection to prompts
   - Reference resolution ("that", "it", "same", etc.)
   - Token-safe truncation

2. **Session Management** - `app/database/sessions.py`
   - Session table with user/session tracking
   - Link conversations to sessions
   - Persist memory across refreshes

3. **Context-Aware RAG Pipeline** - `app/rag/rag_pipeline.py`
   - Inject conversation context into queries
   - Resolve references using memory
   - Context-aware retrieval

### API Changes
- Add session_id to all chat endpoints
- Return session metadata in responses
- Add `/sessions/{id}/context` endpoint

## Phase 3: Dashboard UI Refactor (PRIORITY 2)
### Layout Structure
```
┌─────────────────────────────────────────────────┐
│  Top Bar: Upload, Active Docs, Status          │
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ Sidebar  │  Main Chat Panel                     │
│          │  - Messages                          │
│ - Docs   │  - Inline tables/charts              │
│ - Chat   │  - Input                             │
│ - Finance│                                      │
│ - History│                                      │
│          │                                      │
└──────────┴──────────────────────────────────────┘
```

### Components to Create
1. `frontend/components/Dashboard/Sidebar.tsx`
2. `frontend/components/Dashboard/TopBar.tsx`
3. `frontend/components/Dashboard/ChatPanel.tsx`
4. `frontend/components/Dashboard/DocumentPanel.tsx`
5. `frontend/components/ui/SkeletonLoader.tsx`
6. `frontend/components/ui/ProgressIndicator.tsx`
7. `frontend/components/ui/Toast.tsx`

## Phase 4: Advanced Financial Agent (PRIORITY 2)
### Backend Changes
1. **Financial Agent Service** - `app/rag/financial_agent.py`
   - Separate from general chat
   - 10+ predefined questions
   - Structured analysis logic
   - Chart generation
   - State persistence

2. **Financial Analysis** - `app/rag/financial_analysis.py`
   - Revenue/profit trend analysis
   - YoY comparisons
   - Ratio calculations
   - Key insights extraction

### Questions to Implement
1. Revenue trend analysis (3-5 years)
2. Profit margin analysis
3. YoY revenue comparison
4. Operating expense breakdown
5. Cash flow analysis
6. Debt-to-equity ratio
7. ROE/ROA calculation
8. Working capital trends
9. Revenue by segment
10. Top risk factors

## Phase 5: Web Search Integration (PRIORITY 3)
### Backend Changes
1. **Web Search Service** - `app/rag/web_search.py`
   - Tavily API integration
   - Search trigger logic
   - Result formatting

2. **Hybrid RAG Pipeline** - `app/rag/hybrid_pipeline.py`
   - Document RAG + Web search
   - Source labeling
   - Context separation

### Trigger Conditions
- Insufficient document context (low retrieval scores)
- Explicit user request ("search online", "latest info")
- Time-sensitive questions
- External data needed

## Phase 6: Chart Auto-Detection (PRIORITY 2)
### Already Partially Implemented
- Enhance `app/rag/visualization_pipeline.py`
- Better intent detection for charts
- Follow-up chart context handling
- Support all chart types (line, bar, pie, stacked)

## Phase 7: Chat History Persistence (PRIORITY 2)
### Database Schema
```sql
-- Already exists: conversations table
-- Enhance with:
ALTER TABLE conversations ADD COLUMN session_id TEXT;
ALTER TABLE conversations ADD COLUMN document_ids TEXT; -- JSON array
ALTER TABLE conversations ADD COLUMN metadata TEXT; -- JSON

-- Create messages table
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id TEXT,
    role TEXT, -- user/assistant
    content TEXT,
    timestamp DATETIME,
    metadata TEXT
);
```

## Phase 8: Testing & Validation (PRIORITY 4)
### Test Cases
1. Multi-document upload and retrieval
2. Follow-up question understanding
3. Cross-document comparison
4. Finance agent stability
5. Chart generation with context
6. Web search integration
7. Session persistence
8. Large document handling (500+ pages)

## Phase 9: Production Hardening (PRIORITY 4)
### AWS Deployment
1. Environment configuration
2. Database migration (SQLite → PostgreSQL)
3. Vector store migration (ChromaDB → Pinecone/Weaviate)
4. API rate limiting
5. Error handling and logging
6. Health checks and monitoring
7. Backup and recovery

## Technical Debt to Address
1. ✅ Smart embedding batching (DONE)
2. ✅ Document isolation (DONE)
3. ✅ Fast finance agent mode (DONE)
4. ⚠️ LangChain deprecation warnings
5. ❌ Token limit handling in memory
6. ❌ Concurrent upload handling
7. ❌ Background job processing
8. ❌ Caching strategy for embeddings

## Implementation Order (Next Steps)
1. **Week 1**: Multi-document support + Conversational context
2. **Week 2**: Dashboard UI + Financial agent enhancements
3. **Week 3**: Web search + Chart improvements
4. **Week 4**: Testing + Production hardening

## Key Files to Modify
### Backend
- `app/database/documents.py` (NEW)
- `app/database/sessions.py` (NEW)
- `app/rag/memory.py` (ENHANCE)
- `app/rag/vector_store.py` (ENHANCE)
- `app/rag/financial_agent.py` (NEW)
- `app/rag/web_search.py` (NEW)
- `app/api/routes.py` (MAJOR CHANGES)

### Frontend
- `frontend/app/dashboard/page.tsx` (NEW)
- `frontend/components/Dashboard/*` (NEW)
- All existing components (REFACTOR)

## Success Metrics
- ✅ Upload 5+ documents without errors
- ✅ Ask follow-up questions with correct context
- ✅ Compare data across documents
- ✅ Finance agent works on reload
- ✅ Charts auto-generate from chat
- ✅ Web search when needed
- ✅ Session persists on refresh
- ✅ Handle 500+ page PDFs
- ✅ Deploy to AWS successfully
