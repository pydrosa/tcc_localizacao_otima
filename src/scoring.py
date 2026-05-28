import numpy as np
import pandas as pd


CRITERION_COLUMNS = {
    "solar_potential": "solar_score",
    "wind_potential": "wind_score",
    "grid_distance": "grid_distance_score",
    "demand_distance": "demand_distance_score",
    "road_distance": "road_distance_score",
    "water_distance": "water_distance_score",
    "urban_distance": "urban_distance_score",
    "slope": "slope_score",
    "land_use": "land_use_score",
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


def fuzzy_linear(
    series: pd.Series,
    *,
    lower: float,
    upper: float,
    increasing: bool,
    all_nan_value: float = 0.0,
) -> pd.Series:
    if upper == lower:
        raise ValueError("Os limites fuzzy inferior e superior devem ser diferentes.")

    s = series.astype(float)
    if s.isna().all():
        return pd.Series(np.full(len(s), all_nan_value), index=s.index)

    s = s.fillna(s.median())
    score = (s - lower) / (upper - lower)
    if not increasing:
        score = 1 - score
    return score.clip(0, 1)


def fuzzy_increasing(series: pd.Series, *, lower: float, upper: float) -> pd.Series:
    return fuzzy_linear(series, lower=lower, upper=upper, increasing=True)


def fuzzy_decreasing(series: pd.Series, *, lower: float, upper: float) -> pd.Series:
    return fuzzy_linear(series, lower=lower, upper=upper, increasing=False)


def aptitude_class(series: pd.Series) -> pd.Series:
    scores = series.astype(float).fillna(0).clip(0, 1)
    classes = np.ceil(scores * 9).astype(int)
    return pd.Series(np.clip(classes, 1, 9), index=series.index)


def normalize_weights(weights: dict) -> dict:
    valid_weights = {key: float(weights.get(key, 0) or 0) for key in CRITERION_COLUMNS}
    total = sum(valid_weights.values())
    if total <= 0:
        raise ValueError("A soma dos pesos do cenário deve ser maior que zero.")
    return {key: value / total for key, value in valid_weights.items()}


def weighted_score(df: pd.DataFrame, weights: dict) -> pd.Series:
    normalized = normalize_weights(weights)
    missing_columns = [
        column
        for key, column in CRITERION_COLUMNS.items()
        if normalized[key] > 0 and column not in df.columns
    ]
    if missing_columns:
        raise KeyError(f"Colunas de score ausentes: {missing_columns}")

    score = pd.Series(np.zeros(len(df)), index=df.index, dtype=float)
    for weight_key, column in CRITERION_COLUMNS.items():
        if normalized[weight_key] > 0:
            score = score + normalized[weight_key] * df[column].astype(float)
    return score.clip(0, 1)
