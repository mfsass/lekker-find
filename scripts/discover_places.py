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

# Targeted Locations and Categories based on Gap Analysis
TARGETS = [
    {
        "locations": ["Somerset West", "Stellenbosch"],
        "categories": ["Food & Dining", "Nature & Outdoors", "Culture & Attractions", "Activities & Sports"],
        "min_reviews": 200,
        "min_rating": 4.7
    },
    {
        "locations": ["Cape Town"],
        "categories": ["Nature & Outdoors", "Activities & Sports"], # Focus on gaps
        "min_reviews": 200,
        "min_rating": 4.7
    }
]

def main():
    if not MAPS_API_KEY:
        print("Please set MAPS_API_KEY in .env")
        return

    print("Loading existing venues...")
    existing_names = load_existing_names()
    print(f"Loaded {len(existing_names)} existing venues.")

    all_candidates = []
    seen_place_ids = set()

    for target in TARGETS:
        for loc in target["locations"]:
            print(f"\n=== Targeting Location: {loc} ===")
            for cat in target["categories"]:
                print(f"  Category: {cat}")
                
                # Get queries for this category
                queries = DISCOVERY_CATEGORIES.get(cat, [])
                
                category_candidates = []
                for q in queries:
                    # Search
                    # print(f"    Searching for '{q}' in {loc}...")
                    results = search_places_batch(q, loc, min_rating=4.5) # Fetch wide, filter strict
                    
                    for place in results:
                        pid = place.get('id')
                        if pid in seen_place_ids:
                            continue
                        
                        name = place.get('displayName', {}).get('text', '')
                        rating = place.get('rating', 0)
                        reviews = place.get('userRatingCount', 0)
                        
                        # 1. Filter: Reviews (User requested min 200, maybe 10s if desperate but let's start strict)
                        if reviews < target["min_reviews"]:
                            continue

                        # 2. Filter: Rating (User requested 4.7+)
                        if rating < target["min_rating"]:
                            continue

                        # 3. Filter: Duplicates
                        if normalize_name(name) in existing_names:
                            continue

                        # Add to candidates
                        seen_place_ids.add(pid)
                        cand = {
                            "Name": name,
                            "Category": cat,
                            "SubCategory": q,
                            "Rating": rating,
                            "Reviews": reviews,
                            "Address": place.get('formattedAddress', ''),
                            "ID": pid
                        }
                        category_candidates.append(cand)
                
                # Sort and pick top gems for this category/location
                category_candidates.sort(key=lambda x: (x['Rating'], x['Reviews']), reverse=True)
                
                # Limit to top 5 per category per location to avoid overwhelming
                top_picks = category_candidates[:7] 
                all_candidates.extend(top_picks)
                print(f"    Found {len(category_candidates)} candidates. Selected top {len(top_picks)}.")
                for c in top_picks:
                    print(f"      - {c['Name']} ({c['Rating']}*, {c['Reviews']} reviews) [{c['SubCategory']}]")

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
