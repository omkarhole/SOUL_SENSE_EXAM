#!/usr/bin/env python3
"""
Test suite for FD Resource Manager - Epoll Event Loop Exhaustion Prevention #1183

Tests FD tracking, leak detection, resource limits, and event loop monitoring.
"""

import os
import sys
import time
import threading
import asyncio
import tempfile
import unittest
import logging
from unittest.mock import Mock, patch, MagicMock
import socket
import psutil

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utilities.fd_resource_manager import (
    FDResourceManager, FDType, get_fd_manager, init_fd_manager,
    EventLoopMonitor, track_socket_fd, track_file_fd, safe_close_fd
)
from event_loop_health_monitor import (
    EventLoopHealthMonitor, EventLoopState, FastAPIEventLoopMonitor
)

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestFDResourceManager(unittest.TestCase):
    """Test cases for FD resource manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = FDResourceManager(
            max_fds=100,  # Small limit for testing
            warning_threshold=0.7,
            critical_threshold=0.9,
            leak_detection_interval=1.0,  # Fast for testing
            cleanup_interval=2.0
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.manager.shutdown()

    def test_fd_registration(self):
        """Test FD registration and tracking."""
        # Register a test FD
        test_fd = 42
        self.manager.register_fd(test_fd, FDType.SOCKET, "test_component", port=8080)

        # Check if registered
        fd_info = self.manager.get_fd_info()
        self.assertEqual(len(fd_info), 1)
        self.assertEqual(fd_info[0].fd, test_fd)
        self.assertEqual(fd_info[0].type, FDType.SOCKET)
        self.assertEqual(fd_info[0].owner, "test_component")
        self.assertEqual(fd_info[0].metadata['port'], 8080)

    def test_fd_unregistration(self):
        """Test FD unregistration."""
        test_fd = 43
        self.manager.register_fd(test_fd, FDType.FILE, "test_component")

        # Verify registered
        self.assertEqual(len(self.manager.get_fd_info()), 1)

        # Unregister
        self.manager.unregister_fd(test_fd)

        # Verify unregistered
        self.assertEqual(len(self.manager.get_fd_info()), 0)

    def test_fd_tracking_context_manager(self):
        """Test FD tracking context manager."""
        test_fd = 44

        with self.manager.track_fd(test_fd, FDType.PIPE, "test_context"):
            # FD should be tracked
            fd_info = self.manager.get_fd_info()
            self.assertEqual(len(fd_info), 1)
            self.assertEqual(fd_info[0].fd, test_fd)

        # FD should be unregistered after context
        self.assertEqual(len(self.manager.get_fd_info()), 0)

    def test_fd_access_update(self):
        """Test FD access time updates."""
        test_fd = 45
        self.manager.register_fd(test_fd, FDType.SOCKET, "test")

        initial_info = self.manager.get_fd_info()[0]
        initial_access = initial_info.last_accessed

        # Wait a bit
        time.sleep(0.1)

        # Update access
        self.manager.update_fd_access(test_fd)

        updated_info = self.manager.get_fd_info()[0]
        self.assertGreater(updated_info.last_accessed, initial_access)

    def test_fd_usage_limits(self):
        """Test FD usage limit monitoring."""
        # Mock current FD count to simulate high usage
        with patch.object(self.manager, 'get_current_fd_count', return_value=85):  # 85% usage
            warnings_triggered = []

            def warning_callback(fd_count, ratio):
                warnings_triggered.append((fd_count, ratio))

            self.manager.add_warning_callback(warning_callback)

            # Trigger monitoring
            self.manager._check_fd_usage()

            # Should have triggered warning
            self.assertEqual(len(warnings_triggered), 1)
            self.assertEqual(warnings_triggered[0][0], 85)
            self.assertAlmostEqual(warnings_triggered[0][1], 0.85, places=2)

    def test_critical_fd_usage(self):
        """Test critical FD usage alerts."""
        critical_triggered = []

        def critical_callback(fd_count, ratio):
            critical_triggered.append((fd_count, ratio))

        self.manager.add_critical_callback(critical_callback)

        # Mock critical usage
        with patch.object(self.manager, 'get_current_fd_count', return_value=95):  # 95% usage
            self.manager._check_fd_usage()

            self.assertEqual(len(critical_triggered), 1)
            self.assertEqual(critical_triggered[0][0], 95)

    def test_leak_detection(self):
        """Test FD leak detection."""
        leaks_detected = []

        def leak_callback(fd, info):
            leaks_detected.append((fd, info))

        self.manager.add_leak_callback(leak_callback)

        # Register an old FD
        old_fd = 46
        self.manager.register_fd(old_fd, FDType.FILE, "old_component")

        # Simulate old access time
        fd_info = self.manager._tracked_fds[old_fd]
        fd_info.last_accessed = time.time() - 7201  # 2 hours + 1 second ago
        fd_info.created_at = time.time() - 7201

        # Trigger leak check
        self.manager._check_for_leaks()

        # Should detect leak
        self.assertEqual(len(leaks_detected), 1)
        self.assertEqual(leaks_detected[0][0], old_fd)

    def test_force_cleanup(self):
        """Test force cleanup of leaked FDs."""
        # Register some FDs
        for i in range(3):
            self.manager.register_fd(50 + i, FDType.SOCKET, f"test_{i}")

        # Mark them as old
        current_time = time.time()
        for fd, info in self.manager._tracked_fds.items():
            info.created_at = current_time - 7201
            info.last_accessed = current_time - 7201

        # Force cleanup
        cleaned = self.manager.force_cleanup()

        # Should have cleaned up the old FDs
        self.assertGreaterEqual(cleaned, 3)

    def test_stats_tracking(self):
        """Test statistics tracking."""
        # Register some FDs
        for i in range(5):
            self.manager.register_fd(60 + i, FDType.FILE, f"stat_test_{i}")

        stats = self.manager.get_stats()

        self.assertEqual(stats['total_created'], 5)
        self.assertEqual(stats['tracked_fds'], 5)
        self.assertEqual(stats['max_fds'], 100)


class TestEventLoopMonitor(unittest.TestCase):
    """Test cases for event loop monitor."""

    def setUp(self):
        """Set up test fixtures."""
        self.fd_manager = FDResourceManager(max_fds=100)
        self.monitor = EventLoopMonitor(self.fd_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        self.fd_manager.shutdown()

    async def test_loop_lag_measurement(self):
        """Test event loop lag measurement."""
        lag = await self.monitor._measure_loop_lag()
        self.assertGreaterEqual(lag, 0.0)
        self.assertLess(lag, 1.0)  # Should be very small

    async def test_monitoring_loop(self):
        """Test the monitoring loop."""
        # Start monitoring
        loop = asyncio.get_event_loop()
        await self.monitor.start_monitoring(loop)

        # Let it run for a short time
        await asyncio.sleep(0.1)

        # Stop monitoring
        await self.monitor.stop_monitoring()

        # Check that stats were collected
        stats = self.monitor.get_stats()
        self.assertGreaterEqual(stats['total_checks'], 1)


class TestEventLoopHealthMonitor(unittest.TestCase):
    """Test cases for event loop health monitor."""

    def setUp(self):
        """Set up test fixtures."""
        self.fd_manager = FDResourceManager(max_fds=100)
        self.health_monitor = EventLoopHealthMonitor(
            fd_manager=self.fd_manager,
            lag_warning_threshold=0.01,  # Very low for testing
            lag_critical_threshold=0.1,
            fd_warning_threshold=0.7,
            fd_critical_threshold=0.9
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.fd_manager.shutdown()

    async def test_health_check(self):
        """Test health check functionality."""
        await self.health_monitor._check_health()

        # Should have collected metrics
        metrics = self.health_monitor.get_recent_metrics()
        self.assertGreaterEqual(len(metrics), 1)

        # Check metric structure
        metric = metrics[0]
        self.assertIsInstance(metric.lag_time, float)
        self.assertIsInstance(metric.fd_count, int)
        self.assertIsInstance(metric.fd_usage_ratio, float)
        self.assertIsInstance(metric.pending_tasks, int)

    def test_state_determination(self):
        """Test state determination logic."""
        from event_loop_health_monitor import LoopHealthMetrics

        # Test healthy state
        healthy_metrics = LoopHealthMetrics(
            lag_time=0.001,
            fd_count=10,
            fd_usage_ratio=0.1,
            pending_tasks=5,
            timestamp=time.time()
        )
        state = self.health_monitor._determine_state(healthy_metrics)
        self.assertEqual(state, EventLoopState.HEALTHY)

        # Test warning state (high lag)
        warning_metrics = LoopHealthMetrics(
            lag_time=0.05,
            fd_count=10,
            fd_usage_ratio=0.1,
            pending_tasks=5,
            timestamp=time.time()
        )
        state = self.health_monitor._determine_state(warning_metrics)
        self.assertEqual(state, EventLoopState.WARNING)

        # Test critical state (very high FD usage)
        critical_metrics = LoopHealthMetrics(
            lag_time=0.001,
            fd_count=95,
            fd_usage_ratio=0.95,
            pending_tasks=5,
            timestamp=time.time()
        )
        state = self.health_monitor._determine_state(critical_metrics)
        self.assertEqual(state, EventLoopState.CRITICAL)

    async def test_recovery_mechanism(self):
        """Test recovery mechanism."""
        # Put monitor in critical state
        self.health_monitor._current_state = EventLoopState.CRITICAL
        self.health_monitor._consecutive_critical = 3

        # Create mock metrics
        from event_loop_health_monitor import LoopHealthMetrics
        metrics = LoopHealthMetrics(
            lag_time=0.5,
            fd_count=95,
            fd_usage_ratio=0.95,
            pending_tasks=1500,
            timestamp=time.time()
        )

        # Attempt recovery
        await self.health_monitor._attempt_recovery(metrics)

        # Check that recovery was attempted
        stats = self.health_monitor.get_stats()
        self.assertGreaterEqual(stats['recovery_attempts'], 1)


class TestIntegration(unittest.TestCase):
    """Integration tests for FD management system."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        """Clean up integration test fixtures."""
        # Clean up temp files
        try:
            if os.path.exists(self.temp_file):
                os.unlink(self.temp_file)
            os.rmdir(self.temp_dir)
        except:
            pass

    def test_socket_fd_tracking(self):
        """Test tracking of socket FDs."""
        # Create a socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            fd = sock.fileno()

            # Track the socket
            track_socket_fd(sock, "test_socket", port=8080)

            # Verify tracking
            manager = get_fd_manager()
            fd_info = manager.get_fd_info()

            # Find our socket FD
            socket_info = None
            for info in fd_info:
                if info.fd == fd:
                    socket_info = info
                    break

            self.assertIsNotNone(socket_info)
            self.assertEqual(socket_info.type, FDType.SOCKET)
            self.assertEqual(socket_info.owner, "test_socket")
            self.assertEqual(socket_info.metadata['port'], 8080)

        finally:
            sock.close()

    def test_file_fd_tracking(self):
        """Test tracking of file FDs."""
        # Create a test file
        with open(self.temp_file, 'w') as f:
            f.write("test")

        # Open the file and track it
        with open(self.temp_file, 'r') as f:
            track_file_fd(f, "test_file", path=self.temp_file)

            manager = get_fd_manager()
            fd_info = manager.get_fd_info()

            # Find our file FD
            file_info = None
            for info in fd_info:
                if info.owner == "test_file":
                    file_info = info
                    break

            self.assertIsNotNone(file_info)
            self.assertEqual(file_info.type, FDType.FILE)
            self.assertEqual(file_info.metadata['path'], self.temp_file)

    def test_safe_fd_close(self):
        """Test safe FD closing."""
        # Create a pipe for testing
        r, w = os.pipe()

        try:
            # Close read end safely
            result = safe_close_fd(r)
            self.assertTrue(result)

            # Try to close again (should fail gracefully)
            result = safe_close_fd(r)
            self.assertFalse(result)

        finally:
            try:
                os.close(w)
            except:
                pass

    def test_global_manager_access(self):
        """Test global FD manager access."""
        # Get manager
        manager1 = get_fd_manager()
        manager2 = get_fd_manager()

        # Should be the same instance
        self.assertIs(manager1, manager2)

        # Test initialization
        manager3 = init_fd_manager(max_fds=50)
        self.assertIs(manager3, manager1)
        self.assertEqual(manager3.max_fds, 50)


class TestFastAPIIntegration(unittest.TestCase):
    """Test FastAPI integration."""

    def test_fastapi_monitor_creation(self):
        """Test FastAPI monitor creation."""
        monitor = FastAPIEventLoopMonitor()

        # Should create FD manager and health monitor
        self.assertIsNotNone(monitor.fd_manager)
        self.assertIsNotNone(monitor.health_monitor)

    def test_health_status(self):
        """Test health status reporting."""
        monitor = FastAPIEventLoopMonitor()

        # Get health status
        status = monitor.get_health_status()

        # Check structure
        self.assertIn('event_loop_state', status)
        self.assertIn('event_loop_stats', status)
        self.assertIn('fd_stats', status)
        self.assertIn('healthy', status)
        self.assertIn('degraded', status)
        self.assertIn('critical', status)


if __name__ == '__main__':
    # Configure test logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise during tests
        format='%(levelname)s: %(message)s'
    )

    # Run tests
    unittest.main(verbosity=2)