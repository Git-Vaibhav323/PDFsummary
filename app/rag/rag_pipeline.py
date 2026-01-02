"""
RAG retrieval pipeline with memory-based question rewriting.

Pipeline steps:
1. Load conversational memory
2. Rewrite question using memory to resolve references
3. Perform vector similarity search
4. Retrieve top-K chunks
5. Generate answer strictly from retrieved context
"""
import logging
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from app.config.settings import settings
from app.rag.memory import get_global_memory, get_memory_context
from app.rag.prompts import QUESTION_REWRITE_PROMPT, RAG_ANSWER_PROMPT

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
    
    def rewrite_question(self, question: str, use_memory: bool = True) -> str:
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
        
        memory_context = get_memory_context()
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
    
    def retrieve(self, query: str) -> List[Dict]:
        """
        Retrieve relevant documents for query.
        
        Args:
            query: User query
            
        Returns:
            List of relevant document chunks
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retriever")
            return []
        
        logger.info(f"Retrieving documents for: {query[:100]}")
        
        try:
            # Perform similarity search
            results = self.vector_store.similarity_search(query, k=self.top_k)
            
            if not results:
                logger.warning(f"No documents found for query: {query[:100]}")
                return []
            
            logger.info(f"Retrieved {len(results)} relevant chunks")
            return results
        
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def format_context(self, documents: List[Dict]) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            documents: List of retrieved document chunks
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            page_num = metadata.get("page_number", "?")
            
            # Format: [Source: page X] content...
            context_parts.append(f"[Source: page {page_num}]\n{text}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def generate_answer(self, 
                       question: str, 
                       context: str,
                       use_memory: bool = True) -> str:
        """
        Generate answer strictly from retrieved context.
        
        Args:
            question: Original user question
            context: Retrieved context
            use_memory: Whether to use conversation memory
            
        Returns:
            Generated answer
        """
        if not context or context.strip() == "":
            logger.warning("No context available for answer generation")
            return "Not available in the uploaded document."
        
        # Rewrite question if needed
        rewritten_question = self.question_rewriter.rewrite_question(question, use_memory)
        
        # Create prompt for answer generation
        prompt = RAG_ANSWER_PROMPT.format(
            context=context,
            question=rewritten_question
        )
        
        logger.debug("Generating answer from context")
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content.strip()
            
            if not answer or answer.lower() == "not available":
                return "Not available in the uploaded document."
            
            return answer
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Error processing your question. Please try again."
    
    def answer_question(self, 
                       question: str,
                       use_memory: bool = True) -> Dict:
        """
        Complete RAG pipeline: retrieve + answer.
        
        Args:
            question: User question
            use_memory: Whether to use conversation memory
            
        Returns:
            Dictionary with answer and metadata
        """
        logger.info(f"Processing question: {question[:100]}")
        
        # Step 1: Rewrite question with memory context
        rewritten_question = self.question_rewriter.rewrite_question(question, use_memory)
        
        # Step 2: Retrieve relevant documents
        documents = self.retrieve(rewritten_question)
        
        # Step 3: Format context
        context = self.format_context(documents)
        
        # Step 4: Generate answer
        answer = self.generate_answer(question, context, use_memory=False)  # Already rewritten
        
        # Step 5: Add to memory
        from app.rag.memory import add_to_memory
        add_to_memory("user", question)
        add_to_memory("assistant", answer)
        
        return {
            "question": question,
            "rewritten_question": rewritten_question,
            "answer": answer,
            "context": context,
            "retrieved_documents": documents,
            "document_count": len(documents)
        }
