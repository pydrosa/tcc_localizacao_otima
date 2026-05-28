import numpy as np
import pandas as pd


CRITERION_COLUMNS = {
    "solar_potential": "solar_score",
    "wind_potential": "wind_score",
    "grid_distance": "grid_distance_score",
    "demand_distance": "demand_distance_score",
    "connection_cost": "connection_cost_score",
}


def normalize_positive(
    series: pd.Series,
    *,
    constant_value: float = 0.5,
    all_nan_value: float = 0.0,
) -> pd.Series:
    s = series.astype(float)
    if s.isna().all():
        return pd.Series(np.full(len(s), all_nan_value), index=s.index)
    s = s.fillna(s.median())
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(np.full(len(s), constant_value), index=s.index)
    return (s - mn) / (mx - mn)


def normalize_negative(
    series: pd.Series,
    *,
    constant_value: float = 0.5,
    all_nan_value: float = 0.0,
) -> pd.Series:
    if series.astype(float).isna().all():
        return pd.Series(np.full(len(series), all_nan_value), index=series.index)
    return 1 - normalize_positive(series, constant_value=constant_value, all_nan_value=all_nan_value)


def normalize_weights(weights: dict) -> dict:
    valid_weights = {key: float(weights.get(key, 0) or 0) for key in CRITERION_COLUMNS}
    total = sum(valid_weights.values())
    if total <= 0:
        raise ValueError("A soma dos pesos do cenário deve ser maior que zero.")
    return {key: value / total for key, value in valid_weights.items()}


def weighted_score(df: pd.DataFrame, weights: dict) -> pd.Series:
    normalized = normalize_weights(weights)
    missing_columns = [column for column in CRITERION_COLUMNS.values() if column not in df.columns]
    if missing_columns:
        raise KeyError(f"Colunas de score ausentes: {missing_columns}")

    score = pd.Series(np.zeros(len(df)), index=df.index, dtype=float)
    for weight_key, column in CRITERION_COLUMNS.items():
        score = score + normalized[weight_key] * df[column].astype(float)
    return score.clip(0, 1)
