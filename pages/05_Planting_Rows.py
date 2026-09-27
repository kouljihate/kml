import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core.project import (
    initialize_project_state,
    save_history_snapshot,
)
from services.map_service import build_project_map
from services.row_service import (
    create_rows_for_all_zones,
    remove_all_rows,
)
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("4. Planting Rows")

project = st.session_state.farm_project

zones = project.get("zones", [])
rows = project.get("rows", [])

if not zones:
    st.warning(
        "No irrigation zones exist yet. "
        "Create the zones first."
    )
    st.stop()

st.write(
    "Rows are generated using the elevation-based recommended "
    "angle calculated separately for each zone."
)

analysed_zones = [
    zone
    for zone in zones
    if zone.get(
        "recommended_row_angle_degrees"
    ) is not None
]

not_analysed_zones = [
    zone
    for zone in zones
    if zone.get(
        "recommended_row_angle_degrees"
    ) is None
]

summary_col1, summary_col2, summary_col3 = st.columns(3)

summary_col1.metric(
    "Total zones",
    len(zones),
)

summary_col2.metric(
    "Elevation-analysed zones",
    len(analysed_zones),
)

summary_col3.metric(
    "Existing rows",
    len(rows),
)

if not not_analysed_zones:
    st.success(
        "All zones have an elevation-based row angle."
    )
else:
    missing_ids = [
        zone.get("id")
        for zone in not_analysed_zones
    ]

    st.warning(
        "These zones have no recommended angle: "
        + ", ".join(missing_ids)
        + ". Run Elevation Analysis first."
    )

st.divider()

st.subheader("Row configuration")

config_col1, config_col2 = st.columns(2)

with config_col1:
    row_spacing_m = st.number_input(
        "Row spacing (m)",
        min_value=1.0,
        max_value=20.0,
        value=4.0,
        step=0.5,
    )

with config_col2:
    headland_m = st.number_input(
        "Headland from zone boundary (m)",
        min_value=0.0,
        max_value=20.0,
        value=2.0,
        step=0.5,
    )

st.info(
    "The row angle is not entered globally. "
    "Each zone uses its own recommended elevation-based angle."
)

if analysed_zones:
    angle_rows = []

    for zone in sorted(
        analysed_zones,
        key=lambda item: (
            item.get("sector_id", ""),
            item.get("zone_number", 0),
        ),
    ):
        analysis = zone.get(
            "elevation_analysis",
            {},
        )

        angle_rows.append({
            "Zone": zone.get("id"),
            "Downhill bearing (°)": analysis.get(
                "downhill_bearing_degrees"
            ),
            "Recommended row angle (°)": zone.get(
                "recommended_row_angle_degrees"
            ),
            "Slope (%)": analysis.get(
                "slope_percent"
            ),
        })

    st.subheader("Angles used for row generation")

    st.dataframe(
        pd.DataFrame(angle_rows),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

button_col1, button_col2 = st.columns(
    [2, 1],
    gap="medium",
)

with button_col1:
    generate_disabled = bool(not_analysed_zones)

    if st.button(
        "Generate rows using all zone angles",
        type="primary",
        use_container_width=True,
        disabled=generate_disabled,
    ):
        save_history_snapshot(
            st.session_state,
            "Before elevation-oriented row generation",
        )

        result = create_rows_for_all_zones(
            project=project,
            row_spacing_m=row_spacing_m,
            headland_m=headland_m,
        )

        st.session_state[
            "row_batch_result"
        ] = result

        st.rerun()

with button_col2:
    if st.button(
        "Remove ALL rows",
        type="secondary",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before removing all rows",
        )

        result = remove_all_rows(project)

        st.session_state[
            "row_batch_result"
        ] = result

        st.rerun()

batch_result = st.session_state.get(
    "row_batch_result"
)

if batch_result:
    if batch_result.get("ok"):
        st.success(
            batch_result.get("message", "")
        )
    else:
        st.warning(
            batch_result.get("message", "")
        )

    errors = batch_result.get(
        "errors",
        [],
    )

    if errors:
        st.error(
            " | ".join(errors)
        )

st.divider()

st.subheader("Map with elevation-oriented rows")

st.info(
    "Enable the Rows and trees layer from the map control "
    "if it is not already visible."
)

farm_map = build_project_map(project)

st_folium(
    farm_map,
    key="elevation_oriented_rows_map",
    height=720,
    use_container_width=True,
)

st.divider()

st.subheader("Current rows")

if rows:
    table_rows = []

    for row in rows[:100]:
        table_rows.append({
            "Row ID": row.get("id"),
            "Sector": row.get("sector_id"),
            "Zone": row.get("zone_id"),
            "Length (m)": row.get("length_m"),
            "Spacing (m)": row.get("spacing_m"),
            "Angle (°)": row.get(
                "direction_degrees"
            ),
        })

    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
    )

    if len(rows) > 100:
        st.caption(
            f"Showing first 100 rows of {len(rows)}."
        )
else:
    st.info(
        "No rows have been generated yet."
    )