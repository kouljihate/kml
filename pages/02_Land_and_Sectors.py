import streamlit as st
from streamlit_folium import st_folium

from core.project import save_history_snapshot
from services.land_sector_service import (
    add_sector,
    clear_land_and_sector_setup,
    get_imported_points,
    get_imported_polygons,
    set_basin,
    set_land_boundary,
    set_water_point,
)
from services.map_service import build_project_map
from ui.sidebar import show_project_sidebar


show_project_sidebar()

st.title("2. Land, Water Point, Basin and Sectors")

st.write(
    "Use this page to assign the imported KML elements to their real "
    "irrigation-design roles. First choose the land boundary, then the "
    "water point, basin, and sectors."
)

project = st.session_state.farm_project

imported_polygons = get_imported_polygons(project)
imported_points = get_imported_points(project)

if not imported_polygons and not imported_points:
    st.warning(
        "No imported KML features are available yet. "
        "Go to Project Map, upload dhar.kml, and click "
        "Import KML to project map."
    )
    st.stop()

st.divider()

st.subheader("Current project status")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Land boundary",
    "Ready" if project["land"] else "Not assigned",
)

col2.metric(
    "Water point",
    len(project["water_points"]),
)

col3.metric(
    "Basin",
    len(project["basins"]),
)

col4.metric(
    "Sectors",
    len(project["sectors"]),
)

st.divider()

left_column, right_column = st.columns(
    [1.2, 2.0],
    gap="large",
)

with left_column:
    st.subheader("A. Assign land boundary")

    polygon_options = {
        f"{feature['name']} | {feature['id']}": feature["id"]
        for feature in imported_polygons
    }

    selected_land_label = st.selectbox(
        "Select the whole farm / land polygon",
        options=list(polygon_options.keys()),
        key="land_polygon_selector",
    )

    if st.button(
        "Set selected polygon as land boundary",
        type="primary",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before setting land boundary",
        )

        result = set_land_boundary(
            project,
            polygon_options[selected_land_label],
        )

        if result["ok"]:
            st.success(result["message"])
            st.rerun()
        else:
            st.error(result["message"])

    st.divider()

    st.subheader("B. Assign water point")

    if imported_points:
        point_options = {
            f"{feature['name']} | {feature['id']}": feature["id"]
            for feature in imported_points
        }

        selected_point_label = st.selectbox(
            "Select well / water point",
            options=list(point_options.keys()),
            key="water_point_selector",
        )

        if st.button(
            "Set selected point as water point",
            use_container_width=True,
        ):
            save_history_snapshot(
                st.session_state,
                "Before setting water point",
            )

            result = set_water_point(
                project,
                point_options[selected_point_label],
            )

            if result["ok"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])

    else:
        st.warning(
            "No point marker was imported. "
            "You can add the well manually later from the map."
        )

    st.divider()

    st.subheader("C. Assign basin")

    selected_basin_label = st.selectbox(
        "Select basin polygon",
        options=list(polygon_options.keys()),
        key="basin_polygon_selector",
    )

    if st.button(
        "Set selected polygon as basin",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            "Before setting basin",
        )

        result = set_basin(
            project,
            polygon_options[selected_basin_label],
        )

        if result["ok"]:
            st.success(result["message"])
            st.rerun()
        else:
            st.error(result["message"])

with right_column:
    st.subheader("Farm map")

    st.caption(
        "Click a polygon on the map to view its original KML name. "
        "Use that name to select the correct item in the assignment lists."
    )

    farm_map = build_project_map(project)

    st_folium(
        farm_map,
        key="land_sector_assignment_map",
        height=700,
        use_container_width=True,
    )

st.divider()

st.subheader("D. Assign sectors")

st.write(
    "Assign each sector polygon from the imported KML. "
    "If the KML polygons are already named S1 to S8, select the matching "
    "polygon and give it the corresponding sector number."
)

available_sector_polygons = {
    f"{feature['name']} | {feature['id']}": feature["id"]
    for feature in imported_polygons
}

sector_col1, sector_col2, sector_col3 = st.columns(
    [1.6, 0.7, 1.0],
    gap="medium",
)

with sector_col1:
    selected_sector_polygon_label = st.selectbox(
        "Select imported polygon",
        options=list(available_sector_polygons.keys()),
        key="sector_polygon_selector",
    )

with sector_col2:
    sector_number = st.number_input(
        "Sector number",
        min_value=1,
        max_value=50,
        value=1,
        step=1,
    )

with sector_col3:
    st.write("")
    st.write("")

    if st.button(
        "Add sector",
        use_container_width=True,
    ):
        save_history_snapshot(
            st.session_state,
            f"Before adding S{sector_number}",
        )

        result = add_sector(
            project=project,
            feature_id=available_sector_polygons[
                selected_sector_polygon_label
            ],
            sector_number=sector_number,
        )

        if result["ok"]:
            st.success(result["message"])
            st.rerun()
        else:
            st.error(result["message"])

st.divider()

st.subheader("Assigned sectors")

if project["sectors"]:
    sector_rows = []

    for sector in project["sectors"]:
        sector_rows.append({
            "Sector ID": sector["id"],
            "Original KML name": sector.get("name", ""),
            "Feature ID": sector.get("id", ""),
        })

    st.dataframe(
        sector_rows,
        use_container_width=True,
        hide_index=True,
    )

    remove_options = [
        sector["id"]
        for sector in project["sectors"]
    ]

    selected_sector_to_remove = st.selectbox(
        "Remove sector",
        options=remove_options,
    )

    if st.button(
        "Remove selected sector",
        type="secondary",
    ):
        project["sectors"] = [
            sector
            for sector in project["sectors"]
            if sector["id"] != selected_sector_to_remove
        ]

        st.success(
            f"{selected_sector_to_remove} removed."
        )

        st.rerun()

else:
    st.info("No sectors have been assigned yet.")

st.divider()

with st.expander("Danger zone"):
    st.warning(
        "This clears only the app's assigned land, basin, water point, "
        "and sector setup. It does not delete the original imported KML data."
    )

    if st.button(
        "Clear land and sector assignments",
        type="secondary",
    ):
        result = clear_land_and_sector_setup(project)

        st.success(result["message"])
        st.rerun()