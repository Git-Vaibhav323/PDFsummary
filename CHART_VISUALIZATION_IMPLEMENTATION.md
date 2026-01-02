# Chart Visualization Implementation

## Overview
This document describes the complete implementation of chart and graph visualization for the RAG chatbot, enabling it to automatically generate and display visual representations of financial and numerical data from uploaded PDFs.

## Features Implemented

### 1. Backend Enhancements

#### Visualization Detection
- **Enhanced prompts** to detect financial data requests (revenue, profit, sales, cost, budget, balance sheets, income statements, etc.)
- **Pattern matching** for financial keywords in both questions and context
- **Automatic detection** of numerical data requiring visualization

#### Data Extraction
- **Structured data extraction** from PDFs for charts (labels, values, titles)
- **Financial table extraction** (Balance Sheet, Income Statement, Cash Flow, P&L)
- **Support for multiple chart types**: bar, line, pie, and table

#### Files Modified (Backend):
- `app/rag/prompts.py` - Enhanced prompts for financial data detection
- `app/rag/graph.py` - Improved visualization detection logic
- `app/rag/visualization_pipeline.py` - Added financial keywords to detection

### 2. Frontend Implementation

#### Chart.js Integration
- **Installed Chart.js** and react-chartjs-2 for professional chart rendering
- **Created ChartVisualization component** with support for:
  - Bar charts (comparisons, categories)
  - Line charts (time-series, trends)
  - Pie charts (proportions, distributions)

#### Component Architecture
```
frontend/
├── components/
│   ├── ChartVisualization.tsx (NEW) - Renders bar/line/pie charts
│   ├── ChatMessage.tsx (UPDATED) - Displays charts and tables
│   ├── ChatWindow.tsx (UPDATED) - Message interface updated
│   └── ...
├── app/
│   └── page.tsx (UPDATED) - Chart data mapping
└── package.json (UPDATED) - Added chart.js dependencies
```

#### Files Modified/Created (Frontend):
- **NEW**: `frontend/components/ChartVisualization.tsx` - Chart rendering component
- **UPDATED**: `frontend/components/ChatMessage.tsx` - Added chart rendering logic
- **UPDATED**: `frontend/app/page.tsx` - Improved data mapping for charts
- **UPDATED**: `frontend/components/ChatWindow.tsx` - Interface updates
- **UPDATED**: `frontend/package.json` - Added chart.js and react-chartjs-2

### 3. Chart Features

#### Visual Design
- **Dark theme optimized** with proper colors for dark backgrounds
- **Responsive design** that adapts to container width
- **Professional styling** with subtle grids and borders
- **Formatted tooltips** with comma-separated numbers
- **Color-coded data** with distinct colors for each data point (pie charts)

#### Chart Types

**Bar Charts**:
- Used for: Comparisons, categories, year-wise data
- Features: Value labels, formatted axes, hover tooltips
- Example: Revenue comparison across years

**Line Charts**:
- Used for: Time-series data, trends over time
- Features: Smooth curves, point markers, trend visualization
- Example: Profit trends over quarters

**Pie Charts**:
- Used for: Proportions, percentages, distributions
- Features: Percentage labels, color-coded segments, legend
- Example: Expense distribution by category

**Tables**:
- Used for: Detailed financial statements, multi-column data
- Features: Structured rows/columns, right-aligned numbers, formatted cells
- Example: Balance Sheet, Income Statement

## How It Works

### User Flow
1. **User uploads a PDF** with financial data
2. **User asks for charts**: "Give me the charts for the data" or "Show me revenue trends"
3. **Backend detects** the visualization need
4. **Backend extracts** structured data (labels, values, chart type)
5. **Backend returns** chart data in API response
6. **Frontend receives** chart data and renders it using Chart.js
7. **User sees** beautiful, interactive charts

### Data Flow
```
PDF Upload → Text Extraction → Chunking → Vector Store
                                              ↓
User Question → RAG Retrieval → Context → Visualization Detection
                                              ↓
                                    Data Extraction (LLM)
                                              ↓
                                    Chart Data (labels, values, type)
                                              ↓
                                    API Response → Frontend
                                              ↓
                                    Chart.js Rendering → Display
```

### API Response Format
```json
{
  "answer": "Based on the financial data...",
  "chart": {
    "type": "bar",
    "title": "Revenue by Year",
    "labels": ["2021", "2022", "2023"],
    "values": [100000, 120000, 150000],
    "xAxis": "Year",
    "yAxis": "Revenue (₹)"
  },
  "table": null,
  "chat_history": [...]
}
```

## Usage Examples

### Example 1: Revenue Chart
**User**: "Show me the revenue trends"

**Response**: 
- Text: "Based on the financial data, revenue has grown from ₹100,000 in 2021 to ₹150,000 in 2023."
- Chart: Line chart showing revenue growth over 3 years

### Example 2: Expense Distribution
**User**: "Give me a chart of expenses"

**Response**:
- Text: "The expense breakdown shows the following distribution..."
- Chart: Pie chart showing expense categories (Salaries 40%, Rent 25%, etc.)

### Example 3: Financial Table
**User**: "Show me the balance sheet"

**Response**:
- Text: "The requested table is shown below."
- Table: Structured table with Assets, Liabilities, and Equity

### Example 4: Comparison Chart
**User**: "Compare sales across regions"

**Response**:
- Text: "Sales comparison across regions shows..."
- Chart: Bar chart comparing sales by region

## Technical Details

### Chart.js Configuration
- **Responsive**: Charts adapt to container size
- **Formatted numbers**: Large numbers shown with commas (1,000,000)
- **Compact notation**: Y-axis uses compact format (1M, 1K)
- **Color scheme**: Professional blue/green/amber palette
- **Accessibility**: Proper labels, tooltips, and legends

### Performance Optimizations
- **Dynamic imports**: Chart.js loaded only when needed
- **SSR disabled**: Charts render client-side only
- **Loading states**: Skeleton loaders during chart generation
- **Error handling**: Graceful fallbacks if chart generation fails

### Browser Compatibility
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Testing

### Test Scenarios
1. ✅ Upload PDF with financial data
2. ✅ Ask for "charts" → Should generate appropriate chart
3. ✅ Ask for "revenue trends" → Should generate line chart
4. ✅ Ask for "expense breakdown" → Should generate pie chart
5. ✅ Ask for "comparison" → Should generate bar chart
6. ✅ Ask for "table" → Should generate structured table
7. ✅ Multiple charts in conversation → Each should render correctly

### Known Limitations
- Charts are generated from extracted data (accuracy depends on PDF quality)
- Maximum 50 data points per chart (for performance)
- Tables limited to reasonable size (50 rows)
- Requires numerical data in PDF to generate charts

## Troubleshooting

### Charts Not Showing
1. **Check browser console** for errors
2. **Verify API response** includes chart data with labels and values
3. **Ensure Chart.js is loaded** (check network tab)
4. **Try refreshing** the page

### Charts Look Wrong
1. **Check data format** in API response
2. **Verify labels and values** have same length
3. **Check chart type** is valid (bar, line, pie, table)
4. **Inspect console** for validation errors

### Backend Not Detecting Charts
1. **Check PDF content** has numerical data
2. **Use explicit keywords** like "chart", "graph", "visualize"
3. **Mention financial terms** like "revenue", "profit", "sales"
4. **Check backend logs** for visualization detection

## Future Enhancements

### Potential Improvements
- [ ] Multi-series charts (multiple datasets)
- [ ] Stacked bar charts
- [ ] Area charts for cumulative data
- [ ] Export charts as images (PNG/SVG)
- [ ] Interactive chart controls (zoom, pan)
- [ ] Chart customization (colors, styles)
- [ ] Animated chart transitions
- [ ] Real-time chart updates

### Advanced Features
- [ ] Combination charts (bar + line)
- [ ] Heatmaps for correlation data
- [ ] Scatter plots for relationships
- [ ] Gauge charts for KPIs
- [ ] Funnel charts for conversion data
- [ ] Treemaps for hierarchical data

## Conclusion

The chart visualization system is now fully implemented and ready to use. Users can simply ask for charts, graphs, or visualizations, and the system will automatically:
1. Detect the need for visualization
2. Extract relevant data from the PDF
3. Generate appropriate chart type
4. Render beautiful, interactive charts

The system supports bar charts, line charts, pie charts, and structured tables, making it perfect for financial data analysis and reporting.

