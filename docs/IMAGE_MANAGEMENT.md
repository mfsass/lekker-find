# Image Management & Sync Prevention Guide

## Overview

This guide explains how venue images are managed and how to prevent sync issues between images and venue data.

## The Problem (Historical)

Previously, venue images were named using sequential index-based IDs (v0.jpg, v1.jpg, v2.jpg, etc.). When the CSV data was reordered or updated:
- Venue IDs would change (e.g., "Saunders Rock" moved from v1 to v57)
- But image files remained with their old names
- This caused **wrong images to display for venues** (e.g., a beach photo showing for a bar)

## The Solution: Stable Name-Based IDs

Venues now use **stable, name-based IDs** that never change, even when CSV order changes:

```
Venue Name              → Stable ID
─────────────────────────────────────────────
"Woolley's Tidal Pool"  → "woolleys-tidal-pool-5561"
"Beerhouse on Long"     → "beerhouse-on-long-aea0"
"Saunders Rock"         → "saunders-rock-4799"
```

### ID Generation

IDs are generated from venue names using `venue_id_utils.py`:
1. Convert to lowercase
2. Remove apostrophes: "Woolley's" → "woolleys"
3. Replace spaces/special chars with hyphens
4. Add 4-char hash suffix to ensure uniqueness
5. Result: `woolleys-tidal-pool-5561.jpg`

## File Structure

```
scripts/
  venue_id_utils.py              # ID generation utilities
  generate_embeddings.py         # Generates JSON with stable IDs
  fetch_images.py                # Downloads images using stable IDs
  localize_images.py             # Downloads images locally using stable IDs
  migrate_images_to_stable_ids.py # One-time migration script
  validate_image_sync.py         # Validation tool

src/utils/
  imageHelper.ts                 # Frontend image URL helper

public/
  lekker-find-data.json          # Venue data with stable IDs
  images/venues/
    woolleys-tidal-pool-5561.jpg
    beerhouse-on-long-aea0.jpg
    ...
```

## Workflows

### Adding New Venues

1. **Update CSV**: Add venues to `data-262-2025-12-26.csv`

2. **Regenerate embeddings** (creates stable IDs):
   ```bash
   python scripts/generate_embeddings.py
   ```

3. **Fetch images** (optional - fetches from Google Places):
   ```bash
   python scripts/fetch_images.py
   ```

4. **Download images locally** (optional):
   ```bash
   python scripts/localize_images.py
   ```

5. **Validate sync**:
   ```bash
   python scripts/validate_image_sync.py
   ```

### Updating Existing Venues

When updating venue names or reordering CSV:

1. **Update CSV**: Make your changes to the CSV file

2. **Regenerate embeddings**:
   ```bash
   python scripts/generate_embeddings.py
   ```
   - This preserves existing images by name matching
   - Venues that match by name keep their images
   - New venues get new stable IDs

3. **Validate**:
   ```bash
   python scripts/validate_image_sync.py
   ```
   - Shows any missing images
   - Identifies orphaned images
   - Confirms sync is correct

4. **Fix issues** if any:
   ```bash
   python scripts/localize_images.py  # Download missing images
   ```

## Validation & Monitoring

### Run Validation Regularly

```bash
python scripts/validate_image_sync.py
```

This checks for:
- ✓ Venues with missing images
- ✓ Orphaned images (no corresponding venue)
- ✓ ID format consistency
- ✓ Image URL correctness

### Expected Output (Healthy State)

```
======================================================================
IMAGE-VENUE SYNC VALIDATION
======================================================================

[1/4] Loading venue data from public/lekker-find-data.json...
✓ Loaded 249 venues

[2/4] Scanning image directory public/images/venues...
✓ Found 247 image files

[3/4] Validating venue-to-image mappings...
✓ All venue IDs match expected stable IDs
✓ All venues have corresponding image files
✓ All image URLs match expected paths

[4/4] Checking for orphaned images...
✓ No orphaned images found

======================================================================
VALIDATION SUMMARY
======================================================================
✓ ALL CHECKS PASSED - Images are perfectly synced!
```

## Troubleshooting

### Issue: Wrong image shows for a venue

**Cause**: Old index-based images still exist

**Fix**:
```bash
# 1. Run validation to identify the issue
python scripts/validate_image_sync.py

# 2. If needed, re-run migration
python scripts/migrate_images_to_stable_ids.py --apply
```

### Issue: Missing images for some venues

**Cause**: Images not yet downloaded

**Fix**:
```bash
# Download from Google Places (requires API key)
python scripts/fetch_images.py

# OR download and store locally
python scripts/localize_images.py
```

### Issue: Orphaned images taking up space

**Cause**: Venues were removed from CSV

**Fix**:
```bash
# 1. Identify orphans
python scripts/validate_image_sync.py

# 2. Manually review and delete
rm public/images/venues/old-venue-name-*.jpg
```

## Prevention Checklist

✅ **Always use `generate_embeddings.py` to create/update JSON**
   - This ensures stable IDs are used
   
✅ **Run validation after any data changes**
   ```bash
   python scripts/validate_image_sync.py
   ```

✅ **Never manually rename venue IDs**
   - IDs are generated from names
   - Changing IDs breaks image links

✅ **Use name matching when migrating data**
   - Scripts preserve images by matching venue names
   - Renaming a venue = new image needed

✅ **Commit validation to CI/CD**
   - Add validation step to deployment pipeline
   - Prevents deploying with sync issues

## Migration History

### October 2025: Initial Implementation
- Created stable ID system
- Migrated 247 images from v0.jpg format to name-based format
- Updated all scripts to use stable IDs

### January 2026: Issue Resolution
- Fixed sync issues reported in production
- Added comprehensive validation
- Documented prevention measures

## Technical Details

### ID Collision Handling

The 4-character hash suffix prevents collisions:
- Hash is MD5 of original venue name
- Extremely low collision probability
- Migration script validates no collisions exist

### Image File Format

- **Format**: JPEG
- **Naming**: `{stable-id}.jpg`
- **Size**: Variable (optimized from Google Places)
- **Location**: `public/images/venues/`

### Frontend Integration

The `imageHelper.ts` utility handles image URLs:

```typescript
// Returns the correct image path for any venue
getVenueImage(venue) 
  → "/images/venues/woolleys-tidal-pool-5561.jpg"
```

Fallback behavior:
1. Try venue.image_url if it exists
2. Try local image based on venue.id
3. Fall back to category default image

## Support

If you encounter sync issues:

1. **Run validation**: `python scripts/validate_image_sync.py`
2. **Check this guide** for common issues
3. **Review Git history** for recent data changes
4. **Contact**: Create an issue with validation output

---

**Last Updated**: January 2026
**Version**: 2.0 (Stable ID System)
