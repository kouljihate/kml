from pyproj import Transformer


def lonlat_to_projected(longitude, latitude, working_crs):
    transformer = Transformer.from_crs(
        "EPSG:4326",
        working_crs,
        always_xy=True,
    )
    return transformer.transform(longitude, latitude)


def projected_to_lonlat(x, y, working_crs):
    transformer = Transformer.from_crs(
        working_crs,
        "EPSG:4326",
        always_xy=True,
    )
    return transformer.transform(x, y)
