"""
Metrics Collector for GitLlama
Simple metrics collection focused on AI call and compression tracking
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Simple metrics collector for AI operations"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the metrics collector (only once)"""
        if not self._initialized:
            self.api_calls = 0
            self.operations = []
            self.compression_events = []
            self.start_time = datetime.now()
            MetricsCollector._initialized = True
            logger.info("📊 Metrics Collector initialized")
    
    def record_ai_call(self, operation_type: str, operation_name: str = ""):
        """Record an AI API call"""
        self.api_calls += 1
        self.operations.append({
            "timestamp": datetime.now(),
            "type": operation_type,
            "name": operation_name,
            "call_number": self.api_calls
        })
        logger.info(f"🤖 AI call #{self.api_calls}: {operation_type} - {operation_name}")
    
    def record_compression(self, original_size: int, compressed_size: int, rounds: int, success: bool):
        """Record a context compression event"""
        self.compression_events.append({
            "timestamp": datetime.now(),
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": (1 - compressed_size / original_size) * 100 if original_size > 0 else 0,
            "rounds": rounds,
            "success": success
        })
        logger.info(f"🗜️ Compression recorded: {original_size} → {compressed_size} tokens ({rounds} rounds)")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "total_calls": self.api_calls,
            "runtime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "operations": self.operations,
            "compression_events": self.compression_events,
            "total_compressions": len(self.compression_events)
        }
    
    def get_display_summary(self) -> str:
        """Get formatted summary for display"""
        if not self.operations:
            return "No AI operations recorded."
        
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        # Count operation types
        type_counts = {}
        for op in self.operations:
            op_type = op['type']
            type_counts[op_type] = type_counts.get(op_type, 0) + 1
        
        lines = [
            f"📊 AI Operations Summary:",
            f"🔢 Total Calls: {self.api_calls}",
            f"⏱️ Runtime: {runtime:.1f} seconds",
        ]
        
        # Add compression stats if any
        if self.compression_events:
            successful_compressions = sum(1 for e in self.compression_events if e['success'])
            avg_ratio = sum(e['compression_ratio'] for e in self.compression_events) / len(self.compression_events)
            lines.extend([
                f"🗜️ Context Compressions: {len(self.compression_events)} ({successful_compressions} successful)",
                f"📉 Avg Compression Ratio: {avg_ratio:.1f}%",
            ])
        
        lines.extend([
            "",
            "Operation Types:"
        ])
        
        for op_type, count in type_counts.items():
            lines.append(f"  {op_type}: {count} calls")
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset metrics (for testing)"""
        self.api_calls = 0
        self.operations.clear()
        self.compression_events.clear()
        self.start_time = datetime.now()
        logger.info("🔄 Metrics reset")


# Global instance
context_manager = MetricsCollector()