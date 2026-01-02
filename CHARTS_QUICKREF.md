# 📊 Charts Quick Reference

## ✅ Status: FULLY WORKING

Your RAG chatbot now generates **4 types of charts automatically**:
- ✅ **Bar Charts** - Categorical comparisons
- ✅ **Line Charts** - Time-series trends  
- ✅ **Pie Charts** - Proportional data
- ✅ **Tables** - Multi-column data

## 🚀 Quick Start (30 seconds)

```bash
# 1. Start server
python run.py

# 2. Upload PDF with financial data
curl -X POST http://localhost:8000/upload_pdf \
  -F "file=@financial_report.pdf"

# 3. Ask for a chart
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me revenue by quarter as a bar chart"}'

# 4. Get response with chart!
# Response includes: answer, chart, table (optional), chat_history
```

## 📊 Chart Examples

### Bar Chart (Categorical)
**Ask:** "Show revenue by quarter"
```json
{
  "type": "bar",
  "title": "Quarterly Revenue",
  "labels": ["Q1", "Q2", "Q3", "Q4"],
  "values": [100, 115, 132, 148],
  "xAxis": "Quarter",
  "yAxis": "Revenue (M$)"
}
```

### Line Chart (Time Series)
**Ask:** "What is the revenue trend?"
```json
{
  "type": "line",
  "title": "Revenue Trend 2024",
  "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
  "values": [80, 85, 95, 110, 118, 125],
  "xAxis": "Month",
  "yAxis": "Revenue (M$)"
}
```

### Pie Chart (Proportions)
**Ask:** "Show market share by region"
```json
{
  "type": "pie",
  "title": "Market Share by Region",
  "labels": ["North America", "Europe", "Asia", "Other"],
  "values": [45, 28, 18, 9]
}
```

### Table (Details)
**Ask:** "Create a table of financial metrics"
```json
{
  "type": "table",
  "title": "Financial Summary",
  "headers": ["Metric", "2024", "2023", "Change"],
  "rows": [
    ["Revenue", "$148M", "$120M", "+23%"],
    ["Profit", "$31M", "$24M", "+29%"],
    ["Margin", "21%", "20%", "+1%"]
  ]
}
```

## 🔍 How to Trigger Charts

### Keywords that trigger visualization:
- "Show me..." ✅
- "Create a chart..." ✅
- "Visualize..." ✅
- "Display in [chart type]..." ✅
- "What is the trend?" ✅
- "Show the breakdown..." ✅
- "Compare X across Y..." ✅

### Questions that DON'T trigger:
- "What is the revenue?" ❌
- "Explain the results" ❌
- "What happened?" ❌

### To force a chart:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Create a BAR CHART showing quarterly revenue"}'
```

## 🔧 Configuration

Located in `app/config/settings.py`:
```python
openai_model = "gpt-4.1-mini"              # Chart data extraction
embedding_model_name = "text-embedding-3-small"
temperature = 0.0                          # Deterministic
top_k_retrieval = 5                        # Context size
```

## 📈 Real Example

**PDF Contents:**
```
Q1 2024: Revenue $100M, Profit $20M
Q2 2024: Revenue $115M, Profit $23M
Q3 2024: Revenue $132M, Profit $27M
Q4 2024: Revenue $148M, Profit $31M
```

**Question:**
```
"Show me the revenue growth by quarter"
```

**Response:**
```json
{
  "answer": "Based on the financial data, revenue grew significantly from $100M in Q1 to $148M in Q4, representing 48% growth throughout 2024.",
  "chart": {
    "type": "bar",
    "title": "Quarterly Revenue Growth 2024",
    "labels": ["Q1", "Q2", "Q3", "Q4"],
    "values": [100, 115, 132, 148],
    "xAxis": "Quarter",
    "yAxis": "Revenue (M$)"
  },
  "table": null,
  "chat_history": [
    {"role": "user", "content": "Show me the revenue growth by quarter", "timestamp": "2024-01-02T11:00:00"},
    {"role": "assistant", "content": "Based on the financial data...", "timestamp": "2024-01-02T11:00:02"}
  ]
}
```

## 🧪 Test Commands

```bash
# 1. Test chart generation
python test_charts_simple.py

# 2. Test end-to-end
python test_charts_e2e.py

# 3. Run full system
python run.py

# 4. Manual test with curl
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Create a pie chart of market share"}'
```

## 🎯 Chart Selection Guide

| Data Type | Question Example | Chart Type |
|:--|:--|:--|
| Categories | "Revenue by region?" | Bar |
| Time Series | "Trend over months?" | Line |
| Proportions | "Market share breakdown?" | Pie |
| Multiple Metrics | "Show all details" | Table |

## 🚨 Troubleshooting

| Issue | Solution |
|:--|:--|
| No chart in response | Use keywords like "show", "chart", "visualize" |
| Wrong chart type | Be specific: "Create a PIE chart showing..." |
| Data not extracted | Ensure numbers are in the PDF |
| Empty labels/values | Check data format in document |

## 📚 Related Files

- **Full Guide:** [CHARTS_GUIDE.md](./CHARTS_GUIDE.md)
- **Implementation:** [ENTERPRISE_RAG_IMPLEMENTATION.md](./ENTERPRISE_RAG_IMPLEMENTATION.md)
- **Quick Start:** [QUICKSTART_ENTERPRISE.md](./QUICKSTART_ENTERPRISE.md)

## ✨ Features

✅ **Automatic Detection** - No manual configuration  
✅ **Smart Generation** - Uses gpt-4.1-mini  
✅ **Deterministic** - temperature=0 for reliable output  
✅ **Grounded** - Only uses document data  
✅ **Memory-Aware** - Remembers context in follow-ups  
✅ **Clean JSON** - Ready for frontend rendering  

## 📞 Support

1. Read [CHARTS_GUIDE.md](./CHARTS_GUIDE.md) for detailed docs
2. Run tests: `python test_charts_simple.py`
3. Check [ENTERPRISE_README.md](./ENTERPRISE_README.md) for overview
4. Review code in [app/rag/visualization_pipeline.py](./app/rag/visualization_pipeline.py)

---

**Ready to visualize?** Run: `python run.py` 🚀
