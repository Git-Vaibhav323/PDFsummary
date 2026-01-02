# Financial Visualization Pipeline Architecture

## ✅ IMPLEMENTED: Domain-Aware Financial Visualization

### Core Design Principle
**Visualization is based on FINANCIAL SEMANTICS, not raw tables.**

## Architecture Components

### 1. Financial Document Type Detection (`app/rag/financial_detector.py`)

Detects financial document types using keywords and structure:

- **TRIAL_BALANCE**: Account, Debit, Credit patterns
- **PROFIT_AND_LOSS**: Revenue, Expense, Profit patterns
- **BALANCE_SHEET**: Assets, Liabilities, Equity patterns
- **CASH_FLOW**: Operating, Investing, Financing activities
- **FINANCIAL_SUMMARY**: MIS Reports, Annual Reports
- **GENERIC_FINANCIAL**: Fallback for general financial data

**Detection occurs BEFORE visualization extraction.**

### 2. Financial Data Normalization (`app/rag/financial_normalizer.py`)

Normalizes financial data from various document types into a **COMMON CHART SCHEMA**:

```json
{
  "chart_type": "bar | line | pie | stacked_bar",
  "labels": [],
  "values": [],
  "groups": optional {},
  "title": "",
  "x_axis": "",
  "y_axis": ""
}
```

### 3. Financial Visualization Rules

#### Trial Balance
- **Chart Type**: `stacked_bar`
- **Labels**: Account names
- **Groups**: Debit vs Credit
- **Values**: Absolute amounts

#### Profit & Loss
- **Chart Type**: `bar`
- **Labels**: Revenue, Expenses, Profit
- **Values**: Corresponding amounts

#### Balance Sheet
- **Chart Type**: `pie`
- **Labels**: Assets, Liabilities, Equity
- **Values**: Totals

#### Cash Flow
- **Chart Type**: `line`
- **Labels**: Operating, Investing, Financing
- **Values**: Net cash flows

#### Financial Summary / MIS
- **Chart Type**: `bar` or `pie`
- **Labels**: Major financial categories
- **Values**: Aggregated figures

### 4. Pipeline Integration

The visualization pipeline now:

1. **Detects financial document type** before extraction
2. **Extracts data** (may get table initially)
3. **Normalizes data** based on financial semantics
4. **Generates chart** with proper structure
5. **Returns error** only if normalization fails completely

### 5. Error Handling

**Strict Error Contract:**
- If chart requested but normalization fails → returns exact error message
- Error message: `"No structured financial data available to generate a chart."`
- **NO table fallback** when chart requested
- **NO text-only response** when chart requested

### 6. Frontend Support

- Added `stacked_bar` chart type support
- Supports `groups` prop for stacked bar charts
- Handles all financial chart types: bar, line, pie, stacked_bar

## Success Criteria

For **ANY** enterprise financial document:

**User**: "Show me the chart"
**User**: "Give me the charts"
**User**: "Visualize this financial data"

**System MUST:**
- ✅ Detect financial context
- ✅ Normalize data correctly based on document type
- ✅ Generate meaningful chart
- ✅ OR return exact error message
- ✅ NEVER return a table

## Implementation Files

1. `app/rag/financial_detector.py` - Document type detection
2. `app/rag/financial_normalizer.py` - Data normalization
3. `app/rag/visualization_pipeline.py` - Integrated pipeline
4. `frontend/components/SimpleChart.tsx` - Stacked bar support
5. `frontend/components/ChatMessage.tsx` - Chart rendering

## Testing

### Test Cases:

1. **Trial Balance**: "Give me charts for trial balance"
   - Expected: Stacked bar chart (Debit vs Credit)

2. **P&L Statement**: "Show me profit and loss chart"
   - Expected: Bar chart (Revenue, Expenses, Profit)

3. **Balance Sheet**: "Visualize balance sheet"
   - Expected: Pie chart (Assets, Liabilities, Equity)

4. **Cash Flow**: "Chart cash flow statement"
   - Expected: Line chart (Operating, Investing, Financing)

5. **Generic Financial**: "Show me financial charts"
   - Expected: Bar chart with financial categories

## ✅ Implementation Complete

The system now:
- ✅ Detects financial document types generically
- ✅ Normalizes data based on financial semantics
- ✅ Applies domain-specific visualization rules
- ✅ Generates charts for all enterprise financial documents
- ✅ Never falls back to tables when charts requested
- ✅ Returns clear error messages when chart generation fails

**The architecture is generic and extensible for any financial document type.**

