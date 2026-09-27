import json

import streamlit as st
from streamlit_folium import st_folium

from core.project import (
    initialize_project_state,
    save_history_snapshot,
)
from services.map_service import build_project_map
from services.sector_pipe_service import (
    create_sector_pipe,
    get_sector_by_id,
    get_sector_pipes,
    update_sector_pipe_flows,
)
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("9. 63 mm Sector Distribution Pipes")

project = st.session_state.farm_project
sectors = project.get("sectors", [])

if not sectors:
    st.warning(
        "Create sectors before adding 63 mm pipes."
    )
    st.stop()

st.write(
    "Draw a 63 mm major pipe inside a sector. "
    "It should follow the selected supply corridor and "
    "eventually connect to the 90 mm principal network."
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

existing_pipes = get_sector_pipes(
    project,
    selected_sector_id,
)

next_pipe_number = len(
    existing_pipes
) + 1

st.subheader("Sector pipe settings")

col1, col2 = st.columns(2)

with col1:
    pipe_number = st.number_input(
        "Pipe number",
        min_value=1,
        value=next_pipe_number,
        step=1,
    )

with col2:
    supply_side = st.selectbox(
        "Supply-side classification",
        options=[
            "automatic_high_elevation",
            "north",
            "south",
            "east",
            "west",
        ],
    )

st.info(
    "Use the map drawing tool to draw a line fully inside "
    f"{selected_sector_id}."
)

farm_map = build_project_map(
    project
)

map_result = st_folium(
    farm_map,
    key="sector_pipe_map",
    height=700,
    use_container_width=True,
    returned_objects=[
        "last_active_drawing",
        "all_drawings",
    ],
)

drawn_feature = map_result.get(
    "last_active_drawing"
)

if drawn_feature:
    geometry = drawn_feature.get(
        "geometry",
        {},
    )

    geometry_type = geometry.get(
        "type",
        "",
    )

    if geometry_type != "LineString":
        st.error(
            "Draw a line for a 63 mm sector pipe."
        )

    else:
        coordinates = geometry.get(
            "coordinates",
            [],
        )

        st.success(
            f"Received line with "
            f"{len(coordinates)} points."
        )

        if st.button(
            f"Add 63 mm pipe to {selected_sector_id}",
            type="primary",
            use_container_width=True,
        ):
            save_history_snapshot(
                st.session_state,
                f"Before adding 63 mm pipe to {selected_sector_id}",
            )

            result = create_sector_pipe(
                project=project,
                sector_id=selected_sector_id,
                coordinates=coordinates,
                pipe_number=int(pipe_number),
                parent_pipe_id=None,
                supply_side=supply_side,
            )

            if result["ok"]:
                update_sector_pipe_flows(
                    project
                )

                st.success(
                    result["message"]
                )

                st.rerun()

            else:
                st.error(
                    result["message"]
                )

st.divider()

st.subheader(
    f"Existing 63 mm pipes in {selected_sector_id}"
)

existing_pipes = get_sector_pipes(
    project,
    selected_sector_id,
)

if existing_pipes:
    table_rows = []

    for pipe in existing_pipes:
        table_rows.append({
            "Pipe ID": pipe.get("id"),
            "Length (m)": pipe.get(
                "length_m",
                0.0,
            ),
            "Flow (m³/h)": pipe.get(
                "flow_m3h",
                0.0,
            ),
            "Supply side": pipe.get(
                "supply_side",
                "",
            ),
            "Parent 90 mm pipe": pipe.get(
                "parent_pipe_id",
                "Not connected",
            ),
        })

    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info(
        f"No 63 mm pipes have been created in "
        f"{selected_sector_id}."
    )

st.divider()

st.subheader("Selected sector information")

if selected_sector:
    st.json({
        "sector_id": selected_sector.get("id"),
        "sector_name": selected_sector.get("name"),
        "zone_count": len([
            zone
            for zone in project.get("zones", [])
            if zone.get("sector_id")
            == selected_sector_id
        ]),
        "total_sector_flow_m3h": sum(
            zone.get(
                "target_flow_m3h",
                0.0,
            )
            for zone in project.get("zones", [])
            if zone.get("sector_id")
            == selected_sector_id
        ),
    })