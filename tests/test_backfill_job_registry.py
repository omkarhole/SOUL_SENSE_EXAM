"""
Comprehensive tests for Backfill Job Registry.

Tests cover:
- Job creation, tracking, and completion
- Metrics calculation and validation
- Data integrity checks with checksums
- Error handling and failure scenarios
- Registry persistence and loading
- Rollback capability tracking
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, UTC
from app.infra.backfill_job_registry import (
    BackfillRegistry, BackfillJob, BackfillMetrics, BackfillStatus, get_backfill_registry
)


@pytest.fixture
def temp_registry_path(tmp_path):
    """Create a temporary registry path."""
    registry_file = tmp_path / "backfill_registry.json"
    original_path = BackfillRegistry.REGISTRY_PATH
    BackfillRegistry.REGISTRY_PATH = registry_file
    yield registry_file
    BackfillRegistry.REGISTRY_PATH = original_path


@pytest.fixture
def registry(temp_registry_path):
    """Create a fresh backfill registry."""
    return BackfillRegistry()


class TestBackfillJobCreation:
    """Test backfill job creation."""
    
    def test_create_job_success(self, registry):
        """Test creating a new backfill job."""
        job = registry.create_job(
            job_type="age_group_backfill",
            migration_version="20260306_001",
            metadata={"table": "users"}
        )
        
        assert job is not None
        assert job.job_type == "age_group_backfill"
        assert job.migration_version == "20260306_001"
        assert job.status == BackfillStatus.PENDING.value
        assert job.metadata == {"table": "users"}
    
    def test_job_has_unique_id(self, registry):
        """Test that each job gets a unique ID."""
        job1 = registry.create_job("type1", "migration1")
        job2 = registry.create_job("type2", "migration2")
        
        assert job1.backfill_id != job2.backfill_id
    
    def test_job_timestamps_created(self, registry):
        """Test that job has creation timestamp."""
        job = registry.create_job("test_job", "v1")
        
        assert job.created_at is not None
        assert isinstance(job.created_at, str)
        assert datetime.fromisoformat(job.created_at.replace('Z', '+00:00')) is not None


class TestBackfillJobLifecycle:
    """Test backfill job lifecycle management."""
    
    def test_job_lifecycle_complete_success(self, registry):
        """Test complete success lifecycle."""
        job = registry.create_job("test_type", "v1")
        backfill_id = job.backfill_id
        
        # Start job
        registry.start_job(backfill_id)
        job = registry.get_job(backfill_id)
        assert job.status == BackfillStatus.IN_PROGRESS.value
        assert job.started_at is not None
        
        # Update progress
        registry.update_progress(backfill_id, records_processed=100, records_failed=2)
        job = registry.get_job(backfill_id)
        assert job.metrics.records_processed == 100
        assert job.metrics.records_failed == 2
        assert job.metrics.success_rate == 98.0
        
        # Complete job
        registry.complete_job(backfill_id, {
            'execution_time_ms': 2500.5
        })
        job = registry.get_job(backfill_id)
        assert job.status == BackfillStatus.COMPLETED.value
        assert job.completed_at is not None
        assert job.metrics.execution_time_ms == 2500.5
    
    def test_job_failure_tracking(self, registry):
        """Test job failure tracking."""
        job = registry.create_job("test_type", "v1")
        backfill_id = job.backfill_id
        
        registry.start_job(backfill_id)
        registry.fail_job(backfill_id, "Database connection timeout")
        
        job = registry.get_job(backfill_id)
        assert job.status == BackfillStatus.FAILED.value
        assert job.error_details == "Database connection timeout"
        assert job.completed_at is not None
    
    def test_job_not_found(self, registry):
        """Test handling of non-existent job."""
        registry.start_job("nonexistent_id")  # Should not raise
        result = registry.get_job("nonexistent_id")
        assert result is None


class TestMetricsCalculation:
    """Test metrics calculation."""
    
    def test_success_rate_calculation(self, registry):
        """Test success rate percentage calculation."""
        job = registry.create_job("test", "v1")
        
        # 80 success, 20 failed = 80%
        registry.update_progress(job.backfill_id, records_processed=100, records_failed=20)
        job = registry.get_job(job.backfill_id)
        assert job.metrics.success_rate == 80.0
    
    def test_success_rate_100_percent(self, registry):
        """Test 100% success rate."""
        job = registry.create_job("test", "v1")
        registry.update_progress(job.backfill_id, records_processed=50, records_failed=0)
        job = registry.get_job(job.backfill_id)
        assert job.metrics.success_rate == 100.0
    
    def test_success_rate_zero_records(self, registry):
        """Test success rate with zero records."""
        job = registry.create_job("test", "v1")
        registry.update_progress(job.backfill_id, records_processed=0, records_failed=0)
        job = registry.get_job(job.backfill_id)
        assert job.metrics.success_rate == 0.0
    
    def test_metrics_summary_by_migration(self, registry):
        """Test metrics summary aggregation."""
        # Create multiple jobs for same migration
        j1 = registry.create_job("type1", "migration_v1")
        j2 = registry.create_job("type2", "migration_v1")
        j3 = registry.create_job("type3", "migration_v2")  # Different migration
        
        # Update metrics
        registry.update_progress(j1.backfill_id, 100, 10)
        registry.update_progress(j2.backfill_id, 200, 5)
        registry.update_progress(j3.backfill_id, 150, 20)
        
        summary = registry.get_metrics_summary("migration_v1")
        assert summary['job_count'] == 2
        assert summary['total_records_processed'] == 300
        assert summary['total_records_failed'] == 15
        # avg success rate should be (90% + 97.5%) / 2 = 93.75%
        assert abs(summary['overall_success_rate'] - 93.75) < 0.01


class TestDataIntegrity:
    """Test data integrity validation."""
    
    def test_checksum_validation(self, registry):
        """Test checksum validation."""
        job = registry.create_job("test", "v1")
        backfill_id = job.backfill_id
        
        checksum_before = "abc123def456"
        checksum_after = "xyz789uvw012"
        
        is_valid = registry.validate_data_integrity(
            backfill_id, checksum_before, checksum_after
        )
        
        assert is_valid is True
        job = registry.get_job(backfill_id)
        assert job.metrics.checksum_before == checksum_before
        assert job.metrics.checksum_after == checksum_after
    
    def test_checksum_identical_failure(self, registry):
        """Test data integrity failure when checksums are identical."""
        job = registry.create_job("test", "v1")
        checksum = "abc123def456"
        
        is_valid = registry.validate_data_integrity(job.backfill_id, checksum, checksum)
        assert is_valid is False


class TestRollbackCapability:
    """Test rollback capability tracking."""
    
    def test_rollback_capable_by_default(self, registry):
        """Test that jobs are rollback capable by default."""
        job = registry.create_job("test", "v1")
        assert registry.can_rollback(job.backfill_id) is True
    
    def test_rollback_info_generation(self, registry):
        """Test rollback information generation."""
        job = registry.create_job("age_group_backfill", "20260306_001")
        backfill_id = job.backfill_id
        
        registry.validate_data_integrity(backfill_id, "before_hash", "after_hash")
        registry.update_progress(backfill_id, 100, 0)
        
        info = registry.generate_rollback_info(backfill_id)
        
        assert info['backfill_id'] == backfill_id
        assert info['job_type'] == "age_group_backfill"
        assert info['records_affected'] == 100
        assert info['rollback_capable'] is True
    
    def test_rollback_nonexistent_job(self, registry):
        """Test rollback on nonexistent job."""
        assert registry.can_rollback("nonexistent") is False
        assert registry.generate_rollback_info("nonexistent") == {}


class TestRegistryPersistence:
    """Test registry saving and loading."""
    
    def test_registry_saves_to_file(self, registry, temp_registry_path):
        """Test that registry persists to file."""
        job = registry.create_job("type1", "v1")
        
        assert temp_registry_path.exists()
        with open(temp_registry_path) as f:
            data = json.load(f)
            assert job.backfill_id in data
    
    def test_registry_loads_from_file(self, temp_registry_path):
        """Test that registry loads existing data."""
        # Create and save data
        reg1 = BackfillRegistry()
        job = reg1.create_job("type1", "v1")
        backfill_id = job.backfill_id
        reg1.update_progress(backfill_id, 100, 5)
        
        # Load in new registry instance
        reg2 = BackfillRegistry()
        loaded_job = reg2.get_job(backfill_id)
        
        assert loaded_job is not None
        assert loaded_job.job_type == "type1"
        assert loaded_job.metrics.records_processed == 100
        assert loaded_job.metrics.records_failed == 5
    
    def test_empty_registry_creates_file(self, registry, temp_registry_path):
        """Test that creating a job creates registry file."""
        # Registry doesn't create file on init, only on first job
        assert not temp_registry_path.exists()
        
        # Create a job - this triggers file creation
        registry.create_job("type1", "v1")
        assert temp_registry_path.exists()


class TestGetJobsByMigration:
    """Test querying jobs by migration version."""
    
    def test_get_jobs_by_migration_version(self, registry):
        """Test retrieving jobs for a specific migration."""
        j1 = registry.create_job("type1", "migration_a")
        j2 = registry.create_job("type2", "migration_a")
        j3 = registry.create_job("type3", "migration_b")
        
        jobs_a = registry.get_jobs_by_migration("migration_a")
        jobs_b = registry.get_jobs_by_migration("migration_b")
        
        assert len(jobs_a) == 2
        assert len(jobs_b) == 1
        assert j1 in jobs_a and j2 in jobs_a
        assert j3 in jobs_b
    
    def test_get_jobs_nonexistent_migration(self, registry):
        """Test querying nonexistent migration."""
        registry.create_job("type1", "migration_a")
        jobs = registry.get_jobs_by_migration("nonexistent")
        assert jobs == []


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_none_metadata(self, registry):
        """Test job creation without metadata."""
        job = registry.create_job("test", "v1", metadata=None)
        assert job.metadata == {}
    
    def test_update_progress_zero_records(self, registry):
        """Test progress update with zero records."""
        job = registry.create_job("test", "v1")
        registry.update_progress(job.backfill_id, 0, 0)
        job = registry.get_job(job.backfill_id)
        assert job.metrics.records_processed == 0
        assert job.metrics.success_rate == 0.0
    
    def test_multiple_metrics_updates(self, registry):
        """Test multiple progress updates."""
        job = registry.create_job("test", "v1")
        backfill_id = job.backfill_id
        
        registry.update_progress(backfill_id, 50, 2)
        registry.update_progress(backfill_id, 100, 5)  # Updated values
        
        job = registry.get_job(backfill_id)
        assert job.metrics.records_processed == 100
        assert job.metrics.records_failed == 5
    
    def test_job_to_dict_serialization(self, registry):
        """Test job serialization to dictionary."""
        job = registry.create_job("test_type", "v1")
        registry.update_progress(job.backfill_id, 100, 10)
        
        job = registry.get_job(job.backfill_id)
        job_dict = job.to_dict()
        
        assert isinstance(job_dict, dict)
        assert job_dict['job_type'] == "test_type"
        assert job_dict['status'] == BackfillStatus.PENDING.value
        assert job_dict['records_processed'] == 100
        assert job_dict['records_failed'] == 10


class TestConcurrentBackfills:
    """Test handling multiple concurrent backfills."""
    
    def test_multiple_backfills_same_migration(self, registry):
        """Test multiple backfills for the same migration."""
        migration = "20260306_001"
        
        job1 = registry.create_job("backfill_a", migration)
        job2 = registry.create_job("backfill_b", migration)
        job3 = registry.create_job("backfill_c", migration)
        
        registry.start_job(job1.backfill_id)
        registry.start_job(job2.backfill_id)
        registry.complete_job(job3.backfill_id)  # One completes first
        
        jobs = registry.get_jobs_by_migration(migration)
        assert len(jobs) == 3
        
        assert registry.get_job(job1.backfill_id).status == BackfillStatus.IN_PROGRESS.value
        assert registry.get_job(job2.backfill_id).status == BackfillStatus.IN_PROGRESS.value
        assert registry.get_job(job3.backfill_id).status == BackfillStatus.COMPLETED.value


class TestMetricsDataclass:
    """Test BackfillMetrics dataclass."""
    
    def test_metrics_initialization(self):
        """Test metrics default initialization."""
        metrics = BackfillMetrics()
        assert metrics.records_processed == 0
        assert metrics.records_failed == 0
        assert metrics.success_rate == 0.0
        assert metrics.checksum_before == ""
        assert metrics.checksum_after == ""
    
    def test_metrics_custom_values(self):
        """Test metrics with custom values."""
        metrics = BackfillMetrics(
            records_processed=500,
            records_failed=10,
            execution_time_ms=5000.0,
            checksum_before="abc",
            checksum_after="def"
        )
        assert metrics.records_processed == 500
        assert metrics.records_failed == 10
        assert metrics.execution_time_ms == 5000.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
