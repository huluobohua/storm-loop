"""
Memory management utilities for academic research workloads.
Addresses Issue #65: Performance Optimization and Scalability for Academic Research Loads.
"""

import gc
import psutil
import logging
from typing import Optional
from contextlib import contextmanager


class MemoryManager:
    """Manages memory usage during intensive academic research operations."""
    
    def __init__(self, max_memory_mb: Optional[int] = None):
        """
        Initialize memory manager.
        
        Args:
            max_memory_mb: Maximum memory usage in MB. If None, uses 80% of available memory.
        """
        self.logger = logging.getLogger(__name__)
        
        if max_memory_mb is None:
            # Use 80% of available memory as default limit
            available_memory_mb = psutil.virtual_memory().available // (1024 * 1024)
            self.max_memory_mb = int(available_memory_mb * 0.8)
        else:
            self.max_memory_mb = max_memory_mb
            
        self.logger.info(f"Memory manager initialized with limit: {self.max_memory_mb} MB")
    
    def get_current_memory_usage_mb(self) -> int:
        """Get current memory usage in MB."""
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss // (1024 * 1024)  # Convert bytes to MB
    
    def get_memory_usage_percent(self) -> float:
        """Get current memory usage as percentage of limit."""
        current_mb = self.get_current_memory_usage_mb()
        return (current_mb / self.max_memory_mb) * 100.0
    
    def check_memory_limit(self) -> bool:
        """Check if current memory usage exceeds the limit."""
        return self.get_current_memory_usage_mb() > self.max_memory_mb
    
    def force_garbage_collection(self):
        """Force garbage collection to free memory."""
        collected = gc.collect()
        self.logger.debug(f"Garbage collection freed {collected} objects")
        return collected
    
    @contextmanager
    def memory_monitor(self, operation_name: str = "operation"):
        """Context manager to monitor memory usage during operations."""
        
        start_memory = self.get_current_memory_usage_mb()
        self.logger.info(
            f"Starting {operation_name} - Memory usage: {start_memory} MB "
            f"({self.get_memory_usage_percent():.1f}% of limit)"
        )
        
        try:
            yield self
            
            # Check if we exceeded memory limit during operation
            if self.check_memory_limit():
                self.logger.warning(
                    f"Memory limit exceeded during {operation_name}. "
                    f"Current: {self.get_current_memory_usage_mb()} MB, "
                    f"Limit: {self.max_memory_mb} MB"
                )
                self.force_garbage_collection()
                
        finally:
            end_memory = self.get_current_memory_usage_mb()
            memory_delta = end_memory - start_memory
            
            self.logger.info(
                f"Completed {operation_name} - Memory usage: {end_memory} MB "
                f"(delta: {memory_delta:+d} MB, {self.get_memory_usage_percent():.1f}% of limit)"
            )
    
    def get_memory_stats(self) -> dict:
        """Get detailed memory statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            "process_memory_mb": memory_info.rss // (1024 * 1024),
            "process_memory_percent": process.memory_percent(),
            "system_total_mb": system_memory.total // (1024 * 1024),
            "system_available_mb": system_memory.available // (1024 * 1024),
            "system_used_percent": system_memory.percent,
            "manager_limit_mb": self.max_memory_mb,
            "manager_usage_percent": self.get_memory_usage_percent(),
            "limit_exceeded": self.check_memory_limit()
        }


# Global memory manager instance
memory_manager = MemoryManager()


def get_memory_stats() -> dict:
    """Get current memory statistics."""
    return memory_manager.get_memory_stats()


def monitor_memory(operation_name: str = "operation"):
    """Monitor memory usage for an operation."""
    return memory_manager.memory_monitor(operation_name)