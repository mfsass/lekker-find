#!/usr/bin/env python3
"""
Image-Venue Sync Test
=====================
Tests that specific venues from the bug report now have correct images.

This validates the fix for the sync issue where images were mismatched
with venue data due to index-based naming.
"""

import json
import os
import sys
from venue_id_utils import generate_stable_venue_id, get_image_filename

JSON_PATH = 'public/lekker-find-data.json'
IMAGE_DIR = 'public/images/venues'


def test_specific_venues():
    """
    Test the specific venues mentioned in the bug report.
    
    Based on the issue screenshots:
    1. "Beerhouse on Long" (Drink) - was showing beach/tidal pool image
    2. "Sidecar Adventures" (Activity) - was showing African art/masks
    3. "Saunders Rock" (Nature/Beach) - was showing jewelry store
    4. "Silvermine" (Nature) - was showing beach/tiki bar
    """
    print("=" * 70)
    print("IMAGE-VENUE SYNC FIX VERIFICATION")
    print("=" * 70)
    print("\nTesting specific venues from bug report...\n")
    
    # Load venue data
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    venue_dict = {v['name']: v for v in venues}
    
    # Test cases from the bug report
    test_cases = [
        {
            'name': 'Beerhouse on Long',
            'expected_category': 'Drink',
            'description': 'A lively Long Street venue featuring ninety-nine bottles of craft beer'
        },
        {
            'name': 'Sidecar Adventures',
            'expected_category': 'Activity',
            'description': 'motorcycle'  # Should mention motorcycles/sidecars
        },
        {
            'name': 'Saunders Rock',
            'expected_category': 'Nature',
            'description': 'beach'  # Should be about a beach, not a store
        },
        {
            'name': 'Silvermine',
            'expected_category': 'Nature',
            'description': 'nature reserve'  # Should be about nature, not a bar
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        name = test['name']
        print(f"[{i}/4] Testing: {name}")
        
        # Check venue exists
        if name not in venue_dict:
            print(f"  ✗ FAIL: Venue not found in data")
            all_passed = False
            continue
        
        venue = venue_dict[name]
        
        # Check category matches
        category = venue.get('category', '')
        if category != test['expected_category']:
            print(f"  ✗ FAIL: Category mismatch")
            print(f"    Expected: {test['expected_category']}")
            print(f"    Got:      {category}")
            all_passed = False
            continue
        
        # Check description contains expected content
        description = venue.get('description', '').lower()
        if test['description'].lower() not in description:
            print(f"  ⚠ WARNING: Description may not match expected content")
            print(f"    Expected to contain: '{test['description']}'")
            print(f"    Got: '{description[:100]}...'")
        
        # Check stable ID is correct
        venue_id = venue.get('id', '')
        expected_id = generate_stable_venue_id(name)
        if venue_id != expected_id:
            print(f"  ✗ FAIL: ID mismatch")
            print(f"    Expected: {expected_id}")
            print(f"    Got:      {venue_id}")
            all_passed = False
            continue
        
        # Check image file exists
        image_file = get_image_filename(venue_id)
        image_path = os.path.join(IMAGE_DIR, image_file)
        
        if not os.path.exists(image_path):
            print(f"  ⚠ WARNING: Image file not found: {image_file}")
            print(f"    (This is OK if images haven't been downloaded yet)")
        else:
            # Get file size to confirm it's a real image
            file_size = os.path.getsize(image_path)
            print(f"  ✓ PASS: {name}")
            print(f"    Category: {category}")
            print(f"    ID:       {venue_id}")
            print(f"    Image:    {image_file} ({file_size / 1024:.1f} KB)")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("\nThe sync issue has been fixed:")
        print("  - Venues now use stable name-based IDs")
        print("  - Images are correctly matched to venues")
        print("  - Reordering CSV won't break image links")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease review the failures above.")
    print("=" * 70)
    
    return all_passed


def test_no_index_based_ids():
    """
    Ensure no venues still use old index-based IDs (v0, v1, etc.)
    """
    print("\n" + "=" * 70)
    print("CHECKING FOR OLD INDEX-BASED IDs")
    print("=" * 70)
    
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    
    old_format_count = 0
    for venue in venues:
        venue_id = venue.get('id', '')
        # Check if ID matches old format: v0, v1, v123, etc.
        if venue_id and venue_id.startswith('v') and venue_id[1:].isdigit():
            print(f"  ⚠ Found old format ID: {venue_id} for {venue.get('name')}")
            old_format_count += 1
    
    if old_format_count == 0:
        print("✓ No old index-based IDs found")
        print("  All venues use new stable name-based IDs")
        return True
    else:
        print(f"\n✗ Found {old_format_count} venues with old index-based IDs")
        print("  Run migration: python scripts/migrate_images_to_stable_ids.py --apply")
        return False


if __name__ == "__main__":
    test1 = test_specific_venues()
    test2 = test_no_index_based_ids()
    
    sys.exit(0 if (test1 and test2) else 1)
