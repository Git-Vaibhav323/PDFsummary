"""
Financial Document Type Detection Module.

Detects the type of financial document based on keywords and structure.
"""
import re
import logging
from typing import Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class FinancialDocumentType(Enum):
    """Supported financial document types."""
    TRIAL_BALANCE = "trial_balance"
    PROFIT_AND_LOSS = "profit_and_loss"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    FINANCIAL_SUMMARY = "financial_summary"
    GENERIC_FINANCIAL = "generic_financial"


class FinancialDocumentDetector:
    """Detects financial document types from context and question."""
    
    # Document type patterns
    TRIAL_BALANCE_PATTERNS = [
        r'trial\s+balance',
        r'account\s+debit\s+credit',
        r'debit\s+credit\s+balance',
        r'ledger\s+balance',
        r'chart\s+of\s+accounts'
    ]
    
    PROFIT_AND_LOSS_PATTERNS = [
        r'profit\s+and\s+loss',
        r'p\s*&\s*l',
        r'income\s+statement',
        r'revenue\s+expense',
        r'net\s+income',
        r'operating\s+income',
        r'gross\s+profit',
        r'ebitda'
    ]
    
    BALANCE_SHEET_PATTERNS = [
        r'balance\s+sheet',
        r'assets\s+liabilities',
        r'equity\s+liabilities',
        r'financial\s+position',
        r'statement\s+of\s+financial\s+position'
    ]
    
    CASH_FLOW_PATTERNS = [
        r'cash\s+flow',
        r'cashflow',
        r'operating\s+activities',
        r'investing\s+activities',
        r'financing\s+activities',
        r'net\s+cash'
    ]
    
    FINANCIAL_SUMMARY_PATTERNS = [
        r'financial\s+summary',
        r'mis\s+report',
        r'annual\s+report',
        r'financial\s+report',
        r'financial\s+statement',
        r'consolidated\s+statement'
    ]
    
    GENERIC_FINANCIAL_PATTERNS = [
        r'financial',
        r'revenue',
        r'profit',
        r'expense',
        r'asset',
        r'liability',
        r'equity',
        r'budget',
        r'forecast'
    ]
    
    def detect(self, question: str, context: str) -> FinancialDocumentType:
        """
        Detect financial document type from question and context.
        
        Args:
            question: User question
            context: Retrieved context from document
            
        Returns:
            Detected document type
        """
        combined_text = f"{question} {context}".lower()
        
        # Check in order of specificity
        if self._matches_patterns(combined_text, self.TRIAL_BALANCE_PATTERNS):
            logger.info("✅ Detected: TRIAL_BALANCE")
            return FinancialDocumentType.TRIAL_BALANCE
        
        if self._matches_patterns(combined_text, self.PROFIT_AND_LOSS_PATTERNS):
            logger.info("✅ Detected: PROFIT_AND_LOSS")
            return FinancialDocumentType.PROFIT_AND_LOSS
        
        if self._matches_patterns(combined_text, self.BALANCE_SHEET_PATTERNS):
            logger.info("✅ Detected: BALANCE_SHEET")
            return FinancialDocumentType.BALANCE_SHEET
        
        if self._matches_patterns(combined_text, self.CASH_FLOW_PATTERNS):
            logger.info("✅ Detected: CASH_FLOW")
            return FinancialDocumentType.CASH_FLOW
        
        if self._matches_patterns(combined_text, self.FINANCIAL_SUMMARY_PATTERNS):
            logger.info("✅ Detected: FINANCIAL_SUMMARY")
            return FinancialDocumentType.FINANCIAL_SUMMARY
        
        if self._matches_patterns(combined_text, self.GENERIC_FINANCIAL_PATTERNS):
            logger.info("✅ Detected: GENERIC_FINANCIAL")
            return FinancialDocumentType.GENERIC_FINANCIAL
        
        logger.warning("⚠️ No financial document type detected")
        return FinancialDocumentType.GENERIC_FINANCIAL
    
    def _matches_patterns(self, text: str, patterns: list) -> bool:
        """Check if text matches any pattern."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

