# CRITICAL CHART FIX - Strict Contract Implementation

## ✅ IMPLEMENTED: Hard Pipeline Contract

### 1. **Strict Chart Detection**
- Detects chart intent: `chart`, `charts`, `graph`, `graphs`, `visualize`, `visualization`
- **Location**: `app/rag/visualization_pipeline.py` lines 545-550

### 2. **Strict Data Validation**
- Validates chart_data has `chart_type` in `['bar', 'line', 'pie']`
- Validates `labels` and `values` arrays (min 2 items each)
- Validates length match between labels and values
- Ensures all values are numeric
- **Location**: `app/rag/visualization_pipeline.py` lines 677-730

### 3. **Table-to-Chart Conversion**
- If chart requested but table extracted, forces conversion
- Extracts account names → labels
- Extracts amounts → values (combines Debit/Credit)
- Validates numeric values
- **Location**: `app/rag/visualization_pipeline.py` lines 575-675

### 4. **Strict Error Handling**
- If chart requested but generation fails → returns error message
- If table returned when chart requested → returns error message
- If invalid data → returns error message
- **Error Message**: `"No structured numerical data available to generate a chart."`
- **Location**: `app/rag/visualization_pipeline.py` lines 677-730

### 5. **API Response Enforcement**
- Checks if chart requested
- Rejects tables when chart requested
- Returns error message if chart missing
- **Location**: `app/api/routes.py` lines 399-450

## 🔒 ABSOLUTE PROHIBITIONS ENFORCED

✅ **DO NOT return tables when chart is requested** - Enforced
✅ **DO NOT describe charts in text** - Enforced
✅ **DO NOT say "chart generated" without rendering one** - Enforced
✅ **DO NOT fallback silently** - Returns explicit error message

## 📋 API Response Format

### Success (Chart Generated):
```json
{
  "answer": "short explanation",
  "chart": {
    "type": "bar",
    "labels": [...],
    "values": [...],
    "title": "...",
    "xAxis": "...",
    "yAxis": "..."
  },
  "visualization": {
    "chart_type": "bar",
    "type": "bar",
    "labels": [...],
    "values": [...]
  }
}
```

### Failure (Chart Requested but Can't Generate):
```json
{
  "answer": "No structured numerical data available to generate a chart.",
  "chart": null,
  "visualization": null,
  "table": null
}
```

## 🎯 Success Criteria

### User asks: "Give me the charts"

**System MUST:**
- ✅ Either show a real bar/pie/line chart
- ✅ OR show the exact error message: "No structured numerical data available to generate a chart."
- ✅ NEVER show a table

## 🔍 Validation Points

1. **Detection**: Chart intent detected correctly
2. **Extraction**: Data extracted with labels and values
3. **Conversion**: Table converted to chart if needed
4. **Validation**: All values are numeric, arrays match length
5. **Generation**: Chart object created with type, labels, values
6. **Response**: Chart included in API response
7. **Frontend**: Chart rendered using Recharts

## 🚀 Testing

1. **Test Case 1**: "Give me the charts"
   - Expected: Bar chart with financial data
   - OR: Error message if no data

2. **Test Case 2**: "Show me charts"
   - Expected: Chart visualization
   - OR: Error message

3. **Test Case 3**: "Show me the table"
   - Expected: Table (not chart)

## ✅ Implementation Complete

All strict contract requirements have been implemented:
- ✅ Chart detection
- ✅ Data validation
- ✅ Table-to-chart conversion
- ✅ Error handling
- ✅ API response enforcement
- ✅ Frontend rendering support

The system now enforces the hard pipeline contract and will NEVER return a table when a chart is requested.

