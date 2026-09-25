"""Band definitions shared by local reference and generated Spark SQL."""
import math
import re
from bisect import bisect_right


def require_gold_context(context, config):
    if (context.get("defaultLakehouseId") != config["gold_lakehouse_id"]
            or context.get("defaultLakehouseWorkspaceId") != config["workspace_id"]):
        raise RuntimeError(f"Expected LH_EV_Gold in WS_EV_Analytics; actual Lakehouse={context.get('defaultLakehouseId')!r}, workspace={context.get('defaultLakehouseWorkspaceId')!r}. Sync the latest notebook and start a fresh run so its first %%configure cell is applied.")


def validate_band(band):
    edges, labels = band["edges"], band["labels"]
    if len(labels) != len(edges) + 1 or edges != sorted(set(edges)):
        raise ValueError("Band edges must increase and have one more label than edges")
    if not all(math.isfinite(float(edge)) for edge in edges):
        raise ValueError("Band edges must be finite")


def band_label(value, band):
    if value is None or not math.isfinite(float(value)):
        return "Unknown"
    return band["labels"][bisect_right(band["edges"], float(value))]


def band_sql(band):
    validate_band(band)
    column = band["column"]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", column):
        raise ValueError("Invalid source column")
    def quoted(value):
        return "'" + str(value).replace("'", "''") + "'"
    clauses = [f"WHEN `{column}` IS NULL THEN 'Unknown'"]
    clauses += [f"WHEN `{column}` < {edge} THEN {quoted(label)}" for edge, label in zip(band["edges"], band["labels"])]
    return "CASE " + " ".join(clauses) + " ELSE " + quoted(band["labels"][-1]) + " END"
