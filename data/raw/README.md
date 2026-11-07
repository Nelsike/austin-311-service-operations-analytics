# Source input

The full City CSV is kept locally and excluded from Git. The repository includes official field metadata and the source fingerprint, not the bulk request records.

Place the frozen official export at `data/raw/source_snapshot.csv` to reproduce the documented v1 results. The expected SHA-256 fingerprint is recorded in `reports/run_manifest.json` and `source_provenance.json`.

Dataset: [City of Austin Transportation and Public Works 311 requests](https://data.austintexas.gov/d/38mr-dwji). Field definitions: [official metadata](https://data.austintexas.gov/api/views/38mr-dwji.json).

For a new snapshot, use `src/download_source.py` as described in the root README. Pass its paired CSV and metadata into the pipeline and choose a reporting cutoff after the cohort's observed updates. A new export can revise historical statuses and change the results; it does not replace the frozen v1 input automatically.

The source input has 376,135 rows across multiple years. The analysis selects 73,690 records created in calendar 2025. Raw data, generated detail tables and the SQLite database remain available in the complete local project delivery.
