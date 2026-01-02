"""
Unified API response structure for enterprise RAG chatbot.

Standard response format:
{
  "answer": "string",
  "table": optional markdown table,
  "chart": optional chart object,
  "chat_history": full conversation history
}
"""
import logging
from typing import Dict, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ChartObject(BaseModel):
    """Chart visualization object."""
    type: str = Field(..., description="Chart type: bar, line, pie, or table")
    title: str = Field("", description="Chart title")
    labels: Optional[List[str]] = Field(default=None, description="Data labels/categories")
    values: Optional[List[float]] = Field(default=None, description="Data values")
    xAxis: Optional[str] = Field(default=None, description="X-axis label")
    yAxis: Optional[str] = Field(default=None, description="Y-axis label")
    headers: Optional[List[str]] = Field(default=None, description="Table headers")
    rows: Optional[List[List[str]]] = Field(default=None, description="Table rows")


class MessageObject(BaseModel):
    """Chat message with metadata."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")
    timestamp: str = Field(..., description="ISO timestamp")


class RAGResponse(BaseModel):
    """Standard RAG API response."""
    answer: str = Field(..., description="Main answer text")
    table: Optional[str] = Field(default=None, description="Markdown-formatted table if applicable")
    chart: Optional[ChartObject] = Field(default=None, description="Chart visualization if applicable")
    visualization: Optional[Dict] = Field(default=None, description="Frontend-compatible visualization format")
    chat_history: List[MessageObject] = Field(default_factory=list, description="Full conversation history")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "Based on the Q3 2023 data, revenue increased by 15%...",
                "table": None,
                "chart": {
                    "type": "bar",
                    "title": "Q3 Revenue Comparison",
                    "labels": ["Q1", "Q2", "Q3"],
                    "values": [100, 110, 127],
                    "xAxis": "Quarter",
                    "yAxis": "Revenue (M)"
                },
                "chat_history": [
                    {
                        "role": "user",
                        "content": "What was Q3 revenue?",
                        "timestamp": "2024-01-02T10:00:00"
                    },
                    {
                        "role": "assistant",
                        "content": "Based on the Q3 2023 data...",
                        "timestamp": "2024-01-02T10:00:05"
                    }
                ]
            }
        }


class ResponseBuilder:
    """Build standardized API responses."""
    
    @staticmethod
    def build_response(
        answer: str,
        table: Optional[str] = None,
        chart: Optional[Dict] = None,
        chat_history: Optional[List[Dict]] = None
    ) -> RAGResponse:
        """
        Build standardized RAG response.
        
        Args:
            answer: Main answer text
            table: Optional Markdown table
            chart: Optional chart dictionary
            chat_history: Optional conversation history
            
        Returns:
            RAGResponse object
        """
        # Convert chat history to message objects
        messages = []
        if chat_history:
            for msg in chat_history:
                try:
                    message_obj = MessageObject(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                        timestamp=msg.get("timestamp", "")
                    )
                    messages.append(message_obj)
                except Exception as e:
                    logger.warning(f"Failed to parse chat message: {e}")
        
        # Convert chart dict to ChartObject if present
        chart_obj = None
        if chart:
            try:
                chart_obj = ChartObject(**chart)
            except Exception as e:
                logger.warning(f"Failed to create ChartObject: {e}")
        
        # Build response
        response = RAGResponse(
            answer=answer,
            table=table,
            chart=chart_obj,
            chat_history=messages
        )
        
        return response
    
    @staticmethod
    def build_error_response(
        error: str,
        chat_history: Optional[List[Dict]] = None
    ) -> RAGResponse:
        """
        Build error response.
        
        Args:
            error: Error message
            chat_history: Optional conversation history
            
        Returns:
            RAGResponse with error message
        """
        return ResponseBuilder.build_response(
            answer=f"Error: {error}",
            chat_history=chat_history
        )
    
    @staticmethod
    def build_from_rag_result(
        rag_result: Dict,
        viz_result: Optional[Dict] = None,
        chat_history: Optional[List[Dict]] = None
    ) -> RAGResponse:
        """
        Build response from RAG and visualization pipeline results.
        
        Args:
            rag_result: Result from RAGRetriever.answer_question()
            viz_result: Optional result from VisualizationPipeline.process()
            chat_history: Full conversation history
            
        Returns:
            RAGResponse object
        """
        answer = rag_result.get("answer", "")
        
        # Extract visualization if available
        chart = None
        table = None
        
        if viz_result:
            # CRITICAL: Check if viz_result itself has an error (not nested in chart)
            if isinstance(viz_result, dict) and "error" in viz_result and "chart" not in viz_result:
                error_msg = viz_result.get("error", "No structured numerical data available to generate a chart.")
                logger.warning(f"Visualization error detected at top level: {error_msg} - updating answer")
                # Update answer to show error message
                answer = error_msg
                chart = None
            else:
                chart = viz_result.get("chart")
                
                # CRITICAL: Filter out error objects in chart
                if chart and isinstance(chart, dict):
                    if "error" in chart:
                        error_msg = chart.get("error", "No structured numerical data available to generate a chart.")
                        logger.warning(f"Visualization error detected in chart: {error_msg} - filtering out")
                        answer = error_msg
                        chart = None
                    elif not chart.get("type"):
                        logger.warning("Chart missing type field - filtering out")
                        chart = None

            # CRITICAL: NEVER allow table when chart was requested
            # Check if this is from a chart request (we need to pass this info)
            # For now, if chart type is table, we should filter it out if it's a chart request
            # This will be handled at API level with question context
            if chart and chart.get("type") == "table":
                # Only create table markdown if NOT a chart request
                # Note: Chart request detection happens at API level
                from app.rag.table_generator import MarkdownTableGenerator

                headers = chart.get("headers", [])
                rows = chart.get("rows", [])
                title = chart.get("title")

                if headers and rows:
                    table = MarkdownTableGenerator.generate_table(headers, rows, title)
                    # Keep the `chart` object (of type 'table') so frontends can
                    # render a native table chart if they prefer.
        
        return ResponseBuilder.build_response(
            answer=answer,
            table=table,
            chart=chart,
            chat_history=chat_history
        )


def build_api_response(
    answer: str,
    table: Optional[str] = None,
    chart: Optional[Dict] = None,
    chat_history: Optional[List[Dict]] = None
) -> Dict:
    """
    Build API response dictionary.
    
    Convenience function that returns JSON-serializable dict.
    
    Args:
        answer: Main answer text
        table: Optional Markdown table
        chart: Optional chart dictionary
        chat_history: Optional conversation history
        
    Returns:
        JSON-serializable dictionary
    """
    response = ResponseBuilder.build_response(
        answer=answer,
        table=table,
        chart=chart,
        chat_history=chat_history
    )
    
    return response.model_dump(exclude_none=True)
