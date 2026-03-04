# PR: Cost estimation model for new ML endpoints (#1297)

**Summary**

Adds a deterministic, testable cost estimation module for ML endpoints to support feasibility analysis, CI validation and rollout guardrails.

**Motivation**

- Provide reproducible estimates for request-level cost to assess feasibility before enabling new model endpoints.
- Enable CI to validate cost calculations and detect accidental high-cost regressions.

**What this PR changes**

- Adds `app/ml/cost_estimator.py` with `CostEstimator.estimate()` providing compute/data/total cost breakdown.
- Adds unit tests `tests/test_cost_estimator.py` and an integration-style `tests/integration/test_cost_api.py`.

**Rates / Model tiers**

- `small`: $0.0005 / sec
- `medium`: $0.0020 / sec
- `large`: $0.0100 / sec
- `data`: $0.000001 / token

These are conservative, easy-to-adjust constants intended for feasibility analysis and CI checks.

**CI and Tests**

- Unit tests validate deterministic math and input validation.
- Integration test simulates a request flow and validates the returned breakdown.

**How to run tests locally**

```powershell
pytest -q tests/test_cost_estimator.py
pytest -q tests/integration/test_cost_api.py
```

**Next steps (optional)**

- Expose estimator as an internal API to the billing/edge service.
- Emit Prometheus metrics and dashboards for cost projections and guardrails.
- Add feature-flag gating for experimental model endpoints and automated cost checks in PR pipelines.
