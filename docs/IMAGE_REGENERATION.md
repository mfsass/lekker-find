# Image Regeneration Guide

## Overview

This guide explains how to regenerate all venue images to fix duplicate image issues and add suburb/locality data.

## Problem

After analyzing the current images, we found:
- **11 sets of duplicate images** affecting ~26 venues
- Venues sharing the same image (e.g., "Clifton 4th Beach" and "Cafeen" have identical images)
- No suburb/locality data captured

## Solution

The enhanced image fetcher:
1. **Detects duplicates** by comparing file hashes
2. **Tries alternative photos** when duplicates are detected
3. **Extracts suburb data** from Google Places addresses
4. **Validates** final image set has no duplicates

## Quick Start

### Check for Duplicates

```bash
python scripts/fetch_images_enhanced.py --check-dupes
```

### Regenerate All Images

```bash
# Complete workflow (recommended)
python scripts/regenerate_images_workflow.py --confirm

# Or manual steps:
python scripts/fetch_images_enhanced.py --regenerate-all --force
python scripts/add_suburb_to_csv.py
python scripts/validate_image_sync.py
```

## What Happens During Regeneration

1. **Delete existing images** - All current images removed
2. **Fetch fresh images** - Download images from Google Places
3. **Duplicate detection** - As each image downloads:
   - Calculate file hash
   - Compare with previously downloaded images
   - If duplicate found, try next available photo from Google Places
   - Up to 5 photos tried per venue
4. **Extract suburbs** - Parse formatted address to extract suburb/locality
5. **Update data** - Save suburb info to JSON and CSV
6. **Validate** - Check final state has no duplicates

## New Scripts

### `fetch_images_enhanced.py`

Enhanced image fetcher with duplicate detection.

**Features**:
- Detects duplicate images by file hash comparison
- Automatically tries next available photo when duplicate found
- Extracts suburb from Google Places formatted address
- Regenerates all images with `--regenerate-all --force`

**Usage**:
```bash
# Check for duplicates
python scripts/fetch_images_enhanced.py --check-dupes

# Regenerate all images
python scripts/fetch_images_enhanced.py --regenerate-all --force
```

### `add_suburb_to_csv.py`

Adds a `Suburb` column to the CSV file.

**Usage**:
```bash
python scripts/add_suburb_to_csv.py
```

Reads suburb data from JSON (populated during image fetch) and adds it to CSV.

### `regenerate_images_workflow.py`

Orchestrates the complete regeneration workflow.

**Usage**:
```bash
# Dry run (shows what would happen)
python scripts/regenerate_images_workflow.py

# Actually regenerate
python scripts/regenerate_images_workflow.py --confirm
```

**Steps**:
1. Check current duplicates
2. Regenerate all images (with duplicate detection)
3. Add suburb column to CSV
4. Validate image sync
5. Final duplicate check

## Expected Results

After regeneration:

- ✅ All venues have unique images (or legitimately share location)
- ✅ Duplicates avoided by selecting alternative photos
- ✅ Suburb data captured for all venues
- ✅ CSV has new `Suburb` column
- ✅ JSON has `suburb` field for each venue

## Current Duplicates Found

The current image set has these duplicates:

| Hash | Venues Affected | File Size |
|------|----------------|-----------|
| dd3f268e | cafeen, clifton-4th-beach | 328 KB |
| 10df54c2 | st-james-tidal-pool, chardonnay-deli | 225 KB |
| d6674d76 | woodstock-street-art, saunders-rocks | 335 KB |
| a40d2f26 | muizenberg, the-book-lounge, the-company-s-garden | 203 KB |
| 9b0a5922 | hello-sailor-bistro, arthur-s-mini-super | 181 KB |
| d2d7b024 | the-pok-co, sunsquare-rooftop-bar | 313 KB |
| 1692c8f6 | intaka-island, the-commons | 736 KB |
| d9261158 | jason-bakery, three-wise-monkeys | 234 KB |
| 2453ddda | kalky-s-fish-chips, origin-coffee-roasting | 1491 KB |
| c940ba8e | the-secret-gin-bar, kleinsky-s-deli | 604 KB |
| e42703f8 | dalebrook-tidal-pool, up-cycles, shimansky-diamonds | 290 KB |

**Total**: 11 duplicate sets affecting 26 venues

## Cost Considerations

Regenerating ~250 images:
- **Google Places Text Search**: ~250 requests × $0.00 = FREE (ID only is free)
- **Google Places Photos**: ~250 photos × $0.007 = ~$1.75
- **Additional photos for duplicates**: ~26 extra × $0.007 = ~$0.18

**Estimated total**: ~$2

## Safety

- ✅ Backup created before migration
- ✅ Dry-run mode available
- ✅ Validation after regeneration
- ✅ Can revert via git

## Troubleshooting

### "All photos are duplicates"

Some venues may legitimately have all their photos duplicated with other venues (e.g., shared locations). This is rare but acceptable.

### Missing API Key

Ensure `MAPS_API_KEY` is set in `.env` file:
```bash
echo "MAPS_API_KEY=your_key_here" >> .env
```

### Rate Limiting

The script includes automatic rate limiting (0.3s between requests). If you hit rate limits, the script will wait.

## Next Steps

After regeneration:

1. **Review images** - Visually check a sample of images
2. **Test app** - Build and test the application
3. **Commit changes** - Include updated JSON, CSV, and images
4. **Monitor** - Watch for any issues in production

---

**See also**: 
- `docs/IMAGE_MANAGEMENT.md` - General image management
- `scripts/README.md` - Scripts overview
