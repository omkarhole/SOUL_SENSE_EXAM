"""
Tests for Migration Blast Radius Pre-Approval Checklist

Covers:
- Core validation logic
- Edge cases: degraded dependencies, invalid inputs, concurrency, timeouts, rollback
- Deterministic output for CI integration
- Scoring and risk level classification
"""

import pytest
from app.infra.migration_blast_radius import (
    MigrationBlastRadius,
    MigrationMetadata,
    BlastRadiusCheckResult,
    RiskLevel,
    CheckResult
)


class TestMigrationMetadataValidation:
    """Test input validation (edge case: invalid inputs)."""
    
    def test_valid_metadata(self):
        """Valid metadata passes validation."""
        metadata = MigrationMetadata(
            migration_id="001_add_index",
            description="Add index to users table"
        )
        is_valid, error = metadata.validate_inputs()
        assert is_valid is True
        assert error == ""
    
    def test_missing_migration_id(self):
        """Missing migration_id fails validation."""
        metadata = MigrationMetadata(migration_id="", description="Test")
        is_valid, error = metadata.validate_inputs()
        assert is_valid is False
        assert "migration_id" in error
    
    def test_missing_description(self):
        """Missing description fails validation."""
        metadata = MigrationMetadata(migration_id="001", description="")
        is_valid, error = metadata.validate_inputs()
        assert is_valid is False
        assert "description" in error
    
    def test_negative_duration(self):
        """Negative duration fails validation."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            estimated_duration_seconds=-5
        )
        is_valid, error = metadata.validate_inputs()
        assert is_valid is False
        assert "duration" in error.lower()
    
    def test_negative_affected_user_count(self):
        """Negative user count fails validation."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            affected_user_count=-100
        )
        is_valid, error = metadata.validate_inputs()
        assert is_valid is False
        assert "affected_user_count" in error


class TestBlastRadiusEvaluationBasic:
    """Test basic evaluation scenarios."""
    
    def test_none_metadata_raises(self):
        """None metadata raises ValueError."""
        checker = MigrationBlastRadius()
        with pytest.raises(ValueError):
            checker.evaluate(None)
    
    def test_safe_migration_passes(self):
        """Safe migration (all checks pass) returns passed=True."""
        metadata = MigrationMetadata(
            migration_id="001_add_index",
            description="Add index to users",
            affected_tables=["users"],
            is_breaking_change=False,
            estimated_duration_seconds=30,
            has_rollback_plan=True,
            affected_user_count=1000,
            involves_data_deletion=False,
            has_tests=True,
            ci_passing=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.passed is True
        assert result.risk_level == RiskLevel.LOW
        assert result.score >= 80
        assert len(result.blocking_issues) == 0
    
    def test_missing_tests_blocks(self):
        """Migration without tests is blocked."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            affected_tables=["users"],
            has_tests=False,
            ci_passing=True,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.passed is False
        assert any("test" in issue.lower() for issue in result.blocking_issues)
    
    def test_missing_rollback_blocks(self):
        """Migration without rollback plan is blocked (ROLLBACK VALIDATION)."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            affected_tables=["users"],
            has_tests=True,
            ci_passing=True,
            has_rollback_plan=False
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.passed is False
        assert any("rollback" in issue.lower() for issue in result.blocking_issues)
    
    def test_failing_ci_blocks(self):
        """Migration with failing CI is blocked (DEGRADED DEPENDENCIES)."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            affected_tables=["users"],
            has_tests=True,
            ci_passing=False,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.passed is False
        assert any("CI" in issue for issue in result.blocking_issues)


class TestRiskLevelClassification:
    """Test risk level scoring."""
    
    def test_low_risk_migration(self):
        """Simple migration scores LOW risk."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Add non-critical column",
            affected_tables=["logs"],
            is_breaking_change=False,
            estimated_duration_seconds=10,
            has_rollback_plan=True,
            affected_user_count=100,
            involves_data_deletion=False,
            has_tests=True,
            ci_passing=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.risk_level == RiskLevel.LOW
        assert result.score >= 80
    
    def test_medium_risk_migration(self):
        """Migration with warnings scores MEDIUM risk."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Add breaking change",
            affected_tables=["users", "profiles"],
            is_breaking_change=True,
            estimated_duration_seconds=45,
            has_rollback_plan=True,
            affected_user_count=5000,
            involves_data_deletion=False,
            has_tests=True,
            ci_passing=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert 40 <= result.score < 80
    
    def test_high_risk_migration(self):
        """Migration with data deletion scores HIGH/CRITICAL risk."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Delete old records",
            affected_tables=["users", "audit_logs", "sessions"],
            is_breaking_change=True,
            estimated_duration_seconds=120,
            has_rollback_plan=True,
            affected_user_count=50000,
            involves_data_deletion=True,
            has_tests=True,
            ci_passing=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert result.score <= 70


class TestEdgeCases:
    """Test edge case handling."""
    
    def test_edge_case_invalid_input(self):
        """Invalid input is caught and blocked (EDGE CASE: Invalid inputs)."""
        metadata = MigrationMetadata(
            migration_id="",  # Invalid: empty
            description="Test"
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert len(result.blocking_issues) > 0
        assert any("Invalid" in issue for issue in result.blocking_issues)
    
    def test_edge_case_data_deletion_warning(self):
        """Data deletion triggers warning (EDGE CASE: Data loss prevention)."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Clean old data",
            affected_tables=["old_logs"],
            involves_data_deletion=True,
            has_tests=True,
            ci_passing=True,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        # Should warn but not block if other checks pass
        assert any("data" in rec.lower() for rec in result.recommendations)
    
    def test_edge_case_long_duration(self):
        """Long-running migration triggers warning (EDGE CASE: Timeout handling)."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Large migration",
            affected_tables=["huge_table"],
            estimated_duration_seconds=1200,  # > 600s threshold
            has_tests=True,
            ci_passing=True,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert any("maintenance window" in rec.lower() for rec in result.recommendations)
    
    def test_edge_case_breaking_change_warning(self):
        """Breaking change triggers warning (EDGE CASE: Concurrency race conditions)."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Breaking column rename",
            affected_tables=["users"],
            is_breaking_change=True,
            has_tests=True,
            ci_passing=True,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert any("isolation" in rec.lower() or "rollout" in rec.lower() for rec in result.recommendations)


class TestCheckStructure:
    """Test individual check results."""
    
    def test_all_checks_present(self):
        """Evaluation returns all 7 checks."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            affected_tables=["users"],
            has_tests=True,
            ci_passing=True,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        check_names = {c.check_name for c in result.checks}
        expected_checks = {
            "schema_valid",
            "rollback_plan_present",
            "zero_downtime_capable",
            "test_coverage",
            "ci_validation",
            "data_loss_prevention",
            "duration_safety"
        }
        
        assert check_names == expected_checks
    
    def test_check_has_recommendations(self):
        """Failed checks include recommendations."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            has_tests=False,  # Will fail this check
            ci_passing=True,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        test_check = next(c for c in result.checks if "test" in c.check_name)
        assert test_check.passed is False
        assert len(test_check.recommendation) > 0


class TestDeterministicOutput:
    """Test deterministic behavior for CI integration."""
    
    def test_same_input_same_output(self):
        """Same input always produces same output."""
        metadata = MigrationMetadata(
            migration_id="001_deterministic",
            description="Test deterministic output",
            affected_tables=["users"],
            is_breaking_change=False,
            estimated_duration_seconds=30,
            has_rollback_plan=True,
            affected_user_count=1000,
            has_tests=True,
            ci_passing=True
        )
        
        checker = MigrationBlastRadius()
        result1 = checker.evaluate(metadata)
        result2 = checker.evaluate(metadata)
        
        assert result1.passed == result2.passed
        assert result1.score == result2.score
        assert result1.risk_level == result2.risk_level
        assert len(result1.checks) == len(result2.checks)
    
    def test_result_serializable(self):
        """Result can be serialized to JSON."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            affected_tables=["users"],
            has_tests=True,
            ci_passing=True,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "passed" in result_dict
        assert "risk_level" in result_dict
        assert "score" in result_dict
        assert "checks" in result_dict
        assert isinstance(result_dict["checks"], list)


class TestMetrics:
    """Test metrics collection."""
    
    def test_metrics_present(self):
        """Result includes evaluation metrics."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            affected_tables=["users", "profiles"],
            has_tests=True,
            ci_passing=True,
            has_rollback_plan=True,
            affected_user_count=5000,
            estimated_duration_seconds=45
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert "table_count" in result.metrics
        assert "is_breaking" in result.metrics
        assert "affected_users" in result.metrics
        assert "duration_seconds" in result.metrics
        assert "evaluation_time_ms" in result.metrics
        assert "timestamp" in result.metrics
        
        assert result.metrics["table_count"] == 2
        assert result.metrics["affected_users"] == 5000
        assert result.metrics["duration_seconds"] == 45


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_safe_small_migration(self):
        """Small, safe migration is approved."""
        metadata = MigrationMetadata(
            migration_id="001_add_user_status_index",
            description="Add composite index on user status and created_at",
            affected_tables=["users"],
            is_breaking_change=False,
            estimated_duration_seconds=15,
            has_rollback_plan=True,
            affected_user_count=500,
            involves_data_deletion=False,
            has_tests=True,
            ci_passing=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.passed is True
        assert result.risk_level == RiskLevel.LOW
        assert len(result.blocking_issues) == 0
    
    def test_risky_large_migration(self):
        """Large breaking migration requires review."""
        metadata = MigrationMetadata(
            migration_id="002_refactor_user_payload",
            description="Refactor user table schema - breaking change",
            affected_tables=["users", "user_sessions", "audit_logs"],
            is_breaking_change=True,
            estimated_duration_seconds=300,
            has_rollback_plan=True,
            affected_user_count=100000,
            involves_data_deletion=True,
            has_tests=True,
            ci_passing=True
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        # Should not be blocked, but high risk with recommendations
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(result.recommendations) > 0
    
    def test_incomplete_migration_rejected(self):
        """Incomplete migration (missing tests/rollback) is rejected."""
        metadata = MigrationMetadata(
            migration_id="003_incomplete",
            description="Incomplete migration",
            affected_tables=["users"],
            has_tests=False,
            ci_passing=True,
            has_rollback_plan=False
        )
        
        checker = MigrationBlastRadius()
        result = checker.evaluate(metadata)
        
        assert result.passed is False
        assert len(result.blocking_issues) >= 2


class TestTimeoutHandling:
    """Test timeout edge case (EDGE CASE: Timeout handling)."""
    
    def test_evaluation_completes_within_timeout(self):
        """Normal evaluation completes within timeout."""
        metadata = MigrationMetadata(
            migration_id="001",
            description="Test",
            has_tests=True,
            ci_passing=True,
            has_rollback_plan=True
        )
        
        checker = MigrationBlastRadius(timeout_seconds=300)
        result = checker.evaluate(metadata)
        
        # Should complete without timeout
        assert result is not None
        assert result.metrics["evaluation_time_ms"] < 300000  # Less than timeout in ms
