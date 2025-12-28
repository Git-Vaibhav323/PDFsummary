"""
LangGraph implementation for RAG flow control.
Manages the complete RAG pipeline with conditional visualization.
"""
from typing import TypedDict, List, Dict, Optional
import logging
import time
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from app.config.settings import settings
from app.rag.retriever import ContextRetriever
from app.rag.prompts import (
    RAG_PROMPT,
    VISUALIZATION_DETECTION_PROMPT,
    DATA_EXTRACTION_PROMPT
)
from app.rag.visualization import VisualizationGenerator

logger = logging.getLogger(__name__)


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
        if settings and hasattr(settings, 'groq_api_key') and settings.groq_api_key:
            api_key = settings.groq_api_key
        else:
            import os
            api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set it in your .env file or environment variables.")
        
        model_name = settings.groq_model if settings and hasattr(settings, 'groq_model') else "llama-3.1-8b-instant"
        
        self.llm = ChatGroq(
            model=model_name,
            groq_api_key=api_key,
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
        
        # Compile the graph
        try:
            compiled_graph = workflow.compile()
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
                retrieved_docs = self.retriever.retrieve(question)
                context_text = self.retriever.format_context(retrieved_docs)
                
                logger.info(f"Retrieved {len(retrieved_docs)} context chunks")
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
        try:
            question = state.get("question", "").strip()
            context_text = state.get("context_text", "").strip()
            
            if not question:
                return {**state, "answer": "Please provide a question."}
            
            if not context_text:
                logger.warning("No context available for answer generation")
                answer = "Not available in the uploaded document"
            else:
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
                try:
                    response = self.llm.invoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    # Clean up the answer
                    answer = answer.strip()
                    if not answer:
                        answer = "Not available in the uploaded document"
                except Exception as e:
                    error_str = str(e)
                    logger.error(f"LLM error (first attempt): {e}")
                    
                    # Check if it's a model decommissioned error
                    if "decommissioned" in error_str.lower() or "model_decommissioned" in error_str:
                        logger.warning("Model decommissioned, trying alternative model: llama-3.1-8b-instant")
                        # Try with an alternative model
                        try:
                            # Get API key from settings
                            api_key = None
                            if settings and hasattr(settings, 'groq_api_key') and settings.groq_api_key:
                                api_key = settings.groq_api_key
                            else:
                                import os
                                api_key = os.getenv('GROQ_API_KEY')
                            
                            if api_key:
                                from langchain_groq import ChatGroq
                                fallback_llm = ChatGroq(
                                    model="llama-3.1-8b-instant",
                                    groq_api_key=api_key,
                                    temperature=0.1
                                )
                                response = fallback_llm.invoke(prompt)
                                answer = response.content if hasattr(response, 'content') else str(response)
                                answer = answer.strip()
                                if not answer:
                                    answer = "Not available in the uploaded document"
                                # Update self.llm to use the working model
                                self.llm = fallback_llm
                                logger.info("Successfully switched to llama-3.1-8b-instant model")
                            else:
                                answer = "Error: Groq API key not found. Cannot use fallback model."
                        except Exception as fallback_error:
                            logger.error(f"Fallback model also failed: {fallback_error}")
                            answer = "Error: The configured Groq model is not available. Please update GROQ_MODEL in your .env file. Try: llama-3.1-8b-instant or mixtral-8x7b-32768"
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
                            answer = "Error generating answer. Please try again."
            
            return {**state, "answer": answer}
        except Exception as e:
            logger.error(f"Error in generate_answer_node: {e}", exc_info=True)
            return {**state, "answer": "Error generating answer. Please try again."}
    
    def _check_visualization_node(self, state: GraphState) -> GraphState:
        """Node 3: Check if visualization is needed."""
        try:
            question = state.get("question", "")
            context_text = state.get("context_text", "")
            
            if not context_text:
                return {**state, "needs_visualization": False}
            
            # Use LLM to detect if visualization is needed
            prompt = VISUALIZATION_DETECTION_PROMPT.format(
                question=question,
                context=context_text[:2000]  # Limit context for detection
            )
            
            try:
                response = self.llm.invoke(prompt)
                decision = response.content if hasattr(response, 'content') else str(response)
                decision = decision.strip().upper()
                
                needs_viz = "YES" in decision
                logger.info(f"Visualization needed: {needs_viz}")
                
                return {**state, "needs_visualization": needs_viz}
            except Exception as e:
                logger.error(f"Error checking visualization: {e}")
                return {**state, "needs_visualization": False}
        except Exception as e:
            logger.error(f"Error in check_visualization_node: {e}")
            return {**state, "needs_visualization": False}
    
    def _extract_data_node(self, state: GraphState) -> GraphState:
        """Node 4: Extract numerical data for visualization."""
        try:
            question = state.get("question", "")
            context_text = state.get("context_text", "")
            
            prompt = DATA_EXTRACTION_PROMPT.format(
                question=question,
                context=context_text
            )
            
            try:
                response = self.llm.invoke(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # Parse extracted data
                extracted_data = self.visualization_generator.parse_extracted_data(response_text)
                
                return {**state, "extracted_data_for_chart": extracted_data}
            except Exception as e:
                logger.error(f"Error extracting data: {e}")
                return {**state, "extracted_data_for_chart": {"error": "Extraction failed"}}
        except Exception as e:
            logger.error(f"Error in extract_data_node: {e}")
            return {**state, "extracted_data_for_chart": {"error": "Extraction failed"}}
    
    def _generate_chart_node(self, state: GraphState) -> GraphState:
        """Node 5: Generate visualization chart."""
        try:
            extracted_data = state.get("extracted_data_for_chart", {})
            
            if not extracted_data or "error" in extracted_data:
                return {**state, "visualization": None}
            
            # Generate chart
            chart_result = self.visualization_generator.generate_chart(extracted_data)
            
            return {**state, "visualization": chart_result}
        except Exception as e:
            logger.error(f"Error in generate_chart_node: {e}")
            return {**state, "visualization": None}
    
    def _finalize_response_node(self, state: GraphState) -> GraphState:
        """Node 6: Finalize response with answer and optional visualization."""
        try:
            answer = state.get("answer", "")
            visualization = state.get("visualization")
            
            final_response = {
                "answer": answer,
                "visualization": visualization
            }
            
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
            # Initialize state as a plain dict (not TypedDict instance)
            initial_state = {
                "question": str(question).strip(),
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
                result = self.graph.invoke(initial_state)
            except (KeyError, AttributeError, TypeError) as graph_error:
                logger.warning(f"Graph invoke failed: {graph_error}, using fallback")
                # Use fallback - direct retrieval and answer
                retrieved_docs = self.retriever.retrieve(question)
                if not retrieved_docs:
                    return {"answer": "Not available in the uploaded document", "visualization": None}
                
                context_text = self.retriever.format_context(retrieved_docs)
                from app.rag.prompts import RAG_PROMPT
                prompt = RAG_PROMPT.format(context=context_text, question=question)
                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
                return {"answer": answer.strip(), "visualization": None}
            
            # Extract final response from result
            if isinstance(result, dict):
                # Try different ways to get the answer
                if "final_response" in result and isinstance(result["final_response"], dict):
                    return result["final_response"]
                if "answer" in result:
                    return {
                        "answer": result["answer"],
                        "visualization": result.get("visualization")
                    }
                # Check nested structure (LangGraph sometimes returns node outputs)
                for key, value in result.items():
                    if isinstance(value, dict):
                        if "final_response" in value:
                            return value["final_response"]
                        if "answer" in value:
                            return {
                                "answer": value["answer"],
                                "visualization": value.get("visualization")
                            }
            
            # If we get here, use fallback
            logger.warning("Could not extract response from graph result, using fallback")
            retrieved_docs = self.retriever.retrieve(question)
            if not retrieved_docs:
                return {"answer": "Not available in the uploaded document", "visualization": None}
            
            context_text = self.retriever.format_context(retrieved_docs)
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

