from pathlib import Path

import folium
import geopandas as gpd
from folium.plugins import MarkerCluster


def make_folium_map(results: gpd.GeoDataFrame, output_path: str | Path | None = None, top_n: int = 100):
    gdf = results.head(top_n).to_crs("EPSG:4326").copy()
    if gdf.empty:
        raise ValueError("Resultado vazio para visualização.")

    center = [gdf.geometry.y.mean(), gdf.geometry.x.mean()]
    m = folium.Map(location=center, zoom_start=5, tiles="CartoDB positron")
    cluster = MarkerCluster().add_to(m)

    for _, row in gdf.iterrows():
        popup = f"""
        <b>Rank:</b> {row['rank']}<br>
        <b>Classe:</b> {row['aptitude_class']}/9<br>
        <b>Score:</b> {row['score_final']:.3f}<br>
        <b>Solar:</b> {row['solar_kwh_m2_day']:.2f} kWh/m².dia<br>
        <b>Vento:</b> {row['wind_m_s']:.2f} m/s<br>
        <b>Dist. rede:</b> {row['dist_grid_km']:.1f} km<br>
        <b>Dist. rodovia:</b> {row['dist_road_km']:.1f} km<br>
        <b>Dist. demanda:</b> {row['dist_demand_km']:.1f} km<br>
        <b>Custo infraestrutura:</b> R$ {row['infrastructure_cost_brl']:,.0f}
        """
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=7,
            fill=True,
            fill_opacity=0.75,
            popup=folium.Popup(popup, max_width=320),
        ).add_to(cluster)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        m.save(output_path)
    return m
