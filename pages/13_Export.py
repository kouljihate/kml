import streamlit as st

from core.project import project_to_json
from exporters.geojson_exporter import export_geojson
from exporters.kml_exporter import export_kml
from ui.sidebar import show_project_sidebar


show_project_sidebar()

st.title("8. Export")

project = st.session_state.farm_project

st.download_button(
    "Download project JSON",
    data=project_to_json(project),
    file_name="farm_irrigation_project.json",
    mime="application/json",
)

st.download_button(
    "Download GeoJSON",
    data=export_geojson(project),
    file_name="farm_irrigation_project.geojson",
    mime="application/geo+json",
)

st.download_button(
    "Download KML",
    data=export_kml(project),
    file_name="farm_irrigation_project.kml",
    mime="application/vnd.google-earth.kml+xml",
)
