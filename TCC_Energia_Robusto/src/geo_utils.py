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
    target_union = targets.geometry.union_all()
    return points.geometry.distance(target_union).to_numpy() / 1000.0


def remove_restricted(points: gpd.GeoDataFrame, restrictions: gpd.GeoDataFrame | None) -> gpd.GeoDataFrame:
    if restrictions is None or restrictions.empty:
        points["is_restricted"] = False
        return points
    restricted_union = restrictions.geometry.union_all()
    points = points.copy()
    points["is_restricted"] = points.geometry.within(restricted_union)
    return points[~points["is_restricted"]].copy()
