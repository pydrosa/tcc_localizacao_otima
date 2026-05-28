from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point, Polygon


ROOT = Path(__file__).resolve().parents[1]


def generate_mock_data(root: str | Path = ROOT) -> None:
    root = Path(root)
    raw = root / "data/raw"
    for path in [raw / "ons", raw / "solar", raw / "eolico", raw / "demanda", raw / "restricoes"]:
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
    substations.to_file(raw / "ons/subestacoes.geojson", driver="GeoJSON")

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
    lines.to_file(raw / "ons/linhas.geojson", driver="GeoJSON")

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
    demand.to_file(raw / "demanda/demanda.geojson", driver="GeoJSON")

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
    restrictions.to_file(raw / "restricoes/restricoes.geojson", driver="GeoJSON")

    width = 120
    height = 120
    x_min, y_max = -60, 5
    pixel = 0.35
    transform = from_origin(x_min, y_max, pixel, pixel)

    rng = np.random.default_rng(42)
    y_indices, x_indices = np.indices((height, width))
    lat = y_max - y_indices * pixel
    lon = x_min + x_indices * pixel

    solar = 4.5 + 2.5 * ((lat + 35) / 40) + 0.3 * rng.normal(size=(height, width))
    wind = 4.0 + 4.0 * np.exp(-((lon + 39) ** 2 + (lat + 9) ** 2) / 160) + 1.0 * rng.random((height, width))

    with rasterio.open(
        raw / "solar/irradiancia_global.tif",
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(solar.astype("float32"), 1)

    with rasterio.open(
        raw / "eolico/velocidade_vento.tif",
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(wind.astype("float32"), 1)


if __name__ == "__main__":
    generate_mock_data()
    print("Dados ficticios gerados com sucesso.")
