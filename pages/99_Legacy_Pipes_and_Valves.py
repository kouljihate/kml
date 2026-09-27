import streamlit as st

from core.constants import PIPE_TYPES
from ui.sidebar import show_project_sidebar


show_project_sidebar()

st.title("5. Pipes and Valves")

pipe_type_key = st.selectbox(
    "Pipe type",
    options=list(PIPE_TYPES.keys()),
    format_func=lambda key: PIPE_TYPES[key]["name"],
)

pipe_type = PIPE_TYPES[pipe_type_key]

st.write(f"Selected pipe: {pipe_type['name']}")
st.write(f"Diameter: {pipe_type['diameter_mm']} mm")
