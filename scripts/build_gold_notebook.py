"""Build the dynamic, pipeline-ready Gold notebook."""
import json
from notebook_artifacts import ROOT, EXIT_CELL, write_notebook


def build():
    config = json.loads((ROOT / "metadata/fabric_workspace.json").read_text())
    spec = json.loads((ROOT / "metadata/gold_spec.json").read_text())
    expected = json.loads((ROOT / "metadata/gold_expected_metrics.json").read_text())
    runtime = {key: config[key] for key in ("workspace_id", "silver_lakehouse_id", "gold_lakehouse_id")}
    constants = "import json\nimport notebookutils\n" + "\n".join(f"{key} = json.loads({json.dumps(value)!r})" for key, value in (("CONFIG", runtime), ("DEFAULT_SPEC", spec), ("EXPECTED", expected)))
    cells = [
        ('pipeline_run_id = ""\nrun_mode = "publish"\nsilver_run_id = ""\ngold_run_id = ""\n', True),
        (constants, False),
        ((ROOT / "scripts/pipeline_contract.py").read_text() + "\n" + (ROOT / "scripts/gold_rules.py").read_text() + "\n" + (ROOT / "scripts/fabric_verify.py").read_text(), False),
        ((ROOT / "scripts/fabric_gold.py").read_text(), False),
        (EXIT_CELL, False),
    ]
    write_notebook("NB_EV_Silver_To_Gold", "LH_EV_Gold", config["gold_lakehouse_id"], config["workspace_id"], cells, "Publish and verify Gold for the supplied Silver run; supports PL_EV_E2E.")


if __name__ == "__main__":
    build()
