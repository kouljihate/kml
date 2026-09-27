from services.quantity_service import build_pipe_quantity_table


def export_pipe_quantities_csv(project):
    table = build_pipe_quantity_table(project)
    return table.to_csv(index=False).encode("utf-8")
