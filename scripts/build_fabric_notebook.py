"""Build the pipeline-ready Bronze/Silver notebook."""
import json
from notebook_artifacts import ROOT, EXIT_CELL, write_notebook


def build():
    config = json.loads((ROOT / "metadata/fabric_workspace.json").read_text())
    cells = [
        ('pipeline_run_id = ""\nrun_mode = "publish"\n', True),
        ('import json\nimport notebookutils\n' + (ROOT / "scripts/pipeline_contract.py").read_text(), False),
        ((ROOT / "scripts/fabric_silver.py").read_text(), False),
        (EXIT_CELL, False),
    ]
    write_notebook("NB_EV_Bronze_To_Silver", "LH_EV_Silver", config["silver_lakehouse_id"], config["workspace_id"], cells, "Validate Bronze and publish Silver; supports PL_EV_E2E.")


if __name__ == "__main__":
    build()
