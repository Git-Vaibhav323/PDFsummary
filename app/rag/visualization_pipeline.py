"""
Optimized visualization pipeline for fast, deterministic chart generation.

Step 1: Visualization Detection
Step 2: Structured Data Extraction
Step 3: Chart Generation
Step 4: Response Assembly
"""
import logging
import json
from typing import Dict, Optional, List
from langchain_openai import ChatOpenAI
from app.config.settings import settings
from app.rag.prompts import (
    VISUALIZATION_DETECTION_PROMPT,
    DATA_EXTRACTION_PROMPT
)

logger = logging.getLogger(__name__)

# visualization_pipeline.py

def infer_chart_type(data):
    """
    Enterprise-safe heuristic chart inference.
    """
    if not data or not isinstance(data, list):
        return None

    numeric_values = [
        row.get("value")
        for row in data
        if isinstance(row.get("value"), (int, float))
    ]

    if len(numeric_values) >= 2:
        return "bar"

    if len(numeric_values) == 1:
        return "pie"

    return None

class VisualizationDetector:
    """Detects if visualization is needed for a question/context pair."""
    
    def __init__(self):
        """Initialize detector with gpt-4.1-mini."""
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0,
            api_key=settings.openai_api_key,
            max_retries=2
        )
    
    def should_visualize(self, question: str, context: str) -> bool:
        """
        Determine if visualization is needed - AUTOMATIC CHART GENERATION.
        
        Automatically detects when charts are appropriate based on:
        - Trends, comparisons, growth/decline patterns
        - Year-wise data, percentages, quantitative analysis
        - Financial metrics, numerical comparisons
        - Even if user doesn't explicitly ask for charts
        
        Args:
            question: User question
            context: Retrieved context
            
        Returns:
            True if visualization should be generated
        """
        if not context or context.strip() == "":
            logger.debug("No context, skipping visualization")
            return False
        
        # Quick heuristic checks first (no LLM call)
        question_lower = question.lower().strip()
        
        # CRITICAL: Explicit chart/graph/table requests - ALWAYS visualize
        explicit_chart_keywords = [
            'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
            'bar chart', 'line chart', 'pie chart', 'bar graph', 'line graph', 'pie graph',
            'show chart', 'display chart', 'give me chart', 'give me charts',
            'generate chart', 'create chart', 'plot', 'plotting', 'show this in a graph',
            'table', 'tables', 'tabular', 'show table', 'display table', 'tabular format',
            'financial charts', 'financial data', 'financial graphs'
        ]
        
        # Check for ANY explicit chart/table request
        if any(keyword in question_lower for keyword in explicit_chart_keywords):
            logger.info(f"✅ Explicit visualization request detected: '{question}'")
            return True
        
        # AUTOMATIC DETECTION: Chart-appropriate patterns (even without explicit request)
        chart_indicators = [
            # Trends and comparisons
            'trend', 'trends', 'trending', 'over time', 'across', 'between',
            'compare', 'comparison', 'compared', 'versus', 'vs', 'vs.',
            'growth', 'decline', 'increase', 'decrease', 'change', 'changes',
            'improve', 'improvement', 'deteriorate', 'deterioration',
            
            # Time-based patterns
            'year', 'years', 'yearly', 'yoy', 'year-over-year', 'annual',
            'quarter', 'quarters', 'quarterly', 'q1', 'q2', 'q3', 'q4',
            'month', 'months', 'monthly', 'period', 'periods',
            'fiscal year', 'fy', '2020', '2021', '2022', '2023', '2024', '2025',
            
            # Quantitative analysis
            'percentage', 'percent', '%', 'ratio', 'ratios', 'rate', 'rates',
            'metric', 'metrics', 'performance', 'analysis', 'analyses',
            'statistics', 'statistical', 'data', 'numbers', 'figures',
            
            # Financial terms (always trigger visualization)
            'revenue', 'profit', 'sales', 'cost', 'costs', 'expense', 'expenses',
            'income', 'earnings', 'margin', 'margins', 'ebitda', 'ebit',
            'asset', 'assets', 'liability', 'liabilities', 'equity',
            'balance sheet', 'income statement', 'cash flow', 'p&l', 'profit & loss',
            'financial', 'financially', 'financials', 'financial performance',
            'financial metrics', 'financial data', 'financial analysis',
            
            # Comparison patterns
            'higher', 'lower', 'better', 'worse', 'best', 'worst',
            'top', 'bottom', 'maximum', 'minimum', 'peak', 'lowest',
            'ranking', 'ranked', 'order', 'ordered'
        ]
        
        # Check if question contains chart-appropriate patterns
        has_chart_pattern = any(indicator in question_lower for indicator in chart_indicators)
        
        # Check if context has numerical data (more lenient threshold)
        import re
        numbers = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', context)
        percentages = re.findall(r'\d+(?:\.\d+)?%', context)
        has_numerical_data = len(numbers) >= 2 or len(percentages) >= 1
        
        # Check for year patterns in context
        year_patterns = re.findall(r'\b(20\d{2}|19\d{2})\b', context)
        has_years = len(year_patterns) >= 2
        
        # Check for comparison patterns in context
        comparison_keywords = ['compared', 'versus', 'vs', 'vs.', 'against', 'than', 'from', 'to']
        has_comparisons = any(keyword in context.lower() for keyword in comparison_keywords)
        
        # AUTOMATIC VISUALIZATION: Generate charts when appropriate patterns detected
        should_visualize = (
            has_chart_pattern or  # Question suggests chart
            (has_numerical_data and has_years) or  # Year-wise numerical data
            (has_numerical_data and has_comparisons) or  # Numerical comparisons
            (has_numerical_data and len(percentages) > 0) or  # Percentage data
            (has_numerical_data and len(numbers) >= 3)  # Multiple data points
        )
        
        if should_visualize:
            logger.info(f"✅ Automatic chart generation triggered: pattern={has_chart_pattern}, numbers={len(numbers)}, years={len(year_patterns)}, comparisons={has_comparisons}")
            return True
        
        logger.debug(f"No automatic visualization triggers: numbers={len(numbers)}, years={len(year_patterns)}")
        return False
    
    def detect_with_llm(self, question: str, context: str) -> bool:
        """
        Use LLM to detect visualization need.
        
        Args:
            question: User question
            context: Retrieved context
            
        Returns:
            True if visualization needed
        """
        try:
            prompt = VISUALIZATION_DETECTION_PROMPT.format(
                question=question,
                context=context[:2000]  # Limit context size for speed
            )
            
            response = self.llm.invoke(prompt)
            result = response.content.strip().upper()
            
            logger.debug(f"Visualization detection result: {result}")
            return "YES" in result
        
        except Exception as e:
            logger.warning(f"LLM visualization detection failed: {e}")
            return False


class DataExtractor:
    """Extracts chart-ready data from context."""
    
    def __init__(self):
        """Initialize extractor with gpt-4.1-mini."""
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0,
            api_key=settings.openai_api_key,
            max_retries=2
        )
    
    def extract_chart_data(self, question: str, context: str) -> Optional[Dict]:
        """
        Extract structured chart data from context.
        
        Args:
            question: User question
            context: Retrieved context
            
        Returns:
            Chart data dictionary or None
        """
        if not context or context.strip() == "":
            logger.warning("No context for data extraction")
            return None
        
        try:
            # Limit context to first 4000 chars for speed and cost
            context_limited = context[:4000]
            
            # Determine if user wants chart or table
            question_lower = question.lower()
            # CRITICAL: Check for chart requests first (including plural "charts")
            is_chart_request = any(kw in question_lower for kw in [
                'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
                'bar chart', 'line chart', 'pie chart', 'bar graph', 'line graph', 'pie graph',
                'show chart', 'display chart', 'give me chart', 'give me charts',
                'generate chart', 'create chart', 'plot', 'plotting'
            ])
            is_table_request = any(kw in question_lower for kw in [
                'table', 'tabular', 'show table', 'display table', 
                'trial balance', 'balance sheet', 'income statement',
                'show as table', 'display as table'
            ])
            
            logger.info(f"📊 Extraction request - Chart: {is_chart_request}, Table: {is_table_request}")
            
            # For generic "show me charts" requests, use Mistral to extract ALL financial data
            if (is_chart_request or is_table_request) and ('financial' in question_lower or 'charts' in question_lower or 'table' in question_lower):
                logger.info("🎯 Generic visualization request - extracting all financial data with Mistral")
                try:
                    import httpx
                    
                    mistral_prompt = f"""Extract ALL financial data from this document in JSON format.
                    
Document excerpt:
{context_limited}

Return a JSON object with multiple datasets for visualization:
{{
    "datasets": [
        {{
            "name": "Financial Summary",
            "type": "table",
            "headers": ["Item", "Amount"],
            "rows": [["item1", "value1"], ["item2", "value2"]]
        }},
        {{
            "name": "Revenue Breakdown",
            "type": "bar",
            "labels": ["Category1", "Category2"],
            "values": [100, 200],
            "title": "Revenue by Category"
        }},
        {{
            "name": "Profit Trend",
            "type": "line",
            "labels": ["Q1", "Q2", "Q3", "Q4"],
            "values": [1000, 1500, 1200, 1800],
            "title": "Quarterly Profit Trend"
        }}
    ]
}}

Extract real data from the document. For each dataset, determine the best visualization type.
Return ONLY valid JSON, no explanations."""

                    response = httpx.post(
                        "https://api.mistral.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.mistral_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "mistral-small-latest",
                            "messages": [{"role": "user", "content": mistral_prompt}],
                            "temperature": 0
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        mistral_data = response.json()
                        mistral_response = mistral_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        # Parse Mistral response
                        mistral_datasets = self._parse_json_response(mistral_response)
                        if mistral_datasets and "datasets" in mistral_datasets:
                            logger.info(f"✅ Mistral extracted {len(mistral_datasets.get('datasets', []))} datasets")
                            # Return first valid chart dataset (not table if chart requested)
                            datasets = mistral_datasets.get("datasets", [])
                            for dataset in datasets:
                                # Normalize: 'type' -> 'chart_type'
                                if 'type' in dataset and 'chart_type' not in dataset:
                                    dataset['chart_type'] = dataset.pop('type')
                                
                                chart_type = dataset.get('chart_type')
                                # If chart requested, skip tables and return first valid chart
                                if is_chart_request and chart_type == 'table':
                                    continue
                                # If chart type is valid, return this dataset
                                if chart_type in ['bar', 'line', 'pie', 'table', 'stacked_bar']:
                                    logger.info(f"✅ Returning dataset with chart_type={chart_type}")
                                    return dataset
                            
                            # Fallback: return first dataset if no valid one found
                            if datasets:
                                dataset = datasets[0]
                                if 'type' in dataset and 'chart_type' not in dataset:
                                    dataset['chart_type'] = dataset.pop('type')
                                logger.warning(f"No valid chart dataset found, returning first: chart_type={dataset.get('chart_type')}")
                                return dataset
                    
                except Exception as mistral_error:
                    logger.warning(f"Mistral extraction failed: {mistral_error}, falling back to LLM")
            
            # Fallback: Use OpenAI LLM for data extraction
            prompt = DATA_EXTRACTION_PROMPT.format(
                question=question,
                context=context_limited
            )
            
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Parse JSON response
            chart_data = self._parse_json_response(response_text)
            
            if not chart_data:
                logger.warning("Failed to parse chart data JSON, attempting generic extraction...")
                # Try to auto-generate chart from numbers in context
                return self._auto_extract_from_context(context_limited, is_chart_request)

            
            # CRITICAL: Enforce chart vs table distinction based on user request
            chart_type = chart_data.get('chart_type')
            
            # If user asked for CHART but got TABLE, convert table to chart
            if is_chart_request and chart_type == 'table':
                logger.warning("⚠️ User asked for CHART but got TABLE - converting to chart...")
                headers = chart_data.get('headers', [])
                rows = chart_data.get('rows', [])
                if headers and rows and len(headers) >= 2 and len(rows) > 0:
                    # Convert table to chart: extract account names and amounts
                    labels = []
                    values = []
                    
                    # Find Account column (usually first) and Amount columns (Debit/Credit)
                    account_col_idx = 0
                    amount_col_idx = None
                    
                    # Look for Account/Item/Description column
                    for idx, header in enumerate(headers):
                        if any(keyword in str(header).lower() for keyword in ['account', 'item', 'description', 'category', 'name']):
                            account_col_idx = idx
                            break
                    
                    # Find numeric column (Debit, Credit, Amount, Value)
                    for idx, header in enumerate(headers):
                        if idx != account_col_idx and any(keyword in str(header).lower() for keyword in ['debit', 'credit', 'amount', 'value', 'revenue', 'profit', 'sales', 'total']):
                            amount_col_idx = idx
                            break
                    
                    # If no amount column found, use first non-account column
                    if amount_col_idx is None:
                        for idx in range(len(headers)):
                            if idx != account_col_idx:
                                amount_col_idx = idx
                                break
                    
                    # Extract labels and values from rows
                    for row in rows:
                        if len(row) > account_col_idx:
                            # Get account name
                            account_name = str(row[account_col_idx]).strip()
                            # Clean account name
                            account_name = account_name.replace('$', '').replace('₹', '').replace('(', '').replace(')', '').strip()
                            
                            # Skip if account name is empty or is a separator
                            if not account_name or account_name == "-" or account_name.lower() in ['total', 'sum']:
                                continue
                            
                            # Get amount value
                            amount = 0
                            if amount_col_idx is not None and len(row) > amount_col_idx:
                                amount_str = str(row[amount_col_idx]).strip()
                                # Extract number from string (handle formats like "$1,100 (Bank)" or "1,100")
                                import re
                                # Remove text in parentheses
                                amount_str = re.sub(r'\([^)]*\)', '', amount_str)
                                # Extract number
                                number_match = re.search(r'[\d,]+\.?\d*', amount_str.replace(',', ''))
                                if number_match:
                                    try:
                                        amount = float(number_match.group(0))
                                    except:
                                        amount = 0
                            
                            # Only add if we have both label and value
                            if account_name and amount > 0:
                                labels.append(account_name)
                                values.append(amount)
                    
                    # If we still don't have enough data, try combining Debit and Credit
                    if len(labels) < 2 and len(headers) >= 3:
                        # Try to find Debit and Credit columns separately
                        debit_col = None
                        credit_col = None
                        for idx, header in enumerate(headers):
                            if 'debit' in str(header).lower():
                                debit_col = idx
                            elif 'credit' in str(header).lower():
                                credit_col = idx
                        
                        if debit_col is not None or credit_col is not None:
                            labels = []
                            values = []
                            for row in rows:
                                if len(row) > account_col_idx:
                                    account_name = str(row[account_col_idx]).strip()
                                    if not account_name or account_name == "-":
                                        continue
                                    
                                    # Get debit value
                                    debit_val = 0
                                    if debit_col and len(row) > debit_col:
                                        debit_str = str(row[debit_col]).replace(',', '').replace('$', '').strip()
                                        try:
                                            debit_val = float(debit_str) if debit_str and debit_str != "-" else 0
                                        except:
                                            debit_val = 0
                                    
                                    # Get credit value
                                    credit_val = 0
                                    if credit_col and len(row) > credit_col:
                                        credit_str = str(row[credit_col]).replace(',', '').replace('$', '').strip()
                                        try:
                                            credit_val = float(credit_str) if credit_str and credit_str != "-" else 0
                                        except:
                                            credit_val = 0
                                    
                                    # Use the larger value (or sum if both exist)
                                    total_val = debit_val + credit_val if (debit_val > 0 and credit_val > 0) else (debit_val if debit_val > 0 else credit_val)
                                    
                                    if account_name and total_val > 0:
                                        labels.append(account_name)
                                        values.append(total_val)
                    
                    # Filter out zero values
                    if any(v != 0 for v in values):
                        filtered = [(l, v) for l, v in zip(labels, values) if v != 0]
                        labels = [l for l, v in filtered]
                        values = [v for l, v in filtered]
                    
                    if len(labels) >= 2 and len(values) >= 2 and len(labels) == len(values):
                        chart_data = {
                            "chart_type": "bar",  # Default to bar for financial comparisons
                            "labels": labels,
                            "values": values,
                            "title": chart_data.get('title', 'Financial Analysis Chart'),
                            "x_axis": headers[account_col_idx] if account_col_idx < len(headers) else "Account",
                            "y_axis": "Amount"
                        }
                        logger.info(f"✅ Converted table to chart: {len(labels)} data points")
                    else:
                        logger.warning(f"Failed to convert table to chart - insufficient data: {len(labels)} labels, {len(values)} values")
            
            # If user asked for TABLE but got CHART, keep as chart but log preference
            if is_table_request and chart_type in ['bar', 'line', 'pie']:
                logger.warning(f"⚠️ User asked for TABLE but got {chart_type.upper()} - keeping as requested type")
                # For now, we'll keep it as chart since user might want to see the data visually
                # In future, we could try to reconstruct table from chart data
            
            # Validate extracted data
            if not self._validate_chart_data(chart_data):
                logger.warning("Extracted data failed validation")
                return None
            
            logger.info(f"✅ Extracted chart data: type={chart_data.get('chart_type')}")
            return chart_data
        
        except Exception as e:
            logger.error(f"Error extracting chart data: {e}")
            return None
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse JSON from LLM response.
        
        Args:
            response_text: LLM response text
            
        Returns:
            Parsed dictionary or None
        """
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(f"JSON parsing failed for: {response_text[:200]}")
            return None
    
    def _validate_chart_data(self, data: Dict) -> bool:
        """
        Validate chart data structure.
        
        Args:
            data: Chart data dictionary
            
        Returns:
            True if valid
        """
        if not isinstance(data, dict):
            logger.warning("Data is not a dictionary")
            return False
        
        # Check for error response
        if data.get("error"):
            logger.warning(f"Data extraction returned error: {data.get('error')}")
            return False
        
        chart_type = data.get("chart_type")
        if not chart_type or chart_type not in ["bar", "line", "pie", "table"]:
            logger.warning(f"Invalid chart_type: {chart_type}")
            return False
        
        # Validate by type
        if chart_type == "table":
            headers = data.get("headers", [])
            rows = data.get("rows", [])
            
            if not headers or len(headers) < 2:
                logger.warning("Table missing valid headers")
                return False
            
            if not rows or not isinstance(rows, list):
                logger.warning("Table missing valid rows")
                return False
            
            # Check row structure
            for i, row in enumerate(rows):
                if not isinstance(row, list) or len(row) != len(headers):
                    logger.warning(f"Row {i} has incorrect column count")
                    return False
            
            return True
        
        else:  # bar, line, pie
            labels = data.get("labels", [])
            values = data.get("values", [])
            
            if not isinstance(labels, list) or len(labels) < 2:
                logger.warning("Invalid labels")
                return False
            
            if not isinstance(values, list) or len(values) < 2:
                logger.warning("Invalid values")
                return False
            
            if len(labels) != len(values):
                logger.warning("Labels and values length mismatch")
                return False
            
            # Check all values are numeric
            for v in values:
                try:
                    float(str(v).replace(',', ''))
                except ValueError:
                    logger.warning(f"Non-numeric value: {v}")
                    return False
            
            return True


class ChartGenerator:
    """Generate chart objects from structured data."""
    
    @staticmethod
    def generate_chart(chart_data: Dict, is_chart_request: bool = False) -> Optional[Dict]:
        """
        Generate chart object for frontend rendering.
        
        Args:
            chart_data: Structured chart data
            is_chart_request: Whether user explicitly requested chart
            
        Returns:
            Chart object or None
        """
        if not chart_data:
            return None
        
        chart_type = chart_data.get("chart_type")
        
        # CRITICAL: NEVER return table when chart requested
        if chart_type == "table":
            if is_chart_request:
                logger.error("❌ CRITICAL: ChartGenerator attempted to return table when chart requested - BLOCKED")
                return None  # Return None to trigger error handling upstream
            # Only return table if NOT a chart request
            return {
                "type": "table",
                "title": chart_data.get("title", ""),
                "headers": chart_data.get("headers", []),
                "rows": chart_data.get("rows", [])
            }
        
        elif chart_type == "bar":
            return ChartGenerator._generate_bar_chart(chart_data)
        
        elif chart_type == "line":
            return ChartGenerator._generate_line_chart(chart_data)
        
        elif chart_type == "pie":
            return ChartGenerator._generate_pie_chart(chart_data)
        
        elif chart_type == "stacked_bar":
            return ChartGenerator._generate_stacked_bar_chart(chart_data)
        
        return None
    
    @staticmethod
    def _generate_bar_chart(data: Dict) -> Dict:
        """Generate bar chart for category comparison."""
        return {
            "type": "bar",
            "title": data.get("title", ""),
            "labels": data.get("labels", []),
            "values": data.get("values", []),
            "xAxis": data.get("x_axis", "Category"),
            "yAxis": data.get("y_axis", "Value")
        }
    
    @staticmethod
    def _generate_line_chart(data: Dict) -> Dict:
        """Generate line chart for time-series."""
        return {
            "type": "line",
            "title": data.get("title", ""),
            "labels": data.get("labels", []),
            "values": data.get("values", []),
            "xAxis": data.get("x_axis", "Time"),
            "yAxis": data.get("y_axis", "Value")
        }
    
    @staticmethod
    def _generate_pie_chart(data: Dict) -> Dict:
        """Generate pie chart for proportions."""
        return {
            "type": "pie",
            "title": data.get("title", ""),
            "labels": data.get("labels", []),
            "values": data.get("values", [])
        }


class VisualizationPipeline:
    """Complete visualization pipeline with financial domain awareness."""
    
    def __init__(self):
        """Initialize pipeline components."""
        self.detector = VisualizationDetector()
        self.extractor = DataExtractor()
        self.generator = ChartGenerator()
        
        # Financial domain components
        from app.rag.financial_detector import FinancialDocumentDetector
        from app.rag.financial_normalizer import FinancialDataNormalizer
        
        self.financial_detector = FinancialDocumentDetector()
        self.financial_normalizer = FinancialDataNormalizer()
    
    def process(self, question: str, context: str, answer: str) -> Dict:
        """
        Complete visualization pipeline.
        
        Args:
            question: User question
            context: Retrieved context
            answer: Generated answer
            
        Returns:
            Dictionary with visualization if applicable
        """
        logger.info("Starting visualization pipeline")
        logger.info(f"Question: {question[:100]}")
        logger.info(f"Context length: {len(context)} chars")
        
        # Step 1: Detection
        if not self.detector.should_visualize(question, context):
            logger.debug("Visualization not needed")
            return {}
        
        logger.debug("Visualization detection passed")
        
        # CRITICAL: Check if user explicitly asked for chart (not table)
        question_lower = question.lower()
        is_chart_request = any(kw in question_lower for kw in [
            'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
            'bar chart', 'line chart', 'pie chart', 'bar graph', 'line graph', 'pie graph',
            'show chart', 'display chart', 'give me chart', 'give me charts',
            'generate chart', 'create chart', 'plot', 'plotting'
        ])
        is_table_request = any(kw in question_lower for kw in [
            'table', 'tabular', 'show table', 'display table', 
            'trial balance', 'balance sheet', 'income statement',
            'show as table', 'display as table'
        ])
        
        logger.info(f"📊 User request - Chart: {is_chart_request}, Table: {is_table_request}")
        
        # STEP 1: FINANCIAL DOCUMENT TYPE DETECTION (MANDATORY)
        financial_doc_type = self.financial_detector.detect(question, context)
        logger.info(f"📄 Financial document type: {financial_doc_type.value}")
        
        # Step 2: Data extraction
        chart_data = self.extractor.extract_chart_data(question, context)
        
        if not chart_data:
            logger.warning("Failed to extract chart data - trying fallback extraction")
            # FALLBACK: Try to extract table directly from context (only if table requested)
            if is_table_request or "table" in question.lower() or financial_doc_type.value != "generic_financial":
                logger.info("Attempting fallback table extraction from context...")
                chart_data = self._extract_table_fallback(context)
                # Normalize extracted table
                if chart_data and chart_data.get("chart_type") == "table":
                    from app.rag.table_normalizer import TableNormalizer
                    chart_data = TableNormalizer.normalize_table_data(chart_data)
        
        if not chart_data:
            logger.debug("Failed to extract chart data (including fallback)")
            # If chart requested, try financial normalization even without structured data
            if is_chart_request:
                logger.info("Attempting financial normalization from context...")
                normalized = self.financial_normalizer.normalize(
                    financial_doc_type,
                    {},
                    context
                )
                if normalized:
                    chart_data = normalized
                else:
                    return {
                        "error": "No structured financial data available to generate a chart."
                    }
            else:
                return {}
        
        logger.info(f"Extracted chart data: type={chart_data.get('chart_type')}")
        
        # STEP 2: DOMAIN-AWARE DATA NORMALIZATION (CRITICAL)
        # CRITICAL: If chart requested and we have table data, ALWAYS normalize
        if is_chart_request and chart_data.get('chart_type') == 'table':
            logger.info(f"🔄 CRITICAL: Chart requested but got table - forcing normalization for {financial_doc_type.value}")
            normalized = self.financial_normalizer.normalize(
                financial_doc_type,
                chart_data,
                context
            )
            
            if normalized and normalized.get('chart_type') != 'table':
                chart_data = normalized
                logger.info(f"✅ Financial normalization successful: {chart_data.get('chart_type')}")
            else:
                # Normalization failed or still returned table - try universal converter
                logger.warning("⚠️ Financial normalization failed or returned table - trying universal converter...")
                converted = self._universal_table_to_chart_converter(chart_data)
                
                if converted and converted.get('chart_type') != 'table':
                    chart_data = converted
                    logger.info(f"✅ Universal conversion successful: {chart_data.get('chart_type')}")
                else:
                    logger.error("❌ CRITICAL: All conversion attempts failed")
                    return {
                        "error": "No structured financial data available to generate a chart."
                    }
        elif chart_data.get('chart_type') == 'table' and financial_doc_type.value != "generic_financial":
            # Optional normalization for non-chart requests
            logger.info(f"🔄 Normalizing financial data for {financial_doc_type.value}")
            normalized = self.financial_normalizer.normalize(
                financial_doc_type,
                chart_data,
                context
            )
            if normalized:
                chart_data = normalized
        
        # CRITICAL: If user asked for CHART but got TABLE, force conversion (fallback)
        if is_chart_request and chart_data.get('chart_type') == 'table':
            logger.warning("⚠️ User asked for CHART but got TABLE - forcing conversion to chart...")
            headers = chart_data.get('headers', [])
            rows = chart_data.get('rows', [])
            if headers and rows and len(headers) >= 2 and len(rows) > 0:
                # Convert table to chart
                labels = []
                values = []
                
                # Find Account column and Amount columns
                account_col_idx = 0
                for idx, header in enumerate(headers):
                    if any(keyword in str(header).lower() for keyword in ['account', 'item', 'description', 'category', 'name']):
                        account_col_idx = idx
                        break
                
                # Extract labels and values, handling Debit/Credit columns
                for row in rows:
                    if len(row) > account_col_idx:
                        account_name = str(row[account_col_idx]).strip()
                        account_name = account_name.replace('$', '').replace('₹', '').replace('(', '').replace(')', '').strip()
                        
                        if not account_name or account_name == "-" or account_name.lower() in ['total', 'sum']:
                            continue
                        
                        # For financial data with Debit/Credit, combine them
                        amount = 0
                        if len(headers) >= 3 and 'debit' in str(headers[1]).lower() and 'credit' in str(headers[2]).lower():
                            debit_val = 0
                            credit_val = 0
                            if len(row) > 1:
                                debit_str = str(row[1]).replace(',', '').replace('$', '').strip()
                                try:
                                    debit_val = float(debit_str) if debit_str and debit_str != "-" else 0
                                except:
                                    debit_val = 0
                            if len(row) > 2:
                                credit_str = str(row[2]).replace(',', '').replace('$', '').strip()
                                try:
                                    credit_val = float(credit_str) if credit_str and credit_str != "-" else 0
                                except:
                                    credit_val = 0
                            amount = debit_val + credit_val if (debit_val > 0 or credit_val > 0) else (debit_val if debit_val > 0 else credit_val)
                        else:
                            # Single amount column
                            amount_col_idx = 1 if len(headers) > 1 else None
                            if amount_col_idx and len(row) > amount_col_idx:
                                amount_str = str(row[amount_col_idx]).strip()
                                import re
                                amount_str = re.sub(r'\([^)]*\)', '', amount_str)
                                number_match = re.search(r'[\d,]+\.?\d*', amount_str.replace(',', ''))
                                if number_match:
                                    try:
                                        amount = float(number_match.group(0))
                                    except:
                                        amount = 0
                        
                        if account_name and amount > 0:
                            labels.append(account_name)
                            values.append(amount)
                
                # Filter out zero values
                if any(v != 0 for v in values):
                    filtered = [(l, v) for l, v in zip(labels, values) if v != 0]
                    labels = [l for l, v in filtered]
                    values = [v for l, v in filtered]
                
                if len(labels) >= 2 and len(values) >= 2 and len(labels) == len(values):
                    # Ensure values are numeric
                    numeric_values = []
                    for v in values:
                        try:
                            numeric_values.append(float(v))
                        except (ValueError, TypeError):
                            logger.warning(f"Skipping non-numeric value: {v}")
                            continue
                    
                    # Re-align labels with numeric values
                    if len(numeric_values) >= 2 and len(numeric_values) == len(labels):
                        chart_data = {
                            "chart_type": "bar",
                            "labels": labels,
                            "values": numeric_values,
                            "title": chart_data.get('title', 'Financial Analysis Chart'),
                            "x_axis": headers[account_col_idx] if account_col_idx < len(headers) else "Account",
                            "y_axis": "Amount"
                        }
                        logger.info(f"✅ Converted table to chart: {len(labels)} data points")
                    else:
                        logger.error(f"❌ Failed to convert - insufficient numeric values: {len(numeric_values)} values, {len(labels)} labels")
                        if is_chart_request:
                            return {
                                "error": "No structured financial data available to generate a chart."
                            }
                else:
                    logger.error(f"❌ Failed to convert table to chart - insufficient data: {len(labels)} labels, {len(values)} values")
                    if is_chart_request:
                        return {
                            "error": "No structured financial data available to generate a chart."
                        }
        
        # CRITICAL: If chart requested, enforce strict contract BEFORE generation
        if is_chart_request:
            # Validate chart_data has required fields
            chart_type = chart_data.get('chart_type')
            labels = chart_data.get('labels', [])
            values = chart_data.get('values', [])
            
            # If we have table data, conversion should have happened above
            if chart_type == 'table':
                logger.error("❌ CRITICAL: Chart requested but still have table data - conversion failed")
                return {
                    "error": "No structured financial data available to generate a chart."
                }
            
            # Validate chart data structure - MUST be valid chart type (NOT table)
            if not chart_type or chart_type not in ['bar', 'line', 'pie', 'stacked_bar']:
                logger.error(f"❌ Invalid chart_type: {chart_type} - must be bar/line/pie/stacked_bar, NOT table")
                return {
                    "error": "No structured financial data available to generate a chart."
                }
            
            if not labels or not isinstance(labels, list) or len(labels) < 2:
                logger.error(f"❌ Invalid labels: {labels}")
                return {
                    "error": "No structured financial data available to generate a chart."
                }
            
            if not values or not isinstance(values, list) or len(values) < 2:
                logger.error(f"❌ Invalid values: {values}")
                return {
                    "error": "No structured financial data available to generate a chart."
                }
            
            if len(labels) != len(values):
                logger.error(f"❌ Labels/values length mismatch: {len(labels)} vs {len(values)}")
                return {
                    "error": "No structured financial data available to generate a chart."
                }
            
            # Ensure values are numeric
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except (ValueError, TypeError):
                    logger.warning(f"Non-numeric value: {v}")
                    return {
                        "error": "No structured financial data available to generate a chart."
                    }
            
            # Update chart_data with numeric values
            chart_data['values'] = numeric_values
        
        # Step 3: Chart generation
        try:
            # CRITICAL: If chart requested, ensure we don't generate table
            if is_chart_request and chart_data.get('chart_type') == 'table':
                logger.error("❌ CRITICAL: Attempting to generate table when chart requested")
                return {
                    "error": "No structured financial data available to generate a chart."
                }
            
            # CRITICAL: Pass is_chart_request to generator to block table output
            chart = self.generator.generate_chart(chart_data, is_chart_request=is_chart_request)
            
            if not chart:
                logger.error("❌ Chart generation returned None")
                if is_chart_request:
                    return {
                        "error": "No structured financial data available to generate a chart."
                    }
                return {}
            
            # CRITICAL: If chart requested, ensure result is NOT a table
            if is_chart_request:
                if chart.get('type') == 'table':
                    logger.error("❌ CRITICAL: ChartGenerator returned table when chart requested")
                    return {
                        "error": "No structured financial data available to generate a chart."
                    }
                
                # Validate chart has required fields
                if not chart.get('labels') or not chart.get('values'):
                    logger.error(f"❌ Chart missing labels/values: {chart}")
                    return {
                        "error": "No structured financial data available to generate a chart."
                    }
            
            # Check for errors in chart
            if isinstance(chart, dict) and "error" in chart:
                logger.error(f"❌ Chart generation returned error: {chart.get('error')}")
                if is_chart_request:
                    return {
                        "error": "No structured financial data available to generate a chart."
                    }
                return {}
            
            logger.info(f"✅ Generated {chart.get('type')} chart successfully")
            logger.info(f"Chart data: type={chart.get('type')}, has_labels={bool(chart.get('labels'))}, has_values={bool(chart.get('values'))}")
            
            # Step 4: Return visualization
            result = {
                "chart": chart,
                "extracted_data": chart_data
            }
            
            logger.info(f"✅ Returning visualization result: {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"❌ Error in chart generation: {e}", exc_info=True)
            if is_chart_request:
                return {
                    "error": "No structured financial data available to generate a chart."
                }
            return {}
    
    def _extract_table_fallback(self, context: str) -> Optional[Dict]:
        """Fallback method to extract table data directly from context."""
        try:
            import re
            lines = context.split('\n')
            headers = []
            rows = []
            in_table = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for header row (Account, Debit, Credit pattern)
                if re.search(r'(Account|Item|Description).*(Debit|Credit|Amount)', line, re.IGNORECASE):
                    # Extract headers - split by multiple spaces, tabs, or pipes
                    parts = re.split(r'\s{2,}|\t|\|', line)
                    headers = [p.strip() for p in parts if p.strip()]
                    in_table = True
                    logger.info(f"Found table headers: {headers}")
                    continue
                
                if in_table and headers:
                    # Skip separator rows
                    if re.match(r'^[\s\|:\-]+$', line):
                        continue
                    
                    # Extract data rows - split by multiple spaces, tabs, or pipes
                    parts = re.split(r'\s{2,}|\t+\|?\s*|\|', line)
                    parts = [p.strip() for p in parts if p.strip()]
                    
                    if len(parts) >= 1:  # At least one column
                        # CRITICAL FIX: Handle rows where account name might be in wrong position
                        # Look for pattern: "-" followed by account name followed by amount
                        row = []
                        
                        # If first part is "-" and we have account name in second position
                        if len(parts) >= 2 and parts[0] == "-" and not re.match(r'^[\d,.\-]+$', parts[1]):
                            # Account name is in second position, move it to first
                            # Structure: ["-", "AccountName", "Amount"] -> ["AccountName", "Amount", "-"]
                            account_name = parts[1]
                            amounts = parts[2:] if len(parts) > 2 else []
                            
                            # Build row: [AccountName, Debit, Credit] or [AccountName, Amount]
                            row = [account_name]
                            
                            # Add amounts (could be Debit, Credit, or single Amount)
                            for i, amount in enumerate(amounts):
                                if i < len(headers) - 1:  # -1 because first column is Account
                                    row.append(amount)
                            
                            # Fill remaining columns with "-"
                            while len(row) < len(headers):
                                row.append("-")
                        else:
                            # Normal row extraction
                            for i in range(len(headers)):
                                if i < len(parts):
                                    row.append(parts[i])
                                else:
                                    row.append("-")
                        
                        # Clean up row data
                        cleaned_row = []
                        for cell in row:
                            cell_clean = str(cell).strip()
                            # Remove markdown formatting
                            cell_clean = re.sub(r'\*\*|\*', '', cell_clean)
                            cleaned_row.append(cell_clean if cell_clean else "-")
                        
                        # Skip rows that are all dashes or separators
                        if any(cell and cell != '-' and not re.match(r'^[\s\-:]+$', cell) for cell in cleaned_row):
                            rows.append(cleaned_row)
                            logger.debug(f"Added row: {cleaned_row}")
            
            if headers and rows and len(headers) >= 2:
                logger.info(f"✅ Fallback extraction successful: {len(headers)} columns, {len(rows)} rows")
                # Normalize table structure
                from app.rag.table_normalizer import TableNormalizer
                normalized = TableNormalizer.normalize_table(headers, rows, "Trial Balance")
                return {
                    "chart_type": "table",
                    "headers": normalized["headers"],
                    "rows": normalized["rows"],
                    "title": normalized["title"]
                }
            else:
                logger.warning(f"Fallback extraction incomplete: {len(headers)} headers, {len(rows)} rows")
                return None
        except Exception as e:
            logger.error(f"Fallback table extraction failed: {e}")
            return None
    
    def _universal_table_to_chart_converter(self, table_data: Dict) -> Optional[Dict]:
        """
        Universal financial table → chart converter.
        
        Applies universal rules:
        a) If Debit & Credit columns → bar chart with max(debit, credit)
        b) If single Amount column → bar chart
        c) If Assets/Liabilities/Equity → pie chart
        
        Args:
            table_data: Table data with headers and rows
            
        Returns:
            Chart data or None if conversion fails
        """
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        if not headers or not rows:
            return None
        
        headers_lower = [str(h).lower() for h in headers]
        
        # Rule a: Debit & Credit columns
        debit_idx = None
        credit_idx = None
        for idx, header in enumerate(headers_lower):
            if 'debit' in header:
                debit_idx = idx
            elif 'credit' in header:
                credit_idx = idx
        
        if debit_idx is not None and credit_idx is not None:
            # Find account column
            account_idx = 0
            for idx, header in enumerate(headers_lower):
                if any(kw in header for kw in ['account', 'item', 'description', 'name']):
                    account_idx = idx
                    break
            
            labels = []
            values = []
            
            for row in rows:
                if len(row) <= account_idx:
                    continue
                
                account = str(row[account_idx]).strip()
                if not account or account.lower() in ['total', 'sum', '-', '']:
                    continue
                
                debit_val = self._parse_table_amount(row[debit_idx]) if debit_idx < len(row) else 0
                credit_val = self._parse_table_amount(row[credit_idx]) if credit_idx < len(row) else 0
                
                # Use max(debit, credit) as value
                value = max(debit_val, credit_val)
                
                if value > 0:
                    labels.append(account)
                    values.append(value)
            
            if len(labels) >= 2:
                return {
                    "chart_type": "bar",
                    "labels": labels,
                    "values": values,
                    "title": table_data.get('title', 'Financial Chart'),
                    "x_axis": headers[account_idx] if account_idx < len(headers) else "Account",
                    "y_axis": "Amount"
                }
        
        # Rule b: Single Amount column
        amount_idx = None
        for idx, header in enumerate(headers_lower):
            if any(kw in header for kw in ['amount', 'value', 'total', 'balance']):
                amount_idx = idx
                break
        
        if amount_idx is not None:
            label_idx = 0 if amount_idx != 0 else (1 if len(headers) > 1 else 0)
            
            labels = []
            values = []
            
            for row in rows:
                if len(row) <= max(label_idx, amount_idx):
                    continue
                
                label = str(row[label_idx]).strip()
                if not label or label.lower() in ['total', 'sum', '-', '']:
                    continue
                
                value = self._parse_table_amount(row[amount_idx])
                
                if value > 0:
                    labels.append(label)
                    values.append(value)
            
            if len(labels) >= 2:
                return {
                    "chart_type": "bar",
                    "labels": labels,
                    "values": values,
                    "title": table_data.get('title', 'Financial Chart'),
                    "x_axis": headers[label_idx] if label_idx < len(headers) else "Category",
                    "y_axis": "Amount"
                }
        
        # Rule c: Assets/Liabilities/Equity
        category_idx = None
        for idx, header in enumerate(headers_lower):
            if any(kw in header for kw in ['account', 'item', 'category', 'description']):
                category_idx = idx
                break
        
        if category_idx is not None:
            amount_idx = None
            for idx, header in enumerate(headers_lower):
                if any(kw in header for kw in ['amount', 'value', 'total', 'balance']):
                    amount_idx = idx
                    break
            
            if amount_idx is not None:
                categories = {'assets': [], 'liabilities': [], 'equity': []}
                
                for row in rows:
                    if len(row) <= max(category_idx, amount_idx):
                        continue
                    
                    category = str(row[category_idx]).lower()
                    amount = self._parse_table_amount(row[amount_idx])
                    
                    if amount > 0:
                        if any(kw in category for kw in ['asset', 'property', 'equipment', 'inventory', 'cash']):
                            categories['assets'].append(amount)
                        elif any(kw in category for kw in ['liability', 'debt', 'payable', 'loan']):
                            categories['liabilities'].append(amount)
                        elif any(kw in category for kw in ['equity', 'capital', 'share', 'retained']):
                            categories['equity'].append(amount)
                
                labels = []
                values = []
                
                if sum(categories['assets']) > 0:
                    labels.append("Assets")
                    values.append(sum(categories['assets']))
                if sum(categories['liabilities']) > 0:
                    labels.append("Liabilities")
                    values.append(sum(categories['liabilities']))
                if sum(categories['equity']) > 0:
                    labels.append("Equity")
                    values.append(sum(categories['equity']))
                
                if len(labels) >= 2:
                    return {
                        "chart_type": "pie",
                        "labels": labels,
                        "values": values,
                        "title": table_data.get('title', 'Balance Sheet'),
                        "x_axis": "Category",
                        "y_axis": "Amount"
                    }
        
        return None
    
    def _parse_table_amount(self, value: any) -> float:
        """Parse amount from various formats."""
        if value is None:
            return 0.0
        
        import re
        value_str = str(value).strip()
        value_str = re.sub(r'[()₹$Rs.,\s]', '', value_str)
        value_str = re.sub(r'\([^)]*\)', '', value_str)
        
        number_match = re.search(r'[\d]+\.?\d*', value_str)
        if number_match:
            try:
                return float(number_match.group(0))
            except ValueError:
                return 0.0
        
        return 0.0
