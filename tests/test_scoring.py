import pandas as pd
from src.scoring import normalize_positive, normalize_negative


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
