from app.ml.cost_estimator import CostEstimator


def test_cost_api_simulated_request():
    est = CostEstimator()

    # Simulate a single request to a 'large' model lasting 0.5s and 2000 tokens
    res = est.estimate(model_tier="large", duration_seconds=0.5, tokens=2000, concurrency=1)

    # compute_cost = 0.01 * 0.5 = 0.005
    assert res["compute_cost"] == 0.005
    # data_cost = 2000 * 0.000001 = 0.002
    assert res["data_cost"] == 0.002
    assert res["total_cost"] == 0.007
