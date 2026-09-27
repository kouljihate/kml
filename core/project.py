import copy
import json
from datetime import datetime, timezone


def create_empty_project():
    return {
        "project": {
            "project_id": "new_farm_project",
            "name": "New Farm Irrigation Project",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "updated_utc": datetime.now(timezone.utc).isoformat(),
            "coordinate_system": "EPSG:4326",
            "working_crs": None,
            "source_flow_m3h": 10.0,
        },
        "land": None,
        "water_points": [],
        "basins": [],
        "sectors": [],
        "zones": [],
        "rows": [],
        "trees": [],
        "pipes": [],
        "valves": [],
        "fittings": [],
        "obstacles": [],
        "elevation_points": [],
        "hydraulic_results": {},
        "warnings": [],
    }


def initialize_project_state(session_state):
    if "farm_project" not in session_state:
        session_state.farm_project = create_empty_project()

    if "project_history" not in session_state:
        session_state.project_history = []


def save_history_snapshot(session_state, action_name):
    session_state.project_history.append({
        "action": action_name,
        "project": copy.deepcopy(session_state.farm_project),
    })

    session_state.project_history = session_state.project_history[-20:]


def update_project_timestamp(project):
    project["project"]["updated_utc"] = datetime.now(
        timezone.utc
    ).isoformat()


def project_to_json(project):
    return json.dumps(project, ensure_ascii=False, indent=2)


def project_from_json(json_text):
    return json.loads(json_text)