import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from scripts.generate_mock_data import generate_mock_data
from src.analysis import export_results, run_analysis
from src.config import load_config
from src.scoring import normalize_weights
from src.visualization import make_folium_map


def ensure_demo_data(config: dict) -> None:
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


def render_results(results, exported, map_path, fmap, scenario: str) -> None:
    st.success(f"Análise concluída: {len(results)} pontos candidatos válidos.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Melhor score", f"{results['score_final'].max():.3f}")
    c2.metric("Solar médio", f"{results['solar_kwh_m2_day'].mean():.2f}")
    c3.metric("Vento médio", f"{results['wind_m_s'].mean():.2f}")
    c4.metric("Distância média à rede", f"{results['dist_grid_km'].mean():.1f} km")
    c5.metric("Em área restrita", int(results["is_restricted"].sum()))

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.subheader("Distribuição do score")
        st.plotly_chart(
            px.histogram(results, x="score_final", nbins=30, labels={"score_final": "Score final"}),
            width="stretch",
        )
    with chart_cols[1]:
        st.subheader("Top 10 candidatos")
        top10 = results.head(10).copy()
        top10["candidate_id"] = top10["candidate_id"].astype(str)
        st.plotly_chart(
            px.bar(
                top10.sort_values("score_final"),
                x="score_final",
                y="candidate_id",
                orientation="h",
                labels={"score_final": "Score final", "candidate_id": "Candidato"},
            ),
            width="stretch",
        )

    st.subheader("Mapa dos melhores pontos")
    st_folium(fmap, width=None, height=600, returned_objects=[])

    st.subheader("Ranking")
    display_results = results.to_crs("EPSG:4326").copy()
    display_results["longitude"] = display_results.geometry.x
    display_results["latitude"] = display_results.geometry.y
    cols = [
        "rank",
        "candidate_id",
        "latitude",
        "longitude",
        "solar_kwh_m2_day",
        "wind_m_s",
        "dist_grid_km",
        "dist_demand_km",
        "connection_cost_brl",
        "is_restricted",
        "score_final",
    ]
    st.dataframe(display_results[cols].head(100), width="stretch")

    st.download_button(
        "Baixar ranking CSV",
        data=display_results[cols].to_csv(index=False).encode("utf-8"),
        file_name=f"ranking_{scenario}.csv",
        mime="text/csv",
    )

    st.info(f"Arquivos exportados em: {exported['csv']}, {exported['geojson']} e {map_path}")


st.set_page_config(page_title="TCC Energia", layout="wide")
st.title("Localização Ótima de Usinas Renováveis")
st.caption("Análise multicritério geoespacial para fontes solar, eólica e híbrida.")

config = load_config(ROOT / "config/config.yaml")
ensure_demo_data(config)

with st.sidebar:
    st.header("Parâmetros")
    scenario = st.selectbox("Cenário", ["solar", "eolico", "hibrido"], index=2)
    spacing = st.slider("Espaçamento da malha candidata (km)", 10, 150, int(config["analysis"]["grid_spacing_km"]), 10)
    top_n = st.slider("Top N pontos no mapa", 10, 300, 100, 10)

    st.subheader("Restrições ambientais")
    restriction_policy = st.radio(
        "Tratamento",
        ["exclude", "penalize"],
        format_func=lambda value: "Excluir áreas restritas" if value == "exclude" else "Penalizar áreas restritas",
        horizontal=False,
    )
    config.setdefault("thresholds", {})["restriction_policy"] = restriction_policy
    if restriction_policy == "penalize":
        config["thresholds"]["restriction_penalty_factor"] = st.slider("Fator de penalização", 0.0, 1.0, 0.35, 0.05)

    st.subheader("Pesos do cenário")
    weights = config["weights"][scenario].copy()
    for key, value in list(weights.items()):
        weights[key] = st.slider(key, 0.0, 1.0, float(value), 0.05)
    config["weights"][scenario] = weights
    try:
        normalized_weights = normalize_weights(weights)
        st.caption(f"Soma informada: {sum(weights.values()):.2f}. O modelo normaliza automaticamente para 1,00.")
        st.dataframe(
            pd.DataFrame({"critério": list(normalized_weights), "peso_normalizado": list(normalized_weights.values())}),
            hide_index=True,
            width="stretch",
        )
    except ValueError as exc:
        st.warning(str(exc))

    run_btn = st.button("Executar análise", type="primary")

st.markdown(
    """
### Como interpretar
O score final combina potencial de geração, proximidade da rede, proximidade de carga e custo estimado de conexão.
Quanto maior o score, mais atrativo é o ponto candidato.
"""
)

if run_btn:
    with st.spinner("Processando dados geoespaciais..."):
        try:
            results = run_analysis(config, scenario=scenario, grid_spacing_km=spacing)
            exported = export_results(results, config, scenario)
            map_path = exported["maps_dir"] / f"mapa_{scenario}.html"
            fmap = make_folium_map(results, output_path=map_path, top_n=top_n)
            st.session_state["last_results"] = results
            st.session_state["last_exported"] = exported
            st.session_state["last_map_path"] = map_path
            st.session_state["last_fmap"] = fmap
            st.session_state["last_scenario"] = scenario
        except Exception as exc:
            st.error(f"Não foi possível executar a análise: {exc}")
            st.stop()

if "last_results" in st.session_state:
    render_results(
        st.session_state["last_results"],
        st.session_state["last_exported"],
        st.session_state["last_map_path"],
        st.session_state["last_fmap"],
        st.session_state["last_scenario"],
    )
else:
    st.warning("Clique em 'Executar análise' na barra lateral. Se ainda não tiver dados, rode: python scripts/generate_mock_data.py")
