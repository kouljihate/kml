from core.project import project_to_json
import streamlit as st

from core.project import (
    create_empty_project,
    initialize_project_state,
    project_to_json,
)
from services.project_storage_service import (
    delete_project,
    list_saved_projects,
    load_project,
    save_project,
)
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("0. Save and Load Project")

st.write(
    "Save your irrigation-design project before continuing. "
    "This stores land, sectors, zones, rows, trees, pipes, valves, "
    "and all other project data as JSON."
)

project = st.session_state.farm_project

st.subheader("Current project")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Sectors",
    len(project.get("sectors", [])),
)

col2.metric(
    "Zones",
    len(project.get("zones", [])),
)

col3.metric(
    "Trees",
    len(project.get("trees", [])),
)

col4.metric(
    "Pipes",
    len(project.get("pipes", [])),
)

project_name = st.text_input(
    "Project save name",
    value=project["project"]["name"],
    help=(
        "Example: Dhar Irrigation September 2026. "
        "The application converts this into a safe JSON filename."
    ),
)

save_col1, save_col2 = st.columns(
    [2, 1],
    gap="medium",
)

with save_col1:
    if st.button(
        "Save current project",
        type="primary",
        use_container_width=True,
    ):
        project["project"]["name"] = project_name

        result = save_project(
            project=project,
            project_name=project_name,
        )

        if result["ok"]:
            st.success(
                f"{result['message']} File: "
                f"{result['file_name']}"
            )
        else:
            st.error(
                result["message"]
            )

with save_col2:
    if st.button(
        "Create new empty project",
        type="secondary",
        use_container_width=True,
    ):
        st.session_state.farm_project = (
            create_empty_project()
        )

        st.success(
            "New empty project created."
        )

        st.rerun()

st.divider()

st.subheader("Saved projects")

saved_projects = list_saved_projects()

if not saved_projects:
    st.info(
        "No saved project files yet. "
        "Save the current project first."
    )

else:
    project_options = {
        (
            f"{item['project_name']} | "
            f"{item['file_name']}"
        ): item
        for item in saved_projects
    }

    selected_label = st.selectbox(
        "Select saved project",
        options=list(project_options.keys()),
    )

    selected_project = project_options[
        selected_label
    ]

    st.write(
        f"Selected file: "
        f"`{selected_project['file_name']}`"
    )

    if selected_project.get("saved_utc"):
        st.caption(
            f"Saved: "
            f"{selected_project['saved_utc']}"
        )

    load_col1, load_col2 = st.columns(
        [2, 1],
        gap="medium",
    )

    with load_col1:
        if st.button(
            "Load selected project",
            type="primary",
            use_container_width=True,
        ):
            result = load_project(
                selected_project["file_name"]
            )

            if result["ok"]:
                st.session_state.farm_project = (
                    result["project"]
                )

                st.success(
                    result["message"]
                )

                st.rerun()

            else:
                st.error(
                    result["message"]
                )

    with load_col2:
        if st.button(
            "Delete selected project",
            type="secondary",
            use_container_width=True,
        ):
            result = delete_project(
                selected_project["file_name"]
            )

            if result["ok"]:
                st.success(
                    result["message"]
                )

                st.rerun()

            else:
                st.error(
                    result["message"]
                )

st.divider()

st.subheader("Portable project backup")

st.download_button(
    label="Download current project JSON",
    data=project_to_json(
        st.session_state.farm_project
    ),
    file_name="farm_irrigation_project.json",
    mime="application/json",
    use_container_width=True,
)