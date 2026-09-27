def calculate_zone_flow_m3h(
    tree_count,
    emitters_per_tree,
    emitter_flow_lph,
):
    total_lph = tree_count * emitters_per_tree * emitter_flow_lph
    return total_lph / 1000


def calculate_static_pressure_bar(elevation_difference_m):
    return elevation_difference_m / 10.2
