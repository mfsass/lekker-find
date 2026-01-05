# Lekker Find Scripts

This directory contains the data pipeline scripts for Lekker Find.

## Core Data Pipeline

### 1. `add_places.py` - The Main Entry Point
Use this to add new places (manual input or manual search).
- **Features**: Fetches Google Data, generates AI vibes, downloads images, adds to CSV.
- **Usage**:
  ```bash
  python scripts/add_places.py --input places.txt
  python scripts/add_places.py --demo  # Add demo trails
  ```

### 2. `generate_embeddings.py` - Semantic Search Engine
Generates vector embeddings for all venues to power the "Find matching vibes" feature.
- **Features**: Smart incremental updates (only re-beds changed venues).
- **Usage**:
  ```bash
  python scripts/generate_embeddings.py --update  # Standard run
  python scripts/generate_embeddings.py           # Force regenerate ALL
  ```

### 3. `localize_images.py` - Image Downloader
Downloads images for venues that have a `place_id` but no local image yet.
- **Features**: Checks missing images, downloads from Google Photos API.
- **Usage**:
  ```bash
  python scripts/localize_images.py
  ```

### 4. `sync_metadata.py` - Sync CSV to JSON
Syncs manual edits from `data-*.csv` to the frontend `public/lekker-find-data.json`.
- **Features**: Updates price, rating, suburb, category without re-running embeddings.
- **Usage**:
  ```bash
  python scripts/sync_metadata.py
  ```

## Maintenance & Audit Tools

### `validate_image_sync.py`
Audits the sync between JSON data and the `public/images/venues` folder.
- **Checks**: Missing images, orphaned files, ID mismatches.
- **Usage**:
  ```bash
  python scripts/validate_image_sync.py
  ```

### `enrich_venues.py` (Legacy/Utility)
Used for batch enrichment of descriptions. Mostly superseded by `add_places.py` but useful for bulk fixing.
- **Usage**:
  ```bash
  python scripts/enrich_venues.py --fix-malformed  # Fix "X stars" descriptions
  ```

## Workflow for Manual Edits
1. Edit `data-262-2025-12-26.csv`
2. Run `python scripts/sync_metadata.py` to update JSON
3. (If you changed descriptions) Run `python scripts/generate_embeddings.py --update`
