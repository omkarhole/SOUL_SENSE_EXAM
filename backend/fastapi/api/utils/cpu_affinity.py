"""
CPU Affinity Management Utilities for Celery Workers.

Provides functionality to bind worker processes to specific CPU cores
to reduce context thrashing and improve cache locality.

Supports:
- Linux (via psutil or taskset)
- macOS (via psutil)
- Windows (limited support via psutil)
- Cross-platform fallback with graceful degradation
"""

import os
import logging
import multiprocessing
from typing import List, Optional, Dict, Any
import psutil

logger = logging.getLogger(__name__)


def get_available_cores() -> int:
    """
    Get the number of available CPU cores.
    
    Returns:
        Number of CPU cores available on the system
    """
    cores = os.cpu_count() or multiprocessing.cpu_count()
    return cores


def get_optimal_worker_count(cpu_cores: Optional[int] = None) -> int:
    """
    Calculate optimal worker count based on CPU cores.
    
    Formula: cores * 1.5 to cores * 2 for optimal throughput
    without excessive context switching. Bounded between 2 and 32 workers.
    
    This accounts for:
    - I/O blocking: Workers may block on I/O, needing extra workers
    - Context switch overhead: Too many workers cause thrashing
    - Memory constraints: Limit to 32 workers to avoid resource exhaustion
    
    Args:
        cpu_cores: Number of CPU cores (auto-detected if None)
        
    Returns:
        Recommended number of worker processes for optimal performance
        
    Example:
        >>> get_optimal_worker_count(4)
        6  # 4 * 1.5
        >>> get_optimal_worker_count(8)
        12  # 8 * 1.5
    """
    if cpu_cores is None:
        cpu_cores = get_available_cores()
    
    # Balance: cores * 1.5 for slight oversubscription to handle I/O
    optimal = int(cpu_cores * 1.5)
    
    # Bounds: Between 2 and 32 workers
    return max(2, min(optimal, 32))


def bind_process_to_cores(cores: List[int]) -> bool:
    """
    Bind current process to specific CPU cores.
    
    Cross-platform implementation using psutil with graceful fallback.
    
    Args:
        cores: List of core IDs to bind to (0-indexed)
        
    Returns:
        True if binding successful, False otherwise
        
    Raises:
        Nothing - does not raise on failure, only logs warning
        
    Example:
        >>> bind_process_to_cores([0, 1])
        True  # Process now runs only on cores 0 and 1
    """
    try:
        # Use psutil for cross-platform support
        p = psutil.Process(os.getpid())
        p.cpu_affinity(cores)
        logger.info(f"Process {os.getpid()} bound to cores: {cores}")
        return True
    except AttributeError:
        logger.warning(
            "CPU affinity not supported on this platform "
            "(psutil.Process.cpu_affinity not available)"
        )
        return False
    except (OSError, RuntimeError) as e:
        logger.warning(f"Failed to bind process to cores {cores}: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error binding process to cores: {e}")
        return False


def bind_process_to_core(core_id: int) -> bool:
    """
    Bind current process to a single CPU core.
    
    Convenience wrapper around bind_process_to_cores for single core binding.
    
    Args:
        core_id: Core ID to bind to (0-indexed)
        
    Returns:
        True if binding successful, False otherwise
        
    Example:
        >>> bind_process_to_core(0)
        True  # Process now runs only on core 0
    """
    return bind_process_to_cores([core_id])


def get_process_cpu_affinity(pid: Optional[int] = None) -> Optional[List[int]]:
    """
    Get the CPU affinity of a process.
    
    Retrieves the cores a process is bound to.
    
    Args:
        pid: Process ID (current process if None)
        
    Returns:
        List of core IDs the process is bound to, or None if not available
        
    Example:
        >>> get_process_cpu_affinity()
        [0, 1, 2, 3]  # Process can run on cores 0-3
    """
    try:
        if pid is None:
            pid = os.getpid()
        p = psutil.Process(pid)
        return list(p.cpu_affinity())
    except AttributeError:
        logger.debug("CPU affinity not supported on this platform")
        return None
    except (OSError, psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.debug(f"Failed to get CPU affinity for PID {pid}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Unexpected error getting CPU affinity: {e}")
        return None


def distribute_workers_across_cores(
    num_workers: int,
    num_cores: Optional[int] = None
) -> List[List[int]]:
    """
    Distribute workers across available cores.
    
    Creates assignments for worker processes to minimize context switching
    while ensuring good load distribution.
    
    Strategy:
    - If num_workers <= num_cores: Each worker gets exclusive cores
    - If num_workers > num_cores: Multiple workers share cores (round-robin)
    
    Args:
        num_workers: Number of workers to distribute
        num_cores: Number of available cores (auto-detect if None)
        
    Returns:
        List of core assignments, one list per worker.
        Each inner list contains core IDs for that worker.
        
    Example:
        >>> distribute_workers_across_cores(4, 8)
        [[0], [1], [2], [3]]  # Each worker gets one core
        
        >>> distribute_workers_across_cores(8, 4)
        [[0, 1], [2, 3], [0, 1], [2, 3]]  # Cores shared among workers
        
        >>> distribute_workers_across_cores(2, 8)
        [[0, 1, 2, 3], [4, 5, 6, 7]]  # Each worker gets multiple cores
    """
    if num_cores is None:
        num_cores = get_available_cores()
    
    if num_workers <= 0:
        return []
    
    if num_cores <= 0:
        logger.warning("No cores available for distribution")
        return [[] for _ in range(num_workers)]
    
    cores_per_worker = max(1, num_cores / num_workers)
    worker_cores = []
    
    for i in range(num_workers):
        if cores_per_worker >= 1:
            # Each worker gets multiple cores
            start_core = int(i * cores_per_worker) % num_cores
            num_worker_cores = int(cores_per_worker)
            cores = [(start_core + j) % num_cores for j in range(num_worker_cores)]
        else:
            # Multiple workers share same core(s)
            core = i % num_cores
            cores = [core]
        
        worker_cores.append(cores)
    
    return worker_cores


def validate_affinity_support() -> bool:
    """
    Check if the system supports CPU affinity.
    
    Tests the ability to get and set CPU affinity on the current process.
    
    Returns:
        True if CPU affinity is supported, False otherwise
        
    Example:
        >>> if validate_affinity_support():
        ...     bind_process_to_core(0)
    """
    try:
        p = psutil.Process(os.getpid())
        affinity = p.cpu_affinity()
        logger.info(f"CPU affinity support validated. Current affinity: {affinity}")
        return True
    except AttributeError:
        logger.debug("CPU affinity not supported on this platform")
        return False
    except Exception as e:
        logger.debug(f"Error validating CPU affinity: {e}")
        return False


def get_affinity_report() -> Dict[str, Any]:
    """
    Generate a comprehensive report of CPU affinity status.
    
    Provides diagnostic information for debugging and monitoring.
    
    Returns:
        Dictionary with keys:
        - available_cores: Number of CPU cores
        - optimal_workers: Recommended worker count
        - current_process_affinity: Cores current process can use
        - affinity_supported: Whether affinity is supported
        - physical_core_count: Number of physical cores (if detectable)
        - total_memory_gb: Total system memory in GB
        
    Example:
        >>> report = get_affinity_report()
        >>> print(f"Available cores: {report['available_cores']}")
        Available cores: 8
        >>> print(f"Optimal workers: {report['optimal_workers']}")
        Optimal workers: 12
    """
    report = {
        "available_cores": get_available_cores(),
        "optimal_workers": get_optimal_worker_count(),
        "current_process_affinity": get_process_cpu_affinity(),
        "affinity_supported": validate_affinity_support(),
    }
    
    try:
        # Add physical core count if available
        physical_cores = psutil.cpu_count(logical=False)
        if physical_cores:
            report["physical_core_count"] = physical_cores
    except Exception as e:
        logger.debug(f"Could not get physical core count: {e}")
    
    try:
        # Add total memory info
        mem = psutil.virtual_memory()
        report["total_memory_gb"] = round(mem.total / (1024 ** 3), 2)
    except Exception as e:
        logger.debug(f"Could not get memory info: {e}")
    
    return report


def get_cpu_stats() -> Dict[str, Any]:
    """
    Get current CPU utilization statistics.
    
    Useful for monitoring worker efficiency and identifying scheduling issues.
    
    Returns:
        Dictionary with CPU usage per core and system-wide statistics
        
    Example:
        >>> stats = get_cpu_stats()
        >>> print(f"CPU %: {stats['cpu_percent_total']}")
        CPU %: 45.2
    """
    stats = {
        "cpu_count": get_available_cores(),
    }
    
    try:
        # Per-core CPU percentage
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        stats["cpu_percent_per_core"] = per_cpu
        stats["cpu_percent_total"] = sum(per_cpu) / len(per_cpu)
    except Exception as e:
        logger.debug(f"Could not get CPU stats: {e}")
    
    try:
        # Load average (Linux/Unix only)
        load_avg = os.getloadavg()
        stats["load_average_1min"] = load_avg[0]
        stats["load_average_5min"] = load_avg[1]
        stats["load_average_15min"] = load_avg[2]
    except AttributeError:
        # Load average not available on Windows
        pass
    except Exception as e:
        logger.debug(f"Could not get load average: {e}")
    
    return stats


class WorkerAffinityManager:
    """
    Manager for coordinating CPU affinity across multiple workers.
    
    Provides high-level API for worker process management with affinity.
    """
    
    def __init__(self, num_workers: Optional[int] = None):
        """
        Initialize the affinity manager.
        
        Args:
            num_workers: Number of workers to manage (auto-detect if None)
        """
        self.num_cores = get_available_cores()
        self.num_workers = num_workers or get_optimal_worker_count()
        self.affinity_supported = validate_affinity_support()
        
        logger.info(
            f"WorkerAffinityManager initialized: "
            f"{self.num_workers} workers on {self.num_cores} cores "
            f"(affinity supported: {self.affinity_supported})"
        )
    
    def get_worker_cores(self, worker_id: int) -> List[int]:
        """
        Get the core assignment for a specific worker.
        
        Args:
            worker_id: Worker ID (0-indexed)
            
        Returns:
            List of core IDs for this worker
        """
        distribution = distribute_workers_across_cores(self.num_workers, self.num_cores)
        if 0 <= worker_id < len(distribution):
            return distribution[worker_id]
        return [worker_id % self.num_cores]
    
    def bind_worker(self, worker_id: int) -> bool:
        """
        Bind a worker process to its assigned cores.
        
        Args:
            worker_id: Worker ID (0-indexed)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.affinity_supported:
            logger.debug("Affinity not supported, skipping binding")
            return False
        
        cores = self.get_worker_cores(worker_id)
        logger.info(f"Binding worker {worker_id} to cores: {cores}")
        return bind_process_to_cores(cores)
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get a status report for all workers."""
        return {
            "num_workers": self.num_workers,
            "num_cores": self.num_cores,
            "affinity_supported": self.affinity_supported,
            "worker_distributions": distribute_workers_across_cores(
                self.num_workers, self.num_cores
            ),
            "cpu_report": get_affinity_report(),
            "cpu_stats": get_cpu_stats(),
        }


if __name__ == "__main__":
    # Test and demonstrate the module
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    
    print("\n=== CPU Affinity Diagnostics ===\n")
    
    # Report
    report = get_affinity_report()
    print(f"Available Cores: {report['available_cores']}")
    print(f"Optimal Workers: {report['optimal_workers']}")
    print(f"Affinity Supported: {report['affinity_supported']}")
    print(f"Current Process Affinity: {report['current_process_affinity']}")
    
    # CPU Stats
    print("\n=== CPU Statistics ===\n")
    stats = get_cpu_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Worker Distribution
    print("\n=== Worker Distributions ===\n")
    for num_workers in [1, 2, 4, 8, 16]:
        dist = distribute_workers_across_cores(num_workers, report['available_cores'])
        print(f"Workers: {num_workers}, Cores: {report['available_cores']}")
        for i, cores in enumerate(dist):
            print(f"  Worker {i}: {cores}")
    
    # Manager Demo
    print("\n=== Affinity Manager ===\n")
    manager = WorkerAffinityManager(4)
    print(f"Manager Status:\n{manager.get_status_report()}")
