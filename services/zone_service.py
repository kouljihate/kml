from shapely.geometry import box, mapping, shape


def get_zones_for_sector(project, sector_id):
    return [
        zone
        for zone in project.get("zones", [])
        if zone.get("sector_id") == sector_id
    ]


def get_sector_by_id(project, sector_id):
    for sector in project.get("sectors", []):
        if sector.get("id") == sector_id:
            return sector

    return None


def get_sector_number(sector):
    value = sector.get("sector_number")

    if value is not None:
        return int(value)

    sector_id = str(sector.get("id", ""))

    if sector_id.startswith("S"):
        try:
            return int(sector_id[1:])
        except ValueError:
            return 0

    return 0


def get_polygon_from_geometry(geometry):
    polygon = shape(geometry)

    if polygon.geom_type != "Polygon":
        raise ValueError(
            "Expected a Polygon geometry."
        )

    if not polygon.is_valid:
        raise ValueError(
            "Sector polygon is invalid."
        )

    if polygon.area <= 0:
        raise ValueError(
            "Sector polygon area must be greater than zero."
        )

    return polygon


def find_cut_coordinate(
    polygon,
    axis,
    target_fraction,
):
    min_x, min_y, max_x, max_y = polygon.bounds

    margin = max(
        max_x - min_x,
        max_y - min_y,
    ) * 2

    total_area = polygon.area
    target_area = total_area * target_fraction

    if axis == "x":
        low = min_x
        high = max_x

        for _ in range(60):
            middle = (low + high) / 2

            left_side = box(
                min_x - margin,
                min_y - margin,
                middle,
                max_y + margin,
            )

            current_area = polygon.intersection(
                left_side
            ).area

            if current_area < target_area:
                low = middle
            else:
                high = middle

        return (low + high) / 2

    low = min_y
    high = max_y

    for _ in range(60):
        middle = (low + high) / 2

        bottom_side = box(
            min_x - margin,
            min_y - margin,
            max_x + margin,
            middle,
        )

        current_area = polygon.intersection(
            bottom_side
        ).area

        if current_area < target_area:
            low = middle
        else:
            high = middle

    return (low + high) / 2


def make_three_equal_parts(polygon):
    min_x, min_y, max_x, max_y = polygon.bounds

    width = max_x - min_x
    height = max_y - min_y

    axis = "x" if width >= height else "y"

    first_cut = find_cut_coordinate(
        polygon=polygon,
        axis=axis,
        target_fraction=1 / 3,
    )

    second_cut = find_cut_coordinate(
        polygon=polygon,
        axis=axis,
        target_fraction=2 / 3,
    )

    margin = max(width, height) * 2

    if axis == "x":
        first_area_box = box(
            min_x - margin,
            min_y - margin,
            first_cut,
            max_y + margin,
        )

        second_area_box = box(
            first_cut,
            min_y - margin,
            second_cut,
            max_y + margin,
        )

        third_area_box = box(
            second_cut,
            min_y - margin,
            max_x + margin,
            max_y + margin,
        )

    else:
        first_area_box = box(
            min_x - margin,
            min_y - margin,
            max_x + margin,
            first_cut,
        )

        second_area_box = box(
            min_x - margin,
            first_cut,
            max_x + margin,
            second_cut,
        )

        third_area_box = box(
            min_x - margin,
            second_cut,
            max_x + margin,
            max_y + margin,
        )

    part_1 = polygon.intersection(first_area_box)
    part_2 = polygon.intersection(second_area_box)
    part_3 = polygon.intersection(third_area_box)

    parts = [
        part_1,
        part_2,
        part_3,
    ]

    for index, part in enumerate(parts, start=1):
        if part.is_empty:
            raise ValueError(
                f"Zone part {index} is empty."
            )

        if part.geom_type != "Polygon":
            raise ValueError(
                f"Zone part {index} is not a simple polygon."
            )

        if part.area <= 0:
            raise ValueError(
                f"Zone part {index} has no area."
            )

    return parts


def build_zone(
    sector_id,
    zone_number,
    polygon,
):
    zone_id = f"{sector_id}-Z{zone_number}"

    return {
        "id": zone_id,
        "name": zone_id,
        "entity_type": "zone",
        "sector_id": sector_id,
        "zone_number": zone_number,
        "geometry": mapping(polygon),
        "area_m2": 0.0,
        "target_flow_m3h": 0.0,
        "valve_id": None,
        "row_ids": [],
        "tree_ids": [],
        "pipe_ids": [],
        "properties": {
            "creation_method": "automatic_equal_split",
        },
        "description": (
            f"Automatically generated approximately equal zone "
            f"{zone_number} inside {sector_id}."
        ),
    }


def create_three_zones_for_sector(
    project,
    sector_id,
):
    sector = get_sector_by_id(
        project,
        sector_id,
    )

    if sector is None:
        return {
            "ok": False,
            "message": f"{sector_id} was not found.",
            "created_zones": [],
        }

    existing_zones = get_zones_for_sector(
        project,
        sector_id,
    )

    if existing_zones:
        return {
            "ok": False,
            "message": (
                f"{sector_id} already has "
                f"{len(existing_zones)} zone(s). "
                "It was skipped to prevent duplicates."
            ),
            "created_zones": [],
        }

    try:
        sector_polygon = get_polygon_from_geometry(
            sector["geometry"]
        )

        parts = make_three_equal_parts(
            sector_polygon
        )

    except Exception as exc:
        return {
            "ok": False,
            "message": (
                f"Unable to split {sector_id}: {exc}"
            ),
            "created_zones": [],
        }

    new_zones = []

    for zone_number, part in enumerate(parts, start=1):
        zone = build_zone(
            sector_id=sector_id,
            zone_number=zone_number,
            polygon=part,
        )

        new_zones.append(zone)

    project["zones"].extend(new_zones)

    return {
        "ok": True,
        "message": (
            f"Created three approximately equal zones "
            f"for {sector_id}."
        ),
        "created_zones": new_zones,
    }


def create_three_zones_for_all_sectors(project):
    sectors = project.get("sectors", [])

    if not sectors:
        return {
            "ok": False,
            "message": "No sectors are available.",
            "created_sector_ids": [],
            "skipped_sector_ids": [],
            "errors": [],
        }

    created_sector_ids = []
    skipped_sector_ids = []
    errors = []

    ordered_sectors = sorted(
        sectors,
        key=get_sector_number,
    )

    for sector in ordered_sectors:
        sector_id = sector.get("id")

        result = create_three_zones_for_sector(
            project=project,
            sector_id=sector_id,
        )

        if result["ok"]:
            created_sector_ids.append(
                sector_id
            )
        else:
            message = result.get("message", "")

            if "already has" in message:
                skipped_sector_ids.append(
                    sector_id
                )
            else:
                errors.append(message)

    total_created_zones = len(
        created_sector_ids
    ) * 3

    message = (
        f"Created {total_created_zones} zones in "
        f"{len(created_sector_ids)} sector(s)."
    )

    return {
        "ok": len(created_sector_ids) > 0,
        "message": message,
        "created_sector_ids": created_sector_ids,
        "skipped_sector_ids": skipped_sector_ids,
        "errors": errors,
        "total_created_zones": total_created_zones,
    }


def remove_zone(project, zone_id):
    before_count = len(project.get("zones", []))

    project["zones"] = [
        zone
        for zone in project.get("zones", [])
        if zone.get("id") != zone_id
    ]

    after_count = len(project["zones"])

    if before_count == after_count:
        return {
            "ok": False,
            "message": f"Zone {zone_id} was not found.",
        }

    return {
        "ok": True,
        "message": f"Zone {zone_id} removed.",
    }


def remove_all_zones(project):
    removed_count = len(project.get("zones", []))

    project["zones"] = []

    return {
        "ok": True,
        "message": f"Removed {removed_count} zone(s).",
    }