import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
MAPS_API_KEY = os.getenv('MAPS_API_KEY')
JSON_FILE = 'public/lekker-find-data.json'

headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': MAPS_API_KEY,
    'X-Goog-FieldMask': 'places.id,places.photos'
}

def get_details(name):
    payload = {'textQuery': name + ', South Africa'}
    r = requests.post('https://places.googleapis.com/v1/places:searchText', headers=headers, json=payload)
    if r.status_code == 200:
        data = r.json()
        if 'places' in data and data['places']:
            place = data['places'][0]
            pid = place['id']
            # Fetch first photo URL
            photo_url = None
            if 'photos' in place and place['photos']:
                photo_name = place['photos'][0]['name']
                photo_url = f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=1200&key={MAPS_API_KEY}"
            return pid, photo_url
    return None, None

def patch_json():
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues_to_patch = ['Banana Jam Cafe', "Ferdinando's Pizza", 'Dorp Street', 'Chocolat Bistro']
    
    patch_count = 0
    for venue in data['venues']:
        if venue['name'] in venues_to_patch:
            print(f"Patching {venue['name']}...")
            pid, img_url = get_details(venue['name'] if 'Dorp' not in venue['name'] else 'Dorp Street Stellenbosch')
            if pid:
                venue['place_id'] = pid
                if img_url:
                    venue['image_url'] = img_url
                print(f"  -> {pid} (Image: {'Yes' if img_url else 'No'})")
                patch_count += 1
    
    if patch_count > 0:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    patch_json()
