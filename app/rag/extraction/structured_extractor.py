"""
Structured data extraction using Mistral API.
Extracts tables, metrics, and time-series data as JSON.
"""
import os
import json
from typing import Dict, List, Optional
import logging

try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    Mistral = None

logger = logging.getLogger(__name__)


class StructuredDataExtractor:
    """Extracts structured data from text using Mistral API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize structured data extractor.
        
        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            
        Raises:
            ValueError: If API key is not provided or mistralai is not installed
        """
        if not MISTRAL_AVAILABLE:
            raise ValueError(
                "mistralai package is not installed. Install it with: pip install mistralai"
            )
        
        if api_key is None:
            api_key = os.getenv("MISTRAL_API_KEY")
        
        if not api_key:
            raise ValueError(
                "MISTRAL_API_KEY is not set. Please set it in your .env file or environment variables."
            )
        
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-large-latest"
    
    def extract_structured_data(self, text: str) -> Optional[Dict]:
        """
        Extract structured data for visualization in STRICT chart-ready schema.
        
        Args:
            text: Clean text to extract data from
            
        Returns:
            Dictionary with strict schema:
            {
                "chart_type": "bar | line | pie",
                "labels": ["string", ...],
                "values": [number, ...],
                "title": "string",
                "x_axis": "string",
                "y_axis": "string"
            }
            OR None if no meaningful data found
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for structured extraction")
            return None
        
        try:
            # Use the EXACT prompt format specified
            prompt = (
                "From the text below, extract ONLY meaningful numerical data suitable for visualization.\n\n"
                "Rules:\n"
                "- Ignore page numbers, indexes, serial numbers\n"
                "- Extract ONLY business, financial, or metric data\n"
                "- You MUST return STRICT JSON in the format below\n"
                "- If data cannot be structured, return: null\n\n"
                "JSON FORMAT (MANDATORY):\n"
                "{\n"
                "  'chart_type': 'bar | line | pie',\n"
                "  'labels': [...],\n"
                "  'values': [...],\n"
                "  'title': '...',\n"
                "  'x_axis': '...',\n"
                "  'y_axis': '...'\n"
                "}\n\n"
                "TEXT:\n"
                f"{text[:6000]}\n\n"
                "Return JSON only. No explanation."
            )
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0  # Deterministic output
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response - expect single object or null
            try:
                # Remove markdown code blocks if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                # Check for null response
                if response_text.lower().strip() in ['null', 'none', '']:
                    logger.info("Extractor returned null - no meaningful data found")
                    return None
                
                # Parse as JSON
                data = json.loads(response_text)
                
                # Must be a dictionary
                if not isinstance(data, dict):
                    logger.warning(f"Expected dict, got {type(data)}")
                    return None
                
                # Validate strict schema
                if self._validate_strict_schema(data):
                    logger.info("Extracted data passed strict schema validation")
                    return data
                else:
                    logger.warning("Extracted data failed strict schema validation")
                    return None
                
            except json.JSONDecodeError as json_error:
                logger.error(f"Failed to parse JSON response: {json_error}")
                logger.debug(f"Response text: {response_text[:500]}")
                return None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Structured data extraction failed: {error_msg}")
            return None
    
    def _validate_strict_schema(self, data: Dict) -> bool:
        """
        Validate data matches STRICT chart-ready schema.
        
        Args:
            data: Data dictionary
            
        Returns:
            True if matches strict schema, False otherwise
        """
        try:
            # REQUIRED: chart_type must be one of: bar, line, pie
            if "chart_type" not in data:
                logger.warning("Missing 'chart_type' field")
                return False
            
            chart_type = data["chart_type"]
            if chart_type not in ["bar", "line", "pie"]:
                logger.warning(f"Invalid chart_type: {chart_type}. Must be 'bar', 'line', or 'pie'")
                return False
            
            # REQUIRED: labels must be a list of strings
            if "labels" not in data:
                logger.warning("Missing 'labels' field")
                return False
            
            labels = data.get("labels", [])
            if not isinstance(labels, list):
                logger.warning("'labels' must be a list")
                return False
            
            if len(labels) < 2:
                logger.warning(f"Need at least 2 labels, got {len(labels)}")
                return False
            
            # REQUIRED: values must be a list of numbers
            if "values" not in data:
                logger.warning("Missing 'values' field")
                return False
            
            values = data.get("values", [])
            if not isinstance(values, list):
                logger.warning("'values' must be a list")
                return False
            
            if len(values) < 2:
                logger.warning(f"Need at least 2 values, got {len(values)}")
                return False
            
            # REQUIRED: labels and values must have same length
            if len(labels) != len(values):
                logger.warning(f"Labels ({len(labels)}) and values ({len(values)}) length mismatch")
                return False
            
            # REQUIRED: All values must be valid numbers
            for i, val in enumerate(values):
                try:
                    # Handle comma-separated numbers
                    val_str = str(val).replace(',', '').strip()
                    if val_str.lower() in ['-', 'null', 'none', '', 'n/a', 'na', 'nil']:
                        logger.warning(f"Invalid value at index {i}: {val}")
                        return False
                    num_val = float(val_str)
                    if num_val != num_val:  # NaN check
                        logger.warning(f"NaN value at index {i}")
                        return False
                except (ValueError, TypeError):
                    logger.warning(f"Invalid numeric value at index {i}: {val}")
                    return False
            
            # REQUIRED: title must be a string
            if "title" not in data or not isinstance(data.get("title"), str):
                logger.warning("Missing or invalid 'title' field")
                return False
            
            # REQUIRED: x_axis and y_axis must be strings
            if "x_axis" not in data or not isinstance(data.get("x_axis"), str):
                logger.warning("Missing or invalid 'x_axis' field")
                return False
            
            if "y_axis" not in data or not isinstance(data.get("y_axis"), str):
                logger.warning("Missing or invalid 'y_axis' field")
                return False
            
            logger.info("Data passed strict schema validation")
            return True
            
        except Exception as e:
            logger.error(f"Error validating strict schema: {e}")
            return False

