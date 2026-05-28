import numpy as np
from pyproj import Transformer


def sample_raster_at_points(raster, points_gdf, raster_crs=None):
    if raster is None:
        return np.full(len(points_gdf), np.nan)

    raster_crs = raster_crs or raster.crs
    pts = points_gdf
    if pts.crs != raster_crs:
        transformer = Transformer.from_crs(pts.crs, raster_crs, always_xy=True)
        coords = [transformer.transform(p.x, p.y) for p in pts.geometry]
    else:
        coords = [(p.x, p.y) for p in pts.geometry]

    values = []
    for val in raster.sample(coords):
        x = float(val[0])
        if raster.nodata is not None and x == raster.nodata:
            values.append(np.nan)
        else:
            values.append(x)
    return np.array(values, dtype=float)
