"""Upload the verified Gold snapshot and prepare a Test restore notebook.

No table writes occur here. The notebook validates every input before restoring
to a fresh target. Existing files must match exactly; conflicting files fail.
"""
import base64
import hashlib
import json
from pathlib import Path

from fabric_test_api import Client, WORKSPACE
from recovery_common import check_snapshot, read_json, validate_config, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/phase8"


def prepare():
    config = read_json(ROOT / "config/environments/test.json")
    validate_config(config)
    assert config["workspace_id"] == WORKSPACE
    snapshot = ROOT / "output/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z"
    check_snapshot(snapshot)
    OUT.mkdir(parents=True, exist_ok=True)
    client = Client()
    lakehouse = config["lakehouse_id"]
    files = [(p, "Files/recovery/snapshot/" + p.relative_to(snapshot).as_posix())
             for p in sorted(snapshot.rglob("*")) if p.is_file()]
    files += [(ROOT / "scripts" / name, "Files/recovery/scripts/" + name) for name in
              ["fabric_restore_gold.py", "recovery_common.py", "export_gold_snapshot.py", "star_schema.py"]]
    files += [(ROOT / "config/environments/test.json", "Files/recovery/recovery.config.json")]
    evidence = []
    for source, relative in files:
        payload = source.read_bytes()
        url = f"https://onelake.blob.fabric.microsoft.com/{WORKSPACE}/{lakehouse}/{relative}"
        try:
            client.request(url, "PUT", payload, {"x-ms-blob-type": "BlockBlob",
                           "x-ms-version": "2023-11-03", "If-None-Match": "*",
                           "Content-Type": "application/octet-stream"})
        except RuntimeError as error:
            if "HTTP 409" not in str(error) and "HTTP 412" not in str(error):
                raise
        _, _, actual = client.request(url, headers={"x-ms-version": "2023-11-03"})
        assert actual == payload, f"Target file differs: {relative}"
        evidence.append({"path": relative, "bytes": len(actual), "sha256": hashlib.sha256(actual).hexdigest()})
        write_json(OUT / "upload_verification.json", {"status": "in_progress", "files": evidence})
        print("Verified", relative, flush=True)
    write_json(OUT / "upload_verification.json", {"status": "passed", "workspace_id": WORKSPACE,
               "lakehouse_id": lakehouse, "files": evidence})
    nb = read_json(ROOT / "notebooks/NB_EV_Restore_Gold.ipynb")
    nb["metadata"]["dependencies"] = {"lakehouse": {"default_lakehouse": lakehouse,
        "default_lakehouse_name": config["lakehouse_name"], "default_lakehouse_workspace_id": WORKSPACE}}
    configure = "%%configure -f\n" + json.dumps({"defaultLakehouse": {
        "name": config["lakehouse_name"], "id": lakehouse, "workspaceId": WORKSPACE}})
    nb["cells"] = [{"cell_type": "code", "metadata": {}, "execution_count": None,
                     "outputs": [], "source": configure.splitlines(True)}] + nb["cells"][1:]
    nb["cells"][1]["source"] = ['MODE = "restore"\n',
        'CONFIG_PATH = "/lakehouse/default/Files/recovery/recovery.config.json"\n']
    nb["cells"][-1]["source"] += [
        '\nPath("/lakehouse/default/Files/recovery/phase8_restore_result.json").write_text(json.dumps(result, indent=2))\n']
    write_json(OUT / "restore.ipynb", nb)
    body = {"displayName": "NB_EV_Test_Restore_Gold", "description": "Restore and verify the pinned Gold snapshot in Test.",
            "definition": {"format": "ipynb", "parts": [{"path": "notebook-content.ipynb",
             "payloadType": "InlineBase64", "payload": base64.b64encode(json.dumps(nb).encode()).decode()}]}}
    write_json(OUT / "restore_notebook_request.json", body)


if __name__ == "__main__":
    prepare()
