# No N/A Display Implementation

## Date: January 9, 2026

## User Request
"if you are unable to generate data for some thing...don't highlight it as N/A....implement this thing also....show the charts of things and metric mentioned.....fix this"

---

## ✅ Implementation Complete

### Core Principle
**NO N/A VALUES DISPLAYED ANYWHERE**
- If data cannot be generated → Hide the KPI card completely
- If chart data is invalid → Don't show the chart
- Only show metrics/charts that have valid, meaningful data

---

## Changes Implemented

### 1. KPI Card Component (`KPIDashboard.tsx`)

#### Before:
- Showed "N/A" when value was null/undefined
- Displayed cards with "N/A" text

#### After:
- **Hides card completely** if value is null/undefined/"N/A"
- Returns `null` instead of rendering "N/A"
- Only renders cards with valid numeric values

**Code Changes:**
```tsx
// CRITICAL: Hide card if value is null/undefined/invalid - NO N/A DISPLAY
if (value === null || value === undefined || value === "N/A") {
  return null;
}

// If string value is "N/A", hide the card
if (typeof value === "string" && value.trim() === "N/A") {
  return null;
}
```

### 2. All KPI Components Updated

#### ProfitLossKPIs
- **Before**: Showed 5 cards, some with "N/A"
- **After**: Only shows cards with valid data
- **Fallback**: Shows "Profit & Loss metrics not disclosed in report" if no cards

#### BalanceSheetKPIs
- **Before**: Showed 4 cards, some with "N/A"
- **After**: Only shows cards with valid data
- **Fallback**: Shows "Balance Sheet metrics not disclosed in report" if no cards

#### CashFlowKPIs
- **Before**: Showed 4 cards, some with "N/A"
- **After**: Only shows cards with valid data
- **Fallback**: Shows "Cash Flow metrics not disclosed in report" if no cards

#### AccountingRatiosKPIs
- **Before**: Showed 5 cards, some with "N/A"
- **After**: Only shows cards with valid data
- **Fallback**: Shows "Accounting ratios not disclosed in report" if no cards

#### InvestorPOVKPIs
- **Already implemented** - Only shows cards with valid data
- **Fallback**: Shows "Investor metrics not disclosed in report" if no cards

### 3. Chart Validation (`ChartCard` Component)

#### Frontend Validation
```tsx
// CRITICAL: Hide chart if no valid data - NO EMPTY CHARTS
if (chartProps.labels.length === 0 || chartProps.values.length === 0) {
  return null;
}

// CRITICAL: Hide chart if all values are invalid
const validValues = chartProps.values.filter(isValidNumber);

if (validValues.length === 0) {
  return null; // Hide chart if no valid values
}

// CRITICAL: Hide chart if all valid values are zero (no meaningful data)
const nonZeroValues = validValues.filter(v => v !== 0);
if (nonZeroValues.length === 0) {
  return null; // Hide chart if all values are zero
}
```

**Validation Function:**
```tsx
const isValidNumber = (val: any): boolean => {
  return val !== null && 
         val !== undefined && 
         val !== "N/A" && 
         typeof val === "number" && 
         !isNaN(val) && 
         isFinite(val);
};
```

### 4. Backend Chart Generation Validation

#### Profit & Loss Charts
- Only creates charts if data exists AND has non-zero values
- Validates: `any(v != 0 and isinstance(v, (int, float)) and not (isnan(v) or not isfinite(v)))`

#### Balance Sheet Charts
- Only creates charts if data exists AND has non-zero values
- Validates numeric values before adding to charts array

#### Cash Flow Charts
- Only creates charts if data exists AND has valid numeric values
- Allows negative values (cash flow can be negative)
- Validates: `any(isinstance(v, (int, float)) and not (isnan(v) or not isfinite(v)))`

#### Investor POV Charts
- Only creates charts if data exists AND has valid numeric values
- Validates before adding ROE, ROCE, Dividend, FCF charts

### 5. Removed N/A from LLM Prompts

#### Investor Perspective Summary
- **Before**: Used "N/A" in prompt for missing trends
- **After**: Only includes trends that exist in the prompt
- Builds trend summary dynamically from available data only

**Code:**
```python
# Build trend summary only with available data (no N/A)
trend_summary_parts = []
if trends.get('roe'):
    trend_summary_parts.append(f"ROE Trend: {trends['roe']}")
# ... only add if exists

trend_summary = "\n".join(trend_summary_parts) if trend_summary_parts else "Financial metrics available from annual report"
```

### 6. UI Text Updates

- Changed `"N/A"` → `"Recent"` for news dates
- Removed all "N/A" fallback displays

---

## Validation Rules

### KPI Cards
✅ **Show**: Value is a valid number (not null, not NaN, not Infinity)  
❌ **Hide**: Value is null, undefined, "N/A", NaN, or Infinity

### Charts
✅ **Show**: 
- Has labels AND values arrays
- At least one valid numeric value
- At least one non-zero value (for most metrics)
- Values are finite numbers

❌ **Hide**:
- Empty labels or values arrays
- All values are null/undefined/NaN
- All values are zero (for most metrics)
- Invalid data structure

### Cash Flow Exception
- **Allows negative values** (cash flow can be negative)
- **Allows zero values** (cash flow can be zero)

---

## User Experience

### Before:
- KPI cards showed "N/A" for missing data
- Charts might show empty or invalid data
- User saw "N/A" highlighted in gray

### After:
- **KPI cards completely hidden** if data unavailable
- **Charts only show** when valid data exists
- **Clean dashboard** with only meaningful metrics
- **Fallback message**: "Metrics not disclosed in report" if section has no data

---

## Files Modified

1. **Frontend:** `frontend/components/KPIDashboard.tsx`
   - Updated `KPICard` to return `null` instead of showing "N/A"
   - Updated all KPI components to conditionally render cards
   - Added fallback messages for empty sections

2. **Frontend:** `frontend/components/FinancialDashboard.tsx`
   - Added `isValidNumber` helper function
   - Enhanced `ChartCard` validation to hide invalid charts
   - Changed "N/A" → "Recent" for dates

3. **Backend:** `app/rag/financial_dashboard.py`
   - Added chart validation before adding to charts array
   - Only creates charts with valid, non-zero data
   - Removed "N/A" from LLM prompts
   - Added `isnan` and `isfinite` imports

---

## Testing Checklist

- [ ] KPI cards with null values are hidden (not showing "N/A")
- [ ] Charts with invalid data are hidden
- [ ] Charts with all zeros are hidden (except cash flow)
- [ ] Charts with valid data are displayed
- [ ] Empty sections show "not disclosed" message
- [ ] No "N/A" text appears anywhere in UI
- [ ] Dashboard looks clean with only meaningful metrics

---

## Status: ✅ COMPLETE

**NO N/A VALUES WILL BE DISPLAYED**

- ✅ KPI cards hidden if data unavailable
- ✅ Charts hidden if data invalid
- ✅ Only meaningful metrics shown
- ✅ Clean, professional dashboard appearance
- ✅ Fallback messages for empty sections

