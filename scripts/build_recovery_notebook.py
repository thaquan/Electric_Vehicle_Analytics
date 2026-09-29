"""Create a portable notebook without embedding a source workspace binding."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    code = [
        'MODE = "preflight"  # Change to "restore" only in the separate recovery workspace.\n'
        'CONFIG_PATH = "/lakehouse/default/Files/recovery/recovery.config.json"\n',
        'import sys\nimport json\nfrom pathlib import Path\n'
        'import notebookutils\n'
        'sys.path.insert(0, "/lakehouse/default/Files/recovery/scripts")\n'
        'from fabric_restore_gold import restore\n'
        'if MODE not in ("preflight", "restore"):\n    raise ValueError("MODE must be preflight or restore")\n'
        'config = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))\n'
        'result = restore(spark, notebookutils.runtime.context, config, execute=(MODE == "restore"))\n'
        'print(json.dumps(result, indent=2))\n',
    ]
    cells = [{"cell_type": "markdown", "metadata": {}, "id": "instructions", "source": [
        "# Restore verified EV Gold v2\n",
        "Attach the NEW recovery lakehouse as default. Upload snapshot/, scripts/ and recovery.config.json to Files/recovery/.\n",
        "Run preflight first; then set MODE to restore. No pipeline execution. Existing tables are never overwritten.\n",
        "This notebook has not yet been run in the separate recovery workspace.\n"]}]
    for i, source in enumerate(code):
        compile(source, f"restore-cell-{i}", "exec")
        cells.append({"cell_type": "code", "id": f"cell-{i}", "metadata": {},
                      "execution_count": None, "outputs": [], "source": source.splitlines(keepends=True)})
    notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "kernelspec": {"display_name": "Synapse PySpark", "language": "python", "name": "synapse_pyspark"},
        "language_info": {"name": "python"}}, "cells": cells}
    destination = ROOT / "notebooks/NB_EV_Restore_Gold.ipynb"
    destination.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    build()
