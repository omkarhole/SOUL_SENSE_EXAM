#!/usr/bin/env python3
"""
Standalone tests for CPU Affinity Module - Issue #1192

This test file is independent and doesn't require pytest or full project setup.
Run with: python backend/tests/test_cpu_affinity_standalone.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/fastapi'))

from api.utils.cpu_affinity import (
    get_available_cores,
    get_optimal_worker_count,
    bind_process_to_cores,
    get_process_cpu_affinity,
    distribute_workers_across_cores,
    validate_affinity_support,
    get_affinity_report,
    get_cpu_stats,
)


def test_get_available_cores():
    """Test getting available CPU cores."""
    cores = get_available_cores()
    assert cores > 0, "Must have at least 1 CPU core"
    assert isinstance(cores, int), "Core count must be integer"
    print(f"✓ Test 1 PASSED: get_available_cores() = {cores}")


def test_get_optimal_worker_count():
    """Test optimal worker count calculation."""
    cores = get_available_cores()
    optimal = get_optimal_worker_count()
    
    # Should be between 2 and 32
    assert 2 <= optimal <= 32, f"Optimal workers {optimal} out of bounds [2, 32]"
    
    # Should be >= cores
    assert optimal >= cores, f"Optimal {optimal} should be >= cores {cores}"
    
    # Should be <= cores * 2 (approximately 1.5x)
    assert optimal <= cores * 2, f"Optimal {optimal} should be <= {cores * 2}"
    
    print(f"✓ Test 2 PASSED: get_optimal_worker_count() = {optimal} (cores={cores}, formula={cores}×1.5={cores*1.5})")


def test_validate_affinity_support():
    """Test affinity support detection."""
    supported = validate_affinity_support()
    assert isinstance(supported, bool), "Should return boolean"
    print(f"✓ Test 3 PASSED: validate_affinity_support() = {supported}")


def test_get_process_cpu_affinity():
    """Test getting process CPU affinity."""
    affinity = get_process_cpu_affinity()
    
    # Should either return None or a list
    assert affinity is None or isinstance(affinity, (list, tuple)), \
        f"Affinity should be None or list, got {type(affinity)}"
    
    if affinity:
        cores = get_available_cores()
        for core_id in affinity:
            assert 0 <= core_id < cores, f"Core ID {core_id} out of range [0, {cores-1}]"
    
    print(f"✓ Test 4 PASSED: get_process_cpu_affinity() = {affinity}")


def test_distribute_workers_across_cores():
    """Test worker distribution algorithm."""
    cores = get_available_cores()
    
    # Test with different worker counts
    for num_workers in [1, 2, 4, 8, cores, cores * 2]:
        dist = distribute_workers_across_cores(num_workers, cores)
        
        assert len(dist) == num_workers, \
            f"Distribution for {num_workers} workers should have {num_workers} entries"
        
        for i, worker_cores in enumerate(dist):
            assert isinstance(worker_cores, list), f"Worker {i} cores should be list"
            assert len(worker_cores) > 0, f"Worker {i} should have at least 1 core"
            
            for core_id in worker_cores:
                assert 0 <= core_id < cores, \
                    f"Worker {i}, core {core_id} out of range [0, {cores-1}]"
    
    print(f"✓ Test 5 PASSED: distribute_workers_across_cores() works for all worker counts")


def test_affinity_report():
    """Test affinity diagnostic report."""
    report = get_affinity_report()
    
    assert isinstance(report, dict), "Report should be dictionary"
    assert "available_cores" in report, "Report should have available_cores"
    assert "optimal_workers" in report, "Report should have optimal_workers"
    assert "current_process_affinity" in report, "Report should have current_process_affinity"
    assert "affinity_supported" in report, "Report should have affinity_supported"
    
    assert report["available_cores"] > 0, "Available cores should be > 0"
    assert report["optimal_workers"] > 0, "Optimal workers should be > 0"
    assert isinstance(report["affinity_supported"], bool), "Affinity supported should be bool"
    
    print(f"✓ Test 6 PASSED: get_affinity_report() = {report}")


def test_cpu_stats():
    """Test CPU statistics."""
    stats = get_cpu_stats()
    
    assert isinstance(stats, dict), "Stats should be dictionary"
    assert "cpu_count" in stats, "Stats should have cpu_count"
    assert stats["cpu_count"] > 0, "CPU count should be > 0"
    
    print(f"✓ Test 7 PASSED: get_cpu_stats() = {stats}")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("CPU AFFINITY MODULE - COMPREHENSIVE TEST SUITE (Issue #1192)")
    print("="*70 + "\n")
    
    tests = [
        ("Available Cores Detection", test_get_available_cores),
        ("Optimal Worker Count Calculation", test_get_optimal_worker_count),
        ("Affinity Support Detection", test_validate_affinity_support),
        ("Process CPU Affinity", test_get_process_cpu_affinity),
        ("Worker Distribution Algorithm", test_distribute_workers_across_cores),
        ("Affinity Report Generation", test_affinity_report),
        ("CPU Statistics", test_cpu_stats),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ TEST FAILED: {test_name}")
            print(f"  Error: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ TEST ERROR: {test_name}")
            print(f"  Error: {e}\n")
            failed += 1
    
    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
    print("="*70)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED - CPU AFFINITY IMPLEMENTATION VERIFIED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - REVIEW ERRORS ABOVE")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
