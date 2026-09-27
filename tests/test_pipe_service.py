from services.pipe_service import add_pipe


def test_90_mm_can_supply_63_mm():
    project = {"pipes": []}

    parent_pipe = {"id": "P90-001", "diameter_mm": 90}
    child_pipe = {"id": "P63-S1-001", "diameter_mm": 63}

    result = add_pipe(project, child_pipe, parent_pipe)

    assert result["ok"] is True
    assert len(project["pipes"]) == 1
