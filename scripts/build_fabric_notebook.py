"""Build the importable NB_EV_Bronze_To_Silver notebook from its source script."""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    config = json.loads((ROOT / "metadata/fabric_workspace.json").read_text())
    code = (ROOT / "scripts/fabric_silver.py").read_text()
    compile(code, "fabric_silver.py", "exec")
    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Synapse PySpark", "language": "python", "name": "synapse_pyspark"},
            "language_info": {"name": "python"},
            "dependencies": {"lakehouse": {
                "default_lakehouse": config["silver_lakehouse_id"],
                "default_lakehouse_name": "LH_EV_Silver",
                "default_lakehouse_workspace_id": config["workspace_id"],
                "known_lakehouses": [{"id": config["silver_lakehouse_id"]}, {"id": config["bronze_lakehouse_id"]}],
            }},
        },
        "cells": [
            {"cell_type": "markdown", "id": "intro", "metadata": {}, "source": [
                "# NB_EV_Bronze_To_Silver\n",
                "Default Lakehouse: LH_EV_Silver. Source: LH_EV_Bronze. See docs/bronze_silver.md for prerequisites.\n",
                "Validate all sources, then publish separate versioned Delta tables and a success marker."
            ]},
            {"cell_type": "code", "id": "transform", "metadata": {}, "execution_count": None, "outputs": [], "source": code.splitlines(keepends=True)},
        ],
    }
    target = ROOT / "notebooks/NB_EV_Bronze_To_Silver.ipynb"
    target.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
    print(target)
    git_folder = ROOT / "NB_EV_Bronze_To_Silver.Notebook"
    git_folder.mkdir(exist_ok=True)
    platform_path = git_folder / ".platform"
    if not platform_path.exists():
        platform_path.write_text(json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "Notebook", "displayName": "NB_EV_Bronze_To_Silver", "description": "Validate Bronze EV sources and publish Silver Delta tables."},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid4())},
        }, indent=2) + "\n", encoding="utf-8")
    def meta(value):
        return "\n".join("# META " + line for line in json.dumps(value, indent=2).splitlines())
    header = {"kernel_info": {"name": "synapse_pyspark"}, "dependencies": notebook["metadata"]["dependencies"]}
    content = "# Fabric notebook source\n\n# METADATA ********************\n" + meta(header)
    content += "\n\n# CELL ********************\n\n" + code
    content += "\n# METADATA ********************\n" + meta({"language": "python", "language_group": "synapse_pyspark"}) + "\n"
    compile(content, "notebook-content.py", "exec")
    (git_folder / "notebook-content.py").write_text(content, encoding="utf-8")
    print(git_folder)


if __name__ == "__main__":
    build()
