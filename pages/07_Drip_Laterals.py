import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core.project import (
    initialize_project_state,
    save_history_snapshot,
)
from services.dripline_service import (
    create_driplines_for_all_zones,
    remove_all_driplines,
)
from services.map_service import build_project_map
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("7. 16 mm Drip Laterals")

project = st.session_state.farm_project

zones = project.get("zones", [])
rows = project.get("rows", [])
trees = project.get("trees", [])

driplines = [
    pipe
    for pipe in project.get("pipes", [])
    if pipe.get("pipe_type") == "dripline"
]

if not zones:
    st.warning(
        "No irrigation zones exist yet."
    )
    st.stop()

if not rows:
    st.warning(
        "No planting rows exist yet. "
        "Generate rows first."
    )
    st.stop()

if not trees:
    st.warning(
        "No trees exist yet. "
        "Generate trees before driplines."
    )
    st.stop()

st.write(
    "Each 16 mm dripline follows one planting row. "
    "It supplies the trees positioned on that row."
)

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric(
    "Zones",
    len(zones),
)

metric_col2.metric(
    "Planting rows",
    len(rows),
)

metric_col3.metric(
    "Existing 16 mm driplines",
    len(driplines),
)

st.divider()

st.subheader("Dripline configuration")

config_col1, config_col2 = st.columns(2)

with config_col1:
    diameter_mm = st.selectbox(
        "Dripline diameter",
        options=[16],
        format_func=lambda value: (
            f"{value} mm"
        ),
    )

with config_col2:
    material = st.selectbox(
        "Material",
        options=["LDPE", "PE"],
    )

st.info(
    "Each generated dripline includes a future start connector "
    "at the 32 mm manifold and a future flush/end fitting."
)

action_col1, action_col2 = st.columns(
    [2, 1],
    gap="medium",
)

with action_col1:
    if st.button(
        "Generate 16 mm driplines for ALL zones",
        type="primary",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before automatic dripline generation",
        )

        result = create_driplines_for_all_zones(
            project=project,
            diameter_mm=diameter_mm,
            material=material,
        )

        st.session_state[
            "dripline_batch_result"
        ] = result

        st.rerun()

with action_col2:
    if st.button(
        "Remove ALL driplines",
        type="secondary",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before removing all driplines",
        )

        result = remove_all_driplines(
            project
        )

        st.session_state[
            "dripline_batch_result"
        ] = result

        st.rerun()

result = st.session_state.get(
    "dripline_batch_result"
)

if result:
    if result.get("ok"):
        st.success(
            result.get("message", "")
        )
    else:
        st.warning(
            result.get("message", "")
        )

    if result.get("total_length_m") is not None:
        st.metric(
            "New 16 mm dripline length",
            f"{result['total_length_m']:.1f} m",
        )

    errors = result.get("errors", [])

    if errors:
        st.error(
            " | ".join(errors)
        )

st.divider()

st.subheader("Dripline map")

st.info(
    "Enable the Pipes map layer. "
    "The 16 mm driplines appear as thin grey lines."
)

farm_map = build_project_map(
    project
)

st_folium(
    farm_map,
    key="dripline_map",
    height=720,
    use_container_width=True,
)

st.divider()

st.subheader("Dripline quantities by zone")

table_rows = []

for zone in sorted(
    zones,
    key=lambda item: (
        item.get("sector_id", ""),
        item.get("zone_number", 0),
    ),
):
    table_rows.append({
        "Zone": zone.get("id"),
        "Driplines": zone.get(
            "dripline_count",
            0,
        ),
        "16 mm length (m)": zone.get(
            "dripline_length_m",
            0.0,
        ),
        "Trees": zone.get(
            "tree_count",
            0,
        ),
        "Zone flow (m³/h)": zone.get(
            "target_flow_m3h",
            0.0,
        ),
    })

st.dataframe(
    pd.DataFrame(table_rows),
    use_container_width=True,
    hide_index=True,
)