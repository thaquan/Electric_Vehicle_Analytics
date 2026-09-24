"""Calculate reference Gold counts from the exact local train snapshot."""
import hashlib
import json
from pathlib import Path

import pandas as pd
from gold_rules import band_label, validate_band

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = json.loads((ROOT / "metadata/gold_spec.json").read_text())
    manifest = json.loads((ROOT / "metadata/source_manifest.json").read_text(encoding="utf-8-sig"))
    entry = next(e for e in manifest["files"] if e["name"] == "train.csv")
    path = ROOT / "data/raw/kaggle/train.csv"
    with path.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest().upper() != entry["sha256"]:
            raise ValueError("Train snapshot checksum mismatch")
    frame = pd.read_csv(path)
    frame["yes"] = frame.Will_Buy_EV.eq("Yes").astype("int64")
    if len(frame) != spec["expected_rows"] or int(frame.yes.sum()) != spec["expected_yes"]:
        raise ValueError("Train totals mismatch")
    for name, band in spec["bands"].items():
        validate_band(band)
        frame[name] = frame[band["column"]].map(lambda value: band_label(value, band))
    segments = []
    for dimension in spec["segments"]:
        grouped = frame.groupby(dimension, dropna=False).yes.agg(["count", "sum"])
        if int(grouped["count"].sum()) != len(frame) or int(grouped["sum"].sum()) != spec["expected_yes"]:
            raise ValueError(f"Segment reconciliation failed: {dimension}")
        for label, row in grouped.iterrows():
            segments.append({"segment_dimension": dimension, "segment_value": str(label), "respondent_count": int(row["count"]), "yes_count": int(row["sum"])})
    result = {"verification_scope": "Local train snapshot reference; not Fabric Gold execution", "source_sha256": entry["sha256"],
              "respondent_count": len(frame), "yes_count": int(frame.yes.sum()), "no_count": int(len(frame) - frame.yes.sum()),
              "purchase_intent_rate": float(frame.yes.mean()), "segments": segments}
    (ROOT / "metadata/gold_expected_metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "segments"}))
    print(f"Reconciled {len(segments)} groups across {len(spec['segments'])} dimensions")


if __name__ == "__main__":
    main()
