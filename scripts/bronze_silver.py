"""Validate the pinned source snapshot and prepare separate EV Silver datasets.

Local: python scripts/bronze_silver.py
Fabric: import this module from Files/code; use prepare() before writing Delta.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SOURCES = {
    "train": "train.csv",
    "test": "test.csv",
    "original_reference": "EV_Adoption_and_Range_Anxiety_Dataset.csv",
}
INTEGERS = {"id", "Age", "Number_of_Cars_Owned", "Charging_Stations_Near_Home", "Charging_Stations_Near_Work"}
DECIMALS = {"Annual_Income_USD", "Daily_Commute_km"}
ORIGINAL_NULLABLE = {"Annual_Income_USD", "Daily_Commute_km", "Environmental_Concern_Level"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def validate_frame(frame, entry, categories, profile, key):
    """Hard failures stop publication; observed numeric bounds are warnings only."""
    errors, warnings = [], []
    if list(frame.columns) != entry["columns"]:
        return ["column names/order mismatch"], warnings
    if len(frame) != entry["data_rows"]:
        errors.append("row count mismatch")
    nullable = ORIGINAL_NULLABLE if key == "Buyer_ID" else set()
    for col in frame:
        if col not in nullable and frame[col].str.strip().eq("").any():
            errors.append(f"{col}: missing values")
        baseline = next((c for c in profile["column_profiles"] if c["name"] == col), {})
        if col in nullable and int(frame[col].str.strip().eq("").sum()) != baseline.get("null_count", 0):
            errors.append(f"{col}: null count differs from pinned profile")
    if frame[key].duplicated().any():
        errors.append(f"{key}: duplicate keys")
    for col in (INTEGERS | DECIMALS) & set(frame.columns):
        values = pd.to_numeric(frame[col], errors="coerce")
        present = ~frame[col].str.strip().eq("") if col in nullable else pd.Series(True, index=frame.index)
        if not np.isfinite(values[present]).all():
            errors.append(f"{col}: invalid/non-finite numeric values")
        if col in DECIMALS and not frame.loc[present, col].str.fullmatch(r"-?\d{1,14}(?:\.\d{1,4})?").all():
            errors.append(f"{col}: cannot represent exactly as decimal(18,4)")
        if col in INTEGERS:
            limit = 2**63 if col == "id" else 2**31
            if ((values % 1 != 0) | (values < -limit) | (values >= limit)).any():
                errors.append(f"{col}: invalid or out-of-range integer")
            if col == key and values.duplicated().any():
                errors.append(f"{col}: duplicate keys after cast")
        bounds = next(x for x in profile["column_profiles"] if x["name"] == col)
        if ((values < bounds["min"]) | (values > bounds["max"])).any():
            warnings.append(f"{col}: outside observed profile bounds")
    for category in categories:
        col = category["name"]
        if col == key:
            continue
        observed = frame.loc[~frame[col].str.strip().eq(""), col] if col in nullable else frame[col]
        if not observed.isin(category["value_counts"]).all():
            errors.append(f"{col}: category outside pinned profile")
    if "Will_Buy_EV" in frame:
        if not frame.Will_Buy_EV.isin(["Yes", "No"]).all():
            errors.append("Will_Buy_EV: expected Yes/No")
        expected = next(x["value_counts"] for x in categories if x["name"] == "Will_Buy_EV")
        if frame.Will_Buy_EV.value_counts().to_dict() != expected:
            errors.append("target distribution mismatch")
    return errors, warnings


def transform(frame, source, entry, timestamp):
    result = frame.copy()
    if source == "original_reference":
        for col in ORIGINAL_NULLABLE:
            result[col] = result[col].replace("", None)
    for col in INTEGERS & set(result.columns):
        result[col] = pd.to_numeric(result[col]).astype("int64")
    # Keep exact decimal text until Spark casts to an explicit decimal type.
    if "Will_Buy_EV" in result:
        result["will_buy_ev_flag"] = result.Will_Buy_EV.map({"Yes": 1, "No": 0}).astype("int32")
    result["source_dataset"] = source
    result["source_file"] = entry["name"]
    result["source_sha256"] = entry["sha256"]
    result["processed_at_utc"] = timestamp
    key = "Buyer_ID" if source == "original_reference" else "id"
    result["record_key"] = source + ":" + result[key].astype(str)
    return result


def prepare(raw, metadata, report_path):
    raw, metadata = Path(raw), Path(metadata)
    manifest = read_json(metadata / "source_manifest.json")
    categories = read_json(metadata / "categorical_profile.json")
    profiles = {p["file"]: p for p in read_json(metadata / "profiling_summary.json")}
    timestamp = datetime.now(timezone.utc).isoformat()
    report = {"checked_at_utc": timestamp, "status": "failed", "datasets": {}}
    frames = {}
    try:
        # Verify all four pinned files, including the submission template.
        for entry in manifest["files"]:
            path = raw / entry["name"]
            if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
                raise ValueError(f"Source snapshot mismatch: {path.name}")
            with path.open(encoding="utf-8-sig", newline="") as stream:
                if next(csv.reader(stream)) != entry["columns"]:
                    raise ValueError(f"CSV header mismatch: {path.name}")
        for source, filename in SOURCES.items():
            entry = next(e for e in manifest["files"] if e["name"] == filename)
            frame = pd.read_csv(raw / filename, dtype=str, keep_default_na=False)
            key = "Buyer_ID" if source == "original_reference" else "id"
            errors, warnings = validate_frame(frame, entry, categories[filename], profiles[filename], key)
            report["datasets"][source] = {"rows": len(frame), "errors": errors, "warnings": warnings}
            if errors:
                raise ValueError(f"{source}: {errors}")
            frames[source] = transform(frame, source, entry, timestamp)
        if set(frames["train"].id) & set(frames["test"].id):
            raise ValueError("Train/test IDs overlap")
        submission = pd.read_csv(raw / "sample_submission.csv", dtype={"id": "int64"})
        if not submission.id.equals(frames["test"].id):
            raise ValueError("Submission/test ID order mismatch")
        if "Will_Buy_EV" in frames["test"] or "will_buy_ev_flag" in frames["test"]:
            raise ValueError("Test target leakage")
        report["status"] = "passed"
    except Exception as exc:
        report["failure"] = str(exc)
        raise
    finally:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return frames


def stage_bronze(raw, bronze, metadata):
    """Copy verified bytes into content-addressed, immutable snapshot folders."""
    for entry in read_json(Path(metadata) / "source_manifest.json")["files"]:
        source = Path(raw) / entry["name"]
        if sha256(source) != entry["sha256"]:
            raise ValueError(f"Source checksum mismatch: {source.name}")
        target = Path(bronze) / entry["sha256"].lower() / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with source.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
        if sha256(target) != entry["sha256"]:
            raise ValueError(f"Bronze checksum mismatch: {target}")


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-bronze", action="store_true")
    args = parser.parse_args()
    raw, metadata = root / "data/raw/kaggle", root / "metadata"
    frames = prepare(raw, metadata, metadata / "silver_quality_report.json")
    if args.stage_bronze:
        stage_bronze(raw, root / "data/bronze", metadata)
    print(json.dumps({"status": "passed", "rows": {k: len(v) for k, v in frames.items()}}))


if __name__ == "__main__":
    main()
