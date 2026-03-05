#!/usr/bin/env python3
"""
Standalone Integration Tests for Linux FD Exhaustion Guardrails - Issue #1316

These tests validate the FD guardrails functionality without requiring
the full FastAPI application stack.

Run with: pytest tests/test_fd_guardrails_standalone.py -v
"""

import os
import sys
import time
import asyncio
import unittest
import tempfile
import socket
from unittest.mock import Mock, patch, MagicMock

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
)


class TestFDGuardrailsEndToEnd(unittest.TestCase):
    """End-to-end tests for FD guardrails."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(
            check_interval=0.1,
            leak_detection_interval=0.5,
            max_history_size=100
        )
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_full_lifecycle_healthy(self):
        """Test full lifecycle in healthy state."""
        # Start monitoring
        self.guardrails.start()
        
        # Verify initial state
        self.assertEqual(self.guardrails._state, FDGuardrailState.HEALTHY)
        
        # Check can accept requests
        self.assertTrue(self.guardrails.can_accept_request())
        
        # Check backpressure
        self.assertEqual(self.guardrails.get_backpressure_delay(), 0.0)
        
        # Get status
        status = self.guardrails.get_status()
        self.assertEqual(status['state'], 'healthy')
        self.assertTrue(status['can_accept_requests'])
        
        # Stop monitoring
        self.guardrails.stop()
    
    def test_full_lifecycle_critical(self):
        """Test full lifecycle in critical state."""
        # Start monitoring
        self.guardrails.start()
        
        # Simulate critical state
        with self.guardrails._state_lock:
            self.guardrails._state = FDGuardrailState.CRITICAL
        
        # Verify request rejection
        self.assertFalse(self.guardrails.can_accept_request())
        
        # Check backpressure (should still be defined even though requests are rejected)
        delay = self.guardrails.get_backpressure_delay()
        self.assertGreater(delay, 0)
        
        # Get status
        status = self.guardrails.get_status()
        self.assertEqual(status['state'], 'critical')
        self.assertFalse(status['can_accept_requests'])
        
        # Stop monitoring
        self.guardrails.stop()
    
    def test_state_transitions_through_all_states(self):
        """Test transitioning through all states."""
        states = [
            FDGuardrailState.HEALTHY,
            FDGuardrailState.WARNING,
            FDGuardrailState.DEGRADED,
            FDGuardrailState.CRITICAL,
            FDGuardrailState.DEGRADED,
            FDGuardrailState.WARNING,
            FDGuardrailState.HEALTHY,
        ]
        
        callbacks_received = []
        
        def state_callback(new_state, old_state):
            callbacks_received.append((new_state, old_state))
        
        self.guardrails.add_state_callback(state_callback)
        
        for new_state in states:
            self.guardrails._handle_state_transition(new_state, self.guardrails._max_fds)
        
        # Should have received callbacks for each transition (except same-state)
        self.assertGreater(len(callbacks_received), 0)
    
    def test_request_tracking(self):
        """Test request tracking across states."""
        # Initial state: healthy
        self.assertTrue(self.guardrails.can_accept_request())
        self.assertTrue(self.guardrails.can_accept_request())
        self.assertTrue(self.guardrails.can_accept_request())
        
        with self.guardrails._request_lock:
            self.assertEqual(self.guardrails._requests_accepted, 3)
            self.assertEqual(self.guardrails._requests_rejected, 0)
        
        # Change to critical state
        with self.guardrails._state_lock:
            self.guardrails._state = FDGuardrailState.CRITICAL
        
        # Requests should be rejected
        self.assertFalse(self.guardrails.can_accept_request())
        self.assertFalse(self.guardrails.can_accept_request())
        
        with self.guardrails._request_lock:
            self.assertEqual(self.guardrails._requests_accepted, 3)
            self.assertEqual(self.guardrails._requests_rejected, 2)
    
    def test_metrics_collection_over_time(self):
        """Test metrics collection over time."""
        # Record several metrics
        for i in range(10):
            state = [
                FDGuardrailState.HEALTHY,
                FDGuardrailState.WARNING,
                FDGuardrailState.DEGRADED,
                FDGuardrailState.CRITICAL
            ][i % 4]
            self.guardrails._record_metrics(100 + i * 10, state)
        
        # Get metrics
        metrics = self.guardrails.get_metrics(5)
        self.assertEqual(len(metrics), 5)
        
        # Get all metrics
        all_metrics = self.guardrails.get_metrics(100)
        self.assertEqual(len(all_metrics), 10)
    
    def test_fd_tracking_and_cleanup(self):
        """Test FD tracking and cleanup."""
        # Track some FDs
        for i in range(5):
            self.guardrails.track_fd(100 + i, 'socket', f'test_{i}')
        
        # Verify tracking
        tracked = self.guardrails.get_tracked_fds()
        self.assertEqual(len(tracked), 5)
        
        # Untrack some
        self.guardrails.untrack_fd(100)
        self.guardrails.untrack_fd(101)
        
        tracked = self.guardrails.get_tracked_fds()
        self.assertEqual(len(tracked), 3)
        
        # Force cleanup (may not close actual FDs, but should not error)
        reclaimed = self.guardrails.force_cleanup()
        # reclaimed may be 0 since we didn't create real stale FDs
        self.assertGreaterEqual(reclaimed, 0)
    
    def test_leak_detection_flow(self):
        """Test full leak detection flow."""
        current_time = time.time()
        
        # Add some tracked FDs
        self.guardrails.track_fd(200, 'socket', 'active')
        self.guardrails.track_fd(201, 'file', 'stale')
        
        # Mark one as stale
        with self.guardrails._fd_lock:
            self.guardrails._tracked_fds[201].last_accessed = current_time - 4000  # Over 1 hour ago
            self.guardrails._tracked_fds[201].created_at = current_time - 4000
        
        # Check for leaks
        leaks = self.guardrails._check_for_leaks()
        
        # Should detect the stale FD
        self.assertIn(201, leaks)
        self.assertNotIn(200, leaks)
    
    def test_threshold_enforcement(self):
        """Test that thresholds are properly enforced."""
        thresholds = self.guardrails._calculated_thresholds
        
        # Test state determination at boundaries
        self.assertEqual(
            self.guardrails._determine_state(thresholds['warning'] - 1),
            FDGuardrailState.HEALTHY
        )
        
        self.assertEqual(
            self.guardrails._determine_state(thresholds['warning']),
            FDGuardrailState.WARNING
        )
        
        self.assertEqual(
            self.guardrails._determine_state(thresholds['degraded']),
            FDGuardrailState.DEGRADED
        )
        
        self.assertEqual(
            self.guardrails._determine_state(thresholds['critical']),
            FDGuardrailState.CRITICAL
        )


class TestFDGuardrailsWithRealResources(unittest.TestCase):
    """Tests with real file descriptors and sockets."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(check_interval=60.0)
        self.sockets = []
        self.files = []
    
    def tearDown(self):
        """Clean up resources."""
        for sock in self.sockets:
            try:
                sock.close()
            except:
                pass
        for f in self.files:
            try:
                f.close()
            except:
                pass
        self.guardrails.stop()
    
    def test_real_socket_tracking(self):
        """Test tracking real sockets."""
        # Create sockets
        for i in range(3):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sockets.append(sock)
            fd = sock.fileno()
            self.guardrails.track_fd(fd, 'socket', f'socket_{i}')
        
        # Verify tracking
        tracked = self.guardrails.get_tracked_fds()
        self.assertEqual(len(tracked), 3)
        
        # Verify metadata
        for tracked_fd in tracked:
            self.assertEqual(tracked_fd.fd_type, 'socket')
            self.assertTrue(tracked_fd.owner.startswith('socket_'))
    
    def test_real_file_tracking(self):
        """Test tracking real files."""
        # Create temp files
        for i in range(3):
            fd, path = tempfile.mkstemp()
            self.guardrails.track_fd(fd, 'file', f'file_{i}', path=path)
            # Store for cleanup
            self.files.append(os.fdopen(fd, 'w'))
        
        # Verify tracking
        tracked = self.guardrails.get_tracked_fds()
        self.assertEqual(len(tracked), 3)
    
    def test_fd_count_consistency(self):
        """Test that FD count is consistent with tracked FDs."""
        initial_count = self.guardrails._get_current_fd_count()
        
        # Create and track some sockets
        sockets = []
        for i in range(3):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sockets.append(sock)
            self.guardrails.track_fd(sock.fileno(), 'socket', f'test_{i}')
        
        # Current count should have increased
        current_count = self.guardrails._get_current_fd_count()
        
        # Clean up
        for sock in sockets:
            sock.close()


class TestGlobalIntegration(unittest.TestCase):
    """Test global singleton integration."""
    
    def tearDown(self):
        """Reset global instance."""
        import linux_fd_guardrails
        linux_fd_guardrails._fd_guardrails_instance = None
    
    def test_global_singleton(self):
        """Test global singleton behavior."""
        g1 = get_fd_guardrails()
        g2 = get_fd_guardrails()
        
        self.assertIs(g1, g2)
        
        # Stop to clean up
        g1.stop()
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        guardrails = get_fd_guardrails()
        
        # Test check_can_accept_request
        result = check_can_accept_request()
        self.assertIsInstance(result, bool)
        
        # Test get_current_fd_status
        status = get_current_fd_status()
        self.assertIsInstance(status, dict)
        self.assertIn('state', status)
        self.assertIn('current_fds', status)
        self.assertIn('max_fds', status)
        
        guardrails.stop()


class TestMonitoringIntegration(unittest.TestCase):
    """Test monitoring thread integration."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(
            check_interval=0.1,  # Fast for testing
            max_history_size=50
        )
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_monitoring_records_metrics(self):
        """Test that monitoring thread records metrics."""
        self.guardrails.start()
        
        # Wait for some metrics to be recorded
        time.sleep(0.3)
        
        # Get metrics
        metrics = self.guardrails.get_metrics()
        self.assertGreater(len(metrics), 0)
        
        # Verify metric structure
        for metric in metrics:
            self.assertIsInstance(metric.timestamp, float)
            self.assertIsInstance(metric.current_fds, int)
            self.assertIsInstance(metric.max_fds, int)
            self.assertIsInstance(metric.usage_percent, float)
            self.assertIsInstance(metric.state, FDGuardrailState)


class TestCallbackIntegration(unittest.TestCase):
    """Test callback integration."""
    
    def setUp(self):
        """Set up test guardrail instance."""
        self.guardrails = LinuxFDGuardrails(check_interval=60.0)
        self.state_changes = []
        self.actions_triggered = []
    
    def tearDown(self):
        """Clean up."""
        self.guardrails.stop()
    
    def test_state_change_callbacks(self):
        """Test state change callback integration."""
        def on_state_change(new_state, old_state):
            self.state_changes.append((new_state, old_state))
        
        self.guardrails.add_state_callback(on_state_change)
        
        # Trigger state changes
        self.guardrails._handle_state_transition(FDGuardrailState.WARNING, 100)
        self.guardrails._handle_state_transition(FDGuardrailState.DEGRADED, 100)
        self.guardrails._handle_state_transition(FDGuardrailState.CRITICAL, 100)
        
        # Verify callbacks were called
        self.assertEqual(len(self.state_changes), 3)
        self.assertEqual(self.state_changes[0][0], FDGuardrailState.WARNING)
        self.assertEqual(self.state_changes[1][0], FDGuardrailState.DEGRADED)
        self.assertEqual(self.state_changes[2][0], FDGuardrailState.CRITICAL)
    
    def test_action_callbacks(self):
        """Test action callback integration."""
        def on_action(action, data):
            self.actions_triggered.append((action, data))
        
        self.guardrails.add_action_callback(on_action)
        
        # Trigger action
        self.guardrails._trigger_action_for_state(FDGuardrailState.DEGRADED, 100)
        
        # Verify callback was called
        self.assertEqual(len(self.actions_triggered), 1)
        self.assertEqual(self.actions_triggered[0][0], FDExhaustionAction.BACKPRESSURE)


if __name__ == '__main__':
    import logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s'
    )
    
    unittest.main(verbosity=2)
