---
description: Remove duplicate venues from data files
---

# Removing Duplicate Venues

This workflow removes duplicate venues from `lekker-find-data.json` and the CSV file without re-running embeddings.

## Method

The script uses two approaches to detect duplicates:

1. **Embedding Similarity**: Calculates cosine similarity between venue embeddings. Venues with >92% similarity are flagged as duplicates.
2. **Manual List**: For duplicates that embeddings miss (e.g., same location but different categories like "Nature" vs "Activity").

## Steps

### 1. Find duplicates first (discovery mode)

```bash
node scripts/remove-duplicates.cjs --find
```

This shows all potential duplicates without modifying any files.

### 2. Review the output

Check the duplicates found:
- Embedding-detected duplicates show similarity percentage
- Manual duplicates are listed separately
- First occurrence is KEPT, second is REMOVED

### 3. Add any manual duplicates

If you spot duplicates that embeddings miss, add them to `MANUAL_DUPLICATES` array in `scripts/remove-duplicates.cjs`:

```javascript
const MANUAL_DUPLICATES = [
  'Venue Name To Remove', // Reason for removal
];
```

### 4. Preview removal (dry run)

```bash
node scripts/remove-duplicates.cjs --dry-run
```

Confirms what will be removed from both JSON and CSV without making changes.

### 5. Execute removal

```bash
node scripts/remove-duplicates.cjs
```

This:
- Removes duplicates from `public/lekker-find-data.json`
- Removes duplicates from `data-262-2025-12-26.csv`
- Re-indexes venue IDs to maintain sequential order

## Notes

- Embeddings are preserved - no API calls needed
- The CSV file path is hardcoded; update `CSV_PATH` if using a different file
- Threshold can be adjusted via `SIMILARITY_THRESHOLD` (default: 0.92)
