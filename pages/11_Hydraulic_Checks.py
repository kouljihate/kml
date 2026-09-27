import streamlit as st

from ui.sidebar import show_project_sidebar


show_project_sidebar()

st.title("6. Hydraulic Checks")

project = st.session_state.farm_project

st.metric(
    "Available source flow",
    f"{project['project']['source_flow_m3h']:.2f} m³/h",
)
