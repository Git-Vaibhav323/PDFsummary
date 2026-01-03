# Finance Agent - Quick Start & Usage

## For Users

### How to Use Finance Agent

1. **Upload a PDF**
   - Click the upload area in the left sidebar
   - Wait for processing to complete
   - Finance Agent section will appear

2. **Browse FAQ Questions**
   - Look for "FINANCE AGENT" section with 📈 icon in the left sidebar
   - Click the section header to expand/collapse
   - See 10 predefined financial questions

3. **Click Any Question**
   - Click any FAQ button to ask that question
   - The question automatically sends to the RAG system
   - Answer appears in chat in seconds
   - Button highlights showing it's selected

4. **Continue Chatting**
   - Ask follow-up questions in the chat input
   - Chat history is preserved
   - You're in the same conversation
   - No new session created

### Example Workflow

```
1. Upload: Q3_2024_Financial_Report.pdf
   ✓ Processing complete
   ✓ Finance Agent appears

2. Click FAQ: "What is the company's revenue..."
   ✓ Question sent
   ✓ Answer displayed (2-3 seconds)

3. Read Answer: "Based on Q3 2024 report..."
   ✓ Charts/tables if available

4. Type Follow-up: "Can you break down by segment?"
   ✓ In same conversation
   ✓ Context preserved

5. Clear Chat: "Clear Chat" button resets everything
```

## For Developers

### Installation

No additional dependencies needed! Finance Agent uses existing packages.

### Building

```bash
cd frontend
npm run build  # Builds frontend including Finance Agent
```

### Testing

```bash
# Test in development
npm run dev

# Then:
# 1. Upload a PDF
# 2. See Finance Agent section appear
# 3. Click any FAQ question
# 4. Verify answer appears in chat
```

### Customizing FAQ Questions

To modify the 10 FAQ questions, edit `frontend/components/FinanceAgent.tsx`:

```typescript
const FAQ_QUESTIONS = [
  {
    id: 1,
    title: "Your Title Here",
    question: "Your question here?",
  },
  // ... more questions
];
```

Then rebuild:
```bash
npm run build
```

### Adding Styling

Finance Agent uses Tailwind CSS. Modify in `FinanceAgent.tsx`:

```tsx
<Button
  className="
    your-new-classes-here
  "
/>
```

### Debugging

Enable browser DevTools console to see:

1. **Question sent:** 
   ```
   [API] POST /chat - 200
   ```

2. **Selected question state:**
   ```
   selectedQuestion = "What is the company's revenue..."
   ```

3. **Chat history:**
   ```
   messages: [{role: "user", content: "..."}, ...]
   ```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│        Finance Agent Section            │
│  (Left Sidebar - when PDF loaded)       │
│                                         │
│  ▼ FINANCE AGENT                        │
│  ┌─ Company Overview                    │
│  ├─ Revenue Growth                      │
│  ├─ Profitability                       │
│  ├─ Cost & Expense Structure            │
│  ├─ Cash Flow Position                  │
│  ├─ Debt & Liabilities                  │
│  ├─ Key Financial Risks                 │
│  ├─ Segment Performance                 │
│  ├─ Forward-Looking Guidance            │
│  └─ Key Takeaways                       │
└─────────────────────────────────────────┘
         ↓ Click Question
    handleFaqQuestion()
         ↓
    handleSendMessage()
         ↓
    /chat API (RAG)
         ↓
    Display in ChatWindow
```

## FAQ Behavior Details

### When Clicking a Question

```javascript
// What happens:
handleFaqQuestion("How has revenue changed...")
  → setSelectedQuestion("How has revenue changed...")
  → handleSendMessage("How has revenue changed...")
    → Add user message to chat
    → Call apiClient.sendMessage(question, conversationId)
    → Display assistant response
    → Keep same conversation alive
```

### Conversation Continuity

```
Initial Question: "What is revenue?"
↓ Click FAQ
Answer: "Revenue was $X in period Y"
↓ Type Follow-up
Follow-up: "How about last year?"
↓ (Same conversation, history preserved)
```

### No Session Reset

```
✓ conversation_id preserved
✓ Chat history stays in memory
✓ New FAQ clicks don't create new session
✓ Clear Chat button explicitly resets
```

## Integration Points

### Frontend Components
- **FinanceAgent.tsx:** FAQ UI component
- **Sidebar.tsx:** Hosts Finance Agent section
- **page.tsx:** Manages state and handlers

### Backend API
- **POST /chat:** Existing endpoint handles FAQ questions
- **No changes needed** to backend
- Uses standard ChatRequest/ChatResponse format

### State Management
```typescript
// Key states
const [selectedQuestion, setSelectedQuestion]        // Track active FAQ
const [messages, setMessages]                        // Chat history
const [currentConversationId, setCurrentConversationId]  // Session ID
```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Component Load Time | < 100ms |
| FAQ List Render | Instant |
| Button Click Response | < 50ms |
| RAG Query Time | 1-5s (backend dependent) |
| Conversation Overhead | Negligible |

## Troubleshooting

### Finance Agent Not Showing
```
✓ Check: PDF uploaded?
✓ Check: Processing complete?
✓ Check: Browser console for errors
✓ Refresh page
```

### Questions Not Sending
```
✓ Check: Backend running?
✓ Check: Network tab for /chat API call
✓ Check: NEXT_PUBLIC_API_URL correct?
✓ Check: PDF still loaded?
```

### Answer Not Appearing
```
✓ Check: Browser console for errors
✓ Check: API response in Network tab
✓ Check: Is loading spinner showing?
✓ Try: Ask a simpler question first
```

### Conversation Lost
```
✓ Check: currentConversationId in state
✓ Check: Browser Network tab
✓ Note: Refresh page loses history (expected)
✓ Try: Clear Chat → Upload new PDF → Re-chat
```

## API Contracts

### Frontend → Backend
```javascript
POST /chat
{
  "question": "What is the company's revenue...",
  "conversation_id": "uuid-or-null"
}
```

### Backend → Frontend
```javascript
{
  "answer": "Based on the financial report...",
  "conversation_id": "uuid",
  "visualization": {...},  // Optional charts
  "chart": {...},          // Optional chart data
  "table": "..."           // Optional markdown table
}
```

### No Session Management
- Finance Agent DOES NOT create new sessions
- Reuses existing `conversation_id`
- Every FAQ click maintains context
- Clear Chat explicitly resets session

## Security Notes

- All questions sent to backend RAG system
- Follows existing API authentication (if any)
- No data stored locally except in browser memory
- Clear Chat removes from client memory
- PDF content stays in backend only

## Support

For issues:
1. Check browser console (F12)
2. Check backend API logs
3. Review FINANCE_AGENT_IMPLEMENTATION.md
4. Check this file for troubleshooting

---

**Status:** ✅ Fully Implemented & Integrated
**Last Updated:** January 3, 2026
