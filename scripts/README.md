# Lekker Find Scripts

Automation pipelines for managing venue data, images, and recommendations.

## Core Scripts (Keep These)

| Script | Purpose | Usage |
|--------|---------|-------|
| `add_places.py` | Add new venues via Google Places API | `python scripts/add_places.py --demo` |
| `remove_duplicates.py` | Remove exact + semantic duplicates | `python scripts/remove_duplicates.py --check-embeddings` |
| `clean_data.py` | Fix data quality (NaNs, prices, vibes) | `python scripts/clean_data.py` |
| `sync_metadata.py` | Fast CSV→JSON sync (no API cost) | `python scripts/sync_metadata.py` |
| `generate_embeddings.py` | Generate/update AI embeddings | `python scripts/generate_embeddings.py --update` |
| `discover_places.py` | Find new venue candidates | `python scripts/discover_places.py` |
| `enrich_venues.py` | Generate AI vibe descriptions | `python scripts/enrich_venues.py` |
| `validate_image_sync.py` | Verify image file integrity | `python scripts/validate_image_sync.py` |
| `localize_images.py` | Download remote images to local | `python scripts/localize_images.py` |
| `venue_id_utils.py` | Shared utilities for stable IDs | (imported by other scripts) |

## Recommended Workflow

```bash
# 1. Discover new venues
python scripts/discover_places.py

# 2. Add them
python scripts/add_places.py --input discovered_places.txt

# 3. Clean and dedupe
python scripts/remove_duplicates.py
python scripts/clean_data.py

# 4. Generate embeddings (smart incremental - only changed venues)
python scripts/generate_embeddings.py --update

# 5. Validate
python scripts/validate_image_sync.py
```

## Smart Incremental Updates

The `--update` flag in `generate_embeddings.py` is smart:
- **New venues**: Generates embeddings (API call)
- **Changed vibes**: Re-generates embeddings (API call)
- **Unchanged venues**: Preserves existing embeddings (no cost)
- **Removed venues**: Cleans up orphaned entries

This minimizes API costs when making small data changes.

---

## Lean Repository Principle

**Keep this directory clean.** After solving an issue with a one-off script:

### Delete These After Use
- `fix_*.py` - One-time data fixes
- `debug_*.py` - Debugging scripts
- `test_*.py` - Test scripts (after verification)
- `patch_*.py` - Specific data patches

### Consolidate Similar Scripts
If you create a script similar to an existing one, merge them:
- All duplicate detection → `remove_duplicates.py`
- All data cleaning → `clean_data.py`
- All image operations → `localize_images.py` or `validate_image_sync.py`

### Update Docs
If script names change, update:
- This README
- `.agent/workflows/add-locations.md`
- `.agent/workflows/remove-duplicates.md`
