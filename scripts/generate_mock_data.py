from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point, Polygon


ROOT = Path(__file__).resolve().parents[1]


def _write_vector(path: Path, gdf: gpd.GeoDataFrame, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        return
    gdf.to_file(path, driver="GeoJSON")


def _write_raster(path: Path, data: np.ndarray, transform, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        return
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(data.astype("float32"), 1)


def generate_mock_data(root: str | Path = ROOT, *, overwrite: bool = True) -> None:
    root = Path(root)
    raw = root / "data/raw"
    for path in [
        raw / "ons",
        raw / "solar",
        raw / "eolico",
        raw / "demanda",
        raw / "infra",
        raw / "hidrografia",
        raw / "urbano",
        raw / "topografia",
        raw / "uso_solo",
        raw / "restricoes",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    substations = gpd.GeoDataFrame(
        {
            "id_sub": ["SE-NE-01", "SE-CO-01", "SE-SE-01", "SE-S-01"],
            "nome": ["SE Nordeste", "SE Centro-Oeste", "SE Sudeste", "SE Sul"],
            "tensao_kv": [500, 500, 345, 230],
            "geometry": [Point(-38, -8), Point(-52, -15), Point(-44, -22), Point(-51, -29)],
        },
        crs="EPSG:4326",
    )
    _write_vector(raw / "ons/subestacoes.geojson", substations, overwrite=overwrite)

    lines = gpd.GeoDataFrame(
        {
            "id_linha": ["LT-01", "LT-02", "LT-03"],
            "tensao_kv": [500, 500, 230],
            "geometry": [
                LineString([(-38, -8), (-52, -15)]),
                LineString([(-52, -15), (-44, -22)]),
                LineString([(-44, -22), (-51, -29)]),
            ],
        },
        crs="EPSG:4326",
    )
    _write_vector(raw / "ons/linhas.geojson", lines, overwrite=overwrite)

    demand = gpd.GeoDataFrame(
        {
            "id_demanda": ["REC", "BSB", "SP", "POA"],
            "nome": ["Recife", "Brasilia", "Sao Paulo", "Porto Alegre"],
            "demanda_mw": [1200, 1800, 8500, 2300],
            "geometry": [
                Point(-34.88, -8.05),
                Point(-47.88, -15.79),
                Point(-46.63, -23.55),
                Point(-51.23, -30.03),
            ],
        },
        crs="EPSG:4326",
    )
    _write_vector(raw / "demanda/demanda.geojson", demand, overwrite=overwrite)

    roads = gpd.GeoDataFrame(
        {
            "id_rodovia": ["BR-NE", "BR-CO", "BR-SUL"],
            "nome": ["Corredor Nordeste", "Corredor Centro-Oeste", "Corredor Sul"],
            "geometry": [
                LineString([(-35, -7), (-39, -10), (-44, -13), (-48, -16)]),
                LineString([(-55, -12), (-50, -15), (-45, -18), (-42, -22)]),
                LineString([(-43, -22), (-47, -25), (-51, -29), (-54, -31)]),
            ],
        },
        crs="EPSG:4326",
    )
    _write_vector(raw / "infra/rodovias.geojson", roads, overwrite=overwrite)

    water = gpd.GeoDataFrame(
        {
            "id_recurso": ["RIO-01", "RIO-02", "RES-01"],
            "tipo": ["rio", "rio", "reservatorio"],
            "geometry": [
                LineString([(-42, -6), (-43, -10), (-45, -14), (-47, -18)]),
                LineString([(-54, -18), (-51, -20), (-48, -23), (-46, -25)]),
                Polygon([(-40.8, -10.5), (-39.8, -10.5), (-39.8, -9.7), (-40.8, -9.7)]),
            ],
        },
        crs="EPSG:4326",
    )
    _write_vector(raw / "hidrografia/recursos_hidricos.geojson", water, overwrite=overwrite)

    urban = gpd.GeoDataFrame(
        {
            "id_area": ["REC", "BSB", "SP", "POA"],
            "nome": ["Recife", "Brasilia", "Sao Paulo", "Porto Alegre"],
            "geometry": [
                Polygon([(-35.4, -8.5), (-34.3, -8.5), (-34.3, -7.6), (-35.4, -7.6)]),
                Polygon([(-48.5, -16.3), (-47.2, -16.3), (-47.2, -15.2), (-48.5, -15.2)]),
                Polygon([(-47.4, -24.2), (-45.9, -24.2), (-45.9, -22.9), (-47.4, -22.9)]),
                Polygon([(-51.8, -30.6), (-50.7, -30.6), (-50.7, -29.5), (-51.8, -29.5)]),
            ],
        },
        crs="EPSG:4326",
    )
    _write_vector(raw / "urbano/areas_urbanas.geojson", urban, overwrite=overwrite)

    restrictions = gpd.GeoDataFrame(
        {
            "id": [1, 2],
            "tipo": ["Unidade de conservacao", "Area sensivel"],
            "geometry": [
                Polygon([(-45, -12), (-42, -12), (-42, -9), (-45, -9)]),
                Polygon([(-50, -24), (-47, -24), (-47, -21), (-50, -21)]),
            ],
        },
        crs="EPSG:4326",
    )
    _write_vector(raw / "restricoes/restricoes.geojson", restrictions, overwrite=overwrite)

    width = 120
    height = 120
    x_min, y_max = -60, 5
    pixel = 0.35
    transform = from_origin(x_min, y_max, pixel, pixel)

    rng = np.random.default_rng(42)
    y_indices, x_indices = np.indices((height, width))
    lat = y_max - y_indices * pixel
    lon = x_min + x_indices * pixel

    solar = 4.4 + 2.2 * ((lat + 35) / 40) + 0.25 * rng.normal(size=(height, width))
    wind_ne = np.exp(-((lon + 39) ** 2 + (lat + 9) ** 2) / 150)
    wind_south = np.exp(-((lon + 51) ** 2 + (lat + 29) ** 2) / 110)
    wind = 4.0 + 3.4 * wind_ne + 1.8 * wind_south + 0.6 * rng.random((height, width))
    slope = 1.2 + 6.5 * np.exp(-((lon + 43) ** 2 + (lat + 20) ** 2) / 180) + 1.0 * rng.random((height, width))
    land_use = 0.82 - 0.045 * slope + 0.08 * rng.normal(size=(height, width))

    _write_raster(raw / "solar/irradiancia_global.tif", solar, transform, overwrite=overwrite)
    _write_raster(raw / "eolico/velocidade_vento.tif", wind, transform, overwrite=overwrite)
    _write_raster(raw / "topografia/declividade_percent.tif", slope, transform, overwrite=overwrite)
    _write_raster(raw / "uso_solo/aptidao_solo.tif", np.clip(land_use, 0, 1), transform, overwrite=overwrite)


if __name__ == "__main__":
    generate_mock_data()
    print("Dados ficticios gerados com sucesso.")
