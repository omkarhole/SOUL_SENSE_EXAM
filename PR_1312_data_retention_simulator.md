```markdown
# PR: Data retention impact simulator (#1312)

**Summary**

Adds a deterministic, testable data retention impact simulator for feasibility analysis of data lifecycle policies. Enables reproducible predictions of storage/performance impact and compliance gaps.

**Motivation**

- Predict storage and performance impact of retention policies before deployment
- Enable CI to validate retention decisions and detect regressions
- Support compliance requirements (GDPR, audit retention, PII handling)

**What this PR changes**

- `app/ml/data_retention_simulator.py`: `DataRetentionSimulator` class with 5 core methods
- `tests/test_data_retention_simulator.py`: 30+ unit tests covering all scenarios
- Includes `RetentionPolicy` dataclass for configurable retention days per table

**Core Methods**

- `calculate_storage_impact()`: Current/projected storage in GB, savings %
- `calculate_performance_impact()`: Query slowdown %, cleanup time, index fragmentation
- `calculate_compliance_impact()`: Compliance score (0-100), GDPR violations, recommendations
- `recommend_policy()`: Suggest retention policy based on storage/compliance constraints
- `simulate_cleanup()`: Dry-run preview of rows deleted, warnings about cascading deletes

**Retention Policy Tiers**

- **Transient** (OTP, token revocations): 7 days default
- **Sessions** (user_sessions, refresh_tokens): 90-180 days default
- **Audit/Compliance** (audit_logs, login_attempts): 90-1095 days; GDPR minimum 365 days
- **Transactional** (scores, responses): 1825 days (5 years)
- **Core** (users, profiles): 36500 days (~100 years, keep indefinitely)

**Run tests**

```powershell
pytest -q tests/test_data_retention_simulator.py
```

**Example Usage**

```python
from app.ml.data_retention_simulator import DataRetentionSimulator, RetentionPolicy

sim = DataRetentionSimulator()

# Analyze current impact
policy = RetentionPolicy(audit_logs=730, scores=1095)
storage = sim.calculate_storage_impact(policy)  # Returns: current_gb, projected_gb, savings_pct
perf = sim.calculate_performance_impact(policy)  # Returns: query_slowdown_pct, cleanup_time_hours

# Get recommendation
recommended, rationale = sim.recommend_policy(max_storage_gb=10, compliance_strict=True)

# Dry-run cleanup
cleanup = sim.simulate_cleanup(recommended)  # Returns: rows_deleted, storage_freed_gb, warnings
```

**Deterministic & Reviewable**

- Same input always produces same output (enables deterministic CI checks)
- Configurable row counts for testing
- Conservative assumptions (data uniformly distributed over ~5 years)

**Next steps**

- Expose as internal API for deployment gating and planning tools
- Add Prometheus metrics for score trends and policy compliance
- Integrate with PR pipelines to flag high-storage-impact features
- Dashboard for tracking retention policy effectiveness

```
