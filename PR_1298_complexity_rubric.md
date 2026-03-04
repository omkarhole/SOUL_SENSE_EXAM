# PR: Feature complexity scoring rubric automation (#1298)

**Summary**

This change adds an automated, deterministic rubric to score feature complexity across multiple dimensions. It enables reproducible feasibility assessments, CI checks to detect high-complexity regressions, and a simple API for programmatic use.

**What this PR includes**

- `app/ml/complexity_rubric.py` — `ComplexityRubric.score()` returns breakdown and normalized 0-100 score and a category (Low/Medium/High/Critical).
- `tests/test_complexity_rubric.py` — unit tests covering low/medium inputs and validation errors.

**Technical notes**

- Inputs are 0-10 per dimension. Missing keys default to 0.
- Effort hours are included as a capped additive factor to increase score for very large efforts.
- Weights are configurable via constructor.

**Run tests**

```powershell
pytest -q tests/test_complexity_rubric.py
```

**Next steps**

- Expose this as part of the planning tooling or an internal API used in PR templates.
- Add metrics/logging and dashboarding for scored features.
