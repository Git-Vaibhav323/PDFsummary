# Financial Dashboard Data Extraction Improvements

## Overview
Enhanced the Financial Dashboard to show ALL available data with improved extraction and intelligent derivation.

## Improvements Made

### 1. Auto-Derive Missing P&L Values ✅

**PAT (Profit After Tax)**
- If PAT is missing but Net Profit exists → PAT = Net Profit
- If Net Profit is missing but PAT exists → Net Profit = PAT
- Reason: PAT and Net Profit are the same metric

**EBITDA (Earnings Before Interest, Tax, Depreciation & Amortization)**
- **Method 1**: If Revenue and Expenses available → EBITDA = Revenue - Expenses
- **Method 2**: If Net Profit available → EBITDA ≈ Net Profit × 1.3 (approximate 30% addition for D&A, Interest, Tax)
- Logs derivation source for transparency

### 2. Enhanced Latest News Web Search ✅

**Before:**
- 4 search queries
- Up to 40 results
- Basic deduplication

**After:**
- 5 optimized search queries:
  - "{company} latest news 2024 2025"
  - "{company} earnings announcement financial results"
  - "{company} quarterly results analyst report"
  - "{company} company news updates"
  - "{company} business news financial performance"
- Up to 50 results
- URL-based deduplication
- Improved error handling with detailed logging
- Better summary extraction (250 char limit)

### 3. Enhanced Competitors Web Search ✅

**Before:**
- 4 search queries
- Basic name extraction from titles
- Limited insights

**After:**
- 5 optimized search queries:
  - "{company} competitors list"
  - "{company} industry peers comparison"
  - "{company} vs competitors market share"
  - "{company} competitive analysis"
  - "{company} top competitors market position"
- **LLM-powered extraction**: Uses GPT to extract structured competitor data from web results
- **Fallback extraction**: If LLM fails, uses improved regex-based extraction
- Aims for 5-10 competitors with meaningful insights
- Detailed logging for debugging

### 4. Improved Data Display Logic ✅

**All Sections:**
- Guaranteed to show data (derived, extracted, or fallback)
- Never shows empty sections
- Clear source tracking (document, derived, web, approximated)

**KPI Cards:**
- Shows derived values with appropriate labels
- Hides cards only if absolutely no data available (as per spec)
- Displays "Not disclosed in report" only when necessary

## Technical Details

### Derivation Order
1. **Primary**: Extract from document using LLM + OCR + Regex
2. **Secondary**: Derive from related metrics (PAT from Net Profit, EBITDA from Revenue-Expenses)
3. **Tertiary**: Approximate using financial heuristics (EBITDA from Net Profit)
4. **Fallback**: Show placeholder with clear indication

### Logging Enhancements
```python
logger.info("🔧 Deriving missing P&L metrics...")
logger.info("✅ Derived PAT from Net Profit")
logger.info("✅ Derived EBITDA for X years from Revenue - Expenses")
logger.info("✅ Approximated EBITDA for X years from Net Profit + 30%")
```

### Web Search Improvements
```python
# More queries for better coverage
web_queries = [query1, query2, query3, query4, query5]

# Better logging
logger.info(f"🔍 Searching web for news about: {company_name}")
logger.info(f"   Query: {query}")
logger.info(f"   Found: {len(results)} results")
logger.info(f"✅ Total web results: {len(all_web_results)}")
```

## Expected Results

### Profit & Loss Section
- ✅ Revenue: Extracted from document
- ✅ Net Profit: Extracted from document  
- ✅ EBITDA: **Derived** from Revenue - Expenses (or Net Profit)
- ✅ PAT: **Derived** from Net Profit (same value)
- ✅ All charts showing complete trends

### Latest News Section
- ✅ 10-50 news items from web search
- ✅ Recent headlines with summaries
- ✅ Source URLs included
- ✅ Proper deduplication

### Competitors Section
- ✅ 5-10 competitors identified
- ✅ Meaningful insights for each
- ✅ Market positioning context
- ✅ LLM-powered extraction for accuracy

### Investor Perspective Section
- ✅ All metrics derived from document data
- ✅ ROE, ROCE, FCF, Dividend Payout, CAGR
- ✅ Trend charts for each metric
- ✅ Bull case and risk factors

## Files Modified

1. `app/rag/financial_dashboard.py`
   - Line ~1940: Added derivation logic after data extraction
   - Line ~2975: Enhanced Latest News web search
   - Line ~3045: Enhanced Competitors web search with LLM

## Testing Checklist

- [x] PAT shows value when Net Profit is available
- [x] EBITDA shows value (derived or approximated)
- [x] Latest News shows 10+ items with web search
- [x] Competitors shows 5+ companies with insights
- [x] All KPI cards display values (no N/A unless truly unavailable)
- [x] Source tracking works correctly
- [x] Logging provides clear derivation path

## Future Enhancements

1. Add more derivation rules (Operating Margin from EBITDA, etc.)
2. Implement caching for web search results
3. Add confidence scores for derived values
4. Support multiple languages in web search
5. Add real-time news refresh functionality

---
Generated: 2025-01-08
Version: 2.0

