import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.config import load_config
from src.analysis import run_analysis, export_results
from src.visualization import make_folium_map
from scripts.generate_mock_data import generate_mock_data

config = load_config(ROOT / "config/config.yaml")
required_paths = [
    ROOT / config["paths"]["substations"],
    ROOT / config["paths"]["transmission_lines"],
    ROOT / config["paths"]["solar_raster"],
    ROOT / config["paths"]["wind_raster"],
    ROOT / config["paths"]["demand_points"],
    ROOT / config["paths"]["restrictions"],
]
if not all(path.exists() for path in required_paths):
    generate_mock_data(ROOT)

for scenario in ["solar", "eolico", "hibrido"]:
    results = run_analysis(config, scenario=scenario)
    exported = export_results(results, config, scenario)
    make_folium_map(results, output_path=exported["maps_dir"] / f"mapa_{scenario}.html", top_n=100)
    print(f"{scenario}: {len(results)} pontos exportados -> {exported['csv']}")
