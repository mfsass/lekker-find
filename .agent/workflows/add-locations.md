---
description: Add new venues/locations to Lekker Find using Places API
---

# Add New Locations Workflow

Use this workflow to add new venues (hikes, restaurants, attractions) to Lekker Find.

## Prerequisites

Ensure these are set in `.env`:
```
MAPS_API_KEY=your_google_places_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Quick Start (Recommended)

// turbo-all

### Step 1: Add Places via API
```bash
# Demo mode (predefined hikes)
python scripts/add_places.py --demo --dry-run

# From a text file (name|location|description per line)
python scripts/add_places.py --input places.txt --category Nature

# Remove --dry-run when ready to add
python scripts/add_places.py --demo
```

### Step 2: Enrich with Vibe Descriptions
```bash
python scripts/enrich_venues.py
```

### Step 3: Generate Embeddings
```bash
python scripts/generate_embeddings.py --update
```

### Step 4: Fetch & Localize Images
```bash
python scripts/fetch_images.py
python scripts/localize_images.py
```

### Step 5: Migrate to Stable IDs
```bash
python scripts/migrate_images_to_stable_ids.py --apply
```

### Step 6: Validate Everything
```bash
python scripts/validate_image_sync.py
python scripts/check_new_venues.py
```

## Input Formats

### Text File Format (for --input)
```
India Venster|Lower Cable Station|Technical scrambling route
Tranquility Cracks|Camps Bay|Hidden yellowwood forest
Botmaskop|Stellenbosch|Best view in Winelands
```

### Demo Data
The script includes 15 predefined Cape Town hikes for testing.

## What the Pipeline Does

1. **Duplicate Detection**: Uses fuzzy matching (85% threshold) against existing venues
2. **Places API Lookup**: Gets rating, reviews, suburb, types, photos
3. **Smart Extraction**: Generates vibe tags, tourist level, price estimates
4. **AI Vibe Descriptions**: Creates 2-3 sentence atmospheric descriptions
5. **256D Embeddings**: For semantic matching
6. **Image Management**: Downloads and localizes with stable naming

## Known Issues & Fixes

| Issue | Fix |
|-------|-----|
| `max_tokens` error | Use `max_completion_tokens` for GPT-5 models |
| `radius > 50000` error | Max radius is 50000 in Places API |
| Unicode errors on Windows | Run `chcp 65001` before Python scripts |
| Rating/Suburb missing in JSON | Fixed in `generate_embeddings.py --update` |
| Image ID mismatches | Run `migrate_images_to_stable_ids.py --apply` |

## Cost Estimates

| API | Cost per venue |
|-----|----------------|
| Google Places Text Search | ~$0.032 |
| OpenAI gpt-5-nano | ~$0.0001 |
| OpenAI Embeddings | ~$0.00004 |
| **Total per venue** | **~$0.03** |

For 10 venues: ~$0.50

## Future: Automated Discovery

The script is ready for automated discovery mode (not yet implemented):
```bash
# Find all 4.7+ rated, 500+ review places within 1hr of Cape Town
python scripts/add_places.py --discover --min-rating 4.7 --min-reviews 500 --radius 60
```
