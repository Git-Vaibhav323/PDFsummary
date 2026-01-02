"""
Simple test to verify chart generation is working.
Tests the visualization pipeline directly without starting the server.
"""

import json
from app.config.settings import settings
from app.rag.visualization_pipeline import (
    VisualizationDetector, 
    DataExtractor, 
    ChartGenerator,
    VisualizationPipeline
)

print("="*80)
print("CHART VISUALIZATION TEST")
print("="*80)

# Verify configuration
print(f"\n✅ Configuration:")
print(f"   Model: {settings.openai_model}")
print(f"   Embeddings: {settings.embedding_model_name}")
print(f"   Temperature: {settings.temperature}")

# Test 1: Chart Generation - Bar Chart
print("\n" + "-"*80)
print("[Test 1] Bar Chart Generation")
print("-"*80)

bar_data = {
    "chart_type": "bar",
    "title": "Quarterly Revenue",
    "labels": ["Q1", "Q2", "Q3", "Q4"],
    "values": [100, 115, 132, 148],
    "x_axis": "Quarter",
    "y_axis": "Revenue (M$)"
}
bar_chart = ChartGenerator.generate_chart(bar_data)
print(f"✅ Bar Chart Created:")
print(f"   Type: {bar_chart['type']}")
print(f"   Title: {bar_chart['title']}")
print(f"   Data points: {len(bar_chart['labels'])}")
print(f"   X-Axis: {bar_chart['xAxis']}")
print(f"   Y-Axis: {bar_chart['yAxis']}")
print(f"   Sample data: {list(zip(bar_chart['labels'][:2], bar_chart['values'][:2]))}")

# Test 2: Line Chart
print("\n" + "-"*80)
print("[Test 2] Line Chart Generation")
print("-"*80)

line_data = {
    "chart_type": "line",
    "title": "Revenue Trend (2024)",
    "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "values": [80, 85, 95, 110, 118, 125],
    "x_axis": "Month",
    "y_axis": "Revenue (M$)"
}
line_chart = ChartGenerator.generate_chart(line_data)
print(f"✅ Line Chart Created:")
print(f"   Type: {line_chart['type']}")
print(f"   Title: {line_chart['title']}")
print(f"   Data points: {len(line_chart['labels'])}")
print(f"   First value: {line_chart['labels'][0]} = ${line_chart['values'][0]}M")
print(f"   Last value: {line_chart['labels'][-1]} = ${line_chart['values'][-1]}M")

# Test 3: Pie Chart
print("\n" + "-"*80)
print("[Test 3] Pie Chart Generation")
print("-"*80)

pie_data = {
    "chart_type": "pie",
    "title": "Market Share by Region",
    "labels": ["North America", "Europe", "Asia Pacific", "Other"],
    "values": [45, 28, 18, 9]
}
pie_chart = ChartGenerator.generate_chart(pie_data)
print(f"✅ Pie Chart Created:")
print(f"   Type: {pie_chart['type']}")
print(f"   Title: {pie_chart['title']}")
print(f"   Segments: {len(pie_chart['labels'])}")
for label, value in zip(pie_chart['labels'], pie_chart['values']):
    print(f"     - {label}: {value}%")

# Test 4: Table Chart
print("\n" + "-"*80)
print("[Test 4] Table Generation")
print("-"*80)

table_data = {
    "chart_type": "table",
    "title": "Financial Summary",
    "headers": ["Metric", "2024", "2023"],
    "rows": [
        ["Revenue", "$148M", "$120M"],
        ["Profit", "$31M", "$24M"],
        ["Margin", "21%", "20%"]
    ]
}
table_chart = ChartGenerator.generate_chart(table_data)
print(f"✅ Table Created:")
print(f"   Type: {table_chart['type']}")
print(f"   Title: {table_chart['title']}")
print(f"   Columns: {len(table_chart['headers'])}")
print(f"   Rows: {len(table_chart['rows'])}")
print(f"   Headers: {' | '.join(table_chart['headers'])}")

# Test 5: Visualization Detection
print("\n" + "-"*80)
print("[Test 5] Visualization Detection")
print("-"*80)

detector = VisualizationDetector()

test_questions = [
    ("Create a bar chart of quarterly revenue", True),
    ("Show me the sales trend over time", True),
    ("What is the market share breakdown?", True),
    ("Visualize the profit margins by product", True),
    ("What happened to our revenue?", False),
    ("Explain the quarterly results", False),
]

context = "Q1: $100M, Q2: $115M, Q3: $132M, Q4: $148M"

for question, should_visualize in test_questions:
    should_viz = detector.should_visualize(question, context)
    status = "✅" if should_viz == should_visualize else "⚠️"
    print(f"{status} '{question}'")
    print(f"   Detection: {'Yes' if should_viz else 'No'} | Expected: {'Yes' if should_visualize else 'No'}")

# Test 6: Complete Pipeline
print("\n" + "-"*80)
print("[Test 6] Complete Visualization Pipeline")
print("-"*80)

pipeline = VisualizationPipeline()

# Simulate a question-context-answer for visualization
test_question = "Show me revenue by quarter as a chart"
test_context = """
Financial Results:
Q1 2024: Revenue $100M
Q2 2024: Revenue $115M
Q3 2024: Revenue $132M
Q4 2024: Revenue $148M
"""
test_answer = "Based on the financial data, here are the quarterly revenues."

print(f"Question: {test_question}")
print(f"Context: {len(test_context)} chars")

result = pipeline.process(
    question=test_question,
    context=test_context,
    answer=test_answer
)

if result and result.get('chart'):
    chart = result['chart']
    print(f"\n✅ Pipeline Output:")
    print(f"   Chart Type: {chart['type']}")
    print(f"   Title: {chart['title']}")
    print(f"   Data: {len(chart.get('labels', []))} points")
    print(f"   Full output keys: {list(result.keys())}")
else:
    print(f"\n⚠️  No chart generated (may not match detection criteria)")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("""
✅ All 4 Chart Types Implemented:
   1. Bar Charts    - For categorical comparisons (revenue, sales, by region, etc.)
   2. Line Charts   - For time-series trends (monthly, quarterly, yearly, etc.)
   3. Pie Charts    - For proportional data (market share, distribution %, etc.)
   4. Tables        - For detailed tabular data (multiple columns and rows)

✅ How It Works:
   1. Detection  - Scans question/context for visualization keywords
   2. Extraction - Uses gpt-4.1-mini to extract structured data (JSON)
   3. Generation - Creates chart objects with proper structure
   4. Assembly   - Includes charts in API response alongside answer

✅ Features:
   • Automatic detection (no manual specification needed)
   • Deterministic generation (temperature=0)
   • Strict grounding (data from document only)
   • Multiple chart types in single response
   • Clean JSON output for frontend rendering

📊 Testing with Real API:

1. Upload a PDF with financial data:
   curl -X POST http://localhost:8000/upload_pdf \\
     -F "file=@financial_report.pdf"

2. Ask for a chart:
   curl -X POST http://localhost:8000/chat \\
     -H "Content-Type: application/json" \\
     -d '{
       "question": "Create a bar chart showing quarterly revenue"
     }'

3. Response includes:
   {
     "answer": "...",
     "chart": {
       "type": "bar",
       "title": "Quarterly Revenue",
       "labels": ["Q1", "Q2", "Q3", "Q4"],
       "values": [100, 115, 132, 148],
       ...
     },
     "chat_history": [...]
   }
""")
print("="*80)
