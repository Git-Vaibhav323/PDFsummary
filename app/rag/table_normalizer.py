"""
Table normalization utilities to ensure tables are always properly formatted.
"""
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TableNormalizer:
    """Normalize table data to ensure proper formatting."""
    
    @staticmethod
    def normalize_table(headers: List[str], rows: List[List[str]], title: Optional[str] = None) -> Dict:
        """
        Normalize table structure to ensure proper formatting.
        
        Args:
            headers: Column headers
            rows: Data rows (may be misaligned)
            title: Optional table title
            
        Returns:
            Normalized table dict with properly aligned rows
        """
        if not headers or not rows:
            logger.warning("Cannot normalize table: missing headers or rows")
            return {"headers": headers or [], "rows": rows or [], "title": title}
        
        # Step 1: Clean headers
        cleaned_headers = [str(h).strip().replace('**', '').replace('*', '') for h in headers]
        cleaned_headers = [h for h in cleaned_headers if h]  # Remove empty headers
        
        if len(cleaned_headers) < 2:
            logger.warning(f"Table has insufficient headers: {len(cleaned_headers)}")
            return {"headers": cleaned_headers, "rows": [], "title": title}
        
        # Step 2: Normalize rows
        normalized_rows = []
        
        for row_idx, row in enumerate(rows):
            if not isinstance(row, list):
                logger.warning(f"Row {row_idx} is not a list, skipping")
                continue
            
            # Clean row cells
            cleaned_row = [str(cell).strip().replace('**', '').replace('*', '') for cell in row]
            
            # Step 3: Fix misaligned rows (common issue: ["-", "Account", "Amount"])
            fixed_row = TableNormalizer._fix_row_alignment(cleaned_row, cleaned_headers)
            
            # Step 4: Ensure row length matches headers
            normalized_row = TableNormalizer._normalize_row_length(fixed_row, cleaned_headers)
            
            # Step 5: Skip empty rows (all cells are empty or "-")
            if not TableNormalizer._is_empty_row(normalized_row):
                normalized_rows.append(normalized_row)
        
        logger.info(f"✅ Normalized table: {len(cleaned_headers)} columns, {len(normalized_rows)} rows")
        
        return {
            "headers": cleaned_headers,
            "rows": normalized_rows,
            "title": title or "Table"
        }
    
    @staticmethod
    def _fix_row_alignment(row: List[str], headers: List[str]) -> List[str]:
        """
        Fix row alignment issues.
        
        Common patterns:
        - ["-", "Account", "Amount"] -> ["Account", "Amount", "-"]
        - ["", "Account", "Amount"] -> ["Account", "Amount", ""]
        """
        if not row:
            return row
        
        # Pattern 1: First cell is "-" or empty, second cell is account name
        if len(row) >= 2:
            first_cell = row[0].strip()
            second_cell = row[1].strip()
            
            # Check if first cell is placeholder and second is account name
            if first_cell in ["-", "", "—"] and second_cell:
                # Check if second cell looks like account name (contains letters)
                if re.search(r'[a-zA-Z]', second_cell) and not re.match(r'^[\d,.\-()$₹\s]+$', second_cell):
                    # Move account name to first position
                    # Structure: ["-", "Account", ...] -> ["Account", ...]
                    fixed = [second_cell] + row[2:] + [""]  # Add empty at end if needed
                    return fixed
        
        # Pattern 2: Row has extra leading column
        if len(row) == len(headers) + 1 and row[0] in ["-", "", "—"]:
            return row[1:]
        
        return row
    
    @staticmethod
    def _normalize_row_length(row: List[str], headers: List[str]) -> List[str]:
        """Ensure row has exactly the same length as headers."""
        normalized = list(row)
        
        # Pad with empty strings if too short
        while len(normalized) < len(headers):
            normalized.append("")
        
        # Truncate if too long
        normalized = normalized[:len(headers)]
        
        return normalized
    
    @staticmethod
    def _is_empty_row(row: List[str]) -> bool:
        """Check if row is empty (all cells are empty, "-", or whitespace)."""
        if not row:
            return True
        
        for cell in row:
            cell_str = str(cell).strip()
            if cell_str and cell_str not in ["-", "—", ""]:
                return False
        
        return True
    
    @staticmethod
    def normalize_table_data(table_data: Dict) -> Dict:
        """
        Normalize table data from any source.
        
        Args:
            table_data: Table data dict with headers and rows
            
        Returns:
            Normalized table data
        """
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])
        title = table_data.get("title")
        
        normalized = TableNormalizer.normalize_table(headers, rows, title)
        
        # Preserve other fields
        normalized.update({
            k: v for k, v in table_data.items() 
            if k not in ["headers", "rows", "title"]
        })
        
        return normalized

