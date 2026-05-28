from pathlib import Path
import geopandas as gpd
import rasterio


def read_vector(path: str | Path, required: bool = True):
    path = Path(path)
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Arquivo vetorial não encontrado: {path}")
        return None
    return gpd.read_file(path)


def read_raster(path: str | Path, required: bool = True):
    path = Path(path)
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Arquivo raster não encontrado: {path}")
        return None
    return rasterio.open(path)


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
