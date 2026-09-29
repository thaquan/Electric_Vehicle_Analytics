"""Verify a release directory or ZIP using only the Python standard library."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_entries(read, names):
    manifest_bytes = read("package_manifest.json")
    expected_hash = read("package_manifest.sha256").decode("ascii").split()[0]
    if digest(manifest_bytes) != expected_hash:
        raise ValueError("Package manifest checksum mismatch")
    manifest = json.loads(manifest_bytes)
    paths = [entry["path"] for entry in manifest["files"]]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate inventory paths")
    for path in paths:
        if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts or "\\" in path or ":" in path:
            raise ValueError("Unsafe inventory path")
    expected = set(paths) | {"package_manifest.json", "package_manifest.sha256"}
    if set(names) != expected or len(names) != len(expected):
        raise ValueError("Missing, duplicate or unexpected package files")
    for entry in manifest["files"]:
        data = read(entry["path"])
        if len(data) != entry["bytes"] or digest(data) != entry["sha256"]:
            raise ValueError("Package file checksum mismatch: " + entry["path"])
    snapshot_manifest = read("snapshot/manifest.json")
    if digest(snapshot_manifest) != manifest["snapshot_manifest_sha256"]:
        raise ValueError("Snapshot does not match the release")
    snapshot = json.loads(snapshot_manifest)
    if read("snapshot/manifest.sha256").decode("ascii").split()[0] != digest(snapshot_manifest):
        raise ValueError("Snapshot checksum sidecar mismatch")
    if len(snapshot["tables"]) != 8:
        raise ValueError("Expected eight Parquet tables")
    for entry in snapshot["tables"] + snapshot["evidence_files"]:
        data = read("snapshot/" + entry["path"])
        if len(data) != entry["bytes"] or digest(data) != entry["sha256"]:
            raise ValueError("Snapshot file mismatch: " + entry["path"])
    return {"status": "passed", "files": len(names), "parquet_tables": len(snapshot["tables"]),
            "package_manifest_sha256": digest(manifest_bytes), "snapshot_manifest_sha256": digest(snapshot_manifest),
            "scope": "Package inventory and file integrity; not a Fabric recovery test"}


def verify(path):
    path = Path(path)
    if path.is_dir():
        names = [p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file()]
        def read(relative):
            target = (path / relative).resolve()
            if not target.is_relative_to(path.resolve()):
                raise ValueError("Path escapes package")
            return target.read_bytes()
        return verify_entries(read, names)
    sidecar = path.with_suffix(path.suffix + ".sha256")
    expected = sidecar.read_text(encoding="ascii").split()[0]
    if digest(path.read_bytes()) != expected:
        raise ValueError("ZIP checksum mismatch")
    with zipfile.ZipFile(path) as archive:
        names = [i.filename for i in archive.infolist() if not i.is_dir()]
        root = "EV_Analytics_Recovery/"
        if not all(n.startswith(root) for n in names):
            raise ValueError("Unexpected ZIP root")
        result = verify_entries(lambda relative: archive.read(root + relative), [n[len(root):] for n in names])
        result["zip_sha256"] = expected
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path(__file__).resolve().parent)
    print(json.dumps(verify(parser.parse_args().path), indent=2))
