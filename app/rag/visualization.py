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
        
        # CRITICAL FIX: Support both "chart_type" and "data_type" for compatibility
        chart_type = chart_type or data.get("chart_type") or data.get("data_type", "bar")
        
        # Handle table type
        if chart_type == "table":
            return self._generate_table(data)
        
        # Ensure chart_type is valid
        if chart_type not in ["bar", "line", "pie", "table"]:
            logger.info(f"Invalid chart_type '{chart_type}', defaulting to bar")
            chart_type = "bar"
        
        values = data.get("values", [])
        labels = data.get("labels", [])
        
        if not values or not labels:
            logger.warning("Insufficient data for visualization")
            return {"error": "Insufficient data"}
        
        # Validate and clean data
        # Convert values to numbers, filter out invalid ones
        cleaned_values = []
        cleaned_labels = []
        for i, (val, label) in enumerate(zip(values, labels)):
            try:
                val_str = str(val).strip()
                label_str = str(label).strip() if label else ""
                
                # Reject null/empty/dash values
                if val_str.lower() in ['-', 'null', 'none', '', 'n/a', 'na', 'nil', '0']:
                    logger.debug(f"Skipping null/empty value: {val}")
                    continue
                
                # Reject labels that are just numbers or "appears X times"
                if label_str.lower().startswith('appears') or re.match(r'^\d+$', label_str):
                    logger.debug(f"Skipping meaningless label: {label_str}")
                    continue
                
                # Handle comma-separated numbers (e.g., "5,65,44,552")
                cleaned_val_str = val_str.replace(',', '')
                
                # Convert to float
                num_val = float(cleaned_val_str) if not isinstance(val, (int, float)) else val
                
                # Check for NaN or infinite values
                is_nan = isinstance(num_val, float) and (num_val != num_val)  # NaN check: NaN != NaN is True
                is_inf = isinstance(num_val, float) and (abs(num_val) >= 1e10)  # Infinity check
                
                # Reject zero values (they're not meaningful for most visualizations)
                # But allow if it's explicitly a meaningful zero (e.g., "No sales")
                is_zero = abs(num_val) < 1e-10
                
                # Allow zero only if label suggests it's meaningful (e.g., "No data", "Zero")
                allow_zero = is_zero and any(keyword in label_str.lower() for keyword in ['no', 'zero', 'nil', 'none', 'missing'])
                
                if not is_nan and not is_inf and (not is_zero or allow_zero):
                    cleaned_values.append(num_val)
                    cleaned_labels.append(label_str if label_str else f"Item {i+1}")
                else:
                    logger.debug(f"Skipping invalid value: {val} (NaN={is_nan}, Inf={is_inf}, Zero={is_zero})")
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping value {val} with label {label}: {e}")
                continue
        
        if len(cleaned_values) < 2:
            logger.warning("Not enough valid data points for visualization")
            return {"error": "Not enough valid data points (need at least 2)"}
        
        # Limit to reasonable size (max 50 items for performance)
        max_items = 50
        if len(cleaned_values) > max_items:
            logger.info(f"Limiting visualization to {max_items} items (had {len(cleaned_values)})")
            cleaned_values = cleaned_values[:max_items]
            cleaned_labels = cleaned_labels[:max_items]
        
        values = cleaned_values
        labels = cleaned_labels
        
        try:
            # Use matplotlib as primary (more reliable, faster)
            if chart_type == "bar":
                return self._generate_bar_chart_matplotlib(data, values, labels)
            elif chart_type == "line":
                # Try Plotly first, fallback to matplotlib
                try:
                    return self._generate_line_chart(data, values, labels)
                except Exception as plotly_error:
                    logger.warning(f"Plotly line chart failed: {plotly_error}, using matplotlib")
                    return self._generate_line_chart_matplotlib(data, values, labels)
            elif chart_type == "pie":
                return self._generate_pie_chart_matplotlib(data, values, labels)
            elif chart_type == "table":
                return self._generate_table(data)
            else:
                # Default to bar chart
                return self._generate_bar_chart_matplotlib(data, values, labels)
        except Exception as e:
            logger.error(f"Error generating chart: {e}", exc_info=True)
            return {"error": f"Chart generation failed: {e}"}
    
    def _generate_bar_chart(self, data: Dict, values: list, labels: list) -> Dict:
        """Generate a bar chart using Plotly, with matplotlib fallback."""
        try:
            # Validate inputs
            if not values or not labels:
                raise ValueError(f"Empty data: {len(values)} values, {len(labels)} labels")
            
            if len(values) != len(labels):
                logger.warning(f"Length mismatch: {len(values)} values vs {len(labels)} labels. Truncating to match.")
                min_len = min(len(values), len(labels))
                values = values[:min_len]
                labels = labels[:min_len]
            
            logger.info(f"Generating bar chart with {len(values)} data points")
            
            # Try Plotly first
            try:
                logger.debug("Attempting Plotly chart generation...")
                fig = go.Figure(data=[
                    go.Bar(x=labels, y=values, text=[f"{v:,.0f}" if abs(v) >= 1 else f"{v:.2f}" for v in values], textposition='auto')
                ])
                
                fig.update_layout(
                    title=data.get("title", "Bar Chart"),
                    xaxis_title=data.get("x_axis", "Category"),
                    yaxis_title=data.get("y_axis", "Value"),
                    template="plotly_white",
                    height=500
                )
                
                # Try to convert to image with timeout handling
                logger.debug("Converting Plotly chart to image...")
                import signal
                
                # Try simple conversion first (no engine specified)
                try:
                    img_bytes = fig.to_image(format="png", width=800, height=500)
                    logger.debug(f"Plotly image generated: {len(img_bytes)} bytes")
                except Exception as plotly_error:
                    logger.warning(f"Plotly to_image failed: {plotly_error}. Trying matplotlib fallback...")
                    raise  # Will trigger matplotlib fallback
                
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                result = {
                    "chart_type": "bar",
                    "image_base64": img_base64,
                    "title": data.get("title", "Bar Chart")
                }
                logger.info("✅ Bar chart generated successfully with Plotly")
                return result
                
            except Exception as plotly_error:
                logger.warning(f"Plotly failed: {plotly_error}. Using matplotlib fallback...")
                # Fallback to matplotlib
                return self._generate_bar_chart_matplotlib(data, values, labels)
                
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}", exc_info=True)
            # Last resort: try matplotlib
            try:
                return self._generate_bar_chart_matplotlib(data, values, labels)
            except Exception as matplotlib_error:
                logger.error(f"Both Plotly and matplotlib failed: {matplotlib_error}")
                raise
    
    def _generate_bar_chart_matplotlib(self, data: Dict, values: list, labels: list) -> Dict:
        """Generate a bar chart using matplotlib as fallback."""
        try:
            logger.info("Generating bar chart with matplotlib...")
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(labels, values, color='steelblue', alpha=0.7)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:,.0f}' if abs(height) >= 1 else f'{height:.2f}',
                       ha='center', va='bottom', fontsize=9)
            
            ax.set_title(data.get("title", "Bar Chart"), fontsize=14, fontweight='bold')
            ax.set_xlabel(data.get("x_axis", "Category"), fontsize=12)
            ax.set_ylabel(data.get("y_axis", "Value"), fontsize=12)
            ax.grid(axis='y', alpha=0.3)
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            img_bytes = buffer.read()
            buffer.close()
            plt.close(fig)
            
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            logger.info("✅ Bar chart generated successfully with matplotlib")
            return {
                "chart_type": "bar",
                "image_base64": img_base64,
                "title": data.get("title", "Bar Chart")
            }
        except Exception as e:
            logger.error(f"Matplotlib chart generation failed: {e}", exc_info=True)
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
            
            try:
                img_bytes = fig.to_image(format="png", width=800, height=500, engine="kaleido")
            except Exception:
                img_bytes = fig.to_image(format="png", width=800, height=500)
            
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return {
                "chart_type": "line",
                "image_base64": img_base64,
                "title": data.get("title", "Line Chart")
            }
        except Exception as e:
            logger.error(f"Error creating line chart: {e}")
            raise
    
    def _generate_line_chart_matplotlib(self, data: Dict, values: list, labels: list) -> Dict:
        """Generate a line chart using matplotlib as fallback."""
        try:
            logger.info("Generating line chart with matplotlib...")
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(labels, values, marker='o', linestyle='-', linewidth=2, markersize=8, color='steelblue')
            
            ax.set_title(data.get("title", "Line Chart"), fontsize=14, fontweight='bold')
            ax.set_xlabel(data.get("x_axis", "X Axis"), fontsize=12)
            ax.set_ylabel(data.get("y_axis", "Y Axis"), fontsize=12)
            ax.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            img_bytes = buffer.read()
            buffer.close()
            plt.close(fig)
            
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            logger.info("✅ Line chart generated successfully with matplotlib")
            return {
                "chart_type": "line",
                "image_base64": img_base64,
                "title": data.get("title", "Line Chart")
            }
        except Exception as e:
            logger.error(f"Matplotlib line chart generation failed: {e}", exc_info=True)
            raise
    
    def _generate_pie_chart_matplotlib(self, data: Dict, values: list, labels: list) -> Dict:
        """Generate a pie chart using matplotlib."""
        try:
            logger.info("Generating pie chart with matplotlib...")
            
            fig, ax = plt.subplots(figsize=(8, 8))
            
            # Create pie chart
            colors = plt.cm.Set3(range(len(values)))
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                             startangle=90, colors=colors)
            
            # Improve text appearance
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
            
            ax.set_title(data.get("title", "Pie Chart"), fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            img_bytes = buffer.read()
            buffer.close()
            plt.close(fig)
            
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            logger.info("✅ Pie chart generated successfully")
            return {
                "chart_type": "pie",
                "image_base64": img_base64,
                "title": data.get("title", "Pie Chart")
            }
        except Exception as e:
            logger.error(f"Error creating pie chart: {e}", exc_info=True)
            raise
    
    def parse_extracted_data(self, llm_response: str) -> Dict:
        """
        Parse LLM response containing extracted data.
        Handles various response formats and extracts JSON.
        
        Args:
            llm_response: LLM response string (should be JSON)
            
        Returns:
            Parsed data dictionary
        """
        if not llm_response or not llm_response.strip():
            logger.warning("Empty LLM response")
            return {"error": "Empty response"}
        
        # Log response length for debugging
        if len(llm_response) > 5000:
            logger.debug(f"Large response received ({len(llm_response)} chars), may need truncation")
        
        try:
            import re
            
            response_clean = llm_response.strip()
            
            # Method 1: Try direct JSON parse
            try:
                data = json.loads(response_clean)
                if isinstance(data, dict):
                    # CRITICAL FIX: Normalize to strict schema (chart_type, not data_type)
                    if "data_type" in data and "chart_type" not in data:
                        data["chart_type"] = data.pop("data_type")
                    # Keep table type
                    if data.get("chart_type") == "table":
                        logger.info("Found table chart_type in parse_extracted_data - keeping as table")
                        if "headers" in data and "rows" in data:
                            return data
                    return data
            except json.JSONDecodeError:
                pass
            
            # Method 2: Remove markdown code blocks
            if "```" in response_clean:
                # Extract content between ```json and ``` or just ```
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_clean, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        if isinstance(data, dict):
                            # Normalize to strict schema
                            if "data_type" in data and "chart_type" not in data:
                                data["chart_type"] = data.pop("data_type")
                            # Keep table type
                            if data.get("chart_type") == "table":
                                logger.info("Found table chart_type in parse_extracted_data (method 2) - keeping as table")
                                if "headers" in data and "rows" in data:
                                    return data
                            return data
                    except json.JSONDecodeError:
                        pass
                
                # Try removing first and last lines if they are ```
                lines = response_clean.split("\n")
                if lines[0].strip().startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                response_clean = "\n".join(lines).strip()
            
            # Method 3: Extract JSON object using improved regex (handles nested structures)
            # Find the first { and try to match balanced braces
            brace_count = 0
            start_idx = response_clean.find('{')
            if start_idx != -1:
                json_str = ""
                for i in range(start_idx, len(response_clean)):
                    char = response_clean[i]
                    json_str += char
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found complete JSON object
                            try:
                                data = json.loads(json_str)
                                if isinstance(data, dict):
                                    # Normalize to strict schema
                                    if "data_type" in data and "chart_type" not in data:
                                        data["chart_type"] = data.pop("data_type")
                                    # Keep table type
                                    if data.get("chart_type") == "table":
                                        logger.info("Found table chart_type in parse_extracted_data (method 3) - keeping as table")
                                        if "headers" in data and "rows" in data:
                                            return data
                                    return data
                            except json.JSONDecodeError:
                                # Try to repair common issues
                                try:
                                    # Fix trailing commas in arrays
                                    json_str_fixed = re.sub(r',(\s*[}\]])', r'\1', json_str)
                                    data = json.loads(json_str_fixed)
                                    if isinstance(data, dict):
                                        # Normalize to strict schema
                                        if "data_type" in data and "chart_type" not in data:
                                            data["chart_type"] = data.pop("data_type")
                                        # Keep table type
                                        if data.get("chart_type") == "table":
                                            logger.info("Found table chart_type in parse_extracted_data (method 3 repair) - keeping as table")
                                            if "headers" in data and "rows" in data:
                                                return data
                                        return data
                                except json.JSONDecodeError:
                                    pass
                            break
            
            # Method 4: Try to find and repair incomplete JSON
            # Look for JSON that might be cut off
            if response_clean.startswith('{'):
                # Try to complete incomplete JSON
                if not response_clean.rstrip().endswith('}'):
                    # Might be truncated, try to close it
                    try:
                        # Count braces to see if we can close it
                        open_braces = response_clean.count('{')
                        close_braces = response_clean.count('}')
                        if open_braces > close_braces:
                            # Add missing closing braces
                            test_json = response_clean + '}' * (open_braces - close_braces)
                            # Try to close arrays too
                            open_brackets = test_json.count('[')
                            close_brackets = test_json.count(']')
                            if open_brackets > close_brackets:
                                test_json = test_json + ']' * (open_brackets - close_brackets)
                            data = json.loads(test_json)
                            if isinstance(data, dict):
                                # Normalize to strict schema
                                if "data_type" in data and "chart_type" not in data:
                                    data["chart_type"] = data.pop("data_type")
                                # Keep table type
                                if data.get("chart_type") == "table":
                                    logger.info("Found table chart_type in parse_extracted_data (method 4) - keeping as table")
                                    if "headers" in data and "rows" in data:
                                        return data
                                return data
                    except json.JSONDecodeError:
                        pass
            
            # Method 5: Try parsing cleaned response again
            try:
                data = json.loads(response_clean)
                if isinstance(data, dict):
                    # Normalize to strict schema
                    if "data_type" in data and "chart_type" not in data:
                        data["chart_type"] = data.pop("data_type")
                    # Keep table type
                    if data.get("chart_type") == "table":
                        logger.info("Found table chart_type in parse_extracted_data (method 5) - keeping as table")
                        if "headers" in data and "rows" in data:
                            return data
                    return data
            except json.JSONDecodeError:
                pass
            
            # Method 6: Try to extract just the essential data (values and labels) even if JSON is broken
            try:
                # Look for values array
                values_match = re.search(r'"values"\s*:\s*\[([^\]]+)\]', response_clean, re.DOTALL)
                labels_match = re.search(r'"labels"\s*:\s*\[([^\]]+)\]', response_clean, re.DOTALL)
                
                if values_match and labels_match:
                    # Extract values
                    values_str = values_match.group(1)
                    values = []
                    for num_str in re.findall(r'[\d,]+\.?\d*', values_str):
                        try:
                            val = float(num_str.replace(',', ''))
                            values.append(val)
                        except ValueError:
                            continue
                    
                    # Extract labels
                    labels_str = labels_match.group(1)
                    labels = []
                    # Remove quotes and split by comma
                    labels_clean = re.sub(r'["\']', '', labels_str)
                    for label in labels_clean.split(','):
                        label_clean = label.strip()
                        if label_clean:
                            labels.append(label_clean)
                    
                    # Match lengths
                    min_len = min(len(values), len(labels))
                    if min_len >= 2:
                        return {
                            "chart_type": "bar",
                            "values": values[:min_len],
                            "labels": labels[:min_len],
                            "title": "Extracted Data",
                            "x_axis": "Category",
                            "y_axis": "Value"
                        }
            except Exception as e:
                logger.debug(f"Fallback extraction failed: {e}")
            
            # If all methods fail, log the response for debugging
            logger.warning(f"Could not parse JSON from response. First 200 chars: {response_clean[:200]}")
            logger.debug(f"Full response length: {len(response_clean)} chars")
            return {"error": "Failed to parse extracted data", "raw_response": response_clean[:500]}
            
        except Exception as e:
            logger.error(f"Unexpected error parsing extracted data: {e}")
            return {"error": f"Parsing error: {str(e)}"}
    
    def _generate_table(self, data: Dict) -> Dict:
        """
        Generate a professional financial table with proper markdown formatting.
        
        Rules:
        - Clean markdown syntax only
        - Right-align numeric columns
        - Keep negative values in parentheses
        - No extra pipes at end of rows
        - Professional financial table appearance
        
        Args:
            data: Dictionary containing table data (headers, rows, title)
            
        Returns:
            Dictionary with table data in markdown format
        """
        try:
            headers = data.get("headers", [])
            rows = data.get("rows", [])
            title = data.get("title", "Table")
            
            if not headers or not rows:
                logger.warning("Insufficient data for table")
                return {"error": "Insufficient data for table"}
            
            # Validate and normalize rows to match header count
            normalized_rows = []
            for i, row in enumerate(rows):
                if not isinstance(row, list):
                    logger.warning(f"Row {i} is not a list")
                    continue
                # Pad or truncate to match headers
                normalized_row = list(row[:len(headers)])  # Truncate if too long
                while len(normalized_row) < len(headers):
                    normalized_row.append("")
                normalized_rows.append(normalized_row)
            
            if not normalized_rows:
                return {"error": "No valid rows found"}
            
            rows = normalized_rows
            
            # Detect numeric columns (columns that contain mostly numbers)
            def is_numeric_value(val):
                """Check if a value is numeric."""
                if not val or val == "-" or val == "":
                    return False
                val_str = str(val).strip()
                # Remove common formatting: commas, parentheses, currency symbols
                val_clean = val_str.replace(',', '').replace('₹', '').replace('$', '').replace('Rs.', '').replace('Rs', '')
                val_clean = val_clean.replace('(', '').replace(')', '').strip()
                # Check if it's a number (including negative)
                try:
                    float(val_clean)
                    return True
                except:
                    return False
            
            # Determine which columns are numeric
            numeric_columns = []
            for col_idx in range(len(headers)):
                # Check if majority of non-empty cells in this column are numeric
                numeric_count = 0
                total_count = 0
                for row in rows:
                    cell = row[col_idx] if col_idx < len(row) else ""
                    if cell and str(cell).strip() and str(cell).strip() != "-":
                        total_count += 1
                        if is_numeric_value(cell):
                            numeric_count += 1
                # If >50% are numeric, consider column numeric
                if total_count > 0 and numeric_count / total_count > 0.5:
                    numeric_columns.append(col_idx)
            
            # Format cells: handle negative values and numeric formatting
            def format_cell(cell, is_numeric_col):
                """Format a cell value properly."""
                if not cell or str(cell).strip() == "" or str(cell).strip() == "-":
                    return "-"
                
                cell_str = str(cell).strip()
                
                # For numeric columns, ensure proper formatting
                if is_numeric_col:
                    # Check if already in parentheses format (negative)
                    if cell_str.startswith('(') and cell_str.endswith(')'):
                        return cell_str  # Already formatted
                    # Try to detect negative values
                    val_clean = cell_str.replace(',', '').replace('₹', '').replace('$', '').replace('Rs.', '').replace('Rs', '').strip()
                    try:
                        num_val = float(val_clean)
                        if num_val < 0:
                            # Format as (positive_value)
                            abs_val = abs(num_val)
                            # Preserve original formatting if it had commas
                            if ',' in cell_str:
                                return f"({abs_val:,.2f})"
                            return f"({abs_val})"
                    except:
                        pass
                
                return cell_str
            
            # Format all cells
            formatted_rows = []
            for row in rows:
                formatted_row = []
                for col_idx, cell in enumerate(row):
                    is_numeric = col_idx in numeric_columns
                    formatted_row.append(format_cell(cell, is_numeric))
                formatted_rows.append(formatted_row)
            
            # Generate clean markdown table - STRICT SYNTAX
            # Header row: | Column A | Column B |
            header_cells = [str(h).strip() for h in headers]
            header_row = "| " + " | ".join(header_cells) + " |"
            
            # Separator row with right-alignment for numeric columns
            # Format: |----------|----------:| (exactly one separator row)
            separator_parts = []
            for col_idx in range(len(headers)):
                if col_idx in numeric_columns:
                    separator_parts.append("---:")  # Right-align numeric columns
                else:
                    separator_parts.append("---")   # Left-align text columns
            separator_row = "| " + " | ".join(separator_parts) + " |"
            
            # Data rows: | Value 1 | Value 2 |
            data_rows = []
            for row in formatted_rows:
                # Ensure row has same length as headers (CRITICAL: same number of columns)
                row_padded = row[:len(headers)]
                while len(row_padded) < len(headers):
                    row_padded.append("-")  # Use "-" for empty cells
                row_padded = row_padded[:len(headers)]  # Ensure exact match
                
                # Format row cells
                row_cells = [str(cell).strip() if cell else "-" for cell in row_padded]
                data_row = "| " + " | ".join(row_cells) + " |"
                data_rows.append(data_row)
            
            # Combine into clean markdown table (NO title, NO extra text, NO ASCII art)
            # Exactly: header row, separator row, data rows
            markdown_table = header_row + "\n" + separator_row + "\n"
            markdown_table += "\n".join(data_rows)
            
            logger.info(f"✅ Professional table generated: {len(headers)} columns, {len(rows)} rows")
            logger.info(f"Numeric columns (right-aligned): {numeric_columns}")
            
            return {
                "chart_type": "table",
                "markdown": markdown_table,
                "headers": headers,
                "rows": formatted_rows,  # Return formatted rows
                "title": title
            }
        except Exception as e:
            logger.error(f"Error generating table: {e}", exc_info=True)
            return {"error": f"Table generation failed: {e}"}

