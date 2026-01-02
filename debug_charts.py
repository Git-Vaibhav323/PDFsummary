"""Debug script to check why charts aren't being generated."""
import json
from app.rag.visualization_pipeline import VisualizationDetector, VisualizationPipeline

print("="*80)
print("CHART GENERATION DEBUG")
print("="*80)

# Test the detection
detector = VisualizationDetector()

test_question = "Show me the charts"
test_context = """
Cash Flow Statement
PARTICULARS | AS AT 31ST MARCH | AS AT 31ST MARCH 2023
Income Tax Paid (Net of Refunds) | (270, 01) | 245, 5
Less : Taxes Paid (Income Tax) | (270, 01) | 245, 5
Net Cash Flow from Operating Activities - I | (3,258, 39) | (28,251.28
Cash From Investing Activities : | - | -
Proceeds from Sale of Fixed Assets | - | -
Purchase of Fixed Assets | (298, 04) | (1,373, 88
Net Cash Flow from Investing Activities - II | (298, 04) | (1,373, 88
Cash from Financing Activities | - | -
Increase in Short Term Borrowings | 8, 08 | 8, 0
Financial Charges | 8, 08 | 8, 0
Net Cash Flow from Financing Activities - III | 8, 08 | 8, 0
"""

print(f"\nTest Question: '{test_question}'")
print(f"Context length: {len(test_context)} chars")

# Test detection
should_viz = detector.should_visualize(test_question, test_context)
print(f"\n1. Detection Result: {should_viz}")

# Test full pipeline
pipeline = VisualizationPipeline()
print(f"\n2. Processing with visualization pipeline...")

result = pipeline.process(
    question=test_question,
    context=test_context,
    answer="Here is the cash flow data showing various financial activities"
)

print(f"\n3. Pipeline Result:")
if result:
    print(f"   Keys: {list(result.keys())}")
    if result.get('chart'):
        print(f"   Chart found: {result['chart'].get('type')}")
        print(f"   Chart title: {result['chart'].get('title')}")
    else:
        print(f"   ❌ No chart in result")
else:
    print(f"   ❌ Empty result")

# Try with different questions
print("\n" + "="*80)
print("TESTING DIFFERENT QUESTIONS")
print("="*80)

questions = [
    "Show me the charts",
    "Create a bar chart",
    "Visualize the data",
    "Display as chart",
    "What is the cash flow?",
]

for q in questions:
    viz = detector.should_visualize(q, test_context)
    print(f"  '{q}' → {'Visualize' if viz else 'No viz'}")

print("\n" + "="*80)
