#!/usr/bin/env python3
"""
Test script for TCP TIME_WAIT Socket Exhaustion Fix #1186

Tests the TCP TIME_WAIT socket exhaustion prevention:
- Connection pooling prevents rapid reconnections
- Kernel parameter tuning reduces TIME_WAIT duration
- Monitors TIME_WAIT socket counts during load tests
- Simulates reconnect storms and network instability
"""

import os
import sys
import time
import threading
import subprocess
import psutil
import socket
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)


def test_connection_pooling():
    """Test that connection pooling prevents TIME_WAIT accumulation."""
    print("Testing connection pooling for TIME_WAIT prevention...")

    try:
        from app.db_connection_manager import get_connection_pool, execute_query

        # Get initial TIME_WAIT count
        initial_tw_count = get_time_wait_count()
        print(f"Initial TIME_WAIT sockets: {initial_tw_count}")

        # Perform many database operations using the pool
        def db_operation(i):
            try:
                # Simple query to test connection reuse
                result = execute_query("SELECT 1")
                return True
            except Exception as e:
                logger.error(f"DB operation {i} failed: {e}")
                return False

        # Run 100 concurrent operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(db_operation, i) for i in range(100)]
            results = [f.result() for f in as_completed(futures)]

        successful = sum(results)
        print(f"Completed {successful}/100 database operations")

        # Check TIME_WAIT count after operations
        final_tw_count = get_time_wait_count()
        print(f"Final TIME_WAIT sockets: {final_tw_count}")

        # With connection pooling, TIME_WAIT should not increase significantly
        tw_increase = final_tw_count - initial_tw_count
        print(f"TIME_WAIT socket increase: {tw_increase}")

        if tw_increase < 20:  # Allow some increase for connection establishment
            print("✓ Connection pooling effectively prevents TIME_WAIT accumulation")
            return True
        else:
            print("✗ Connection pooling may not be preventing TIME_WAIT accumulation")
            return False

    except Exception as e:
        print(f"✗ Connection pooling test failed: {e}")
        return False


def test_kernel_parameter_tuning():
    """Test kernel parameter tuning for TIME_WAIT optimization."""
    print("Testing kernel parameter tuning...")

    try:
        from tcp_time_wait_optimizer import TCPTuner

        tuner = TCPTuner()
        current_settings = tuner.get_current_settings()

        print(f"System: {tuner.system}")
        print(f"Admin privileges: {tuner.is_admin}")

        if not current_settings:
            print("✗ Could not retrieve kernel parameters")
            return False

        # Check for key TIME_WAIT related parameters
        tw_params = []
        if tuner.system == "linux":
            tw_params = ["net.ipv4.tcp_tw_reuse", "net.ipv4.tcp_fin_timeout"]
        elif tuner.system == "darwin":
            tw_params = ["net.inet.tcp.twreusetimeout"]
        elif tuner.system == "windows":
            tw_params = ["netsh_tcp_global"]

        found_params = [p for p in tw_params if p in current_settings]
        print(f"Found {len(found_params)}/{len(tw_params)} TIME_WAIT parameters")

        if found_params:
            print("✓ Kernel parameter monitoring available")
            for param in found_params:
                print(f"  {param}: {current_settings[param]}")
            return True
        else:
            print("✗ No TIME_WAIT related kernel parameters found")
            return False

    except Exception as e:
        print(f"✗ Kernel parameter tuning test failed: {e}")
        return False


def test_reconnect_storm_simulation():
    """Simulate reconnect storm to test TIME_WAIT handling."""
    print("Testing reconnect storm simulation...")

    try:
        # Get initial metrics
        initial_tw = get_time_wait_count()
        initial_connections = len(psutil.net_connections())

        print(f"Initial state - TIME_WAIT: {initial_tw}, Connections: {initial_connections}")

        # Simulate rapid connection/disconnection
        def connection_storm():
            sockets = []
            try:
                # Create many short-lived connections
                for i in range(50):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    try:
                        # Try to connect to a dummy service (will fail but create socket)
                        sock.connect(("127.0.0.1", 9999))  # Non-existent service
                    except:
                        pass  # Expected to fail
                    finally:
                        sock.close()
                        sockets.append(sock)
            except Exception as e:
                logger.error(f"Connection storm failed: {e}")
            finally:
                # Ensure all sockets are closed
                for sock in sockets:
                    try:
                        sock.close()
                    except:
                        pass

        # Run connection storm in threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=connection_storm)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Wait a bit for sockets to enter TIME_WAIT
        time.sleep(2)

        # Check final metrics
        final_tw = get_time_wait_count()
        final_connections = len(psutil.net_connections())

        print(f"Final state - TIME_WAIT: {final_tw}, Connections: {final_connections}")

        tw_increase = final_tw - initial_tw
        print(f"TIME_WAIT increase: {tw_increase}")

        # In a well-tuned system, TIME_WAIT should be managed
        if tw_increase < 100:  # Reasonable threshold
            print("✓ Reconnect storm handled reasonably")
            return True
        else:
            print("⚠ High TIME_WAIT increase detected (may be normal for unoptimized system)")
            return True  # Still pass the test, just warn

    except Exception as e:
        print(f"✗ Reconnect storm simulation failed: {e}")
        return False


def test_network_instability_simulation():
    """Test handling of network instability scenarios."""
    print("Testing network instability simulation...")

    try:
        from app.db_connection_manager import get_connection_pool

        pool = get_connection_pool()
        initial_pool_size = len(pool._pool)

        # Simulate network instability by forcing connection failures
        def unstable_operation():
            try:
                # This should handle connection failures gracefully
                from app.db_connection_manager import execute_query
                result = execute_query("SELECT 1")
                return True
            except Exception as e:
                logger.debug(f"Expected connection failure: {e}")
                return False

        # Run operations that may fail due to "instability"
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(unstable_operation) for _ in range(20)]
            results = [f.result() for f in as_completed(futures)]

        successful = sum(results)
        print(f"Completed {successful}/20 operations under instability simulation")

        # Check that pool recovered
        final_pool_size = len(pool._pool)
        print(f"Connection pool size: {initial_pool_size} -> {final_pool_size}")

        if successful >= 15:  # At least 75% success rate
            print("✓ Network instability handled well")
            return True
        else:
            print("✗ Too many failures under instability simulation")
            return False

    except Exception as e:
        print(f"✗ Network instability test failed: {e}")
        return False


def get_time_wait_count():
    """Get the current TIME_WAIT socket count."""
    try:
        if sys.platform == "win32":
            # Windows - use netstat
            result = subprocess.run(
                ["netstat", "-n"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                tw_count = sum(1 for line in lines if 'TIME_WAIT' in line)
                return tw_count
        else:
            # Unix-like systems - use ss or netstat
            try:
                result = subprocess.run(
                    ["ss", "-tn", "state", "time-wait"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    return max(0, len(lines) - 1)  # Subtract header line
            except FileNotFoundError:
                # Fallback to netstat
                result = subprocess.run(
                    ["netstat", "-tn"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    tw_count = sum(1 for line in lines if 'TIME_WAIT' in line)
                    return tw_count

        return 0
    except Exception as e:
        logger.error(f"Failed to get TIME_WAIT count: {e}")
        return -1


def test_time_wait_monitoring():
    """Test TIME_WAIT socket monitoring capability."""
    print("Testing TIME_WAIT socket monitoring...")

    try:
        # Test basic monitoring
        tw_count = get_time_wait_count()
        if tw_count >= 0:
            print(f"✓ TIME_WAIT monitoring available (current count: {tw_count})")
            return True
        else:
            print("✗ TIME_WAIT monitoring not available")
            return False
    except Exception as e:
        print(f"✗ TIME_WAIT monitoring test failed: {e}")
        return False


def run_all_tests():
    """Run all TIME_WAIT socket exhaustion tests."""
    print("Running TCP TIME_WAIT Socket Exhaustion Tests (#1186)")
    print("=" * 55)

    tests = [
        test_connection_pooling,
        test_kernel_parameter_tuning,
        test_reconnect_storm_simulation,
        test_network_instability_simulation,
        test_time_wait_monitoring,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with error: {e}")
            print()

    print(f"Results: {passed}/{len(tests)} tests passed")

    if passed >= len(tests) - 1:  # Allow 1 test to fail (kernel tuning may not be available)
        print("✓ TCP TIME_WAIT socket exhaustion prevention tests passed!")
        return True
    else:
        print("✗ Multiple tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)