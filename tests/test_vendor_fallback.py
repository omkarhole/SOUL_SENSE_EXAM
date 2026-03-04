from app.ml.vendor_fallback import VendorFallback


def test_ready_vendor():
    v = VendorFallback()
    metrics = {
        "availability": 99.9,
        "latency": 50,
        "error_rate": 0.1,
        "support_response_time": 4,
        "retryability": 9,
        "sla_coverage": 99,
        "cost_impact": 2,
    }
    out = v.readiness(metrics)
    assert out["category"] == "Ready"
    assert out["normalized_score"] >= 75.0


def test_unready_vendor():
    v = VendorFallback()
    metrics = {
        "availability": 70,
        "latency": 1000,
        "error_rate": 20,
        "support_response_time": 120,
        "retryability": 1,
        "sla_coverage": 50,
        "cost_impact": 9,
    }
    out = v.readiness(metrics)
    assert out["category"] in ("High Risk", "Unready")
    assert out["recommended_action"] in ("switch_to_backup", "disable_feature")


def test_invalid_metrics():
    v = VendorFallback()
    try:
        v.readiness("not a dict")
        assert False
    except ValueError:
        pass
