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


# Visualization Detection Prompt - AUTOMATIC CHART GENERATION
VISUALIZATION_DETECTION_PROMPT_TEMPLATE = """Analyze the following question and retrieved context to determine if a visualization (chart/graph/table) should be generated.

CRITICAL RULES - AUTOMATIC CHART GENERATION:
- ALWAYS respond "YES" if the question asks to "show", "visualize", "chart", "graph", "compare", "trend", "display", "plot", "table", "tabular", or "list"
- ALWAYS respond "YES" if the context contains ANY numerical data (numbers, percentages, counts, measurements, tables)
- ALWAYS respond "YES" if the context has tabular data, lists of numbers, or comparisons
- ALWAYS respond "YES" if the question explicitly asks for a "table" or "tabular format"
- ALWAYS respond "YES" for financial data questions (revenue, profit, sales, cost, budget, balance sheet, income statement, cash flow, financial statements, earnings, expenses, assets, liabilities, equity, P&L, profit & loss)
- ALWAYS respond "YES" if the question mentions financial terms (revenue, profit, sales, cost, budget, balance, income, expense, asset, liability, equity, earnings, margin, ratio, growth, decline, increase, decrease, comparison, trend)
- ALWAYS respond "YES" if the question asks about financial performance, financial data, financial metrics, or financial analysis

AUTOMATIC CHART GENERATION TRIGGERS (respond "YES" for these):
- Questions about trends, growth, decline, changes over time
- Questions comparing data across years, periods, or categories
- Questions mentioning percentages, ratios, or quantitative metrics
- Questions asking "how much", "what was", "show me" with numerical context
- Questions about year-wise data, quarterly data, or time-series information
- Questions asking "which is higher/lower/better" or ranking comparisons
- ANY question where context contains multiple numbers, years, or percentages
- Questions about performance, metrics, statistics, or data analysis

GENERAL RULE:
- When in doubt, respond "YES" - charts enhance understanding of quantitative data
- Do NOT check if the original document contains a chart - generate a visualization from the data
- The presence of numerical/tabular data is sufficient to require visualization
- Even if user doesn't explicitly ask for a chart, generate one if data suggests it would be helpful

Question: {question}

Retrieved Context:
{context}

Respond with ONLY one word: "YES" if visualization is needed, "NO" if not needed.
Do not provide any explanation."""

VISUALIZATION_DETECTION_PROMPT = PromptTemplate(
    input_variables=["question", "context"],
    template=VISUALIZATION_DETECTION_PROMPT_TEMPLATE
)


# Data Extraction for Visualization Prompt - PRIORITIZE VISUAL REPRESENTATION
DATA_EXTRACTION_PROMPT_TEMPLATE = """Extract MEANINGFUL numerical data from the following context that is relevant to the question.

PRIORITY: Visual representation FIRST, then textual explanation.

Question: {question}

Context:
{context}

CRITICAL EXTRACTION RULES FOR AUTOMATIC CHART GENERATION:
1. If the question asks for "tables", "tabular data", or "show as table", you MUST extract actual table data with headers and rows. Do NOT just describe what tables exist - extract the actual data from the tables.

2. For trends over time: Extract ALL data points with their time periods (years, quarters, months). Include labels (time periods) and values (numbers). Use "line" chart type.

3. For comparisons: Extract ALL items being compared with their values. Create clear labels and corresponding values. Use "bar" chart type.

4. For percentages/ratios: Extract the percentage values and what they represent. Include both labels and values. Use "pie" or "bar" chart type.

5. For financial data: Extract ALL relevant metrics (revenue, profit, costs, etc.) with their values and time periods if available.

6. For year-wise data: Extract data for EACH year mentioned with clear labels (e.g., "2020", "2021", "2022") and corresponding values.

7. For growth/decline: Extract the starting value, ending value, and calculate/show the change percentage.

8. ALWAYS extract structured data in a format that can be directly rendered as charts:
   - For trends: Use "line" chart type with time periods as labels
   - For comparisons: Use "bar" chart type with categories as labels
   - For distributions: Use "pie" chart type with categories as labels
   - For multiple series: Use "stacked_bar" chart type with groups

9. Include proper titles that clearly describe what the chart shows.

10. Ensure all numerical values are extracted accurately - do not round or approximate unless necessary.

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


# RAG Answer Generation Prompt - Strict grounding with multi-document support + AUTOMATIC CHART GENERATION
RAG_ANSWER_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based on provided context from documents and/or web search results.

CRITICAL RULES FOR MULTI-SOURCE HANDLING:
1. Answer using the information in the provided context
2. If "[Web Search Results]" section is present, PRIORITIZE web search information for current/recent information (especially for questions about "latest", "current", "2024", "2025", etc.)
3. If "[Document Context]" section is present, use it for historical or document-specific information
4. If multiple documents are present, CLEARLY attribute information to its source document
5. Use labels like "Document 1", "Document 2", etc., or document names when available
6. NEVER mix metrics, years, or facts from different sources without attribution
7. If information is missing in a document, explicitly state which document lacks that information
8. For questions about recent/current information (2024, 2025, "latest", "current"), use web search results as PRIMARY source
9. If the answer is not in ANY context (neither documents nor web search), respond exactly: "Not available in the uploaded document(s) or web search results."
10. Be concise and direct - focus on high-level understanding, not excessive numerical detail
11. Cite page numbers when available in the context metadata, and cite URLs when using web search results
12. Do NOT add external knowledge beyond what's in the provided context
13. If asked for specific data (numbers, dates, names), use EXACTLY what appears in the context

CRITICAL RULES FOR COMPARISON QUESTIONS (MANDATORY - SCALABLE FOR MANY DOCUMENTS):
When the question asks to "compare", "difference", "versus", "which is better/different", "trend across documents", or similar comparison patterns:

COMPARISON REASONING STRUCTURE (MANDATORY ORDER):
1. IDENTIFY COMMON THEME: What is being compared? (finance, risk, operations, strategy, etc.)
   - Extract the core theme/metric from the question
   - Align scope and time periods across documents BEFORE comparing
   - Example: "Comparing financial performance across documents, aligning FY2021 data from Document 1 with FY2022 data from Document 2..."

2. EXTRACT COMPARABLE SIGNALS: For each document, extract ONLY the relevant comparable data
   - Do NOT summarize entire documents
   - Extract ONLY metrics/facts relevant to the comparison theme
   - Group by document: "Document 1 shows X, Document 2 shows Y, Document 3 shows Z..."

3. CONTRAST SIMILARITIES AND DIFFERENCES:
   - Identify what is SIMILAR across documents: "All documents indicate...", "Most documents show..."
   - Identify what is DIFFERENT: "In contrast...", "While Document 1 emphasizes..., Document 2 focuses on..."
   - Use comparative language: "whereas", "however", "on the other hand", "in contrast"

4. EXPLAIN WHY DIFFERENCES MATTER:
   - Provide reasoning: "This difference suggests...", "This indicates...", "This reflects..."
   - Connect differences to implications or trends
   - Explain significance: "The key difference is... because..."

5. SYNTHESIZED CONCLUSION:
   - End with a clear comparative conclusion
   - Summarize the key insight, trend, or difference
   - Example: "Overall, the comparison reveals [insight], with Document X showing [pattern] while Document Y demonstrates [contrasting pattern]."

SCALABILITY RULES FOR MANY DOCUMENTS (5+ documents):
- When comparing many documents, identify PATTERNS rather than listing each document
- Use grouping: "Most documents (Documents 1, 2, 3) indicate X, while Documents 4 and 5 show Y..."
- Summarize trends: "The majority trend is..., with exceptions in..."
- Focus on outliers: "Most documents align on X, except Document N which differs by..."
- Avoid exhaustive detail - focus on key insights and contrasts

CRITICAL PROHIBITIONS:
1. DO NOT list or dump everything contained in each document independently
2. DO NOT describe documents separately without linking them
3. DO NOT repeat the same information for each document
4. DO NOT provide exhaustive summaries - focus on comparative insights
5. DO NOT mix facts from different documents without clear attribution
6. DO NOT infer missing data - explicitly state when a document lacks comparable information

OUTPUT REQUIREMENTS:
- Clearly separate documents as "Document 1", "Document 2", etc., but CONNECT them through comparative statements
- Use concise language suitable for a normal user (not analyst-level depth)
- Only include detailed tables or raw data if the user explicitly asks for them
- Ensure every comparison answer:
  * Explains the RELATIONSHIP between documents
  * Avoids repetition and redundancy
  * Feels ANALYTICAL, not descriptive
  * Scales gracefully with document count (patterns for many docs, detailed for few docs)

COMPARISON ANSWER STRUCTURE:
- Opening: Identify what is being compared and align scope/time periods
- Body: Present comparative insights linking documents (e.g., "Document 1 shows X, while Document 2 shows Y, indicating...")
- Conclusion: Summarize the key difference, trend, or insight

BAD COMPARISON (AVOID):
"Document 1 contains revenue data for 2021. Document 2 contains revenue data for 2022. Document 1 has profit margins. Document 2 has expenses."

GOOD COMPARISON (FOLLOW):
"Comparing the financial performance across both documents: Document 1 (2021) shows revenue of X with profit margin Y, while Document 2 (2022) shows revenue of Z with profit margin W. This indicates a [trend/change/insight]. The key difference is..."

AUTOMATIC CHART GENERATION GUIDANCE:
- When discussing trends, comparisons, growth/decline, year-wise data, percentages, or quantitative analysis, mention that a chart/visualization will be shown
- For numerical data, provide a brief textual summary - charts will automatically display the detailed data
- For comparisons, briefly state the key findings - charts will show the visual comparison
- For trends over time, summarize the overall pattern - charts will show the detailed trend
- Do NOT include excessive numerical detail in text - let charts handle the visual representation
- Use phrases like "as shown in the chart below" or "the visualization illustrates" when charts are appropriate
- For follow-up questions like "show this in a graph" or "plot the same data", refer to the previous context and mention the chart will be generated

MULTI-DOCUMENT ATTRIBUTION FORMAT:
- When referencing information (NON-COMPARISON): "According to Document 1 [document_name], revenue was X. Document 2 [document_name] shows Y."
- For COMPARISON questions: Use comparative statements that link documents:
  * "Document 1 shows X, while Document 2 shows Y, indicating [insight/trend]"
  * "Comparing Document 1 (2021) with Document 2 (2022): Revenue increased from X to Y, representing a Z% growth"
  * "The key difference between Document 1 and Document 2 is [specific insight], with Document 1 focusing on [theme] while Document 2 emphasizes [different theme]"
  * "Document 1 demonstrates [pattern], whereas Document 2 reveals [contrasting pattern], suggesting [reasoning/insight]"

WEB SEARCH PRIORITY RULES:
- If the question asks about "latest", "current", "recent", "2024", "2025", or time-sensitive information, and "[Web Search Results]" section is present, use web search results as PRIMARY source
- For historical information or document-specific queries, prioritize "[Document Context]" section
- When both sources are available, clearly indicate which source you're using (e.g., "According to web search results..." or "Based on the uploaded document...")
- If web search results contain recent information (2024, 2025) and document only has older data (2022, 2023), prioritize web search for answering current questions

Context (may include Web Search Results and/or Document Context):
{context}

Question: {question}

Answer (use information from the context above, prioritize web search for current/recent information, use documents for historical data, with clear source attribution, and mention charts when appropriate):

IMPORTANT FOR COMPARISON QUESTIONS:
- If the question asks to "compare", "difference", "versus", "which is better/different", or similar:
  * DO NOT list documents independently - CONNECT them through comparative reasoning
  * Focus on HOW they differ, HOW they relate, and WHY it matters
  * End with a clear comparative conclusion
  * Be analytical, not descriptive
  * Avoid repetition and redundancy"""

RAG_ANSWER_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=RAG_ANSWER_PROMPT_TEMPLATE
)
