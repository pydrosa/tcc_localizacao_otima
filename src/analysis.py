from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from src.geo_utils import apply_restrictions, create_grid_from_bounds, nearest_distance_km, to_crs
from src.io import ensure_dir, read_raster, read_vector
from src.raster_tools import sample_raster_at_points
from src.scoring import aptitude_class, fuzzy_decreasing, fuzzy_increasing, normalize_negative, weighted_score


VALID_SCENARIOS = {"solar", "eolico", "hibrido", "infraestrutura", "ambiental"}
DEFAULT_FUZZY = {
    "solar_potential": {"lower": 4.2, "upper": 6.0},
    "wind_potential": {"lower": 5.0, "upper": 8.5},
    "grid_distance": {"lower": 10, "upper": 120},
    "demand_distance": {"lower": 25, "upper": 250},
    "road_distance": {"lower": 5, "upper": 80},
    "water_distance": {"lower": 10, "upper": 120},
    "urban_distance": {"lower": 5, "upper": 30},
    "slope": {"lower": 2, "upper": 8},
}


def _optional_vector(paths: dict, key: str):
    path = paths.get(key)
    return read_vector(path, required=False) if path else None


def _optional_raster(paths: dict, key: str):
    path = paths.get(key)
    return read_raster(path, required=False) if path else None


def _metric_bounds(config: dict, key: str) -> tuple[float, float]:
    cfg = {**DEFAULT_FUZZY[key], **config.get("fuzzy", {}).get(key, {})}
    return float(cfg["lower"]), float(cfg["upper"])


def _bounded_score(values: np.ndarray, index: pd.Index) -> pd.Series:
    score = pd.Series(values, index=index, dtype=float)
    if score.isna().all():
        return pd.Series(np.zeros(len(score)), index=index, dtype=float)
    return score.fillna(score.median()).clip(0, 1)


def _concat_geometry(layers: list[gpd.GeoDataFrame], crs: str) -> gpd.GeoDataFrame | None:
    valid_layers = [g for g in layers if g is not None and not g.empty]
    if not valid_layers:
        return None
    return gpd.GeoDataFrame(
        geometry=pd.concat([g.geometry for g in valid_layers], ignore_index=True),
        crs=crs,
    )


def run_analysis(config: dict, scenario: str = "hibrido", grid_spacing_km: float | None = None) -> gpd.GeoDataFrame:
    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"Cenário inválido: {scenario}. Use um de: {sorted(VALID_SCENARIOS)}.")

    paths = config["paths"]
    analysis_cfg = config["analysis"]
    thresholds = config.get("thresholds", {})
    projected_crs = analysis_cfg.get("crs_projected", "EPSG:5880")
    spacing_km = grid_spacing_km or analysis_cfg.get("grid_spacing_km", 50)
    if spacing_km <= 0:
        raise ValueError("O espaçamento da malha deve ser maior que zero.")
    spacing_m = spacing_km * 1000

    substations = _optional_vector(paths, "substations")
    lines = _optional_vector(paths, "transmission_lines")
    demand = _optional_vector(paths, "demand_points")
    roads = _optional_vector(paths, "roads")
    water = _optional_vector(paths, "water_resources")
    urban = _optional_vector(paths, "urban_areas")
    restrictions = _optional_vector(paths, "restrictions")
    solar_raster = _optional_raster(paths, "solar_raster")
    wind_raster = _optional_raster(paths, "wind_raster")
    slope_raster = _optional_raster(paths, "slope_raster")
    land_use_raster = _optional_raster(paths, "land_use_raster")

    substations_m = to_crs(substations, projected_crs)
    lines_m = to_crs(lines, projected_crs)
    demand_m = to_crs(demand, projected_crs)
    roads_m = to_crs(roads, projected_crs)
    water_m = to_crs(water, projected_crs)
    urban_m = to_crs(urban, projected_crs)
    restrictions_m = to_crs(restrictions, projected_crs)

    bounds_sources = [g for g in [substations_m, lines_m, demand_m, roads_m, water_m, urban_m] if g is not None and not g.empty]
    if not bounds_sources:
        raise ValueError("Nenhuma camada vetorial válida foi encontrada para gerar a área de estudo.")

    study_area = gpd.GeoSeries(pd.concat([g.geometry for g in bounds_sources], ignore_index=True), crs=projected_crs).union_all().envelope
    minx, miny, maxx, maxy = study_area.bounds
    buffer_m = analysis_cfg.get("max_distance_grid_km", 250) * 1000
    bounds = (minx - buffer_m, miny - buffer_m, maxx + buffer_m, maxy + buffer_m)

    grid = create_grid_from_bounds(bounds, spacing_m=spacing_m, crs=projected_crs)
    grid = apply_restrictions(
        grid,
        restrictions_m,
        policy=thresholds.get("restriction_policy", "exclude"),
        penalty_factor=thresholds.get("restriction_penalty_factor", 0.35),
    )
    if grid.empty:
        raise ValueError("Nenhum ponto candidato restou após aplicar as restrições ambientais.")

    grid_geo = grid.to_crs("EPSG:4326")
    grid["solar_kwh_m2_day"] = sample_raster_at_points(solar_raster, grid_geo)
    grid["wind_m_s"] = sample_raster_at_points(wind_raster, grid_geo)
    grid["slope_percent"] = sample_raster_at_points(slope_raster, grid_geo)
    grid["land_use_score"] = _bounded_score(sample_raster_at_points(land_use_raster, grid_geo), grid.index)

    network = _concat_geometry([substations_m, lines_m], projected_crs)
    grid["dist_grid_km"] = nearest_distance_km(grid, network)
    grid["dist_demand_km"] = nearest_distance_km(grid, demand_m)
    grid["dist_road_km"] = nearest_distance_km(grid, roads_m)
    grid["dist_water_km"] = nearest_distance_km(grid, water_m)
    grid["dist_urban_km"] = nearest_distance_km(grid, urban_m)

    costs = config.get("costs", {})
    grid_cost = costs.get("grid_connection_cost_per_km_brl", costs.get("connection_cost_per_km_brl", 1200000))
    road_cost = costs.get("road_access_cost_per_km_brl", 250000)
    water_cost = costs.get("water_access_cost_per_km_brl", 180000)
    grid["connection_cost_brl"] = grid["dist_grid_km"] * grid_cost
    grid["infrastructure_cost_brl"] = (
        grid["dist_grid_km"].fillna(0) * grid_cost
        + grid["dist_road_km"].fillna(0) * road_cost
        + grid["dist_water_km"].fillna(0) * water_cost
    )

    min_solar = thresholds.get("min_solar_kwh_m2_day", 0)
    min_wind = thresholds.get("min_wind_m_s", 0)
    solar_ok = grid["solar_kwh_m2_day"].fillna(0) >= min_solar
    wind_ok = grid["wind_m_s"].fillna(0) >= min_wind
    if scenario == "solar":
        grid = grid[solar_ok].copy()
    elif scenario == "eolico":
        grid = grid[wind_ok].copy()
    else:
        grid = grid[solar_ok | wind_ok].copy()

    if grid.empty:
        raise ValueError("Nenhum ponto candidato atendeu aos limiares mínimos do cenário selecionado.")

    lower, upper = _metric_bounds(config, "solar_potential")
    grid["solar_score"] = fuzzy_increasing(grid["solar_kwh_m2_day"], lower=lower, upper=upper)
    lower, upper = _metric_bounds(config, "wind_potential")
    grid["wind_score"] = fuzzy_increasing(grid["wind_m_s"], lower=lower, upper=upper)
    lower, upper = _metric_bounds(config, "grid_distance")
    grid["grid_distance_score"] = fuzzy_decreasing(grid["dist_grid_km"], lower=lower, upper=upper)
    lower, upper = _metric_bounds(config, "demand_distance")
    grid["demand_distance_score"] = fuzzy_decreasing(grid["dist_demand_km"], lower=lower, upper=upper)
    lower, upper = _metric_bounds(config, "road_distance")
    grid["road_distance_score"] = fuzzy_decreasing(grid["dist_road_km"], lower=lower, upper=upper)
    lower, upper = _metric_bounds(config, "water_distance")
    grid["water_distance_score"] = fuzzy_decreasing(grid["dist_water_km"], lower=lower, upper=upper)
    lower, upper = _metric_bounds(config, "urban_distance")
    grid["urban_distance_score"] = fuzzy_increasing(grid["dist_urban_km"], lower=lower, upper=upper)
    lower, upper = _metric_bounds(config, "slope")
    grid["slope_score"] = fuzzy_decreasing(grid["slope_percent"], lower=lower, upper=upper)
    grid["connection_cost_score"] = normalize_negative(grid["infrastructure_cost_brl"])

    weights = config["weights"].get(scenario, config["weights"]["hibrido"])
    grid["score_final"] = weighted_score(grid, weights) * grid["restriction_factor"]
    grid["aptitude_class"] = aptitude_class(grid["score_final"])
    grid["scenario"] = scenario

    grid = grid.sort_values("score_final", ascending=False).reset_index(drop=True)
    grid["rank"] = grid.index + 1
    return grid


def export_results(gdf: gpd.GeoDataFrame, config: dict, scenario: str) -> dict:
    output_dir = Path(config["paths"].get("outputs", "outputs"))
    reports = ensure_dir(output_dir / "reports")
    maps = ensure_dir(output_dir / "maps")

    csv_path = reports / f"ranking_{scenario}.csv"
    geojson_path = reports / f"ranking_{scenario}.geojson"

    cols = [
        "rank",
        "candidate_id",
        "scenario",
        "aptitude_class",
        "solar_kwh_m2_day",
        "wind_m_s",
        "slope_percent",
        "dist_grid_km",
        "dist_demand_km",
        "dist_road_km",
        "dist_water_km",
        "dist_urban_km",
        "connection_cost_brl",
        "infrastructure_cost_brl",
        "is_restricted",
        "restriction_factor",
        "score_final",
        "geometry",
    ]
    export_gdf = gdf[cols].to_crs("EPSG:4326")
    export_gdf["longitude"] = export_gdf.geometry.x
    export_gdf["latitude"] = export_gdf.geometry.y
    export_gdf.drop(columns="geometry").to_csv(csv_path, index=False)
    export_gdf.to_file(geojson_path, driver="GeoJSON")

    return {"csv": csv_path, "geojson": geojson_path, "maps_dir": maps}
