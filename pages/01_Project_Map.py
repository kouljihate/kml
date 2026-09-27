import streamlit as st
from streamlit_folium import st_folium

from core.project import save_history_snapshot
from services.kml_service import import_kml_to_project
from services.map_service import build_project_map
from ui.sidebar import show_project_sidebar


show_project_sidebar()

st.title("1. Project Map and KML Import")

st.success("NEW KML MAP PAGE IS ACTIVE")

uploaded_kml = st.file_uploader(
    "Upload farm KML",
    type=["kml"],
)

if uploaded_kml is not None:
    st.success(f"Selected file: {uploaded_kml.name}")

    if st.button(
        "Import KML to project map",
        type="primary",
        use_container_width=True,
    ):
        try:
            save_history_snapshot(
                st.session_state,
                "Before KML import",
            )

            result = import_kml_to_project(
                project=st.session_state.farm_project,
                kml_bytes=uploaded_kml.getvalue(),
            )

            st.success(result["message"])

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total features",
                result["feature_count"],
            )

            col2.metric(
                "Points",
                result["point_count"],
            )

            col3.metric(
                "Lines",
                result["line_count"],
            )

            col4.metric(
                "Polygons",
                result["polygon_count"],
            )

        except Exception as exc:
            st.error(f"KML import failed: {exc}")

st.divider()

st.subheader("Farm map")

features = st.session_state.farm_project.get(
    "kml_features",
    [],
)

if not features:
    st.warning(
        "No KML features imported yet. "
        "Upload the KML and click the blue import button."
    )

farm_map = build_project_map(
    st.session_state.farm_project,
)

st_folium(
    farm_map,
    key="farm_project_map",
    height=720,
    use_container_width=True,
)

st.subheader("Imported KML objects")

for feature in st.session_state.farm_project.get(
    "kml_features",
    [],
):
    st.write(
        feature["geometry"]["type"],
        " | ",
        feature["name"],
        " | ",
        feature["id"],
    )