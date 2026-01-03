# Finance Agent - Code Changes Reference

## Summary of Changes

| File | Type | Lines | Purpose |
|------|------|-------|---------|
| `frontend/components/FinanceAgent.tsx` | NEW | 132 | Finance Agent UI component |
| `frontend/components/Sidebar.tsx` | UPDATED | +8 | Integration into sidebar |
| `frontend/app/page.tsx` | UPDATED | +15 | State and handlers |

---

## File 1: FinanceAgent.tsx (NEW - 132 lines)

**Location:** `frontend/components/FinanceAgent.tsx`

**Purpose:** Standalone component for Finance Agent UI

**Key Elements:**
```typescript
// Props interface
interface FinanceAgentProps {
  onQuestionClick: (question: string) => void;
  disabled?: boolean;
  selectedQuestion?: string;
}

// 10 hardcoded FAQ questions
const FAQ_QUESTIONS = [
  {
    id: 1,
    title: "Company Overview",
    question: "What is the overall financial performance...",
  },
  // ... 9 more questions
];

// Component renders:
// - Expandable header with TrendingUp icon
// - List of clickable question buttons
// - Selected state highlighting
// - Disabled message when no PDF
// - Max-height scrollable container
```

**Imports Required:**
```typescript
"use client";
import { useState } from "react";
import { ChevronDown, ChevronUp, TrendingUp } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
```

---

## File 2: Sidebar.tsx (UPDATED - +8 lines)

**Location:** `frontend/components/Sidebar.tsx`

### Change 1: Import FinanceAgent
**Line 5:** Add import
```typescript
import FinanceAgent from "./FinanceAgent";
```

### Change 2: Update Interface Props
**Lines 20-21:** Add new props
```typescript
interface SidebarProps {
  // ... existing props ...
  onFaqQuestion?: (question: string) => void;      // NEW
  selectedQuestion?: string;                        // NEW
  // ... rest of props ...
}
```

### Change 3: Destructure New Props
**Lines 36-37:** Add to destructuring
```typescript
export default function Sidebar({
  // ... existing destructuring ...
  onFaqQuestion,                                    // NEW
  selectedQuestion,                                 // NEW
  // ... rest of destructuring ...
}: SidebarProps) {
```

### Change 4: Render Finance Agent
**After Status section (~line 120):** Add this block
```typescript
{/* Finance Agent Section */}
{isPDFLoaded && onFaqQuestion && (
  <FinanceAgent
    onQuestionClick={onFaqQuestion}
    disabled={!isPDFLoaded}
    selectedQuestion={selectedQuestion}
  />
)}
```

---

## File 3: page.tsx (UPDATED - +15 lines)

**Location:** `frontend/app/page.tsx`

### Change 1: Add State for Selected Question
**Line 40:** Add state variable
```typescript
export default function Home() {
  // ... existing states ...
  const [selectedQuestion, setSelectedQuestion] = useState<string | undefined>();
  // ... rest of states ...
}
```

### Change 2: Create FAQ Handler
**After handleUploadError (~line 56):** Add new handler
```typescript
const handleFaqQuestion = useCallback(
  (question: string) => {
    setSelectedQuestion(question);
    handleSendMessage(question);
  },
  [handleSendMessage]
);
```

### Change 3: Reset Selected on Clear
**In handleClearChat (~line 211):** Add state reset
```typescript
const handleClearChat = useCallback(() => {
  setMessages([]);
  setError(null);
  setCurrentConversationId(undefined);
  setSelectedQuestion(undefined);  // NEW
}, []);
```

### Change 4: Pass Props to Sidebar
**In Sidebar component call (~line 305):** Add new props
```typescript
<Sidebar
  isPDFLoaded={isPDFLoaded}
  isProcessing={isProcessing}
  onUploadSuccess={handleUploadSuccess}
  onUploadError={handleUploadError}
  onClearChat={handleClearChat}
  onRemoveFile={handleRemoveFile}
  onFaqQuestion={handleFaqQuestion}                 // NEW
  messageCount={messages.length}
  uploadedFileName={uploadedFileName}
  uploadedFileSize={uploadedFileSize}
  selectedQuestion={selectedQuestion}               // NEW
>
  {/* ... children ... */}
</Sidebar>
```

---

## Data Flow Diagram

```
FinanceAgent.tsx
├─ Props: onQuestionClick
├─ State: isExpanded
├─ Renders: 10 FAQ buttons
└─ Event: Button.onClick
   └─ Calls: onQuestionClick(question)
      │
      └─> Sidebar.tsx
          ├─ Props: onFaqQuestion (from page.tsx)
          ├─ Renders: FinanceAgent with onFaqQuestion
          └─ Passes: onQuestionClick={onFaqQuestion}
             │
             └─> page.tsx
                 ├─ handleFaqQuestion(question)
                 ├─ setSelectedQuestion(question)
                 └─ handleSendMessage(question)
                    │
                    └─> Existing Chat Flow
                        ├─ Add user message
                        ├─ Call /chat API
                        ├─ Get response
                        └─ Add assistant message
                           │
                           └─> ChatWindow displays answer
```

---

## Type Definitions

### FinanceAgentProps
```typescript
interface FinanceAgentProps {
  onQuestionClick: (question: string) => void;
  disabled?: boolean;
  selectedQuestion?: string;
}
```

### FAQ Question Shape
```typescript
interface FAQQuestion {
  id: number;
  title: string;
  question: string;
}
```

### No Additional API Types Needed
- Reuses existing `ChatRequest` and `ChatResponse` types
- `ChatRequest` already supports questions
- `ChatResponse` already returns answers

---

## Import Dependencies

### FinanceAgent.tsx
```typescript
"use client"                          // Next.js client component
import { useState } from "react"      // React hook
import { ChevronDown, ChevronUp, TrendingUp } from "lucide-react"  // Icons
import { Button } from "./ui/button"  // Existing UI component
import { Card, CardContent } from "./ui/card"  // Existing UI component
```

### Sidebar.tsx
```typescript
import FinanceAgent from "./FinanceAgent"  // NEW import
```

### page.tsx
```typescript
// No new imports needed
// Uses existing imports and hooks
```

---

## Component Integration Points

### 1. Parent: page.tsx
- Manages `selectedQuestion` state
- Defines `handleFaqQuestion` callback
- Passes both to `Sidebar`

### 2. Intermediary: Sidebar.tsx
- Receives `onFaqQuestion` prop
- Receives `selectedQuestion` prop
- Passes them to `FinanceAgent`
- Conditional render (only when `isPDFLoaded`)

### 3. Child: FinanceAgent.tsx
- Receives `onQuestionClick` prop (actually `onFaqQuestion`)
- Receives `selectedQuestion` prop for highlighting
- Calls `onQuestionClick` when button clicked
- Manages local `isExpanded` state

---

## State Flow

```
page.tsx
├─ selectedQuestion: string | undefined
│  ├─ Set by: handleFaqQuestion
│  ├─ Reset by: handleClearChat
│  └─ Passed to: Sidebar → FinanceAgent
│
└─ handleFaqQuestion callback
   ├─ Takes: question (string)
   ├─ Does: 
   │  ├─ setSelectedQuestion(question)
   │  └─ handleSendMessage(question)
   └─ Passed to: Sidebar → FinanceAgent as onQuestionClick
```

---

## Styling Classes Used

### FinanceAgent.tsx
```typescript
// Header button
"flex w-full items-center gap-2 px-2 hover:opacity-75 transition-opacity"

// FAQ question buttons
"w-full justify-start text-left h-auto whitespace-normal py-2 px-3"
"border-border/50 bg-card/50 hover:bg-card hover:border-border"
"transition-all duration-200"

// Selected state
"border-primary bg-primary/5"

// Disabled message
"text-xs text-muted-foreground px-2 py-2 rounded-md bg-card/30"
```

---

## Testing Points

### Unit Testing
```typescript
// Test FinanceAgent renders all 10 questions
expect(screen.getAllByRole('button')).toHaveLength(10);

// Test selected state applies correct class
expect(button).toHaveClass('border-primary');

// Test click calls callback
fireEvent.click(button);
expect(onQuestionClick).toHaveBeenCalledWith(question);
```

### Integration Testing
```typescript
// Test FAQ click sends to backend
// 1. Click FAQ button
// 2. Verify user message in chat
// 3. Verify /chat API called
// 4. Verify assistant response shown
// 5. Verify conversation_id preserved
```

### E2E Testing
```typescript
// Full user flow
// 1. Upload PDF
// 2. Finance Agent appears
// 3. Click FAQ
// 4. Answer appears
// 5. Ask follow-up
// 6. Context maintained
```

---

## Environment Configuration

**No environment changes needed**
- Reuses existing `NEXT_PUBLIC_API_URL`
- Reuses existing `apiClient`
- Reuses existing `/chat` endpoint

---

## Backward Compatibility

✅ **Fully backward compatible**
- No breaking changes to existing components
- Optional props on Sidebar (onFaqQuestion, selectedQuestion)
- New component doesn't affect other features
- Can be disabled/removed without impacting system

---

## Performance Considerations

### Bundle Impact
- FinanceAgent.tsx: ~2KB minified
- No new dependencies
- Reuses existing imports

### Runtime Impact
- Component: ~100KB memory
- State management: Minimal overhead
- Re-renders: Only when selectedQuestion changes
- No infinite loops or waterfalls

### Optimization Opportunities
- FAQ list could be memoized (useMemo)
- Button list could use virtualization if > 100 questions
- useCallback already used for click handler

---

## Documentation References

For more details, see:
1. **FINANCE_AGENT_IMPLEMENTATION.md** - Technical architecture
2. **FINANCE_AGENT_QUICKSTART.md** - Usage and troubleshooting
3. **FINANCE_AGENT_VALIDATION.md** - Requirements checklist
4. **FINANCE_AGENT_SUMMARY.md** - Executive summary

---

## Quick Copy-Paste Guide

### Add to Sidebar.tsx
```typescript
// Line 5
import FinanceAgent from "./FinanceAgent";

// In SidebarProps interface, add:
onFaqQuestion?: (question: string) => void;
selectedQuestion?: string;

// In component destructuring, add:
onFaqQuestion,
selectedQuestion,

// Before {children}, add:
{/* Finance Agent Section */}
{isPDFLoaded && onFaqQuestion && (
  <FinanceAgent
    onQuestionClick={onFaqQuestion}
    disabled={!isPDFLoaded}
    selectedQuestion={selectedQuestion}
  />
)}
```

### Add to page.tsx
```typescript
// Add state
const [selectedQuestion, setSelectedQuestion] = useState<string | undefined>();

// Add handler (after handleUploadError)
const handleFaqQuestion = useCallback(
  (question: string) => {
    setSelectedQuestion(question);
    handleSendMessage(question);
  },
  [handleSendMessage]
);

// Update handleClearChat
const handleClearChat = useCallback(() => {
  setMessages([]);
  setError(null);
  setCurrentConversationId(undefined);
  setSelectedQuestion(undefined);
}, []);

// Update Sidebar component
<Sidebar
  // ... existing props ...
  onFaqQuestion={handleFaqQuestion}
  selectedQuestion={selectedQuestion}
>
```

---

**All changes are minimal, focused, and non-breaking**
**No refactoring of existing code required**
**Ready for immediate integration and testing**
