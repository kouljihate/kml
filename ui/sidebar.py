import streamlit as st

from core.project import initialize_project_state


def show_project_sidebar():
    initialize_project_state(
        st.session_state
    )

    project = st.session_state.farm_project

    st.sidebar.title("Farm Project")

    project["project"]["name"] = st.sidebar.text_input(
        "Project name",
        value=project["project"]["name"],
        key="sidebar_project_name",
    )

    project["project"]["source_flow_m3h"] = st.sidebar.number_input(
        "Available source flow (m³/h)",
        min_value=0.1,
        step=0.5,
        value=float(
            project["project"]["source_flow_m3h"]
        ),
        key="sidebar_source_flow",
    )

    st.sidebar.divider()

    st.sidebar.subheader("Design status")

    checks = [
        (
            "Land boundary",
            project["land"] is not None,
        ),
        (
            "Water point",
            len(project["water_points"]) > 0,
        ),
        (
            "Basin",
            len(project["basins"]) > 0,
        ),
        (
            "Sectors",
            len(project["sectors"]) > 0,
        ),
        (
            "Zones",
            len(project["zones"]) > 0,
        ),
        (
            "Rows",
            len(project["rows"]) > 0,
        ),
        (
            "Trees",
            len(project["trees"]) > 0,
        ),
        (
            "Pipes",
            len(project["pipes"]) > 0,
        ),
        (
            "Valves",
            len(project["valves"]) > 0,
        ),
    ]

    for label, complete in checks:
        icon = "✅" if complete else "⬜"
        st.sidebar.write(
            f"{icon} {label}"
        )

    st.sidebar.divider()

    st.sidebar.caption(
        "Project data currently exists in Streamlit session memory. "
        "Use Export to save a JSON project backup."
    )