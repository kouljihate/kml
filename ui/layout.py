import streamlit as st


def show_project_header(project):
    project_name = project["project"]["name"]
    flow = project["project"]["source_flow_m3h"]

    st.markdown(
        "<div style='padding: 0.8rem 1rem; border-radius: 0.6rem; "
        "background: #0f766e; color: white; margin-bottom: 1rem;'>"
        "<h2 style='margin: 0;'>💧 " + project_name + "</h2>"
        "<small>Source flow: " + str(flow) + " m³/h</small>"
        "</div>",
        unsafe_allow_html=True,
    )
