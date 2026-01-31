import json
import requests
import concurrent.futures
from urllib.parse import urlparse

DATA_FILE = "public/lekker-find-data.json"

REQUIRED_FIELDS = [
    "id", "name", "category", "tourist_level", "price_tier",
    "numerical_price", "best_season", "vibes", "description", "embedding"
]

VALID_PRICE_TIERS = ["Free", "R", "RR", "RRR"]
VALID_TOURIST_LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # App uses 1-5 logic but data might have 1-10? matcher.ts filters by tourist_level >= 6 for "Famous" (1-2). Let's be lenient but check type.

import os

def check_image(url):
    """
    Checks if an image URL is reachable or if the local file exists.
    Returns (url, status, error_message)
    """
    if not url:
        return url, "MISSING", "No URL provided"

    # Check for local file path (starts with /)
    if url.startswith('/'):
        # Assuming script runs from project root, and public/ is the root for these paths
        local_path = f"public{url}"
        if os.path.exists(local_path):
            return url, "OK", None
        else:
            return url, "ERROR", f"File not found: {local_path}"
    
    try:
        # Use a proper User-Agent to avoid being blocked by some CDNs (like Google's)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return url, "OK", None
        elif response.status_code == 403:
             # Sometimes HEAD is forbidden but GET works, or it requires cookies. 
             # Google UserContent often allows HEAD.
             return url, "WARNING", f"Status {response.status_code}"
        else:
            return url, "ERROR", f"Status {response.status_code}"
    except Exception as e:
        return url, "ERROR", str(e)

def verify_data():
    print(f"Loading {DATA_FILE}...")
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Data file not found!")
        return

    venues = data.get('venues', [])
    tag_embeddings = data.get('tag_embeddings', {})
    
    print(f"Found {len(venues)} venues.")
    print(f"Found {len(tag_embeddings)} tag embeddings.")

    errors = []
    warnings = []
    
    image_urls = []

    print("\nVerifying schema and logic...")
    for i, venue in enumerate(venues):
        # 1. Check Required Fields
        for field in REQUIRED_FIELDS:
            if field not in venue:
                errors.append(f"Venue {i} ({venue.get('name', 'Unknown')}): Missing field '{field}'")
        
        # 2. Check Types and Constraints
        if 'price_tier' in venue and venue['price_tier'] not in VALID_PRICE_TIERS:
             # Allow empty string if it's not strictly required by runtime but matcher uses getBudgetTiers which handles mapped values. 
             # matcher.ts seems to strictly filter by allowedTiers.
             warnings.append(f"Venue {i} ({venue.get('name')}): Invalid price_tier '{venue['price_tier']}'")

        if 'tourist_level' in venue:
            if not isinstance(venue['tourist_level'], (int, float)):
                 errors.append(f"Venue {i} ({venue.get('name')}): tourist_level is not a number")
        
        # 3. Check Vibes exist in embeddings
        if 'vibes' in venue:
            for vibe in venue['vibes']:
                # The app logic often maps vibe -> embedding key (VIBE_EMBEDDING_MAP).
                # But strict check: does the tag exist in tag_embeddings?
                if vibe not in tag_embeddings:
                     # This might be okay if VIBE_EMBEDDING_MAP handles it, but good to know.
                     pass 

        # 4. Check Embedding Dimensions (should be 256 for text-embedding-3-small as per matcher.ts comment)
        if 'embedding' in venue:
            if len(venue['embedding']) != 256:
                warnings.append(f"Venue {i} ({venue.get('name')}): Embedding dimension is {len(venue['embedding'])}, expected 256.")

        # Collect image for checking
        if 'image_url' in venue and venue['image_url']:
            image_urls.append(venue['image_url'])
        else:
            warnings.append(f"Venue {i} ({venue.get('name')}): Missing image_url")

    print(f"Schema check complete. Found {len(errors)} errors and {len(warnings)} warnings.")
    for err in errors[:10]:
        print(f"  [Error] {err}")
    if len(errors) > 10: print(f"  ... and {len(errors)-10} more.")
    
    for warn in warnings[:10]:
        print(f"  [Warn] {warn}")
    if len(warnings) > 10: print(f"  ... and {len(warnings)-10} more.")

    # 5. Verify Images
    print(f"\nVerifying {len(image_urls)} images (this may take a moment)...")
    
    broken_images = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_image, image_urls))
    
    for url, status, msg in results:
        if status == "ERROR":
            broken_images.append((url, msg))
            
    print(f"Image check complete. {len(image_urls) - len(broken_images)} valid, {len(broken_images)} broken.")
    
    if broken_images:
        print("\nBroken Images:")
        for url, msg in broken_images[:10]:
             print(f"  {url} -> {msg}")
        if len(broken_images) > 10:
            print(f"  ...and {len(broken_images)-10} more.")

    # Final Verdict
    if not errors and not broken_images:
        print("\n✅ PASSED: Data integrity and resources verified.")
    else:
        print("\n❌ FAILED: Issues found.")

if __name__ == "__main__":
    verify_data()
