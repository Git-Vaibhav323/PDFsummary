import sys
import json
from app.rag.vector_store import VectorStore

query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Show me the charts"

vs = VectorStore()

try:
    # try to get collection count
    try:
        collection = vs.vectorstore._collection
        count = collection.count()
    except Exception:
        count = None

    print(json.dumps({"query": query, "collection_count": count}))

    results = vs.similarity_search(query, k=5)
    print(json.dumps({"results": results}, default=str, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
    raise
