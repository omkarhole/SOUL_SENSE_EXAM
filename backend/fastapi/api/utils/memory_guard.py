import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def check_memory_usage(threshold_mb: int = 512) -> bool:
    """
    Checks if the current process memory usage exceeds the threshold.
    Returns True if usage is within limits, False if it exceeds it.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024 * 1024)
        
        if mem_mb > threshold_mb:
            logger.warning(f"Proactive Memory Guard: Process {os.getpid()} using {mem_mb:.2f} MB, exceeding threshold {threshold_mb} MB.")
            return False
        return True
    except ImportError:
        logger.warning("[MemoryGuard] psutil not installed. Memory check skipped. To enable, install psutil (e.g., pip install psutil).")
        return True
    except Exception as e:
        logger.warning(f"[MemoryGuard] Memory check failed or not supported on this platform: {e}")
        return True

def enforce_memory_limit(threshold_mb: int = 512):
    """
    If memory usage exceeds threshold, raises a MemoryError or signals for restart.
    """
    if not check_memory_usage(threshold_mb):
        raise MemoryError(f"Process memory threshold exceeded ({threshold_mb} MB)")

def get_total_system_memory_usage() -> float:
    """Returns system memory usage percentage."""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except ImportError:
        return 0.0
