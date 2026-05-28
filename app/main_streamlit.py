import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from scripts.generate_mock_data import generate_mock_data
from src.analysis import VALID_SCENARIOS, export_results, run_analysis
from src.config import load_config
from src.scoring import normalize_weights
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

SCENARIO_LABELS = {
    "solar": "Solar",
    "eolico": "Eólico",
    "hibrido": "Híbrido",
    "infraestrutura": "Infraestrutura",
    "ambiental": "Ambiental",
}

CRITERION_LABELS = {
    "solar_potential": "Potencial solar",
    "wind_potential": "Potencial eólico",
    "grid_distance": "Proximidade da rede",
    "demand_distance": "Proximidade da demanda",
    "road_distance": "Acesso rodoviário",
    "water_distance": "Acesso hídrico",
    "urban_distance": "Afastamento urbano",
    "slope": "Declividade",
    "land_use": "Aptidão do uso do solo",
    "connection_cost": "Custo de infraestrutura",
}

MAP_MODE_LABELS = {
    "points": "Pontos",
    "heatmap": "Mapa de calor",
}


def ensure_demo_data(config: dict) -> None:
    required_paths = [ROOT / config["paths"][key] for key in DATA_PATH_KEYS if key in config["paths"]]
    if not all(path.exists() for path in required_paths):
        generate_mock_data(ROOT, overwrite=False)


def _selection_rows(selection_event) -> list[int]:
    try:
        return list(selection_event.selection.rows)
    except AttributeError:
        return []


def _format_ranking(results, top_n: int) -> pd.DataFrame:
    display_results = results.head(top_n).to_crs("EPSG:4326").copy()
    display_results["longitude"] = display_results.geometry.x
    display_results["latitude"] = display_results.geometry.y
    return display_results[
        [
            "rank",
            "candidate_id",
            "aptitude_class",
            "score_final",
            "solar_kwh_m2_day",
            "wind_m_s",
            "slope_percent",
            "dist_grid_km",
            "dist_road_km",
            "dist_water_km",
            "dist_urban_km",
            "dist_demand_km",
            "infrastructure_cost_brl",
            "latitude",
            "longitude",
        ]
    ].copy()


def _selected_candidate_id(ranking: pd.DataFrame, selection_event) -> int:
    selected_id = int(ranking.iloc[0]["candidate_id"])
    selected_rows = _selection_rows(selection_event)
    if selected_rows and selected_rows[0] < len(ranking):
        selected_id = int(ranking.iloc[selected_rows[0]]["candidate_id"])

    valid_ids = set(ranking["candidate_id"].astype(int))
    if selected_id not in valid_ids:
        selected_id = int(ranking.iloc[0]["candidate_id"])
    st.session_state["selected_candidate_id"] = selected_id
    return selected_id


def _ranking_map(ranking: pd.DataFrame, selected_candidate_id: int, map_mode: str) -> pdk.Deck:
    map_data = ranking.copy()
    map_data["is_selected"] = map_data["candidate_id"].astype(int) == selected_candidate_id
    selected = map_data[map_data["is_selected"]]
    base = map_data[~map_data["is_selected"]]

    if map_mode == "heatmap":
        layers = [
            pdk.Layer(
                "HeatmapLayer",
                data=map_data,
                get_position="[longitude, latitude]",
                get_weight="score_final",
                aggregation="SUM",
                radiusPixels=55,
                intensity=1.3,
                threshold=0.04,
                pickable=False,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=selected,
                get_position="[longitude, latitude]",
                get_radius=65000,
                get_fill_color="[220, 38, 38, 230]",
                get_line_color="[255, 255, 255, 240]",
                get_line_width=7000,
                stroked=True,
                pickable=True,
            ),
        ]
    else:
        layers = [
            pdk.Layer(
                "ScatterplotLayer",
                data=base,
                get_position="[longitude, latitude]",
                get_radius=24000,
                get_fill_color="[37, 99, 235, 145]",
                pickable=True,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=selected,
                get_position="[longitude, latitude]",
                get_radius=70000,
                get_fill_color="[220, 38, 38, 230]",
                get_line_color="[255, 255, 255, 240]",
                get_line_width=7000,
                stroked=True,
                pickable=True,
            ),
        ]

    center = selected.iloc[0] if not selected.empty else map_data.iloc[0]
    return pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=float(center["latitude"]),
            longitude=float(center["longitude"]),
            zoom=4.2,
            pitch=0,
        ),
        layers=layers,
        tooltip={
            "html": (
                "<b>Rank:</b> {rank}<br/>"
                "<b>Score:</b> {score_final}<br/>"
                "<b>Classe:</b> {aptitude_class}/9<br/>"
                "<b>Solar:</b> {solar_kwh_m2_day} kWh/m².dia<br/>"
                "<b>Vento:</b> {wind_m_s} m/s"
            )
        },
    )


def render_results(results, exported, map_path, scenario: str, top_n: int, map_mode: str) -> None:
    st.success(f"Análise concluída: {len(results)} pontos candidatos válidos.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Melhor score", f"{results['score_final'].max():.3f}")
    c2.metric("Classe máxima", f"{int(results['aptitude_class'].max())}/9")
    c3.metric("Solar médio", f"{results['solar_kwh_m2_day'].mean():.2f}")
    c4.metric("Vento médio", f"{results['wind_m_s'].mean():.2f}")
    c5.metric("Distância média à rede", f"{results['dist_grid_km'].mean():.1f} km")

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

    ranking = _format_ranking(results, top_n)

    st.subheader("Ranking")
    ranking_event = st.dataframe(
        ranking,
        hide_index=True,
        width="stretch",
        key="ranking_table",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "rank": st.column_config.NumberColumn("Rank", format="%d"),
            "candidate_id": st.column_config.NumberColumn("Candidato", format="%d"),
            "aptitude_class": st.column_config.NumberColumn("Classe", format="%d"),
            "score_final": st.column_config.NumberColumn("Score", format="%.3f"),
            "solar_kwh_m2_day": st.column_config.NumberColumn("Solar", format="%.2f"),
            "wind_m_s": st.column_config.NumberColumn("Vento", format="%.2f"),
            "slope_percent": st.column_config.NumberColumn("Declividade", format="%.2f"),
            "dist_grid_km": st.column_config.NumberColumn("Rede km", format="%.1f"),
            "dist_road_km": st.column_config.NumberColumn("Rodovia km", format="%.1f"),
            "dist_water_km": st.column_config.NumberColumn("Água km", format="%.1f"),
            "dist_urban_km": st.column_config.NumberColumn("Urbano km", format="%.1f"),
            "dist_demand_km": st.column_config.NumberColumn("Demanda km", format="%.1f"),
            "infrastructure_cost_brl": st.column_config.NumberColumn("Custo infra", format="R$ %.0f"),
            "latitude": st.column_config.NumberColumn("Latitude", format="%.5f"),
            "longitude": st.column_config.NumberColumn("Longitude", format="%.5f"),
        },
    )

    selected_id = _selected_candidate_id(ranking, ranking_event)
    selected_row = ranking[ranking["candidate_id"].astype(int) == selected_id].iloc[0]

    st.subheader(f"Mapa dos melhores pontos - {MAP_MODE_LABELS[map_mode]}")
    st.pydeck_chart(_ranking_map(ranking, selected_id, map_mode), height=620)
    st.caption(
        f"Ponto destacado: candidato {selected_id} | rank {int(selected_row['rank'])} | "
        f"score {selected_row['score_final']:.3f}"
    )

    st.download_button(
        "Baixar ranking CSV",
        data=_format_ranking(results, len(results)).to_csv(index=False).encode("utf-8"),
        file_name=f"ranking_{scenario}.csv",
        mime="text/csv",
    )

    st.info(f"Arquivos exportados em: {exported['csv']}, {exported['geojson']} e {map_path}")


def render_methodology(config: dict) -> None:
    st.divider()
    st.header("Metodologia e parâmetros")

    st.markdown(
        """
Este aplicativo usa uma análise multicritério geoespacial baseada em WLC
(*Weighted Linear Combination*). A lógica é compatível com estudos SIG/AHP:
cada critério é transformado para uma escala comum entre 0 e 1, recebe um peso
normalizado e entra na soma ponderada final.

```text
score = soma(peso_normalizado_i * criterio_i) * fator_restricao
```

O resultado é uma pontuação contínua entre 0 e 1 e uma classe de aptidão de 1 a 9.
Quanto maior o score e a classe, mais atrativo é o ponto candidato.
"""
    )

    st.subheader("Parâmetros de execução")
    st.markdown(
        f"""
- **Cenário**: altera a importância relativa dos critérios. O cenário híbrido é o principal quando o objetivo é considerar solar e eólica simultaneamente.
- **Espaçamento da malha candidata**: define a distância entre os pontos avaliados. Valores menores aumentam o detalhe espacial e também o tempo de processamento.
- **Top N pontos no mapa**: limita quantos candidatos aparecem na visualização. O ranking completo continua disponível no CSV.
- **Tratamento das restrições**: `exclude` remove pontos em áreas restritas; `penalize` mantém o ponto, mas reduz o score pelo fator configurado.
- **CRS projetado**: `{config["analysis"].get("crs_projected", "EPSG:5880")}` é usado para cálculo de distâncias em metros.
"""
    )

    st.subheader("Critérios do score")
    st.markdown(
        """
- **Potencial solar**: irradiância solar diária no ponto. Quanto maior, melhor.
- **Potencial eólico**: velocidade média do vento no ponto. Quanto maior, melhor.
- **Proximidade da rede**: distância até subestações ou linhas de transmissão. Quanto menor, melhor.
- **Proximidade da demanda**: distância até centros de carga. Quanto menor, melhor.
- **Acesso rodoviário**: distância até rodovias. Quanto menor, melhor para implantação, operação e manutenção.
- **Acesso hídrico**: distância até recursos hídricos. Pode ser relevante para obras, limpeza, operação ou condicionantes locais.
- **Afastamento urbano**: distância até áreas urbanas. Quanto maior dentro da faixa configurada, menor o conflito de uso.
- **Declividade**: inclinação do terreno. Quanto menor, melhor para reduzir complexidade construtiva.
- **Aptidão do uso do solo**: indicador raster de adequação territorial. Quanto maior, melhor.
- **Custo de infraestrutura**: estimativa simplificada a partir de distâncias à rede, rodovias e água. Nos cenários padrão, esse peso fica zerado para não duplicar o efeito das distâncias que já compõem o custo.
"""
    )

    fuzzy_rows = []
    for key, bounds in config.get("fuzzy", {}).items():
        fuzzy_rows.append(
            {
                "critério": CRITERION_LABELS.get(key, key),
                "limite_inferior": bounds.get("lower"),
                "limite_superior": bounds.get("upper"),
            }
        )
    if fuzzy_rows:
        st.subheader("Faixas fuzzy")
        st.dataframe(pd.DataFrame(fuzzy_rows), hide_index=True, width="stretch")

    st.subheader("Interpretação dos pesos")
    st.markdown(
        """
Os pesos informados na barra lateral não precisam somar exatamente 1. O modelo normaliza automaticamente a soma antes de calcular o score. Assim, aumentar um peso aumenta a importância relativa daquele critério em relação aos demais.

Na prática:

- cenário **solar** favorece irradiância e viabilidade territorial;
- cenário **eólico** favorece vento e viabilidade territorial;
- cenário **híbrido** equilibra solar, vento e infraestrutura;
- cenário **infraestrutura** favorece conexão, demanda e acesso;
- cenário **ambiental** favorece menor conflito territorial e topográfico.
"""
    )

    st.subheader("Visualização do mapa")
    st.markdown(
        """
- **Pontos**: mostra os candidatos individualmente e destaca em vermelho o item selecionado no ranking.
- **Mapa de calor**: agrega os candidatos por intensidade espacial, usando o `score_final` como peso. Áreas mais quentes indicam concentração de candidatos com boa pontuação.
"""
    )


st.set_page_config(page_title="TCC Energia", layout="wide")
st.title("Localização Ótima de Usinas Renováveis")
st.caption("Análise multicritério geoespacial para fontes solar, eólica e híbrida.")

config = load_config(ROOT / "config/config.yaml")
ensure_demo_data(config)

with st.sidebar:
    st.header("Parâmetros")
    scenario_options = [scenario for scenario in config["weights"] if scenario in VALID_SCENARIOS]
    default_scenario = config["analysis"].get("default_scenario", "hibrido")
    default_index = scenario_options.index(default_scenario) if default_scenario in scenario_options else 0
    scenario = st.selectbox(
        "Cenário",
        scenario_options,
        index=default_index,
        format_func=lambda value: SCENARIO_LABELS.get(value, value.title()),
    )
    spacing = st.slider("Espaçamento da malha candidata (km)", 10, 150, int(config["analysis"]["grid_spacing_km"]), 10)
    top_n = st.slider("Top N pontos no mapa", 10, 300, 100, 10)
    map_mode = st.radio(
        "Tipo de mapa",
        options=["points", "heatmap"],
        index=0,
        format_func=lambda value: MAP_MODE_LABELS[value],
        horizontal=True,
    )
    map_mode = map_mode or "points"

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
        weights[key] = st.slider(CRITERION_LABELS.get(key, key), 0.0, 1.0, float(value), 0.05)
    config["weights"][scenario] = weights
    try:
        normalized_weights = normalize_weights(weights)
        st.caption(f"Soma informada: {sum(weights.values()):.2f}. O modelo normaliza automaticamente para 1,00.")
        st.dataframe(
            pd.DataFrame(
                {
                    "critério": [CRITERION_LABELS.get(key, key) for key in normalized_weights],
                    "peso_normalizado": list(normalized_weights.values()),
                }
            ),
            hide_index=True,
            width="stretch",
        )
    except ValueError as exc:
        st.warning(str(exc))

    run_btn = st.button("Executar análise", type="primary")

if run_btn:
    with st.spinner("Processando dados geoespaciais..."):
        try:
            results = run_analysis(config, scenario=scenario, grid_spacing_km=spacing)
            exported = export_results(results, config, scenario)
            map_path = exported["maps_dir"] / f"mapa_{scenario}.html"
            make_folium_map(results, output_path=map_path, top_n=top_n)
            st.session_state["last_results"] = results
            st.session_state["last_exported"] = exported
            st.session_state["last_map_path"] = map_path
            st.session_state["last_scenario"] = scenario
        except Exception as exc:
            st.error(f"Não foi possível executar a análise: {exc}")
            st.stop()

if "last_results" in st.session_state:
    render_results(
        st.session_state["last_results"],
        st.session_state["last_exported"],
        st.session_state["last_map_path"],
        st.session_state["last_scenario"],
        top_n,
        map_mode,
    )
else:
    st.warning("Nenhuma análise executada nesta sessão.")

render_methodology(config)
