import streamlit as st
from streamlit_folium import st_folium

from core.project import initialize_project_state

from core.project import save_history_snapshot
from services.map_service import build_project_map
from services.zone_service import (
    create_three_zones_for_all_sectors,
    build_zone,
    get_sector_by_id,
    get_zones_for_sector,
    remove_all_zones,
    remove_zone,
)
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("3. Irrigation Zones")

project = st.session_state.farm_project
sectors = project.get("sectors", [])

if not sectors:
    st.warning(
        "No sectors are available. Complete the Land and Sectors page first."
    )
    st.stop()

st.write(
    "Draw each irrigation zone inside its sector. "
    "The application will reject any zone extending outside the selected sector."
)

st.subheader("Automatic zone generation")

st.write(
    "Create three approximately equal zones in every sector. "
    "The system will create S1-Z1 to S1-Z3, then repeat for "
    "S2 through S8."
)

total_existing_zones = len(
    project.get("zones", [])
)

st.metric(
    "Existing zones",
    total_existing_zones,
)

automatic_col1, automatic_col2 = st.columns(
    [2, 1],
    gap="medium",
)

with automatic_col1:
    if st.button(
        "Create 3 equal zones for ALL sectors",
        type="primary",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before automatic creation of all zones",
        )

        result = create_three_zones_for_all_sectors(
            project
        )

        st.session_state["zone_batch_result"] = result

        st.rerun()

with automatic_col2:
    if st.button(
        "Remove ALL zones",
        type="secondary",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before removing all zones",
        )

        result = remove_all_zones(project)

        st.session_state["zone_batch_result"] = result

        st.rerun()

batch_result = st.session_state.get(
    "zone_batch_result"
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

    created_sector_ids = batch_result.get(
        "created_sector_ids",
        [],
    )

    skipped_sector_ids = batch_result.get(
        "skipped_sector_ids",
        [],
    )

    errors = batch_result.get(
        "errors",
        [],
    )

    if created_sector_ids:
        st.write(
            "Created zones for: "
            + ", ".join(created_sector_ids)
        )

    if skipped_sector_ids:
        st.write(
            "Skipped existing sectors: "
            + ", ".join(skipped_sector_ids)
        )

    if errors:
        st.error(
            "Errors: " + " | ".join(errors)
        )

sector_ids = [
    sector.get("id")
    for sector in sectors
]

selected_sector_id = st.selectbox(
    "Select sector",
    options=sector_ids,
)

selected_sector = get_sector_by_id(
    project,
    selected_sector_id,
)

existing_zones = get_zones_for_sector(
    project,
    selected_sector_id,
)

used_zone_numbers = [
    zone.get("zone_number")
    for zone in existing_zones
]

available_zone_numbers = [
    number
    for number in range(1, 21)
    if number not in used_zone_numbers
]

if not available_zone_numbers:
    st.error(
        f"All available zone numbers are already used in {selected_sector_id}."
    )
    st.stop()

selected_zone_number = st.selectbox(
    "New zone number",
    options=available_zone_numbers,
)

zone_name = st.text_input(
    "Zone name",
    value=f"{selected_sector_id}-Z{selected_zone_number}",
)

st.info(
    "Use the polygon drawing tool on the map. "
    "Draw the zone completely inside the orange sector boundary."
)

st.subheader("Map")

farm_map = build_project_map(project)

map_result = st_folium(
    farm_map,
    key="zones_map",
    height=700,
    use_container_width=True,
    returned_objects=[
        "last_active_drawing",
        "all_drawings",
    ],
)

drawn_feature = map_result.get("last_active_drawing")

if drawn_feature:
    geometry = drawn_feature.get("geometry", {})
    geometry_type = geometry.get("type", "")

    st.success(
        f"Geometry received from map: {geometry_type}"
    )

    if geometry_type != "Polygon":
        st.error(
            "For a zone, use the polygon drawing tool, "
            "not the marker or line tool."
        )
    else:
        if st.button(
            f"Create {selected_sector_id}-Z{selected_zone_number}",
            type="primary",
            use_container_width=True,
        ):
            save_history_snapshot(
                st.session_state,
                f"Before creating {selected_sector_id}-Z{selected_zone_number}",
            )

            result = create_zone(
                project=project,
                sector_id=selected_sector_id,
                zone_number=selected_zone_number,
                geojson_geometry=geometry,
                name=zone_name,
            )

            if result["ok"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])
else:
    st.warning(
        "Draw a polygon on the map to create a new irrigation zone."
    )

st.divider()

st.subheader(f"Zones in {selected_sector_id}")

current_zones = get_zones_for_sector(
    project,
    selected_sector_id,
)

if current_zones:
    table_rows = []

    for zone in current_zones:
        table_rows.append({
            "Zone ID": zone.get("id"),
            "Name": zone.get("name"),
            "Area m²": zone.get("area_m2", 0),
            "Target flow m³/h": zone.get("target_flow_m3h", 0),
        })

    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
    )

    zone_ids = [
        zone.get("id")
        for zone in current_zones
    ]

    zone_to_remove = st.selectbox(
        "Select zone to remove",
        options=zone_ids,
        key=f"remove_zone_{selected_sector_id}",
    )

    if st.button(
        f"Remove {zone_to_remove}",
        type="secondary",
    ):
        save_history_snapshot(
            st.session_state,
            f"Before removing {zone_to_remove}",
        )

        result = remove_zone(
            project,
            zone_to_remove,
        )

        if result["ok"]:
            st.success(result["message"])
            st.rerun()
        else:
            st.error(result["message"])
else:
    st.info(
        f"No zones have been created in {selected_sector_id} yet."
    )

st.divider()

st.subheader("Zone design progress")

total_zones = len(project.get("zones", []))
expected_zones = len(sectors) * 3

st.write(
    f"Created zones: {total_zones} / {expected_zones}"
)

progress_value = min(
    total_zones / expected_zones,
    1.0,
) if expected_zones else 0.0

st.progress(progress_value)