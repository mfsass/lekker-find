# Scripts

This folder contains Python scripts for data processing.

## Quick Start

```bash
# Set API keys in .env
OPENAI_API_KEY=sk-...
MAPS_API_KEY=AIza...

# Generate embeddings (only runs on new venues)
python scripts/generate_embeddings.py

# Fetch images (adds external URLs to JSON)
python scripts/fetch_images.py

# Localize images (downloads to public/ and updates JSON paths)
python scripts/localize_images.py

# Test embedding quality
python scripts/test_embeddings.py
```

## Adding New Venues

**The scripts are designed to be incremental** - they only process new items:

### Step 1: Update CSV
Add new venues to `data-262-2025-12-26.csv`

### Step 2: Regenerate Embeddings
```bash
python scripts/generate_embeddings.py --update
```
This will:
- Load existing `lekker-find-data.json`
- Find venues in CSV that aren't in JSON
- Generate embeddings ONLY for new venues
- Merge with existing data

### Step 3: Fetch Meta-data for New Venues
```bash
python scripts/fetch_images.py
```
This automatically skips venues that already have an `image_url` property in the JSON.

### Step 4: Localize New Images
```bash
python scripts/localize_images.py
```
**This is required for production.** It downloads the actual image files to `public/images/venues/` and replaces the Google API URLs with local paths.
- Skips images that already exist on disk.
- Removes the need for a runtime API key.
- Ensures absolute reliability in production.

---

## Files

### `generate_embeddings.py`
Generates semantic embeddings for venues using OpenAI.

**Configuration (from benchmarks):**
- Model: `text-embedding-3-small`
- Dimensions: `256`
- Strategy: Vibes only (best signal clarity)

**Flags:**
- `--update` - Incremental mode (only new venues)
- `--force` - Regenerate all (costs money!)
- `--dry-run` - Preview what would be processed

**Output:** `public/lekker-find-data.json`

---

### `fetch_images.py`
Fetches venue photos from Google Places API.

**Flags:**
- `--test` - Test with one venue
- `--dry-run` - Preview venues needing images
- `--verify` - Check all image URLs work
- `--report` - Generate review report for missing images

**What it adds to each venue:**
```json
{
  "place_id": "ChIJ...",
  "maps_url": "https://maps.google.com/...",
  "image_url": "https://places.googleapis.com/...",
  "image_width": 4032,
  "image_height": 3024,
  "image_attribution": "Photographer Name"
}
```

---

### `localize_images.py`
Downloads images to local storage and strips API keys from JSON.

**Workflow:**
1. Looks for `image_url` starting with `http` in JSON.
2. Downloads the binary file to `public/images/venues/[id].jpg`.
3. Skips if the file already exists on disk (incremental).
4. Updates JSON `image_url` to the local relative path.

**Flags:**
- `--force` - Redownload all images even if they exist.

---

### `test_embeddings.py`
Validates embedding quality.

---

## Cost Summary

| Script | Cost |
|--------|------|
| generate_embeddings.py | ~$0.0001 per 261 venues |
| fetch_images.py | ~$0.00 (Text Search is free tier) |

## Manual Review Required

Venues without photos (need name fix or removal):
- Check `scripts/missing_images.txt` after running fetch

---

## Best Practices

1. **Never delete `lekker-find-data.json`** - it contains all generated embeddings
2. **Use `--update` flag** for incremental processing
3. **Check `missing_images.txt`** for venues that need manual attention
4. **Backup before major changes** - embeddings cost API calls to regenerate
