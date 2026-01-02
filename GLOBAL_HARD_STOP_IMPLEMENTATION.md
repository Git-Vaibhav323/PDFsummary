# Global Hard Stop for Chart Requests - Complete Implementation

## ✅ IMPLEMENTED: Multi-Layer Defense System

This document describes the comprehensive multi-layer defense system that prevents tables from being returned when charts are requested.

---

## 🔒 Defense Layers

| Layer | Location | Purpose |
|-------|----------|---------|
| **Layer 1** | `routes.py:296` | Global `is_chart_request` detection at TOP |
| **Layer 2** | `routes.py:330` | Table-to-chart conversion |
| **Layer 3** | `routes.py:450` | Early block for `response.visualization` |
| **Layer 4** | `routes.py:480` | Block table from `chart_data` |
| **Layer 5** | `routes.py:540` | Final API Response Guard |
| **Layer 6** | `routes.py:668` | Final Sanitization |
| **Layer 7** | `graph.py:1076` | Graph Finalize Early Block |
| **Layer 8** | `graph.py:1910` | Final Graph Guard |

---

## 📋 Layer Details

### Layer 1: Global Chart Intent Detection (routes.py)
```python
# Line 296 - FIRST check in chat endpoint
is_chart_request = any(kw in question_lower for kw in [
    'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization',
    'visualise', 'show chart', 'display chart', 'give me chart',
    'generate chart', 'create chart', 'plot', 'plotting', 'show charts'
])
```

### Layer 2: Table-to-Chart Conversion (routes.py)
```python
# Line 330 - If chart requested and we extracted table, CONVERT to chart
if is_chart_request:
    # Extract account names and values
    # Convert to bar chart with labels/values
    response["chart"] = {
        "type": "bar",
        "labels": labels,
        "values": values,
        ...
    }
```

### Layer 3: Early Block for response.visualization (routes.py)
```python
# Line 450 - Block if visualization is table when chart requested
if is_chart_request and viz_chart_type == "table":
    return ChatResponse(
        answer="No structured numerical data available to generate a chart.",
        chart=None,
        visualization=None,
        table=None
    )
```

### Layer 4: Block table from chart_data (routes.py)
```python
# Line 480 - Block if chart_data is table when chart requested
if chart_data.get("type") == "table" and is_chart_request:
    return ChatResponse(
        answer="No structured numerical data available to generate a chart.",
        ...
    )
```

### Layer 5: Final API Response Guard (routes.py)
```python
# Line 540 - Comprehensive table detection
if is_chart_request:
    is_table_visualization = False
    
    # Check 1: chart_type = "table"
    # Check 2: type = "table"
    # Check 3: markdown tables
    # Check 4: headers/rows without labels/values
    
    if is_table_visualization:
        return ChatResponse(
            answer="No structured numerical data available to generate a chart.",
            ...
        )
```

### Layer 6: Final Sanitization (routes.py)
```python
# Line 668 - Last check before return
if is_chart_request:
    if final_visualization.get("chart_type") == "table":
        return ChatResponse(
            answer="No structured numerical data available to generate a chart.",
            ...
        )
```

### Layer 7: Graph Finalize Early Block (graph.py)
```python
# Line 1076 - Block in RAG pipeline
if is_chart_request and visualization:
    if viz_chart_type == "table":
        visualization = None  # Will trigger error response
```

### Layer 8: Final Graph Guard (graph.py)
```python
# Line 1910 - Last check in graph pipeline
if is_chart_request and visualization:
    if viz_chart_type == "table" or has_table_structure:
        visualization = None
        answer = "No structured numerical data available to generate a chart."
```

---

## 🎯 Chart Intent Keywords Detected

The system detects chart intent for ANY of these:
- `chart`, `charts`
- `graph`, `graphs`
- `visualize`, `visualization`, `visualizations`
- `visualise` (British spelling)
- `show chart`, `display chart`
- `give me chart`, `give me charts`
- `generate chart`, `create chart`
- `plot`, `plotting`
- `show charts`

---

## 🚫 Blocked Outputs When Chart Requested

| Type | Description | Blocked? |
|------|-------------|----------|
| `chart_type = "table"` | Explicit table type | ✅ BLOCKED |
| `type = "table"` | Alternative table type field | ✅ BLOCKED |
| `markdown` with `\|` | Markdown table syntax | ✅ BLOCKED |
| `headers` + `rows` without `labels` | Hidden table structure | ✅ BLOCKED |

---

## ✅ Allowed Outputs When Chart Requested

### 1️⃣ Valid Chart Object
```json
{
  "answer": "...",
  "chart": {
    "type": "bar | pie | line | stacked_bar",
    "labels": ["Label1", "Label2", ...],
    "values": [100, 200, ...],
    "title": "...",
    "xAxis": "...",
    "yAxis": "..."
  },
  "visualization": {
    "chart_type": "bar | pie | line | stacked_bar",
    "labels": [...],
    "values": [...]
  },
  "table": null
}
```

### 2️⃣ Error Response (No Data)
```json
{
  "answer": "No structured numerical data available to generate a chart.",
  "chart": null,
  "visualization": null,
  "table": null
}
```

---

## 🔄 Defense Flow

```
User: "Give me the charts"
        │
        ▼
┌─────────────────────────────────────┐
│ Layer 1: Global Intent Detection    │
│ is_chart_request = TRUE             │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ Layer 2: Table-to-Chart Conversion  │
│ If extracted table → Convert to bar │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ Layers 3-4: Early Blocks            │
│ Block tables from viz/chart fields  │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ Layer 5: Final API Guard            │
│ Multi-check for ANY table form      │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ Layer 6: Final Sanitization         │
│ Last check before HTTP response     │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ RESPONSE                            │
│ ✅ Valid chart OR                   │
│ ✅ Error message                    │
│ ❌ NEVER a table                    │
└─────────────────────────────────────┘
```

---

## 🏢 Enterprise Scope

This system applies to ALL financial documents:
- ✅ Trial Balance
- ✅ Balance Sheet
- ✅ Profit & Loss (P&L)
- ✅ Cash Flow Statements
- ✅ Bank Statements
- ✅ GST / Tax Reports
- ✅ Audit Reports
- ✅ Any tabular financial PDF

---

## 🧪 Test Cases

| User Input | Expected Result |
|------------|-----------------|
| "Give me the charts" | Chart or error message |
| "Show me charts" | Chart or error message |
| "I want visualization" | Chart or error message |
| "Display graph" | Chart or error message |
| "Plot this data" | Chart or error message |

**NEVER:**
- ❌ Table output
- ❌ Markdown table
- ❌ headers/rows structure
- ❌ `chart_type = "table"`

---

## ✅ Implementation Complete

All 8 defense layers are active and working. The system guarantees:

1. **When user asks for chart** → Only chart or error
2. **No table can pass through** → Blocked at 8 layers
3. **Consistent error message** → "No structured numerical data available to generate a chart."
4. **Enterprise-grade** → Works for all financial documents

**Date:** January 3, 2026
**Status:** ✅ COMPLETE

