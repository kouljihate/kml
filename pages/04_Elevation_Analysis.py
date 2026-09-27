import pandas as pd
import streamlit as st

from core.project import (
    initialize_project_state,
    save_history_snapshot,
)
from services.elevation_service import (
    calculate_elevation_for_all_zones,
    extract_elevation_points_from_kml,
)
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("4. Elevation and Row Orientation")

project = st.session_state.farm_project

zones = project.get("zones", [])

if not zones:
    st.warning(
        "No zones are available. "
        "Create zones before calculating elevation."
    )
    st.stop()

elevation_points = extract_elevation_points_from_kml(
    project
)

st.write(
    "This page reads elevation from the third coordinate of the "
    "initial KML: longitude, latitude, elevation."
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "KML elevation points",
    len(elevation_points),
)

col2.metric(
    "Zones",
    len(zones),
)

analysed_zone_count = len([
    zone
    for zone in zones
    if zone.get("elevation_analysis")
])

col3.metric(
    "Analysed zones",
    analysed_zone_count,
)

st.divider()

st.subheader("Automatic terrain analysis")

st.info(
    "For each zone, the system calculates the downhill direction "
    "from KML elevation values, then recommends planting rows "
    "perpendicular to that downhill direction."
)

if st.button(
    "Analyse elevation for ALL zones",
    type="primary",
    use_container_width=True,
):
    save_history_snapshot(
        st.session_state,
        "Before elevation analysis",
    )

    result = calculate_elevation_for_all_zones(
        project
    )

    st.session_state[
        "elevation_analysis_result"
    ] = result

    st.rerun()

result = st.session_state.get(
    "elevation_analysis_result"
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

st.subheader("Zone elevation results")

table_rows = []

for zone in sorted(
    zones,
    key=lambda item: (
        item.get("sector_id", ""),
        item.get("zone_number", 0),
    ),
):
    analysis = zone.get(
        "elevation_analysis",
        {},
    )

    table_rows.append({
        "Zone": zone.get("id"),
        "Min elevation (m)": analysis.get(
            "minimum_elevation_m"
        ),
        "Max elevation (m)": analysis.get(
            "maximum_elevation_m"
        ),
        "Range (m)": analysis.get(
            "elevation_range_m"
        ),
        "Slope (%)": analysis.get(
            "slope_percent"
        ),
        "Downhill bearing (°)": analysis.get(
            "downhill_bearing_degrees"
        ),
        "Recommended row angle (°)": analysis.get(
            "recommended_row_angle_degrees"
        ),
        "Elevation points": analysis.get(
            "elevation_point_count"
        ),
    })

dataframe = pd.DataFrame(table_rows)

st.dataframe(
    dataframe,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Row angle convention: 0° is approximately west-east; "
    "90° is approximately south-north."
)

st.divider()

st.subheader("How to read the result")

st.markdown(
    """
    - **Downhill bearing** shows the direction water naturally travels.
    - **Recommended row angle** is perpendicular to that downhill direction.
    - The future row generator will use the recommended angle automatically.
    - You will still be able to override a zone manually if the terrain,
      access road, basin, or irrigation pipe corridor requires it.
    """
)