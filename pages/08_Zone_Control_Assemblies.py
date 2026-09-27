import pandas as pd
import streamlit as st

from core.project import (
    initialize_project_state,
    save_history_snapshot,
)
from services.manifold_service import (
    create_control_assemblies_for_all_zones,
    migrate_zone_valve_ids,
)
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("8. Zone Valves and 32 mm Manifolds")

project = st.session_state.farm_project

migration_result = migrate_zone_valve_ids(
    project
)

if migration_result.get("renamed_valves"):
    st.success(
        migration_result["message"]
    )

zones = project.get("zones", [])
driplines = [
    pipe
    for pipe in project.get("pipes", [])
    if pipe.get("pipe_type") == "dripline"
]

if not zones:
    st.warning(
        "Create irrigation zones first."
    )
    st.stop()

if not driplines:
    st.warning(
        "Create 16 mm driplines first."
    )
    st.stop()

st.write(
    "This page creates one control assembly for each zone: "
    "zone valve, pressure-regulated filtration position, "
    "63 × 32 mm reducer, and 32 mm manifold."
)

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric(
    "Zones",
    len(zones),
)

metric_col2.metric(
    "Zone valves",
    len(project.get("valves", [])),
)

metric_col3.metric(
    "32 mm manifolds",
    len([
        pipe
        for pipe in project.get("pipes", [])
        if pipe.get("pipe_type")
        == "manifold_32"
    ]),
)

st.divider()

st.info(
    "The current page stores the control components and their "
    "relationships. Exact manifold route geometry will be added "
    "after the 63 mm sector branches are created."
)

if st.button(
    "Create valves and 32 mm manifolds for ALL zones",
    type="primary",
    use_container_width=True,
):
    save_history_snapshot(
        st.session_state,
        "Before creating zone control assemblies",
    )

    result = create_control_assemblies_for_all_zones(
        project
    )

    st.session_state[
        "control_assembly_result"
    ] = result

    st.rerun()

result = st.session_state.get(
    "control_assembly_result"
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

    errors = result.get(
        "errors",
        [],
    )

    if errors:
        st.error(
            " | ".join(errors)
        )

st.divider()

st.subheader("Zone control assembly table")

table_rows = []

for zone in sorted(
    zones,
    key=lambda item: (
        item.get("sector_id", ""),
        item.get("zone_number", 0),
    ),
):
    zone_id = zone.get("id")

    zone_valves = [
        valve
        for valve in project.get("valves", [])
        if valve.get("zone_id") == zone_id
    ]

    zone_manifolds = [
        pipe
        for pipe in project.get("pipes", [])
        if pipe.get("zone_id") == zone_id
        and pipe.get("pipe_type")
        == "manifold_32"
    ]

    zone_driplines = [
        pipe
        for pipe in project.get("pipes", [])
        if pipe.get("zone_id") == zone_id
        and pipe.get("pipe_type")
        == "dripline"
    ]

    table_rows.append({
        "Zone": zone_id,
        "Valve": (
            zone_valves[0]["id"]
            if zone_valves
            else "Missing"
        ),
        "Manifold": (
            zone_manifolds[0]["id"]
            if zone_manifolds
            else "Missing"
        ),
        "16 mm outlets": len(
            zone_driplines
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

st.divider()

st.subheader("Installation order per zone")

st.code(
    "63 mm branch\n"
    "  → 63×32 mm reducer tee\n"
    "  → isolation/control valve\n"
    "  → filter\n"
    "  → pressure regulator\n"
    "  → 32 mm manifold\n"
    "  → 16 mm dripline outlets",
    language="text",
)