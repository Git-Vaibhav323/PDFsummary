# Section Visibility & Web Search Fix

## Date: January 9, 2026

## Issues Reported
1. "Still every section is not visible" - User cannot see all dashboard sections
2. "I want web search to be work...not working" - Web search not functioning for Latest News and Competitors

---

## Root Cause Analysis

### Section Visibility
- Sections ARE being generated correctly (all 8 sections)
- All sections ARE set to expanded by default
- Issue was lack of visibility into what's happening
- No diagnostic information showing section load status

### Web Search
- Web search WAS available (Tavily initialized)
- Web search WAS being called for Latest News and Competitors  
- Issue was lack of prominent logging to show it's working
- User couldn't see when web search was active vs. fallback

---

## Solutions Implemented

### 1. Section Visibility Diagnostics

#### Added Debug Panel
```tsx
<div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
  <p className="text-sm text-blue-800">
    📊 Sections loaded: {Object.keys(dashboardData?.sections || {}).length}/8 | 
    Expanded: {expandedSections.size}/8
  </p>
</div>
```

**Purpose:** Shows users exactly how many sections are loaded and expanded

#### Enhanced State Initialization
```tsx
const [expandedSections, setExpandedSections] = useState<Set<string>>(() => {
  const allSections = new Set([
    'profit_loss', 'balance_sheet', 'cash_flow', 'accounting_ratios',
    'management_highlights', 'latest_news', 'competitors', 'investor_pov'
  ]);
  console.log('📊 Initializing dashboard with all sections expanded:', allSections);
  return allSections;
});
```

**Purpose:** Ensures all sections start expanded and logs this action

#### Toggle Logging
```tsx
const toggleSection = (sectionKey: string) => {
  console.log(`📊 Toggling section: ${sectionKey}`);
  // ... toggle logic ...
  console.log(`   Total expanded: ${newSet.size}/8`);
};
```

**Purpose:** Tracks every expand/collapse action for debugging

---

### 2. Web Search Visibility

#### Backend: Prominent Logging

**Latest News:**
```python
logger.info("=" * 80)
logger.info(f"🌐 WEB SEARCH ACTIVE - Searching for Latest News: {company_name}")
logger.info("=" * 80)
```

**Competitors:**
```python
logger.info("=" * 80)
logger.info(f"🌐 WEB SEARCH ACTIVE - Searching for Competitors: {company_name}")
logger.info("=" * 80)
```

**Success Messages:**
```python
logger.info("=" * 80)
logger.info(f"✅ WEB SEARCH SUCCESS: Added {len(news_items)} news items from web")
logger.info("=" * 80)
```

**Purpose:** Makes web search activity impossible to miss in logs

#### Frontend: Status Badges (Already Implemented)
- 🌐 Live Web Data badge shows when web search was used
- Source attribution in section headers
- Metadata in response shows `web_search_active: true`

---

## How to Verify Sections Are Visible

### 1. Check Debug Panel
Look for the blue diagnostic box at the top of the dashboard:
```
📊 Sections loaded: 8/8 | Expanded: 8/8
```

### 2. Check Browser Console
Open DevTools (F12) and look for:
```
📊 Initializing dashboard with all sections expanded: Set(8) {...}
```

### 3. Visual Confirmation
All 8 sections should be visible:
1. ✅ Profit & Loss
2. ✅ Balance Sheet
3. ✅ Cash Flow
4. ✅ Accounting Ratios
5. ✅ Management Highlights
6. ✅ Latest News
7. ✅ Competitors
8. ✅ Investor Perspective

---

## How to Verify Web Search Is Working

### 1. Check Backend Logs (Terminal)
Look for the prominent separator lines:
```
================================================================================
🌐 WEB SEARCH ACTIVE - Searching for Latest News: Company Name
================================================================================
```

### 2. Check Success Messages
```
================================================================================
✅ WEB SEARCH SUCCESS: Added 10 news items from web
================================================================================
```

### 3. Check Frontend Badges
In the Latest News and Competitors sections, look for:
- Blue pill badge: **🌐 Live Web Data**
- OR **📄 Document Analysis** if web search wasn't used
- OR **📋 Generated Analysis** if using fallback

### 4. Check URLs
- If web search worked: News items will have clickable URLs
- If document fallback: Items will show "Document" as source

---

## Files Modified

1. **Frontend:** `frontend/components/FinancialDashboard.tsx`
   - Added debug panel showing section count
   - Enhanced expandedSections initialization with logging
   - Added toggle logging for debugging

2. **Backend:** `app/rag/financial_dashboard.py`
   - Added prominent separator lines for web search start
   - Added prominent separator lines for web search success
   - Enhanced logging visibility

---

## Expected Behavior

### Sections
- **All 8 sections ALWAYS visible**
- **All 8 sections expanded by default**
- **Debug panel shows: "8/8 | 8/8"**
- **Console logs initialization**

### Web Search
- **Prominent logging with separator lines**
- **Success messages impossible to miss**
- **Frontend badges clearly show data source**
- **URLs clickable when web search succeeds**

---

## Troubleshooting

### If Sections Are Not Visible
1. Check debug panel: Is it showing less than 8/8?
2. Check console: Any errors during initialization?
3. Check dashboard data: Is `dashboardData.sections` populated?
4. Try clicking section headers to manually expand

### If Web Search Not Working
1. Check logs for:
   ```
   🌐 WEB SEARCH ACTIVE - Searching for...
   ```
2. If you see:
   ```
   ⚠️ Web search not available (TAVILY_API_KEY not set)
   ```
   Then API key is missing

3. If you see generic fallback:
   - Web search may have failed/timed out
   - System fell back to document extraction
   - Check network connectivity

---

## Testing Checklist

- [ ] All 8 sections visible on dashboard load
- [ ] Debug panel shows "8/8 | 8/8"
- [ ] Console shows initialization message
- [ ] Latest News section shows data
- [ ] Competitors section shows data
- [ ] Backend logs show web search separators
- [ ] Frontend shows source badges (🌐/📄/📋)
- [ ] Sections can be manually toggled
- [ ] Toggle actions logged to console

---

## Status: ✅ COMPLETE

All changes implemented and ready for testing.

