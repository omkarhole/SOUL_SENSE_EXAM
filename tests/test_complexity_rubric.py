from app.ml.complexity_rubric import ComplexityRubric


def test_simple_low_feature():
    r = ComplexityRubric()
    features = {"user_visible": 1, "infra_changes": 0, "data_required": 0}
    out = r.score(features, effort_hours=2)
    assert out["category"] == "Low"
    assert 0 <= out["normalized_score"] <= 100


def test_medium_to_high_feature():
    r = ComplexityRubric()
    features = {
        "user_visible": 8,
        "infra_changes": 6,
        "data_required": 7,
        "dependencies": 6,
        "security_impact": 2,
        "rollout_complexity": 5,
        "backward_incompat": 3,
    }
    out = r.score(features, effort_hours=40)
    assert out["category"] in ("Medium", "High")
    assert out["normalized_score"] >= 35


def test_invalid_inputs():
    r = ComplexityRubric()
    try:
        r.score("not-a-dict")
        assert False, "should have raised"
    except ValueError:
        pass

    try:
        r.score({"user_visible": 11})
        assert False, "should have raised"
    except ValueError:
        pass
