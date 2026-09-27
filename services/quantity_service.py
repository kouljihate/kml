import pandas as pd


def build_pipe_quantity_table(project):
    rows = []

    for pipe in project.get("pipes", []):
        rows.append({
            "Pipe ID": pipe.get("id"),
            "Diameter (mm)": pipe.get("diameter_mm"),
            "Material": pipe.get("material", "HDPE"),
            "Length (m)": pipe.get("length_m", 0),
            "Sector": pipe.get("sector_id"),
            "Zone": pipe.get("zone_id"),
        })

    return pd.DataFrame(rows)


def build_project_summary(project):
    return {
        "sectors": len(project.get("sectors", [])),
        "zones": len(project.get("zones", [])),
        "rows": len(project.get("rows", [])),
        "trees": len(project.get("trees", [])),
        "pipes": len(project.get("pipes", [])),
        "valves": len(project.get("valves", [])),
    }
