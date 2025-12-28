"""
Visualization generation using Matplotlib and Plotly.
Generates charts from extracted numerical data.
"""
import json
import os
import base64
from typing import Dict, Optional
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

logger = logging.getLogger(__name__)


class VisualizationGenerator:
    """Generates charts and graphs from numerical data."""
    
    def __init__(self, output_dir: str = "./charts"):
        """
        Initialize the visualization generator.
        
        Args:
            output_dir: Directory to save chart images
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_chart(self, data: Dict, chart_type: Optional[str] = None) -> Dict:
        """
        Generate a chart from extracted data.
        
        Args:
            data: Dictionary containing chart data (values, labels, etc.)
            chart_type: Type of chart (bar, line, pie) - auto-detected if None
            
        Returns:
            Dictionary with chart image (base64) and metadata
        """
        if "error" in data:
            logger.warning("No data available for visualization")
            return {"error": data["error"]}
        
        chart_type = chart_type or data.get("data_type", "bar")
        values = data.get("values", [])
        labels = data.get("labels", [])
        
        if not values or not labels:
            logger.warning("Insufficient data for visualization")
            return {"error": "Insufficient data"}
        
        if len(values) != len(labels):
            logger.warning("Mismatch between values and labels length")
            # Truncate to minimum length
            min_len = min(len(values), len(labels))
            values = values[:min_len]
            labels = labels[:min_len]
        
        try:
            if chart_type == "bar":
                return self._generate_bar_chart(data, values, labels)
            elif chart_type == "line":
                return self._generate_line_chart(data, values, labels)
            elif chart_type == "pie":
                return self._generate_pie_chart(data, values, labels)
            else:
                # Default to bar chart
                return self._generate_bar_chart(data, values, labels)
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return {"error": f"Chart generation failed: {e}"}
    
    def _generate_bar_chart(self, data: Dict, values: list, labels: list) -> Dict:
        """Generate a bar chart using Plotly."""
        try:
            fig = go.Figure(data=[
                go.Bar(x=labels, y=values, text=values, textposition='auto')
            ])
            
            fig.update_layout(
                title=data.get("title", "Bar Chart"),
                xaxis_title=data.get("x_axis", "Category"),
                yaxis_title=data.get("y_axis", "Value"),
                template="plotly_white"
            )
            
            # Convert to base64
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return {
                "chart_type": "bar",
                "image_base64": img_base64,
                "title": data.get("title", "Bar Chart")
            }
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}")
            raise
    
    def _generate_line_chart(self, data: Dict, values: list, labels: list) -> Dict:
        """Generate a line chart using Plotly."""
        try:
            fig = go.Figure(data=[
                go.Scatter(x=labels, y=values, mode='lines+markers', name='Data')
            ])
            
            fig.update_layout(
                title=data.get("title", "Line Chart"),
                xaxis_title=data.get("x_axis", "X Axis"),
                yaxis_title=data.get("y_axis", "Y Axis"),
                template="plotly_white"
            )
            
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return {
                "chart_type": "line",
                "image_base64": img_base64,
                "title": data.get("title", "Line Chart")
            }
        except Exception as e:
            logger.error(f"Error creating line chart: {e}")
            raise
    
    def _generate_pie_chart(self, data: Dict, values: list, labels: list) -> Dict:
        """Generate a pie chart using Plotly."""
        try:
            fig = go.Figure(data=[
                go.Pie(labels=labels, values=values, textinfo='label+percent')
            ])
            
            fig.update_layout(
                title=data.get("title", "Pie Chart"),
                template="plotly_white"
            )
            
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return {
                "chart_type": "pie",
                "image_base64": img_base64,
                "title": data.get("title", "Pie Chart")
            }
        except Exception as e:
            logger.error(f"Error creating pie chart: {e}")
            raise
    
    def parse_extracted_data(self, llm_response: str) -> Dict:
        """
        Parse LLM response containing extracted data.
        
        Args:
            llm_response: LLM response string (should be JSON)
            
        Returns:
            Parsed data dictionary
        """
        try:
            # Try to extract JSON from response
            response_clean = llm_response.strip()
            
            # Remove markdown code blocks if present
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1])
            
            # Parse JSON
            data = json.loads(response_clean)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extracted data: {e}")
            return {"error": "Failed to parse extracted data"}

