"""
Comparison intent detection for multi-document RAG queries.
"""
import logging
import re
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)


def detect_comparison_intent(question: str) -> Tuple[bool, Optional[str], List[str]]:
    """
    Detect if a question has comparison intent and extract comparison signals.
    
    Args:
        question: User question
        
    Returns:
        Tuple of (is_comparison, comparison_type, comparison_signals)
        - is_comparison: True if comparison intent detected
        - comparison_type: Type of comparison ("compare", "difference", "trend", "which", "better", etc.)
        - comparison_signals: List of keywords/phrases that triggered detection
    """
    question_lower = question.lower()
    
    # Comparison keywords and patterns
    comparison_patterns = {
        "compare": [
            "compare", "comparison", "comparing", "compared", "compare between",
            "compare the", "compare these", "compare both", "compare all"
        ],
        "difference": [
            "difference", "different", "differ", "differs", "differing",
            "what's different", "how different", "what differs", "what is the difference"
        ],
        "versus": [
            "versus", "vs", "vs.", "v.", "against", "compared to", "compared with"
        ],
        "trend": [
            "trend", "trends", "trending", "over time", "across documents",
            "across years", "across periods", "evolution", "change over"
        ],
        "which": [
            "which one", "which document", "which is", "which has", "which shows",
            "which contains", "which indicates", "which demonstrates"
        ],
        "better": [
            "better", "best", "worse", "worst", "superior", "inferior",
            "outperforms", "underperforms", "stronger", "weaker"
        ],
        "change": [
            "change", "changed", "changes", "changing", "shift", "shifted",
            "from one to another", "from document", "between documents"
        ],
        "similarity": [
            "similar", "similarity", "same", "alike", "common", "shared",
            "in common", "both have", "all have"
        ],
        "contrast": [
            "contrast", "contrasting", "contrary", "opposite", "opposing",
            "on the other hand", "whereas", "while", "however"
        ]
    }
    
    detected_signals = []
    detected_types = []
    
    for comp_type, patterns in comparison_patterns.items():
        for pattern in patterns:
            # Use word boundaries for better matching
            pattern_regex = r'\b' + re.escape(pattern) + r'\b'
            if re.search(pattern_regex, question_lower):
                detected_signals.append(pattern)
                if comp_type not in detected_types:
                    detected_types.append(comp_type)
                break  # Only need one match per type
    
    # Also check for multi-document references
    multi_doc_patterns = [
        r"document\s+\d+", r"doc\s+\d+", r"first\s+document", r"second\s+document",
        r"third\s+document", r"both\s+documents", r"all\s+documents", r"multiple\s+documents"
    ]
    
    has_multi_doc_ref = any(re.search(pattern, question_lower) for pattern in multi_doc_patterns)
    
    # Determine comparison type
    is_comparison = len(detected_types) > 0 or has_multi_doc_ref
    
    if is_comparison:
        # Determine primary comparison type
        if "compare" in detected_types:
            primary_type = "compare"
        elif "difference" in detected_types:
            primary_type = "difference"
        elif "versus" in detected_types:
            primary_type = "versus"
        elif "trend" in detected_types:
            primary_type = "trend"
        elif "which" in detected_types:
            primary_type = "which"
        elif "better" in detected_types:
            primary_type = "better"
        elif "change" in detected_types:
            primary_type = "change"
        elif "contrast" in detected_types:
            primary_type = "contrast"
        elif "similarity" in detected_types:
            primary_type = "similarity"
        else:
            primary_type = "multi_document"
        
        logger.info(f"🔍 Comparison intent detected: type={primary_type}, signals={detected_signals}")
        return True, primary_type, detected_signals
    
    return False, None, []


def should_retrieve_from_all_documents(question: str, document_ids: Optional[List[str]] = None) -> bool:
    """
    Determine if retrieval should target all documents for comparison.
    
    Args:
        question: User question
        document_ids: List of available document IDs
        
    Returns:
        True if should retrieve from all documents
    """
    is_comparison, comp_type, _ = detect_comparison_intent(question)
    
    if not is_comparison:
        return False
    
    # If comparison detected and multiple documents available, retrieve from all
    if document_ids and len(document_ids) > 1:
        return True
    
    # If comparison detected but no specific documents selected, retrieve from all
    if is_comparison and (not document_ids or len(document_ids) == 0):
        return True
    
    return False


def extract_comparison_theme(question: str) -> Optional[str]:
    """
    Extract the theme/topic being compared from the question.
    
    Args:
        question: User question
        
    Returns:
        Theme string (e.g., "revenue", "financial performance", "risk factors")
    """
    # Common comparison themes
    themes = {
        "financial": ["revenue", "profit", "sales", "income", "earnings", "financial", "financials", "performance"],
        "risk": ["risk", "risks", "risk factors", "threats", "challenges"],
        "people": ["employees", "staff", "people", "workforce", "personnel"],
        "operations": ["operations", "operational", "processes", "activities"],
        "strategy": ["strategy", "strategic", "plans", "goals", "objectives"],
        "growth": ["growth", "growth rate", "expansion", "increase", "decline"],
        "metrics": ["metrics", "kpis", "indicators", "measures", "ratios"]
    }
    
    question_lower = question.lower()
    
    for theme, keywords in themes.items():
        for keyword in keywords:
            if keyword in question_lower:
                return theme
    
    return None

