#!/usr/bin/env python3
"""
End-to-end debugging script to diagnose chart visualization pipeline.
Traces the entire flow from document ingestion to chart generation.
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_document_retrieval():
    """Test 1: Check if documents are in the vector store."""
    print("\n" + "="*80)
    print("TEST 1: DOCUMENT RETRIEVAL")
    print("="*80)
    
    try:
        from app.rag.vector_store import VectorStore
        
        vs = VectorStore()
        
        # Try to get all documents
        print("\n📦 Checking vector store contents...")
        collection = vs.vectorstore._collection
        if collection:
            collection_data = collection.get(include=["documents", "metadatas"])
            doc_ids = collection_data.get("ids", [])
            doc_texts = collection_data.get("documents", [])
            doc_metas = collection_data.get("metadatas", [])
            
            print(f"✓ Vector store has {len(doc_ids)} documents")
            
            if doc_ids:
                print(f"\n📄 Sample documents:")
                for i in range(min(3, len(doc_ids))):
                    text_preview = doc_texts[i][:100] if doc_texts[i] else "No text"
                    meta = doc_metas[i] if i < len(doc_metas) else {}
                    print(f"  [{i}] ID: {doc_ids[i]}")
                    print(f"      Text: {text_preview}...")
                    print(f"      Meta: {meta}")
            else:
                print("❌ NO DOCUMENTS FOUND IN VECTOR STORE")
                print("   The PDF may not have been uploaded or indexed.")
                return False
        else:
            print("❌ Could not access vector store collection")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking vector store: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False


def test_similarity_search():
    """Test 2: Check if similarity search works."""
    print("\n" + "="*80)
    print("TEST 2: SIMILARITY SEARCH")
    print("="*80)
    
    try:
        from app.rag.vector_store import VectorStore
        
        vs = VectorStore()
        
        # Try different queries to find relevant documents
        queries = [
            "cash flow",
            "financial statement",
            "revenue",
            "income",
            "balance sheet",
            "data",
            "chart",
            "table"
        ]
        
        print("\n🔍 Testing similarity search with multiple queries...")
        
        found_results = False
        for query in queries:
            print(f"\n  Query: '{query}'")
            results = vs.similarity_search(query, k=3)
            
            if results:
                print(f"  ✓ Found {len(results)} results")
                for i, result in enumerate(results[:1]):  # Just show first result
                    text_preview = result.get("text", "")[:80]
                    score = result.get("score", 0)
                    meta = result.get("metadata", {})
                    print(f"    Result 1: score={score:.4f}, meta={meta}")
                    print(f"    Text: {text_preview}...")
                found_results = True
            else:
                print(f"  ✗ No results found")
        
        if not found_results:
            print("\n❌ Similarity search returned no results for any query")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error in similarity search: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False


def test_rag_retriever():
    """Test 3: Check if RAG retriever works."""
    print("\n" + "="*80)
    print("TEST 3: RAG RETRIEVER")
    print("="*80)
    
    try:
        from app.rag.rag_system import RAGRetriever
        from app.rag.vector_store import VectorStore
        
        vs = VectorStore()
        retriever = RAGRetriever(vector_store=vs, top_k=5)
        
        test_question = "Show me the financial data"
        print(f"\n❓ Test question: '{test_question}'")
        
        # Test retrieval
        print("\n📖 Retrieving context...")
        rag_result = retriever.answer_question(test_question, use_memory=False)
        
        answer = rag_result.get("answer", "")
        context = rag_result.get("context", "")
        docs = rag_result.get("documents", [])
        
        print(f"✓ Answer length: {len(answer)} chars")
        print(f"✓ Context length: {len(context)} chars")
        print(f"✓ Retrieved documents: {len(docs)}")
        
        if context:
            print(f"\n📄 Context preview: {context[:200]}...")
        else:
            print("\n❌ No context retrieved - RAG retriever returned empty context")
            print("   This is likely why charts are null")
            return False
        
        if "not available" in answer.lower():
            print(f"⚠️  Answer: '{answer}'")
            print("   RAG system returned 'Not available' response")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error in RAG retriever: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False


def test_visualization_detection():
    """Test 4: Check if visualization is detected."""
    print("\n" + "="*80)
    print("TEST 4: VISUALIZATION DETECTION")
    print("="*80)
    
    try:
        from app.rag.visualization_pipeline import VisualizationPipeline
        
        viz_pipeline = VisualizationPipeline()
        
        test_cases = [
            ("Show me a bar chart of sales by region", "bar chart query"),
            ("Create a line graph of revenue over time", "line chart query"),
            ("Display financial metrics in a table", "table query"),
            ("What are the total revenues?", "general query"),
        ]
        
        print("\n🔍 Testing visualization detection...")
        
        for question, description in test_cases:
            print(f"\n  Test: {description}")
            print(f"  Question: '{question}'")
            
            should_visualize = viz_pipeline.detector.detect(question)
            print(f"  Detection: {should_visualize}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error in visualization detection: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False


def test_data_extraction():
    """Test 5: Check if data extraction works."""
    print("\n" + "="*80)
    print("TEST 5: DATA EXTRACTION")
    print("="*80)
    
    try:
        from app.rag.visualization_pipeline import DataExtractor
        
        extractor = DataExtractor()
        
        # Test with sample contexts
        test_contexts = [
            "The quarterly revenue was: Q1: $1.2M, Q2: $1.5M, Q3: $1.8M, Q4: $2.1M",
            "Sales by region: North: 100, South: 150, East: 120, West: 180",
            "No numeric data in this context at all",
        ]
        
        print("\n📊 Testing data extraction...")
        
        for i, context in enumerate(test_contexts):
            print(f"\n  Test {i+1}: {context[:60]}...")
            
            extracted = extractor.extract(
                context=context,
                question="Create a chart"
            )
            
            if extracted and isinstance(extracted, dict):
                print(f"  ✓ Extracted data: {json.dumps(extracted, indent=2)[:200]}...")
            else:
                print(f"  ✗ No structured data extracted: {extracted}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in data extraction: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False


def test_chart_generation():
    """Test 6: Check if chart generation works."""
    print("\n" + "="*80)
    print("TEST 6: CHART GENERATION")
    print("="*80)
    
    try:
        from app.rag.visualization_pipeline import ChartGenerator
        
        generator = ChartGenerator()
        
        # Test with sample structured data
        test_data = {
            "type": "bar",
            "title": "Q Revenue",
            "labels": ["Q1", "Q2", "Q3", "Q4"],
            "values": [1.2, 1.5, 1.8, 2.1],
            "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
        }
        
        print(f"\n📈 Test data: {test_data}")
        
        chart = generator.generate(data=test_data, question="Show revenue by quarter")
        
        if chart and isinstance(chart, dict):
            print(f"✓ Chart generated successfully")
            print(f"  Type: {chart.get('type')}")
            print(f"  Title: {chart.get('title')}")
            print(f"  Has data: {'data' in chart}")
            return True
        else:
            print(f"❌ Chart generation failed: {chart}")
            return False
        
    except Exception as e:
        logger.error(f"Error in chart generation: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False


def test_full_pipeline():
    """Test 7: Full end-to-end visualization pipeline."""
    print("\n" + "="*80)
    print("TEST 7: FULL PIPELINE (with sample context)")
    print("="*80)
    
    try:
        from app.rag.visualization_pipeline import VisualizationPipeline
        
        pipeline = VisualizationPipeline()
        
        sample_question = "Show cash flow data as a chart"
        sample_context = """
        Annual Cash Flow Summary:
        - Operating Activities: $5.2M
        - Investing Activities: -$1.3M
        - Financing Activities: $0.8M
        - Net Change in Cash: $4.7M
        
        Quarterly breakdown:
        Q1: 1.0M, Q2: 1.2M, Q3: 1.5M, Q4: 1.5M
        """
        
        print(f"\n❓ Question: {sample_question}")
        print(f"📄 Context: {sample_context[:100]}...")
        
        print("\n🔄 Processing through visualization pipeline...")
        result = pipeline.process(
            question=sample_question,
            context=sample_context
        )
        
        if result:
            print(f"✓ Pipeline result: {json.dumps(result, indent=2)[:300]}...")
            
            if result.get("chart"):
                print(f"✓ Chart generated: {result['chart'].get('type')}")
                return True
            else:
                print(f"❌ No chart in result: {result.keys()}")
                return False
        else:
            print(f"❌ Pipeline returned None")
            return False
        
    except Exception as e:
        logger.error(f"Error in full pipeline: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False


async def test_with_real_question():
    """Test 8: Test with actual RAG system using real question."""
    print("\n" + "="*80)
    print("TEST 8: REAL QUESTION WITH RAG SYSTEM")
    print("="*80)
    
    try:
        from app.rag.rag_system import get_rag_system
        
        rag_system = get_rag_system()
        
        test_question = "What is the cash flow data?"
        print(f"\n❓ Question: {test_question}")
        
        print("\n🔄 Processing through RAG system...")
        result = rag_system.answer_question(test_question, use_memory=False)
        
        if result:
            answer = result.get("answer", "")
            viz_result = result.get("visualization")
            
            print(f"✓ Answer: {answer[:100]}...")
            
            if viz_result:
                print(f"✓ Visualization result: {json.dumps(viz_result, indent=2)[:300]}...")
                
                if viz_result.get("chart"):
                    print(f"✓ Chart generated: {viz_result['chart'].get('type')}")
                    return True
                else:
                    print(f"⚠️  No chart in visualization result")
                    return False
            else:
                print(f"⚠️  No visualization result from RAG system")
                return False
        else:
            print(f"❌ RAG system returned None")
            return False
        
    except Exception as e:
        logger.error(f"Error in real question test: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("END-TO-END CHART VISUALIZATION DEBUGGING")
    print("="*80)
    
    results = {}
    
    # Run tests in order
    test_functions = [
        ("Vector Store Contents", test_document_retrieval),
        ("Similarity Search", test_similarity_search),
        ("RAG Retriever", test_rag_retriever),
        ("Visualization Detection", test_visualization_detection),
        ("Data Extraction", test_data_extraction),
        ("Chart Generation", test_chart_generation),
        ("Full Pipeline", test_full_pipeline),
    ]
    
    for test_name, test_func in test_functions:
        try:
            passed = test_func()
            results[test_name] = "✓ PASSED" if passed else "✗ FAILED"
        except Exception as e:
            results[test_name] = f"✗ ERROR: {e}"
            logger.error(f"Test '{test_name}' failed: {e}", exc_info=True)
    
    # Test 8 is async
    try:
        passed = asyncio.run(test_with_real_question())
        results["Real Question Test"] = "✓ PASSED" if passed else "✗ FAILED"
    except Exception as e:
        results["Real Question Test"] = f"✗ ERROR: {e}"
        logger.error(f"Real question test failed: {e}", exc_info=True)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        print(f"{test_name:<40} {result}")
    
    # Determine overall status
    passed_count = sum(1 for r in results.values() if "PASSED" in r)
    total_count = len(results)
    
    print(f"\n{passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ All tests passed! Chart visualization should work.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("\nKey issues to check:")
        if "✗ FAILED" in results.get("Vector Store Contents", ""):
            print("  1. No documents in vector store - PDF may not be uploaded")
        if "✗ FAILED" in results.get("Similarity Search", ""):
            print("  2. Similarity search not working - vector store issue")
        if "✗ FAILED" in results.get("RAG Retriever", ""):
            print("  3. RAG retriever returning no context - document retrieval issue")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
