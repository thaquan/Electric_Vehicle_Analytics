"""Generate a self-contained Gold notebook for Fabric Git and manual import."""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    config = json.loads((ROOT / "metadata/fabric_workspace.json").read_text())
    spec = json.loads((ROOT / "metadata/gold_spec.json").read_text())
    expected = json.loads((ROOT / "metadata/gold_expected_metrics.json").read_text())
    name = "NB_EV_Silver_To_Gold"
    dependencies = {"lakehouse": {
        "default_lakehouse": config["gold_lakehouse_id"],
        "default_lakehouse_name": "LH_EV_Gold",
        "default_lakehouse_workspace_id": config["workspace_id"],
        "known_lakehouses": [{"id": config["gold_lakehouse_id"]}, {"id": config["silver_lakehouse_id"]}],
    }}
    runtime_config = {key: config[key] for key in ("workspace_id", "silver_lakehouse_id", "gold_lakehouse_id")}
    parameters = "import json\n" + "\n".join(f"{key} = json.loads({json.dumps(value)!r})" for key, value in (("CONFIG", runtime_config), ("SPEC", spec), ("EXPECTED", expected)))
    cells = [parameters, (ROOT / "scripts/gold_rules.py").read_text(), (ROOT / "scripts/fabric_gold.py").read_text()]
    notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "kernelspec": {"display_name": "Synapse PySpark", "language": "python", "name": "synapse_pyspark"},
        "language_info": {"name": "python"}, "dependencies": dependencies}, "cells": [
        {"cell_type": "markdown", "id": "intro", "metadata": {}, "source": [
            "# NB_EV_Silver_To_Gold\n", "Default Lakehouse: LH_EV_Gold. Train-only purchase-intent analysis.\n",
            "Run all; success requires the published marker. See docs/gold_runbook.md. No external Python helper upload is needed.\n"]}
    ]}
    for index, cell in enumerate(cells):
        compile(cell, f"gold-cell-{index}", "exec")
        notebook["cells"].append({"cell_type": "code", "id": f"gold-{index}", "metadata": {}, "execution_count": None, "outputs": [], "source": cell.splitlines(keepends=True)})
    target = ROOT / f"notebooks/{name}.ipynb"
    target.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
    folder = ROOT / f"{name}.Notebook"
    folder.mkdir(exist_ok=True)
    platform = folder / ".platform"
    if not platform.exists():
        platform.write_text(json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "Notebook", "displayName": name, "description": "Publish verified train-only EV purchase-intent Gold tables."},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}}, indent=2) + "\n", encoding="utf-8")
    def meta(value):
        return "# METADATA ********************\n" + "\n".join("# META " + line for line in json.dumps(value, indent=2).splitlines())
    source = "# Fabric notebook source\n\n" + meta({"kernel_info": {"name": "synapse_pyspark"}, "dependencies": dependencies})
    for cell in cells:
        source += "\n\n# CELL ********************\n\n" + cell + "\n\n" + meta({"language": "python", "language_group": "synapse_pyspark"})
    compile(source, "gold-notebook-content.py", "exec")
    (folder / "notebook-content.py").write_text(source + "\n", encoding="utf-8")
    print(f"Built {name}: Fabric Git and ipynb; embedded configuration, reference metrics and rules.")


if __name__ == "__main__":
    build()
