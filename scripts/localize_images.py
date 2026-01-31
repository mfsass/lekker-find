import os
import json
import requests
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from venue_id_utils import generate_stable_venue_id, get_image_filename

# Load New API Key
load_dotenv()
MAPS_API_KEY = os.getenv('MAPS_API_KEY') or os.getenv('VITE_GOOGLE_PLACES_API_KEY')

# Configuration
JSON_PATH = 'public/lekker-find-data.json'
IMAGE_DIR = 'public/images/venues'
Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)

def extract_resource_path(url):
    """Extracts the 'places/.../photos/...' part from a Google Places media URL."""
    match = re.search(r'(places/[^/]+/photos/[^/]+)/media', url)
    if match:
        return match.group(1)
    return None

def localize_images(force_redownload=False):
    """
    Downloads venue images from Google Places API and updates the local JSON.
    Skips images that already exist in the venue directory.
    """
    if not MAPS_API_KEY:
        print("✗ ERROR: MAPS_API_KEY not found in .env")
        return

    print(f"--- Lekker Find Image Localizer ---")
    print(f"Loading {JSON_PATH}...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues = data.get('venues', [])
    total = len(venues)
    downloaded = 0
    skipped = 0
    failed = 0

    print(f"Processing {total} venues...")

    for i, venue in enumerate(venues):
        url = venue.get('image_url', '')
        venue_name = venue.get('name', '')
        venue_id = venue.get('id', '')
        
        # Use stable ID for filename
        if not venue_id and venue_name:
            venue_id = generate_stable_venue_id(venue_name)
            venue['id'] = venue_id
        
        filename = get_image_filename(venue_id) if venue_id else f"venue_{i}.jpg"
        filepath = os.path.join(IMAGE_DIR, filename)

        # 1. Check if it's already localized in JSON
        if url.startswith('/images/venues/'):
            # If the file also exists on disk, we skip unless forced
            if os.path.exists(filepath) and not force_redownload:
                skipped += 1
                continue
            else:
                # Url is local but file is missing? We might need to handle this
                # but currently we don't have the original Google URL anymore.
                # In a real scenario, you'd store the 'google_url_backup' or just search again.
                continue

        # 2. Skip if it's not a URL we can download
        if not url.startswith('http'):
            skipped += 1
            continue
            
        # 3. Double check disk even if JSON isn't updated yet
        if os.path.exists(filepath) and not force_redownload:
            # File exists, just update JSON to point to it
            venue['image_url'] = f"/images/venues/{filename}"
            skipped += 1
            continue

        # 4. DOWNLOAD
        resource_path = extract_resource_path(url)
        fetch_url = url
        
        if resource_path:
            fetch_url = f"https://places.googleapis.com/v1/{resource_path}/media?key={MAPS_API_KEY}&maxWidthPx=1200"

        try:
            print(f"[{i+1}/{total}] Downloading new image: {venue['name']}...", end=' ', flush=True)
            response = requests.get(fetch_url, timeout=15)
            if response.status_code == 200:
                with open(filepath, 'wb') as img_f:
                    img_f.write(response.content)
                venue['image_url'] = f"/images/venues/{filename}"
                print("DONE")
                downloaded += 1
                time.sleep(0.2) # Throttling
            else:
                print(f"FAIL (HTTP {response.status_code})")
                failed += 1
        except Exception as e:
            print(f"ERROR (Error: {e})")
            failed += 1

    # Save changes
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print("\n" + "="*30)
    print("FINISHED")
    print(f"  [OK] Newly downloaded: {downloaded}")
    print(f"  [SKIPPED] Existing/Skipped: {skipped}")
    print(f"  [FAIL] Failed:           {failed}")
    print("="*30)

if __name__ == "__main__":
    import sys
    force = '--force' in sys.argv
    localize_images(force_redownload=force)
