import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.generate_mock_data import generate_mock_data
from src.analysis import VALID_SCENARIOS, export_results, run_analysis
from src.config import load_config
from src.visualization import make_folium_map


DATA_PATH_KEYS = [
    "substations",
    "transmission_lines",
    "solar_raster",
    "wind_raster",
    "demand_points",
    "roads",
    "water_resources",
    "urban_areas",
    "slope_raster",
    "land_use_raster",
    "restrictions",
]


config = load_config(ROOT / "config/config.yaml")
required_paths = [ROOT / config["paths"][key] for key in DATA_PATH_KEYS if key in config["paths"]]
if not all(path.exists() for path in required_paths):
    generate_mock_data(ROOT, overwrite=False)

for scenario in [scenario for scenario in config["weights"] if scenario in VALID_SCENARIOS]:
    results = run_analysis(config, scenario=scenario)
    exported = export_results(results, config, scenario)
    make_folium_map(results, output_path=exported["maps_dir"] / f"mapa_{scenario}.html", top_n=100)
    print(f"{scenario}: {len(results)} pontos exportados -> {exported['csv']}")
