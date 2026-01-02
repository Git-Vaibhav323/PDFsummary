"""
Markdown table generation and standardization.

Ensures all tables follow enterprise standards:
- Valid Markdown syntax
- One header row
- One separator row
- Equal column count
- Right-aligned numeric columns
- No ASCII borders
- No explanatory text inside tables
"""
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class MarkdownTableGenerator:
    """Generate clean, standardized Markdown tables."""
    
    @staticmethod
    def is_numeric(value: str) -> bool:
        """Check if value is numeric."""
        if not value or not isinstance(value, str):
            return False
        
        value = value.strip()
        if not value:
            return False
        
        # Remove common numeric formatting
        cleaned = value.replace(',', '').replace('$', '').replace('%', '').strip()
        
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def format_cell(value: str, is_numeric: bool = False) -> str:
        """
        Format a table cell value.
        
        Args:
            value: Cell value
            is_numeric: Whether to format as number
            
        Returns:
            Formatted cell value
        """
        if not value:
            return ""
        
        value = str(value).strip()
        
        # Remove explanatory text (keep only the value)
        if '(' in value and ')' in value:
            # Extract content within parentheses separately if it's a note
            parts = value.split('(')
            value = parts[0].strip()
        
        return value
    
    @staticmethod
    def generate_table(headers: List[str], 
                       rows: List[List[str]],
                       title: Optional[str] = None) -> str:
        """
        Generate a standardized Markdown table.
        
        Args:
            headers: List of column headers
            rows: List of rows, each row is a list of values
            title: Optional table title (rendered above table)
            
        Returns:
            Markdown table string
        """
        if not headers or not rows:
            logger.warning("Cannot generate table: missing headers or rows")
            return ""
        
        # Validate input
        if not isinstance(headers, list) or len(headers) < 2:
            logger.warning("Table needs at least 2 columns")
            return ""
        
        if not isinstance(rows, list) or len(rows) < 1:
            logger.warning("Table needs at least 1 row")
            return ""
        
        # Ensure all rows have correct column count
        for i, row in enumerate(rows):
            if len(row) != len(headers):
                logger.warning(f"Row {i} has {len(row)} columns, expected {len(headers)}")
                return ""
        
        # Determine which columns are numeric
        numeric_cols = MarkdownTableGenerator._detect_numeric_columns(headers, rows)
        
        # Build table
        lines = []
        
        # Add title if provided
        if title:
            lines.append(f"**{title}**")
            lines.append("")
        
        # Header row
        header_line = "| " + " | ".join(headers) + " |"
        lines.append(header_line)
        
        # Separator row with alignment
        separator_parts = []
        for i, header in enumerate(headers):
            if numeric_cols[i]:
                # Right-align for numeric columns
                separator_parts.append("-:")
            else:
                # Left-align for text columns
                separator_parts.append(":--")
        
        separator_line = "|" + "|".join(separator_parts) + "|"
        lines.append(separator_line)
        
        # Data rows
        for row in rows:
            formatted_row = []
            for i, value in enumerate(row):
                formatted_value = MarkdownTableGenerator.format_cell(
                    str(value), 
                    is_numeric=numeric_cols[i]
                )
                formatted_row.append(formatted_value)
            
            row_line = "| " + " | ".join(formatted_row) + " |"
            lines.append(row_line)
        
        table_string = "\n".join(lines)
        logger.info(f"Generated Markdown table: {len(headers)} columns, {len(rows)} rows")
        
        return table_string
    
    @staticmethod
    def _detect_numeric_columns(headers: List[str], rows: List[List[str]]) -> List[bool]:
        """
        Detect which columns contain numeric data.
        
        Args:
            headers: Column headers
            rows: Data rows
            
        Returns:
            List of boolean indicating if each column is numeric
        """
        numeric_cols = [True] * len(headers)
        
        # Check first few rows to determine column types
        sample_size = min(5, len(rows))
        
        for col_idx in range(len(headers)):
            for row_idx in range(sample_size):
                if row_idx < len(rows) and col_idx < len(rows[row_idx]):
                    value = str(rows[row_idx][col_idx]).strip()
                    if value and not MarkdownTableGenerator.is_numeric(value):
                        numeric_cols[col_idx] = False
                        break
        
        return numeric_cols
    
    @staticmethod
    def generate_from_dict_rows(headers: List[str],
                                rows: List[Dict],
                                title: Optional[str] = None) -> str:
        """
        Generate table from list of dictionaries.
        
        Args:
            headers: Column headers (keys to extract from dicts)
            rows: List of dictionaries
            title: Optional table title
            
        Returns:
            Markdown table string
        """
        # Convert dict rows to list rows
        list_rows = []
        for row_dict in rows:
            row_list = [str(row_dict.get(header, "")) for header in headers]
            list_rows.append(row_list)
        
        return MarkdownTableGenerator.generate_table(headers, list_rows, title)
    
    @staticmethod
    def validate_table_structure(headers: List[str], 
                                 rows: List[List[str]]) -> Tuple[bool, str]:
        """
        Validate table structure.
        
        Args:
            headers: Column headers
            rows: Data rows
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not headers:
            return False, "Headers are required"
        
        if len(headers) < 2:
            return False, "Table must have at least 2 columns"
        
        if not rows:
            return False, "Table must have at least 1 row"
        
        if len(rows) < 1:
            return False, "Table must have at least 1 row"
        
        for i, row in enumerate(rows):
            if not isinstance(row, list):
                return False, f"Row {i} is not a list"
            
            if len(row) != len(headers):
                return False, f"Row {i} has {len(row)} columns, expected {len(headers)}"
        
        return True, ""


class TableExtractor:
    """Extract tables from structured data."""
    
    @staticmethod
    def extract_from_chart_data(chart_data: Dict) -> Optional[str]:
        """
        Extract table representation from chart data.
        
        Args:
            chart_data: Chart data with labels and values
            
        Returns:
            Markdown table string or None
        """
        if chart_data.get("chart_type") == "table":
            # Already in table format
            headers = chart_data.get("headers", [])
            rows = chart_data.get("rows", [])
            
            if headers and rows:
                return MarkdownTableGenerator.generate_table(
                    headers,
                    rows,
                    title=chart_data.get("title")
                )
        
        # Convert chart data to table format
        labels = chart_data.get("labels", [])
        values = chart_data.get("values", [])
        
        if labels and values and len(labels) == len(values):
            headers = [
                chart_data.get("x_axis", "Category"),
                chart_data.get("y_axis", "Value")
            ]
            
            rows = [[label, str(value)] for label, value in zip(labels, values)]
            
            return MarkdownTableGenerator.generate_table(
                headers,
                rows,
                title=chart_data.get("title")
            )
        
        return None
