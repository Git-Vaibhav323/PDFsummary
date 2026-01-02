"""
Financial Data Normalization Module.

Normalizes financial data from various document types into a common chart schema.
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from app.rag.financial_detector import FinancialDocumentType

logger = logging.getLogger(__name__)


class FinancialDataNormalizer:
    """Normalizes financial data based on document type and financial semantics."""
    
    def normalize(
        self,
        document_type: FinancialDocumentType,
        extracted_data: Dict,
        context: str
    ) -> Optional[Dict]:
        """
        Normalize financial data into common chart schema.
        
        Args:
            document_type: Detected financial document type
            extracted_data: Raw extracted data (may be table or unstructured)
            context: Original context text
            
        Returns:
            Normalized chart data or None if normalization fails
        """
        logger.info(f"Normalizing data for {document_type.value}")
        
        if document_type == FinancialDocumentType.TRIAL_BALANCE:
            return self._normalize_trial_balance(extracted_data, context)
        elif document_type == FinancialDocumentType.PROFIT_AND_LOSS:
            return self._normalize_profit_and_loss(extracted_data, context)
        elif document_type == FinancialDocumentType.BALANCE_SHEET:
            return self._normalize_balance_sheet(extracted_data, context)
        elif document_type == FinancialDocumentType.CASH_FLOW:
            return self._normalize_cash_flow(extracted_data, context)
        elif document_type == FinancialDocumentType.FINANCIAL_SUMMARY:
            return self._normalize_financial_summary(extracted_data, context)
        else:
            return self._normalize_generic_financial(extracted_data, context)
    
    def _normalize_trial_balance(self, data: Dict, context: str) -> Optional[Dict]:
        """Normalize Trial Balance data."""
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        
        if not headers or not rows:
            # Try to extract from context
            return self._extract_trial_balance_from_context(context)
        
        # Find account, debit, credit columns
        account_col = self._find_column_index(headers, ['account', 'item', 'description', 'name'])
        debit_col = self._find_column_index(headers, ['debit'])
        credit_col = self._find_column_index(headers, ['credit'])
        
        if account_col is None:
            logger.error("❌ Cannot find account column in Trial Balance")
            return None
        
        labels = []
        debit_values = []
        credit_values = []
        
        for row in rows:
            if len(row) <= account_col:
                continue
            
            account_name = str(row[account_col]).strip()
            account_name = re.sub(r'[()$₹,\s]+', '', account_name)
            
            if not account_name or account_name.lower() in ['total', 'sum', '-', '']:
                continue
            
            debit_val = 0
            credit_val = 0
            
            if debit_col is not None and len(row) > debit_col:
                debit_val = self._parse_amount(row[debit_col])
            
            if credit_col is not None and len(row) > credit_col:
                credit_val = self._parse_amount(row[credit_col])
            
            # Only include accounts with non-zero values
            if debit_val > 0 or credit_val > 0:
                labels.append(account_name)
                debit_values.append(debit_val)
                credit_values.append(credit_val)
        
        if len(labels) < 2:
            logger.error("❌ Insufficient data for Trial Balance chart")
            return None
        
        # Use stacked bar for Debit vs Credit
        return {
            "chart_type": "stacked_bar",
            "labels": labels,
            "values": [max(d, c) for d, c in zip(debit_values, credit_values)],  # Use max for main values
            "groups": {
                "Debit": debit_values,
                "Credit": credit_values
            },
            "title": "Trial Balance",
            "x_axis": "Account",
            "y_axis": "Amount"
        }
    
    def _normalize_profit_and_loss(self, data: Dict, context: str) -> Optional[Dict]:
        """Normalize Profit & Loss Statement data."""
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        
        if not headers or not rows:
            return self._extract_pnl_from_context(context)
        
        # Look for revenue, expense, profit categories
        category_col = self._find_column_index(headers, ['item', 'description', 'category', 'account', 'name'])
        amount_col = self._find_column_index(headers, ['amount', 'value', 'total', 'revenue', 'expense', 'profit'])
        
        labels = []
        values = []
        
        # Financial categories to extract
        key_categories = ['revenue', 'sales', 'income', 'expense', 'cost', 'profit', 'loss', 'ebitda', 'net income']
        
        for row in rows:
            if category_col is not None and len(row) > category_col:
                category = str(row[category_col]).lower().strip()
                
                # Check if this is a key financial category
                if any(keyword in category for keyword in key_categories):
                    label = str(row[category_col]).strip()
                    
                    # Find amount
                    amount = 0
                    if amount_col is not None and len(row) > amount_col:
                        amount = self._parse_amount(row[amount_col])
                    else:
                        # Try to find amount in any numeric column
                        for idx, cell in enumerate(row):
                            if idx != category_col:
                                parsed = self._parse_amount(cell)
                                if parsed > amount:
                                    amount = parsed
                    
                    if amount > 0:
                        labels.append(label)
                        values.append(amount)
        
        if len(labels) < 2:
            logger.error("❌ Insufficient data for P&L chart")
            return None
        
        return {
            "chart_type": "bar",
            "labels": labels,
            "values": values,
            "title": "Profit & Loss Statement",
            "x_axis": "Category",
            "y_axis": "Amount"
        }
    
    def _normalize_balance_sheet(self, data: Dict, context: str) -> Optional[Dict]:
        """Normalize Balance Sheet data."""
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        
        if not headers or not rows:
            return self._extract_balance_sheet_from_context(context)
        
        # Look for Assets, Liabilities, Equity
        category_col = self._find_column_index(headers, ['item', 'category', 'account', 'description'])
        amount_col = self._find_column_index(headers, ['amount', 'value', 'total', 'balance'])
        
        # Group by major categories
        assets = []
        liabilities = []
        equity = []
        
        for row in rows:
            if category_col is not None and len(row) > category_col:
                category = str(row[category_col]).lower().strip()
                amount = 0
                
                if amount_col is not None and len(row) > amount_col:
                    amount = self._parse_amount(row[amount_col])
                
                if amount > 0:
                    if any(keyword in category for keyword in ['asset', 'property', 'equipment', 'inventory', 'cash', 'receivable']):
                        assets.append(amount)
                    elif any(keyword in category for keyword in ['liability', 'debt', 'payable', 'loan']):
                        liabilities.append(amount)
                    elif any(keyword in category for keyword in ['equity', 'capital', 'share', 'retained']):
                        equity.append(amount)
        
        # Create aggregated chart
        labels = []
        values = []
        
        if sum(assets) > 0:
            labels.append("Assets")
            values.append(sum(assets))
        if sum(liabilities) > 0:
            labels.append("Liabilities")
            values.append(sum(liabilities))
        if sum(equity) > 0:
            labels.append("Equity")
            values.append(sum(equity))
        
        if len(labels) < 2:
            logger.error("❌ Insufficient data for Balance Sheet chart")
            return None
        
        return {
            "chart_type": "pie",  # Pie chart for Assets/Liabilities/Equity
            "labels": labels,
            "values": values,
            "title": "Balance Sheet",
            "x_axis": "Category",
            "y_axis": "Amount"
        }
    
    def _normalize_cash_flow(self, data: Dict, context: str) -> Optional[Dict]:
        """Normalize Cash Flow Statement data."""
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        
        if not headers or not rows:
            return self._extract_cash_flow_from_context(context)
        
        category_col = self._find_column_index(headers, ['activity', 'category', 'item', 'description'])
        amount_col = self._find_column_index(headers, ['amount', 'cash', 'flow', 'net'])
        
        labels = []
        values = []
        
        # Look for operating, investing, financing activities
        activity_keywords = {
            'operating': ['operating', 'operations', 'operational'],
            'investing': ['investing', 'investment', 'capital'],
            'financing': ['financing', 'finance', 'loan', 'debt']
        }
        
        for row in rows:
            if category_col is not None and len(row) > category_col:
                category = str(row[category_col]).lower().strip()
                amount = 0
                
                if amount_col is not None and len(row) > amount_col:
                    amount = self._parse_amount(row[amount_col])
                
                # Match to activity type
                for activity_type, keywords in activity_keywords.items():
                    if any(keyword in category for keyword in keywords):
                        labels.append(activity_type.title())
                        values.append(abs(amount))  # Use absolute value
                        break
        
        if len(labels) < 2:
            logger.error("❌ Insufficient data for Cash Flow chart")
            return None
        
        return {
            "chart_type": "line",  # Line chart for cash flow over time
            "labels": labels,
            "values": values,
            "title": "Cash Flow Statement",
            "x_axis": "Activity",
            "y_axis": "Cash Flow"
        }
    
    def _normalize_financial_summary(self, data: Dict, context: str) -> Optional[Dict]:
        """Normalize Financial Summary/MIS Report data."""
        # Similar to generic but with more aggregation
        return self._normalize_generic_financial(data, context)
    
    def _normalize_generic_financial(self, data: Dict, context: str) -> Optional[Dict]:
        """Normalize generic financial data."""
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        
        if not headers or not rows:
            return self._extract_generic_from_context(context)
        
        # Find label and value columns
        label_col = self._find_column_index(headers, ['item', 'category', 'account', 'description', 'name'])
        value_col = self._find_column_index(headers, ['amount', 'value', 'total', 'balance', 'revenue', 'profit'])
        
        if label_col is None or value_col is None:
            # Try first and second columns
            label_col = 0
            value_col = 1 if len(headers) > 1 else None
        
        labels = []
        values = []
        
        for row in rows:
            if label_col is not None and len(row) > label_col:
                label = str(row[label_col]).strip()
                if not label or label.lower() in ['total', 'sum', '-', '']:
                    continue
                
                value = 0
                if value_col is not None and len(row) > value_col:
                    value = self._parse_amount(row[value_col])
                else:
                    # Try to find any numeric value in row
                    for idx, cell in enumerate(row):
                        if idx != label_col:
                            parsed = self._parse_amount(cell)
                            if parsed > value:
                                value = parsed
                
                if value > 0:
                    labels.append(label)
                    values.append(value)
        
        if len(labels) < 2:
            logger.error("❌ Insufficient data for generic financial chart")
            return None
        
        return {
            "chart_type": "bar",
            "labels": labels,
            "values": values,
            "title": "Financial Analysis",
            "x_axis": "Category",
            "y_axis": "Amount"
        }
    
    # Helper methods
    def _find_column_index(self, headers: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by matching keywords."""
        for idx, header in enumerate(headers):
            header_lower = str(header).lower()
            if any(keyword in header_lower for keyword in keywords):
                return idx
        return None
    
    def _parse_amount(self, value: any) -> float:
        """Parse amount from various formats."""
        if value is None:
            return 0.0
        
        value_str = str(value).strip()
        
        # Remove currency symbols and text
        value_str = re.sub(r'[()₹$Rs.,\s]', '', value_str)
        value_str = re.sub(r'\([^)]*\)', '', value_str)  # Remove parentheses content
        
        # Extract number
        number_match = re.search(r'[\d]+\.?\d*', value_str)
        if number_match:
            try:
                return float(number_match.group(0))
            except ValueError:
                return 0.0
        
        return 0.0
    
    # Context extraction methods (fallback when table structure not available)
    def _extract_trial_balance_from_context(self, context: str) -> Optional[Dict]:
        """Extract Trial Balance from context text."""
        # Implementation similar to existing fallback but with financial semantics
        return None  # Placeholder - can be enhanced
    
    def _extract_pnl_from_context(self, context: str) -> Optional[Dict]:
        """Extract P&L from context text."""
        return None
    
    def _extract_balance_sheet_from_context(self, context: str) -> Optional[Dict]:
        """Extract Balance Sheet from context text."""
        return None
    
    def _extract_cash_flow_from_context(self, context: str) -> Optional[Dict]:
        """Extract Cash Flow from context text."""
        return None
    
    def _extract_generic_from_context(self, context: str) -> Optional[Dict]:
        """Extract generic financial data from context text."""
        return None

