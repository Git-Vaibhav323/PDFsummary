"""
Advanced Financial Agent for structured financial analysis.

Provides:
- 10+ predefined financial questions
- Structured analysis with tables and charts
- State persistence
- Cross-document financial comparisons
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

# Database path for financial agent state
def find_project_root():
    """Find the project root directory."""
    current = os.path.abspath(__file__)
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, ".git")) or os.path.exists(os.path.join(current, "requirements.txt")):
            return str(current)
        current = os.path.dirname(current)
    return os.getcwd()

PROJECT_ROOT = find_project_root()
DB_DIR = os.path.join(PROJECT_ROOT, "data")
FINANCIAL_AGENT_STATE_PATH = os.path.join(DB_DIR, "financial_agent_state.json")


class FinancialAgent:
    """Advanced Financial Agent with predefined questions and state persistence."""
    
    # 10+ Advanced Financial Questions
    FINANCIAL_QUESTIONS = [
        {
            "id": 1,
            "question": "Analyze the revenue trend over the last 3-5 years. Show year-over-year growth rates and identify any significant changes.",
            "category": "Revenue Analysis",
            "requires_chart": True,
            "chart_type": "line"
        },
        {
            "id": 2,
            "question": "Compare profit margins (gross, operating, net) across different periods. Identify trends and explain any margin compression or expansion.",
            "category": "Profitability Analysis",
            "requires_chart": True,
            "chart_type": "bar"
        },
        {
            "id": 3,
            "question": "Calculate and analyze key financial ratios: current ratio, debt-to-equity ratio, return on equity (ROE), and return on assets (ROA).",
            "category": "Ratio Analysis",
            "requires_chart": True,
            "chart_type": "table"
        },
        {
            "id": 4,
            "question": "Break down operating expenses by category. Identify the top 3-5 expense components and their percentage of total revenue.",
            "category": "Expense Analysis",
            "requires_chart": True,
            "chart_type": "pie"
        },
        {
            "id": 5,
            "question": "Analyze cash flow from operations, investing, and financing activities. Identify cash flow trends and any concerns.",
            "category": "Cash Flow Analysis",
            "requires_chart": True,
            "chart_type": "bar"
        },
        {
            "id": 6,
            "question": "Assess the debt position: total debt, debt maturity schedule, interest coverage ratio, and debt service capacity.",
            "category": "Debt Analysis",
            "requires_chart": True,
            "chart_type": "table"
        },
        {
            "id": 7,
            "question": "Identify and analyze the top 3-5 financial risks mentioned in the document. Assess their potential impact.",
            "category": "Risk Analysis",
            "requires_chart": False
        },
        {
            "id": 8,
            "question": "Compare financial performance across business segments or geographic regions. Identify the best and worst performing areas.",
            "category": "Segment Analysis",
            "requires_chart": True,
            "chart_type": "bar"
        },
        {
            "id": 9,
            "question": "Analyze working capital trends: current assets, current liabilities, and working capital changes over time.",
            "category": "Working Capital Analysis",
            "requires_chart": True,
            "chart_type": "line"
        },
        {
            "id": 10,
            "question": "Evaluate forward-looking guidance: revenue projections, profit forecasts, and key assumptions. Assess reasonableness.",
            "category": "Forward-Looking Analysis",
            "requires_chart": False
        },
        {
            "id": 11,
            "question": "Calculate and analyze EBITDA trends. Compare EBITDA margins across periods and explain changes.",
            "category": "EBITDA Analysis",
            "requires_chart": True,
            "chart_type": "bar"
        },
        {
            "id": 12,
            "question": "Analyze asset turnover ratios and efficiency metrics. Identify trends in asset utilization.",
            "category": "Efficiency Analysis",
            "requires_chart": True,
            "chart_type": "line"
        }
    ]
    
    def __init__(self):
        """Initialize Financial Agent."""
        self.state_path = FINANCIAL_AGENT_STATE_PATH
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        self._load_state()
    
    def _load_state(self):
        """Load persisted state."""
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r') as f:
                    self.state = json.load(f)
                logger.info("Financial Agent state loaded")
            else:
                self.state = {
                    "selected_documents": [],
                    "cached_answers": {},
                    "processed_questions": [],
                    "last_updated": None
                }
        except Exception as e:
            logger.warning(f"Failed to load Financial Agent state: {e}")
            self.state = {
                "selected_documents": [],
                "cached_answers": {},
                "processed_questions": [],
                "last_updated": None
            }
    
    def _save_state(self):
        """Save state to disk."""
        try:
            self.state["last_updated"] = datetime.utcnow().isoformat()
            with open(self.state_path, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug("Financial Agent state saved")
        except Exception as e:
            logger.warning(f"Failed to save Financial Agent state: {e}")
    
    def get_questions(self) -> List[Dict]:
        """Get all financial questions."""
        return self.FINANCIAL_QUESTIONS
    
    def get_question_by_id(self, question_id: int) -> Optional[Dict]:
        """Get a specific question by ID."""
        return next((q for q in self.FINANCIAL_QUESTIONS if q["id"] == question_id), None)
    
    def set_selected_documents(self, document_ids: List[str]):
        """Set selected documents for analysis."""
        self.state["selected_documents"] = document_ids
        self._save_state()
    
    def get_selected_documents(self) -> List[str]:
        """Get selected documents."""
        return self.state.get("selected_documents", [])
    
    def cache_answer(self, question_id: int, answer: str, visualization: Optional[Dict] = None):
        """Cache an answer for a question."""
        self.state["cached_answers"][str(question_id)] = {
            "answer": answer,
            "visualization": visualization,
            "timestamp": datetime.utcnow().isoformat()
        }
        if question_id not in self.state["processed_questions"]:
            self.state["processed_questions"].append(question_id)
        self._save_state()
    
    def get_cached_answer(self, question_id: int) -> Optional[Dict]:
        """Get cached answer for a question."""
        return self.state["cached_answers"].get(str(question_id))
    
    def is_question_processed(self, question_id: int) -> bool:
        """Check if a question has been processed."""
        return question_id in self.state.get("processed_questions", [])
    
    def clear_cache(self):
        """Clear all cached answers."""
        self.state["cached_answers"] = {}
        self.state["processed_questions"] = []
        self._save_state()
    
    def get_state_summary(self) -> Dict:
        """Get summary of current state."""
        return {
            "selected_documents": len(self.state.get("selected_documents", [])),
            "cached_answers": len(self.state.get("cached_answers", {})),
            "processed_questions": len(self.state.get("processed_questions", [])),
            "last_updated": self.state.get("last_updated")
        }

