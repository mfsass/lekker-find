#!/usr/bin/env python3
"""
Lekker Find - Google Places Image Fetcher
==========================================

Uses Google Places API (New) to fetch high-quality photos for each venue.

API Flow:
1. Text Search → Get place_id and photos[] array
2. Construct photo URL with maxWidthPx=1200

Usage:
    python scripts/fetch_images.py              # Fetch all missing images
    python scripts/fetch_images.py --test       # Test with one venue
    python scripts/fetch_images.py --dry-run    # Preview what would be fetched

Cost: ~$0.00 (Text Search ID only is free, Photos ~$7/1000)
"""

import os
import json
import time
import pandas as pd
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, List
from venue_id_utils import generate_stable_venue_id, get_image_filename

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

MAPS_API_KEY = os.getenv('MAPS_API_KEY')
INPUT_CSV = 'data-262-2025-12-26.csv'
OUTPUT_JSON = 'public/lekker-find-data.json'

# API endpoints
TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'
PHOTO_BASE_URL = 'https://places.googleapis.com/v1'

# Image settings
MAX_WIDTH_PX = 1200  # High quality for fullscreen mobile
CAPE_TOWN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": -33.9249, "longitude": 18.4241},  # Cape Town
        "radius": 50000.0  # 50km radius
    }
}

# ============================================================================
# API FUNCTIONS
# ============================================================================

def search_place(venue_name: str) -> Optional[Dict]:
    """
    Search for a place using Text Search (New).
    Returns place_id and photos array.
    """
    if not MAPS_API_KEY:
        print("✗ MAPS_API_KEY not found in .env")
        return None
    
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': MAPS_API_KEY,
        # Request only what we need to minimize cost
        'X-Goog-FieldMask': 'places.id,places.displayName,places.photos,places.formattedAddress,places.googleMapsUri'
    }
    
    payload = {
        'textQuery': f"{venue_name}, Cape Town",
        'locationBias': CAPE_TOWN_LOCATION_BIAS,
        'languageCode': 'en'
    }
    
    try:
        response = requests.post(TEXT_SEARCH_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if 'places' in data and len(data['places']) > 0:
            return data['places'][0]
        return None
        
    except requests.RequestException as e:
        print(f"  ✗ API error: {e}")
        return None


def get_photo_url(photo_name: str, max_width: int = MAX_WIDTH_PX) -> str:
    """
    Construct direct photo URL from photo resource name.
    """
    return f"{PHOTO_BASE_URL}/{photo_name}/media?key={MAPS_API_KEY}&maxWidthPx={max_width}"


def verify_image_url(url: str) -> bool:
    """
    Verify that an image URL is accessible.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except:
        return False


# ============================================================================
# TEST MODE
# ============================================================================

def test_single_venue():
    """Test the API with one venue to verify everything works."""
    print("=" * 60)
    print("GOOGLE PLACES API TEST")
    print("=" * 60)
    
    if not MAPS_API_KEY:
        print("\n✗ MAPS_API_KEY not found in .env file")
        print("  Add: MAPS_API_KEY=AIza...")
        return False
    
    print(f"\n✓ API key found: {MAPS_API_KEY[:10]}...")
    
    # Test with a well-known venue
    test_venue = "Clifton 4th Beach"
    print(f"\n[1/3] Searching for: {test_venue}")
    
    place = search_place(test_venue)
    
    if not place:
        print("  ✗ No place found")
        return False
    
    print(f"  ✓ Found: {place.get('displayName', {}).get('text', 'Unknown')}")
    print(f"  ✓ Place ID: {place.get('id', 'N/A')}")
    print(f"  ✓ Address: {place.get('formattedAddress', 'N/A')}")
    print(f"  ✓ Maps URL: {place.get('googleMapsUri', 'N/A')}")
    
    # Check photos
    photos = place.get('photos', [])
    print(f"\n[2/3] Photos found: {len(photos)}")
    
    if not photos:
        print("  ⚠ No photos available for this place")
        return True  # API works, just no photos
    
    # Get first photo URL
    first_photo = photos[0]
    photo_name = first_photo.get('name')
    photo_url = get_photo_url(photo_name)
    
    print(f"  ✓ Photo name: {photo_name[:50]}...")
    print(f"  ✓ Photo URL: {photo_url[:80]}...")
    
    # Verify image is accessible
    print(f"\n[3/3] Verifying image accessibility...")
    if verify_image_url(photo_url):
        print(f"  ✓ Image is accessible!")
    else:
        print(f"  ⚠ Could not verify image (may still work in browser)")
    
    # Print full photo details
    print("\n" + "-" * 60)
    print("FULL PHOTO DETAILS:")
    print(f"  Width: {first_photo.get('widthPx', 'N/A')}px")
    print(f"  Height: {first_photo.get('heightPx', 'N/A')}px")
    
    attributions = first_photo.get('authorAttributions', [])
    if attributions:
        print(f"  Attribution: {attributions[0].get('displayName', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE - API is working!")
    print("=" * 60)
    
    print(f"\n📸 View the image:")
    print(f"   {photo_url}")
    
    return True


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def process_all_venues(dry_run: bool = False):
    """
    Process all venues and add image URLs to the JSON data.
    Only fetches for venues that don't already have an image_url.
    """
    print("=" * 60)
    print("LEKKER FIND - IMAGE FETCHER")
    print("=" * 60)
    
    if not MAPS_API_KEY:
        print("\n✗ MAPS_API_KEY not found in .env")
        return
    
    print(f"\n✓ API key found: {MAPS_API_KEY[:10]}...")
    
    # Load existing data
    print(f"\n[1/3] Loading {OUTPUT_JSON}...")
    
    if not os.path.exists(OUTPUT_JSON):
        print(f"  ✗ File not found. Run generate_embeddings.py first.")
        return
    
    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    print(f"  ✓ Loaded {len(venues)} venues")
    
    # Count how many need images
    need_images = [v for v in venues if not v.get('image_url')]
    print(f"  → {len(need_images)} venues need images")
    
    if dry_run:
        print("\n[DRY RUN] Would fetch images for:")
        for v in need_images[:10]:
            print(f"  - {v['name']}")
        if len(need_images) > 10:
            print(f"  ... and {len(need_images) - 10} more")
        return
    
    if len(need_images) == 0:
        print("\n✓ All venues already have images!")
        return
    
    # Process venues
    print(f"\n[2/3] Fetching images...")
    
    success = 0
    failed = 0
    no_photos = 0
    
    for i, venue in enumerate(venues):
        # Skip if already has image
        if venue.get('image_url'):
            continue
        
        name = venue['name']
        print(f"  [{i+1}/{len(venues)}] {name}...", end=' ')
        
        # Search for place
        place = search_place(name)
        
        if not place:
            print("✗ Not found")
            failed += 1
            time.sleep(0.2)  # Rate limiting
            continue
        
        # Store place_id and maps URL
        venue['place_id'] = place.get('id')
        venue['maps_url'] = place.get('googleMapsUri')
        
        # Get photo
        photos = place.get('photos', [])
        
        if not photos:
            print("⚠ No photos")
            no_photos += 1
            time.sleep(0.2)
            continue
        
        # Get first (cover) photo
        first_photo = photos[0]
        photo_name = first_photo.get('name')
        
        venue['image_url'] = get_photo_url(photo_name)
        venue['image_width'] = first_photo.get('widthPx')
        venue['image_height'] = first_photo.get('heightPx')
        
        # Store attribution if required
        attrs = first_photo.get('authorAttributions', [])
        if attrs:
            venue['image_attribution'] = attrs[0].get('displayName')
        
        print("✓")
        success += 1
        
        # Rate limiting (to avoid API throttling)
        time.sleep(0.3)
    
    # Save updated data
    print(f"\n[3/3] Saving updated data...")
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    size_kb = os.path.getsize(OUTPUT_JSON) / 1024
    print(f"  ✓ Saved to {OUTPUT_JSON} ({size_kb:.1f} KB)")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  ✓ Success:   {success}")
    print(f"  ⚠ No photos: {no_photos}")
    print(f"  ✗ Failed:    {failed}")
    print(f"\nTotal with images: {sum(1 for v in venues if v.get('image_url'))}/{len(venues)}")


def verify_all_images():
    """Verify that all image URLs are accessible."""
    print("=" * 60)
    print("IMAGE VERIFICATION")
    print("=" * 60)
    
    if not os.path.exists(OUTPUT_JSON):
        print(f"\n✗ {OUTPUT_JSON} not found")
        return
    
    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    
    total = 0
    valid = 0
    invalid = 0
    no_image = 0
    
    print(f"\nVerifying {len(venues)} venues...")
    
    for venue in venues:
        url = venue.get('image_url')
        if not url:
            no_image += 1
            continue
        
        total += 1
        if verify_image_url(url):
            valid += 1
        else:
            invalid += 1
            print(f"  ✗ {venue['name']}")
    
    print(f"\n✓ Valid:    {valid}/{total}")
    print(f"✗ Invalid:  {invalid}/{total}")
    print(f"⚠ No image: {no_image}/{len(venues)}")


def generate_report():
    """Generate a review report of venues needing attention."""
    print("=" * 60)
    print("GENERATING REVIEW REPORT")
    print("=" * 60)
    
    if not os.path.exists(OUTPUT_JSON):
        print(f"\n✗ {OUTPUT_JSON} not found")
        return
    
    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    
    # Find venues without images
    missing = [v for v in venues if not v.get('image_url')]
    
    # Save report
    report_file = 'scripts/missing_images.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("VENUES REQUIRING MANUAL REVIEW\n")
        f.write("=" * 50 + "\n\n")
        f.write("These venues have no Google Places photos.\n")
        f.write("Options:\n")
        f.write("  1. Fix the venue name in the CSV (e.g., 'Darling Toffee' → 'Darling Sweet')\n")
        f.write("  2. Remove the venue if it's closed\n")
        f.write("  3. Manually add an image_url\n\n")
        f.write("-" * 50 + "\n\n")
        
        for v in missing:
            f.write(f"Name: {v['name']}\n")
            f.write(f"Category: {v['category']}\n")
            f.write(f"Vibes: {', '.join(v.get('vibes', []))}\n")
            f.write(f"Place ID: {v.get('place_id', 'N/A')}\n")
            f.write(f"Maps URL: {v.get('maps_url', 'N/A')}\n")
            f.write("\n")
    
    print(f"\n✓ Report saved to {report_file}")
    print(f"\nVenues needing attention ({len(missing)}):")
    for v in missing:
        print(f"  - {v['name']} ({v['category']})")


# ============================================================================
# MAIN
# ============================================================================

def main():
    import sys
    
    if '--test' in sys.argv:
        test_single_venue()
        return
    
    if '--verify' in sys.argv:
        verify_all_images()
        return
    
    if '--dry-run' in sys.argv:
        process_all_venues(dry_run=True)
        return
    
    if '--report' in sys.argv:
        generate_report()
        return
    
    if '--help' in sys.argv:
        print(__doc__)
        return
    
    # Default: process all
    process_all_venues()


if __name__ == "__main__":
    main()


