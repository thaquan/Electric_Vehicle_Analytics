"""Write consistent Fabric Git/ipynb notebooks including real parameter cells."""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXIT_CELL = 'if notebookutils.runtime.context.get("isForPipeline") or notebookutils.runtime.context.get("isReferenceRun"):\n    notebookutils.notebook.exit(json.dumps(result))\n'


def write_notebook(name, lakehouse_name, lakehouse_id, workspace_id, cells, description):
    dependencies = {"lakehouse": {"default_lakehouse": lakehouse_id, "default_lakehouse_name": lakehouse_name,
                    "default_lakehouse_workspace_id": workspace_id, "known_lakehouses": [{"id": lakehouse_id}]}}
    notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "kernelspec": {"display_name": "Synapse PySpark", "language": "python", "name": "synapse_pyspark"},
        "language_info": {"name": "python"}, "dependencies": dependencies}, "cells": []}
    def meta(value):
        return "# METADATA ********************\n" + "\n".join("# META " + line for line in json.dumps(value, indent=2).splitlines())
    source = "# Fabric notebook source\n\n" + meta({"kernel_info": {"name": "synapse_pyspark"}, "dependencies": dependencies})
    for index, (body, parameter_cell) in enumerate(cells):
        compile(body, f"{name}-cell-{index}", "exec")
        notebook["cells"].append({"cell_type": "code", "id": f"cell-{index}", "metadata": {"tags": ["parameters"]} if parameter_cell else {},
                                 "execution_count": None, "outputs": [], "source": body.splitlines(keepends=True)})
        source += "\n\n# " + ("PARAMETERS CELL" if parameter_cell else "CELL") + " ********************\n\n" + body
        source += "\n\n" + meta({"language": "python", "language_group": "synapse_pyspark"})
    compile(source, name, "exec")
    folder = ROOT / f"{name}.Notebook"
    folder.mkdir(exist_ok=True)
    platform = folder / ".platform"
    if not platform.exists():
        platform.write_text(json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "Notebook", "displayName": name, "description": description},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}}, indent=2) + "\n", encoding="utf-8")
    (folder / "notebook-content.py").write_text(source + "\n", encoding="utf-8")
    (ROOT / f"notebooks/{name}.ipynb").write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
    print(f"Built {name} (Fabric Git + ipynb)")
