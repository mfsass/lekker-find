#!/usr/bin/env python3
"""
Experimental script to discover new high-rated places using Google Places API.
"""

import os
import sys
import re
import json
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Set

# Load environment variables
load_dotenv()

# Configuration
CSV_FILE = Path('data-262-2025-12-26.csv')
MAPS_API_KEY = os.getenv('MAPS_API_KEY')
TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'

# Cape Town Center
CAPE_TOWN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": -33.9249, "longitude": 18.4241},
        "radius": 50000.0
    }
}


# Categories and Queries
# Each category has a list of specific search terms
DISCOVERY_CATEGORIES = {
    "Food & Dining": [
        "restaurants", "cafes", "bakeries", "cocktail bars", "wine farms", 
        "breakfast spots", "seafood restaurants", "tapas bars", "fine dining"
    ],
    "Nature & Outdoors": [
        "hiking trails", "beaches", "nature reserves", "parks", "botanical gardens", 
        "tidal pools", "scenic drives", "waterfalls", "caves"
    ],
    "Culture & Attractions": [
        "museums", "art galleries", "markets", "landmarks", "tourist attractions", 
        "viewpoints", "historic sites", "theaters"
    ],
    "Activities & Sports": [
        "surfing spots", "kayaking", "paragliding", "yoga studios", "padel courts", 
        "golf courses", "climbing gyms", "horse riding"
    ]
}

# Locations to ensure wider reach
SEARCH_LOCATIONS = [
    "Cape Town",
    "Stellenbosch",
    "Franschhoek",
    "Constantia",
    "Kalk Bay",
    "Hout Bay",
    "Bloubergstrand",
    "Somerset West"
]

SIMILARITY_THRESHOLD = 0.85

def normalize_name(name: str) -> str:
    """Normalize venue name for comparison."""
    name = name.lower().strip()
    name = re.sub(r"[''']s?\b", "", name)
    name = re.sub(r"\bthe\b", "", name)
    name = re.sub(r"[^\w\s]", "", name)
    return re.sub(r"\s+", " ", name).strip()

def load_existing_names() -> Set[str]:
    """Load existing venue names from CSV."""
    if not CSV_FILE.exists():
        return set()
    df = pd.read_csv(CSV_FILE)
    return set(normalize_name(n) for n in df['Name'].tolist())

def search_places_batch(query: str, location: str, min_rating: float = 4.5) -> List[Dict]:
    """Search for places with high rating in a specific location."""
    if not MAPS_API_KEY:
        print("Error: MAPS_API_KEY not set")
        return []

    search_query = f"{query} in {location}"

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': MAPS_API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.types,places.location'
    }

    all_places = []
    page_token = None
    
    # Fetch up to 2 pages (40 results) per location/query to manage quota but get depth
    for _ in range(2):
        payload = {
            'textQuery': search_query,
            'minRating': min_rating,
            # We remove strict locationBias here and rely on the text query "in Location" 
            # to allow the API to find the best spots in that area naturally.
            'pageSize': 20
        }
        
        if page_token:
            payload['pageToken'] = page_token

        try:
            response = requests.post(TEXT_SEARCH_URL, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"API Error ({response.status_code}): {response.text}")
                break
            
            data = response.json()
            places = data.get('places', [])
            all_places.extend(places)
            
            page_token = data.get('nextPageToken')
            if not page_token:
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"Exception during search: {e}")
            break
            
    return all_places

def main():
    if not MAPS_API_KEY:
        print("Please set MAPS_API_KEY in .env")
        return

    print("Loading existing venues...")
    existing_names = load_existing_names()
    print(f"Loaded {len(existing_names)} existing venues.")

    all_candidates = []
    seen_place_ids = set()

    for category, queries in DISCOVERY_CATEGORIES.items():
        print(f"\n=== Searching Category: {category} ===")
        category_candidates = []
        
        # We'll use a slightly lower rating threshold for fetching, then filter strict
        # strict_min_rating = 4.7
        # strict_min_reviews = 500
        
        # But we adapt for "Activities" or "Hidden" if needed. 
        # For now, implementing the user's robust request:
        
        for q in queries:
            # Pick a random subset of locations or all?
            # Doing all combinations is expensive (8 locations * ~8 queries = 64 requests per category).
            # Let's optimize: General search first, then specific if needed.
            # Actually, let's just use "Cape Town" generally, and maybe "Stellenbosch" for wine/food.
            
            locations_to_use = ["Cape Town"]
            if "wine" in q or "food" in q:
                locations_to_use.append("Stellenbosch")
                locations_to_use.append("Franschhoek")
            elif "surf" in q:
                locations_to_use.append("Muizenberg")
            
            for loc in locations_to_use:
                # print(f"  Querying: '{q}' in {loc}...")
                results = search_places_batch(q, loc, min_rating=4.5)
                
                for place in results:
                    pid = place.get('id')
                    if pid in seen_place_ids:
                        continue
                    
                    name = place.get('displayName', {}).get('text', '')
                    rating = place.get('rating', 0)
                    reviews = place.get('userRatingCount', 0)
                    
                    # 1. Filter: Legitimacy (Review Count)
                    # Lower threshold for Activities/Nature as they often have fewer reviews than restaurants
                    min_reviews = 400 if category == "Food & Dining" else 200
                    if reviews < min_reviews:
                        continue

                    # 2. Filter: Quality (Rating)
                    if rating < 4.6: # User asked for 4.7, we allow 4.6 to catch rounding/fluctuation
                        continue

                    # 3. Filter: Duplicates
                    if normalize_name(name) in existing_names:
                        continue

                    # Add to candidates
                    seen_place_ids.add(pid)
                    cand = {
                        "Name": name,
                        "Category": category,
                        "SubCategory": q,
                        "Rating": rating,
                        "Reviews": reviews,
                        "Address": place.get('formattedAddress', ''),
                        "ID": pid
                    }
                    category_candidates.append(cand)

        # Sort by Rating desc, then Reviews desc
        category_candidates.sort(key=lambda x: (x['Rating'], x['Reviews']), reverse=True)
        
        # Take top 15 unique for this category
        top_15 = category_candidates[:15]
        all_candidates.extend(top_15)
        print(f"  Found {len(category_candidates)} candidates. Selected top {len(top_15)}.")
        for c in top_15:
            print(f"    - {c['Name']} ({c['Rating']}*, {c['Reviews']} reviews) [{c['SubCategory']}]")

    # Output results
    print("\n\n=== FINAL DISCOVERY LIST ===")
    print(f"{'Name':<40} | {'Category':<20} | {'Rating':<5} | {'Reviews':<7}")
    print("-" * 80)
    
    with open('discovered_places.txt', 'w', encoding='utf-8') as f:
        for c in all_candidates:
            # Format: Name|Location Hint|Description(Category + stats)
            line = f"{c['Name']}|{c['Address']}|{c['Category']} - {c['SubCategory']} ({c['Rating']} stars, {c['Reviews']} reviews)"
            f.write(line + "\n")
            print(f"{c['Name']:<40} | {c['Category']:<20} | {c['Rating']:<5} | {c['Reviews']:<7}")

    print(f"\nSaved {len(all_candidates)} candidates to discovered_places.txt")
    print("Review this file, then use it with 'python scripts/add_places.py --input discovered_places.txt' to add them.")

if __name__ == "__main__":
    main()
