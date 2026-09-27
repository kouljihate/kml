from math import atan2, degrees, floor

import numpy as np
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform


def get_utm_epsg_from_geometry(geometry):
    polygon = shape(geometry)
    centroid = polygon.centroid

    longitude = centroid.x
    latitude = centroid.y

    utm_zone = int(
        floor((longitude + 180) / 6) + 1
    )

    if latitude >= 0:
        return f"EPSG:{32600 + utm_zone}"

    return f"EPSG:{32700 + utm_zone}"


def get_projected_transformer(working_crs):
    return Transformer.from_crs(
        "EPSG:4326",
        working_crs,
        always_xy=True,
    )


def add_elevation_point(
    points,
    longitude,
    latitude,
    elevation,
    source_id,
):
    if elevation is None:
        return

    try:
        elevation_value = float(elevation)
    except (TypeError, ValueError):
        return

    points.append({
        "longitude": float(longitude),
        "latitude": float(latitude),
        "elevation_m": elevation_value,
        "source_id": source_id,
    })


def extract_elevation_points_from_kml(project):
    points = []
    seen_coordinates = set()

    for feature in project.get(
        "kml_features",
        [],
    ):
        geometry = feature.get("geometry", {})
        geometry_type = geometry.get("type", "")
        coordinates = geometry.get("coordinates", [])
        source_id = feature.get("id", "KML")

        raw_coordinates = []

        if geometry_type == "Point":
            raw_coordinates = [coordinates]

        elif geometry_type == "LineString":
            raw_coordinates = coordinates

        elif geometry_type == "Polygon":
            if coordinates:
                raw_coordinates = coordinates[0]

        for coordinate in raw_coordinates:
            if len(coordinate) < 3:
                continue

            longitude = coordinate[0]
            latitude = coordinate[1]
            elevation = coordinate[2]

            coordinate_key = (
                round(float(longitude), 8),
                round(float(latitude), 8),
                round(float(elevation), 3),
            )

            if coordinate_key in seen_coordinates:
                continue

            seen_coordinates.add(
                coordinate_key
            )

            add_elevation_point(
                points=points,
                longitude=longitude,
                latitude=latitude,
                elevation=elevation,
                source_id=source_id,
            )

    return points


def get_zone_by_id(project, zone_id):
    for zone in project.get("zones", []):
        if zone.get("id") == zone_id:
            return zone

    return None


def collect_nearest_elevation_points(
    zone_geometry,
    elevation_points,
    maximum_points=20,
):
    if len(elevation_points) < 3:
        return []

    working_crs = get_utm_epsg_from_geometry(
        zone_geometry
    )

    transformer = get_projected_transformer(
        working_crs
    )

    zone_polygon_wgs84 = shape(zone_geometry)

    zone_polygon = transform(
        transformer.transform,
        zone_polygon_wgs84,
    )

    centroid = zone_polygon.centroid

    ranked_points = []

    for item in elevation_points:
        x, y = transformer.transform(
            item["longitude"],
            item["latitude"],
        )

        distance_m = centroid.distance(
            Point(x, y)
        )

        ranked_points.append({
            "x": x,
            "y": y,
            "z": item["elevation_m"],
            "distance_m": distance_m,
            "source_id": item["source_id"],
        })

    ranked_points = sorted(
        ranked_points,
        key=lambda item: item["distance_m"],
    )

    return ranked_points[:maximum_points]


def fit_terrain_plane(projected_points):
    if len(projected_points) < 3:
        raise ValueError(
            "At least three elevation points are required."
        )

    matrix = []
    elevations = []

    for point in projected_points:
        matrix.append([
            point["x"],
            point["y"],
            1.0,
        ])

        elevations.append(
            point["z"]
        )

    coefficients, _, _, _ = np.linalg.lstsq(
        np.array(matrix),
        np.array(elevations),
        rcond=None,
    )

    slope_x = float(coefficients[0])
    slope_y = float(coefficients[1])
    intercept = float(coefficients[2])

    return slope_x, slope_y, intercept


def calculate_zone_elevation_analysis(
    project,
    zone_id,
):
    zone = get_zone_by_id(
        project,
        zone_id,
    )

    if zone is None:
        return {
            "ok": False,
            "message": f"Zone {zone_id} was not found.",
        }

    elevation_points = extract_elevation_points_from_kml(
        project
    )

    if len(elevation_points) < 3:
        return {
            "ok": False,
            "message": (
                "The KML does not contain at least three usable "
                "elevation coordinates."
            ),
        }

    projected_points = collect_nearest_elevation_points(
        zone_geometry=zone["geometry"],
        elevation_points=elevation_points,
        maximum_points=20,
    )

    if len(projected_points) < 3:
        return {
            "ok": False,
            "message": (
                f"Not enough elevation points are available "
                f"near {zone_id}."
            ),
        }

    try:
        slope_x, slope_y, intercept = fit_terrain_plane(
            projected_points
        )

    except Exception as exc:
        return {
            "ok": False,
            "message": (
                f"Unable to calculate terrain plane "
                f"for {zone_id}: {exc}"
            ),
        }

    downhill_x = -slope_x
    downhill_y = -slope_y

    downhill_bearing = (
        degrees(
            atan2(
                downhill_x,
                downhill_y,
            )
        )
        + 360
    ) % 360

    contour_row_bearing = (
        downhill_bearing + 90
    ) % 180

    row_angle_degrees = (
        90 - contour_row_bearing
    ) % 180

    slope_ratio = (
        slope_x ** 2 + slope_y ** 2
    ) ** 0.5

    slope_percent = slope_ratio * 100

    elevations = [
        point["z"]
        for point in projected_points
    ]

    analysis = {
        "elevation_point_count": len(
            projected_points
        ),
        "minimum_elevation_m": round(
            min(elevations),
            2,
        ),
        "maximum_elevation_m": round(
            max(elevations),
            2,
        ),
        "average_elevation_m": round(
            sum(elevations) / len(elevations),
            2,
        ),
        "elevation_range_m": round(
            max(elevations) - min(elevations),
            2,
        ),
        "slope_x": round(slope_x, 8),
        "slope_y": round(slope_y, 8),
        "slope_percent": round(
            slope_percent,
            2,
        ),
        "downhill_bearing_degrees": round(
            downhill_bearing,
            2,
        ),
        "contour_row_bearing_degrees": round(
            contour_row_bearing,
            2,
        ),
        "recommended_row_angle_degrees": round(
            row_angle_degrees,
            2,
        ),
        "working_crs": get_utm_epsg_from_geometry(
            zone["geometry"]
        ),
        "method": (
            "KML elevation vertices - "
            "least-squares terrain plane"
        ),
    }

    zone["elevation_analysis"] = analysis
    zone["recommended_row_angle_degrees"] = (
        analysis["recommended_row_angle_degrees"]
    )

    return {
        "ok": True,
        "message": (
            f"Elevation analysis complete for {zone_id}."
        ),
        "analysis": analysis,
    }


def calculate_elevation_for_all_zones(project):
    zones = project.get("zones", [])

    if not zones:
        return {
            "ok": False,
            "message": "No zones are available.",
            "analysed_zone_ids": [],
            "errors": [],
        }

    analysed_zone_ids = []
    errors = []

    ordered_zones = sorted(
        zones,
        key=lambda zone: (
            zone.get("sector_id", ""),
            zone.get("zone_number", 0),
        ),
    )

    for zone in ordered_zones:
        result = calculate_zone_elevation_analysis(
            project=project,
            zone_id=zone["id"],
        )

        if result["ok"]:
            analysed_zone_ids.append(
                zone["id"]
            )
        else:
            errors.append(
                result["message"]
            )

    return {
        "ok": len(analysed_zone_ids) > 0,
        "message": (
            f"Elevation analysis completed for "
            f"{len(analysed_zone_ids)} zone(s)."
        ),
        "analysed_zone_ids": analysed_zone_ids,
        "errors": errors,
    }