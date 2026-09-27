import pandas as pd
import streamlit as st

from core.project import (
    initialize_project_state,
    save_history_snapshot,
)
from services.tree_service import (
    create_trees_for_all_zones,
    remove_all_trees,
)
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("6. Trees and Zone Water Demand")

project = st.session_state.farm_project

zones = project.get("zones", [])
rows = project.get("rows", [])
trees = project.get("trees", [])

if not zones:
    st.warning(
        "No zones are available yet."
    )
    st.stop()

if not rows:
    st.warning(
        "No planting rows exist yet. "
        "Generate elevation-oriented rows first."
    )
    st.stop()

st.write(
    "Trees are created along the existing elevation-oriented rows. "
    "Their location and future 16 mm dripline direction automatically "
    "follow the recommended angle for each zone."
)

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric(
    "Zones",
    len(zones),
)

metric_col2.metric(
    "Rows",
    len(rows),
)

metric_col3.metric(
    "Existing trees",
    len(trees),
)

st.divider()

st.subheader("Tree and emitter configuration")

config_col1, config_col2 = st.columns(2)

with config_col1:
    crop_type = st.text_input(
        "Crop type",
        value="Orchard",
    )

    tree_spacing_m = st.number_input(
        "Tree spacing on each row (m)",
        min_value=1.0,
        max_value=20.0,
        value=4.0,
        step=0.5,
    )

    end_offset_m = st.number_input(
        "Row-end offset (m)",
        min_value=0.0,
        max_value=20.0,
        value=2.0,
        step=0.5,
    )

with config_col2:
    emitters_per_tree = st.number_input(
        "Emitters per tree",
        min_value=1,
        max_value=10,
        value=2,
        step=1,
    )

    emitter_flow_lph = st.number_input(
        "Emitter flow (L/h)",
        min_value=0.5,
        max_value=20.0,
        value=4.0,
        step=0.5,
    )

    tree_flow_lph = (
        emitters_per_tree
        * emitter_flow_lph
    )

    st.metric(
        "Flow per tree",
        f"{tree_flow_lph:.1f} L/h",
    )

st.divider()

action_col1, action_col2 = st.columns(
    [2, 1],
    gap="medium",
)

with action_col1:
    if st.button(
        "Generate trees for ALL zones",
        type="primary",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before automatic tree generation",
        )

        result = create_trees_for_all_zones(
            project=project,
            tree_spacing_m=tree_spacing_m,
            end_offset_m=end_offset_m,
            crop_type=crop_type,
            emitters_per_tree=emitters_per_tree,
            emitter_flow_lph=emitter_flow_lph,
        )

        st.session_state[
            "tree_batch_result"
        ] = result

        st.rerun()

with action_col2:
    if st.button(
        "Remove ALL trees",
        type="secondary",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before removing all trees",
        )

        result = remove_all_trees(project)

        st.session_state[
            "tree_batch_result"
        ] = result

        st.rerun()

result = st.session_state.get(
    "tree_batch_result"
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

    errors = result.get("errors", [])

    if errors:
        st.error(
            " | ".join(errors)
        )

st.divider()

st.subheader("Zone tree and water-demand summary")

summary_rows = []

for zone in sorted(
    zones,
    key=lambda item: (
        item.get("sector_id", ""),
        item.get("zone_number", 0),
    ),
):
    summary_rows.append({
        "Zone": zone.get("id"),
        "Trees": zone.get(
            "tree_count",
            0,
        ),
        "Tree spacing (m)": tree_spacing_m,
        "Emitters/tree": emitters_per_tree,
        "Emitter L/h": emitter_flow_lph,
        "Zone flow (m³/h)": zone.get(
            "target_flow_m3h",
            0.0,
        ),
    })

st.dataframe(
    pd.DataFrame(summary_rows),
    use_container_width=True,
    hide_index=True,
)

total_trees = len(
    project.get("trees", [])
)

total_flow_m3h = sum(
    zone.get("target_flow_m3h", 0.0)
    for zone in zones
)

st.metric(
    "Total generated trees",
    total_trees,
)

st.metric(
    "Total theoretical flow if all zones run",
    f"{total_flow_m3h:.2f} m³/h",
)

st.info(
    "The total theoretical flow is not the pump requirement. "
    "The hydraulic stage will choose which zones can run together "
    "under your available source flow."
)