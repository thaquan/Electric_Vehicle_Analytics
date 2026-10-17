# Clean rehearsal and controlled retention

`scripts/prepare_clean_rehearsal.py` creates a new source directory from tracked
and non-ignored working-tree files, with a SHA-256 inventory and the base commit.
It excludes ignored data, runtime caches, output and Git internals. Its manifest
explicitly records whether the working tree is dirty; a local source snapshot
does not claim that its bytes came from a hosted CI build.

```powershell
python scripts/prepare_clean_rehearsal.py --output output/rehearsal-new
python -m venv output/rehearsal-new/venv
output/rehearsal-new/venv/Scripts/python.exe -m pip install -r output/rehearsal-new/source/requirements/requirements_dev.txt -c output/rehearsal-new/source/requirements/constraints-local-py313.txt
output/rehearsal-new/venv/Scripts/python.exe -m pip check
```

Run the snapshot's unit suite with that virtual environment. For the full data
run, use the snapshot as the working directory, initialize its Java/Hadoop helper
with explicit paths to independently installed helpers, and pass absolute raw
input and output paths. Verify all four CSVs before processing. The six stages
must complete and write `run_report.json` with `status=passed` and a sealed
`published.json`. Compare all eight Gold tables with a retained verified run
using `scripts/phase11_reconcile.py`, which checks schemas and duplicate-sensitive
row equality and ignores only the three named lineage value columns.

Use a new run ID after any source/configuration change. The context gate seals
every Python file under `src/` and `scripts/`; editing even a delivery helper
during a running pipeline correctly invalidates the context. Freeze the source
snapshot before testing to avoid concurrent editing invalidating a data run.

## Retention decisions

| Artifact | Decision and reason |
| --- | --- |
| Current `.Report` and `.SemanticModel` | Authoritative paired release source. Includes the referenced shared base theme so Service readback compares the complete package. |
| `models/SM_EV_Analytics/` | Retain as a labeled historical 12-measure export; recovery/history references still use it. Never package it instead of the current 29-measure model. |
| Old `docs/screenshots/customer_profile.png` | Removed from the current tree after confirming only documentation referenced it. A verified local backup and Git history remain; see the retirement inventory below. |
| `output/`, `.tools/`, raw data and local evidence | Ignored local artifacts. Keep accepted releases, operation journals, rollback captures and referenced Gold runs until their replacements are verified. |
| Public Git history | Preserve the existing cleaned history. Any further rewrite or remote deletion needs a separately scoped, backed-up operation. |

The unused historical screenshot was retired with its SHA-256, Git blob and
recovery commit in [the retirement inventory](../evidence/retired_artifacts_20261017.json).
Recover it without changing history, if needed:

```powershell
git restore --source=c4cd4a230d067ca9ccd5a0403863f864f1edf75e -- docs/screenshots/customer_profile.png
```

No data snapshot, rollback package or remote branch was deleted. The preparation
helpers never delete historical artifacts. Remove another retained artifact only after checking references,
recording its checksum and replacement, verifying recovery, and identifying the
exact deletion target. The current acceptance inventory is evidence of those
decisions; it is not a destructive cleanup script.
