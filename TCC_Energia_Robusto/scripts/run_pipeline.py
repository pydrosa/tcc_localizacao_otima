from src.config import load_config
from src.analysis import run_analysis, export_results
from src.visualization import make_folium_map

config = load_config("config/config.yaml")
for scenario in ["solar", "eolico", "hibrido"]:
    results = run_analysis(config, scenario=scenario)
    exported = export_results(results, config, scenario)
    make_folium_map(results, output_path=f"outputs/maps/mapa_{scenario}.html", top_n=100)
    print(f"{scenario}: {len(results)} pontos exportados -> {exported['csv']}")
