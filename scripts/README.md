# Lekker Find - Data & Scripts

This directory contains utility scripts for managing venue data, images, and embeddings.

## 🛠️ Data Pipeline

The data flows from CSV → AI Enrichment → Embeddings → App.

### 1. Vibe System (The Core)
We use a **Curated Vibe System** (44 specific vibes) defined in `src/data/vibes.ts`.
*   **Script:** `scripts/generate_vibe_embeddings.py`
*   **Purpose:** Generates rich, atmospheric descriptions for each of the 44 vibes (saved to `curated_vibe_embeddings.json`).
*   **Usage:** Run this only if you change the definition of what a "Beach" or "Cozy" vibe feels like.

### 2. Add New Venues (NEW - Recommended)

**Automated workflow using Google Places API:**

```bash
# Preview what would be added (dry run)
python scripts/add_places.py --demo --dry-run

# Add demo hikes to CSV
python scripts/add_places.py --demo

# Add from a text file (name|location|description per line)
python scripts/add_places.py --input places.txt --category Nature

# Complete the pipeline
python scripts/enrich_venues.py          # Generate vibe descriptions
python scripts/generate_embeddings.py --update  # Generate embeddings
python scripts/fetch_images.py           # Fetch image URLs
python scripts/localize_images.py        # Download images locally
python scripts/migrate_images_to_stable_ids.py --apply  # Fix IDs
python scripts/validate_image_sync.py    # Verify everything
```

**Features:**
- ✅ Duplicate detection (85% fuzzy matching)
- ✅ Smart suburb extraction
- ✅ Rating & review count from Google
- ✅ AI-generated vibe descriptions
- ✅ Automatic vibe tag generation

### 3. Manual Venue Addition (Alternative)
1.  **Start Server:** `python scripts/serve_admin.py`
2.  **Go to:** `http://localhost:8000/admin/add-venue.html`
3.  **Add & Save:** Automatically updates CSV, fetches images, and regenerates embeddings.

### 4. Generate Embeddings (Main Build)
Builds the `public/lekker-find-data.json` file used by the app.
```bash
python scripts/generate_embeddings.py         # Full regeneration
python scripts/generate_embeddings.py --update  # Incremental (new venues only)
```
*   **Logic:** Prioritizes the `VibeDescription` (rich text) column from CSV for embedding generation.
*   **Consistency:** Ensures venue embeddings are in the same semantic space as the curated vibe embeddings.

### 5. Enrich Data
If you added raw rows to CSV directly:
```bash
python scripts/enrich_venues.py
```
*   Generates rich `VibeDescription` strings using AI (gpt-5-nano).
*   Uses "warm, evocative" language to align with our embedding strategy.

---

## 🧪 Testing & Verification

### 1. Verify Recommendation Logic
The primary test suite for the matching engine:
```bash
npx tsx scripts/test-vibe-logic.ts
```
*   Runs 8+ real-world user scenarios (e.g., "Water + Wildlife + Avoid Beach").
*   Checks if the correct venues appear in Top 3.

### 2. Image Management

**Important**: Images now use **stable name-based IDs** to prevent sync issues.

```bash
# Fetch images from Google Places API
python scripts/fetch_images.py

# Download images locally (for offline use)
python scripts/localize_images.py

# Migrate to stable IDs (run after adding new venues)
python scripts/migrate_images_to_stable_ids.py --apply

# Validate image-venue sync (run after any data changes!)
python scripts/validate_image_sync.py

# Quick check of new venues
python scripts/check_new_venues.py
```

**See [IMAGE_MANAGEMENT.md](../docs/IMAGE_MANAGEMENT.md) for complete guide.**

Key points:
- ✅ Images are named based on venue names, not CSV order
- ✅ Reordering CSV won't break image links
- ✅ Always validate after data changes

---

## ⚠️ Known Issues & Fixes

| Issue | Fix |
|-------|-----|
| `max_tokens` not supported | Use `max_completion_tokens` for GPT-5 models |
| `Invalid circle.radius` | Max radius is 50000 in Places API |
| Unicode errors on Windows | Run `chcp 65001` before Python scripts |
| Rating/Suburb missing | Use `--update` with fixed `generate_embeddings.py` |
| Image ID mismatches | Run `migrate_images_to_stable_ids.py --apply` |

---

## 📂 Key Files Overview

| Script | Purpose |
|--------|---------|
| `add_places.py` | **NEW**. Adds venues via Google Places API with duplicate detection. |
| `generate_embeddings.py` | **Vital**. Converts CSV data → JSON with embeddings. Uses stable IDs. |
| `generate_vibe_embeddings.py` | **Vital**. Generates semantic definitions for the 44 curated vibes. |
| `test-vibe-logic.ts` | **Vital**. Validates that user choices lead to correct venues. |
| `validate_image_sync.py` | **Important**. Checks image-venue sync. Run after data changes! |
| `check_new_venues.py` | Quick verification that new venues have complete profiles. |
| `enrich_venues.py` | AI-generates rich descriptions for venues. |
| `serve_admin.py` | Local automation server for the admin interface. |
| `localize_images.py` | Downloads images locally with stable naming. |
| `fetch_images.py` | Fetches image URLs from Google Places API. |
| `venue_id_utils.py` | Utility for generating stable venue IDs from names. |
| `migrate_images_to_stable_ids.py` | Migrates images from index-based to name-based IDs. |

---

## 💰 Cost Estimates

| API | Cost |
|-----|------|
| Google Places Text Search | ~$0.032/query |
| OpenAI gpt-5-nano | ~$0.0001/venue |
| OpenAI Embeddings | ~$0.00004/venue |
| **Total per venue** | **~$0.03** |

For 10 venues: ~$0.50
