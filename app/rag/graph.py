"""
LangGraph implementation for RAG flow control.
Manages the complete RAG pipeline with conditional visualization.
"""
from typing import TypedDict, List, Dict, Optional
import logging
import time
import re
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from app.config.settings import settings
from app.rag.retriever import ContextRetriever
from app.rag.prompts import (
    RAG_PROMPT,
    VISUALIZATION_DETECTION_PROMPT,
    DATA_EXTRACTION_PROMPT
)
from app.rag.visualization import VisualizationGenerator

logger = logging.getLogger(__name__)


def _validate_strict_schema(data: Dict) -> bool:
    """
    Validate data matches STRICT chart-ready schema.
    
    REQUIRED SCHEMA:
    {
        "chart_type": "bar | line | pie",
        "labels": ["string", ...],
        "values": [number, ...],
        "title": "string",
        "x_axis": "string",
        "y_axis": "string"
    }
    
    Args:
        data: Data dictionary
        
    Returns:
        True if matches strict schema, False otherwise
    """
    if not data or not isinstance(data, dict):
        return False
    
    # REQUIRED: chart_type must be one of: bar, line, pie, table
    chart_type = data.get("chart_type") or data.get("data_type")  # Support both for compatibility
    if not chart_type or chart_type not in ["bar", "line", "pie", "table"]:
        logger.warning(f"Invalid chart_type: {chart_type}")
        return False
    
    # For tables, validate table-specific schema
    if chart_type == "table":
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        if not headers or not isinstance(headers, list) or len(headers) < 2:
            logger.warning(f"Invalid table headers: need list with at least 2 items")
            return False
        if not rows or not isinstance(rows, list) or len(rows) < 1:
            logger.warning(f"Invalid table rows: need list with at least 1 row")
            return False
        # Check that all rows have same length as headers
        for i, row in enumerate(rows):
            if not isinstance(row, list) or len(row) != len(headers):
                logger.warning(f"Row {i} length ({len(row) if isinstance(row, list) else 'N/A'}) doesn't match headers ({len(headers)})")
                return False
        return True
    
    # REQUIRED: labels must be a list of strings
    labels = data.get("labels", [])
    if not isinstance(labels, list) or len(labels) < 2:
        logger.warning(f"Invalid labels: need list with at least 2 items")
        return False
    
    # REQUIRED: values must be a list of numbers
    values = data.get("values", [])
    if not isinstance(values, list) or len(values) < 2:
        logger.warning(f"Invalid values: need list with at least 2 items")
        return False
    
    # REQUIRED: labels and values must have same length
    if len(labels) != len(values):
        logger.warning(f"Labels ({len(labels)}) and values ({len(values)}) length mismatch")
        return False
    
    # REQUIRED: All values must be valid numbers
    for i, val in enumerate(values):
        try:
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
    
    # REQUIRED: title, x_axis, y_axis must be strings
    if not isinstance(data.get("title"), str) or not data.get("title"):
        logger.warning("Missing or invalid 'title' field")
        return False
    
    if not isinstance(data.get("x_axis"), str) or not data.get("x_axis"):
        logger.warning("Missing or invalid 'x_axis' field")
        return False
    
    if not isinstance(data.get("y_axis"), str) or not data.get("y_axis"):
        logger.warning("Missing or invalid 'y_axis' field")
        return False
    
    logger.info("Data passed strict schema validation")
    return True


def _is_meaningful_data(extracted_data: Dict) -> bool:
    """
    Validate if extracted data is meaningful for visualization.
    Filters out page numbers, indexes, serial numbers, etc.
    
    Args:
        extracted_data: Dictionary with values, labels, etc.
        
    Returns:
        True if data is meaningful, False otherwise
    """
    if not extracted_data or not isinstance(extracted_data, dict):
        return False
    
    if "error" in extracted_data:
        return False
    
    values = extracted_data.get("values", [])
    labels = extracted_data.get("labels", [])
    
    # Must have at least 2 data points
    if not values or not labels or len(values) < 2 or len(labels) < 2:
        return False
    
    # Must have matching lengths
    if len(values) != len(labels):
        return False
    
    # Check if labels are meaningful (not page numbers, indexes, etc.)
    meaningless_patterns = [
        r'^page\s*\d+$',
        r'^p\.?\s*\d+$',
        r'^section\s*\d+',
        r'^chapter\s*\d+',
        r'^fig\.?\s*\d+',
        r'^table\s*\d+',
        r'^\d+$',  # Just a number without context
        r'^item\s*\d+$',
        r'^#\d+$',
    ]
    
    meaningful_count = 0
    for label in labels:
        label_str = str(label).lower().strip()
        
        # Check if label matches meaningless patterns
        is_meaningless = any(re.match(pattern, label_str) for pattern in meaningless_patterns)
        
        # Check if label has semantic meaning (contains words, not just numbers)
        has_semantic_meaning = (
            any(char.isalpha() for char in label_str) or
            any(keyword in label_str for keyword in [
                'year', 'month', 'quarter', 'revenue', 'profit', 'sales', 'cost',
                'budget', 'amount', 'value', 'percentage', '%', 'ratio', 'count',
                'total', 'average', 'growth', 'rate', 'share', 'market'
            ])
        )
        
        if not is_meaningless and (has_semantic_meaning or len(label_str) > 3):
            meaningful_count += 1
    
    # At least 2 labels must be meaningful
    if meaningful_count < 2:
        logger.warning(f"Only {meaningful_count} meaningful labels found out of {len(labels)}")
        return False
    
    # Check for null/empty/invalid values
    valid_value_count = 0
    valid_pairs = []
    for val, label in zip(values, labels):
        val_str = str(val).strip().lower()
        label_str = str(label).strip().lower()
        
        # Reject null, empty, dash, or non-numeric values
        if val_str in ['-', 'null', 'none', '', 'n/a', 'na', 'nil', '—', '–']:
            continue
        
        # Reject labels that are meaningless
        if label_str.startswith('appears') or re.match(r'^\d+$', label_str) or len(label_str) < 2:
            continue
        
        # Try to convert to number
        try:
            # Handle comma-separated numbers (remove all commas)
            cleaned_val = val_str.replace(',', '').replace(' ', '')
            # Reject if it's still not a valid number after cleaning
            if not cleaned_val or cleaned_val == '-':
                continue
            num_val = float(cleaned_val)
            if not (num_val != num_val):  # Not NaN
                valid_value_count += 1
                valid_pairs.append((num_val, label))
        except (ValueError, TypeError):
            continue
    
    # Must have at least 2 valid numeric values with meaningful labels
    if valid_value_count < 2:
        logger.warning(f"Only {valid_value_count} valid numeric values with meaningful labels found out of {len(values)}")
        return False
    
    # Check that we have at least 2 unique label-value pairs
    unique_pairs = set((str(label).lower().strip(), float(val)) for val, label in valid_pairs)
    if len(unique_pairs) < 2:
        logger.warning(f"Only {len(unique_pairs)} unique label-value pairs found")
        return False
    
    # Check if values are reasonable (not all the same, not all sequential page numbers)
    # Convert values to numbers for comparison
    numeric_values = []
    for val in values:
        try:
            val_str = str(val).strip().replace(',', '')
            if val_str.lower() not in ['-', 'null', 'none', '', 'n/a', 'na', 'nil']:
                num_val = float(val_str)
                if num_val == num_val:  # Not NaN
                    numeric_values.append(num_val)
        except (ValueError, TypeError):
            continue
    
    if len(numeric_values) < 2:
        return False
    
    unique_values = set(numeric_values)
    if len(unique_values) < 2:
        logger.warning("All values are the same - not meaningful for visualization")
        return False
    
    # Check if values look like page numbers (sequential small integers)
    if all(isinstance(v, (int, float)) and 1 <= v <= 1000 for v in values):
        # Check if they're sequential (like page numbers)
        sorted_values = sorted([v for v in values if isinstance(v, (int, float))])
        if len(sorted_values) > 1:
            diffs = [sorted_values[i+1] - sorted_values[i] for i in range(len(sorted_values)-1)]
            # If differences are mostly 1 or small, might be page numbers
            if all(1 <= d <= 5 for d in diffs[:min(5, len(diffs))]):
                # But check if labels are meaningful - if labels are good, it's OK
                if meaningful_count < len(labels) * 0.7:  # Less than 70% meaningful labels
                    logger.warning("Values appear to be sequential numbers (possibly page numbers)")
                    return False
    
    return True


def _deduplicate_data(extracted_data: Dict) -> Dict:
    """
    Remove duplicate data entries based on label-value pairs.
    
    Args:
        extracted_data: Dictionary with values and labels
        
    Returns:
        Deduplicated data dictionary
    """
    if not extracted_data or not isinstance(extracted_data, dict):
        return extracted_data
    
    values = extracted_data.get("values", [])
    labels = extracted_data.get("labels", [])
    
    if not values or not labels:
        return extracted_data
    
    # Create unique pairs
    seen = set()
    unique_values = []
    unique_labels = []
    
    for val, label in zip(values, labels):
        pair_key = (str(label).lower().strip(), float(val) if isinstance(val, (int, float)) else val)
        if pair_key not in seen:
            seen.add(pair_key)
            unique_values.append(val)
            unique_labels.append(label)
    
    if len(unique_values) < len(values):
        logger.info(f"Deduplicated data: {len(values)} -> {len(unique_values)} entries")
        extracted_data["values"] = unique_values
        extracted_data["labels"] = unique_labels
    
    return extracted_data


class GraphState(TypedDict, total=False):
    """State definition for LangGraph."""
    question: str
    retrieved_context: List[Dict]
    context_text: str
    answer: str
    needs_visualization: bool
    extracted_data_for_chart: Optional[Dict]
    visualization: Optional[Dict]
    final_response: Dict


class RAGGraph:
    """LangGraph-based RAG pipeline with visualization support."""
    
    def __init__(self, retriever: ContextRetriever):
        """
        Initialize the RAG graph.
        
        Args:
            retriever: ContextRetriever instance
        """
        self.retriever = retriever
        
        # Get API key from settings or environment
        api_key = None
        if settings and hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            api_key = settings.openai_api_key
        else:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file or environment variables.")
        
        model_name = settings.openai_model if settings and hasattr(settings, 'openai_model') else "gpt-4o-mini"
        
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0.1  # Low temperature for factual responses
        )
        self.visualization_generator = VisualizationGenerator(
            output_dir=settings.chart_output_dir
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        workflow.add_node("check_visualization", self._check_visualization_node)
        workflow.add_node("extract_data", self._extract_data_node)
        workflow.add_node("generate_chart", self._generate_chart_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        
        # Set entry point
        workflow.set_entry_point("retrieve_context")
        
        # Add edges
        workflow.add_edge("retrieve_context", "generate_answer")
        workflow.add_edge("generate_answer", "check_visualization")
        
        # Conditional edge for visualization
        workflow.add_conditional_edges(
            "check_visualization",
            self._should_visualize,
            {
                "yes": "extract_data",
                "no": "finalize_response"
            }
        )
        
        workflow.add_edge("extract_data", "generate_chart")
        workflow.add_edge("generate_chart", "finalize_response")
        workflow.add_edge("finalize_response", END)
        
        # Compile the graph - use None checkpointer to avoid configuration issues
        try:
            # Compile without checkpointer to avoid configuration requirements
            compiled_graph = workflow.compile(checkpointer=None)
            logger.info("Graph compiled successfully without checkpointer")
            return compiled_graph
        except Exception as compile_error:
            logger.error(f"Error compiling graph: {compile_error}")
            # Return a dummy graph that will use fallback
            class DummyGraph:
                def invoke(self, state):
                    raise KeyError("Graph compilation failed, using fallback")
            return DummyGraph()
    
    def _retrieve_context_node(self, state: GraphState) -> GraphState:
        """Node 1: Retrieve relevant context from vector store."""
        try:
            question = state.get("question", "")
            if not question:
                logger.error("No question provided in state")
                return {**state, "retrieved_context": [], "context_text": ""}
            
            # Retrieve context
            try:
                logger.info(f"Retrieving context for question: {question[:100]}...")
                retrieved_docs = self.retriever.retrieve(question)
                context_text = self.retriever.format_context(retrieved_docs)
                
                logger.info(f"Retrieved {len(retrieved_docs)} context chunks")
                logger.info(f"Formatted context length: {len(context_text)} characters")
                
                # If no results, try fallback: get all documents
                if not retrieved_docs or not context_text:
                    logger.warning("Primary retrieval returned no results, trying fallback: get all documents")
                    try:
                        fallback_docs = self.retriever.vector_store.get_all_documents(limit=15)
                        if fallback_docs:
                            logger.info(f"Fallback retrieval got {len(fallback_docs)} documents")
                            retrieved_docs = fallback_docs
                            context_text = self.retriever.format_context(fallback_docs)
                            logger.info(f"Fallback context length: {len(context_text)} characters")
                    except Exception as fallback_error:
                        logger.error(f"Fallback retrieval also failed: {fallback_error}")
                
                if retrieved_docs and not context_text:
                    logger.error("Retrieved documents but context_text is empty - formatting issue!")
                    # Try to manually format if formatting failed
                    context_parts = []
                    for doc in retrieved_docs:
                        text = doc.get("text", "")
                        if text:
                            page_num = doc.get("metadata", {}).get("page_number", "Unknown")
                            context_parts.append(f"[Page {page_num}]\n{text}\n")
                    context_text = "\n".join(context_parts)
                    logger.info(f"Manually formatted context length: {len(context_text)} characters")
            except Exception as retrieve_error:
                error_str = str(retrieve_error)
                # Check if it's a quota/embedding issue
                if "limit: 0" in error_str or "free_tier" in error_str.lower() or "429" in error_str:
                    logger.error(f"Retrieval failed due to embedding quota: {retrieve_error}")
                    return {
                        **state,
                        "retrieved_context": [],
                        "context_text": "",
                        "answer": "Error: Cannot retrieve context. This should not happen with local embeddings. Please check if sentence-transformers is installed."
                    }
                # Try fallback even on error
                try:
                    logger.info("Trying fallback retrieval after exception...")
                    fallback_docs = self.retriever.vector_store.get_all_documents(limit=15)
                    if fallback_docs:
                        retrieved_docs = fallback_docs
                        context_text = self.retriever.format_context(fallback_docs)
                        logger.info(f"Fallback succeeded after exception: {len(fallback_docs)} documents")
                    else:
                        raise
                except:
                    logger.error("All retrieval methods failed")
                    raise
            
            return {
                **state,
                "retrieved_context": retrieved_docs,
                "context_text": context_text
            }
        except Exception as e:
            logger.error(f"Error in retrieve_context_node: {e}")
            return {**state, "retrieved_context": [], "context_text": ""}
    
    def _generate_answer_node(self, state: GraphState) -> GraphState:
        """Node 2: Generate answer using LLM with retrieved context."""
        answer = ""  # Initialize answer variable
        try:
            question = state.get("question", "").strip()
            context_text = state.get("context_text", "").strip()
            retrieved_docs = state.get("retrieved_context", [])
            
            logger.info(f"Generating answer for question: {question[:100]}...")
            logger.info(f"Context text length: {len(context_text)} characters")
            logger.info(f"Retrieved documents count: {len(retrieved_docs)}")
            
            if not question:
                answer = "Please provide a question."
                logger.warning("Empty question provided")
                return {**state, "answer": answer}
            
            if not context_text:
                logger.warning("No context available for answer generation")
                if not retrieved_docs:
                    logger.error("No documents were retrieved from vector store. The document may not be properly indexed.")
                    # Try to get ANY documents from the vector store as a last resort
                    try:
                        # Try to get all documents directly from vector store
                        all_docs = self.retriever.vector_store.get_all_documents(limit=10)
                        if all_docs:
                            logger.info(f"Got {len(all_docs)} documents using fallback method, formatting context...")
                            context_text = self.retriever.format_context(all_docs)
                            retrieved_docs = all_docs
                            logger.info(f"Fallback context length: {len(context_text)} characters")
                        else:
                            # Final diagnostic check
                            test_results = self.retriever.retrieve("test", k=1)
                            if not test_results:
                                answer = "The document appears to be empty or not properly indexed. Please try re-uploading the PDF file."
                            else:
                                answer = f"I couldn't find information matching your question '{question}'. Try rephrasing your question or asking about different topics in the document."
                    except Exception as diag_error:
                        logger.error(f"Diagnostic check failed: {diag_error}")
                        answer = "I couldn't find any relevant information in the uploaded document. Please ensure the PDF was processed correctly. Try re-uploading the document."
                else:
                    logger.warning(f"Retrieved {len(retrieved_docs)} documents but context_text is empty. This may indicate a formatting issue.")
                    # Try to manually format the context
                    context_parts = []
                    for doc in retrieved_docs:
                        text = doc.get("text", "")
                        if text and text.strip():
                            page_num = doc.get("metadata", {}).get("page_number", "Unknown")
                            context_parts.append(f"[Page {page_num}]\n{text}\n")
                    if context_parts:
                        context_text = "\n".join(context_parts)
                        logger.info(f"Manually formatted context: {len(context_text)} characters")
                        # Continue to generate answer with manually formatted context
                    else:
                        answer = "I found some content in the document, but couldn't extract the text properly. Please try re-uploading the document or ask a different question."
                        return {**state, "answer": answer}
            
            # Generate answer if we have context (either from normal flow or manually formatted)
            if context_text:
                # Check if user is asking for a summary
                question_lower = question.lower()
                is_summary_request = any(word in question_lower for word in [
                    "summary", "summarize", "overview", "brief", "what is this about",
                    "what is this document about", "give me a summary", "summarize this"
                ])
                
                if is_summary_request:
                    # Use summary prompt
                    from app.rag.prompts import SUMMARY_PROMPT
                    prompt = SUMMARY_PROMPT.format(context=context_text)
                    logger.info("Generating summary for document")
                else:
                    # Use regular RAG prompt
                    prompt = RAG_PROMPT.format(
                        context=context_text,
                        question=question
                    )
                
                # Generate answer with retry
                logger.info(f"Invoking LLM with prompt length: {len(str(prompt))} characters")
                logger.info(f"Context preview: {context_text[:500]}...")
                try:
                    response = self.llm.invoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    # Clean up the answer
                    answer = answer.strip()
                    logger.info(f"LLM response length: {len(answer)} characters")
                    logger.info(f"LLM response preview: {answer[:200]}...")
                    
                    # Check if LLM is being too conservative and saying "not available" when we have context
                    if answer.lower().startswith("not available") and len(context_text) > 100:
                        logger.warning("LLM said 'not available' but we have context. Trying more directive prompt...")
                        try:
                            directive_prompt = f"""You MUST answer the question using the provided context. The context contains relevant information - use it.

Question: {question}

Context from document:
{context_text[:4000]}

IMPORTANT: Answer the question using the information in the context above. Do not say "not available" - extract and present the relevant information from the context.

Answer:"""
                            response = self.llm.invoke(directive_prompt)
                            answer = response.content if hasattr(response, 'content') else str(response)
                            answer = answer.strip()
                            if answer and not answer.lower().startswith("not available"):
                                logger.info("Directive prompt succeeded")
                        except Exception as directive_error:
                            logger.error(f"Directive prompt failed: {directive_error}")
                    
                    if not answer:
                        logger.warning("LLM returned empty answer")
                        # Try a simpler prompt as fallback
                        try:
                            simple_prompt = f"""Based on the following document content, answer this question: {question}

Document content:
{context_text[:3000]}

Answer:"""
                            logger.info("Trying simpler prompt as fallback...")
                            response = self.llm.invoke(simple_prompt)
                            answer = response.content if hasattr(response, 'content') else str(response)
                            answer = answer.strip()
                            if answer:
                                logger.info("Fallback prompt succeeded")
                        except Exception as fallback_error:
                            logger.error(f"Fallback prompt also failed: {fallback_error}")
                            # Last resort: provide context directly
                            answer = f"Based on the document content:\n\n{context_text[:1000]}..."
                except Exception as e:
                    error_str = str(e)
                    logger.error(f"LLM error (first attempt): {e}")
                    
                    # Check if it's a model decommissioned error
                    if "decommissioned" in error_str.lower() or "model_decommissioned" in error_str or "model_not_found" in error_str.lower():
                        logger.warning("Model not available, trying alternative model: gpt-3.5-turbo")
                        # Try with an alternative model
                        try:
                            # Get API key from settings
                            api_key = None
                            if settings and hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                                api_key = settings.openai_api_key
                            else:
                                import os
                                api_key = os.getenv('OPENAI_API_KEY')
                            
                            if api_key:
                                from langchain_openai import ChatOpenAI
                                fallback_llm = ChatOpenAI(
                                    model="gpt-3.5-turbo",
                                    api_key=api_key,
                                    temperature=0.1
                                )
                                response = fallback_llm.invoke(prompt)
                                answer = response.content if hasattr(response, 'content') else str(response)
                                answer = answer.strip()
                                if not answer:
                                    answer = "Not available in the uploaded document"
                                # Update self.llm to use the working model
                                self.llm = fallback_llm
                                logger.info("Successfully switched to gpt-3.5-turbo model")
                            else:
                                answer = "Error: OpenAI API key not found. Cannot use fallback model."
                        except Exception as fallback_error:
                            logger.error(f"Fallback model also failed: {fallback_error}")
                            answer = "Error: The configured OpenAI model is not available. Please update OPENAI_MODEL in your .env file. Try: gpt-4o-mini, gpt-4o, or gpt-3.5-turbo"
                    else:
                        # Retry once for other errors
                        try:
                            time.sleep(1)  # Brief delay before retry
                            response = self.llm.invoke(prompt)
                            answer = response.content if hasattr(response, 'content') else str(response)
                            answer = answer.strip()
                            if not answer:
                                answer = "Not available in the uploaded document"
                        except Exception as retry_error:
                            logger.error(f"LLM error (retry failed): {retry_error}")
                            # Final fallback: use context directly if available
                            if context_text:
                                logger.warning("Using context directly as final fallback")
                                answer = f"I found information in the document related to your question. Here's what I found:\n\n{context_text[:1000]}..."
                                if len(context_text) > 1000:
                                    answer += "\n\n(Content truncated - there's more information in the document)"
                            else:
                                answer = "Error generating answer. Please try again."
            
            # Ensure answer is set before returning
            if not answer or not answer.strip():
                logger.error("Answer is empty after all processing attempts!")
                if context_text:
                    # Last resort: return context directly
                    answer = f"Based on the document content, here's what I found:\n\n{context_text[:800]}..."
                else:
                    answer = "I couldn't generate an answer. Please try rephrasing your question or ensure the document was uploaded correctly."
            
            logger.info(f"Returning answer with length: {len(answer)} characters")
            logger.info(f"Answer preview: {answer[:200]}...")
            
            # CRITICAL: Ensure answer is never empty when returning
            if not answer or not answer.strip():
                logger.error("CRITICAL: Answer is empty in generate_answer_node return! Using emergency fallback.")
                if context_text:
                    answer = f"Based on the document content: {context_text[:500]}..."
                else:
                    answer = "I couldn't generate an answer. Please try rephrasing your question."
            
            result_state = {**state, "answer": answer}
            logger.info(f"generate_answer_node returning state with answer length: {len(result_state.get('answer', ''))}")
            return result_state
        except Exception as e:
            logger.error(f"Error in generate_answer_node: {e}", exc_info=True)
            error_answer = "Error generating answer. Please try again."
            # Use answer if it was set, otherwise use error message
            final_answer = answer if (answer and answer.strip()) else error_answer
            return {**state, "answer": final_answer}
    
    def _check_visualization_node(self, state: GraphState) -> GraphState:
        """Node 3: Check if visualization is needed - ALWAYS generate chart if numerical data exists."""
        try:
            question = state.get("question", "")
            context_text = state.get("context_text", "")
            
            if not context_text:
                return {**state, "needs_visualization": False}
            
            # CRITICAL FIX: Check for meaningful numerical data directly in context
            import re
            # Look for patterns indicating meaningful numerical/tabular data (not just any numbers)
            has_percentages = bool(re.search(r'\d+%', context_text))
            has_tables = bool(re.search(r'\|\s*\w+', context_text) or 'table' in context_text.lower())
            has_comparisons = bool(re.search(r'\d+\s*(vs|versus|compared|than|more|less)', context_text, re.IGNORECASE))
            # Look for financial/metric keywords with numbers - ENHANCED for financial data
            financial_terms = r'\b(revenue|profit|sales|cost|budget|amount|value|percentage|ratio|count|total|average|growth|rate|income|expense|asset|liability|equity|earnings|margin|balance|statement|p&l|cash flow|financial)'
            has_meaningful_numbers = bool(
                re.search(f'{financial_terms}\s*[:\-]?\s*\d+', context_text, re.IGNORECASE) or
                re.search(r'\d+\s*(revenue|profit|sales|cost|budget|amount|value|percentage|ratio|count|total|average|growth|rate|income|expense|asset|liability|equity|earnings|margin|balance)', 
                         context_text, re.IGNORECASE) or
                re.search(r'\b(19|20)\d{2}\s*[:\-]?\s*\d+', context_text) or  # Year with value
                re.search(r'\b(balance sheet|income statement|cash flow|p&l|profit & loss|financial statement)', context_text, re.IGNORECASE)  # Financial statements
            )
            
            # Check user intent keywords
            question_lower = question.lower()
            visualization_keywords = ["show", "visualize", "chart", "graph", "compare", "trend", "display", "plot"]
            user_wants_viz = any(keyword in question_lower for keyword in visualization_keywords)
            # CRITICAL: Explicit table requests must always enable visualization path
            user_wants_table = "table" in question_lower
            # Financial data keywords - always trigger visualization
            financial_keywords = [
                "revenue", "profit", "sales", "cost", "budget", "balance", "income", "expense", 
                "asset", "liability", "equity", "earnings", "margin", "ratio", "growth", 
                "financial", "statement", "p&l", "profit & loss", "cash flow", "balance sheet",
                "income statement", "financial data", "financial metrics", "financial performance"
            ]
            user_asks_financial = any(keyword in question_lower for keyword in financial_keywords)
            
            # If meaningful numerical data exists OR user explicitly asks for visualization, generate chart
            if has_percentages or has_tables or has_comparisons or has_meaningful_numbers or user_wants_viz or user_wants_table or user_asks_financial:
                logger.info(f"Meaningful numerical data detected or user requested visualization (financial: {user_asks_financial}) - enabling chart generation")
                return {**state, "needs_visualization": True}
            
            # Fallback: Use LLM to detect if visualization is needed
            prompt = VISUALIZATION_DETECTION_PROMPT.format(
                question=question,
                context=context_text[:2000]  # Limit context for detection
            )
            
            try:
                response = self.llm.invoke(prompt)
                decision = response.content if hasattr(response, 'content') else str(response)
                decision = decision.strip().upper()
                
                needs_viz = "YES" in decision
                logger.info(f"Visualization needed (LLM decision): {needs_viz}")
                
                return {**state, "needs_visualization": needs_viz}
            except Exception as e:
                logger.error(f"Error checking visualization: {e}")
                # If LLM fails but we have meaningful numerical data, still generate chart
                if has_percentages or has_tables or has_meaningful_numbers:
                    return {**state, "needs_visualization": True}
                return {**state, "needs_visualization": False}
        except Exception as e:
            logger.error(f"Error in check_visualization_node: {e}")
            # On error, check if context has numbers - if yes, still try visualization
            context_text = state.get("context_text", "")
            if context_text:
                import re
                if re.search(r'\d+', context_text):
                    return {**state, "needs_visualization": True}
            return {**state, "needs_visualization": False}
    
    def _extract_data_node(self, state: GraphState) -> GraphState:
        """Node 4: Extract numerical data for visualization - STRICT SCHEMA REQUIRED."""
        try:
            question = state.get("question", "")
            context_text = state.get("context_text", "")
            
            # Check if user is asking for tables - prioritize table extraction
            question_lower = question.lower()
            # CRITICAL: Detect ANY mention of "table" or "tabular" in the question
            is_table_request = "table" in question_lower or "tabular" in question_lower
            
            if is_table_request:
                logger.info("User requested tables - using specialized table extraction")
                
                # CRITICAL: Try to extract tables directly from context first
                import re
                table_lines = []
                for line in context_text.split('\n'):
                    if '|' in line and line.count('|') >= 2:
                        # Check if it's not a separator row
                        if not re.match(r'^[\s\|:\-]+$', line.strip()):
                            table_lines.append(line)
                
                if table_lines and len(table_lines) >= 2:
                    logger.info(f"Found {len(table_lines)} table lines in context - extracting directly")
                    try:
                        # Parse the table
                        headers = []
                        rows = []
                        
                        # First line is headers
                        header_parts = table_lines[0].split('|')
                        for part in header_parts:
                            cleaned = part.strip().replace('**', '').replace('*', '').strip()
                            if cleaned:
                                headers.append(cleaned)
                        
                        # Remaining lines are data rows
                        for row_line in table_lines[1:]:
                            row_parts = row_line.split('|')
                            row_cells = []
                            for part in row_parts:
                                cleaned = part.strip().replace('**', '').replace('*', '').strip()
                                if cleaned or len(row_cells) < len(headers):
                                    row_cells.append(cleaned if cleaned else "-")
                            
                            # Skip separator rows
                            if all(re.match(r'^[\s\-:]+$', cell) for cell in row_cells if cell):
                                continue
                            
                            # Pad to match headers
                            while len(row_cells) < len(headers):
                                row_cells.append("-")
                            row_cells = row_cells[:len(headers)]
                            
                            if any(cell.strip() and cell.strip() != "-" for cell in row_cells):
                                rows.append(row_cells)
                        
                        if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                            logger.info(f"✅ Successfully extracted table from context: {len(headers)} columns, {len(rows)} rows")
                            # Normalize table structure
                            from app.rag.table_normalizer import TableNormalizer
                            normalized_table = TableNormalizer.normalize_table(headers, rows, "Document Table")
                            extracted_data = {
                                "chart_type": "table",
                                "headers": normalized_table["headers"],
                                "rows": normalized_table["rows"],
                                "title": normalized_table["title"]
                            }
                            return {**state, "extracted_data_for_chart": extracted_data}
                    except Exception as direct_parse_error:
                        logger.warning(f"Direct table parsing failed: {direct_parse_error}")
                
                # If direct extraction failed, try LLM extraction
                logger.info("Direct table extraction failed, trying LLM extraction")
                prompt = DATA_EXTRACTION_PROMPT.format(
                    question=question,
                    context=context_text
                )
                try:
                    response = self.llm.invoke(prompt)
                    response_text = response.content if hasattr(response, 'content') else str(response)
                    
                    if response_text.strip().lower() in ['null', 'none']:
                        logger.warning("LLM returned null for table extraction")
                        # Don't give up - return empty error so finalize can try again
                        return {**state, "extracted_data_for_chart": {"error": "No table data extracted, will retry in finalize"}}
                    
                    extracted_data = self.visualization_generator.parse_extracted_data(response_text)
                    
                    # Validate table data
                    if extracted_data and isinstance(extracted_data, dict) and extracted_data.get("chart_type") == "table":
                        headers = extracted_data.get("headers", [])
                        rows = extracted_data.get("rows", [])
                        if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                            # Normalize table structure
                            from app.rag.table_normalizer import TableNormalizer
                            normalized_table = TableNormalizer.normalize_table(
                                headers, 
                                rows, 
                                extracted_data.get("title")
                            )
                            extracted_data["headers"] = normalized_table["headers"]
                            extracted_data["rows"] = normalized_table["rows"]
                            extracted_data["title"] = normalized_table["title"]
                            logger.info(f"✅ Successfully extracted and normalized table: {len(normalized_table['headers'])} columns, {len(normalized_table['rows'])} rows")
                            return {**state, "extracted_data_for_chart": extracted_data}
                        else:
                            logger.warning(f"Table data validation failed - headers: {len(headers) if headers else 0}, rows: {len(rows) if rows else 0}")
                    else:
                        logger.warning(f"Extracted data is not a table format - chart_type: {extracted_data.get('chart_type') if isinstance(extracted_data, dict) else 'N/A'}")
                except Exception as table_error:
                    logger.error(f"Table extraction failed: {table_error}", exc_info=True)
            
            # Try structured_extractor first if available (uses Mistral with strict prompt) - for charts only
            extracted_data = None
            try:
                import os
                from app.rag.extraction.structured_extractor import StructuredDataExtractor
                mistral_key = os.getenv("MISTRAL_API_KEY") or (settings.mistral_api_key if hasattr(settings, 'mistral_api_key') else None)
                if mistral_key and not is_table_request:  # Don't use structured extractor for tables
                    extractor = StructuredDataExtractor(api_key=mistral_key)
                    # Extract from clean context text
                    extracted_data = extractor.extract_structured_data(context_text)
                    if extracted_data:
                        logger.info("Successfully extracted data using structured_extractor")
                    else:
                        logger.info("Structured extractor returned null - no meaningful data")
                else:
                    logger.debug("MISTRAL_API_KEY not available or table requested, using LLM extraction")
            except Exception as extractor_error:
                logger.debug(f"Structured extractor not available or failed: {extractor_error}, using LLM extraction")
            
            # Fallback to LLM extraction if structured_extractor didn't work
            if not extracted_data:
                prompt = DATA_EXTRACTION_PROMPT.format(
                    question=question,
                    context=context_text
                )
                
                try:
                    response = self.llm.invoke(prompt)
                    response_text = response.content if hasattr(response, 'content') else str(response)
                    
                    # Check for null response
                    if response_text.strip().lower() in ['null', 'none']:
                        logger.info("LLM returned null - no meaningful data")
                        if is_table_request:
                            logger.warning("User asked for table but extraction returned null - trying to extract any table-like data")
                        return {**state, "extracted_data_for_chart": {"error": "No meaningful extractable data"}}
                    
                    # Parse extracted data
                    extracted_data = self.visualization_generator.parse_extracted_data(response_text)
                    
                    # If user asked for table but got chart, log warning
                    if is_table_request and extracted_data and isinstance(extracted_data, dict):
                        if extracted_data.get("chart_type") != "table":
                            logger.warning(f"User asked for table but got {extracted_data.get('chart_type')} - this may not be what user wants")
                except Exception as llm_error:
                    logger.error(f"LLM extraction failed: {llm_error}")
                    return {**state, "extracted_data_for_chart": {"error": "Extraction failed"}}
            
            # Process extracted data
            # CRITICAL FIX: Validate strict schema FIRST
            if extracted_data and isinstance(extracted_data, dict):
                # Check if it's an error response or null
                if "error" in extracted_data:
                    error_msg = extracted_data.get("error", "")
                    if "meaningful" in error_msg.lower() or "no extractable" in error_msg.lower() or "null" in error_msg.lower():
                        logger.info("No meaningful data extracted - returning error")
                        return {**state, "extracted_data_for_chart": extracted_data}
                
                # Normalize data_type to chart_type for compatibility
                if "data_type" in extracted_data and "chart_type" not in extracted_data:
                    extracted_data["chart_type"] = extracted_data.pop("data_type")
                
                # Handle table type - validate separately
                if extracted_data.get("chart_type") == "table":
                    # Validate table schema
                    headers = extracted_data.get("headers", [])
                    rows = extracted_data.get("rows", [])
                    if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                        logger.info(f"✅ Table data validated successfully: {len(headers)} columns, {len(rows)} rows")
                        return {**state, "extracted_data_for_chart": extracted_data}
                    else:
                        logger.warning(f"Table data validation failed - headers: {len(headers) if headers else 0}, rows: {len(rows) if rows else 0}")
                        # Try to fix: if we have rows but no headers, infer from first row
                        if rows and len(rows) > 0 and not headers:
                            extracted_data["headers"] = [f"Column{i+1}" for i in range(len(rows[0]))]
                            logger.info("Inferred headers from first row")
                            return {**state, "extracted_data_for_chart": extracted_data}
                        # If user explicitly asked for table, return partial data anyway
                        if is_table_request and rows:
                            logger.warning("Table validation failed but user asked for table - returning partial data")
                            return {**state, "extracted_data_for_chart": extracted_data}
                        return {**state, "extracted_data_for_chart": {"error": "Invalid table data"}}
                
                # CRITICAL: Validate strict schema for charts - if it doesn't match, reject
                if not _validate_strict_schema(extracted_data):
                    logger.warning("Extracted data failed strict schema validation")
                    return {**state, "extracted_data_for_chart": {"error": "No meaningful extractable data"}}
                
                # Additional meaningfulness check
                if not _is_meaningful_data(extracted_data):
                    logger.warning("Extracted data failed meaningfulness validation")
                    return {**state, "extracted_data_for_chart": {"error": "No meaningful extractable data"}}
                
                # Deduplicate data
                extracted_data = _deduplicate_data(extracted_data)
                
                # Re-validate after deduplication
                if not _validate_strict_schema(extracted_data) or not _is_meaningful_data(extracted_data):
                    logger.warning("Data failed validation after deduplication")
                    return {**state, "extracted_data_for_chart": {"error": "No meaningful extractable data"}}
                
                # Ensure chart_type is valid (should already be from strict schema validation)
                if extracted_data.get("chart_type") not in ["bar", "line", "pie"]:
                    # Auto-detect chart type based on data
                    if extracted_data.get("values") and extracted_data.get("labels"):
                        labels = extracted_data.get("labels", [])
                        is_time_series = any(
                            re.search(r'\b(19|20)\d{2}\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', 
                                     str(label).lower()) for label in labels[:3]
                        )
                        extracted_data["chart_type"] = "line" if is_time_series else "bar"
                    else:
                        extracted_data["chart_type"] = "bar"
                
                return {**state, "extracted_data_for_chart": extracted_data}
            else:
                # No extracted data or not a dict
                logger.info("No extracted data or invalid format")
                return {**state, "extracted_data_for_chart": {"error": "No meaningful extractable data"}}
        except Exception as e:
            logger.error(f"Error in extract_data_node: {e}")
            return {**state, "extracted_data_for_chart": {"error": "Extraction failed"}}
    
    def _generate_chart_node(self, state: GraphState) -> GraphState:
        """Node 5: Generate visualization chart - with retry logic."""
        try:
            extracted_data = state.get("extracted_data_for_chart", {})
            
            if not extracted_data or "error" in extracted_data:
                logger.warning("No valid extracted data for chart generation")
                return {**state, "visualization": None}
            
            # Normalize chart_type (support both chart_type and data_type)
            if "data_type" in extracted_data and "chart_type" not in extracted_data:
                extracted_data["chart_type"] = extracted_data.pop("data_type")
            
            # Handle table type separately
            if isinstance(extracted_data, dict) and extracted_data.get("chart_type") == "table":
                logger.info("Generating table visualization")
                try:
                    chart_result = self.visualization_generator.generate_chart(extracted_data)
                    if chart_result and "error" not in chart_result:
                        logger.info("Table visualization generated successfully")
                        return {**state, "visualization": chart_result}
                    else:
                        logger.warning(f"Table generation returned error: {chart_result.get('error') if isinstance(chart_result, dict) else 'Unknown error'}")
                        return {**state, "visualization": None}
                except Exception as table_error:
                    logger.error(f"Error generating table: {table_error}", exc_info=True)
                    return {**state, "visualization": None}
            
            # CRITICAL FIX: Validate strict schema before generating chart (for non-table types)
            if not _validate_strict_schema(extracted_data):
                logger.warning("Extracted data does not match strict schema - cannot generate chart")
                return {**state, "visualization": None}
            
            # Generate chart with retry
            max_retries = 2
            chart_result = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    chart_result = self.visualization_generator.generate_chart(extracted_data)
                    
                    # Check if chart generation was successful
                    if chart_result and "error" not in chart_result:
                        logger.info(f"Chart generated successfully on attempt {attempt + 1}")
                        return {**state, "visualization": chart_result}
                    else:
                        # Chart generation returned an error, try again
                        if attempt < max_retries - 1:
                            logger.warning(f"Chart generation returned error, retrying... (attempt {attempt + 1}/{max_retries})")
                            time.sleep(0.5)  # Brief delay before retry
                            continue
                except Exception as e:
                    last_error = e
                    logger.warning(f"Chart generation failed on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(0.5)  # Brief delay before retry
                        continue
            
            # If all retries failed, log error but don't return None if we have data
            # Check for both chart data (values/labels) and table data (headers/rows)
            has_chart_data = extracted_data.get("values") and extracted_data.get("labels")
            has_table_data = extracted_data.get("headers") and extracted_data.get("rows")
            
            if has_chart_data or has_table_data:
                logger.error(f"Visualization generation failed after {max_retries} attempts: {last_error}")
                # Check if chart was requested
                question = state.get("question", "").lower()
                is_chart_req = any(kw in question for kw in ['chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization'])
                if is_chart_req:
                    # Update answer to error message instead of setting error in visualization
                    return {
                        **state,
                        "visualization": None,
                        "answer": "No structured numerical data available to generate a chart."
                    }
                return {**state, "visualization": None}
            
            return {**state, "visualization": None}
        except Exception as e:
            logger.error(f"Error in generate_chart_node: {e}")
            return {**state, "visualization": None}
    
    def _finalize_response_node(self, state: GraphState) -> GraphState:
        """Node 6: Finalize response - FORCE chart generation if numerical data exists."""
        try:
            answer = state.get("answer", "")
            visualization = state.get("visualization")
            extracted_data = state.get("extracted_data_for_chart", {})
            context_text = state.get("context_text", "")
            question = state.get("question", "")
            
            logger.info(f"Finalizing response. Answer length: {len(answer)} characters")
            logger.info(f"Answer preview: {answer[:200] if answer else 'EMPTY'}...")
            logger.info(f"Visualization present: {visualization is not None}")
            logger.info(f"Extracted data present: {extracted_data is not None}")
            
            # ============================================================
            # GLOBAL CHART INTENT DETECTION - MUST BE FIRST
            # ============================================================
            question_lower = question.lower()
            is_chart_request = any(kw in question_lower for kw in [
                'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
                'visualise', 'show chart', 'display chart', 'give me chart', 'give me charts',
                'generate chart', 'create chart', 'plot', 'plotting', 'show charts'
            ])
            
            logger.info(f"🎯 GRAPH FINALIZE: is_chart_request = {is_chart_request}")
            
            # ============================================================
            # CRITICAL EARLY BLOCK: If chart requested and visualization is table, BLOCK NOW
            # ============================================================
            if is_chart_request and visualization and isinstance(visualization, dict):
                viz_chart_type = visualization.get("chart_type") or visualization.get("type")
                if viz_chart_type == "table":
                    logger.error(f"❌ GRAPH FINALIZE BLOCK: visualization is table when chart requested - setting to None")
                    visualization = None  # Will trigger error response
                # Check for headers/rows without labels/values (hidden table)
                elif visualization.get("headers") and visualization.get("rows") and not visualization.get("labels"):
                    logger.error(f"❌ GRAPH FINALIZE BLOCK: visualization has headers/rows but no labels - setting to None")
                    visualization = None  # Will trigger error response
            
            # CRITICAL: If answer is empty, something went wrong - use fallback
            if not answer or not answer.strip():
                logger.error("Answer is empty in finalize_response_node! Using fallback.")
                if context_text:
                    # Try to generate a simple answer from context
                    try:
                        logger.info("Attempting to generate answer from context in finalize_response_node...")
                        from app.rag.prompts import RAG_PROMPT
                        prompt = RAG_PROMPT.format(context=context_text[:2000], question=question)  # Limit context for speed
                        response = self.llm.invoke(prompt)
                        answer = response.content if hasattr(response, 'content') else str(response)
                        answer = answer.strip()
                        logger.info(f"Generated fallback answer with length: {len(answer)} characters")
                        if not answer:
                            # Last resort: return context directly
                            answer = f"Based on the document content: {context_text[:800]}..."
                    except Exception as fallback_error:
                        logger.error(f"Fallback answer generation failed: {fallback_error}")
                        if context_text:
                            answer = f"I found information in the document. Here's what I found: {context_text[:800]}..."
                        else:
                            answer = "I found information in the document but couldn't generate a proper answer. Please try rephrasing your question."
                else:
                    answer = "I couldn't find any relevant information in the uploaded document. Please ensure the PDF was processed correctly."
            
            # Store original answer before cleaning (in case cleaning removes everything)
            original_answer = answer
            
            # Check if user asked for tables (but NOT if they asked for charts)
            # question_lower already defined above
            is_table_request = ("table" in question_lower or "tabular" in question_lower) and not is_chart_request
            
            # CRITICAL FIX: If visualization is None but we have numerical data, force chart generation
            if not visualization or (isinstance(visualization, dict) and "error" in visualization):
                # If user asked for table, prioritize table generation
                if is_table_request and context_text:
                    logger.info("User asked for table but no visualization - forcing table extraction from context")
                    # Try to extract table directly from context
                    try:
                        import re
                        # Look for financial data patterns in context
                        # Extract key-value pairs or structured data
                        financial_patterns = [
                            r'(\w+(?:\s+\w+)*)\s*[:\-]?\s*([\d,]+\.?\d*)',
                            r'(\d{2}-\d{2}-\d{4})\s*[:\-]?\s*([\d,]+\.?\d*)',
                        ]
                        
                        # Try to find table-like structures
                        table_lines = []
                        for line in context_text.split('\n'):
                            if '|' in line and line.count('|') >= 2:
                                table_lines.append(line)
                        
                        if table_lines and len(table_lines) >= 2:
                            logger.info(f"Found {len(table_lines)} table lines in context - extracting")
                            # Parse table from context
                            headers = []
                            rows = []
                            
                            # First line is headers
                            header_parts = table_lines[0].split('|')
                            for part in header_parts:
                                cleaned = part.strip().replace('**', '').replace('*', '').strip()
                                if cleaned:
                                    headers.append(cleaned)
                            
                            # Remaining lines are data rows
                            for row_line in table_lines[1:]:
                                row_parts = row_line.split('|')
                                row_cells = []
                                for part in row_parts:
                                    cleaned = part.strip().replace('**', '').replace('*', '').strip()
                                    if cleaned or len(row_cells) < len(headers):
                                        row_cells.append(cleaned if cleaned else "-")
                                
                                # Skip separator rows
                                if all(re.match(r'^[\s\-:]+$', cell) for cell in row_cells if cell):
                                    continue
                                
                                # Pad to match headers
                                while len(row_cells) < len(headers):
                                    row_cells.append("-")
                                row_cells = row_cells[:len(headers)]
                                
                                if any(cell.strip() and cell.strip() != "-" for cell in row_cells):
                                    rows.append(row_cells)
                            
                            if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                                logger.info(f"✅ Extracted table from context: {len(headers)} columns, {len(rows)} rows")
                                # Generate table visualization
                                table_data = {
                                    "chart_type": "table",
                                    "headers": headers,
                                    "rows": rows,
                                    "title": "Financial Data"
                                }
                                table_viz = self.visualization_generator.generate_chart(table_data)
                                if table_viz and "error" not in table_viz:
                                    visualization = table_viz
                                    logger.info("✅ Successfully generated table visualization from context")
                    except Exception as context_extract_error:
                        logger.error(f"Failed to extract table from context: {context_extract_error}", exc_info=True)
                    
                    # CRITICAL FALLBACK: If no markdown tables found, extract financial data and create table
                    if not visualization and is_table_request and context_text:
                        logger.info("No markdown tables found - extracting financial data from text to create table")
                        try:
                            import re
                            # Extract financial data patterns from context
                            financial_data = []
                            
                            # Pattern 1: Look for financial terms with numbers
                            patterns = [
                                (r'(Total\s+(?:Assets|Equity|Liabilities|Income|Expenditure|Expenses?))\s*[:\-]?\s*([\d,]+\.?\d*)', 'Financial Metric'),
                                (r'(Revenue|Profit|Loss|Sales|Cost|Budget|Amount|Value)\s*(?:from|of|before|after)?\s*[:\-]?\s*([\d,]+\.?\d*)', 'Financial Metric'),
                                (r'(\d{2}-\d{2}-\d{4})\s*[:\-]?\s*([\d,]+\.?\d*)', 'Date'),
                                (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[:\-]?\s*([\d,]+\.?\d*)', 'Metric'),
                            ]
                            
                            # Extract all matches
                            for pattern, label_type in patterns:
                                matches = re.finditer(pattern, context_text, re.IGNORECASE)
                                for match in matches:
                                    label = match.group(1).strip()
                                    value = match.group(2).strip()
                                    # Clean value
                                    value_clean = value.replace(',', '').replace('₹', '').replace('$', '').replace('Rs.', '').replace('Rs', '').strip()
                                    try:
                                        float(value_clean)  # Validate it's a number
                                        financial_data.append((label, value))
                                    except:
                                        pass
                            
                            # If we found financial data, create a table
                            if financial_data and len(financial_data) >= 2:
                                logger.info(f"Found {len(financial_data)} financial data points - creating table")
                                
                                # Group by date if dates are present, otherwise create simple table
                                dates = set()
                                metrics = {}
                                
                                for label, value in financial_data:
                                    # Check if label is a date
                                    if re.match(r'\d{2}-\d{2}-\d{4}', label):
                                        dates.add(label)
                                    else:
                                        if label not in metrics:
                                            metrics[label] = []
                                        metrics[label].append(value)
                                
                                # Create table structure
                                if dates and len(dates) >= 2:
                                    # Multi-year table
                                    headers = ["Particulars"] + sorted(list(dates))
                                    rows = []
                                    for metric, values in metrics.items():
                                        row = [metric] + values[:len(headers)-1]
                                        while len(row) < len(headers):
                                            row.append("-")
                                        rows.append(row[:len(headers)])
                                else:
                                    # Simple two-column table
                                    headers = ["Particulars", "Amount"]
                                    rows = [[label, value] for label, value in financial_data[:20]]  # Limit to 20 rows
                                
                                if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                                    logger.info(f"✅ Created table from financial data: {len(headers)} columns, {len(rows)} rows")
                                    table_data = {
                                        "chart_type": "table",
                                        "headers": headers,
                                        "rows": rows,
                                        "title": "Financial Data"
                                    }
                                    table_viz = self.visualization_generator.generate_chart(table_data)
                                    if table_viz and "error" not in table_viz:
                                        visualization = table_viz
                                        logger.info("✅ Successfully generated table visualization from financial data extraction")
                                    else:
                                        # Fallback: use raw structure
                                        visualization = {
                                            "chart_type": "table",
                                            "headers": headers,
                                            "rows": rows,
                                            "title": "Financial Data"
                                        }
                                        logger.warning("Table generation failed, using raw structure")
                        except Exception as fallback_error:
                            logger.error(f"Financial data extraction fallback failed: {fallback_error}", exc_info=True)
                
                # Check if we have extracted data with values and labels
                if extracted_data and isinstance(extracted_data, dict):
                    # Check if it's an error indicating no meaningful data
                    if "error" in extracted_data:
                        error_msg = extracted_data.get("error", "").lower()
                        if "meaningful" in error_msg or "no extractable" in error_msg:
                            logger.info("No meaningful data available for visualization")
                            # CRITICAL: Only overwrite answer if user explicitly asked for visualization/chart/table
                            # If user asked for summary or general question, keep the original answer
                            question_lower = question.lower()
                            needs_viz = state.get("needs_visualization", False)
                            if needs_viz and ("chart" in question_lower or "graph" in question_lower or "visualize" in question_lower or "plot" in question_lower):
                                answer = "No meaningful numerical data suitable for visualization was found in the document."
                            # Otherwise, keep the original answer (summary, etc.)
                            final_response = {
                                "answer": answer,  # Keep original answer if not visualization request
                                "visualization": None
                            }
                            return {**state, "final_response": final_response}
                    
                    # Validate data is meaningful before generating chart
                    if not _is_meaningful_data(extracted_data):
                        logger.info("Extracted data is not meaningful - skipping chart generation")
                        # CRITICAL: Only overwrite answer if user explicitly asked for visualization
                        question_lower = question.lower()
                        needs_viz = state.get("needs_visualization", False)
                        if needs_viz and ("chart" in question_lower or "graph" in question_lower or "visualize" in question_lower or "plot" in question_lower):
                            answer = "No meaningful numerical data suitable for visualization was found in the document."
                        # Otherwise, keep the original answer
                        final_response = {
                            "answer": answer,  # Keep original answer if not visualization request
                            "visualization": None
                        }
                        return {**state, "final_response": final_response}
                    
                    values = extracted_data.get("values", [])
                    labels = extracted_data.get("labels", [])
                    
                    # Check for table data first (headers/rows)
                    headers = extracted_data.get("headers", [])
                    rows = extracted_data.get("rows", [])
                    if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                        # Handle table type
                        logger.info("Forcing table generation from extracted data")
                        if "data_type" in extracted_data and "chart_type" not in extracted_data:
                            extracted_data["chart_type"] = extracted_data.pop("data_type")
                        if extracted_data.get("chart_type") != "table":
                            extracted_data["chart_type"] = "table"
                        
                        # Try to generate table
                        try:
                            table_viz = self.visualization_generator.generate_chart(extracted_data)
                            if table_viz and "error" not in table_viz:
                                visualization = table_viz
                                logger.info("Successfully generated table in finalize_response_node")
                            else:
                                logger.warning("Table generation failed in finalize_response_node")
                        except Exception as table_error:
                            logger.error(f"Failed to generate table in finalize_response: {table_error}")
                    elif values and labels and len(values) >= 2 and len(labels) >= 2:
                        # Handle chart data (bar/line/pie)
                        logger.info("Forcing chart generation from extracted data")
                        # Normalize to strict schema
                        if "data_type" in extracted_data and "chart_type" not in extracted_data:
                            extracted_data["chart_type"] = extracted_data.pop("data_type")
                        # Ensure chart_type is valid (but don't convert table to bar)
                        if extracted_data.get("chart_type") == "table":
                            # If we have values/labels but chart_type is table, it's wrong - use bar
                            extracted_data["chart_type"] = "bar"
                        if extracted_data.get("chart_type") not in ["bar", "line", "pie"]:
                            extracted_data["chart_type"] = "bar"
                        
                        # Validate strict schema before generating
                        if not _validate_strict_schema(extracted_data):
                            logger.warning("Data does not match strict schema - cannot generate chart")
                            answer = "No meaningful numerical data suitable for visualization was found in the document."
                            final_response = {
                                "answer": answer,
                                "visualization": None
                            }
                            return {**state, "final_response": final_response}
                        
                        # Try to generate chart one more time
                        try:
                            visualization = self.visualization_generator.generate_chart(extracted_data)
                            if visualization and "error" not in visualization:
                                logger.info("Successfully generated chart in finalize_response_node")
                        except Exception as e:
                            logger.error(f"Failed to generate chart in finalize_response: {e}")
                            visualization = None  # Don't set error object, just return None
                            # Update answer if chart was requested
                            if is_chart_request:
                                answer = "No structured numerical data available to generate a chart."
                else:
                    # Check if context has numerical data and user asked for visualization
                    question_lower = question.lower()
                    viz_keywords = ["show", "visualize", "chart", "graph", "display", "plot"]
                    if any(kw in question_lower for kw in viz_keywords) and context_text:
                        # Try to extract and generate chart from context
                        import re
                        if re.search(r'\d+[.,]?\d*', context_text):
                            logger.info("Attempting to extract and generate chart from context")
                            try:
                                prompt = DATA_EXTRACTION_PROMPT.format(
                                    question=question,
                                    context=context_text
                                )
                                response = self.llm.invoke(prompt)
                                response_text = response.content if hasattr(response, 'content') else str(response)
                                extracted_data = self.visualization_generator.parse_extracted_data(response_text)
                                
                                if extracted_data and isinstance(extracted_data, dict):
                                    # Validate meaningfulness
                                    if "error" in extracted_data:
                                        error_msg = extracted_data.get("error", "").lower()
                                        if "meaningful" in error_msg or "no extractable" in error_msg:
                                            answer = "No meaningful numerical data suitable for visualization was found in the document."
                                            final_response = {
                                                "answer": answer,
                                                "visualization": None
                                            }
                                            return {**state, "final_response": final_response}
                                    
                                    if not _is_meaningful_data(extracted_data):
                                        answer = "No meaningful numerical data suitable for visualization was found in the document."
                                        final_response = {
                                            "answer": answer,
                                            "visualization": None
                                        }
                                        return {**state, "final_response": final_response}
                                    
                                    # Normalize to strict schema
                                    if "data_type" in extracted_data and "chart_type" not in extracted_data:
                                        extracted_data["chart_type"] = extracted_data.pop("data_type")
                                    if extracted_data.get("chart_type") == "table":
                                        extracted_data["chart_type"] = "bar"
                                    
                                    # Validate strict schema
                                    if not _validate_strict_schema(extracted_data):
                                        answer = "No meaningful numerical data suitable for visualization was found in the document."
                                        final_response = {
                                            "answer": answer,
                                            "visualization": None
                                        }
                                        return {**state, "final_response": final_response}
                                    
                                    # Handle both chart data (values/labels) and table data (headers/rows)
                                    if extracted_data.get("chart_type") == "table":
                                        # Generate table visualization
                                        try:
                                            table_viz = self.visualization_generator.generate_chart(extracted_data)
                                            if table_viz and "error" not in table_viz:
                                                visualization = table_viz
                                                logger.info("Successfully generated table from context extraction")
                                        except Exception as table_error:
                                            logger.error(f"Failed to generate table: {table_error}")
                                    elif extracted_data.get("values") and extracted_data.get("labels"):
                                        visualization = self.visualization_generator.generate_chart(extracted_data)
                            except Exception as e:
                                logger.error(f"Failed to extract and generate chart: {e}")
            
            # If no visualization and user asked for it, provide specific message
            question_lower = question.lower()
            viz_keywords = ["show", "visualize", "chart", "graph", "display", "plot"]
            user_asked_for_viz = any(kw in question_lower for kw in viz_keywords)
            
            if user_asked_for_viz and (not visualization or (isinstance(visualization, dict) and "error" in visualization)):
                # Check if we have meaningful data
                if extracted_data and isinstance(extracted_data, dict):
                    if "error" in extracted_data:
                        error_msg = extracted_data.get("error", "").lower()
                        if "meaningful" in error_msg or "no extractable" in error_msg:
                            answer = "No meaningful numerical data suitable for visualization was found in the document."
                            visualization = None
                    elif not _is_meaningful_data(extracted_data):
                        answer = "No meaningful numerical data suitable for visualization was found in the document."
                        visualization = None
            
            # Clean up answer - remove disallowed phrases, tables, and multiple chart references
            if answer:
                disallowed_phrases = [
                    "the document does not provide a chart",
                    "i will present the data as a table instead",
                    "cannot generate a chart",
                    "no chart available"
                ]
                for phrase in disallowed_phrases:
                    if phrase.lower() in answer.lower():
                        # Replace with simple message
                        answer = answer.replace(phrase, "").strip()
                        if not answer:
                            answer = "Here is the data visualization:"
                
                # CRITICAL FIX: Parse markdown/ASCII tables in the answer and convert to strict Markdown tables.
                import re
                
                # Comprehensive markdown table parser - find ALL tables in the answer
                lines = answer.split('\n')
                all_tables = []
                current_table = []
                in_table = False
                last_was_separator = False
                
                for i, line in enumerate(lines):
                    stripped_line = line.strip()
                    # Check if line looks like a table row (has | separators)
                    if '|' in stripped_line and stripped_line.count('|') >= 2:
                        # Check if it's a separator row (only dashes, colons, spaces, pipes)
                        is_separator = bool(re.match(r'^[\s\|:\-]+$', stripped_line))
                        
                        if is_separator:
                            # Separator row - mark that we're in a table
                            if current_table:
                                last_was_separator = True
                                in_table = True
                            continue
                        else:
                            # Data row
                            if not in_table and not current_table:
                                # Start of a new table
                                current_table = [(i, line)]
                                in_table = True
                                last_was_separator = False
                            elif in_table:
                                # Continue current table
                                current_table.append((i, line))
                                last_was_separator = False
                    else:
                        # Not a table row
                        if in_table and current_table:
                            # End of table - save it if it has at least header + 1 data row
                            if len(current_table) >= 2 or (len(current_table) >= 1 and last_was_separator):
                                all_tables.append(current_table)
                            current_table = []
                            in_table = False
                            last_was_separator = False
                
                # Don't forget the last table if answer ends with a table
                if current_table and (len(current_table) >= 2 or (len(current_table) >= 1 and last_was_separator)):
                    all_tables.append(current_table)
                
                # Parse the largest/most complete table
                if all_tables and (not visualization or not isinstance(visualization, dict) or not visualization.get("headers")):
                    # Sort by size (number of rows) and take the largest
                    all_tables.sort(key=len, reverse=True)
                    table_lines = all_tables[0]
                    
                    logger.info(f"Found {len(all_tables)} table(s) in answer, parsing largest one with {len(table_lines)} rows...")
                    try:
                        # First line is headers
                        header_line = table_lines[0][1]
                        # Split by | and clean - preserve empty cells to maintain column structure
                        header_parts = header_line.split('|')
                        headers = []
                        for part in header_parts:
                            cleaned = part.strip().replace('**', '').replace('*', '').strip()
                            # Include empty parts to maintain column count, but skip if it's just whitespace
                            if cleaned or len(headers) == 0:  # Always include first, then only non-empty
                                if cleaned:
                                    headers.append(cleaned)
                                elif len(headers) > 0:  # Empty cell after headers started
                                    headers.append("")
                        
                        # Remove empty headers at the end
                        while headers and not headers[-1]:
                            headers.pop()
                        
                        if len(headers) >= 2:
                            # Parse data rows
                            rows = []
                            for idx, row_line in table_lines[1:]:
                                row_parts = row_line.split('|')
                                row_cells = []
                                for part in row_parts:
                                    # Clean cell: remove markdown formatting, preserve content
                                    cleaned = part.strip().replace('**', '').replace('*', '').strip()
                                    # Preserve empty cells and dashes
                                    if cleaned == "":
                                        cleaned = "-"
                                    row_cells.append(cleaned)
                                
                                # Skip separator rows (lines with only dashes/colons/spaces)
                                if all(re.match(r'^[\s\-:]+$', cell) for cell in row_cells if cell):
                                    continue
                                
                                # Pad or truncate to match header count exactly
                                while len(row_cells) < len(headers):
                                    row_cells.append("-")
                                row_cells = row_cells[:len(headers)]
                                
                                # Include row if it has at least one non-empty cell (not just dashes)
                                if any(cell.strip() and cell.strip() != "-" for cell in row_cells):
                                    rows.append(row_cells)
                            
                            if rows:
                                logger.info(f"✅ Successfully converted markdown table: {len(headers)} columns, {len(rows)} rows")
                                logger.info(f"Headers: {headers}")
                                logger.info(f"Sample rows: {rows[:2]}")
                                # Create table visualization - MUST generate through visualization_generator
                                try:
                                    table_data = {
                                        "chart_type": "table",
                                        "headers": headers,
                                        "rows": rows,
                                        "title": "Extracted Table"
                                    }
                                    table_viz = self.visualization_generator.generate_chart(table_data)
                                    if table_viz and "error" not in table_viz:
                                        visualization = table_viz
                                        logger.info("✅ Successfully generated table visualization from parsed markdown")
                                    else:
                                        # Fallback: use raw structure if generation fails
                                        visualization = {
                                            "chart_type": "table",
                                            "headers": headers,
                                            "rows": rows,
                                            "title": "Extracted Table"
                                        }
                                        logger.warning("Table generation returned error, using raw structure")
                                except Exception as gen_error:
                                    logger.error(f"Failed to generate table visualization: {gen_error}")
                                    # Fallback: use raw structure
                                    visualization = {
                                        "chart_type": "table",
                                        "headers": headers,
                                        "rows": rows,
                                        "title": "Extracted Table"
                                    }
                            else:
                                logger.warning("Parsed headers but no valid rows found")
                        else:
                            logger.warning(f"Insufficient headers found: {len(headers)}")
                    except Exception as parse_error:
                        logger.error(f"Failed to parse markdown table: {parse_error}", exc_info=True)

                # CRITICAL: For explicit table requests, if we detected ANY table blocks (even imperfect),
                # rebuild the answer as STRICT markdown tables (and nothing else).
                if is_table_request and all_tables:
                    logger.info(f"Table request detected. Rebuilding answer from {len(all_tables)} detected table block(s).")

                    def _clean_title(s: str) -> str:
                        s = (s or "").strip()
                        s = re.sub(r'^[\*\s]+|[\*\s]+$', '', s)  # strip surrounding * and spaces
                        s = s.replace("**", "").replace("*", "").strip()
                        return s

                    def _infer_table_title(table_block, all_lines):
                        """Try to find a nearby title line above the header."""
                        if not table_block:
                            return ""
                        header_idx = table_block[0][0]
                        j = header_idx - 1
                        while j >= 0:
                            cand = all_lines[j].strip()
                            if not cand:
                                j -= 1
                                continue
                            # ignore obvious prefaces
                            if '|' in cand or re.match(r'^[\s\+\-\=\|]{5,}$', cand):
                                j -= 1
                                continue
                            if re.search(r'(here is|this table|the following|tabular data|summary)', cand, re.IGNORECASE):
                                j -= 1
                                continue
                            cand = _clean_title(cand)
                            # keep it reasonably short
                            if 0 < len(cand) <= 120:
                                return cand
                            break
                        return ""

                    def _parse_table_block(table_block):
                        """Parse a table block (list of (idx, line)) into headers/rows."""
                        if not table_block:
                            return None
                        header_line = table_block[0][1]
                        raw_headers = [c.strip() for c in header_line.split('|')]
                        # drop empty leading/trailing cells
                        while raw_headers and raw_headers[0] == "":
                            raw_headers.pop(0)
                        while raw_headers and raw_headers[-1] == "":
                            raw_headers.pop()
                        headers = [_clean_title(h) if _clean_title(h) else "-" for h in raw_headers]
                        if len(headers) < 2:
                            return None
                        rows = []
                        for _, row_line in table_block[1:]:
                            if re.match(r'^[\s\|:\-]+$', row_line.strip()):
                                continue
                            if re.match(r'^[\s\+\-\=\|]{5,}$', row_line.strip()):
                                continue
                            raw_cells = [c.strip() for c in row_line.split('|')]
                            while raw_cells and raw_cells[0] == "":
                                raw_cells.pop(0)
                            while raw_cells and raw_cells[-1] == "":
                                raw_cells.pop()
                            cells = [(_clean_title(c) if _clean_title(c) else "-") for c in raw_cells]
                            # pad/truncate
                            while len(cells) < len(headers):
                                cells.append("-")
                            cells = cells[:len(headers)]
                            if any(c != "-" for c in cells):
                                rows.append(cells)
                        if not rows:
                            return None
                        return {"headers": headers, "rows": rows}

                    # Prefer larger tables first; keep up to 5 to avoid runaway output
                    sorted_tables = sorted(all_tables, key=len, reverse=True)[:5]
                    md_parts = []
                    for idx, tbl in enumerate(sorted_tables, start=1):
                        parsed = _parse_table_block(tbl)
                        if not parsed:
                            continue
                        title = _infer_table_title(tbl, lines) or f"Table {idx}"
                        # Generate strict markdown via visualization generator
                        table_viz = self.visualization_generator.generate_chart({
                            "chart_type": "table",
                            "headers": parsed["headers"],
                            "rows": parsed["rows"],
                            "title": title
                        })
                        table_md = None
                        if isinstance(table_viz, dict):
                            table_md = (table_viz.get("markdown") or "").strip()
                        if not table_md:
                            # fallback: build minimal strict markdown
                            header_row = "| " + " | ".join(parsed["headers"]) + " |"
                            sep_row = "| " + " | ".join(["---"] * len(parsed["headers"])) + " |"
                            body = "\n".join("| " + " | ".join(r) + " |" for r in parsed["rows"])
                            table_md = "\n".join([header_row, sep_row, body]).strip()

                        # Rule: if multiple tables exist, separate with a clear heading
                        if len(sorted_tables) > 1:
                            md_parts.append(f"### {title}\n{table_md}")
                        else:
                            md_parts.append(table_md)

                    if md_parts:
                        # STRICT: no explanatory text before/after tables
                        answer = "\n\n".join(md_parts).strip()
                        # CRITICAL: Keep visualization object so frontend can render HTML table
                        # Don't set visualization = None - the frontend needs it!
                        logger.info("Rebuilt answer as strict markdown table(s). Keeping visualization object for frontend rendering.")
                    else:
                        logger.warning("Detected table blocks but failed to parse any into strict markdown.")
                
                
                # Check if we have a table visualization
                has_table_viz = (
                    visualization and 
                    isinstance(visualization, dict) and 
                    (visualization.get("chart_type") == "table" or 
                     (visualization.get("headers") and visualization.get("rows")))
                )
                
                # Remove markdown tables AND ASCII art tables (lines with |, +, -, = separators) - always clean these
                # Create a set of line indices that are part of tables
                table_line_indices = set()
                for table in all_tables:
                    for idx, _ in table:
                        table_line_indices.add(idx)
                
                cleaned_lines = []
                skip_next_separator = False
                for i, line in enumerate(lines):
                    # Skip lines that are part of tables
                    if i in table_line_indices:
                        skip_next_separator = True
                        continue
                    
                    # Check if line looks like a markdown table row (contains |)
                    if '|' in line and line.count('|') >= 2:
                        # Skip table rows - they'll be shown in the visualization
                        skip_next_separator = True
                        continue
                    
                    # Check if line is an ASCII art table border (contains +, -, =, or multiple dashes)
                    # Pattern: lines with +, -, =, or multiple consecutive dashes/equals
                    if re.match(r'^[\s\+\-\=\|]+$', line.strip()) and len(line.strip()) > 3:
                        # ASCII art table border - skip it
                        skip_next_separator = True
                        continue
                    
                    # Check if line is a markdown table separator (contains --- or ===)
                    if re.match(r'^[\s\|:\-]+$', line.strip()):
                        if skip_next_separator:
                            skip_next_separator = False
                            continue
                        # Skip table separators
                        continue
                    skip_next_separator = False
                    
                    # Check if line says "Chart:", "Table:", or similar headers
                    if re.match(r'^(Chart|Table|Here is|This table|The following table)\s*:?\s*$', line, re.IGNORECASE):
                        # Skip these headers when we have a table viz
                        if has_table_viz:
                            continue
                    
                    # Remove lines that describe tables when we have table visualization
                    if has_table_viz:
                        if re.search(r'(summarizes|presents|shows|relevant data|extracted from).*(table|tabular|data)', line, re.IGNORECASE):
                            # Skip descriptive text about tables
                            continue
                        if re.search(r'this table|the table|following table|above table|tabular format', line, re.IGNORECASE):
                            # Skip references to tables
                            continue
                    
                    # Remove ASCII art table patterns (lines with +, multiple dashes, etc.)
                    if re.search(r'^[\s\+\-\=\|]{5,}', line.strip()):
                        # ASCII art border - skip
                        continue
                    
                    cleaned_lines.append(line)
                answer = '\n'.join(cleaned_lines).strip()
                
                # If we have a table visualization and answer is mostly empty or just descriptive, replace with simple message
                if has_table_viz:
                    # Remove any remaining table-related text and ASCII art
                    answer = re.sub(r'this table.*summarizes.*', '', answer, flags=re.IGNORECASE)
                    answer = re.sub(r'here is.*relevant data.*tabular.*', '', answer, flags=re.IGNORECASE)
                    answer = re.sub(r'the following.*table.*', '', answer, flags=re.IGNORECASE)
                    answer = re.sub(r'presented.*tabular.*format', '', answer, flags=re.IGNORECASE)
                    # Remove ASCII art patterns
                    answer = re.sub(r'[\+\-\=\|]{3,}.*[\+\-\=\|]{3,}', '', answer, flags=re.MULTILINE)
                    answer = answer.strip()
                    # If answer is empty or very short, use a simple message
                    if not answer or len(answer) < 30:
                        answer = "Here is the requested table:"
                
                # Remove references to multiple charts (Chart 1, Chart 2, etc.)
                # Remove patterns like "Chart 1:", "Chart 2:", etc.
                answer = re.sub(r'Chart\s+\d+\s*:?\s*', '', answer, flags=re.IGNORECASE)
                # Remove patterns like "Numerical Data", "Financial Data", "Yearly Data" as separate chart titles
                answer = re.sub(r'(Numerical Data|Financial Data|Yearly Data|Monthly Data|Quarterly Data)\s*:?\s*', '', answer, flags=re.IGNORECASE)
                # Remove standalone "Chart:" labels
                answer = re.sub(r'^Chart\s*:?\s*$', '', answer, flags=re.IGNORECASE | re.MULTILINE)
                # Clean up multiple newlines
                answer = re.sub(r'\n{3,}', '\n\n', answer)
                answer = answer.strip()
                
                # CRITICAL: If cleaning removed everything, restore original (but NEVER for explicit table requests
                # when we already detected table blocks; in that case we must not reintroduce broken ASCII tables).
                if (not answer or len(answer) < 10) and not (is_table_request and all_tables):
                    logger.warning("Answer was too aggressively cleaned, restoring original")
                    answer = original_answer.strip()
                    if not answer:
                        answer = "I found information in the document but couldn't format it properly."
                
                # If visualization exists, provide a simple summary
                if visualization and not (isinstance(visualization, dict) and "error" in visualization):
                    # Check if it's a table
                    if isinstance(visualization, dict) and visualization.get("chart_type") == "table":
                        if not answer or len(answer) < 20:
                            answer = "Here is the requested table:"
                    else:
                        if not answer or len(answer) < 20:
                            answer = "Here is the numerical data visualization from the document:"
            
            # Final safety check - ensure answer is never empty
            if not answer or not answer.strip():
                logger.error("Answer is still empty after all processing! Using emergency fallback.")
                if context_text:
                    answer = f"Based on the document: {context_text[:500]}..."
                else:
                    answer = "I processed your question but couldn't generate a response. Please try rephrasing or check if the document contains relevant information."
            
            # CRITICAL: If user asked for table but we still don't have visualization, force extraction
            if is_table_request and (not visualization or (isinstance(visualization, dict) and "error" in visualization)):
                logger.warning("User asked for table but no visualization exists - forcing final extraction attempt")
                try:
                    # Use DATA_EXTRACTION_PROMPT to force table extraction
                    prompt = DATA_EXTRACTION_PROMPT.format(
                        question=question + " Extract as table with headers and rows.",
                        context=context_text[:4000]  # Use more context
                    )
                    response = self.llm.invoke(prompt)
                    response_text = response.content if hasattr(response, 'content') else str(response)
                    
                    if response_text and response_text.strip().lower() not in ['null', 'none']:
                        extracted_data = self.visualization_generator.parse_extracted_data(response_text)
                        
                        if extracted_data and isinstance(extracted_data, dict) and extracted_data.get("chart_type") == "table":
                            headers = extracted_data.get("headers", [])
                            rows = extracted_data.get("rows", [])
                            if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                                logger.info(f"✅ Final extraction successful: {len(headers)} columns, {len(rows)} rows")
                                table_data = {
                                    "chart_type": "table",
                                    "headers": headers,
                                    "rows": rows,
                                    "title": "Financial Data"
                                }
                                table_viz = self.visualization_generator.generate_chart(table_data)
                                if table_viz and "error" not in table_viz:
                                    visualization = table_viz
                                    logger.info("✅ Successfully generated table visualization from final extraction")
                                else:
                                    visualization = {
                                        "chart_type": "table",
                                        "headers": headers,
                                        "rows": rows,
                                        "title": "Financial Data"
                                    }
                except Exception as final_error:
                    logger.error(f"Final table extraction attempt failed: {final_error}", exc_info=True)
            
            # If we converted a markdown table to structured format, make sure it's included
            if visualization and isinstance(visualization, dict) and visualization.get("chart_type") == "table":
                logger.info(f"Finalizing response with table visualization: {len(visualization.get('headers', []))} columns, {len(visualization.get('rows', []))} rows")
                # Ensure visualization has required fields
                if not visualization.get("headers") or not visualization.get("rows"):
                    logger.error("Visualization missing headers or rows!")
                else:
                    logger.info(f"Visualization ready: {len(visualization.get('headers'))} headers, {len(visualization.get('rows'))} rows")
            
            # ============================================================
            # FINAL GRAPH GUARD: If chart requested, NEVER return table
            # ============================================================
            if is_chart_request and visualization and isinstance(visualization, dict):
                viz_chart_type = visualization.get("chart_type") or visualization.get("type")
                has_table_structure = (visualization.get("headers") and visualization.get("rows") and 
                                       not visualization.get("labels") and not visualization.get("values"))
                
                if viz_chart_type == "table" or has_table_structure:
                    logger.error(f"❌ FINAL GRAPH GUARD: Chart requested but visualization is table - BLOCKING")
                    visualization = None
                    answer = "No structured numerical data available to generate a chart."
            
            # ============================================================
            # FINAL CHECK: Fix answer if we have table but answer says "not available"
            # ============================================================
            question_lower_final = question.lower()
            is_table_request_final = ("table" in question_lower_final or "tabular" in question_lower_final) and not is_chart_request
            
            if visualization and isinstance(visualization, dict):
                viz_type = visualization.get("chart_type") or visualization.get("type")
                has_table = viz_type == "table" or (visualization.get("headers") and visualization.get("rows"))
                
                # CRITICAL: Only set table message if NOT a chart request
                if has_table and not is_chart_request and (not answer or "not available" in answer.lower()):
                    answer = "The requested table is shown below."
                    logger.info("✅ FINALIZE FINAL CHECK: Fixed answer - replaced 'Not available' with table message")
                elif has_table and is_chart_request:
                    # Chart requested but we have table - should have been blocked above, but double-check
                    logger.error("❌ FINALIZE FINAL CHECK: Chart requested but table detected - should have been blocked")
                    visualization = None
                    answer = "No structured numerical data available to generate a chart."
            
            final_response = {
                "answer": answer,
                "visualization": visualization
            }
            
            # CRITICAL: Log visualization status
            if visualization:
                logger.info(f"✅ Returning visualization: type={visualization.get('chart_type') if isinstance(visualization, dict) else type(visualization)}")
                if isinstance(visualization, dict):
                    logger.info(f"Visualization keys: {list(visualization.keys())}")
                    if visualization.get("headers"):
                        logger.info(f"Visualization has {len(visualization.get('headers'))} headers")
                    if visualization.get("rows"):
                        logger.info(f"Visualization has {len(visualization.get('rows'))} rows")
            else:
                logger.warning("⚠️ No visualization in final response!")
            
            logger.info(f"Final response prepared. Answer: {answer[:100] if answer else 'EMPTY'}...")
            logger.info(f"Final response answer length: {len(answer)} characters")
            
            return {**state, "final_response": final_response}
        except Exception as e:
            logger.error(f"Error in finalize_response_node: {e}")
            return {
                **state,
                "final_response": {
                    "answer": "Error finalizing response.",
                    "visualization": None
                }
            }
    
    def _should_visualize(self, state: GraphState) -> str:
        """Conditional function to determine if visualization path should be taken."""
        needs_viz = state.get("needs_visualization", False)
        return "yes" if needs_viz else "no"
    
    def invoke(self, question: str) -> Dict:
        """
        Invoke the RAG graph with a question.
        
        Args:
            question: User question
            
        Returns:
            Final response dictionary with answer and optional visualization
        """
        try:
            question = str(question).strip()
            logger.info(f"Invoking RAG graph with question: {question[:100]}...")
            
            # Initialize state as a plain dict (not TypedDict instance)
            initial_state = {
                "question": question,
                "retrieved_context": [],
                "context_text": "",
                "answer": "",
                "needs_visualization": False,
                "extracted_data_for_chart": None,
                "visualization": None,
                "final_response": {}
            }
            
            # Try invoke first
            try:
                logger.info("Executing graph workflow...")
                # Try invoke - handle checkpointer config issues
                try:
                    result = self.graph.invoke(initial_state, config={"configurable": {}})
                except Exception as invoke_error:
                    error_str = str(invoke_error).lower()
                    if "configurable" in error_str or "checkpointer" in error_str:
                        logger.warning(f"Invoke with config failed (checkpointer issue): {invoke_error}, trying without config...")
                        result = self.graph.invoke(initial_state)
                    else:
                        raise
                logger.info(f"Graph execution completed. Result type: {type(result)}")
                logger.info(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                
                # Log full result structure for debugging
                if isinstance(result, dict):
                    for key, value in result.items():
                        if key == "answer":
                            logger.info(f"Result['answer'] = {str(value)[:200] if value else 'None'}...")
                        elif key == "final_response":
                            if isinstance(value, dict):
                                logger.info(f"Result['final_response'] keys: {list(value.keys())}")
                                if "answer" in value:
                                    logger.info(f"Result['final_response']['answer'] = {str(value['answer'])[:200] if value.get('answer') else 'None'}...")
                        else:
                            logger.debug(f"Result['{key}'] type: {type(value)}")
            except (KeyError, AttributeError, TypeError, Exception) as graph_error:
                error_str = str(graph_error)
                logger.warning(f"Graph invoke failed: {error_str}, using fallback")
                # Log full traceback for debugging
                import traceback
                logger.debug(f"Graph error traceback: {traceback.format_exc()}")
                # Use fallback - direct retrieval and answer
                retrieved_docs = self.retriever.retrieve(question)
                if not retrieved_docs:
                    logger.warning("Fallback: No documents retrieved")
                    return {"answer": "Not available in the uploaded document", "visualization": None}
                
                context_text = self.retriever.format_context(retrieved_docs)
                if not context_text:
                    logger.warning("Fallback: Context text is empty after formatting")
                    return {"answer": "Not available in the uploaded document", "visualization": None}
                
                # Check if user asked for tables
                question_lower = question.lower()
                is_table_request = "table" in question_lower or "tabular" in question_lower
                
                # If user asked for tables, extract and generate table
                visualization = None
                if is_table_request:
                    logger.info("Fallback: User asked for table - extracting from context")
                    try:
                        # Try to extract table from context
                        import re
                        table_lines = []
                        for line in context_text.split('\n'):
                            if '|' in line and line.count('|') >= 2:
                                if not re.match(r'^[\s\|:\-]+$', line.strip()):
                                    table_lines.append(line)
                        
                        if table_lines and len(table_lines) >= 2:
                            logger.info(f"Fallback: Found {len(table_lines)} table lines - extracting")
                            headers = []
                            rows = []
                            
                            # Parse headers
                            header_parts = table_lines[0].split('|')
                            for part in header_parts:
                                cleaned = part.strip().replace('**', '').replace('*', '').strip()
                                if cleaned:
                                    headers.append(cleaned)
                            
                            # Parse rows
                            for row_line in table_lines[1:]:
                                row_parts = row_line.split('|')
                                row_cells = []
                                for part in row_parts:
                                    cleaned = part.strip().replace('**', '').replace('*', '').strip()
                                    if cleaned or len(row_cells) < len(headers):
                                        row_cells.append(cleaned if cleaned else "-")
                                
                                if all(re.match(r'^[\s\-:]+$', cell) for cell in row_cells if cell):
                                    continue
                                
                                while len(row_cells) < len(headers):
                                    row_cells.append("-")
                                row_cells = row_cells[:len(headers)]
                                
                                if any(cell.strip() and cell.strip() != "-" for cell in row_cells):
                                    rows.append(row_cells)
                            
                            if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                                logger.info(f"Fallback: ✅ Extracted table: {len(headers)} columns, {len(rows)} rows")
                                table_data = {
                                    "chart_type": "table",
                                    "headers": headers,
                                    "rows": rows,
                                    "title": "Financial Data"
                                }
                                table_viz = self.visualization_generator.generate_chart(table_data)
                                if table_viz and "error" not in table_viz:
                                    visualization = table_viz
                                    logger.info("Fallback: ✅ Generated table visualization")
                                else:
                                    visualization = {
                                        "chart_type": "table",
                                        "headers": headers,
                                        "rows": rows,
                                        "title": "Financial Data"
                                    }
                        else:
                            # Try LLM extraction
                            logger.info("Fallback: No markdown tables found, trying LLM extraction")
                            from app.rag.prompts import DATA_EXTRACTION_PROMPT
                            extract_prompt = DATA_EXTRACTION_PROMPT.format(
                                question=question + " Extract as table with headers and rows.",
                                context=context_text[:4000]
                            )
                            extract_response = self.llm.invoke(extract_prompt)
                            extract_text = extract_response.content if hasattr(extract_response, 'content') else str(extract_response)
                            extracted_data = self.visualization_generator.parse_extracted_data(extract_text)
                            
                            if extracted_data and isinstance(extracted_data, dict) and extracted_data.get("chart_type") == "table":
                                headers = extracted_data.get("headers", [])
                                rows = extracted_data.get("rows", [])
                                if headers and rows and len(headers) >= 2 and len(rows) >= 1:
                                    logger.info(f"Fallback: ✅ LLM extracted table: {len(headers)} columns, {len(rows)} rows")
                                    table_data = {
                                        "chart_type": "table",
                                        "headers": headers,
                                        "rows": rows,
                                        "title": "Financial Data"
                                    }
                                    table_viz = self.visualization_generator.generate_chart(table_data)
                                    if table_viz and "error" not in table_viz:
                                        visualization = table_viz
                                    else:
                                        visualization = table_data
                    except Exception as table_error:
                        logger.error(f"Fallback: Table extraction failed: {table_error}", exc_info=True)
                
                # Check if user asked for chart vs table
                question_lower = question.lower()
                is_chart_request = any(kw in question_lower for kw in [
                    'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization',
                    'visualise', 'show chart', 'display chart', 'give me chart',
                    'generate chart', 'create chart', 'plot', 'plotting', 'show charts'
                ])
                
                # CRITICAL: Check for table BEFORE generating answer
                is_table_request = "table" in question_lower or "tabular" in question_lower
                answer = None
                
                if visualization:
                    viz_type = visualization.get("chart_type") or visualization.get("type")
                    has_table_structure = visualization.get("headers") and visualization.get("rows") and not visualization.get("labels")
                    
                    if is_chart_request and (viz_type == "table" or has_table_structure):
                        # Chart requested but we have table - return error
                        logger.error("❌ FALLBACK BLOCK: Chart requested but visualization is table - blocking")
                        visualization = None
                        answer = "No structured numerical data available to generate a chart."
                    elif (is_table_request or viz_type == "table" or has_table_structure) and not is_chart_request:
                        # Table requested and we have table - set answer immediately (SKIP LLM)
                        # CRITICAL: Only set if NOT a chart request
                        if not is_chart_request:
                            answer = "The requested table is shown below."
                            logger.info("✅ Fallback: Table found - setting answer to table message (skipping LLM)")
                        else:
                            # Chart requested but we have table - return error
                            logger.error("❌ Fallback: Chart requested but table detected - blocking")
                            visualization = None
                            answer = "No structured numerical data available to generate a chart."
                    elif not is_chart_request:
                        # We have a chart visualization - set answer
                        answer = "Here is the visualization based on the document data."
                
                # Only call LLM if we don't have a valid visualization or answer
                if not answer:
                    from app.rag.prompts import RAG_PROMPT
                    prompt = RAG_PROMPT.format(context=context_text, question=question)
                    logger.info("Fallback: Invoking LLM for answer...")
                    response = self.llm.invoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    answer = answer.strip()
                    
                    # CRITICAL: If we have visualization but answer says "Not available", fix it
                    if visualization and "not available" in answer.lower():
                        viz_type = visualization.get("chart_type") or visualization.get("type")
                        has_table = viz_type == "table" or (visualization.get("headers") and visualization.get("rows") and not visualization.get("labels"))
                        
                        # CRITICAL: Only set table message if NOT a chart request
                        if has_table and not is_chart_request and (is_table_request or viz_type == "table"):
                            answer = "The requested table is shown below."
                            logger.info("✅ Fallback: Fixed answer - replaced 'Not available' with table message")
                        elif has_table and is_chart_request:
                            # Chart requested but we have table - return error
                            logger.error("❌ Fallback: Chart requested but table detected - blocking")
                            visualization = None
                            answer = "No structured numerical data available to generate a chart."
                        elif not has_table:
                            answer = "Here is the visualization based on the document data."
                
                logger.info(f"Fallback: Generated answer length: {len(answer)} characters")
                logger.info(f"Fallback: Visualization present: {visualization is not None}")
                return {"answer": answer, "visualization": visualization}
            
            # Extract final response from result
            if isinstance(result, dict):
                logger.info("Extracting response from graph result...")
                # Try different ways to get the answer
                if "final_response" in result and isinstance(result["final_response"], dict):
                    final = result["final_response"]
                    answer = final.get("answer", "")
                    visualization = final.get("visualization")
                    logger.info(f"Found final_response. Answer length: {len(answer)} characters")
                    logger.info(f"Visualization in final_response: {visualization is not None}")
                    if visualization:
                        logger.info(f"Visualization type: {type(visualization)}")
                        if isinstance(visualization, dict):
                            logger.info(f"Visualization keys: {list(visualization.keys())}")
                            logger.info(f"Has headers: {bool(visualization.get('headers'))}")
                            logger.info(f"Has rows: {bool(visualization.get('rows'))}")
                    if not answer or answer.strip() == "":
                        logger.warning("final_response has empty answer, checking other fields...")
                        # Try to get answer from result directly
                        if "answer" in result:
                            answer = result.get("answer", "")
                            logger.info(f"Got answer from result. Length: {len(answer)} characters")
                        if not answer or answer.strip() == "":
                            logger.error("Answer is still empty after checking result!")
                            answer = "I processed your question but couldn't generate a response. Please try rephrasing or check if the document contains relevant information."
                    # CRITICAL: If we have a valid table or chart, NEVER show error
                    if visualization and isinstance(visualization, dict):
                        has_chart = visualization.get("labels") and visualization.get("values")
                        has_table = visualization.get("headers") and visualization.get("rows")
                        
                        # CRITICAL: If we have valid table/chart data, remove any error
                        if has_table or has_chart:
                            # Remove error if present
                            if "error" in visualization:
                                logger.warning("⚠️ Removing error from visualization - valid table/chart data exists")
                                visualization.pop("error", None)
                            
                            # CRITICAL: Check if chart was requested
                            question_lower_check = question.lower()
                            is_chart_request_check = any(kw in question_lower_check for kw in [
                                'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
                                'visualise', 'show chart', 'display chart', 'give me chart', 'give me charts',
                                'generate chart', 'create chart', 'plot', 'plotting', 'show charts'
                            ])
                            
                            if has_table:
                                # We have a table - use simple message ONLY if NOT a chart request
                                if not is_chart_request_check and ("not available" in answer.lower() or answer.strip() == "" or "error" in answer.lower()):
                                    answer = "The requested table is shown below."
                                elif is_chart_request_check:
                                    # Chart requested but we have table - return error
                                    logger.error("❌ Chart requested but table detected in invoke - blocking")
                                    visualization = None
                                    answer = "No structured numerical data available to generate a chart."
                            elif has_chart:
                                # We have a chart - use chart message
                                if "not available" in answer.lower() or answer.strip() == "" or "error" in answer.lower():
                                    answer = "Here is the visualization based on the document data."
                        else:
                            # No valid data - check for error
                            if "error" in visualization:
                                answer = visualization.get("error", "No structured numerical data available to generate a chart.")
                                visualization = None
                    
                    return {
                        "answer": answer.strip() if answer else "I couldn't generate an answer. Please try rephrasing your question.",
                        "visualization": visualization
                    }
                
                if "answer" in result:
                    answer = result["answer"]
                    visualization = result.get("visualization")
                    logger.info(f"Found answer in result. Length: {len(answer)} characters")
                    
                    # CRITICAL: If we have a valid table or chart, NEVER show error
                    if visualization and isinstance(visualization, dict):
                        has_chart = visualization.get("labels") and visualization.get("values")
                        has_table = visualization.get("headers") and visualization.get("rows")
                        
                        # CRITICAL: If we have valid table/chart data, remove any error
                        if has_table or has_chart:
                            # Remove error if present
                            if "error" in visualization:
                                logger.warning("⚠️ Removing error from visualization - valid table/chart data exists")
                                visualization.pop("error", None)
                            
                            # CRITICAL: Check if chart was requested
                            question_lower_check = question.lower()
                            is_chart_request_check = any(kw in question_lower_check for kw in [
                                'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
                                'visualise', 'show chart', 'display chart', 'give me chart', 'give me charts',
                                'generate chart', 'create chart', 'plot', 'plotting', 'show charts'
                            ])
                            
                            if has_table:
                                # We have a table - use simple message ONLY if NOT a chart request
                                if not is_chart_request_check and ("not available" in answer.lower() or answer.strip() == "" or "error" in answer.lower()):
                                    answer = "The requested table is shown below."
                                elif is_chart_request_check:
                                    # Chart requested but we have table - return error
                                    logger.error("❌ Chart requested but table detected in invoke - blocking")
                                    visualization = None
                                    answer = "No structured numerical data available to generate a chart."
                            elif has_chart:
                                # We have a chart - use chart message
                                if "not available" in answer.lower() or answer.strip() == "" or "error" in answer.lower():
                                    answer = "Here is the visualization based on the document data."
                        else:
                            # No valid data - check for error
                            if "error" in visualization:
                                answer = visualization.get("error", "No structured numerical data available to generate a chart.")
                                visualization = None
                    
                    if answer and answer.strip():
                        return {
                            "answer": answer.strip(),
                            "visualization": visualization
                        }
                    else:
                        logger.warning("Answer in result is empty, using fallback")
                        answer = "I processed your question but couldn't generate a response. Please try rephrasing or check if the document contains relevant information."
                        return {
                            "answer": answer,
                            "visualization": visualization
                        }
                
                # Check nested structure (LangGraph sometimes returns node outputs)
                for key, value in result.items():
                    if isinstance(value, dict):
                        if "final_response" in value:
                            final = value["final_response"]
                            answer = final.get("answer", "")
                            visualization = final.get("visualization")
                            logger.info(f"Found final_response in nested key '{key}'. Answer length: {len(answer)} characters")
                            
                            # CRITICAL: Check for visualization error and update answer
                            if visualization and isinstance(visualization, dict) and "error" in visualization:
                                answer = visualization.get("error", "No structured numerical data available to generate a chart.")
                                visualization = None
                            
                            # CRITICAL: If we have a valid chart or table, don't show "Not available" message
                            if visualization and isinstance(visualization, dict):
                                has_chart = visualization.get("labels") and visualization.get("values")
                                has_table = visualization.get("headers") and visualization.get("rows")
                                
                                # CRITICAL: Check if chart was requested
                                question_lower_check = question.lower()
                                is_chart_request_check = any(kw in question_lower_check for kw in [
                                    'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
                                    'visualise', 'show chart', 'display chart', 'give me chart', 'give me charts',
                                    'generate chart', 'create chart', 'plot', 'plotting', 'show charts'
                                ])
                                
                                if has_table:
                                    # We have a table - use simple message ONLY if NOT a chart request
                                    if not is_chart_request_check and ("not available" in answer.lower() or answer.strip() == ""):
                                        answer = "The requested table is shown below."
                                    elif is_chart_request_check:
                                        # Chart requested but we have table - return error
                                        logger.error("❌ Chart requested but table detected in nested response - blocking")
                                        visualization = None
                                        answer = "No structured numerical data available to generate a chart."
                                elif has_chart:
                                    # We have a chart - use chart message
                                    if "not available" in answer.lower() or answer.strip() == "":
                                        answer = "Here is the visualization based on the document data."
                            
                            if not answer or answer.strip() == "":
                                answer = "I processed your question but couldn't generate a response. Please try rephrasing or check if the document contains relevant information."
                            return {
                                "answer": answer.strip() if answer else "I couldn't generate an answer. Please try rephrasing your question.",
                                "visualization": visualization
                            }
                        if "answer" in value:
                            answer = value["answer"]
                            visualization = value.get("visualization")
                            logger.info(f"Found answer in nested key '{key}'. Length: {len(answer)} characters")
                            
                            # CRITICAL: Check for visualization error and update answer
                            if visualization and isinstance(visualization, dict) and "error" in visualization:
                                answer = visualization.get("error", "No structured numerical data available to generate a chart.")
                                visualization = None
                            
                            # CRITICAL: If we have a valid chart or table, don't show "Not available" message
                            if visualization and isinstance(visualization, dict):
                                has_chart = visualization.get("labels") and visualization.get("values")
                                has_table = visualization.get("headers") and visualization.get("rows")
                                
                                # CRITICAL: Check if chart was requested
                                question_lower_check = question.lower()
                                is_chart_request_check = any(kw in question_lower_check for kw in [
                                    'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
                                    'visualise', 'show chart', 'display chart', 'give me chart', 'give me charts',
                                    'generate chart', 'create chart', 'plot', 'plotting', 'show charts'
                                ])
                                
                                if has_table:
                                    # We have a table - use simple message ONLY if NOT a chart request
                                    if not is_chart_request_check and ("not available" in answer.lower() or answer.strip() == ""):
                                        answer = "The requested table is shown below."
                                    elif is_chart_request_check:
                                        # Chart requested but we have table - return error
                                        logger.error("❌ Chart requested but table detected in nested response - blocking")
                                        visualization = None
                                        answer = "No structured numerical data available to generate a chart."
                                elif has_chart:
                                    # We have a chart - use chart message
                                    if "not available" in answer.lower() or answer.strip() == "":
                                        answer = "Here is the visualization based on the document data."
                            
                            if not answer or answer.strip() == "":
                                answer = "I processed your question but couldn't generate a response. Please try rephrasing or check if the document contains relevant information."
                            return {
                                "answer": answer.strip() if answer else "I couldn't generate an answer. Please try rephrasing your question.",
                                "visualization": visualization
                            }
            
            # If we get here, use fallback
            logger.warning("Could not extract response from graph result, using fallback")
            logger.warning(f"Result structure: {result}")
            retrieved_docs = self.retriever.retrieve(question)
            if not retrieved_docs:
                return {"answer": "Not available in the uploaded document", "visualization": None}
            
            context_text = self.retriever.format_context(retrieved_docs)
            if not context_text:
                return {"answer": "Not available in the uploaded document", "visualization": None}
            
            from app.rag.prompts import RAG_PROMPT
            prompt = RAG_PROMPT.format(context=context_text, question=question)
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            return {"answer": answer.strip(), "visualization": None}
            
        except Exception as e:
            logger.error(f"Error invoking graph: {e}", exc_info=True)
            # Final fallback
            try:
                retrieved_docs = self.retriever.retrieve(question)
                if not retrieved_docs:
                    return {"answer": "Not available in the uploaded document", "visualization": None}
                
                context_text = self.retriever.format_context(retrieved_docs)
                from app.rag.prompts import RAG_PROMPT
                prompt = RAG_PROMPT.format(context=context_text, question=question)
                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
                return {"answer": answer.strip(), "visualization": None}
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return {"answer": f"Error: {str(e)}", "visualization": None}
