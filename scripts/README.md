# Lekker Find - Data & Scripts

This directory contains utility scripts for managing venue data, images, and embeddings.

## 🛠️ Data Pipeline

The data flows from CSV → AI Enrichment → Embeddings → App.

### 1. Vibe System (The Core)
We use a **Curated Vibe System** (44 specific vibes) defined in `src/data/vibes.ts`.
*   **Script:** `scripts/generate_vibe_embeddings.py`
*   **Purpose:** Generates rich, atmospheric descriptions for each of the 44 vibes (saved to `curated_vibe_embeddings.json`).
*   **Usage:** Run this only if you change the definition of what a "Beach" or "Cozy" vibe feels like.

### 2. Add New Venues
1.  **Start Server:** `python scripts/serve_admin.py`
2.  **Go to:** `http://localhost:8000/admin/add-venue.html`
3.  **Add & Save:** Automatically updates CSV, fetches images, and regnerates embeddings.

### 3. Generate Embeddings (Main Build)
Builds the `public/lekker-find-data.json` file used by the app.
```bash
python scripts/generate_embeddings.py
```
*   **Logic:** Prioritizes the `VibeDescription` (rich text) column from CSV for embedding generation.
*   **Consistency:** Ensures venue embeddings are in the same semantic space as the curated vibe embeddings.

### 4. Enrich Data
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

# Validate image-venue sync (run after any data changes!)
python scripts/validate_image_sync.py
```

**See [IMAGE_MANAGEMENT.md](../docs/IMAGE_MANAGEMENT.md) for complete guide.**

Key points:
- ✅ Images are named based on venue names, not CSV order
- ✅ Reordering CSV won't break image links
- ✅ Always validate after data changes


---

## 📂 Key Files Overview

| Script | Purpose |
|--------|---------|
| `generate_embeddings.py` | **Vital**. Converts CSV data → JSON with embeddings. Uses stable IDs. |
| `generate_vibe_embeddings.py` | **Vital**. Generates the semantic definitions for the 44 curated vibes. |
| `test-vibe-logic.ts` | **Vital**. Validates that user choices lead to correct venues. |
| `validate_image_sync.py` | **Important**. Checks image-venue sync. Run after data changes! |
| `enrich_venues.py` | AI-generates rich descriptions for venues. |
| `serve_admin.py` | Local automation server for the admin interface. |
| `localize_images.py` | Downloads images locally with stable naming. |
| `fetch_images.py` | Fetches image URLs from Google Places API. |
| `venue_id_utils.py` | Utility for generating stable venue IDs from names. |
| `migrate_images_to_stable_ids.py` | One-time migration script (already run). |

