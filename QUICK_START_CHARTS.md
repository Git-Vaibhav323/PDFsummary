# Quick Start: Chart Visualization

## ✅ What's Been Implemented

Your RAG chatbot now has **full chart and graph visualization capabilities**! Here's what you can do:

### 📊 Supported Chart Types
1. **Bar Charts** - For comparisons and categories
2. **Line Charts** - For trends and time-series data
3. **Pie Charts** - For proportions and distributions
4. **Tables** - For detailed financial statements

## 🚀 How to Use

### Step 1: Start the Backend
```bash
# Make sure you're in the project root
python run.py
```

### Step 2: Start the Frontend
```bash
cd frontend
npm run dev
```

### Step 3: Upload a PDF
- Upload a PDF with financial data (revenue, expenses, balance sheets, etc.)
- Wait for processing to complete

### Step 4: Ask for Charts!

Try these example questions:

#### For Bar Charts:
- "Give me the charts for the data"
- "Show me revenue comparison"
- "Compare sales across years"
- "Display profit by quarter"

#### For Line Charts:
- "Show me revenue trends"
- "Display growth over time"
- "Show profit trends"

#### For Pie Charts:
- "Show expense distribution"
- "Display market share breakdown"
- "Show proportion of costs"

#### For Tables:
- "Show me the balance sheet"
- "Display the income statement"
- "Show financial tables"
- "Give me the P&L statement"

## 🎨 What You'll See

When you ask for charts, you'll see:
1. **Text Answer** - A brief summary of the data
2. **Interactive Chart** - A beautiful, professional chart rendered with Chart.js
3. **Hover Tooltips** - Hover over data points to see exact values
4. **Formatted Numbers** - Large numbers shown with commas (1,000,000)

### Example Output:

**User**: "Show me revenue trends"

**Response**:
```
Text: "Based on the financial data, revenue has grown from ₹100,000 
in 2021 to ₹150,000 in 2023, showing a 50% increase."

Chart: [Beautiful line chart showing upward trend]
```

## 🔧 Troubleshooting

### Charts Not Showing?

1. **Check Console**: Open browser DevTools (F12) and check for errors
2. **Verify Data**: Make sure your PDF has numerical data
3. **Use Keywords**: Include words like "chart", "graph", "show", "visualize"
4. **Check API**: Verify backend is running and responding

### Backend Not Detecting Charts?

1. **Use explicit keywords**: "chart", "graph", "visualize", "show"
2. **Mention financial terms**: "revenue", "profit", "sales", "balance sheet"
3. **Check backend logs**: Look for "Visualization detection" messages

## 📝 Technical Details

### Dependencies Added:
- `chart.js` - Chart rendering library
- `react-chartjs-2` - React wrapper for Chart.js

### Files Modified:
- ✅ `frontend/components/ChartVisualization.tsx` (NEW)
- ✅ `frontend/components/ChatMessage.tsx`
- ✅ `frontend/app/page.tsx`
- ✅ `frontend/components/ChatWindow.tsx`
- ✅ `frontend/package.json`
- ✅ `app/rag/prompts.py`
- ✅ `app/rag/graph.py`
- ✅ `app/rag/visualization_pipeline.py`

## 🎯 Next Steps

1. **Test with your PDFs**: Upload financial documents and ask for charts
2. **Try different chart types**: Experiment with bar, line, and pie charts
3. **Explore financial data**: Ask about revenue, expenses, profits, etc.
4. **Share feedback**: Let me know if you need any adjustments!

## 💡 Pro Tips

- **Be specific**: "Show me revenue by year" works better than "show data"
- **Use financial terms**: Mention "revenue", "profit", "expenses" for better detection
- **Ask for comparisons**: "Compare X vs Y" often generates good charts
- **Request tables**: For detailed data, ask for "table" or "tabular format"

## 🎉 You're All Set!

Your RAG chatbot now automatically generates beautiful, interactive charts from your PDF data. Just upload a PDF and start asking for visualizations!

For detailed technical documentation, see `CHART_VISUALIZATION_IMPLEMENTATION.md`.

