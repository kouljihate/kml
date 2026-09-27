import pandas as pd
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium

from core.project import (
    initialize_project_state,
    save_history_snapshot,
)
from services.map_service import build_project_map
from services.principal_pipe_service import (
    get_available_principal_route_ids,
    get_principal_pipes,
    remove_principal_route,
    create_principal_route,
)
from ui.sidebar import show_project_sidebar


initialize_project_state(
    st.session_state
)

show_project_sidebar()

st.title("9. High-Elevation 90 mm Principal Routes")

project = st.session_state.farm_project

if not project.get("land"):
    st.warning(
        "No land boundary is assigned yet. "
        "Complete Land and Sectors first."
    )
    st.stop()

if not project.get("basins"):
    st.warning(
        "No basin is assigned yet. "
        "Complete Land and Sectors first."
    )
    st.stop()

principal_routes = get_principal_pipes(
    project
)

available_route_ids = get_available_principal_route_ids(
    project
)

st.write(
    "Create exactly three 90 mm principal routes. "
    "Draw them manually along the high-elevation boundary "
    "or the approved high-elevation supply corridor."
)

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric(
    "Principal routes created",
    f"{len(principal_routes)} / 3",
)

metric_col2.metric(
    "Available route IDs",
    len(available_route_ids),
)

metric_col3.metric(
    "Total 90 mm length",
    f"{sum(pipe.get('length_m', 0) for pipe in principal_routes):.1f} m",
)

st.divider()

st.subheader("Principal-route drawing rules")

st.code(
    "Only three routes are allowed:\n"
    "  P90-R1\n"
    "  P90-R2\n"
    "  P90-R3\n\n"
    "Rules:\n"
    "  1. Draw inside the land boundary.\n"
    "  2. Keep the route on the high-elevation boundary.\n"
    "  3. Start near the basin or connect to an approved route.\n"
    "  4. Do not draw through irrigation zones unnecessarily.\n"
    "  5. Do not create a fourth 90 mm route.",
    language="text",
)

if available_route_ids:
    selected_route_id = st.selectbox(
        "Select principal route ID",
        options=available_route_ids,
    )

    route_description = st.text_area(
        "Route notes",
        value=(
            "High-elevation boundary route. "
            "Serves future 63 mm sector branches."
        ),
    )

    st.info(
        "Use the line-drawing tool in the upper-left "
        "corner of the map. Draw the 90 mm route along "
        "the high-elevation boundary."
    )

    farm_map = build_project_map(
        project
    )

    Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": {
                "shapeOptions": {
                    "color": "#ff0000",
                    "weight": 7,
                }
            },
            "polygon": False,
            "rectangle": False,
            "marker": False,
            "circle": False,
            "circlemarker": False,
        },
        edit_options={
            "edit": False,
            "remove": False,
        },
    ).add_to(farm_map)

    map_result = st_folium(
        farm_map,
        key="principal_route_map",
        height=720,
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

        if geometry_type == "LineString":
            coordinates = geometry.get(
                "coordinates",
                [],
            )

            st.success(
                f"Route drawing detected: "
                f"{len(coordinates)} points."
            )

            if st.button(
                f"Save {selected_route_id}",
                type="primary",
                use_container_width=True,
            ):
                save_history_snapshot(
                    st.session_state,
                    f"Before creating {selected_route_id}",
                )

                result = create_principal_route(
                    project=project,
                    route_id=selected_route_id,
                    coordinates=coordinates,
                    route_description=route_description,
                )

                if result["ok"]:
                    st.session_state[
                        "principal_route_result"
                    ] = result

                    st.rerun()

                else:
                    st.error(
                        result["message"]
                    )

        else:
            st.error(
                "Draw a line, not a marker or polygon."
            )

else:
    st.success(
        "All three principal routes have been created."
    )

st.divider()

st.subheader("Existing 90 mm principal routes")

if principal_routes:
    route_rows = []

    for route in principal_routes:
        route_rows.append({
            "Route ID": route.get("id"),
            "Diameter": (
                f"{route.get('diameter_mm')} mm"
            ),
            "Length (m)": route.get(
                "length_m",
                0.0,
            ),
            "Source": route.get(
                "from_node_id",
                "",
            ),
            "High-elevation review": route.get(
                "properties",
                {},
            ).get(
                "requires_high_elevation_review",
                False,
            ),
        })

    st.dataframe(
        pd.DataFrame(route_rows),
        use_container_width=True,
        hide_index=True,
    )

    route_ids = [
        route.get("id")
        for route in principal_routes
    ]

    route_to_remove = st.selectbox(
        "Select route to redraw or remove",
        options=route_ids,
    )

    if st.button(
        f"Remove {route_to_remove}",
        type="secondary",
    ):
        save_history_snapshot(
            st.session_state,
            f"Before removing {route_to_remove}",
        )

        result = remove_principal_route(
            project,
            route_to_remove,
        )

        if result["ok"]:
            st.session_state[
                "principal_route_result"
            ] = result

            st.rerun()

        else:
            st.error(
                result["message"]
        )

else:
    st.info(
        "No 90 mm principal routes have been created yet."
    )

result = st.session_state.get(
    "principal_route_result"
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