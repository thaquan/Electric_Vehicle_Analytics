"""Read-only comparison of separately acquired CSVs with the pinned manifest."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPETITION_FILES = {"train.csv", "test.csv", "sample_submission.csv"}


def verify(directory, manifest, competition_only=False):
    results = []
    for entry in manifest["files"]:
        name = entry["name"]
        if competition_only and name not in COMPETITION_FILES:
            continue
        if Path(name).name != name or "/" in name or "\\" in name:
            raise ValueError("Manifest filename must be a basename")
        path = directory / name
        if not path.is_file():
            status = "missing"
        else:
            with path.open("rb") as stream:
                checksum = hashlib.file_digest(stream, "sha256").hexdigest()
            status = "matched" if path.stat().st_size == entry["bytes"] and checksum.lower() == entry["sha256"].lower() else "mismatch"
        results.append({"file": name, "status": status})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--competition-only", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "metadata/source_manifest.json").read_text(encoding="utf-8-sig"))
    results = verify(args.directory, manifest, args.competition_only)
    print(json.dumps({"scope": "competition files only" if args.competition_only else "all four source files", "results": results,
                      "note": "Identity with the pinned snapshot only; does not verify download provenance or redistribution rights."}, indent=2))
    return 0 if results and all(item["status"] == "matched" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
