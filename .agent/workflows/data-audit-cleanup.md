---
description: Run the Data Audit and Cleanup process for Lekker Find
---

# Data Audit & Cleanup Workflow

This workflow automates the process of auditing, cleaning, and enriching the Lekker Find venue data (`public/lekker-find-data.json`) using Google Maps Platform and heuristic checks.

## Prerequisites

-   **Google Maps API Key**: Ensure `MAPS_API_KEY` is set in `.env` with access to:
    -   Places API (New) (Text Search, Place Details, Photos)
-   **Python Environment**:
    -   `pip install requests python-dotenv`

## Workflow Steps

### 1. Pre-Audit Analysis
Run the analysis script to inspect the current state of the data (duplicates, missing fields, suburb distribution).

```bash
python scripts/analyze_data.py
```

### 2. Execution: Cleanup & Enrichment
Run the main threaded cleanup script. This will:
-   Backup the current data to `data/backups/`.
-   Normalize suburbs (fix common street address errors).
-   Enrich data using Google Maps API (Photos, Pricing, Ratings).
-   Deduplicate venues based on Place ID.

```bash
// turbo
python scripts/audit_cleanup.py
```

### 3. Verification: Compare Results
Run the comparison script to see a "Before vs After" report on key metrics (venue count, pricing standardization, etc.).

```bash
python scripts/compare_before_after.py
```

### 4. Sync CSV
Ensure the CSV dataset matches the audited JSON.

```bash
python scripts/sync_json_to_csv.py
```

### 5. Final Cleanup (Optional)
Once verified, remove the `data/backups` created during the process to keep the workspace clean.

### 6. (Optional) Manual Fixes
If the comparison report highlights specific issues (e.g., remaining invalid suburbs), create and run a targeted fix script similar to `scripts/fix_remaining_suburbs.py` (which is typically deleted after use).

## Key Files
-   `scripts/audit_cleanup.py`: Main logic for API enrichment and suburb fixing.
-   `scripts/analyze_data.py`: General health check script.
-   `scripts/compare_before_after.py`: Differential analysis tool.
