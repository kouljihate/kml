def export_epanet_inp(project):
    project_name = project["project"]["name"]
    return "[TITLE]\\n; " + project_name + "\\n\\n[JUNCTIONS]\\n"
