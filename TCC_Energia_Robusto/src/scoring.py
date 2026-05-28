import numpy as np
import pandas as pd


def normalize_positive(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    if s.isna().all():
        return pd.Series(np.zeros(len(s)), index=s.index)
    s = s.fillna(s.median())
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(np.ones(len(s)), index=s.index)
    return (s - mn) / (mx - mn)


def normalize_negative(series: pd.Series) -> pd.Series:
    return 1 - normalize_positive(series)


def weighted_score(df: pd.DataFrame, weights: dict) -> pd.Series:
    return (
        weights.get("solar_potential", 0) * df["solar_score"] +
        weights.get("wind_potential", 0) * df["wind_score"] +
        weights.get("grid_distance", 0) * df["grid_distance_score"] +
        weights.get("demand_distance", 0) * df["demand_distance_score"] +
        weights.get("connection_cost", 0) * df["connection_cost_score"]
    )
