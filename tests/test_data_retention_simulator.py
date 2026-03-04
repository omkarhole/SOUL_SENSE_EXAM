"""
Unit tests for data retention simulator.
"""

import pytest
from app.ml.data_retention_simulator import DataRetentionSimulator, RetentionPolicy


class TestRetentionPolicy:
    """Test RetentionPolicy configuration."""

    def test_policy_defaults(self):
        """Default policy should have reasonable retention."""
        policy = RetentionPolicy()
        assert policy.otp_codes == 7
        assert policy.audit_logs == 1095  # 3 years
        assert policy.users == 36500  # ~100 years

    def test_policy_custom(self):
        """Custom policy should override defaults."""
        policy = RetentionPolicy(otp_codes=1, audit_logs=365)
        assert policy.otp_codes == 1
        assert policy.audit_logs == 365
        assert policy.users == 36500  # Unchanged


class TestStorageCalculation:
    """Test storage impact calculations."""

    def test_current_storage_calculation(self):
        """Current storage should be calculated from row counts."""
        sim = DataRetentionSimulator()
        storage = sim.calculate_storage_impact(RetentionPolicy())
        assert storage["current_gb"] > 0
        assert "projected_gb" in storage
        assert "savings_pct" in storage

    def test_aggressive_policy_reduces_storage(self):
        """Aggressive policy should reduce storage vs default."""
        sim = DataRetentionSimulator()
        default_storage = sim.calculate_storage_impact(RetentionPolicy())
        
        aggressive = RetentionPolicy(
            otp_codes=1,
            audit_logs=180,
            scores=365,
            responses=365,
        )
        aggressive_storage = sim.calculate_storage_impact(aggressive)
        
        assert aggressive_storage["projected_gb"] < default_storage["projected_gb"]
        assert aggressive_storage["savings_pct"] > 0

    def test_no_retention_zero_storage(self):
        """No retention (0 days) should project minimal storage."""
        sim = DataRetentionSimulator()
        policy = RetentionPolicy(
            otp_codes=0,
            audit_logs=0,
            scores=0,
            responses=0,
        )
        storage = sim.calculate_storage_impact(policy)
        # Users kept long-term, so not zero, but significant savings
        assert storage["savings_pct"] > 50


class TestPerformanceImpact:
    """Test performance impact calculations."""

    def test_performance_impact_structure(self):
        """Performance impact should return all required fields."""
        sim = DataRetentionSimulator()
        perf = sim.calculate_performance_impact(RetentionPolicy())
        
        assert "query_slowdown_pct" in perf
        assert "cleanup_time_hours" in perf
        assert "index_fragmentation" in perf
        assert perf["query_slowdown_pct"] >= 0
        assert perf["cleanup_time_hours"] >= 0

    def test_aggressive_cleanup_high_slowdown(self):
        """Aggressive cleanup should show more slowdown."""
        sim = DataRetentionSimulator()
        aggressive = RetentionPolicy(
            otp_codes=0,
            audit_logs=1,
            scores=30,
            responses=30,
        )
        perf = sim.calculate_performance_impact(aggressive)
        assert perf["query_slowdown_pct"] > 5  # Should be noticeable

    def test_fragmentation_levels(self):
        """Fragmentation should scale with deletion ratio."""
        sim = DataRetentionSimulator()
        
        # Low deletion
        low_del = RetentionPolicy(audit_logs=730, scores=1825, responses=1825)
        perf_low = sim.calculate_performance_impact(low_del)
        assert perf_low["index_fragmentation"] in ["low", "moderate"]
        
        # High deletion
        high_del = RetentionPolicy(audit_logs=1, scores=30, responses=30)
        perf_high = sim.calculate_performance_impact(high_del)
        assert perf_high["index_fragmentation"] in ["moderate", "high"]


class TestComplianceImpact:
    """Test compliance scoring."""

    def test_high_compliance_score(self):
        """Default policy should have good compliance."""
        sim = DataRetentionSimulator()
        comp = sim.calculate_compliance_impact(RetentionPolicy())
        assert comp["score"] >= 70
        assert len(comp["violations"]) == 0 or len(comp["violations"]) < 3

    def test_gdpr_violation(self):
        """Audit logs < 1 year should trigger violation."""
        sim = DataRetentionSimulator()
        policy = RetentionPolicy(audit_logs=180)  # Only 6 months
        comp = sim.calculate_compliance_impact(policy)
        
        assert "GDPR" in str(comp["violations"])
        assert comp["score"] < 100

    def test_compliance_recommendations(self):
        """Should provide actionable recommendations."""
        sim = DataRetentionSimulator()
        aggressive = RetentionPolicy(
            otp_codes=100,  # High for transient
            audit_logs=365,  # Low for compliance
        )
        comp = sim.calculate_compliance_impact(aggressive)
        assert len(comp["recommendations"]) > 0


class TestRecommendedPolicy:
    """Test policy recommendation."""

    def test_recommend_default(self):
        """Default recommendation should be provided."""
        sim = DataRetentionSimulator()
        policy, rationale = sim.recommend_policy()
        
        assert isinstance(policy, RetentionPolicy)
        assert "storage" in rationale
        assert "policy_name" in rationale

    def test_recommend_compliance_strict(self):
        """Strict compliance should enforce 3yr audit logs."""
        sim = DataRetentionSimulator()
        policy, _ = sim.recommend_policy(compliance_strict=True)
        
        assert policy.audit_logs == 1095  # 3 years

    def test_recommend_storage_constraint(self):
        """Should recommend aggressive policy if storage limited."""
        sim = DataRetentionSimulator()
        policy, _ = sim.recommend_policy(max_storage_gb=1)  # Very tight budget
        
        # Should recommend aggressive cleanup
        storage = sim.calculate_storage_impact(policy)
        assert storage["savings_pct"] > 40


class TestCleanupSimulation:
    """Test cleanup dry-run simulation."""

    def test_cleanup_structure(self):
        """Cleanup should return required fields."""
        sim = DataRetentionSimulator()
        cleanup = sim.simulate_cleanup(RetentionPolicy())
        
        assert "rows_deleted" in cleanup
        assert "storage_freed_gb" in cleanup
        assert "cleanup_time_hours" in cleanup
        assert "warnings" in cleanup
        assert isinstance(cleanup["warnings"], list)

    def test_aggressive_cleanup_warnings(self):
        """Large cleanup should generate warnings."""
        sim = DataRetentionSimulator()
        aggressive = RetentionPolicy(
            otp_codes=0,
            audit_logs=1,
            scores=30,
            responses=30,
        )
        cleanup = sim.simulate_cleanup(aggressive)
        
        assert len(cleanup["warnings"]) > 0

    def test_no_warnings_conservative(self):
        """Conservative policy should have minimal warnings."""
        sim = DataRetentionSimulator()
        policy = RetentionPolicy()  # Defaults
        cleanup = sim.simulate_cleanup(policy, risk_assessment=True)
        
        # May still have cascade warning, but not size warning
        assert cleanup["rows_deleted"] < 5000000


class TestDeterminism:
    """Test that outputs are deterministic."""

    def test_same_input_same_output(self):
        """Same input should produce same output."""
        policy = RetentionPolicy(audit_logs=730)
        
        sim1 = DataRetentionSimulator()
        storage1 = sim1.calculate_storage_impact(policy)
        perf1 = sim1.calculate_performance_impact(policy)
        
        sim2 = DataRetentionSimulator()
        storage2 = sim2.calculate_storage_impact(policy)
        perf2 = sim2.calculate_performance_impact(policy)
        
        assert storage1 == storage2
        assert perf1 == perf2

    def test_custom_row_counts_deterministic(self):
        """Custom row counts should deterministically affect output."""
        policy = RetentionPolicy()
        row_counts_a = {"audit_logs": 100000, "scores": 500000, "users": 10000}
        row_counts_b = {"audit_logs": 100000, "scores": 500000, "users": 10000}
        
        sim_a = DataRetentionSimulator(row_counts_a)
        sim_b = DataRetentionSimulator(row_counts_b)
        
        assert sim_a.calculate_storage_impact(policy) == sim_b.calculate_storage_impact(policy)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_rows(self):
        """Zero rows should handle gracefully."""
        sim = DataRetentionSimulator({table: 0 for table in {
            "otp_codes", "user_sessions", "audit_logs", "scores", "users"
        }})
        storage = sim.calculate_storage_impact(RetentionPolicy())
        assert storage["current_gb"] == 0.0

    def test_very_high_retention(self):
        """Very high retention (infinite) should keep all data."""
        sim = DataRetentionSimulator()
        policy = RetentionPolicy(audit_logs=36500, scores=36500)
        storage = sim.calculate_storage_impact(policy)
        assert storage["savings_pct"] == 0.0

    def test_custom_row_counts_empty(self):
        """Empty row counts should still calculate."""
        sim = DataRetentionSimulator({})
        storage = sim.calculate_storage_impact(RetentionPolicy())
        # May have errors or defaults, but should not crash
        assert isinstance(storage, dict)


class TestIntegration:
    """Integration tests across multiple methods."""

    def test_workflow_analyze_recommend_cleanup(self):
        """Full workflow: analyze -> recommend -> simulate cleanup."""
        sim = DataRetentionSimulator()
        
        # 1. Analyze current state
        current_policy = RetentionPolicy()
        storage = sim.calculate_storage_impact(current_policy)
        assert storage["current_gb"] > 0
        
        # 2. Get recommendation
        recommended_policy, rationale = sim.recommend_policy(
            max_storage_gb=int(storage["current_gb"] * 0.5),
            compliance_strict=True
        )
        
        # 3. Simulate cleanup
        cleanup = sim.simulate_cleanup(recommended_policy)
        assert cleanup["storage_freed_gb"] > 0
