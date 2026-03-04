# PR: Third-party vendor fallback readiness score (#1300)

**Summary**

Adds a deterministic readiness scoring utility to evaluate third-party vendor health
and recommend safe fallback actions for high-risk architecture changes.

**Motivation**

- Gate risky changes that depend on external vendors by computing a reproducible readiness score.
- Provide CI-checkable logic and deterministic results that reviewers can validate.

**What this PR changes**

- `app/ml/vendor_fallback.py`: `VendorFallback.readiness()` that returns a normalized 0-100 score, category, recommended action, and breakdown.
- `tests/test_vendor_fallback.py`: unit tests for ready/unready/invalid inputs.

**How it works**

- Inputs: availability(%), latency(ms), error_rate(%), support_response_time(hours), retryability(0-10), sla_coverage(%), cost_impact(0-10).
- Each metric is scaled to 0-1 (1 best) and weighted. The weighted sum is normalized to 0-100.
- Actions: `use_primary`, `enable_degraded_mode`, `switch_to_backup`, `disable_feature`.

**Run tests**

```powershell
pytest -q tests/test_vendor_fallback.py
```

**Next steps**

- Integrate with deployment gating and PR checks; emit logs and Prometheus metrics for score and action.
- Add an API endpoint for operators and dashboarding to visualize readiness over time.
