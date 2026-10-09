# Data acquisition and verification

The repository distributes code, aggregate profiles and analytical results. Obtain the source CSVs separately; raw data and row-level identifier lists are not included in the current public snapshot.

## Source and limits

- [Kaggle competition data](https://www.kaggle.com/competitions/playground-series-s6e9/data): `train.csv`, `test.csv` and `sample_submission.csv`.
- [Competition rules](https://www.kaggle.com/competitions/playground-series-s6e9/rules): review the applicable conditions using your own Kaggle account before downloading or reusing the data.
- [Reference notebook](https://www.kaggle.com/code/thuandao/predicting-electric-vehicle-full-eda): provenance reference for the separate original dataset, `EV_Adoption_and_Range_Anxiety_Dataset.csv`. Check the original dataset's own terms; competition rules do not establish its redistribution rights.

The existing snapshot was acquired from a public repository referenced by that notebook. Its filenames, sizes and SHA-256 values are pinned in [source_manifest.json](../metadata/source_manifest.json). **Direct comparison with a fresh official Kaggle download remains unverified.** A matching local checksum establishes identity with the pinned snapshot, not source authenticity or permission to redistribute.

## Verify your downloaded files

1. Download the three competition files from Kaggle after reviewing its terms. Obtain the original reference file separately from its original publisher.
2. Extract them into a separate directory; keep the four filenames unchanged.
3. Compare against the pinned manifest:

   ```powershell
   python scripts/verify_source_download.py --directory D:/downloads/ev-official
   ```

   For just the official competition download, use `--competition-only`; this does not verify the reference file.

4. If all requested files match, place them in `data/raw/kaggle/` and follow the [runtime instructions](pipelines/standalone_pipeline.md). A mismatch stops verification. Do not change pinned hashes merely to make the check pass: first establish which source/version changed.

The verifier reads files without uploading data or modifying the manifest. Do not commit downloaded CSVs or redistribute them based solely on their being described as synthetic. Published identifier profiles retain counts rather than listing individual `Buyer_ID` values.
