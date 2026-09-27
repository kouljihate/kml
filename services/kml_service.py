import re
from lxml import etree


KML_NS = "http://www.opengis.net/kml/2.2"
NS = {"kml": KML_NS}


def parse_kml(kml_bytes):
    return etree.fromstring(kml_bytes)


def serialize_kml(root):
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )


def parse_coordinates(coordinates_text):
    if not coordinates_text:
        return []

    coordinates = []

    for item in coordinates_text.strip().split():
        values = item.split(",")

        if len(values) < 2:
            continue

        longitude = float(values[0])
        latitude = float(values[1])
        altitude = float(values[2]) if len(values) >= 3 else 0.0

        coordinates.append([
            longitude,
            latitude,
            altitude,
        ])

    return coordinates


def get_placemark_name(placemark):
    name_node = placemark.find("kml:name", namespaces=NS)

    if name_node is not None and name_node.text:
        return name_node.text.strip()

    return "Unnamed Item"


def get_placemark_description(placemark):
    description_node = placemark.find(
        "kml:description",
        namespaces=NS,
    )

    if description_node is not None and description_node.text:
        return description_node.text.strip()

    return ""


def get_parent_folder_name(placemark):
    parent = placemark.getparent()

    while parent is not None:
        if parent.tag == f"{{{KML_NS}}}Folder":
            name_node = parent.find("kml:name", namespaces=NS)

            if name_node is not None and name_node.text:
                return name_node.text.strip()

        parent = parent.getparent()

    return "Imported KML"


def extract_kml_features(kml_bytes):
    root = parse_kml(kml_bytes)

    features = []

    placemarks = root.findall(
        ".//kml:Placemark",
        namespaces=NS,
    )

    for index, placemark in enumerate(placemarks, start=1):
        name = get_placemark_name(placemark)
        description = get_placemark_description(placemark)
        folder_name = get_parent_folder_name(placemark)

        point_nodes = placemark.findall(
            ".//kml:Point/kml:coordinates",
            namespaces=NS,
        )

        for geometry_index, point_node in enumerate(point_nodes, start=1):
            coordinates = parse_coordinates(point_node.text)

            if not coordinates:
                continue

            longitude, latitude, altitude = coordinates[0]

            features.append({
                "id": f"KML-POINT-{index}-{geometry_index}",
                "name": name,
                "description": description,
                "folder": folder_name,
                "entity_type": "imported_point",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        longitude,
                        latitude,
                        altitude,
                    ],
                },
            })

        line_nodes = placemark.findall(
            ".//kml:LineString/kml:coordinates",
            namespaces=NS,
        )

        for geometry_index, line_node in enumerate(line_nodes, start=1):
            coordinates = parse_coordinates(line_node.text)

            if len(coordinates) < 2:
                continue

            features.append({
                "id": f"KML-LINE-{index}-{geometry_index}",
                "name": name,
                "description": description,
                "folder": folder_name,
                "entity_type": "imported_line",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
            })

        polygon_nodes = placemark.findall(
            ".//kml:Polygon/kml:outerBoundaryIs/"
            "kml:LinearRing/kml:coordinates",
            namespaces=NS,
        )

        for geometry_index, polygon_node in enumerate(polygon_nodes, start=1):
            coordinates = parse_coordinates(polygon_node.text)

            if len(coordinates) < 3:
                continue

            if coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])

            features.append({
                "id": f"KML-POLYGON-{index}-{geometry_index}",
                "name": name,
                "description": description,
                "folder": folder_name,
                "entity_type": "imported_polygon",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coordinates],
                },
            })

    return features


def polygon_coordinate_count(feature):
    geometry = feature.get("geometry", {})

    if geometry.get("type") != "Polygon":
        return 0

    coordinates = geometry.get("coordinates", [])

    if not coordinates:
        return 0

    outer_ring = coordinates[0]

    return len(outer_ring)


def normalize_name(value):
    return value.strip().lower()


def is_sector_name(name):
    normalized = normalize_name(name)

    return bool(
        re.fullmatch(
            r"s[\s_-]?\d+",
            normalized,
        )
    )


def is_basin_name(name):
    normalized = normalize_name(name)

    basin_keywords = [
        "basin",
        "bassin",
        "reservoir",
        "tank",
        "water tank",
        "water storage",
    ]

    return any(
        keyword in normalized
        for keyword in basin_keywords
    )


def is_water_point_name(name):
    normalized = normalize_name(name)

    water_keywords = [
        "well",
        "water",
        "water point",
        "source",
        "pump",
        "forage",
        "puits",
        "t1",
    ]

    return any(
        keyword in normalized
        for keyword in water_keywords
    )


def import_kml_to_project(project, kml_bytes):
    features = extract_kml_features(kml_bytes)

    project["kml_features"] = features

    project["land"] = None
    project["water_points"] = []
    project["basins"] = []
    project["sectors"] = []

    point_features = [
        feature
        for feature in features
        if feature["geometry"]["type"] == "Point"
    ]

    line_features = [
        feature
        for feature in features
        if feature["geometry"]["type"] == "LineString"
    ]

    polygon_features = [
        feature
        for feature in features
        if feature["geometry"]["type"] == "Polygon"
    ]

    for point in point_features:
        point_name = point.get("name", "")

        point["entity_type"] = "water_point"

        if is_water_point_name(point_name):
            point["entity_type"] = "water_point"

        project["water_points"].append(point)

    basin_polygons = []

    for polygon in polygon_features:
        polygon_name = polygon.get("name", "")

        if is_sector_name(polygon_name):
            sector_number_match = re.search(
                r"\d+",
                polygon_name,
            )

            sector_number = int(
                sector_number_match.group()
            )

            polygon["entity_type"] = "sector"
            polygon["sector_number"] = sector_number
            polygon["id"] = f"S{sector_number}"

            project["sectors"].append(polygon)

        elif is_basin_name(polygon_name):
            polygon["entity_type"] = "basin"
            polygon["id"] = "BASIN-001"

            basin_polygons.append(polygon)

    project["basins"] = basin_polygons

    classified_polygon_ids = set()

    for sector in project["sectors"]:
        classified_polygon_ids.add(sector["id"])

    for basin in project["basins"]:
        classified_polygon_ids.add(basin["id"])

    remaining_polygons = []

    for polygon in polygon_features:
        entity_type = polygon.get("entity_type", "")

        if entity_type not in ["sector", "basin"]:
            remaining_polygons.append(polygon)

    if remaining_polygons:
        land_polygon = max(
            remaining_polygons,
            key=polygon_coordinate_count,
        )

        land_polygon["entity_type"] = "land"
        land_polygon["id"] = "LAND-001"
        land_polygon["name"] = "Land Boundary"

        project["land"] = land_polygon

    project["sectors"] = sorted(
        project["sectors"],
        key=lambda sector: sector.get(
            "sector_number",
            999,
        ),
    )

    return {
        "feature_count": len(features),
        "point_count": len(point_features),
        "line_count": len(line_features),
        "polygon_count": len(polygon_features),
        "land_count": 1 if project["land"] else 0,
        "water_point_count": len(project["water_points"]),
        "basin_count": len(project["basins"]),
        "sector_count": len(project["sectors"]),
        "message": "KML imported and classified successfully.",
    }

def export_project_to_kml(project):
    root = etree.Element(
        f"{{{KML_NS}}}kml",
        nsmap={None: KML_NS},
    )

    document = etree.SubElement(
        root,
        f"{{{KML_NS}}}Document",
    )

    etree.SubElement(
        document,
        f"{{{KML_NS}}}name",
    ).text = project["project"]["name"]

    return serialize_kml(root)