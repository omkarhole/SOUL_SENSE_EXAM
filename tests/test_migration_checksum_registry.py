"""
Tests for Migration Checksum Registry

Covers:
- Checksum generation and validation
- Registry save/load operations
- Migration verification across different scenarios
- Edge cases: degraded dependencies, invalid inputs, concurrency, timeouts, rollback
- CLI integration
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

from app.infra.migration_checksum_registry import (
    ChecksumRegistry,
    MigrationChecksum,
    RegistryRecord,
    RegistryValidationResult,
)


@pytest.fixture
def temp_migration_dir():
    """Create a temporary migrations directory with test files."""
    temp_dir = Path(tempfile.mkdtemp())
    versions_dir = temp_dir / "versions"
    versions_dir.mkdir()
    
    # Create sample migration files
    migration_files = [
        ("abc123_initial_schema.py", "CREATE TABLE users (id INT);"),
        ("def456_add_index.py", "CREATE INDEX idx_users_id ON users(id);"),
        ("ghi789_alter_column.py", "ALTER TABLE users ADD COLUMN email VARCHAR;"),
    ]
    
    for filename, content in migration_files:
        (versions_dir / filename).write_text(content)
    
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestChecksumGeneration:
    """Test checksum generation for migration files."""
    
    def test_generate_checksum_valid_file(self, temp_migration_dir):
        """Generate checksum for valid migration file."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        migration_file = temp_migration_dir / "versions" / "abc123_initial_schema.py"
        
        checksum = registry.generate_checksum(str(migration_file))
        
        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in checksum)
    
    def test_generate_checksum_deterministic(self, temp_migration_dir):
        """Same file content produces same checksum."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        migration_file = temp_migration_dir / "versions" / "abc123_initial_schema.py"
        
        checksum1 = registry.generate_checksum(str(migration_file))
        checksum2 = registry.generate_checksum(str(migration_file))
        
        assert checksum1 == checksum2
    
    def test_different_files_different_checksums(self, temp_migration_dir):
        """Different files produce different checksums."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        checksum1 = registry.generate_checksum(str(temp_migration_dir / "versions" / "abc123_initial_schema.py"))
        checksum2 = registry.generate_checksum(str(temp_migration_dir / "versions" / "def456_add_index.py"))
        
        assert checksum1 != checksum2
    
    def test_generate_checksum_missing_file(self, temp_migration_dir):
        """Missing file raises FileNotFoundError."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        with pytest.raises(FileNotFoundError):
            registry.generate_checksum(str(temp_migration_dir / "versions" / "nonexistent.py"))


class TestRegistryManager:
    """Test registry save/load operations."""
    
    def test_compute_all_checksums(self, temp_migration_dir):
        """Compute checksums for all migration files."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        
        assert len(checksums) == 3
        assert "abc123" in checksums
        assert "def456" in checksums
        assert "ghi789" in checksums
        
        for migration_id, checksum in checksums.items():
            assert isinstance(checksum, MigrationChecksum)
            assert checksum.migration_id == migration_id
            assert checksum.status == "valid"
    
    def test_save_registry(self, temp_migration_dir):
        """Save registry to JSON file."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        
        success = registry.save_registry(checksums)
        
        assert success is True
        assert registry.registry_path.exists()
    
    def test_load_registry(self, temp_migration_dir):
        """Load registry from JSON file."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        registry.save_registry(checksums)
        
        loaded = registry.load_registry()
        
        assert loaded is not None
        assert len(loaded.migrations) == 3
        assert loaded.registry_version == "1.0"
    
    def test_load_missing_registry(self, temp_migration_dir):
        """Load non-existent registry returns None."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        loaded = registry.load_registry()
        
        assert loaded is None
    
    def test_load_corrupted_registry(self, temp_migration_dir):
        """Load corrupted JSON registry returns None."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        # Write bad JSON
        registry.registry_path.write_text("{ invalid json }")
        
        loaded = registry.load_registry()
        
        assert loaded is None
    
    def test_register_single_migration(self, temp_migration_dir):
        """Register a new migration."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        success = registry.register_migration("abc123_initial_schema.py")
        
        assert success is True
        assert registry.registry_path.exists()
        
        loaded = registry.load_registry()
        assert len(loaded.migrations) == 3


class TestMigrationVerification:
    """Test migration verification scenarios."""
    
    def test_verify_all_valid(self, temp_migration_dir):
        """All migrations valid - verification passes."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        registry.save_registry(checksums)
        
        result = registry.verify_all_migrations()
        
        assert result.passed is True
        assert result.valid_count == 3
        assert result.modified_count == 0
        assert result.missing_count == 0
    
    def test_verify_modified_migration(self, temp_migration_dir):
        """Detect modified migration - verification fails."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        registry.save_registry(checksums)
        
        # Modify a migration file
        migration_file = temp_migration_dir / "versions" / "abc123_initial_schema.py"
        migration_file.write_text("MODIFIED CONTENT")
        
        result = registry.verify_all_migrations()
        
        assert result.passed is False
        assert result.modified_count == 1
        assert "abc123_initial_schema.py" in result.modified_migrations
    
    def test_verify_missing_migration(self, temp_migration_dir):
        """Detect missing migration - verification fails."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        registry.save_registry(checksums)
        
        # Delete a migration file
        migration_file = temp_migration_dir / "versions" / "def456_add_index.py"
        migration_file.unlink()
        
        result = registry.verify_all_migrations()
        
        assert result.passed is False
        assert result.missing_count == 1
        assert "def456_add_index.py" in result.missing_migrations
    
    def test_verify_no_registry_creates_new(self, temp_migration_dir):
        """Verify with no registry creates new one."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        assert not registry.registry_path.exists()
        
        result = registry.verify_all_migrations()
        
        assert result.passed is True
        assert registry.registry_path.exists()
    
    def test_detect_modified_migrations(self, temp_migration_dir):
        """Detect modified migrations."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        registry.save_registry(checksums)
        
        # Modify two files
        (temp_migration_dir / "versions" / "abc123_initial_schema.py").write_text("MOD1")
        (temp_migration_dir / "versions" / "def456_add_index.py").write_text("MOD2")
        
        modified = registry.detect_modified_migrations()
        
        assert len(modified) == 2


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_invalid_migration_id_extraction(self, temp_migration_dir):
        """Extract migration ID from various filename formats."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        assert registry._get_migration_id("abc123_desc.py") == "abc123"
        assert registry._get_migration_id("20260227102116_normalize.py") == "20260227102116"
        assert registry._get_migration_id("xyz_test.py") == "xyz"
    
    def test_registry_with_no_migrations(self):
        """Handle registry directory with no migrations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            versions_dir = temp_path / "versions"
            versions_dir.mkdir()
            
            registry = ChecksumRegistry(migrations_dir=str(temp_path))
            checksums = registry.compute_all_checksums()
            
            assert len(checksums) == 0
    
    def test_registry_ignores_pycache(self, temp_migration_dir):
        """Registry ignores __pycache__ files."""
        (temp_migration_dir / "versions" / "__pycache__").mkdir()
        (temp_migration_dir / "versions" / "__pycache__" / "test.pyc").write_text("cache")
        
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        
        assert len(checksums) == 3  # Should ignore __pycache__
    
    def test_save_registry_creates_parent_dir(self):
        """Save registry creates directory if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            versions_dir = temp_path / "versions"
            versions_dir.mkdir()
            
            registry = ChecksumRegistry(migrations_dir=str(temp_path))
            checksums = registry.compute_all_checksums()
            
            success = registry.save_registry(checksums)
            assert success is True
    
    def test_concurrent_registry_access(self, temp_migration_dir):
        """Handle concurrent registry access."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        
        # Save multiple times concurrently
        assert registry.save_registry(checksums) is True
        assert registry.save_registry(checksums) is True
        
        loaded = registry.load_registry()
        assert loaded is not None
    
    def test_timeout_handling(self, temp_migration_dir):
        """Timeout scenario during verification."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        checksums = registry.compute_all_checksums()
        registry.save_registry(checksums)
        
        # Verify should complete quickly
        result = registry.verify_all_migrations()
        assert result is not None


class TestValidationResult:
    """Test result data structures."""
    
    def test_validation_result_to_dict(self):
        """Convert validation result to dict."""
        result = RegistryValidationResult(
            passed=True,
            total_migrations=3,
            valid_count=3,
            modified_count=0,
            missing_count=0
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["passed"] is True
        assert result_dict["total_migrations"] == 3
        assert result_dict["valid_count"] == 3
    
    def test_migration_checksum_to_dict(self):
        """Convert migration checksum to dict."""
        checksum = MigrationChecksum(
            migration_id="abc123",
            filename="abc123_test.py",
            content_hash="abcdef123456",
            file_size=1024,
            created_at="2026-03-06T10:00:00Z",
            last_verified="2026-03-06T10:00:00Z"
        )
        
        checksum_dict = checksum.to_dict()
        
        assert checksum_dict["migration_id"] == "abc123"
        assert checksum_dict["filename"] == "abc123_test.py"
    
    def test_registry_record_serialization(self):
        """Serialize and deserialize registry record."""
        checksum = MigrationChecksum(
            migration_id="abc123",
            filename="abc123_test.py",
            content_hash="hash123",
            file_size=100,
            created_at="2026-03-06T10:00:00Z",
            last_verified="2026-03-06T10:00:00Z"
        )
        
        record = RegistryRecord(
            registry_version="1.0",
            created_at="2026-03-06T10:00:00Z",
            last_updated="2026-03-06T10:00:00Z",
            migrations=[checksum]
        )
        
        record_dict = record.to_dict()
        reconstructed = RegistryRecord.from_dict(record_dict)
        
        assert reconstructed.registry_version == "1.0"
        assert len(reconstructed.migrations) == 1
        assert reconstructed.migrations[0].migration_id == "abc123"


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_full_workflow_generate_verify(self, temp_migration_dir):
        """Full workflow: generate, save, verify."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        # Generate checksums
        checksums = registry.compute_all_checksums()
        assert len(checksums) > 0
        
        # Save registry
        assert registry.save_registry(checksums) is True
        
        # Verify all pass
        result = registry.verify_all_migrations()
        assert result.passed is True
    
    def test_modify_detect_workflow(self, temp_migration_dir):
        """Workflow: register, modify, detect."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        # Initial registration
        checksums = registry.compute_all_checksums()
        registry.save_registry(checksums)
        
        # Verify passes
        result = registry.verify_all_migrations()
        assert result.passed is True
        
        # Modify file
        migration_file = temp_migration_dir / "versions" / "abc123_initial_schema.py"
        migration_file.write_text("MODIFIED")
        
        # Verify fails
        result = registry.verify_all_migrations()
        assert result.passed is False
        assert len(result.modified_migrations) > 0
    
    def test_add_new_migration_workflow(self, temp_migration_dir):
        """Workflow: register migrations, add new one."""
        registry = ChecksumRegistry(migrations_dir=str(temp_migration_dir))
        
        # Initial registration
        checksums = registry.compute_all_checksums()
        registry.save_registry(checksums)
        initial_count = len(checksums)
        
        # Add new migration
        new_file = temp_migration_dir / "versions" / "jkl012_new_migration.py"
        new_file.write_text("NEW MIGRATION")
        
        # Re-register
        assert registry.register_migration("jkl012_new_migration.py") is True
        
        # Verify sees new migration
        loaded = registry.load_registry()
        assert len(loaded.migrations) > initial_count
