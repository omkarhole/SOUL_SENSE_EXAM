# PR: Prototype gate for high-risk architecture changes (#1299)

**Summary**

Adds a lightweight automation to evaluate PRs for high-risk architecture changes and recommend gating actions (block, require review, add tests, feature flagging).

**What this PR includes**

- `app/infra/prototype_gate.py` — `PrototypeGate.evaluate()` returns `pass` boolean, `score`, `reasons`, and `actions`.
- `tests/test_prototype_gate.py` — unit tests covering blocking and allowing scenarios.

**Design notes**

- The gate is deterministic and intended for use in CI to flag PRs that require extra review.
- Inputs are simple signals (normalized complexity 0-100, booleans for infra/API changes, tests present, CI passing).
- Blocking heuristics are conservative: block high-complexity or infra/public-api changes unless covered by tests and passing CI.

**How to use**

- Integrate into CI as a step that gathers PR metadata (complexity score from planning tooling, boolean signals) and calls `PrototypeGate.evaluate()`.
- If `pass` is False, fail the job and surface `actions` to the author.

**Next steps**

- Wire into PR pipelines, add logging/metrics, and build dashboard for gate results.
