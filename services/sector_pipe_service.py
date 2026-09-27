from pyproj import Transformer
from shapely.geometry import LineString, mapping, shape
from shapely.ops import transform


def get_sector_by_id(project, sector_id):
    for sector in project.get("sectors", []):
        if sector.get("id") == sector_id:
            return sector

    return None


def get_sector_pipes(project, sector_id):
    return [
        pipe
        for pipe in project.get("pipes", [])
        if pipe.get("pipe_type") == "major_63"
        and pipe.get("sector_id") == sector_id
    ]


def get_sector_zones(project, sector_id):
    return [
        zone
        for zone in project.get("zones", [])
        if zone.get("sector_id") == sector_id
    ]


def get_zone_control_point(project, zone_id):
    for valve in project.get("valves", []):
        if valve.get("zone_id") == zone_id:
            return valve.get("geometry")

    return None


def get_utm_crs_from_geometry(geometry):
    polygon = shape(geometry)
    centroid = polygon.centroid

    longitude = centroid.x
    latitude = centroid.y

    zone_number = int(
        (longitude + 180) / 6
    ) + 1

    if latitude >= 0:
        return f"EPSG:{32600 + zone_number}"

    return f"EPSG:{32700 + zone_number}"


def calculate_geometry_length_m(geometry):
    working_crs = get_utm_crs_from_geometry(
        geometry
    )

    to_projected = Transformer.from_crs(
        "EPSG:4326",
        working_crs,
        always_xy=True,
    )

    line = shape(geometry)

    projected_line = transform(
        to_projected.transform,
        line,
    )

    return working_crs, projected_line.length


def create_sector_pipe(
    project,
    sector_id,
    coordinates,
    pipe_number,
    parent_pipe_id=None,
    supply_side="automatic_high_elevation",
):
    sector = get_sector_by_id(
        project,
        sector_id,
    )

    if sector is None:
        return {
            "ok": False,
            "message": f"Sector {sector_id} was not found.",
        }

    if len(coordinates) < 2:
        return {
            "ok": False,
            "message": "A sector pipe needs at least two points.",
        }

    geometry = {
        "type": "LineString",
        "coordinates": coordinates,
    }

    sector_polygon = shape(
        sector["geometry"]
    )

    pipe_line = shape(geometry)

    if not sector_polygon.covers(pipe_line):
        return {
            "ok": False,
            "message": (
                f"The 63 mm pipe extends outside {sector_id}."
            ),
        }

    existing_pipes = get_sector_pipes(
        project,
        sector_id,
    )

    pipe_id = (
        f"P63-{sector_id}-"
        f"{pipe_number:03d}"
    )

    if any(
        pipe.get("id") == pipe_id
        for pipe in existing_pipes
    ):
        return {
            "ok": False,
            "message": f"{pipe_id} already exists.",
        }

    try:
        working_crs, length_m = (
            calculate_geometry_length_m(
                geometry
            )
        )

    except Exception as exc:
        return {
            "ok": False,
            "message": (
                f"Unable to calculate pipe length: {exc}"
            ),
        }

    pipe = {
        "id": pipe_id,
        "name": pipe_id,
        "entity_type": "pipe",
        "pipe_type": "major_63",
        "diameter_mm": 63,
        "material": "HDPE",
        "sector_id": sector_id,
        "zone_id": None,
        "length_m": round(length_m, 2),
        "flow_m3h": 0.0,
        "parent_pipe_id": parent_pipe_id,
        "supply_side": supply_side,
        "geometry": mapping(pipe_line),
        "properties": {
            "working_crs": working_crs,
            "role": "sector_major_distribution",
        },
        "description": (
            f"63 mm sector distribution pipe "
            f"for {sector_id}."
        ),
    }

    project["pipes"].append(pipe)

    return {
        "ok": True,
        "message": f"{pipe_id} created successfully.",
        "pipe": pipe,
    }


def calculate_sector_flow(project, sector_id):
    total_flow = 0.0

    for zone in get_sector_zones(
        project,
        sector_id,
    ):
        total_flow += zone.get(
            "target_flow_m3h",
            0.0,
        )

    return round(total_flow, 3)


def update_sector_pipe_flows(project):
    for pipe in project.get("pipes", []):
        if pipe.get("pipe_type") != "major_63":
            continue

        sector_id = pipe.get("sector_id")

        pipe["flow_m3h"] = calculate_sector_flow(
            project,
            sector_id,
        )

    return project