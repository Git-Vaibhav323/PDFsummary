# Hard Block Implementation - Table Output Prevention

## ✅ IMPLEMENTED: Hard Blocks on Table Output

### 1. **ChartGenerator Hard Block**
- **Location**: `app/rag/visualization_pipeline.py` line 441-463
- **Implementation**: `generate_chart()` now accepts `is_chart_request` parameter
- **Behavior**: If chart requested and chart_type is "table", returns `None` (triggers error upstream)
- **Result**: ChartGenerator CANNOT return table when chart requested

### 2. **Universal Table-to-Chart Converter**
- **Location**: `app/rag/visualization_pipeline.py` line 954-1090
- **Implementation**: `_universal_table_to_chart_converter()` method
- **Rules Applied**:
  - **Rule a**: Debit & Credit columns → bar chart with max(debit, credit)
  - **Rule b**: Single Amount column → bar chart
  - **Rule c**: Assets/Liabilities/Equity → pie chart
- **Result**: Always attempts conversion before failing

### 3. **Pipeline-Level Hard Block**
- **Location**: `app/rag/visualization_pipeline.py` line 609-640
- **Implementation**: Forces normalization when chart requested and table detected
- **Behavior**: 
  1. Tries financial normalization
  2. If fails, tries universal converter
  3. If both fail, returns error (NOT table)
- **Result**: Table data is ALWAYS converted or error returned

### 4. **Validation Hard Block**
- **Location**: `app/rag/visualization_pipeline.py` line 726-760
- **Implementation**: Validates chart_type BEFORE generation
- **Behavior**: 
  - Rejects if chart_type is "table"
  - Only allows: bar, line, pie, stacked_bar
- **Result**: Invalid chart types blocked before generation

### 5. **API-Level Hard Block**
- **Location**: `app/api/routes.py` line 416-431, 458-470
- **Implementation**: Multiple checks for table when chart requested
- **Behavior**:
  - Checks if chart_data is table → returns error
  - Checks if visualization is table → returns error
  - Final validation before response
- **Result**: API NEVER returns table when chart requested

### 6. **Response Handler Filter**
- **Location**: `app/rag/response_handler.py` line 186-197
- **Implementation**: Filters tables (handled at API level with question context)
- **Result**: Additional layer of protection

## 🔒 Hard Blocks Summary

| Location | Block Type | Action |
|----------|-----------|--------|
| ChartGenerator | Method-level | Returns None if table when chart requested |
| Pipeline | Conversion | Forces normalization → universal converter → error |
| Validation | Pre-generation | Rejects table chart_type |
| API Routes | Response-level | Multiple checks, returns error if table detected |
| Response Handler | Filter-level | Additional filtering |

## 📋 Response Contract Enforcement

### Allowed (Chart Requested):
```json
{
  "answer": "...",
  "chart": {
    "type": "bar | line | pie | stacked_bar",
    "labels": [...],
    "values": [...]
  }
}
```

### Forbidden (Chart Requested):
- ❌ `chart_type = "table"`
- ❌ `type = "table"`
- ❌ `markdown` tables
- ❌ `headers` / `rows` arrays

### Error Response (Chart Requested, Conversion Failed):
```json
{
  "answer": "No structured financial data available to generate a chart.",
  "chart": null,
  "visualization": null,
  "table": null
}
```

## ✅ Success Criteria Met

**User**: "Show me the chart"  
**User**: "Give me the charts"

**System MUST:**
- ✅ Render bar/pie/line/stacked_bar chart
- ✅ OR return exact error message
- ✅ NEVER render table
- ✅ NEVER return chart_type = "table"

## 🎯 Implementation Complete

All hard blocks are in place:
- ✅ ChartGenerator blocks table output
- ✅ Universal converter attempts conversion
- ✅ Pipeline forces conversion
- ✅ Validation rejects tables
- ✅ API blocks tables
- ✅ Response handler filters tables

**The system now STRICTLY ENFORCES the contract: NO TABLES when charts requested!**

