# Data Quality Cleanup Task

**Created**: 2026-01-05
**Status**: 🔄 In Progress

## Overview
Systematic cleanup of data quality issues discovered during venue card audit.

---

## Task 1: Fix Malformed Descriptions (77 venues)
**Status**: ⏳ Pending

### Problem
77 venues have raw Places API data as descriptions, e.g.:
- `"bakeries (5 stars, 573 reviews)"`
- `"seafood restaurants (4.8 stars, 1116 reviews)"`

### Action
1. Generate proper VibeDescription for these venues using AI
2. Update CSV with new descriptions
3. Sync to JSON
4. Verify descriptions no longer contain "stars, X reviews"

### Verification
```powershell
# Should return 0 after fix
$json = (Get-Content "public/lekker-find-data.json" -Raw | ConvertFrom-Json).venues
($json | Where-Object { $_.description -match "stars, \d+ reviews" }).Count
```

---

## Task 2: Fix Missing Venue Images (15 venues)
**Status**: ⏳ Pending

### Problem
15 venues have no corresponding image file:
- Sanook Somerset
- Idiom Restaurant & Wine
- Kogel Bay (Koeël Bay)
- Dylan Lewis Studio
- CityROCK Cape Town
- Kayak Cape Town (Simon's)
- Bloc 11 – Diep River
- Platō Coffee Stellenbosch
- Echo Valley
- Cape Town Surf School
- +5 more

### Action
1. Run `python scripts/localize_images.py`
2. Verify images were downloaded
3. If any fail, manually add placeholder or find images

### Verification
```powershell
python scripts/validate_image_sync.py
# "Missing Images" should be 0
```

---

## Task 3: Clean Up Orphaned Images (41 files)
**Status**: ⏳ Pending

### Problem
41 image files have no matching venue (old names, duplicates)

### Action
1. Review orphaned image list
2. Move to backup folder before deletion
3. Delete orphaned images
4. Verify no orphaned images remain

### Verification
```powershell
python scripts/validate_image_sync.py
# "Orphaned Images" should be 0
```

---

## Task 4: Normalize Suburb Names (~25 fixes)
**Status**: ⏳ Pending

### Problem
Bad suburb values in CSV:
- Street addresses: `Wharf St`, `13 Drama St`, `6 Nobel St`
- Roads: `R45`, `R304`, `Banghoek Rd`
- Data errors: `Sweet LionHeart`, `Coffee/Freezo.`, `and`
- Duplicates: `Victoria & Alfred Waterfront` vs `V&A Waterfront`

### Action
1. Create mapping of bad -> correct suburb names
2. Update CSV with correct suburbs
3. Sync to JSON
4. Verify all suburbs are normalized

### Verification
```powershell
# All suburbs should be recognizable neighborhood names
$csv = Import-Csv "data-262-2025-12-26.csv"
$csv | Group-Object Suburb | Sort-Object Count | Select-Object -Last 20
```

---

## Task 5: Improve Add Location Workflow
**Status**: ⏳ Pending

### Problem
Current workflow allows venues to be added without:
- Proper VibeDescription (gets raw API data)
- Downloaded local images
- Validated suburb names

### Action
1. Update `/add-locations` workflow to include validation steps
2. Add checks to `add_places.py` for description quality
3. Ensure image download is mandatory step
4. Add suburb validation against known list

### Files to Update
- `.agent/workflows/add-locations.md`
- `scripts/add_places.py`
- `scripts/generate_vibe_descriptions.py` (create if needed)

---

## Task 6: Repository Cleanup
**Status**: ⏳ Pending

### Problem
One-off and duplicate scripts cluttering the repo

### Action
1. Audit all scripts in `/scripts`
2. Identify one-off or unused scripts
3. Consolidate where possible
4. Delete unused scripts
5. Update `scripts/README.md`

### Verification
```powershell
# Scripts should have clear purposes, no duplicates
Get-ChildItem scripts/*.py | Select-Object Name
```

---

## Progress Log

| Task | Status | Completed |
|------|--------|-----------|
| 1. Fix descriptions | ⏳ | - |
| 2. Fix missing images | ⏳ | - |
| 3. Clean orphaned images | ⏳ | - |
| 4. Normalize suburbs | ⏳ | - |
| 5. Improve workflow | ⏳ | - |
| 6. Repo cleanup | ⏳ | - |
