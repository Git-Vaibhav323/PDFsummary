# 📊 Chart Visualization Guide

## ✅ System Status

Your RAG chatbot **already has complete chart visualization implemented and tested**! All features are working correctly.

### What's Working

| Chart Type | Status | Use Case |
|:--|:--|:--|
| **Bar Charts** | ✅ Working | Categorical comparisons (revenue by quarter, sales by region, etc.) |
| **Line Charts** | ✅ Working | Time-series trends (monthly trends, yearly growth, etc.) |
| **Pie Charts** | ✅ Working | Proportional data (market share, distribution, %, etc.) |
| **Tables** | ✅ Working | Detailed tabular data (multiple columns and rows) |

## 🚀 How to Use

### 1. Start Your Server

```bash
python run.py
```

Server will be available at `http://localhost:8000`

### 2. Upload a PDF with Financial Data

```bash
curl -X POST http://localhost:8000/upload_pdf \
  -F "file=@financial_report.pdf"
```

### 3. Ask for a Chart

The system automatically detects when you want a chart. Just ask naturally:

```bash
# For bar chart
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me revenue by quarter as a bar chart"
  }'

# For line chart
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the revenue trend over time?"
  }'

# For pie chart
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show the market share breakdown by region"
  }'

# For table
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Display the financial metrics in a table"
  }'
```

### 4. API Response with Chart

```json
{
  "answer": "Based on the financial data, here are the quarterly revenues...",
  "chart": {
    "type": "bar",
    "title": "Quarterly Revenue Trend",
    "labels": ["Q1", "Q2", "Q3", "Q4"],
    "values": [100, 115, 132, 148],
    "xAxis": "Quarter",
    "yAxis": "Revenue (M$)"
  },
  "table": null,
  "chat_history": [
    {
      "role": "user",
      "content": "Show me revenue by quarter as a bar chart",
      "timestamp": "2024-01-02T11:00:00"
    },
    {
      "role": "assistant",
      "content": "Based on the financial data...",
      "timestamp": "2024-01-02T11:00:02"
    }
  ]
}
```

## 📋 Chart Type Examples

### Bar Chart
**Best for:** Comparing values across categories

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

**Trigger phrases:**
- "Show me X by [category]"
- "Compare X across [categories]"
- "Create a bar chart of X"

### Line Chart
**Best for:** Showing trends over time

```json
{
  "type": "line",
  "title": "Revenue Trend (2024)",
  "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
  "values": [80, 85, 95, 110, 118, 125],
  "xAxis": "Month",
  "yAxis": "Revenue (M$)"
}
```

**Trigger phrases:**
- "What is the trend?"
- "Show the [metric] over time"
- "How did [metric] change?"

### Pie Chart
**Best for:** Showing proportions and percentages

```json
{
  "type": "pie",
  "title": "Market Share by Region",
  "labels": ["North America", "Europe", "Asia Pacific", "Other"],
  "values": [45, 28, 18, 9]
}
```

**Trigger phrases:**
- "Show the breakdown of X"
- "What is the market share?"
- "Display the distribution of X"

### Table Chart
**Best for:** Detailed multi-column data

```json
{
  "type": "table",
  "title": "Financial Summary",
  "headers": ["Metric", "2024", "2023"],
  "rows": [
    ["Revenue", "$148M", "$120M"],
    ["Profit", "$31M", "$24M"],
    ["Margin", "21%", "20%"]
  ]
}
```

**Trigger phrases:**
- "Show me the details in a table"
- "Create a table of X"
- "Display X in table format"

## 🔍 How Chart Detection Works

The system uses a **4-step intelligent pipeline**:

### Step 1: Detection (Smart Keywords)
The system scans your question for visualization keywords:

```
Keywords: "show", "chart", "graph", "visualize", "plot", "diagram", "trend", "breakdown", "by"
```

If detected → Continue to Step 2  
If not → Just return text answer

### Step 2: Data Extraction (LLM)
Uses `gpt-4.1-mini` to extract structured data from context:

```
Input: Question + Document Context
Output: JSON with chart type, labels, values, etc.
```

### Step 3: Chart Generation
Converts extracted data into proper chart structure:
- Validates all required fields
- Formats data correctly
- Prepares for frontend rendering

### Step 4: Response Assembly
Includes chart in API response alongside answer:

```json
{
  "answer": "text response",
  "chart": {...},
  "table": null,
  "chat_history": [...]
}
```

## 🎨 Frontend Integration

Your response includes everything needed for frontend rendering:

```python
# JavaScript/React example
const response = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({ question: "Show revenue by quarter" })
});

const data = await response.json();

// Check if chart exists
if (data.chart) {
  renderChart(data.chart);  // Your chart library (Chart.js, Recharts, etc.)
}

// Always display answer
displayAnswer(data.answer);

// Show table if present
if (data.table) {
  displayTable(data.table);
}

// Show conversation history
displayChatHistory(data.chat_history);
```

## 📊 Live Testing

Run the test suite to verify everything works:

```bash
python test_charts_simple.py
```

Expected output:
```
✅ All 4 Chart Types Implemented
✅ Bar Chart Created
✅ Line Chart Created
✅ Pie Chart Created
✅ Table Created
✅ Visualization Detection (6/6 tests passed)
✅ Complete Visualization Pipeline
```

## 🔧 Configuration

Charts use these settings:

```python
# app/config/settings.py
openai_model = "gpt-4.1-mini"              # For chart extraction
embedding_model_name = "text-embedding-3-small"
temperature = 0.0                          # Deterministic output
top_k_retrieval = 5                        # Context for extraction
```

## 🚨 Troubleshooting

### Chart not appearing?

1. **Check if question triggers visualization:**
   - Use keywords like "show", "chart", "visualize", "trend", "breakdown"
   - Example: "Show me the revenue by quarter" ✅
   - Example: "What is the revenue?" ❌ (won't trigger visualization)

2. **Verify API response:**
   ```bash
   curl http://localhost:8000/chat -d '{"question": "Create a bar chart of quarterly revenue"}'
   ```
   Look for `"chart": {...}` in response

3. **Check data extraction:**
   - Document must contain numbers/data
   - Numbers must be in context retrieved
   - Format should be clear (Q1: $100M, etc.)

4. **Review logs:**
   ```bash
   # Server logs will show:
   # "Starting visualization pipeline"
   # "Generated [type] chart successfully"
   # "Visualization not needed" (if no keywords)
   ```

### Chart showing wrong type?

The system automatically detects the best chart type based on data:
- **Multiple categories** → Bar chart
- **Time-series with timestamps** → Line chart
- **Percentages/proportions** → Pie chart
- **Multiple columns** → Table

If you want a specific type, be explicit:
- "Create a **pie chart** showing market share"
- "Show a **line chart** of the trend"

## 💡 Pro Tips

1. **Upload financial PDFs** - System works best with:
   - Quarterly/annual reports
   - Financial statements
   - Revenue/profit data
   - Market data
   - Performance metrics

2. **Ask naturally** - The system understands:
   - "Show me..." → Triggers visualization
   - "What is..." → May or may not visualize
   - "Visualize..." → Always visualizes
   - "Display in chart..." → Always visualizes

3. **Memory works with charts** - Follow-up questions remember context:
   ```
   User: "Show quarterly revenue as a bar chart"
   Assistant: [Bar chart] Here's the revenue...
   
   User: "What about profit?"
   Assistant: [Bar chart] Here's the profit... (remembers quarterly context)
   ```

4. **Tables for detailed data** - Use tables when you need:
   - Multiple metrics side-by-side
   - Exact numerical values
   - Year-over-year comparison
   - Multiple columns of data

## 📈 Example Workflow

### Step 1: Upload Document
```bash
curl -X POST http://localhost:8000/upload_pdf \
  -F "file=@Q4_2024_Results.pdf"
```

### Step 2: Ask about Data
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Create a bar chart showing quarterly revenue trends"
  }'
```

### Step 3: Receive Response with Chart
```json
{
  "answer": "Based on the Q4 2024 results, here are the quarterly revenues...",
  "chart": {
    "type": "bar",
    "title": "Quarterly Revenue 2024",
    "labels": ["Q1", "Q2", "Q3", "Q4"],
    "values": [100, 115, 132, 148]
  },
  "chat_history": [...]
}
```

### Step 4: Follow-up Question
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What about profit margins?"
  }'
```

### Step 5: Get Follow-up Chart (Memory-Aware)
```json
{
  "answer": "The profit margins by quarter were...",
  "chart": {
    "type": "line",
    "title": "Profit Margin Trends",
    "labels": ["Q1", "Q2", "Q3", "Q4"],
    "values": [20, 20, 21, 21]
  },
  "chat_history": [...]
}
```

## ✅ Implementation Status

| Component | Status | Details |
|:--|:--|:--|
| Bar Chart | ✅ Complete | Categorical data, fully working |
| Line Chart | ✅ Complete | Time-series, fully working |
| Pie Chart | ✅ Complete | Proportions, fully working |
| Tables | ✅ Complete | Multi-column, fully working |
| Detection | ✅ Complete | Smart keyword + LLM detection |
| Extraction | ✅ Complete | Uses gpt-4.1-mini |
| Generation | ✅ Complete | Creates proper JSON structures |
| API Integration | ✅ Complete | In /chat endpoint |
| Frontend Support | ✅ Ready | Send charts to frontend |

## 📚 Reference

**Main Files:**
- [app/rag/visualization_pipeline.py](./app/rag/visualization_pipeline.py) - Core visualization engine
- [app/rag/response_handler.py](./app/rag/response_handler.py) - Response formatting
- [app/api/routes.py](./app/api/routes.py) - API endpoints

**Tests:**
- [test_charts_simple.py](./test_charts_simple.py) - Verification test suite

**Documentation:**
- [ENTERPRISE_RAG_IMPLEMENTATION.md](./ENTERPRISE_RAG_IMPLEMENTATION.md) - Technical details
- [QUICKSTART_ENTERPRISE.md](./QUICKSTART_ENTERPRISE.md) - Quick start guide

---

**Ready to visualize data?** Start with:
```bash
python run.py
```

Then upload a PDF and ask: **"Show me the data as charts!"** 📊
