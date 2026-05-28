from __future__ import annotations

from pathlib import Path
import geopandas as gpd
import pandas as pd

from src.io import read_vector, read_raster, ensure_dir
from src.geo_utils import to_crs, create_grid_from_bounds, nearest_distance_km, remove_restricted
from src.raster_tools import sample_raster_at_points
from src.scoring import normalize_positive, normalize_negative, weighted_score


def run_analysis(config: dict, scenario: str = "hibrido", grid_spacing_km: float | None = None) -> gpd.GeoDataFrame:
    paths = config["paths"]
    analysis_cfg = config["analysis"]
    projected_crs = analysis_cfg.get("crs_projected", "EPSG:5880")
    spacing_km = grid_spacing_km or analysis_cfg.get("grid_spacing_km", 50)
    spacing_m = spacing_km * 1000

    substations = read_vector(paths["substations"], required=False)
    lines = read_vector(paths["transmission_lines"], required=False)
    demand = read_vector(paths["demand_points"], required=False)
    restrictions = read_vector(paths["restrictions"], required=False)
    solar_raster = read_raster(paths["solar_raster"], required=False)
    wind_raster = read_raster(paths["wind_raster"], required=False)

    substations_m = to_crs(substations, projected_crs)
    lines_m = to_crs(lines, projected_crs)
    demand_m = to_crs(demand, projected_crs)
    restrictions_m = to_crs(restrictions, projected_crs)

    bounds_sources = [g for g in [substations_m, lines_m, demand_m] if g is not None and not g.empty]
    if not bounds_sources:
        raise ValueError("Nenhuma camada vetorial válida foi encontrada para gerar a área de estudo.")

    study_area = gpd.GeoSeries(pd.concat([g.geometry for g in bounds_sources], ignore_index=True), crs=projected_crs).union_all().envelope
    minx, miny, maxx, maxy = study_area.bounds
    buffer_m = config["analysis"].get("max_distance_grid_km", 250) * 1000
    bounds = (minx - buffer_m, miny - buffer_m, maxx + buffer_m, maxy + buffer_m)

    grid = create_grid_from_bounds(bounds, spacing_m=spacing_m, crs=projected_crs)
    grid = remove_restricted(grid, restrictions_m)

    grid_geo = grid.to_crs("EPSG:4326")
    grid["solar_kwh_m2_day"] = sample_raster_at_points(solar_raster, grid_geo)
    grid["wind_m_s"] = sample_raster_at_points(wind_raster, grid_geo)

    network_layers = [g for g in [substations_m, lines_m] if g is not None and not g.empty]
    network = None
    if network_layers:
        network = gpd.GeoDataFrame(geometry=pd.concat([g.geometry for g in network_layers], ignore_index=True), crs=projected_crs)

    grid["dist_grid_km"] = nearest_distance_km(grid, network)
    grid["dist_demand_km"] = nearest_distance_km(grid, demand_m)

    cost_per_km = config.get("costs", {}).get("connection_cost_per_km_brl", 1200000)
    grid["connection_cost_brl"] = grid["dist_grid_km"] * cost_per_km

    thresholds = config.get("thresholds", {})
    min_solar = thresholds.get("min_solar_kwh_m2_day", 0)
    min_wind = thresholds.get("min_wind_m_s", 0)

    if scenario == "solar":
        grid = grid[grid["solar_kwh_m2_day"].fillna(0) >= min_solar].copy()
    elif scenario == "eolico":
        grid = grid[grid["wind_m_s"].fillna(0) >= min_wind].copy()
    elif scenario == "hibrido":
        grid = grid[(grid["solar_kwh_m2_day"].fillna(0) >= min_solar) | (grid["wind_m_s"].fillna(0) >= min_wind)].copy()

    grid["solar_score"] = normalize_positive(grid["solar_kwh_m2_day"])
    grid["wind_score"] = normalize_positive(grid["wind_m_s"])
    grid["grid_distance_score"] = normalize_negative(grid["dist_grid_km"])
    grid["demand_distance_score"] = normalize_negative(grid["dist_demand_km"])
    grid["connection_cost_score"] = normalize_negative(grid["connection_cost_brl"])

    weights = config["weights"].get(scenario, config["weights"]["hibrido"])
    grid["score_final"] = weighted_score(grid, weights)
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
        "rank", "candidate_id", "scenario", "solar_kwh_m2_day", "wind_m_s",
        "dist_grid_km", "dist_demand_km", "connection_cost_brl", "score_final", "geometry"
    ]
    export_gdf = gdf[cols].to_crs("EPSG:4326")
    export_gdf.drop(columns="geometry").to_csv(csv_path, index=False)
    export_gdf.to_file(geojson_path, driver="GeoJSON")

    return {"csv": csv_path, "geojson": geojson_path, "maps_dir": maps}
