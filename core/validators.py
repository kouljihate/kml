from core.constants import PIPE_HIERARCHY
from core.geometry import is_inside_polygon


def validate_pipe_hierarchy(parent_diameter_mm, child_diameter_mm):
    allowed = PIPE_HIERARCHY.get(parent_diameter_mm, [])

    if child_diameter_mm not in allowed:
        return {
            "ok": False,
            "message": (
                f"Invalid connection: {parent_diameter_mm} mm pipe cannot "
                f"directly supply {child_diameter_mm} mm pipe."
            ),
        }

    return {
        "ok": True,
        "message": "Pipe hierarchy is valid.",
    }


def validate_zone_inside_sector(zone_geometry, sector_geometry):
    valid = is_inside_polygon(zone_geometry, sector_geometry)

    return {
        "ok": valid,
        "message": (
            "Zone is inside the selected sector."
            if valid
            else "Zone extends outside the selected sector."
        ),
    }
