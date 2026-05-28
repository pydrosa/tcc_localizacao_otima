import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from src.config import load_config
from src.analysis import run_analysis, export_results
from src.visualization import make_folium_map

st.set_page_config(page_title="TCC Energia", layout="wide")
st.title("Localização Ótima de Usinas Renováveis")
st.caption("Análise multicritério geoespacial para fontes solar, eólica e híbrida.")

config = load_config(ROOT / "config/config.yaml")

with st.sidebar:
    st.header("Parâmetros")
    scenario = st.selectbox("Cenário", ["solar", "eolico", "hibrido"], index=2)
    spacing = st.slider("Espaçamento da malha candidata (km)", 10, 150, int(config["analysis"]["grid_spacing_km"]), 10)
    top_n = st.slider("Top N pontos no mapa", 10, 300, 100, 10)

    st.subheader("Pesos do cenário")
    weights = config["weights"][scenario]
    for key, value in list(weights.items()):
        weights[key] = st.slider(key, 0.0, 1.0, float(value), 0.05)
    config["weights"][scenario] = weights

    run_btn = st.button("Executar análise", type="primary")

st.markdown("""
### Como interpretar
O score final combina potencial de geração, proximidade da rede, proximidade de carga e custo estimado de conexão.
Quanto maior o score, mais atrativo é o ponto candidato.
""")

if run_btn:
    with st.spinner("Processando dados geoespaciais..."):
        results = run_analysis(config, scenario=scenario, grid_spacing_km=spacing)
        exported = export_results(results, config, scenario)
        fmap = make_folium_map(results, top_n=top_n)

    st.success(f"Análise concluída: {len(results)} pontos candidatos válidos.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Melhor score", f"{results['score_final'].max():.3f}")
    c2.metric("Solar médio", f"{results['solar_kwh_m2_day'].mean():.2f}")
    c3.metric("Vento médio", f"{results['wind_m_s'].mean():.2f}")
    c4.metric("Distância média à rede", f"{results['dist_grid_km'].mean():.1f} km")

    st.subheader("Mapa dos melhores pontos")
    st_folium(fmap, width=None, height=600)

    st.subheader("Ranking")
    cols = ["rank", "candidate_id", "solar_kwh_m2_day", "wind_m_s", "dist_grid_km", "dist_demand_km", "connection_cost_brl", "score_final"]
    st.dataframe(results[cols].head(100), use_container_width=True)

    st.download_button(
        "Baixar ranking CSV",
        data=results[cols].to_csv(index=False).encode("utf-8"),
        file_name=f"ranking_{scenario}.csv",
        mime="text/csv",
    )

    st.info(f"Arquivos exportados em: {exported['csv']} e {exported['geojson']}")
else:
    st.warning("Clique em 'Executar análise' na barra lateral. Se ainda não tiver dados, rode: python scripts/generate_mock_data.py")
