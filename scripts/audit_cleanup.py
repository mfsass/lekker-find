import json
import os
import shutil
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment variables
load_dotenv()
API_KEY = os.getenv("MAPS_API_KEY")

DATA_FILE = "public/lekker-find-data.json"
BACKUP_DIR = "data/backups"
MAX_WORKERS = 5 # 5 parallel requests to be safe with rate limits

# --- Constants ---
SUBURB_MAPPING = {
    "45 Yew St": "Salt River", 
    "51 Gogosoa St": "Langa", 
    "Selwyn St": "Observatory", 
    "Plateau Rd": "Cape Point", 
    "Witteboomen": "Constantia",
    "Otto du Plessis Dr": "Bloubergstrand", 
    "Main Rd": "Kalk Bay", 
    "Three Anchor Bay": "Sea Point", 
    "Mouille Point": "Green Point", 
}

# --- Helpers ---

def backup_data():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/lekker-find-data_{timestamp}.json"
    shutil.copy(DATA_FILE, backup_path)
    print(f"Backed up data to {backup_path}")

def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    # Atomic write to avoid corruption
    temp_file = DATA_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    shutil.move(temp_file, DATA_FILE)
    print(f"Saved updated data to {DATA_FILE}")

# --- Google Maps API ---

def search_text_new(query):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.id,places.name,places.formattedAddress"
    }
    payload = {"textQuery": query}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        places = data.get('places', [])
        if places:
            return places[0]
    except Exception as e:
        print(f"Error searching for '{query}': {e}")
    return None

def get_place_details_new(place_id):
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "id,name,photos,priceLevel,rating,userRatingCount,editorialSummary"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting details for {place_id}: {e}")
        return None

def get_photo_url(photo_name):
    return f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=1200&key={API_KEY}"

# --- Worker Function ---

def process_venue_item(venue, seen_ids, lock):
    original_name = venue.get('name')
    suburb = venue.get('suburb')
    
    # 1. Suburb Cleanup
    if suburb in SUBURB_MAPPING:
        venue['suburb'] = SUBURB_MAPPING[suburb]
        suburb = venue['suburb']
    
    # Check if already processed (has place_id and enriched fields)
    if 'place_id' in venue and venue.get('rating') and venue['place_id'] not in seen_ids:
        # Assume valid, but add to seen_ids to prevent duplicates
        with lock:
            if venue['place_id'] in seen_ids:
                return None # Mark for removal if duplicate? Or just skip
            seen_ids.add(venue['place_id'])
        # Return venue as is (or maybe we want to re-enrich? let's stick to skip if valid)
        # Verify specific enrichment like price_tier
        if venue.get('price_tier') and venue.get('image_url') and "placeholder" not in venue['image_url']:
             return venue

    # 2. Enrichment
    search_query = f"{original_name} {suburb} Cape Town"
    place_result = search_text_new(search_query)
    
    if place_result:
        place_id = place_result['id']
        
        with lock:
            if place_id in seen_ids:
                print(f"Skipping duplicate: {original_name}")
                return None # Duplicate
            seen_ids.add(place_id)
        
        details = get_place_details_new(place_id)
        if details:
            if details.get('userRatingCount', 0) > 10:
                venue['rating'] = details.get('rating', venue.get('rating'))
            
            price_level = details.get('priceLevel')
            if price_level:
                if price_level == 'PRICE_LEVEL_FREE':
                    venue['price_tier'] = 'Free'
                    venue['numerical_price'] = 'Free'
                elif price_level == 'PRICE_LEVEL_INEXPENSIVE':
                    venue['price_tier'] = 'R'
                elif price_level == 'PRICE_LEVEL_MODERATE': 
                    venue['price_tier'] = 'RR'
                elif price_level in ['PRICE_LEVEL_EXPENSIVE', 'PRICE_LEVEL_VERY_EXPENSIVE']:
                    venue['price_tier'] = 'RRR'
            
            photos = details.get('photos', [])
            if photos:
                first_photo = photos[0]
                photo_ref = first_photo.get('name')
                google_url = get_photo_url(photo_ref)
                if not venue.get('image_url') or "placeholder" in venue.get('image_url', ''):
                     venue['image_url'] = google_url
                     auth = first_photo.get('authorAttributions', [])
                     if auth:
                         venue['image_attribution'] = auth[0].get('displayName')

        venue['place_id'] = place_id
        return venue
        
    else:
        print(f"Not found: {original_name}")
        return venue # Keep original

# --- Main Logic ---

def process_venues_threaded():
    data = load_data()
    venues = data.get('venues', [])
    updated_venues = []
    seen_ids = set()
    lock = threading.Lock()
    
    print(f"Starting processing of {len(venues)} venues with {MAX_WORKERS} workers...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_venue = {executor.submit(process_venue_item, v.copy(), seen_ids, lock): v for v in venues}
        
        processed_count = 0
        for future in as_completed(future_to_venue):
            processed_count += 1
            try:
                result = future.result()
                if result:
                    updated_venues.append(result)
            except Exception as exc:
                print(f"Venue generated an exception: {exc}")
                # Append original in case of error to be safe?
                updated_venues.append(future_to_venue[future])
            
            if processed_count % 20 == 0:
                print(f"Processed {processed_count}/{len(venues)}...")

    data['venues'] = updated_venues
    save_data(data)

if __name__ == "__main__":
    if not API_KEY:
        print("Error: MAPS_API_KEY not found in .env")
    else:
        backup_data()
        process_venues_threaded()
