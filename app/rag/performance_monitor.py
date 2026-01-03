"""
Performance monitoring and profiling utilities for enterprise RAG.

Tracks:
- Request latency
- Retrieval performance
- Embedding performance
- Cache hit rates
- End-to-end processing time
"""
import logging
import time
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors and tracks performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, Dict] = {
            "requests": [],
            "retrievals": [],
            "embeddings": [],
            "answers": []
        }
        self.start_time = time.time()
    
    def record_request(self, question: str, latency_s: float, cached: bool = False) -> None:
        """Record chat request latency."""
        self.metrics["requests"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "question_length": len(question),
            "latency_s": latency_s,
            "cached": cached
        })
        logger.debug(f"📊 Request recorded: {latency_s:.3f}s (cached={cached})")
    
    def record_retrieval(self, query: str, count: int, latency_s: float, confidence: float = 1.0) -> None:
        """Record retrieval performance."""
        self.metrics["retrievals"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "query_length": len(query),
            "result_count": count,
            "latency_s": latency_s,
            "confidence": confidence
        })
    
    def record_embedding(self, count: int, latency_s: float) -> None:
        """Record embedding performance."""
        self.metrics["embeddings"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "count": count,
            "latency_s": latency_s,
            "rate_per_sec": count / max(latency_s, 0.001)
        })
    
    def record_answer(self, answer_length: int, latency_s: float) -> None:
        """Record answer generation performance."""
        self.metrics["answers"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "answer_length": answer_length,
            "latency_s": latency_s
        })
    
    def get_summary(self) -> Dict:
        """Get performance summary statistics."""
        return {
            "total_requests": len(self.metrics["requests"]),
            "total_retrievals": len(self.metrics["retrievals"]),
            "total_embeddings": len(self.metrics["embeddings"]),
            "total_answers": len(self.metrics["answers"]),
            "avg_request_latency_s": self._avg_latency(self.metrics["requests"]),
            "avg_retrieval_latency_s": self._avg_latency(self.metrics["retrievals"]),
            "avg_embedding_latency_s": self._avg_latency(self.metrics["embeddings"]),
            "avg_answer_latency_s": self._avg_latency(self.metrics["answers"]),
            "uptime_s": time.time() - self.start_time
        }
    
    @staticmethod
    def _avg_latency(metrics: list) -> float:
        """Calculate average latency from metrics list."""
        if not metrics:
            return 0.0
        return sum(m["latency_s"] for m in metrics) / len(metrics)
    
    def log_summary(self) -> None:
        """Log performance summary."""
        summary = self.get_summary()
        logger.info("=" * 60)
        logger.info("📊 PERFORMANCE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Requests: {summary['total_requests']}")
        logger.info(f"Avg Request Latency: {summary['avg_request_latency_s']:.3f}s")
        logger.info(f"Avg Retrieval Latency: {summary['avg_retrieval_latency_s']:.3f}s")
        logger.info(f"Avg Answer Latency: {summary['avg_answer_latency_s']:.3f}s")
        logger.info(f"Uptime: {summary['uptime_s']:.1f}s")
        logger.info("=" * 60)


# Global monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor
