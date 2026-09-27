import folium
from folium.plugins import Draw, Fullscreen, MousePosition
from streamlit_folium import st_folium


def render_project_map(
    project,
    height=700,
    allow_draw=True,
    draw_options=None,
):
    farm_map = build_base_map(project)

    add_land_layer(farm_map, project.get("land"))
    add_sector_layer(farm_map, project.get("sectors", []))
    add_zone_layer(farm_map, project.get("zones", []))
    add_row_layer(farm_map, project.get("rows", []))
    add_tree_layer(farm_map, project.get("trees", []))
    add_pipe_layer(farm_map, project.get("pipes", []))
    add_valve_layer(farm_map, project.get("valves", []))
    add_equipment_layer(
        farm_map,
        project.get("water_points", []),
        project.get("basins", []),
    )

    if allow_draw:
        Draw(
            export=False,
            draw_options=draw_options or default_draw_options(),
            edit_options={
                "edit": False,
                "remove": False,
            },
        ).add_to(farm_map)

    Fullscreen().add_to(farm_map)
    MousePosition().add_to(farm_map)
    folium.LayerControl(collapsed=False).add_to(farm_map)

    return st_folium(
        farm_map,
        height=height,
        use_container_width=True,
        returned_objects=[
            "last_active_drawing",
            "all_drawings",
            "last_object_clicked",
        ],
    )