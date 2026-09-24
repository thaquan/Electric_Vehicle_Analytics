"""Create reproducibility and first-pass profiling artifacts from raw EV CSVs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIRECTORY = ROOT / "data" / "raw" / "kaggle"
METADATA_DIRECTORY = ROOT / "metadata"
DOCS_DIRECTORY = ROOT / "docs"
NUMERIC_COLUMNS = {
    "id",
    "Age",
    "Annual_Income_USD",
    "Daily_Commute_km",
    "Number_of_Cars_Owned",
    "Charging_Stations_Near_Home",
    "Charging_Stations_Near_Work",
}
ROLES = {
    "id": "Competition record key",
    "Buyer_ID": "Original-source record key",
    "Will_Buy_EV": "EV purchase-interest target",
    "Age": "Buyer demographic",
    "Gender": "Buyer demographic",
    "Annual_Income_USD": "Financial attribute",
    "City_Type": "Location segment",
    "Daily_Commute_km": "Mobility attribute",
    "Number_of_Cars_Owned": "Vehicle ownership",
    "Current_Car_Type": "Current vehicle",
    "Charging_Stations_Near_Home": "Charging infrastructure",
    "Charging_Stations_Near_Work": "Charging infrastructure",
    "Home_Charging_Possible": "Charging accessibility",
    "Environmental_Concern_Level": "Environmental attitude",
    "Subsidy_Available": "Policy/incentive",
    "Range_Anxiety_Level": "EV adoption barrier",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def profile_csv(path: Path) -> dict:
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        fields = reader.fieldnames or []
        numeric = {
            field: {"null_count": 0, "count": 0, "sum": 0.0, "sum_sq": 0.0, "min": None, "max": None}
            for field in fields if field in NUMERIC_COLUMNS
        }
        categorical = {field: {"null_count": 0, "values": Counter()} for field in fields if field not in NUMERIC_COLUMNS}
        rows = 0
        for rows, row in enumerate(reader, start=1):
            for field in fields:
                value = (row[field] or "").strip()
                if field in numeric:
                    stats = numeric[field]
                    if not value:
                        stats["null_count"] += 1
                        continue
                    number = float(value)
                    stats["count"] += 1
                    stats["sum"] += number
                    stats["sum_sq"] += number * number
                    stats["min"] = number if stats["min"] is None else min(stats["min"], number)
                    stats["max"] = number if stats["max"] is None else max(stats["max"], number)
                else:
                    stats = categorical[field]
                    if not value:
                        stats["null_count"] += 1
                    else:
                        stats["values"][value] += 1

    column_profiles = []
    for field in fields:
        if field in numeric:
            stats = numeric[field]
            count = stats["count"]
            mean = stats["sum"] / count if count else None
            variance = (stats["sum_sq"] - count * mean * mean) / (count - 1) if count > 1 else 0.0
            column_profiles.append({
                "name": field, "type": "numeric", "null_count": stats["null_count"],
                "null_percentage": round(100 * stats["null_count"] / rows, 6) if rows else 0,
                "min": stats["min"], "max": stats["max"], "mean": round(mean, 6) if mean is not None else None,
                "stddev": round(math.sqrt(max(variance, 0.0)), 6),
            })
        else:
            stats = categorical[field]
            column_profiles.append({
                "name": field, "type": "categorical", "null_count": stats["null_count"],
                "null_percentage": round(100 * stats["null_count"] / rows, 6) if rows else 0,
                "distinct_count": len(stats["values"]),
                "value_counts": dict(sorted(stats["values"].items(), key=lambda item: (-item[1], item[0]))),
            })
    return {"file": path.name, "data_rows": rows, "columns": fields, "column_profiles": column_profiles}


def main() -> None:
    METADATA_DIRECTORY.mkdir(exist_ok=True)
    DOCS_DIRECTORY.mkdir(exist_ok=True)
    files = sorted(DATA_DIRECTORY.glob("*.csv"))
    profiles = [profile_csv(path) for path in files]
    profile_by_file = {profile["file"]: profile for profile in profiles}
    manifest = {
        "source": "Kaggle Playground Series S6E9: Predicting Electric Vehicle Purchases",
        "competition_url": "https://www.kaggle.com/competitions/playground-series-s6e9",
        "notebook_reference": "https://www.kaggle.com/code/thuandao/predicting-electric-vehicle-full-eda",
        "acquisition_note": "Retrieved from the public repository referenced by the Kaggle notebook; validate against a direct Kaggle download when API access is configured.",
        "profiled_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": [{"name": path.name, "bytes": path.stat().st_size, "data_rows": profile_by_file[path.name]["data_rows"], "columns": profile_by_file[path.name]["columns"], "sha256": sha256(path)} for path in files],
    }
    (METADATA_DIRECTORY / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (METADATA_DIRECTORY / "profiling_summary.json").write_text(json.dumps(profiles, indent=2), encoding="utf-8")
    categorical = {profile["file"]: [column for column in profile["column_profiles"] if column["type"] == "categorical"] for profile in profiles}
    (METADATA_DIRECTORY / "categorical_profile.json").write_text(json.dumps(categorical, indent=2), encoding="utf-8")

    unique_columns = {}
    for profile in profiles:
        for column in profile["column_profiles"]:
            unique_columns.setdefault(column["name"], column)
    lines = ["# Data dictionary", "", "Generated from the first profiling run. Column meanings come from the Kaggle notebook; observed types and categories come from the local CSV files.", "", "| Field | Logical type | Role |", "| --- | --- | --- |"]
    for name, column in unique_columns.items():
        lines.append(f"| {name} | {'Numeric' if column['type'] == 'numeric' else 'Categorical'} | {ROLES.get(name, 'Not documented')} |")
    lines.extend(["", "Important: this is a synthetic competition dataset. Analytical results describe this dataset only and are not causal or population-level EV-market claims.", ""])
    (DOCS_DIRECTORY / "data_dictionary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Profiled {len(files)} CSV files. Artifacts written to {METADATA_DIRECTORY} and {DOCS_DIRECTORY}.")


if __name__ == "__main__":
    main()
