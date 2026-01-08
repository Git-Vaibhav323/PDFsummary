"""
RAG retrieval pipeline with memory-based question rewriting and comparison-first multi-document support.

Pipeline steps:
1. Load conversational memory
2. Detect comparison intent
3. Rewrite question using memory to resolve references
4. Perform vector similarity search (comparison-aware retrieval)
5. Retrieve top-K chunks with balanced multi-document representation
6. Format context for comparison reasoning
7. Generate answer strictly from retrieved context

Performance optimized with timing logs and batched operations.
"""
import logging
import time
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from app.config.settings import settings
from app.rag.memory import get_global_memory, get_memory_context
from typing import Optional, List
from app.rag.prompts import QUESTION_REWRITE_PROMPT, RAG_ANSWER_PROMPT
from app.rag.comparison_detector import detect_comparison_intent, should_retrieve_from_all_documents, extract_comparison_theme

logger = logging.getLogger(__name__)


class QuestionRewriter:
    """Rewrites questions using conversation memory to resolve references."""
    
    def __init__(self):
        """Initialize question rewriter with gpt-4.1-mini."""
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0,  # Deterministic
            api_key=settings.openai_api_key,
            max_retries=2
        )
    
    def rewrite_question(self, question: str, use_memory: bool = True, session_id: Optional[str] = None) -> str:
        """
        Rewrite question using memory context to resolve references.
        
        Args:
            question: Original user question
            use_memory: Whether to use conversation memory
            
        Returns:
            Rewritten question (standalone if needed)
        """
        # If no memory needed or no history, return original
        if not use_memory:
            return question
        
        memory_context = get_memory_context(session_id, max_turns=10)
        if not memory_context:
            logger.debug("No memory context available, using original question")
            return question
        
        logger.debug(f"Rewriting question with memory context")
        
        try:
            # Create prompt for question rewriting
            prompt = QUESTION_REWRITE_PROMPT.format(
                memory_context=memory_context,
                current_question=question
            )
            
            response = self.llm.invoke(prompt)
            rewritten = response.content.strip()
            
            logger.debug(f"Original: {question[:100]}")
            logger.debug(f"Rewritten: {rewritten[:100]}")
            
            return rewritten
        except Exception as e:
            logger.warning(f"Question rewriting failed: {e}, using original")
            return question


class RAGRetriever:
    """Complete RAG retrieval pipeline."""
    
    def __init__(self, vector_store, top_k: int = 5):
        """
        Initialize RAG retriever.
        
        Args:
            vector_store: VectorStore instance for similarity search
            top_k: Number of top results to retrieve
        """
        self.vector_store = vector_store
        self.top_k = top_k
        self.question_rewriter = QuestionRewriter()
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0,  # Deterministic
            api_key=settings.openai_api_key,
            max_retries=2
        )
        self.current_document_ids: Optional[List[str]] = None  # Document filter(s) for multi-doc support
    
    def set_document_filter(self, document_ids: Optional[List[str]]) -> None:
        """
        Set the document ID filter(s) for retrieval.
        
        Args:
            document_ids: List of document IDs to filter by (None to disable filtering)
        """
        self.current_document_ids = document_ids
        if document_ids:
            logger.info(f"🔐 Document filter set to: {document_ids}")
        else:
            logger.info(f"🔓 Document filter disabled")
    
    def retrieve(self, query: str, top_k: Optional[int] = None, is_comparison: bool = False) -> List[Dict]:
        """
        Retrieve relevant documents for query with performance tracking.
        Enhanced with comparison-aware multi-document retrieval.
        
        Args:
            query: User query
            top_k: Number of results to retrieve (overrides default for fast queries)
            is_comparison: Whether this is a comparison query (affects retrieval strategy)
            
        Returns:
            List of relevant document chunks, balanced across documents if comparison
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retriever")
            return []
        
        # Use provided top_k or fall back to instance default
        k = top_k if top_k is not None else self.top_k
        
        start_time = time.time()
        logger.info(f"🔍 Retrieving: {query[:80]}... (top_k={k}, comparison={is_comparison})")
        
        try:
            # Determine retrieval strategy
            retrieve_from_all = should_retrieve_from_all_documents(query, self.current_document_ids)
            
            if is_comparison or retrieve_from_all:
                # COMPARISON MODE: Retrieve balanced chunks from all relevant documents
                logger.info(f"🔍 Comparison-aware retrieval: ensuring balanced representation across documents")
                
                # Get all documents to search (either specified or all available)
                target_doc_ids = self.current_document_ids if self.current_document_ids else None
                
                if target_doc_ids and len(target_doc_ids) > 1:
                    # Multi-document comparison: retrieve balanced chunks per document
                    chunks_per_doc = max(2, k // len(target_doc_ids))  # At least 2 chunks per doc
                    all_results = []
                    
                    for doc_id in target_doc_ids:
                        filter_dict = {"document_id": doc_id}
                        doc_results = self.vector_store.similarity_search(
                            query, 
                            k=chunks_per_doc + 2,  # Get extra for filtering
                            filter_dict=filter_dict
                        )
                        # Take top chunks_per_doc from this document
                        all_results.extend(doc_results[:chunks_per_doc])
                        logger.info(f"   📄 Retrieved {len(doc_results[:chunks_per_doc])} chunks from document {doc_id[:8]}")
                    
                    # Sort all results by score and take top k
                    all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                    results = all_results[:k]
                    logger.info(f"   ✅ Comparison retrieval: {len(results)} chunks from {len(target_doc_ids)} documents")
                else:
                    # Comparison query but single/no document filter: retrieve more broadly
                    results = self.vector_store.similarity_search(query, k=k * 2)
                    # Group by document and ensure diversity
                    doc_groups = {}
                    for result in results:
                        doc_id = result.get("metadata", {}).get("document_id", "unknown")
                        if doc_id not in doc_groups:
                            doc_groups[doc_id] = []
                        doc_groups[doc_id].append(result)
                    
                    # Take balanced representation
                    balanced_results = []
                    max_per_doc = max(2, k // max(1, len(doc_groups)))
                    for doc_id, doc_results in doc_groups.items():
                        balanced_results.extend(doc_results[:max_per_doc])
                    
                    # Sort by score and limit
                    balanced_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                    results = balanced_results[:k]
                    logger.info(f"   ✅ Comparison retrieval: {len(results)} chunks from {len(doc_groups)} documents")
            else:
                # STANDARD MODE: Standard retrieval with optional filtering
                filter_dict = None
                if self.current_document_ids and len(self.current_document_ids) == 1:
                    # Single document: use filter for efficiency
                    filter_dict = {"document_id": self.current_document_ids[0]}
                    logger.info(f"   📄 Filtering by document: {self.current_document_ids[0]}")
                elif self.current_document_ids and len(self.current_document_ids) > 1:
                    # Multi-document: search all and filter results
                    logger.info(f"   📄 Multi-document search across: {self.current_document_ids}")
                
                # Perform similarity search
                results = self.vector_store.similarity_search(
                    query, 
                    k=k * 2 if self.current_document_ids and len(self.current_document_ids) > 1 else k, 
                    filter_dict=filter_dict
                )
                
                # Filter results for multi-document case
                if self.current_document_ids and len(self.current_document_ids) > 1 and results:
                    filtered_results = []
                    for result in results:
                        metadata = result.get("metadata", {})
                        doc_id = metadata.get("document_id")
                        if doc_id in self.current_document_ids:
                            filtered_results.append(result)
                    results = filtered_results[:k]  # Limit to top k
                    logger.info(f"   ✅ Filtered to {len(results)} results from {len(self.current_document_ids)} documents")
            
            elapsed = time.time() - start_time
            
            if not results:
                logger.warning(f"⚠️ No documents found (retrieval took {elapsed:.3f}s)")
                return []
            
            logger.info(f"✅ Retrieved {len(results)} chunks in {elapsed:.3f}s | Avg score: {sum(r.get('score', 0) for r in results) / len(results):.3f}")
            return results
        
        except Exception as e:
            logger.error(f"❌ Error retrieving documents: {e}")
            return []
    
    def format_context(self, documents: List[Dict], is_comparison: bool = False, comparison_theme: Optional[str] = None) -> str:
        """
        Format retrieved documents into context string with document attribution.
        Enhanced for comparison queries with structured grouping.
        
        Args:
            documents: List of retrieved document chunks
            is_comparison: Whether this is a comparison query
            comparison_theme: Theme/topic being compared (e.g., "financial", "risk")
            
        Returns:
            Formatted context string with document identifiers, structured for comparison if needed
        """
        if not documents:
            return ""
        
        # Group documents by document_id to identify unique documents
        doc_groups = {}
        doc_names = {}
        doc_periods = {}
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            doc_id = metadata.get("document_id", "unknown")
            doc_name = metadata.get("filename", f"Document {doc_id[:8]}")
            doc_period = metadata.get("document_period") or metadata.get("period") or None
            
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
                doc_names[doc_id] = doc_name
                doc_periods[doc_id] = doc_period
            doc_groups[doc_id].append(doc)
        
        # Create document index map (sorted for consistency)
        doc_ids_list = sorted(list(doc_groups.keys()))  # Sort for consistent ordering
        doc_index_map = {doc_id: idx + 1 for idx, doc_id in enumerate(doc_ids_list)}
        
        if is_comparison and len(doc_groups) > 1:
            # COMPARISON MODE: Structured format for comparison reasoning
            context_parts = []
            
            # Add comparison header
            theme_str = f" ({comparison_theme})" if comparison_theme else ""
            context_parts.append(f"[COMPARISON CONTEXT{theme_str} - Multiple Documents]")
            context_parts.append(f"Number of documents: {len(doc_groups)}")
            context_parts.append("")
            
            # Format each document with clear separation
            for doc_id in doc_ids_list:
                doc_index = doc_index_map[doc_id]
                doc_name = doc_names[doc_id]
                doc_period = doc_periods[doc_id]
                doc_chunks = doc_groups[doc_id]
                
                # Document header with period if available
                period_str = f" | Period: {doc_period}" if doc_period else ""
                context_parts.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                context_parts.append(f"[Document {doc_index}: {doc_name}{period_str}]")
                context_parts.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                
                # Add chunks from this document
                for doc in doc_chunks:
                    text = doc.get("text", "")
                    metadata = doc.get("metadata", {})
                    page_num = metadata.get("page_number", "?")
                    
                    # Format: [Source: Document X, page Y] content...
                    context_parts.append(f"[Source: Document {doc_index}, page {page_num}]\n{text}")
                    context_parts.append("")  # Empty line between chunks
            
            # Add comparison instruction footer
            context_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            context_parts.append("[COMPARISON INSTRUCTIONS]")
            context_parts.append("When answering comparison questions:")
            context_parts.append("1. Identify common themes/metrics across documents")
            context_parts.append("2. Extract comparable signals from each document")
            context_parts.append("3. Contrast similarities and differences")
            context_parts.append("4. Explain why differences matter")
            context_parts.append("5. Align time periods/scope before comparing")
            context_parts.append("6. End with a clear synthesized conclusion")
            
            return "\n".join(context_parts)
        else:
            # STANDARD MODE: Simple document grouping
            context_parts = []
            for doc_id in doc_ids_list:
                doc_index = doc_index_map[doc_id]
                doc_name = doc_names[doc_id]
                doc_period = doc_periods[doc_id]
                doc_chunks = doc_groups[doc_id]
                
                # Add document header
                period_str = f" (Period: {doc_period})" if doc_period else ""
                context_parts.append(f"[Document {doc_index}: {doc_name}{period_str}]")
                
                # Add chunks from this document
                for doc in doc_chunks:
                    text = doc.get("text", "")
                    metadata = doc.get("metadata", {})
                    page_num = metadata.get("page_number", "?")
                    
                    # Format: [Source: Document X, page Y] content...
                    context_parts.append(f"[Source: Document {doc_index}, page {page_num}]\n{text}")
            
            return "\n\n---\n\n".join(context_parts)
    
    def generate_answer(self, 
                       question: str, 
                       context: str,
                       use_memory: bool = True,
                       is_comparison: bool = False,
                       comparison_type: Optional[str] = None) -> str:
        """
        Generate answer strictly from retrieved context with timing.
        Enhanced with comparison-aware prompt selection.
        
        Args:
            question: Original user question
            context: Retrieved context
            use_memory: Whether to use conversation memory
            is_comparison: Whether this is a comparison query
            comparison_type: Type of comparison ("compare", "difference", etc.)
            
        Returns:
            Generated answer
        """
        if not context or context.strip() == "":
            logger.warning("No context available for answer generation")
            return "Not available in the uploaded document."
        
        start_time = time.time()
        
        # Rewrite question if needed
        rewritten_question = self.question_rewriter.rewrite_question(question, use_memory)
        
        # Create prompt for answer generation (comparison-aware)
        prompt = RAG_ANSWER_PROMPT.format(
            context=context,
            question=rewritten_question
        )
        
        if is_comparison:
            logger.debug(f"🤖 Generating comparison answer (type: {comparison_type})...")
        else:
            logger.debug("🤖 Generating answer from context...")
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content.strip()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Answer generated in {elapsed:.3f}s | {len(answer)} chars")
            
            if not answer or answer.lower() == "not available":
                return "Not available in the uploaded document."
            
            return answer
        
        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            return "Error processing your question. Please try again."
    
    def answer_question(self, 
                       question: str,
                       use_memory: bool = True,
                       fast_mode: bool = False,
                       session_id: Optional[str] = None,
                       document_ids: Optional[List[str]] = None) -> Dict:
        """
        Complete RAG pipeline: retrieve + answer with comprehensive timing.
        
        Args:
            question: User question
            use_memory: Whether to use conversation memory
            fast_mode: If True, use fewer documents for faster response (for finance agent)
            session_id: Optional session ID for memory scoping
            document_ids: Optional list of document IDs to filter by
            
        Returns:
            Dictionary with answer and metadata
        """
        pipeline_start = time.time()
        logger.info(f"📋 RAG Pipeline: {question[:80]}... {'(FAST MODE)' if fast_mode else ''}")
        
        # Set document filter if provided
        if document_ids is not None:
            self.set_document_filter(document_ids)
        
        # Step 0: Detect comparison intent (before rewriting to preserve original question)
        is_comparison, comparison_type, comparison_signals = detect_comparison_intent(question)
        comparison_theme = extract_comparison_theme(question) if is_comparison else None
        
        if is_comparison:
            logger.info(f"🔍 COMPARISON MODE detected: type={comparison_type}, theme={comparison_theme}, signals={comparison_signals}")
        
        # Step 1: Rewrite question with memory context (skip if fast mode)
        rewrite_start = time.time()
        if fast_mode or not use_memory:
            rewritten_question = question  # Skip rewriting for speed
            rewrite_time = 0
        else:
            rewritten_question = self.question_rewriter.rewrite_question(question, use_memory, session_id)
            rewrite_time = time.time() - rewrite_start
        
        # Step 2: Retrieve relevant documents (use fewer docs if fast mode, comparison-aware)
        retrieve_start = time.time()
        if fast_mode:
            from app.config.settings import settings
            documents = self.retrieve(rewritten_question, top_k=settings.top_k_finance_agent, is_comparison=is_comparison)
        else:
            documents = self.retrieve(rewritten_question, is_comparison=is_comparison)
        retrieve_time = time.time() - retrieve_start
        
        # Step 3: Format context (comparison-aware formatting)
        context = self.format_context(documents, is_comparison=is_comparison, comparison_theme=comparison_theme)
        
        # Step 4: Generate answer with multi-document awareness
        answer_start = time.time()
        # Check if multiple documents are involved
        doc_ids_in_context = set()
        for doc in documents:
            metadata = doc.get("metadata", {})
            doc_id = metadata.get("document_id")
            if doc_id:
                doc_ids_in_context.add(doc_id)
        
        # Use rewritten question (already has memory context)
        # The context formatting already includes document attribution
        # Pass comparison flag to answer generation for prompt selection
        answer = self.generate_answer(
            rewritten_question, 
            context, 
            use_memory=False,  # Already rewritten
            is_comparison=is_comparison,
            comparison_type=comparison_type
        )
        answer_time = time.time() - answer_start
        
        # Step 5: Add to memory (skip if fast mode to reduce overhead)
        if not fast_mode:
            from app.rag.memory import add_to_memory
            add_to_memory("user", question, session_id=session_id)
            add_to_memory("assistant", answer, session_id=session_id)
        
        total_time = time.time() - pipeline_start
        
        # Calculate average retrieval score
        retrieval_score = 0.0
        if documents:
            scores = [doc.get("score", 0.0) for doc in documents if isinstance(doc, dict)]
            if scores:
                retrieval_score = sum(scores) / len(scores)
        
        logger.info(f"📊 RAG Pipeline complete: {total_time:.3f}s total | Rewrite: {rewrite_time:.3f}s | Retrieve: {retrieve_time:.3f}s | Answer: {answer_time:.3f}s")
        return {
            "question": question,
            "rewritten_question": rewritten_question,
            "answer": answer,
            "context": context,
            "retrieved_documents": documents,
            "document_count": len(documents),
            "retrieval_score": retrieval_score,
            "is_comparison": is_comparison,
            "comparison_type": comparison_type,
            "documents_involved": len(doc_ids_in_context)
        }
