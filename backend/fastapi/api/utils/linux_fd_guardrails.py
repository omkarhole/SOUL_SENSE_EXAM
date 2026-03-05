#!/usr/bin/env python3
"""
Linux File Descriptor Exhaustion Guardrails - Issue #1316

Implements comprehensive guardrails to prevent OS-level file descriptor exhaustion:
- Proactive FD monitoring with configurable thresholds
- Backpressure mechanisms for burst traffic
- Graceful degradation when approaching limits
- Automatic leak detection and recovery
- Integration with FastAPI for request rejection at critical levels

This module provides deterministic protection against EMFILE errors and service
crashes under high load on Linux systems.
"""

import os
import sys
import time
import asyncio
import threading
import logging
from typing import Dict, List, Set, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from contextlib import contextmanager, asynccontextmanager
from collections import defaultdict
import psutil

# resource module is only available on Unix-like systems
try:
    import resource
    HAS_RESOURCE_MODULE = True
except ImportError:
    HAS_RESOURCE_MODULE = False
    resource = None

logger = logging.getLogger(__name__)


class FDGuardrailState(Enum):
    """States of the FD guardrail system."""
    HEALTHY = "healthy"           # Normal operation
    WARNING = "warning"           # Elevated usage, monitor closely
    DEGRADED = "degraded"         # High usage, apply backpressure
    CRITICAL = "critical"         # Near limit, reject new requests
    RECOVERING = "recovering"     # Attempting recovery after critical


class FDExhaustionAction(Enum):
    """Actions to take when FD exhaustion is detected."""
    LOG_ONLY = auto()             # Just log the issue
    BACKPRESSURE = auto()         # Apply backpressure (slow down)
    REJECT_REQUESTS = auto()      # Reject new incoming requests
    FORCE_CLEANUP = auto()        # Aggressive cleanup of resources
    EMERGENCY_SHUTDOWN = auto()   # Emergency shutdown (last resort)


@dataclass
class FDThresholds:
    """Configurable thresholds for FD guardrails."""
    warning_percent: float = 70.0      # 70% - warning threshold
    degraded_percent: float = 80.0     # 80% - degraded threshold  
    critical_percent: float = 90.0     # 90% - critical threshold
    emergency_percent: float = 95.0    # 95% - emergency threshold
    
    # Absolute FD counts (used if system limit can't be determined)
    warning_count: int = 700
    degraded_count: int = 800
    critical_count: int = 900
    emergency_count: int = 950
    
    def get_thresholds(self, max_fds: int) -> Dict[str, int]:
        """Calculate absolute thresholds based on system limit."""
        if max_fds > 0:
            return {
                'warning': int(max_fds * self.warning_percent / 100),
                'degraded': int(max_fds * self.degraded_percent / 100),
                'critical': int(max_fds * self.critical_percent / 100),
                'emergency': int(max_fds * self.emergency_percent / 100),
            }
        else:
            return {
                'warning': self.warning_count,
                'degraded': self.degraded_count,
                'critical': self.critical_count,
                'emergency': self.emergency_count,
            }


@dataclass
class FDGuardrailMetrics:
    """Metrics for FD guardrail monitoring."""
    timestamp: float
    current_fds: int
    max_fds: int
    usage_percent: float
    state: FDGuardrailState
    requests_accepted: int = 0
    requests_rejected: int = 0
    cleanups_performed: int = 0
    fds_reclaimed: int = 0


@dataclass
class TrackedFD:
    """Information about a tracked file descriptor."""
    fd: int
    fd_type: str
    owner: str
    created_at: float
    last_accessed: float
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class LinuxFDGuardrails:
    """
    Linux File Descriptor Exhaustion Guardrails.
    
    Provides comprehensive protection against FD exhaustion with:
    - Real-time FD usage monitoring
    - Configurable threshold-based state transitions
    - Backpressure and request rejection mechanisms
    - Automatic leak detection and cleanup
    - Detailed metrics and observability
    
    Usage:
        guardrails = LinuxFDGuardrails()
        guardrails.start()
        
        # Check before accepting new connections
        if guardrails.can_accept_request():
            # Process request
        else:
            # Return 503 Service Unavailable
    """
    
    def __init__(
        self,
        thresholds: Optional[FDThresholds] = None,
        check_interval: float = 5.0,
        leak_detection_interval: float = 60.0,
        enable_auto_cleanup: bool = True,
        max_history_size: int = 1000,
        max_fds: Optional[int] = None
    ):
        """
        Initialize FD guardrails.
        
        Args:
            thresholds: FD usage thresholds
            check_interval: How often to check FD usage (seconds)
            leak_detection_interval: How often to check for leaks (seconds)
            enable_auto_cleanup: Whether to enable automatic cleanup
            max_history_size: Maximum metrics history to keep
            max_fds: Override system FD limit (for testing)
        """
        self.thresholds = thresholds or FDThresholds()
        self.check_interval = check_interval
        self.leak_detection_interval = leak_detection_interval
        self.enable_auto_cleanup = enable_auto_cleanup
        self.max_history_size = max_history_size
        
        # System limits
        self._max_fds = max_fds if max_fds is not None else self._get_system_fd_limit()
        self._calculated_thresholds = self.thresholds.get_thresholds(self._max_fds)
        
        # State tracking
        self._state = FDGuardrailState.HEALTHY
        self._state_lock = threading.RLock()
        self._last_state_change = time.time()
        
        # FD tracking
        self._tracked_fds: Dict[int, TrackedFD] = {}
        self._fd_lock = threading.RLock()
        self._fd_usage_history: List[Tuple[float, int]] = []
        
        # Request tracking
        self._requests_accepted = 0
        self._requests_rejected = 0
        self._request_lock = threading.Lock()
        
        # Cleanup tracking
        self._cleanups_performed = 0
        self._fds_reclaimed = 0
        
        # Metrics history
        self._metrics_history: List[FDGuardrailMetrics] = []
        
        # Callbacks
        self._state_callbacks: List[Callable[[FDGuardrailState, FDGuardrailState], None]] = []
        self._action_callbacks: List[Callable[[FDExhaustionAction, Dict], None]] = []
        
        # Monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # Recovery tracking
        self._consecutive_critical = 0
        self._last_cleanup_time = 0
        self._recovery_cooldown = 30.0  # Seconds between recovery attempts
        
        logger.info(
            f"LinuxFDGuardrails initialized: max_fds={self._max_fds}, "
            f"thresholds={self._calculated_thresholds}"
        )
    
    def _get_system_fd_limit(self) -> int:
        """Get the system file descriptor limit."""
        if not HAS_RESOURCE_MODULE:
            # Windows fallback - use reasonable default
            return 8192
        
        try:
            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            # Use soft limit but cap at reasonable value for containerized environments
            return min(soft_limit, 65536)
        except (AttributeError, OSError, ValueError) as e:
            logger.warning(f"Could not get system FD limit: {e}, using default")
            return 8192
    
    def _get_current_fd_count(self) -> int:
        """Get current number of open file descriptors."""
        try:
            # Method 1: /proc/self/fd (Linux-specific)
            fd_dir = '/proc/self/fd'
            if os.path.exists(fd_dir):
                return len(os.listdir(fd_dir)) - 1  # Exclude the fd directory itself
        except (OSError, PermissionError):
            pass
        
        try:
            # Method 2: psutil
            process = psutil.Process()
            return process.num_fds()
        except (AttributeError, psutil.Error):
            pass
        
        # Fallback: return tracked count
        with self._fd_lock:
            return len(self._tracked_fds)
    
    def _determine_state(self, current_fds: int) -> FDGuardrailState:
        """Determine guardrail state based on current FD usage."""
        thresholds = self._calculated_thresholds
        
        if current_fds >= thresholds['emergency']:
            return FDGuardrailState.CRITICAL
        elif current_fds >= thresholds['critical']:
            return FDGuardrailState.CRITICAL
        elif current_fds >= thresholds['degraded']:
            return FDGuardrailState.DEGRADED
        elif current_fds >= thresholds['warning']:
            return FDGuardrailState.WARNING
        else:
            return FDGuardrailState.HEALTHY
    
    def _handle_state_transition(
        self,
        new_state: FDGuardrailState,
        current_fds: int
    ) -> None:
        """Handle state transition and trigger appropriate actions."""
        with self._state_lock:
            old_state = self._state
            
            if new_state == old_state:
                # Track consecutive critical events
                if new_state == FDGuardrailState.CRITICAL:
                    self._consecutive_critical += 1
                return
            
            # State has changed
            self._state = new_state
            self._last_state_change = time.time()
            
            if new_state == FDGuardrailState.CRITICAL:
                self._consecutive_critical += 1
            else:
                self._consecutive_critical = 0
            
            logger.warning(
                f"FD Guardrail state change: {old_state.value} -> {new_state.value} "
                f"(FDs: {current_fds}/{self._max_fds})"
            )
        
        # Trigger callbacks outside of lock
        for callback in self._state_callbacks:
            try:
                callback(new_state, old_state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
        
        # Trigger appropriate action
        self._trigger_action_for_state(new_state, current_fds)
    
    def _trigger_action_for_state(
        self,
        state: FDGuardrailState,
        current_fds: int
    ) -> None:
        """Trigger appropriate action for the current state."""
        actions_map = {
            FDGuardrailState.HEALTHY: FDExhaustionAction.LOG_ONLY,
            FDGuardrailState.WARNING: FDExhaustionAction.LOG_ONLY,
            FDGuardrailState.DEGRADED: FDExhaustionAction.BACKPRESSURE,
            FDGuardrailState.CRITICAL: FDExhaustionAction.REJECT_REQUESTS,
        }
        
        action = actions_map.get(state, FDExhaustionAction.LOG_ONLY)
        
        action_data = {
            'state': state,
            'current_fds': current_fds,
            'max_fds': self._max_fds,
            'usage_percent': (current_fds / self._max_fds * 100) if self._max_fds > 0 else 0,
            'timestamp': time.time()
        }
        
        # Execute action
        if action == FDExhaustionAction.FORCE_CLEANUP or (
            state == FDGuardrailState.CRITICAL and self.enable_auto_cleanup
        ):
            self._perform_cleanup()
        
        # Trigger callbacks
        for callback in self._action_callbacks:
            try:
                callback(action, action_data)
            except Exception as e:
                logger.error(f"Error in action callback: {e}")
    
    def _perform_cleanup(self) -> int:
        """Perform cleanup of leaked/reclaimable FDs. Returns number reclaimed."""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self._last_cleanup_time < self._recovery_cooldown:
            return 0
        
        self._last_cleanup_time = current_time
        reclaimed = 0
        
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clean up old tracked FDs
            with self._fd_lock:
                stale_fds = []
                for fd, info in self._tracked_fds.items():
                    # Consider FDs stale if not accessed for 10 minutes
                    if current_time - info.last_accessed > 600:
                        stale_fds.append(fd)
                
                for fd in stale_fds:
                    try:
                        os.close(fd)
                        del self._tracked_fds[fd]
                        reclaimed += 1
                    except OSError:
                        # FD may already be closed
                        if fd in self._tracked_fds:
                            del self._tracked_fds[fd]
            
            self._cleanups_performed += 1
            self._fds_reclaimed += reclaimed
            
            if reclaimed > 0:
                logger.info(f"Cleanup completed: reclaimed {reclaimed} FDs")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        return reclaimed
    
    def _check_for_leaks(self) -> List[int]:
        """Check for potential FD leaks. Returns list of potentially leaked FDs."""
        current_time = time.time()
        suspected_leaks = []
        
        with self._fd_lock:
            for fd, info in self._tracked_fds.items():
                # Check for FDs that haven't been accessed in a long time
                if current_time - info.last_accessed > 3600:  # 1 hour
                    suspected_leaks.append(fd)
                    logger.warning(
                        f"Suspected FD leak: fd={fd}, owner={info.owner}, "
                        f"age={current_time - info.created_at:.0f}s"
                    )
        
        return suspected_leaks
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        last_leak_check = 0
        
        while not self._stop_monitoring.is_set():
            try:
                current_fds = self._get_current_fd_count()
                new_state = self._determine_state(current_fds)
                
                # Record metrics
                self._record_metrics(current_fds, new_state)
                
                # Handle state transition
                self._handle_state_transition(new_state, current_fds)
                
                # Periodic leak detection
                current_time = time.time()
                if current_time - last_leak_check >= self.leak_detection_interval:
                    self._check_for_leaks()
                    last_leak_check = current_time
                
            except Exception as e:
                logger.error(f"Error in FD guardrail monitor loop: {e}")
            
            self._stop_monitoring.wait(self.check_interval)
    
    def _record_metrics(
        self,
        current_fds: int,
        state: FDGuardrailState
    ) -> None:
        """Record metrics for monitoring."""
        with self._request_lock:
            metrics = FDGuardrailMetrics(
                timestamp=time.time(),
                current_fds=current_fds,
                max_fds=self._max_fds,
                usage_percent=(current_fds / self._max_fds * 100) if self._max_fds > 0 else 0,
                state=state,
                requests_accepted=self._requests_accepted,
                requests_rejected=self._requests_rejected,
                cleanups_performed=self._cleanups_performed,
                fds_reclaimed=self._fds_reclaimed
            )
        
        self._metrics_history.append(metrics)
        
        # Trim history if needed
        if len(self._metrics_history) > self.max_history_size:
            self._metrics_history = self._metrics_history[-self.max_history_size:]
        
        # Keep FD usage history for trend analysis
        self._fd_usage_history.append((time.time(), current_fds))
        if len(self._fd_usage_history) > 100:
            self._fd_usage_history = self._fd_usage_history[-100:]
    
    def start(self) -> None:
        """Start the FD guardrail monitoring."""
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            logger.warning("FD guardrail monitoring already running")
            return
        
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Linux FD Guardrails monitoring started")
    
    def stop(self) -> None:
        """Stop the FD guardrail monitoring."""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10.0)
            logger.info("Linux FD Guardrails monitoring stopped")
    
    def can_accept_request(self) -> bool:
        """
        Check if a new request can be accepted.
        
        Returns:
            True if request can be accepted, False otherwise
        """
        with self._state_lock:
            state = self._state
        
        with self._request_lock:
            if state in (FDGuardrailState.CRITICAL,):
                self._requests_rejected += 1
                return False
            self._requests_accepted += 1
            return True
    
    def get_backpressure_delay(self) -> float:
        """
        Get recommended backpressure delay for current state.
        
        Returns:
            Delay in seconds to apply before processing requests
        """
        with self._state_lock:
            state = self._state
        
        delays = {
            FDGuardrailState.HEALTHY: 0.0,
            FDGuardrailState.WARNING: 0.01,     # 10ms
            FDGuardrailState.DEGRADED: 0.1,      # 100ms
            FDGuardrailState.CRITICAL: 0.5,      # 500ms (rarely used as requests rejected)
            FDGuardrailState.RECOVERING: 0.05,   # 50ms
        }
        return delays.get(state, 0.0)
    
    def track_fd(
        self,
        fd: int,
        fd_type: str,
        owner: str,
        **metadata
    ) -> None:
        """
        Track a file descriptor.
        
        Args:
            fd: File descriptor number
            fd_type: Type of FD (socket, file, pipe, etc.)
            owner: Component that owns this FD
            **metadata: Additional metadata
        """
        import traceback
        
        with self._fd_lock:
            self._tracked_fds[fd] = TrackedFD(
                fd=fd,
                fd_type=fd_type,
                owner=owner,
                created_at=time.time(),
                last_accessed=time.time(),
                stack_trace=traceback.format_stack(limit=5) if logger.isEnabledFor(logging.DEBUG) else None,
                metadata=metadata
            )
    
    def untrack_fd(self, fd: int) -> None:
        """Stop tracking a file descriptor."""
        with self._fd_lock:
            if fd in self._tracked_fds:
                del self._tracked_fds[fd]
    
    def update_fd_access(self, fd: int) -> None:
        """Update last access time for a tracked FD."""
        with self._fd_lock:
            if fd in self._tracked_fds:
                self._tracked_fds[fd].last_accessed = time.time()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current guardrail status."""
        with self._state_lock:
            state = self._state
        
        current_fds = self._get_current_fd_count()
        
        with self._request_lock:
            return {
                'state': state.value,
                'current_fds': current_fds,
                'max_fds': self._max_fds,
                'usage_percent': round((current_fds / self._max_fds * 100), 2) if self._max_fds > 0 else 0,
                'thresholds': self._calculated_thresholds,
                'requests_accepted': self._requests_accepted,
                'requests_rejected': self._requests_rejected,
                'cleanups_performed': self._cleanups_performed,
                'fds_reclaimed': self._fds_reclaimed,
                'tracked_fds_count': len(self._tracked_fds),
                'can_accept_requests': state not in (FDGuardrailState.CRITICAL,),
            }
    
    def get_metrics(self, count: int = 100) -> List[FDGuardrailMetrics]:
        """Get recent metrics history."""
        return self._metrics_history[-count:] if self._metrics_history else []
    
    def get_tracked_fds(self) -> List[TrackedFD]:
        """Get list of tracked file descriptors."""
        with self._fd_lock:
            return list(self._tracked_fds.values())
    
    def add_state_callback(
        self,
        callback: Callable[[FDGuardrailState, FDGuardrailState], None]
    ) -> None:
        """Add a callback for state changes."""
        self._state_callbacks.append(callback)
    
    def add_action_callback(
        self,
        callback: Callable[[FDExhaustionAction, Dict], None]
    ) -> None:
        """Add a callback for actions."""
        self._action_callbacks.append(callback)
    
    @contextmanager
    def managed_fd(self, fd: int, fd_type: str, owner: str, **metadata):
        """
        Context manager for tracking FD lifecycle.
        
        Usage:
            with guardrails.managed_fd(sock.fileno(), 'socket', 'connection_handler'):
                # Use socket
                pass
            # FD automatically untracked on exit
        """
        self.track_fd(fd, fd_type, owner, **metadata)
        try:
            yield fd
        finally:
            self.untrack_fd(fd)
    
    def force_cleanup(self) -> int:
        """Force immediate cleanup. Returns number of FDs reclaimed."""
        return self._perform_cleanup()
    
    def get_fd_usage_trend(self, window_seconds: float = 300.0) -> Optional[float]:
        """
        Calculate FD usage trend (FDs per minute) over the specified window.
        
        Returns:
            Trend in FDs per minute, or None if insufficient data
        """
        if len(self._fd_usage_history) < 2:
            return None
        
        current_time = time.time()
        recent_samples = [
            (t, fds) for t, fds in self._fd_usage_history
            if current_time - t <= window_seconds
        ]
        
        if len(recent_samples) < 2:
            return None
        
        # Simple linear regression
        n = len(recent_samples)
        sum_x = sum(t for t, _ in recent_samples)
        sum_y = sum(fds for _, fds in recent_samples)
        sum_xy = sum(t * fds for t, fds in recent_samples)
        sum_x2 = sum(t * t for t, _ in recent_samples)
        
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            # Convert to FDs per minute
            return slope * 60
        except ZeroDivisionError:
            return None


# Global instance for application-wide use
_fd_guardrails_instance: Optional[LinuxFDGuardrails] = None
_fd_guardrails_lock = threading.Lock()


def get_fd_guardrails() -> LinuxFDGuardrails:
    """Get the global FD guardrails instance."""
    global _fd_guardrails_instance
    with _fd_guardrails_lock:
        if _fd_guardrails_instance is None:
            _fd_guardrails_instance = LinuxFDGuardrails()
        return _fd_guardrails_instance


def init_fd_guardrails(**kwargs) -> LinuxFDGuardrails:
    """
    Initialize the global FD guardrails with custom settings.
    
    Args:
        **kwargs: Arguments to pass to LinuxFDGuardrails constructor
        
    Returns:
        The initialized LinuxFDGuardrails instance
    """
    global _fd_guardrails_instance
    with _fd_guardrails_lock:
        if _fd_guardrails_instance is None:
            _fd_guardrails_instance = LinuxFDGuardrails(**kwargs)
        return _fd_guardrails_instance


# Convenience functions for common operations
def check_can_accept_request() -> bool:
    """Check if the system can accept new requests."""
    return get_fd_guardrails().can_accept_request()


def get_current_fd_status() -> Dict[str, Any]:
    """Get current FD guardrail status."""
    return get_fd_guardrails().get_status()


# Async helpers for FastAPI integration
@asynccontextmanager
async def fd_guarded_operation(operation_name: str = "unnamed"):
    """
    Async context manager for FD-guarded operations.
    
    Usage:
        async with fd_guarded_operation("database_query"):
            # Perform operation
            result = await db.execute(query)
    """
    guardrails = get_fd_guardrails()
    
    if not guardrails.can_accept_request():
        raise FDExhaustionError("Service temporarily unavailable due to resource constraints")
    
    try:
        yield
    finally:
        pass


class FDExhaustionError(Exception):
    """Exception raised when FD exhaustion prevents operation execution."""
    pass
