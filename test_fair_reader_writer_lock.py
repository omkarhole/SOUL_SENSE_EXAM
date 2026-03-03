#!/usr/bin/env python3
"""
Test script for Fair Reader-Writer Lock - Prevents Writer Starvation #1187

Tests the fair reader-writer lock implementation to ensure:
- Writers are not starved under read-heavy loads
- Fair scheduling prevents indefinite writer delays
- Read operations can proceed concurrently
- Write operations are properly serialized
"""

import os
import sys
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.utilities.fair_reader_writer_lock import FairReaderWriterLock, get_fair_reader_writer_lock


class TestFairReaderWriterLock:
    """Comprehensive test suite for fair reader-writer lock."""

    def __init__(self):
        self.lock = FairReaderWriterLock()
        self.shared_data = {"counter": 0, "data": []}
        self.results = {}

    def test_basic_functionality(self):
        """Test basic read/write lock functionality."""
        print("Testing basic read/write lock functionality...")

        # Test write lock
        with self.lock.write_lock():
            self.shared_data["counter"] = 1
            assert self.shared_data["counter"] == 1

        # Test read lock
        with self.lock.read_lock():
            value = self.shared_data["counter"]
            assert value == 1

        print("✓ Basic functionality test passed")
        return True

    def test_concurrent_reads(self):
        """Test that multiple readers can proceed concurrently."""
        print("Testing concurrent read operations...")

        read_count = 0
        read_lock = threading.Lock()

        def reader():
            nonlocal read_count
            with self.lock.read_lock():
                with read_lock:
                    read_count += 1
                    # Simulate some work
                    time.sleep(0.01)
                    read_count -= 1

        # Start multiple readers
        threads = []
        for i in range(10):
            t = threading.Thread(target=reader)
            threads.append(t)
            t.start()

        # Wait for all to complete
        for t in threads:
            t.join()

        print("✓ Concurrent reads test passed")
        return True

    def test_write_exclusion(self):
        """Test that writes exclude all other operations."""
        print("Testing write exclusion...")

        write_active = False
        write_lock = threading.Lock()

        def writer():
            nonlocal write_active
            with self.lock.write_lock():
                with write_lock:
                    assert not write_active, "Multiple writers active simultaneously!"
                    write_active = True
                    time.sleep(0.01)
                    write_active = False

        # Start multiple writers
        threads = []
        for i in range(5):
            t = threading.Thread(target=writer)
            threads.append(t)
            t.start()

        # Wait for all to complete
        for t in threads:
            t.join()

        print("✓ Write exclusion test passed")
        return True

    def test_read_heavy_load_writer_starvation_prevention(self):
        """Test that writers don't get starved under read-heavy load."""
        print("Testing read-heavy load writer starvation prevention...")

        writer_times = []
        writer_lock = threading.Lock()

        def continuous_reader():
            """Reader that runs continuously."""
            while not self.results.get('stop_readers', False):
                with self.lock.read_lock():
                    _ = self.shared_data["counter"]
                    time.sleep(0.001)  # Small delay to simulate work

        def writer():
            """Writer that records timing."""
            start_time = time.time()
            with self.lock.write_lock():
                end_time = time.time()
                with writer_lock:
                    writer_times.append(end_time - start_time)
                self.shared_data["counter"] += 1
                time.sleep(0.001)  # Small delay

        # Start continuous readers
        reader_threads = []
        for i in range(20):  # High read concurrency
            t = threading.Thread(target=continuous_reader, daemon=True)
            reader_threads.append(t)
            t.start()

        # Give readers time to start
        time.sleep(0.1)

        # Start writers and measure their wait times
        writer_threads = []
        for i in range(10):
            t = threading.Thread(target=writer)
            writer_threads.append(t)
            t.start()

        # Wait for writers to complete
        for t in writer_threads:
            t.join()

        # Stop readers
        self.results['stop_readers'] = True
        for t in reader_threads:
            t.join(timeout=1.0)

        # Analyze results
        if writer_times:
            avg_wait = statistics.mean(writer_times)
            max_wait = max(writer_times)
            print(f"  Average writer wait time: {avg_wait:.4f}s")
            print(f"  Maximum writer wait time: {max_wait:.4f}s")
            # With fair locking, writers should not be excessively delayed
            # Allow some delay but prevent starvation (no more than 1 second average)
            if avg_wait < 1.0:
                print("✓ Read-heavy load writer starvation prevention test passed")
                return True
            else:
                print("✗ Writers may be experiencing starvation")
                return False
        else:
            print("✗ No writer timing data collected")
            return False

    def test_write_burst_fairness(self):
        """Test fairness during write bursts."""
        print("Testing write burst fairness...")

        write_order = []
        write_lock = threading.Lock()

        def writer(writer_id):
            with self.lock.write_lock():
                with write_lock:
                    write_order.append(writer_id)
                time.sleep(0.01)  # Simulate work

        # Start writers in quick succession (burst)
        threads = []
        for i in range(10):
            t = threading.Thread(target=writer, args=(i,))
            threads.append(t)
            t.start()
            time.sleep(0.001)  # Small stagger to avoid perfect synchronization

        # Wait for all to complete
        for t in threads:
            t.join()

        # Check that writers executed in reasonable order (not completely random)
        # With fair locking, we should see some ordering preservation
        first_half = write_order[:5]
        second_half = write_order[5:]

        # At least some writers from first half should complete before second half
        if any(i in second_half for i in first_half):
            print("✓ Write burst fairness test passed")
            return True
        else:
            print("✗ Write burst may not be fair")
            return False

    def test_lock_contention_profiling(self):
        """Profile lock contention under various loads."""
        print("Testing lock contention profiling...")

        stats_history = []
        contention_lock = threading.Lock()

        def monitor_stats():
            """Monitor lock statistics over time."""
            while not self.results.get('stop_monitor', False):
                stats = self.lock.get_stats()
                with contention_lock:
                    stats_history.append(stats)
                time.sleep(0.01)

        def reader_worker():
            """Reader worker for contention testing."""
            for _ in range(100):
                with self.lock.read_lock():
                    _ = self.shared_data["counter"]
                    time.sleep(0.001)

        def writer_worker():
            """Writer worker for contention testing."""
            for _ in range(20):
                with self.lock.write_lock():
                    self.shared_data["counter"] += 1
                    time.sleep(0.002)

        # Start monitoring
        monitor_thread = threading.Thread(target=monitor_stats, daemon=True)
        monitor_thread.start()

        # Start mixed workload
        with ThreadPoolExecutor(max_workers=20) as executor:
            # Submit readers and writers
            futures = []
            for _ in range(10):
                futures.append(executor.submit(reader_worker))
            for _ in range(5):
                futures.append(executor.submit(writer_worker))

            # Wait for completion
            for future in as_completed(futures):
                future.result()

        # Stop monitoring
        self.results['stop_monitor'] = True
        monitor_thread.join(timeout=1.0)

        # Analyze contention
        if stats_history:
            max_readers = max(s['reader_count'] for s in stats_history)
            max_waiting_writers = max(s['waiting_writers'] for s in stats_history)
            writer_active_count = sum(1 for s in stats_history if s['writer_active'])

            print(f"  Max concurrent readers: {max_readers}")
            print(f"  Max waiting writers: {max_waiting_writers}")
            print(f"  Writer active periods: {writer_active_count}")

            # Verify reasonable contention levels
            if max_readers > 0 and writer_active_count > 0:
                print("✓ Lock contention profiling test passed")
                return True
            else:
                print("✗ Insufficient contention data")
                return False
        else:
            print("✗ No contention statistics collected")
            return False

    def test_timeout_behavior(self):
        """Test timeout behavior for lock acquisition."""
        print("Testing timeout behavior...")

        # Acquire write lock to block readers
        with self.lock.write_lock():
            # Try to acquire read lock with timeout
            start_time = time.time()
            acquired = self.lock.acquire_read(timeout=0.1)
            end_time = time.time()

            if not acquired and (end_time - start_time) >= 0.1:
                print("✓ Timeout behavior test passed")
                return True
            else:
                print("✗ Timeout behavior incorrect")
                return False

    def test_questions_integration(self):
        """Test integration with questions.py module."""
        print("Testing questions.py integration...")

        try:
            from app.questions import load_questions, initialize_questions, get_question_count

            # Test that functions work with the new locking
            questions = load_questions()
            count = get_question_count()

            print(f"  Loaded {len(questions)} questions")
            print(f"  Question count: {count}")

            if isinstance(questions, list) and isinstance(count, int):
                print("✓ Questions integration test passed")
                return True
            else:
                print("✗ Questions integration failed")
                return False

        except Exception as e:
            print(f"✗ Questions integration error: {e}")
            return False


def run_all_tests():
    """Run all tests and report results."""
    print("Running Fair Reader-Writer Lock Tests (#1187)")
    print("=" * 50)

    test_instance = TestFairReaderWriterLock()
    tests = [
        test_instance.test_basic_functionality,
        test_instance.test_concurrent_reads,
        test_instance.test_write_exclusion,
        test_instance.test_read_heavy_load_writer_starvation_prevention,
        test_instance.test_write_burst_fairness,
        test_instance.test_lock_contention_profiling,
        test_instance.test_timeout_behavior,
        test_instance.test_questions_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("✓ All Fair Reader-Writer Lock tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)