import requests
import json
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()
MAPS_API_KEY = os.getenv('MAPS_API_KEY')
TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
CACHE_DIR = "data/cache"

# Bias towards Western Cape
CAPE_TOWN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": -33.9249, "longitude": 18.4241},
        "radius": 50000.0
    }
}

class MapsService:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _get_cache_key(self, query):
        """Generate a unique filename for the query."""
        hash_obj = hashlib.md5(query.encode())
        return os.path.join(CACHE_DIR, f"{hash_obj.hexdigest()}.json")

    def search_places(self, query, max_results=20, search_strategy="normal", force_refresh=False):
        """Search Google Places with file-based caching and pagination."""
        if not MAPS_API_KEY:
            raise Exception("MAPS_API_KEY not set")

        # Cache Key includes strategy and depth to avoid mixing small/large scans
        cache_key_str = f"{query}_{max_results}_{search_strategy}"
        cache_file = self._get_cache_key(cache_key_str)

        # Check Cache
        if not force_refresh and os.path.exists(cache_file):
            print(f"  [CACHE HIT] Loading results for '{query}'...")
            with open(cache_file, 'r') as f:
                return json.load(f)

        # Cache Miss - Call API
        print(f"  [API CALL] Searching Maps for: '{query}' (Depth: {max_results}, Strategy: {search_strategy})...")
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': MAPS_API_KEY,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.websiteUri,places.rating,places.userRatingCount,places.internationalPhoneNumber,places.priceLevel,places.types,nextPageToken'
        }
        
        all_places = []
        next_page_token = None
        
        payload = {
            'textQuery': query,
            'pageSize': 20 # Max allowed per page by Google
        }
        
        # Strategy: Normal vs Deep
        if search_strategy == "normal":
             payload['locationBias'] = CAPE_TOWN_LOCATION_BIAS
        # Deep Discovery: Remove bias to find things outside immediate area if needed, 
        # or keep it but rely on pagination to dig deeper in the same area.
        # For now, let's keep bias but just page deeper.
        elif search_strategy == "deep_discovery":
             payload['locationBias'] = CAPE_TOWN_LOCATION_BIAS

        while len(all_places) < max_results:
            if next_page_token:
                payload['pageToken'] = next_page_token
                # Wait a bit for token to be valid
                import time
                time.sleep(2) 
            
            try:
                response = requests.post(TEXT_SEARCH_URL, headers=headers, json=payload)
                
                if response.status_code != 200:
                    print(f"  Maps API Error: {response.text}")
                    break
                    
                data = response.json()
                places = data.get('places', [])
                
                if not places:
                    break
                    
                all_places.extend(places)
                print(f"  Fetched {len(places)} places. Total: {len(all_places)}")
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
            except Exception as e:
                print(f"  Maps Request Failed: {e}")
                break
                
        # Save to Cache
        with open(cache_file, 'w') as f:
            json.dump(all_places, f)
            
        return all_places
