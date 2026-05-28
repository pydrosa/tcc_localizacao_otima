import pandas as pd
import pytest

from src.scoring import normalize_positive, normalize_negative, normalize_weights, weighted_score


def test_normalize_positive():
    s = pd.Series([10, 20, 30])
    out = normalize_positive(s)
    assert out.min() == 0
    assert out.max() == 1


def test_normalize_negative():
    s = pd.Series([10, 20, 30])
    out = normalize_negative(s)
    assert out.iloc[0] == 1
    assert out.iloc[-1] == 0


def test_normalize_negative_all_nan_is_not_rewarded():
    out = normalize_negative(pd.Series([None, None]))
    assert out.tolist() == [0.0, 0.0]


def test_constant_criterion_is_neutral():
    out = normalize_positive(pd.Series([5, 5, 5]))
    assert out.tolist() == [0.5, 0.5, 0.5]


def test_normalize_weights_keeps_relative_importance():
    weights = {"solar_potential": 2, "wind_potential": 1}
    out = normalize_weights(weights)
    assert out["solar_potential"] == pytest.approx(2 / 3)
    assert out["wind_potential"] == pytest.approx(1 / 3)
    assert sum(out.values()) == pytest.approx(1)


def test_weighted_score_stays_between_zero_and_one():
    df = pd.DataFrame(
        {
            "solar_score": [1.0],
            "wind_score": [0.0],
            "grid_distance_score": [1.0],
            "demand_distance_score": [1.0],
            "connection_cost_score": [1.0],
        }
    )
    out = weighted_score(df, {"solar_potential": 10, "grid_distance": 10})
    assert out.iloc[0] == pytest.approx(1.0)
