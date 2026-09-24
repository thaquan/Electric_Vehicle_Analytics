"""Pure validation of pipeline arguments and immutable publication markers."""
import re


def check_run_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{8}T\d{12}Z", value):
        raise ValueError("A valid publication run ID is required")
    return value


def check_pipeline_id(value, required=False):
    if required and not value:
        raise ValueError("Pipeline run ID was not injected; check the notebook parameter cell")
    if value and not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value):
        raise ValueError("Invalid pipeline run ID")


def require_publication(marker, stage, run_id, pipeline_run_id="", silver_run_id=None):
    check_run_id(run_id)
    if marker.get("status") != "published" or marker.get("run_id") != run_id:
        raise ValueError("Missing or mismatched publication marker")
    if pipeline_run_id and marker.get("pipeline_run_id") != pipeline_run_id:
        raise ValueError("Publication belongs to another pipeline execution")
    suffix = run_id.lower()
    if stage == "silver":
        expected = {f"silver_train_{suffix}": 668665, f"silver_test_{suffix}": 286571, f"silver_original_reference_{suffix}": 10000}
    elif stage == "gold":
        expected = {f"fact_ev_purchase_intent_{suffix}": 668665, f"agg_ev_kpi_{suffix}": 1, f"agg_ev_segments_{suffix}": 35}
        if marker.get("silver_run_id") != silver_run_id:
            raise ValueError("Gold does not reference the selected Silver run")
        if marker.get("respondent_count") != 668665 or marker.get("yes_count") != 116779:
            raise ValueError("Gold KPI marker mismatch")
    else:
        raise ValueError("Unsupported publication stage")
    tables = marker.get("tables", [])
    if len(tables) != len(expected) or {t.get("table"): t.get("rows") for t in tables} != expected:
        raise ValueError("Publication table set/count mismatch")
    return expected
