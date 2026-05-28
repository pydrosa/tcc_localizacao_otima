import numpy as np
import geopandas as gpd
from shapely.geometry import Point


def to_crs(gdf: gpd.GeoDataFrame | None, crs: str):
    if gdf is None:
        return None
    if gdf.crs is None:
        return gdf.set_crs("EPSG:4326").to_crs(crs)
    return gdf.to_crs(crs)


def create_grid_from_bounds(bounds, spacing_m: float, crs: str) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = bounds
    xs = np.arange(minx, maxx + spacing_m, spacing_m)
    ys = np.arange(miny, maxy + spacing_m, spacing_m)
    points = [Point(x, y) for x in xs for y in ys]
    return gpd.GeoDataFrame({"candidate_id": range(1, len(points) + 1)}, geometry=points, crs=crs)


def nearest_distance_km(points: gpd.GeoDataFrame, targets: gpd.GeoDataFrame | None) -> np.ndarray:
    if targets is None or targets.empty:
        return np.full(len(points), np.nan)

    target_geometries = targets[["geometry"]].copy()
    if target_geometries.crs != points.crs:
        target_geometries = target_geometries.to_crs(points.crs)

    joined = gpd.sjoin_nearest(
        points[["geometry"]],
        target_geometries,
        how="left",
        distance_col="distance_m",
    )
    distances_m = joined.groupby(level=0)["distance_m"].min().reindex(points.index)
    return distances_m.to_numpy(dtype=float) / 1000.0


def apply_restrictions(
    points: gpd.GeoDataFrame,
    restrictions: gpd.GeoDataFrame | None,
    *,
    policy: str = "exclude",
    penalty_factor: float = 0.35,
) -> gpd.GeoDataFrame:
    points = points.copy()
    points["is_restricted"] = False
    points["restriction_factor"] = 1.0

    if restrictions is None or restrictions.empty:
        return points

    if policy not in {"exclude", "penalize"}:
        raise ValueError("restriction_policy deve ser 'exclude' ou 'penalize'.")
    if not 0 <= penalty_factor <= 1:
        raise ValueError("restriction_penalty_factor deve estar entre 0 e 1.")

    restricted_union = restrictions.geometry.union_all()
    points["is_restricted"] = points.geometry.within(restricted_union)
    if policy == "exclude":
        return points[~points["is_restricted"]].copy()

    points.loc[points["is_restricted"], "restriction_factor"] = penalty_factor
    return points
