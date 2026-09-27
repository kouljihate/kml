import streamlit as st

from core.project import initialize_project_state
from ui.layout import show_project_header
from ui.sidebar import show_project_sidebar


st.set_page_config(
    page_title="Farm Irrigation Designer",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_project_state(st.session_state)

show_project_header(st.session_state.farm_project)
show_project_sidebar()

st.title("Farm Irrigation Designer")

st.info(
    "Use the pages in the left menu to build the project in order: "
    "Project Map → Land and Sectors → Zones → Rows and Trees → "
    "Pipes and Valves → Hydraulic Checks → Quantities → Export."
)
