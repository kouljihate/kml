from shapely.geometry import shape


def geojson_to_shape(geometry):
    return shape(geometry)


def is_inside_polygon(candidate_geometry, boundary_geometry):
    candidate = geojson_to_shape(candidate_geometry)
    boundary = geojson_to_shape(boundary_geometry)
    return boundary.covers(candidate)
