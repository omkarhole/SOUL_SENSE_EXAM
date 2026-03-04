from app.infra.prototype_gate import PrototypeGate


def test_gate_blocks_high_complexity_without_tests():
    gate = PrototypeGate(high_risk_threshold=70)
    change = {
        "normalized_complexity": 85.0,
        "introduces_infra": False,
        "public_api_change": False,
        "tests_added": False,
        "ci_checks_passing": False,
    }

    res = gate.evaluate(change)
    assert res["pass"] is False
    assert any("Complexity score" in r for r in res["reasons"])


def test_gate_allows_low_risk_with_tests_and_ci():
    gate = PrototypeGate()
    change = {
        "normalized_complexity": 20.0,
        "introduces_infra": False,
        "public_api_change": False,
        "tests_added": True,
        "ci_checks_passing": True,
    }

    res = gate.evaluate(change)
    assert res["pass"] is True
    assert "Allowed" in " ".join(res["actions"]) or res["actions"]


def test_gate_blocks_infra_when_no_ci_or_tests():
    gate = PrototypeGate()
    change = {
        "normalized_complexity": 30.0,
        "introduces_infra": True,
        "tests_added": False,
        "ci_checks_passing": False,
    }

    res = gate.evaluate(change)
    assert res["pass"] is False
    assert any("infrastructure" in r.lower() for r in res["reasons"]) or any("architectural review" in a.lower() for a in res["actions"]) 
