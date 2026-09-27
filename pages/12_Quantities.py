import streamlit as st

from services.quantity_service import build_project_summary
from ui.sidebar import show_project_sidebar


show_project_sidebar()

st.title("7. Quantities and Bill of Materials")

summary = build_project_summary(st.session_state.farm_project)

st.json(summary)
