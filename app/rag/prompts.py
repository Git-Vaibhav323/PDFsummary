"""
Prompt templates for RAG and visualization detection.
"""
from langchain.prompts import PromptTemplate


# RAG Answer Generation Prompt
RAG_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based ONLY on the provided context from a PDF document.

CRITICAL RULES:
1. Answer STRICTLY from the provided context. Do NOT use any external knowledge.
2. If the answer is not in the context, respond with: "Not available in the uploaded document"
3. Do NOT make assumptions or hallucinate information.
4. If the context contains numerical data, tables, or trends, mention this in your answer.
5. Be precise and cite page numbers when available.
6. If asked for a summary, provide a comprehensive summary based on the context.

Context from PDF:
{context}

Question: {question}

Answer (based ONLY on the context above):"""

# Summary Generation Prompt
SUMMARY_PROMPT_TEMPLATE = """Based on the following context from a PDF document, provide a comprehensive summary.

CRITICAL RULES:
1. Summarize ONLY the information present in the provided context.
2. Do NOT add information that is not in the context.
3. Organize the summary logically (main topics, key points, conclusions).
4. Include important numerical data, dates, and facts if present.
5. Cite page numbers when available.

Context from PDF:
{context}

Provide a comprehensive summary of this document:"""

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=RAG_PROMPT_TEMPLATE
)


# Visualization Detection Prompt
VISUALIZATION_DETECTION_PROMPT_TEMPLATE = """Analyze the following question and retrieved context to determine if a visualization (chart/graph) would be helpful.

Consider creating a visualization if:
- The question asks about trends, comparisons, or distributions
- The context contains numerical data (percentages, counts, measurements)
- The context has tabular data or lists of numbers
- The question asks "how many", "what percentage", "compare", "show", "graph", "chart"

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
DATA_EXTRACTION_PROMPT_TEMPLATE = """Extract numerical data from the following context that is relevant to the question.

Question: {question}

Context:
{context}

Extract:
1. All numerical values mentioned
2. Labels/categories associated with numbers
3. Any time series data (dates, years, periods)
4. Any comparisons or relationships

Format your response as a JSON object with this structure:
{{
    "data_type": "bar|line|pie|table",
    "values": [list of numbers],
    "labels": [list of labels],
    "title": "Chart title",
    "x_axis": "X axis label",
    "y_axis": "Y axis label"
}}

If data cannot be extracted, return: {{"error": "No extractable data"}}"""

DATA_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["question", "context"],
    template=DATA_EXTRACTION_PROMPT_TEMPLATE
)

# Summary Prompt
SUMMARY_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=SUMMARY_PROMPT_TEMPLATE
)

