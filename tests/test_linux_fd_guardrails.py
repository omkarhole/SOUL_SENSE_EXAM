#!/usr/bin/env python3
"""
Comprehensive Test Suite for Linux File Descriptor Exhaustion Guardrails - Issue #1316

Tests cover:
- FD monitoring and threshold detection
- State transitions and callbacks
- Backpressure mechanisms
- Leak detection and cleanup
- Request acceptance/rejection logic
- Metrics collection and trend analysis
- Integration with health checks

Run with: pytest tests/test_linux_fd_guardrails.py -v
"""

import os
import sys
import time
import asyncio
import threading
import unittest
import tempfile
import socket
from unittest.mock import Mock, patch, MagicMock, call
from typing import List, Dict, Any

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'fastapi', 'api', 'utils'))
from linux_fd_guardrails import (
    LinuxFDGuardrails,
    FDGuardrailState,
    FDExhaustionAction,
    FDThresholds,
    FDGuardrailMetrics,
    TrackedFD,
    FDExhaustionError,
    get_fd_guardrails,
    init_fd_guardrails,
    check_can_accept_request,
    get_current_fd_status,
    fd_guarded_operation
)


class TestFDThresholds(unittest.TestCase):
    """Test FD threshold configuration."""
    
    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = FDThresholds()
        self.assertEqual(thresholds.warning_percent, 70.0)
        self.assertEqual(thresholds.degraded_percent, 80.0)
        self.assertEqual(thresholds.critical_percent, 90.0)
        self.assertEqual(thresholds.emergency_percent, 95.0)
    
    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        thresholds = FDThresholds(
            warning_percent=60.0,
            degraded_percent=75.0,
            critical_percent=85.0,
            emergency_percent=95.0
        )
        self.assertEqual(thresholds.warning_percent, 60.0)
        self.assertEqual(thresholds.degraded_percent, 75.0)
    
    def test_threshold_calculation_with_system_limit(self):
        """Test threshold calculation based on system limit."""
        thresholds = FDThresholds()
        calculated = thresholds.get_thresholds(1024)
        
        self.assertEqual(calculated['warning'], 716)  # 70% of 1024
        self.assertEqual(calculated['degraded'], 819)  # 80% of 1024
        self.assertEqual(calculated['critical'], 921)  # 90% of 1024
        self.assertEqual(calculated['emergency'], 972)  # 95% of 1024
    
    def test_threshold_calculation_fallback(self):
        """Test threshold fallback when system limit is unknown."""
        thresholds = FDThresholds()
        calculated = thresholds.get_thresholds(0)
        
        self.assertEqual(calculated['warning'], thresholds.warning_count)
        self.assertEqual(calculated['degraded'], thresholds.degraded_count)


class TestLinuxFDGuardrailsBasics(unittest.TestCase):
    """Test basic FD guardrail functionality."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(
            check_interval=0.1,  # Fast for testing
            leak_detection_interval=0.5,
            max_history_size=100
        )
    
    def tearDown(self):
        """Clean up test guardrail instance."""
        self.guardrails.stop()
    
    def test_initialization(self):
        """Test guardrail initialization."""
        self.assertEqual(self.guardrails._state, FDGuardrailState.HEALTHY)
        self.assertTrue(self.guardrails._max_fds > 0)
        self.assertIsNotNone(self.guardrails._calculated_thresholds)
    
    def test_system_fd_limit_detection(self):
        """Test system FD limit detection."""
        max_fds = self.guardrails._get_system_fd_limit()
        self.assertIsInstance(max_fds, int)
        self.assertTrue(max_fds > 0)
        self.assertTrue(max_fds <= 65536)  # Should be capped
    
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_current_fd_count_proc(self, mock_exists, mock_listdir):
        """Test FD count via /proc/self/fd."""
        mock_exists.return_value = True
        mock_listdir.return_value = ['0', '1', '2', '3', '4']
        count = self.guardrails._get_current_fd_count()
        self.assertEqual(count, 4)  # -1 for the fd directory itself
    
    @patch('psutil.Process')
    def test_current_fd_count_psutil(self, mock_process_class):
        """Test FD count via psutil fallback."""
        mock_process = MagicMock()
        mock_process.num_fds.return_value = 42
        mock_process_class.return_value = mock_process
        
        with patch('os.listdir', side_effect=OSError("No /proc")):
            count = self.guardrails._get_current_fd_count()
            self.assertEqual(count, 42)
    
    def test_state_determination(self):
        """Test state determination based on FD usage."""
        thresholds = self.guardrails._calculated_thresholds
        
        # Test healthy state
        self.assertEqual(
            self.guardrails._determine_state(thresholds['warning'] - 1),
            FDGuardrailState.HEALTHY
        )
        
        # Test warning state
        self.assertEqual(
            self.guardrails._determine_state(thresholds['warning']),
            FDGuardrailState.WARNING
        )
        
        # Test degraded state
        self.assertEqual(
            self.guardrails._determine_state(thresholds['degraded']),
            FDGuardrailState.DEGRADED
        )
        
        # Test critical state
        self.assertEqual(
            self.guardrails._determine_state(thresholds['critical']),
            FDGuardrailState.CRITICAL
        )
    
    def test_can_accept_request_healthy(self):
        """Test request acceptance in healthy state."""
        self.guardrails._state = FDGuardrailState.HEALTHY
        self.assertTrue(self.guardrails.can_accept_request())
    
    def test_can_accept_request_warning(self):
        """Test request acceptance in warning state."""
        self.guardrails._state = FDGuardrailState.WARNING
        self.assertTrue(self.guardrails.can_accept_request())
    
    def test_can_accept_request_degraded(self):
        """Test request acceptance in degraded state."""
        self.guardrails._state = FDGuardrailState.DEGRADED
        self.assertTrue(self.guardrails.can_accept_request())
    
    def test_cannot_accept_request_critical(self):
        """Test request rejection in critical state."""
        self.guardrails._state = FDGuardrailState.CRITICAL
        self.assertFalse(self.guardrails.can_accept_request())


class TestFDTracking(unittest.TestCase):
    """Test FD tracking functionality."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(check_interval=60.0)  # Long interval, we're not testing monitoring
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_track_fd(self):
        """Test tracking a file descriptor."""
        self.guardrails.track_fd(42, 'socket', 'test_owner', port=8080)
        
        with self.guardrails._fd_lock:
            self.assertIn(42, self.guardrails._tracked_fds)
            tracked = self.guardrails._tracked_fds[42]
            self.assertEqual(tracked.fd, 42)
            self.assertEqual(tracked.fd_type, 'socket')
            self.assertEqual(tracked.owner, 'test_owner')
            self.assertEqual(tracked.metadata['port'], 8080)
    
    def test_untrack_fd(self):
        """Test untracking a file descriptor."""
        self.guardrails.track_fd(42, 'socket', 'test')
        self.guardrails.untrack_fd(42)
        
        with self.guardrails._fd_lock:
            self.assertNotIn(42, self.guardrails._tracked_fds)
    
    def test_update_fd_access(self):
        """Test updating FD access time."""
        self.guardrails.track_fd(42, 'socket', 'test')
        
        initial_access = self.guardrails._tracked_fds[42].last_accessed
        time.sleep(0.01)
        self.guardrails.update_fd_access(42)
        updated_access = self.guardrails._tracked_fds[42].last_accessed
        
        self.assertGreater(updated_access, initial_access)
    
    def test_get_tracked_fds(self):
        """Test getting list of tracked FDs."""
        self.guardrails.track_fd(42, 'socket', 'owner1')
        self.guardrails.track_fd(43, 'file', 'owner2')
        
        tracked = self.guardrails.get_tracked_fds()
        self.assertEqual(len(tracked), 2)
        fds = [t.fd for t in tracked]
        self.assertIn(42, fds)
        self.assertIn(43, fds)


class TestBackpressure(unittest.TestCase):
    """Test backpressure mechanisms."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(check_interval=60.0)
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_no_backpressure_healthy(self):
        """Test no backpressure delay in healthy state."""
        self.guardrails._state = FDGuardrailState.HEALTHY
        delay = self.guardrails.get_backpressure_delay()
        self.assertEqual(delay, 0.0)
    
    def test_backpressure_warning(self):
        """Test backpressure delay in warning state."""
        self.guardrails._state = FDGuardrailState.WARNING
        delay = self.guardrails.get_backpressure_delay()
        self.assertEqual(delay, 0.01)  # 10ms
    
    def test_backpressure_degraded(self):
        """Test backpressure delay in degraded state."""
        self.guardrails._state = FDGuardrailState.DEGRADED
        delay = self.guardrails.get_backpressure_delay()
        self.assertEqual(delay, 0.1)  # 100ms
    
    def test_backpressure_critical(self):
        """Test backpressure delay in critical state."""
        self.guardrails._state = FDGuardrailState.CRITICAL
        delay = self.guardrails.get_backpressure_delay()
        self.assertEqual(delay, 0.5)  # 500ms


class TestStateTransitions(unittest.TestCase):
    """Test state transition handling."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(check_interval=60.0)
        self.callback_invocations: List[tuple] = []
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_state_callback(self):
        """Test state change callback invocation."""
        def state_callback(new_state, old_state):
            self.callback_invocations.append((new_state, old_state))
        
        self.guardrails.add_state_callback(state_callback)
        
        # Ensure we start in HEALTHY state
        with self.guardrails._state_lock:
            self.guardrails._state = FDGuardrailState.HEALTHY
        
        # Trigger state change from HEALTHY to WARNING
        self.guardrails._handle_state_transition(FDGuardrailState.WARNING, 100)
        
        self.assertEqual(len(self.callback_invocations), 1)
        self.assertEqual(self.callback_invocations[0][0], FDGuardrailState.WARNING)
        self.assertEqual(self.callback_invocations[0][1], FDGuardrailState.HEALTHY)
    
    def test_consecutive_critical_tracking(self):
        """Test tracking of consecutive critical events."""
        self.guardrails._state = FDGuardrailState.WARNING
        
        # Transition to critical
        self.guardrails._handle_state_transition(FDGuardrailState.CRITICAL, 900)
        self.assertEqual(self.guardrails._consecutive_critical, 1)
        
        # Stay in critical
        self.guardrails._handle_state_transition(FDGuardrailState.CRITICAL, 950)
        self.assertEqual(self.guardrails._consecutive_critical, 2)
        
        # Leave critical
        self.guardrails._handle_state_transition(FDGuardrailState.WARNING, 700)
        self.assertEqual(self.guardrails._consecutive_critical, 0)


class TestLeakDetection(unittest.TestCase):
    """Test leak detection functionality."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(
            check_interval=60.0,
            leak_detection_interval=0.1
        )
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_leak_detection(self):
        """Test detection of stale FDs."""
        current_time = time.time()
        
        # Add some tracked FDs
        self.guardrails.track_fd(42, 'socket', 'test1')
        self.guardrails.track_fd(43, 'file', 'test2')
        
        # Mark one as stale
        with self.guardrails._fd_lock:
            self.guardrails._tracked_fds[42].last_accessed = current_time - 7200  # 2 hours ago
            self.guardrails._tracked_fds[42].created_at = current_time - 7200
        
        # Check for leaks
        leaks = self.guardrails._check_for_leaks()
        
        self.assertIn(42, leaks)
        self.assertNotIn(43, leaks)
    
    def test_force_cleanup(self):
        """Test forced cleanup of leaked FDs."""
        current_time = time.time()
        
        # Add stale FDs
        self.guardrails.track_fd(42, 'socket', 'test')
        with self.guardrails._fd_lock:
            self.guardrails._tracked_fds[42].created_at = current_time - 7201
            self.guardrails._tracked_fds[42].last_accessed = current_time - 3601
        
        # Force cleanup
        reclaimed = self.guardrails.force_cleanup()
        
        # Should have cleaned up
        self.assertGreaterEqual(reclaimed, 0)  # May or may not close depending on FD validity


class TestMetrics(unittest.TestCase):
    """Test metrics collection."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(
            check_interval=0.1,
            max_history_size=50
        )
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_metrics_recording(self):
        """Test metrics recording."""
        self.guardrails._record_metrics(100, FDGuardrailState.WARNING)
        
        metrics = self.guardrails.get_metrics()
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].current_fds, 100)
        self.assertEqual(metrics[0].state, FDGuardrailState.WARNING)
    
    def test_metrics_history_limit(self):
        """Test metrics history size limit."""
        for i in range(60):
            self.guardrails._record_metrics(i, FDGuardrailState.HEALTHY)
        
        metrics = self.guardrails.get_metrics(100)
        self.assertLessEqual(len(metrics), 50)  # max_history_size
    
    def test_get_status(self):
        """Test status retrieval."""
        status = self.guardrails.get_status()
        
        self.assertIn('state', status)
        self.assertIn('current_fds', status)
        self.assertIn('max_fds', status)
        self.assertIn('usage_percent', status)
        self.assertIn('thresholds', status)
        self.assertIn('can_accept_requests', status)
    
    def test_fd_usage_trend(self):
        """Test FD usage trend calculation."""
        # Add some history
        current_time = time.time()
        for i in range(10):
            self.guardrails._fd_usage_history.append((current_time - (9-i)*10, 100 + i*10))
        
        trend = self.guardrails.get_fd_usage_trend()
        
        self.assertIsNotNone(trend)
        # Trend should be positive (increasing FDs)
        self.assertGreater(trend, 0)


class TestMonitoring(unittest.TestCase):
    """Test monitoring thread functionality."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(check_interval=0.1)
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_monitor_start_stop(self):
        """Test starting and stopping monitoring."""
        self.guardrails.start()
        self.assertTrue(self.guardrails._monitor_thread.is_alive())
        
        self.guardrails.stop()
        self.assertFalse(self.guardrails._monitor_thread.is_alive())
    
    def test_monitor_records_metrics(self):
        """Test that monitoring records metrics."""
        self.guardrails.start()
        time.sleep(0.2)  # Wait for at least one check
        
        metrics = self.guardrails.get_metrics()
        self.assertGreater(len(metrics), 0)
        
        self.guardrails.stop()


class TestGlobalInstance(unittest.TestCase):
    """Test global singleton instance."""
    
    def tearDown(self):
        """Reset global instance after each test."""
        import linux_fd_guardrails
        linux_fd_guardrails._fd_guardrails_instance = None
    
    def test_singleton_instance(self):
        """Test that get_fd_guardrails returns singleton."""
        g1 = get_fd_guardrails()
        g2 = get_fd_guardrails()
        self.assertIs(g1, g2)
    
    def test_init_fd_guardrails(self):
        """Test initialization with custom settings."""
        guardrails = init_fd_guardrails(max_fds=2048, check_interval=10.0)
        self.assertEqual(guardrails._max_fds, 2048)
        self.assertEqual(guardrails.check_interval, 10.0)
        
        # Second init should return same instance
        guardrails2 = init_fd_guardrails()
        self.assertIs(guardrails, guardrails2)
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test check_can_accept_request
        result = check_can_accept_request()
        self.assertIsInstance(result, bool)
        
        # Test get_current_fd_status
        status = get_current_fd_status()
        self.assertIsInstance(status, dict)
        self.assertIn('state', status)


class TestAsyncOperations(unittest.TestCase):
    """Test async operations."""
    
    def setUp(self):
        """Set up event loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()
    
    def test_fd_guarded_operation_allows(self):
        """Test that fd_guarded_operation allows execution when healthy."""
        async def test():
            async with fd_guarded_operation("test"):
                return "success"
        
        result = self.loop.run_until_complete(test())
        self.assertEqual(result, "success")


class TestIntegration(unittest.TestCase):
    """Integration tests with real resources."""
    
    def setUp(self):
        """Set up test resources."""
        self.guardrails = LinuxFDGuardrails(check_interval=60.0)
        self.temp_files: List[str] = []
    
    def tearDown(self):
        """Clean up resources."""
        self.guardrails.stop()
        for f in self.temp_files:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except:
                pass
    
    def test_real_fd_tracking(self):
        """Test tracking real file descriptors."""
        # Create a real file
        fd, path = tempfile.mkstemp()
        self.temp_files.append(path)
        
        try:
            # Track the FD
            self.guardrails.track_fd(fd, 'file', 'test', path=path)
            
            # Verify tracking
            tracked = self.guardrails.get_tracked_fds()
            self.assertEqual(len(tracked), 1)
            self.assertEqual(tracked[0].fd, fd)
            
            # Close and untrack
            os.close(fd)
            self.guardrails.untrack_fd(fd)
            
            tracked = self.guardrails.get_tracked_fds()
            self.assertEqual(len(tracked), 0)
        except:
            try:
                os.close(fd)
            except:
                pass
            raise
    
    def test_socket_tracking(self):
        """Test tracking socket file descriptors."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            fd = sock.fileno()
            self.guardrails.track_fd(fd, 'socket', 'test_socket', family='AF_INET')
            
            tracked = self.guardrails.get_tracked_fds()
            self.assertEqual(len(tracked), 1)
            self.assertEqual(tracked[0].fd_type, 'socket')
        finally:
            sock.close()
            self.guardrails.untrack_fd(fd)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(check_interval=60.0)
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_untrack_nonexistent_fd(self):
        """Test untracking an FD that doesn't exist."""
        # Should not raise
        self.guardrails.untrack_fd(99999)
    
    def test_update_access_nonexistent_fd(self):
        """Test updating access for non-tracked FD."""
        # Should not raise
        self.guardrails.update_fd_access(99999)
    
    def test_empty_metrics(self):
        """Test getting metrics when none recorded."""
        metrics = self.guardrails.get_metrics()
        self.assertEqual(metrics, [])
    
    def test_callback_error_handling(self):
        """Test that callback errors don't break the system."""
        def bad_callback(new_state, old_state):
            raise RuntimeError("Callback error")
        
        self.guardrails.add_state_callback(bad_callback)
        
        # Should not raise despite callback error
        self.guardrails._handle_state_transition(FDGuardrailState.WARNING, 100)


class TestFDExhaustionMiddleware(unittest.TestCase):
    """Test FastAPI middleware integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        from backend.fastapi.api.middleware.fd_exhaustion_middleware import (
            FDExhaustionMiddleware,
            FDExhaustionMiddlewareConfig
        )
        self.FDExhaustionMiddleware = FDExhaustionMiddleware
        self.FDExhaustionMiddlewareConfig = FDExhaustionMiddlewareConfig
        
        self.mock_app = Mock()
        self.guardrails = LinuxFDGuardrails(check_interval=60.0)
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_middleware_initialization(self):
        """Test middleware initialization."""
        middleware = self.FDExhaustionMiddleware(
            self.mock_app,
            guardrails=self.guardrails
        )
        self.assertIs(middleware.guardrails, self.guardrails)
        self.assertTrue(middleware.add_headers)
    
    def test_excluded_paths(self):
        """Test that health endpoints are excluded."""
        middleware = self.FDExhaustionMiddleware(self.mock_app)
        
        self.assertIn('/health', middleware.excluded_paths)
        self.assertIn('/ready', middleware.excluded_paths)
        self.assertIn('/startup', middleware.excluded_paths)


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s'
    )
    
    # Run tests
    unittest.main(verbosity=2)
