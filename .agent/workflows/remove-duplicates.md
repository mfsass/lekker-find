---
description: Remove duplicate venues from data files
---

# Removing Duplicate Venues

This workflow removes duplicate venues from `lekker-find-data.json` and the CSV file.

## Method

The script uses two approaches:
1. **Exact Name Match**: Automatically removes exact duplicates (keeping the newest).
2. **Embedding Similarity**: Flags potential semantic duplicates (e.g. "The Rock" vs "The Rock Restaurant") for manual review.

## Steps

### 1. Remove Exact Duplicates (Auto)

```bash
python scripts/remove_duplicates.py
```

This will:
- Clean the CSV of exact name matches.
- Clean `public/lekker-find-data.json` of exact and canonical duplicates.

### 2. Check for Semantic Duplicates (Manual Review)

Use the embeddings check to find venues with >92% similarity (or custom threshold).

```bash
# Check with default 0.92 threshold
python scripts/remove_duplicates.py --check-embeddings

# Check with stricter threshold
python scripts/remove_duplicates.py --check-embeddings --threshold 0.95
```

### 3. Resolve Found Duplicates

If the script outputs high-similarity pairs:
1. Open `data-262-2025-12-26.csv`.
2. Search for the duplicate names.
3. Delete the row you don't want.
4. Run `python scripts/remove_duplicates.py` again to sync the JSON.
