#!/usr/bin/env python3
"""
Enhanced Image Fetcher with Duplicate Detection
================================================

Fetches fresh images for all venues with:
1. Duplicate image detection (by file hash)
2. Automatic selection of next available photo for duplicates
3. Suburb/locality extraction from Google Places
4. Complete image regeneration support

Usage:
    python scripts/fetch_images_enhanced.py --regenerate-all  # Delete and refetch all
    python scripts/fetch_images_enhanced.py --check-dupes     # Find duplicates
    python scripts/fetch_images_enhanced.py                   # Normal fetch
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, List, Set
from collections import defaultdict
from venue_id_utils import generate_stable_venue_id, get_image_filename

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

MAPS_API_KEY = os.getenv('MAPS_API_KEY')
OUTPUT_JSON = 'public/lekker-find-data.json'
IMAGE_DIR = 'public/images/venues'

# API endpoints
TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'
PHOTO_BASE_URL = 'https://places.googleapis.com/v1'

# Image settings
MAX_WIDTH_PX = 1200
CAPE_TOWN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": -33.9249, "longitude": 18.4241},
        "radius": 50000.0
    }
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_file_hash(filepath: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return ""


def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(filepath)
    except:
        return 0


def find_duplicate_images(image_dir: str) -> Dict[str, List[str]]:
    """
    Find duplicate images by comparing file hashes.
    Returns dict mapping hash -> list of filenames with that hash.
    """
    hash_to_files = defaultdict(list)
    
    if not os.path.exists(image_dir):
        return {}
    
    for filename in os.listdir(image_dir):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            filepath = os.path.join(image_dir, filename)
            file_hash = get_file_hash(filepath)
            if file_hash:
                hash_to_files[file_hash].append(filename)
    
    # Only return hashes that have duplicates
    return {h: files for h, files in hash_to_files.items() if len(files) > 1}


def extract_suburb(formatted_address: str) -> Optional[str]:
    """
    Extract suburb from formatted address.
    Google Places addresses typically: "Street, Suburb, City, Postal Code, Country"
    """
    if not formatted_address:
        return None
    
    parts = [p.strip() for p in formatted_address.split(',')]
    
    # Typical format: Street, Suburb, Cape Town, Postal, South Africa
    # Suburb is usually the second or third component
    if len(parts) >= 3:
        # Skip first (street) and look for suburb before "Cape Town"
        for part in parts[1:]:
            if 'Cape Town' not in part and 'South Africa' not in part and not part.isdigit():
                # Filter out postal codes (pure numbers)
                if not all(c.isdigit() or c.isspace() for c in part):
                    return part.strip()
    
    return None


# ============================================================================
# API FUNCTIONS
# ============================================================================

def search_place(venue_name: str) -> Optional[Dict]:
    """
    Search for a place using Text Search (New).
    Returns place data including photos and address.
    """
    if not MAPS_API_KEY:
        print("✗ MAPS_API_KEY not found in .env")
        return None
    
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': MAPS_API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.photos,places.formattedAddress,places.googleMapsUri,places.addressComponents'
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
    """Construct photo URL from photo resource name."""
    return f"{PHOTO_BASE_URL}/{photo_name}/media?key={MAPS_API_KEY}&maxWidthPx={max_width}"


def download_image(url: str, filepath: str) -> bool:
    """Download image from URL to filepath."""
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
    return False


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def check_duplicates():
    """Check for and report duplicate images."""
    print("=" * 70)
    print("DUPLICATE IMAGE DETECTION")
    print("=" * 70)
    
    duplicates = find_duplicate_images(IMAGE_DIR)
    
    if not duplicates:
        print("\n✓ No duplicate images found!")
        return {}
    
    print(f"\n⚠ Found {len(duplicates)} sets of duplicate images:\n")
    
    for file_hash, files in duplicates.items():
        file_size = get_file_size(os.path.join(IMAGE_DIR, files[0]))
        print(f"Hash: {file_hash[:8]}... ({file_size / 1024:.1f} KB)")
        for filename in files:
            print(f"  - {filename}")
        print()
    
    return duplicates


def regenerate_all_images(force: bool = False):
    """
    Delete all existing images and fetch fresh ones.
    Also updates suburb information in JSON.
    """
    print("=" * 70)
    print("REGENERATE ALL IMAGES")
    print("=" * 70)
    
    if not force:
        print("\n⚠ WARNING: This will delete ALL existing images!")
        print("Add --force flag to proceed")
        return
    
    # Delete all existing images
    if os.path.exists(IMAGE_DIR):
        print(f"\n[1/5] Deleting existing images...")
        deleted = 0
        for filename in os.listdir(IMAGE_DIR):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                os.remove(os.path.join(IMAGE_DIR, filename))
                deleted += 1
        print(f"  ✓ Deleted {deleted} images")
    else:
        os.makedirs(IMAGE_DIR, exist_ok=True)
        print(f"\n[1/5] Created image directory")
    
    # Load venue data
    print(f"\n[2/5] Loading venue data...")
    if not os.path.exists(OUTPUT_JSON):
        print(f"  ✗ {OUTPUT_JSON} not found")
        return
    
    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data.get('venues', [])
    print(f"  ✓ Loaded {len(venues)} venues")
    
    # Track used image hashes to detect duplicates during download
    used_hashes: Dict[str, str] = {}  # hash -> venue_name
    
    # Fetch images for all venues
    print(f"\n[3/5] Fetching fresh images...")
    
    success = 0
    failed = 0
    duplicates_avoided = 0
    suburbs_added = 0
    
    for i, venue in enumerate(venues):
        name = venue['name']
        venue_id = venue.get('id', generate_stable_venue_id(name))
        filename = get_image_filename(venue_id)
        filepath = os.path.join(IMAGE_DIR, filename)
        
        print(f"  [{i+1}/{len(venues)}] {name}...", end=' ', flush=True)
        
        # Search for place
        place = search_place(name)
        
        if not place:
            print("✗ Not found")
            failed += 1
            time.sleep(0.2)
            continue
        
        # Extract and store suburb
        formatted_address = place.get('formattedAddress', '')
        if formatted_address:
            suburb = extract_suburb(formatted_address)
            if suburb and not venue.get('suburb'):
                venue['suburb'] = suburb
                suburbs_added += 1
        
        # Store place metadata
        venue['place_id'] = place.get('id')
        venue['maps_url'] = place.get('googleMapsUri')
        
        # Get photos
        photos = place.get('photos', [])
        
        if not photos:
            print("⚠ No photos")
            failed += 1
            time.sleep(0.2)
            continue
        
        # Try photos in order until we find a unique one
        photo_downloaded = False
        for photo_idx, photo in enumerate(photos[:5]):  # Try up to 5 photos
            photo_name = photo.get('name')
            photo_url = get_photo_url(photo_name)
            
            # Download to temp location first
            temp_path = filepath + '.tmp'
            if download_image(photo_url, temp_path):
                # Check if this image is a duplicate
                image_hash = get_file_hash(temp_path)
                
                if image_hash in used_hashes:
                    # Duplicate! Try next photo
                    os.remove(temp_path)
                    if photo_idx < len(photos) - 1:
                        duplicates_avoided += 1
                        continue
                    else:
                        print(f"⚠ All photos are duplicates (matches {used_hashes[image_hash]})")
                        failed += 1
                        break
                else:
                    # Unique image! Keep it
                    os.rename(temp_path, filepath)
                    used_hashes[image_hash] = name
                    
                    # Store image metadata
                    venue['image_url'] = f"/images/venues/{filename}"
                    venue['image_width'] = photo.get('widthPx')
                    venue['image_height'] = photo.get('heightPx')
                    
                    attrs = photo.get('authorAttributions', [])
                    if attrs:
                        venue['image_attribution'] = attrs[0].get('displayName')
                    
                    if photo_idx > 0:
                        print(f"✓ (photo #{photo_idx + 1})")
                    else:
                        print("✓")
                    
                    success += 1
                    photo_downloaded = True
                    break
        
        if not photo_downloaded and photo_idx == 0:
            failed += 1
        
        time.sleep(0.3)  # Rate limiting
    
    # Save updated data
    print(f"\n[4/5] Saving updated data...")
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✓ Saved to {OUTPUT_JSON}")
    
    # Summary
    print(f"\n[5/5] Summary")
    print("=" * 70)
    print(f"  ✓ Success:            {success}")
    print(f"  ✗ Failed:             {failed}")
    print(f"  🔄 Duplicates avoided: {duplicates_avoided}")
    print(f"  📍 Suburbs added:      {suburbs_added}")
    print(f"\nTotal images: {success}/{len(venues)}")
    
    # Final duplicate check
    print(f"\n[6/6] Final duplicate check...")
    final_dupes = find_duplicate_images(IMAGE_DIR)
    if final_dupes:
        print(f"  ⚠ Still found {len(final_dupes)} sets of duplicates")
        print("  (These venues may legitimately share the same location)")
    else:
        print("  ✓ No duplicates in final image set!")


def main():
    import sys
    
    if '--check-dupes' in sys.argv:
        duplicates = check_duplicates()
        sys.exit(0 if not duplicates else 1)
    
    if '--regenerate-all' in sys.argv:
        force = '--force' in sys.argv
        regenerate_all_images(force=force)
        return
    
    print(__doc__)
    print("\nUsage examples:")
    print("  python scripts/fetch_images_enhanced.py --check-dupes")
    print("  python scripts/fetch_images_enhanced.py --regenerate-all --force")


if __name__ == "__main__":
    main()
