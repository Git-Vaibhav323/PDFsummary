"""
Prompt templates for RAG and visualization detection.
"""
from langchain.prompts import PromptTemplate


# RAG Answer Generation Prompt - OPTIMIZED FOR SPEED & ACCURACY
RAG_PROMPT_TEMPLATE = """You are a precision financial assistant. Answer STRICTLY based on the provided context.

CRITICAL RULES (MANDATORY):
1. NEVER speculate, infer, or generalize - ONLY use the provided context
2. Answer the specific question asked - no unnecessary elaboration
3. If information is not in the provided context, respond: "This information is not available in the provided document."
4. Be precise, factual, and cite sources (page numbers) when available
5. NEVER provide unsolicited summaries, overviews, or introductions
6. Do NOT provide any information the user did not request

RESPONSE FORMAT (STRICT):
- Direct answer (1-2 lines maximum)
- Key points (bullet list if applicable)
- Numerical data (if present and relevant)
- Brief conclusion (optional)

NO long introductions. NO unnecessary explanations.

SPECIAL RULES:
- For financial data: Provide key metrics only, charts will be generated automatically
- For tables/tabular data: Response = "The requested table is shown below."
- For comparisons: Provide brief analysis, let visualization show data
- NEVER mention "Chart 1" or multiple charts - only ONE will be generated

Context from PDF (FACT-CHECKED AND COMPRESSED):
{context}

Question: {question}

Answer (precise, structured, fact-based ONLY):"""

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
- ALWAYS respond "YES" if the question asks to "show", "visualize", "chart", "graph", "compare", "trend", "display", "plot", "table", "tabular", or "list"
- ALWAYS respond "YES" if the context contains ANY numerical data (numbers, percentages, counts, measurements, tables)
- ALWAYS respond "YES" if the context has tabular data, lists of numbers, or comparisons
- ALWAYS respond "YES" if the question explicitly asks for a "table" or "tabular format"
- ALWAYS respond "YES" for financial data questions (revenue, profit, sales, cost, budget, balance sheet, income statement, cash flow, financial statements, earnings, expenses, assets, liabilities, equity, P&L, profit & loss)
- ALWAYS respond "YES" if the question mentions financial terms (revenue, profit, sales, cost, budget, balance, income, expense, asset, liability, equity, earnings, margin, ratio, growth, decline, increase, decrease, comparison, trend)
- ALWAYS respond "YES" if the question asks about financial performance, financial data, financial metrics, or financial analysis
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
   - For financial data: Accept labels like "Revenue", "Profit", "Sales", "Cost", "Expense", "Asset", "Liability", "Equity", "Balance", "Income", "Earnings", "Margin", "Ratio", "Growth", "Year", "Quarter", "Month", etc.

2. SEMANTIC MEANING REQUIRED:
   - Valid: Currency (₹, $, revenue, profit, sales, cost, budget, balance, income, expense, asset, liability, equity, earnings, margin), Percentages (%), Quantities (counts, amounts), Time-based values (years, months, quarters), Financial ratios, Growth rates, Comparisons
   - Invalid: Page numbers, Index values, Serial numbers, Isolated numeric sequences, Reference numbers

3. MINIMUM REQUIREMENTS:
   - At least 2 labeled values required
   - Numbers must belong to the same metric/category
   - Must have units or clear semantic meaning
   - For financial tables: Extract complete table structure with all rows and columns

4. EXCLUDE THESE:
   - Page numbers (e.g., "Page 7", "p. 10")
   - Section numbers (e.g., "Section 1.2", "Chapter 3")
   - Serial numbers or reference codes
   - Random numeric sequences without context
   - Index values or table of contents numbers

Extract ONLY:
1. Financial data (revenue, profit, cost, sales, budget, balance, income statement, balance sheet, cash flow, P&L, profit & loss, earnings, expenses, assets, liabilities, equity, financial statements, financial metrics, financial performance) - MUST have proper labels
2. Statistical data (percentages, ratios, counts with meaning) - MUST have proper labels
3. Time-series data (years, months, quarters with associated values) - MUST have proper labels
4. Comparative data (categories with associated metrics) - MUST have proper labels
5. Financial tables (Balance Sheet, Income Statement, Cash Flow Statement, Financial Summary, P&L Statement) - Extract complete table structure

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

**CHART vs TABLE DECISION (CRITICAL):**
- If question contains: "chart", "graph", "visualize", "bar chart", "line chart", "pie chart", "comparison", "trend", "show chart" → Use CHART type ("bar", "line", or "pie")
  * Extract labels and values arrays
  * DO NOT use "table" type
  * Example: "Show me a chart of revenue" → chart_type: "bar" with labels/values

- If question contains: "table", "tabular", "show table", "display table", "tabular format" → Use TABLE type ("table")
  * Extract headers and rows arrays
  * DO NOT use chart types
  * Example: "Show me the balance sheet table" → chart_type: "table" with headers/rows

- **MANDATORY TABLE EXTRACTION**: If the question explicitly asks for "table", "tables", "tabular", "show as table", you MUST:
  * Extract the actual table data from the context
  * Identify table headers (column names)
  * Extract all rows of data from the table
  * Return chart_type: "table" with headers and rows arrays
  * DO NOT return chart data (labels/values) when user asks for tables

- **MANDATORY CHART EXTRACTION**: If the question asks for "chart", "graph", "visualize", "bar chart", "line chart", "pie chart", you MUST:
  * Extract numerical data with labels
  * Return chart_type: "bar", "line", or "pie" with labels and values arrays
  * DO NOT return table format (headers/rows) when user asks for charts

- Chart type selection:
  * "bar" for comparisons and categories (revenue by year, expenses by category)
  * "line" for time-series data (revenue trends, growth over time)
  * "pie" for proportions/percentages (expense distribution, market share)

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


# Question Rewriting Prompt - For resolving references using memory
QUESTION_REWRITE_PROMPT_TEMPLATE = """You are a helpful assistant that rewrites questions to make them standalone by using conversation context.

Your task: Rewrite the question to be standalone and clear, using only the conversation history to resolve pronouns and references.

RULES:
1. If the current question contains pronouns (it, that, this, these, those) or references (previous, earlier, same), resolve them using the conversation context
2. Keep the question concise and natural
3. Do NOT add external knowledge - only use the conversation context
4. If the context doesn't clarify a reference, keep the original wording
5. Return ONLY the rewritten question, no explanation

Conversation Context:
{memory_context}

Current Question: {current_question}

Rewritten Question:"""

QUESTION_REWRITE_PROMPT = PromptTemplate(
    input_variables=["memory_context", "current_question"],
    template=QUESTION_REWRITE_PROMPT_TEMPLATE
)


# RAG Answer Generation Prompt - Strict grounding
RAG_ANSWER_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions STRICTLY based on provided context.

CRITICAL RULES:
1. Answer ONLY using the information in the provided context
2. If the answer is not in the context, respond exactly: "Not available in the uploaded document."
3. Be concise and direct
4. Cite page numbers when available in the context metadata
5. Do NOT add external knowledge or assumptions
6. If asked for specific data (numbers, dates, names), use EXACTLY what appears in the context

Context from Document:
{context}

Question: {question}

Answer (use ONLY information from the context above):"""

RAG_ANSWER_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=RAG_ANSWER_PROMPT_TEMPLATE
)
