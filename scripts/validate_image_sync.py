#!/usr/bin/env python3
"""
Image-Venue Sync Validator
===========================
Validates that images are correctly synced with venue data.

This script checks:
1. Each venue has a corresponding image file
2. Each image file has a corresponding venue
3. Image URLs in JSON match actual files on disk
4. No orphaned images exist

Usage:
    python scripts/validate_image_sync.py
"""

import json
import os
import sys
from pathlib import Path
from venue_id_utils import generate_stable_venue_id, get_image_filename

JSON_PATH = 'public/lekker-find-data.json'
IMAGE_DIR = 'public/images/venues'


def validate_sync():
    """
    Validate that images are correctly synced with venue data.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    print("=" * 70)
    print("IMAGE-VENUE SYNC VALIDATION")
    print("=" * 70)
    
    # Load venue data
    print(f"\n[1/4] Loading venue data from {JSON_PATH}...")
    
    if not os.path.exists(JSON_PATH):
        print(f"✗ ERROR: {JSON_PATH} not found")
        return False
    
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    print(f"✓ Loaded {len(venues)} venues")
    
    # Get list of image files
    print(f"\n[2/4] Scanning image directory {IMAGE_DIR}...")
    
    if not os.path.exists(IMAGE_DIR):
        print(f"✗ ERROR: {IMAGE_DIR} not found")
        return False
    
    image_files = set()
    for filename in os.listdir(IMAGE_DIR):
        if filename.endswith('.jpg') or filename.endswith('.jpeg'):
            image_files.add(filename)
    
    print(f"✓ Found {len(image_files)} image files")
    
    # Validate venues
    print(f"\n[3/4] Validating venue-to-image mappings...")
    
    missing_images = []
    id_mismatches = []
    url_mismatches = []
    
    for venue in venues:
        name = venue.get('name', '')
        venue_id = venue.get('id', '')
        image_url = venue.get('image_url', '')
        
        # Check if venue has a stable ID
        expected_id = generate_stable_venue_id(name)
        if venue_id != expected_id:
            id_mismatches.append({
                'name': name,
                'current_id': venue_id,
                'expected_id': expected_id
            })
        
        # Check if image file exists
        expected_filename = get_image_filename(expected_id)
        
        if expected_filename not in image_files:
            missing_images.append({
                'name': name,
                'id': venue_id,
                'expected_file': expected_filename
            })
        
        # Check if image_url matches the stable ID pattern
        if image_url:
            expected_url = f"/images/venues/{expected_filename}"
            if image_url != expected_url and not image_url.startswith('http'):
                url_mismatches.append({
                    'name': name,
                    'current_url': image_url,
                    'expected_url': expected_url
                })
    
    # Report venues with issues
    if id_mismatches:
        print(f"\n⚠ ID Mismatches: {len(id_mismatches)}")
        for item in id_mismatches[:5]:
            print(f"  - {item['name'][:40]:40}")
            print(f"    Current:  {item['current_id']}")
            print(f"    Expected: {item['expected_id']}")
        if len(id_mismatches) > 5:
            print(f"  ... and {len(id_mismatches) - 5} more")
    else:
        print("✓ All venue IDs match expected stable IDs")
    
    if missing_images:
        print(f"\n⚠ Missing Images: {len(missing_images)}")
        for item in missing_images[:10]:
            print(f"  - {item['name'][:40]:40} (expected: {item['expected_file']})")
        if len(missing_images) > 10:
            print(f"  ... and {len(missing_images) - 10} more")
    else:
        print("✓ All venues have corresponding image files")
    
    if url_mismatches:
        print(f"\n⚠ Image URL Mismatches: {len(url_mismatches)}")
        for item in url_mismatches[:5]:
            print(f"  - {item['name'][:40]:40}")
            print(f"    Current:  {item['current_url']}")
            print(f"    Expected: {item['expected_url']}")
        if len(url_mismatches) > 5:
            print(f"  ... and {len(url_mismatches) - 5} more")
    else:
        print("✓ All image URLs match expected paths")
    
    # Check for orphaned images
    print(f"\n[4/4] Checking for orphaned images...")
    
    venue_filenames = set()
    for venue in venues:
        name = venue.get('name', '')
        if name:
            venue_id = generate_stable_venue_id(name)
            venue_filenames.add(get_image_filename(venue_id))
    
    orphaned = image_files - venue_filenames
    
    if orphaned:
        print(f"\n⚠ Orphaned Images: {len(orphaned)}")
        print("  These image files have no corresponding venue:")
        for filename in sorted(orphaned)[:20]:
            print(f"  - {filename}")
        if len(orphaned) > 20:
            print(f"  ... and {len(orphaned) - 20} more")
        print("\n  Consider removing orphaned images to save space.")
    else:
        print("✓ No orphaned images found")
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    total_issues = len(id_mismatches) + len(missing_images) + len(url_mismatches) + len(orphaned)
    
    if total_issues == 0:
        print("✓ ALL CHECKS PASSED - Images are perfectly synced!")
        return True
    else:
        print(f"⚠ {total_issues} issues found:")
        if id_mismatches:
            print(f"  - {len(id_mismatches)} ID mismatches")
        if missing_images:
            print(f"  - {len(missing_images)} missing images")
        if url_mismatches:
            print(f"  - {len(url_mismatches)} URL mismatches")
        if orphaned:
            print(f"  - {len(orphaned)} orphaned images")
        
        print("\nRecommended actions:")
        if id_mismatches or url_mismatches:
            print("  1. Run: python scripts/migrate_images_to_stable_ids.py --apply")
        if missing_images:
            print("  2. Run: python scripts/localize_images.py")
        if orphaned:
            print("  3. Manually review and remove orphaned images")
        
        return False


if __name__ == "__main__":
    success = validate_sync()
    sys.exit(0 if success else 1)
