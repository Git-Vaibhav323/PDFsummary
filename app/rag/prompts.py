"""
Prompt templates for RAG and visualization detection.
"""
from langchain.prompts import PromptTemplate


# RAG Answer Generation Prompt
RAG_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based on the provided context from a PDF document.

CRITICAL RULES:
1. ALWAYS provide an answer based on the provided context. Use ALL available information in the context.
2. If the context contains relevant information, USE IT to answer the question - even if it's not a perfect match.
3. If asked for tables, lists, or data, extract and present the relevant information from the context.
4. If asked for a summary, provide a comprehensive summary using ALL information in the context.
5. If the context contains numerical data, tables, or trends, provide a brief TEXTUAL summary. A chart will be generated automatically.
6. Be precise and cite page numbers when available.
7. NEVER say "Not available in the uploaded document" unless the context is completely empty or irrelevant.
8. If the context has ANY relevant information, use it to answer - do not be overly conservative.
9. NEVER say "the document does not provide a chart" or "I will present the data as a table instead" - charts are generated automatically from numerical data.
10. DO NOT mention "Chart 1", "Chart 2", or multiple charts - only ONE chart will be generated.
11. DO NOT list raw numbers or create numbered lists of charts - provide a simple text summary.
12. If numerical data exists and the user asks for a table, a table visualization will be generated automatically. Otherwise, describe it briefly in text.
13. DO NOT use phrases like "Chart:" followed by a table. Just provide a textual description of the data.
14. IMPORTANT: If the question explicitly asks for "tables" or "tabular format", the system will generate a table visualization automatically.
15. CRITICAL: If the user asks ANYTHING about tables:
    - DO NOT provide descriptions or summaries
    - DO NOT create tables in your response
    - DO NOT use markdown tables, ASCII art, or any table formatting
    - ONLY say: "The requested table is shown below."
    - The system will automatically extract and display the actual table
16. NEVER include table syntax (|, ---, +, =, dashed lines, borders) in your response.
17. NEVER describe what is in a table - the system shows the actual table automatically.
18. For ANY question containing the word "table" or "tables", respond with ONLY: "The requested table is shown below."

Context from PDF:
{context}

Question: {question}

Answer (use ALL relevant information from the context above):"""

# Summary Generation Prompt
SUMMARY_PROMPT_TEMPLATE = """Based on the following context from a PDF document, provide a comprehensive, detailed summary.

CRITICAL RULES:
1. Summarize ALL information present in the provided context - be thorough and comprehensive.
2. Include ALL key topics, main points, important details, and conclusions from the context.
3. Organize the summary logically (main topics, key points, conclusions, important data).
4. Include important numerical data, dates, facts, tables, and any structured information if present.
5. Cite page numbers when available.
6. Make the summary detailed and informative - cover all major aspects mentioned in the context.
7. If tables or structured data are mentioned, describe them in detail.
8. DO NOT skip information - include everything relevant from the context.

Context from PDF:
{context}

Provide a comprehensive, detailed summary of this document covering all major topics and information:"""

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=RAG_PROMPT_TEMPLATE
)


# Visualization Detection Prompt
VISUALIZATION_DETECTION_PROMPT_TEMPLATE = """Analyze the following question and retrieved context to determine if a visualization (chart/graph/table) should be generated.

CRITICAL RULES:
- ALWAYS respond "YES" if the context contains ANY numerical data (numbers, percentages, counts, measurements, tables)
- ALWAYS respond "YES" if the question asks to "show", "visualize", "chart", "graph", "compare", "trend", "display", "plot", "table", "tabular", or "list"
- ALWAYS respond "YES" if the context has tabular data, lists of numbers, or comparisons
- ALWAYS respond "YES" if the question explicitly asks for a "table" or "tabular format"
- Do NOT check if the original document contains a chart - generate a visualization from the data
- The presence of numerical/tabular data is sufficient to require visualization

Question: {question}

Retrieved Context:
{context}

Respond with ONLY one word: "YES" if visualization is needed, "NO" if not needed.
Do not provide any explanation."""

VISUALIZATION_DETECTION_PROMPT = PromptTemplate(
    input_variables=["question", "context"],
    template=VISUALIZATION_DETECTION_PROMPT_TEMPLATE
)


# Data Extraction for Visualization Prompt
DATA_EXTRACTION_PROMPT_TEMPLATE = """Extract MEANINGFUL numerical data from the following context that is relevant to the question.

Question: {question}

Context:
{context}

CRITICAL: If the question asks for "tables", "tabular data", or "show as table", you MUST extract actual table data with headers and rows. Do NOT just describe what tables exist - extract the actual data from the tables.

TABLE EXTRACTION INSTRUCTIONS (CRITICAL - FOLLOW EXACTLY):
1. Look for structured data in the context that appears in rows and columns
2. Identify the column headers (first row or header row) - these become the "headers" array
3. Extract ALL data rows from the table - each row becomes an array in the "rows" array
4. Preserve the exact structure - if a table has 5 columns, each row must have 5 values
5. Include ALL columns and rows - don't skip any data
6. If multiple tables exist, extract the MOST RELEVANT one based on the question
7. For financial tables (Balance Sheets, Income Statements, Cash Flows, etc.), extract the complete table structure
8. Include all numerical values, labels, dates, and text exactly as they appear
9. Example: If context has "Revenue | 2022 | 2021\nSales | 1000 | 900", extract:
   headers: ["Metric", "2022", "2021"]
   rows: [["Sales", "1000", "900"]]
10. DO NOT return chart format (labels/values) when user asks for tables - ONLY return table format

CRITICAL FILTERING RULES - ONLY extract data that meets ALL criteria:

1. CONTEXTUAL LABELS REQUIRED:
   - Each number MUST have a meaningful label (year, category, metric name, financial term)
   - DO NOT extract numbers without labels
   - DO NOT extract page numbers, section numbers, or indexes

2. SEMANTIC MEANING REQUIRED:
   - Valid: Currency (₹, $, revenue, profit, sales, cost), Percentages (%), Quantities (counts, amounts), Time-based values (years, months, quarters)
   - Invalid: Page numbers, Index values, Serial numbers, Isolated numeric sequences, Reference numbers

3. MINIMUM REQUIREMENTS:
   - At least 2 labeled values required
   - Numbers must belong to the same metric/category
   - Must have units or clear semantic meaning

4. EXCLUDE THESE:
   - Page numbers (e.g., "Page 7", "p. 10")
   - Section numbers (e.g., "Section 1.2", "Chapter 3")
   - Serial numbers or reference codes
   - Random numeric sequences without context
   - Index values or table of contents numbers

Extract ONLY:
1. Financial data (revenue, profit, cost, sales, budget, balance, etc.) - MUST have proper labels
2. Statistical data (percentages, ratios, counts with meaning) - MUST have proper labels
3. Time-series data (years, months, quarters with associated values) - MUST have proper labels
4. Comparative data (categories with associated metrics) - MUST have proper labels

CRITICAL: 
- DO NOT extract raw numbers without labels
- DO NOT extract data with "-" or null values
- DO NOT extract data where labels are just numbers or "appears X times"
- Each value MUST have a meaningful descriptive label (e.g., "Revenue 2024", "Profit Margin", "Sales Q1", "Opening Balance")
- Extract ONLY ONE best/most meaningful dataset - NOT multiple charts
- If multiple datasets exist, select the MOST IMPORTANT financial or summary data
- DO NOT create separate charts for different sections - combine related data into ONE chart

CRITICAL RULES:
- You MUST respond with ONLY valid JSON. No explanations, no markdown, no extra text. Just the JSON object.
- "chart_type" MUST be one of: "bar", "line", "pie", or "table"
- **MANDATORY TABLE EXTRACTION**: If the question contains words like "table", "tables", "tabular", "show as table", or asks to "display tables", you MUST:
  * Extract the actual table data from the context
  * Identify table headers (column names)
  * Extract all rows of data from the table
  * Return chart_type: "table" with headers and rows arrays
  * DO NOT return chart data (labels/values) when user asks for tables
- Use "table" when:
  * The question explicitly asks for a table, tabular format, or "show as table" (HIGHEST PRIORITY)
  * The data has multiple columns/categories that are better displayed in rows and columns
  * The data has more than 2 dimensions (e.g., multiple metrics per category)
  * The user wants to see exact values rather than visual trends
- Use "bar" for comparisons and categories (default, but NOT when user asks for tables)
- Use "line" for time-series data (years, dates, months)
- Use "pie" for proportions/percentages
- If data is naturally tabular (multiple columns), prefer "table" over "bar"

IMPORTANT LIMITATIONS:
- Limit "values" array to maximum 20 numbers (if more data exists, select the most important 20)
- Limit "labels" array to maximum 20 labels (must match values count)
- Keep JSON compact and valid
- Select the MOST MEANINGFUL financial or summary data if multiple options exist

Format your response as a JSON object with this EXACT structure (STRICT SCHEMA):

For charts (bar, line, pie):
{{
    "chart_type": "bar | line | pie",
    "labels": ["string", "string", ...],
    "values": [number, number, ...],
    "title": "string",
    "x_axis": "string",
    "y_axis": "string"
}}

For tables (USE THIS when question asks for tables):
{{
    "chart_type": "table",
    "headers": ["Column1", "Column2", "Column3", ...],
    "rows": [
        ["Row1Col1", "Row1Col2", "Row1Col3", ...],
        ["Row2Col1", "Row2Col2", "Row2Col3", ...],
        ...
    ],
    "title": "string"
}}

IMPORTANT FOR TABLES:
- Extract ALL rows from the table found in the context
- Include ALL columns/headers from the table
- Preserve the exact structure of the table
- Include numerical values, text labels, dates, and all data from the table
- If multiple tables exist, extract the MOST RELEVANT one based on the question
- Maximum 50 rows to avoid truncation (select most important if more exist)

CRITICAL: Use "chart_type" NOT "data_type". All fields are REQUIRED.

Chart Type Selection Rules:
- "bar": Comparisons, categories, year-wise snapshots (DEFAULT for simple comparisons)
- "line": Time-series, trends over years/months
- "pie": Proportions, percentages, share distributions
- "table": Multi-column data, exact values, structured information, when user asks for tables

If NO meaningful numerical data exists (only page numbers, indexes, etc.), return EXACTLY: {{"error": "No meaningful extractable data"}}

IMPORTANT: 
- Return ONLY the JSON object, nothing else
- No markdown code blocks, no explanations
- Ensure values and labels arrays have the SAME length
- Keep arrays small (max 20 items) to avoid truncation
- Use "table" when the data structure or user request calls for tabular display
- ONLY extract data with meaningful labels and semantic context"""

DATA_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["question", "context"],
    template=DATA_EXTRACTION_PROMPT_TEMPLATE
)

# Summary Prompt
SUMMARY_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=SUMMARY_PROMPT_TEMPLATE
)

