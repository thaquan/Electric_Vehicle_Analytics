"""Prepare an isolated measure-description change and its exact rollback payload."""
import base64
import copy
from pathlib import Path
from recovery_common import read_json, write_json, require

OUT = Path(__file__).resolve().parents[1] / "output/phase8"
MARKER = "Phase 8 Test rollback drill; calculation unchanged."


def prepare():
    original = read_json(OUT / "model_definition_a.json")["body"]["definition"]
    original = copy.deepcopy(original)
    original["parts"] = [p for p in original["parts"] if p["path"] != ".platform"]
    changed = copy.deepcopy(original)
    part = next(p for p in changed["parts"] if p["path"] == "definition/tables/EV Respondents.tmdl")
    text = base64.b64decode(part["payload"]).decode("utf-8")
    before = "Number of labeled train respondents in the current filter context."
    require(text.count(before) == 1, "Expected one Respondents description")
    part["payload"] = base64.b64encode(text.replace(before, MARKER).encode()).decode()
    write_json(OUT / "rollback_a.json", {"definition": original})
    write_json(OUT / "release_b.json", {"definition": changed})
    print("Prepared B (description only) and A rollback from the deployed Test definition")


if __name__ == "__main__":
    prepare()
