import pytest

from app.ml.cost_estimator import CostEstimator


def test_estimate_basic():
    est = CostEstimator()
    r = est.estimate(model_tier="small", duration_seconds=2.0, tokens=1000, concurrency=1)
    # compute_cost = 0.0005 * 2 = 0.001
    assert r["compute_cost"] == 0.001
    # data_cost = 1000 * 0.000001 = 0.001
    assert r["data_cost"] == 0.001
    assert r["total_cost"] == 0.002


def test_estimate_concurrency():
    est = CostEstimator()
    r = est.estimate(model_tier="medium", duration_seconds=5.0, tokens=0, concurrency=3)
    # compute_cost = 0.0020 * 5 * 3 = 0.03
    assert r["compute_cost"] == 0.03
    assert r["data_cost"] == 0.0
    assert r["total_cost"] == 0.03


def test_invalid_inputs():
    est = CostEstimator()
    with pytest.raises(ValueError):
        est.estimate(model_tier="xlarge", duration_seconds=1)
    with pytest.raises(ValueError):
        est.estimate(model_tier="small", duration_seconds=-1)
    with pytest.raises(ValueError):
        est.estimate(model_tier="small", duration_seconds=1, tokens=-10)
    with pytest.raises(ValueError):
        est.estimate(model_tier="small", duration_seconds=1, concurrency=0)
