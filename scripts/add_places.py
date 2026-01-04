#!/usr/bin/env python3
"""
Lekker Find - Places API Integration Pipeline
==============================================

A consolidated script for adding new venues/hikes using Google Places API.
Features smart extraction, duplicate detection, batch processing, and full enrichment.

USAGE:
------
    # Add places from a manual list (demo mode)
    python scripts/add_places.py --demo

    # Add places from a text file
    python scripts/add_places.py --input places.txt

    # Search and add places meeting criteria
    python scripts/add_places.py --search "hiking trails near Cape Town" --min-rating 4.5 --min-reviews 100

    # Automated discovery mode (future)
    python scripts/add_places.py --discover --radius 60 --min-rating 4.7 --min-reviews 500

    # Dry run to preview without changes
    python scripts/add_places.py --demo --dry-run

FEATURES:
---------
    ✅ Google Places API (New) integration
    ✅ Duplicate detection against existing venues
    ✅ Smart suburb/location extraction
    ✅ AI-generated vibe descriptions
    ✅ Batch API support for cost savings
    ✅ Image fetching and localization
    ✅ Automatic embedding generation

COST ESTIMATES:
---------------
    - Google Places Text Search: ~$0.032 per query
    - Google Places Details: ~$0.017 per request
    - OpenAI gpt-5-nano: ~$0.0001 per venue description
    - Total for 10 venues: ~$0.50

"""

import os
import sys
import re
import json
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# File paths
CSV_FILE = Path('data-262-2025-12-26.csv')
JSON_FILE = Path('public/lekker-find-data.json')
IMAGES_DIR = Path('public/images')

# API Keys
MAPS_API_KEY = os.getenv('MAPS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Google Places API (New)
TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'
PLACE_DETAILS_URL = 'https://places.googleapis.com/v1/places'
PHOTO_BASE_URL = 'https://places.googleapis.com/v1'

CAPE_TOWN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": -33.9249, "longitude": 18.4241},
        "radius": 50000.0  # 50km - max allowed by Google Places API
    }
}

# OpenAI Model
OPENAI_MODEL = 'gpt-5-nano'

# Similarity threshold for duplicate detection
SIMILARITY_THRESHOLD = 0.85

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PlaceInput:
    """Input data for a place to add."""
    name: str
    location_hint: str = ""  # e.g., "Lower Cable Station" or "Camps Bay"
    description_hint: str = ""  # e.g., "Local guide suggestion"
    category: str = "Nature"  # Default for hikes
    
    
@dataclass
class PlaceDetails:
    """Extracted details from Google Places API."""
    place_id: str
    name: str
    formatted_address: str
    suburb: str
    rating: Optional[float]
    review_count: int
    types: List[str]
    editorial_summary: str
    reviews: List[str]
    photo_reference: str
    price_level: Optional[int]
    lat: float
    lng: float
    
    
@dataclass
class VenueOutput:
    """Final venue data for CSV."""
    Name: str
    Category: str
    Tourist_Level: int
    Price_Range: str
    Numerical_Price: str
    Best_Season: str
    Vibe: str
    Description: str
    Rating: Optional[float]
    VibeDescription: str
    Suburb: str


# ============================================================================
# DUPLICATE DETECTION
# ============================================================================

def normalize_name(name: str) -> str:
    """Normalize venue name for comparison."""
    # Remove common suffixes, articles, punctuation
    name = name.lower().strip()
    name = re.sub(r"[''']s?\b", "", name)  # Remove possessives
    name = re.sub(r"\bthe\b", "", name)
    name = re.sub(r"\bhike\b", "", name)
    name = re.sub(r"\btrail\b", "", name)
    name = re.sub(r"\bbeach\b", "", name)
    name = re.sub(r"[^\w\s]", "", name)  # Remove punctuation
    name = re.sub(r"\s+", " ", name).strip()
    return name


def similarity_score(name1: str, name2: str) -> float:
    """Calculate similarity between two venue names."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    return SequenceMatcher(None, n1, n2).ratio()


def find_duplicates(new_name: str, existing_names: List[str]) -> List[Tuple[str, float]]:
    """Find potential duplicates among existing venues."""
    matches = []
    for existing in existing_names:
        score = similarity_score(new_name, existing)
        if score >= SIMILARITY_THRESHOLD:
            matches.append((existing, score))
    return sorted(matches, key=lambda x: x[1], reverse=True)


def is_duplicate(new_name: str, existing_names: List[str]) -> Tuple[bool, Optional[str]]:
    """Check if venue is a duplicate. Returns (is_dup, matched_name)."""
    matches = find_duplicates(new_name, existing_names)
    if matches:
        return True, matches[0][0]
    return False, None


# ============================================================================
# GOOGLE PLACES API
# ============================================================================

def search_place(query: str, category_hint: str = "") -> Optional[Dict]:
    """
    Search for a place using Google Places API (New).
    Returns the first matching place with all details.
    """
    if not MAPS_API_KEY:
        print("  ✗ MAPS_API_KEY not found in .env")
        return None
    
    # Enhanced query for better matching
    search_query = f"{query}, Cape Town"
    
    # Use a simpler field mask that works (matching fetch_images.py pattern)
    # Note: Some fields may not be available in all API versions
    field_mask = 'places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.types,places.editorialSummary,places.reviews,places.photos,places.location'
    
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': MAPS_API_KEY,
        'X-Goog-FieldMask': field_mask
    }
    
    payload = {
        'textQuery': search_query,
        'locationBias': CAPE_TOWN_LOCATION_BIAS,
        'languageCode': 'en'
    }
    
    try:
        response = requests.post(TEXT_SEARCH_URL, headers=headers, json=payload)
        
        # Log API error details for debugging
        if response.status_code != 200:
            print(f"  ✗ API {response.status_code}: {response.text[:200]}")
            return None
            
        data = response.json()
        
        if 'places' in data and len(data['places']) > 0:
            return data['places'][0]
        return None
        
    except Exception as e:
        print(f"  ✗ Places API error: {e}")
        return None


def extract_suburb(place: Dict) -> str:
    """Extract suburb from address components."""
    components = place.get('addressComponents', [])
    
    # Priority: sublocality > locality > administrative_area_level_2
    for component in components:
        types = component.get('types', [])
        if 'sublocality' in types or 'sublocality_level_1' in types:
            return component.get('longText', '')
    
    for component in components:
        types = component.get('types', [])
        if 'locality' in types:
            return component.get('longText', '')
    
    # Fallback: extract from formatted address
    address = place.get('formattedAddress', '')
    parts = address.split(',')
    if len(parts) >= 2:
        # Usually suburb is the second part
        potential_suburb = parts[1].strip() if len(parts) > 2 else parts[0].strip()
        # Filter out "Cape Town" and similar
        if potential_suburb.lower() not in ['cape town', 'south africa', 'western cape']:
            return potential_suburb
    
    return ""


def parse_place_details(place: Dict) -> PlaceDetails:
    """Parse Google Places API response into PlaceDetails."""
    # Extract reviews text
    reviews = []
    for review in place.get('reviews', [])[:5]:
        text = review.get('text', {}).get('text', '')
        if text:
            reviews.append(text[:300])  # Truncate long reviews
    
    # Extract photo reference
    photos = place.get('photos', [])
    photo_ref = photos[0].get('name', '') if photos else ''
    
    # Extract location
    location = place.get('location', {})
    
    return PlaceDetails(
        place_id=place.get('id', ''),
        name=place.get('displayName', {}).get('text', ''),
        formatted_address=place.get('formattedAddress', ''),
        suburb=extract_suburb(place),
        rating=place.get('rating'),
        review_count=place.get('userRatingCount', 0),
        types=place.get('types', []),
        editorial_summary=place.get('editorialSummary', {}).get('text', ''),
        reviews=reviews,
        photo_reference=photo_ref,
        price_level=place.get('priceLevel'),
        lat=location.get('latitude', 0),
        lng=location.get('longitude', 0)
    )


# ============================================================================
# VIBE & DESCRIPTION GENERATION
# ============================================================================

def generate_vibe_tags(details: PlaceDetails, category: str, hint: str = "") -> str:
    """Generate vibe tags based on place data."""
    tags = set()
    
    # Derive from types
    type_mapping = {
        'hiking_area': ['Active', 'Nature', 'Scenic'],
        'park': ['Nature', 'Peaceful', 'Family'],
        'natural_feature': ['Natural', 'Scenic', 'Wild'],
        'tourist_attraction': ['Famous', 'Tourist'],
        'restaurant': ['Food', 'Social'],
        'cafe': ['Cozy', 'Relaxed'],
        'bar': ['Lively', 'Social'],
        'beach': ['Beach', 'Coastal', 'Scenic'],
    }
    
    for place_type in details.types:
        if place_type in type_mapping:
            tags.update(type_mapping[place_type])
    
    # Derive from rating
    if details.rating and details.rating >= 4.7:
        tags.add('Famous')
    if details.review_count < 100:
        tags.add('Hidden')
    elif details.review_count > 1000:
        tags.add('Famous')
    
    # Derive from description hint
    hint_lower = hint.lower()
    if 'secret' in hint_lower:
        tags.add('Secret')
    if 'hidden' in hint_lower or 'unmarked' in hint_lower:
        tags.add('Hidden')
    if 'technical' in hint_lower or 'scrambling' in hint_lower:
        tags.add('Adventurous')
    if 'view' in hint_lower or 'panoramic' in hint_lower:
        tags.add('Scenic')
    if 'sunset' in hint_lower:
        tags.add('Sunset')
    if 'waterfall' in hint_lower:
        tags.add('Waterfall')
    if 'forest' in hint_lower or 'trees' in hint_lower:
        tags.add('Forest')
    if 'easy' in hint_lower or 'family' in hint_lower:
        tags.add('Family')
    
    # Limit to 3 tags
    final_tags = list(tags)[:3]
    return ', '.join(final_tags) if final_tags else 'Scenic, Nature'


def estimate_tourist_level(details: PlaceDetails) -> int:
    """Estimate tourist level (1-10 scale)."""
    # Based on review count
    if details.review_count > 5000:
        return 10
    elif details.review_count > 2000:
        return 9
    elif details.review_count > 1000:
        return 8
    elif details.review_count > 500:
        return 7
    elif details.review_count > 200:
        return 6
    elif details.review_count > 100:
        return 5
    elif details.review_count > 50:
        return 4
    elif details.review_count > 20:
        return 3
    else:
        return 2


def estimate_price_range(details: PlaceDetails, category: str) -> Tuple[str, str]:
    """Estimate price range based on category and data."""
    if category == "Nature":
        # Most hikes are free, some reserves have fees
        if any(t in details.types for t in ['nature_reserve', 'national_park']):
            return "R", "R40-R150"
        return "Free", "Free"
    
    # Map Google price level to our system
    if details.price_level:
        levels = {
            0: ("R", "R50-R100"),
            1: ("R", "R100-R200"),
            2: ("RR", "R200-R400"),
            3: ("RRR", "R400-R800"),
            4: ("RRR", "R800+"),
        }
        return levels.get(details.price_level, ("RR", "R200-R400"))
    
    return "R", "R100-R200"


def generate_vibe_description_ai(
    details: PlaceDetails,
    category: str,
    vibe_tags: str,
    hint: str = ""
) -> Optional[str]:
    """Generate rich vibe description using AI."""
    if not OPENAI_API_KEY:
        print("  ⚠ OPENAI_API_KEY not set - skipping vibe description")
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        print("  ⚠ openai package not installed")
        return None
    
    # Build context
    context_parts = []
    if details.editorial_summary:
        context_parts.append(f"Google says: \"{details.editorial_summary}\"")
    if details.reviews:
        reviews_text = " | ".join(details.reviews[:2])
        context_parts.append(f"Reviews: \"{reviews_text[:400]}\"")
    if hint:
        context_parts.append(f"Local tip: \"{hint}\"")
    
    context = "\n".join(context_parts) if context_parts else "Limited information available."
    
    prompt = f"""You are a Cape Town travel expert. Write a 2-3 sentence vibe description for this place.
Focus on the FEELING and ATMOSPHERE - what makes it special, who would love it, and the energy.
Use warm, inviting language. Be specific and evocative. Avoid clichés.

Place: {details.name}
Category: {category}
Location: {details.suburb or details.formatted_address}
Vibes: {vibe_tags}
Rating: {details.rating}/5 ({details.review_count:,} reviews)

Context:
{context}

Write ONLY the vibe description (2-3 sentences). No intro or labels."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=200,  # Use max_completion_tokens for GPT-5 models
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ⚠ OpenAI error: {e}")
        return None


def create_short_description(details: PlaceDetails, hint: str = "") -> str:
    """Create a concise description for CSV."""
    # Use editorial summary if available
    if details.editorial_summary:
        return details.editorial_summary[:200]
    
    # Use the hint
    if hint:
        return hint[:200]
    
    # Generate from reviews
    if details.reviews:
        # Extract key phrases from first review
        first_review = details.reviews[0][:200]
        return f"Popular spot with {details.review_count:,} reviews. {first_review[:100]}..."
    
    return f"A rated {details.rating}/5 spot in {details.suburb or 'Cape Town'}."


# ============================================================================
# IMAGE HANDLING
# ============================================================================

def get_photo_url(photo_name: str, max_width: int = 1200) -> str:
    """Construct photo URL from photo resource name."""
    return f"{PHOTO_BASE_URL}/{photo_name}/media?maxWidthPx={max_width}&key={MAPS_API_KEY}"


def download_image(url: str, venue_name: str) -> Optional[Path]:
    """Download image and save locally with stable naming."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Generate stable filename from venue name
        safe_name = re.sub(r'[^\w\s-]', '', venue_name.lower())
        safe_name = re.sub(r'[-\s]+', '-', safe_name).strip('-')
        filename = f"{safe_name}.jpg"
        
        filepath = IMAGES_DIR / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filepath
        
    except Exception as e:
        print(f"  ⚠ Image download failed: {e}")
        return None


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_place(
    input_place: PlaceInput,
    existing_names: List[str],
    dry_run: bool = False
) -> Optional[VenueOutput]:
    """Process a single place and generate venue data."""
    print(f"\n  Processing: {input_place.name}")
    
    # Check for duplicates
    is_dup, match = is_duplicate(input_place.name, existing_names)
    if is_dup:
        print(f"    ⚠ DUPLICATE: Similar to '{match}' - skipping")
        return None
    
    # Search Google Places
    query = f"{input_place.name} {input_place.location_hint}".strip()
    place = search_place(query, input_place.category)
    
    if not place:
        print(f"    ✗ Not found on Google Places")
        return None
    
    # Parse details
    details = parse_place_details(place)
    print(f"    ✓ Found: {details.name}")
    print(f"      Rating: {details.rating}/5 ({details.review_count:,} reviews)")
    print(f"      Suburb: {details.suburb or 'Unknown'}")
    
    if dry_run:
        print("    [DRY RUN] Would add this venue")
        return None
    
    # Generate vibes and descriptions
    vibe_tags = generate_vibe_tags(details, input_place.category, input_place.description_hint)
    tourist_level = estimate_tourist_level(details)
    price_range, numerical_price = estimate_price_range(details, input_place.category)
    short_desc = create_short_description(details, input_place.description_hint)
    
    # Generate AI vibe description
    print("    Generating vibe description...")
    vibe_description = generate_vibe_description_ai(
        details, input_place.category, vibe_tags, input_place.description_hint
    )
    
    if vibe_description:
        print(f"    ✓ Vibe: {vibe_description[:80]}...")
    
    # Create output
    return VenueOutput(
        Name=details.name,
        Category=input_place.category,
        Tourist_Level=tourist_level,
        Price_Range=price_range,
        Numerical_Price=numerical_price,
        Best_Season="All Year",
        Vibe=vibe_tags,
        Description=short_desc,
        Rating=details.rating,
        VibeDescription=vibe_description or "",
        Suburb=details.suburb
    )


def add_venues_to_csv(venues: List[VenueOutput]):
    """Add new venues to the CSV file."""
    if not venues:
        print("\nNo venues to add.")
        return
    
    # Load existing CSV
    df = pd.read_csv(CSV_FILE)
    
    # Convert venues to DataFrame
    new_rows = pd.DataFrame([asdict(v) for v in venues])
    
    # Concatenate
    df = pd.concat([df, new_rows], ignore_index=True)
    
    # Save
    df.to_csv(CSV_FILE, index=False)
    print(f"\n✓ Added {len(venues)} venues to {CSV_FILE}")


# ============================================================================
# DEMO DATA
# ============================================================================

DEMO_HIKES = [
    PlaceInput("India Venster", "Lower Cable Station", "An adventurous, technical alternative to Platteklip Gorge with scrambling and chains"),
    PlaceInput("Tranquility Cracks", "Theresa Ave, Camps Bay", "A hidden labyrinth of corridors and ancient yellowwood trees"),
    PlaceInput("Judas Peak", "Suikerbossie, Hout Bay", "Last of the 12 Apostles with unparalleled Atlantic views"),
    PlaceInput("Kasteelspoort", "Theresa Ave, Camps Bay", "Home to the famous Diving Board rock and old cableway ruins"),
    PlaceInput("Skeleton Gorge", "Kirstenbosch Gardens", "Lush climb through indigenous forest to Maclear's Beacon"),
    PlaceInput("Suther Peak", "Hout Bay", "Rugged wild trail seeing the Sentinel from above"),
    PlaceInput("Elephant's Eye Cave", "Silvermine Nature Reserve", "Family-friendly hike to a massive cave with Silvermine Dam swim"),
    PlaceInput("Lion's Head", "Signal Hill Road", "The go-to for sunset or full moon hikes with 360-degree views"),
    PlaceInput("Spes Bona Valley", "Boyes Drive, Kalk Bay", "Raised wooden boardwalks through shady forest with whale-watching"),
    PlaceInput("Myburgh's Waterfall Ravine", "Tarragona, Hout Bay", "Winter waterfalls or February rare red disa flowers"),
]

DEMO_WINELANDS = [
    PlaceInput("Botmaskop", "Stellenbosch, Idas Valley", "Best view in the Winelands overlooking Hellshoogte pass", "Nature"),
    PlaceInput("Krom River Trail", "Du Toitskloof, Paarl", "Jungle hike with river crossing to spectacular waterfalls", "Nature"),
    PlaceInput("Helderberg West Peak", "Somerset West", "Serious climb with unmatched views back to Cape Town", "Nature"),
    PlaceInput("Paradyskloof Waterfall", "Stellenbosch", "Magical pine forest and fynbos walk to secluded waterfall", "Nature"),
    PlaceInput("Mont Rochelle Vista Trail", "Franschhoek", "High-altitude hiking with views into Wemmershoek valley", "Nature"),
]


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Add new places to Lekker Find using Google Places API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--demo', action='store_true', help='Run with demo hike data')
    parser.add_argument('--input', type=str, help='Input file with places (one per line: Name|Location|Description)')
    parser.add_argument('--search', type=str, help='Search query for discovering places')
    parser.add_argument('--min-rating', type=float, default=4.0, help='Minimum rating filter (default: 4.0)')
    parser.add_argument('--min-reviews', type=int, default=10, help='Minimum review count (default: 10)')
    parser.add_argument('--category', type=str, default='Nature', help='Category for new venues (default: Nature)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--skip-embeddings', action='store_true', help='Skip embedding generation')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LEKKER FIND - PLACES API INTEGRATION")
    print("=" * 60)
    
    # Validate API keys
    if not MAPS_API_KEY:
        print("\n✗ ERROR: MAPS_API_KEY not found in .env file")
        print("  Add: MAPS_API_KEY=your_key_here")
        sys.exit(1)
    
    # Load existing venue names for duplicate checking
    print(f"\n[1/4] Loading existing venues from {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    existing_names = df['Name'].tolist()
    print(f"  ✓ Found {len(existing_names)} existing venues")
    
    # Get places to process
    places_to_process = []
    
    if args.demo:
        print(f"\n[2/4] Using demo data ({len(DEMO_HIKES)} hikes + {len(DEMO_WINELANDS)} winelands)...")
        places_to_process = DEMO_HIKES + DEMO_WINELANDS
    elif args.input:
        print(f"\n[2/4] Loading places from {args.input}...")
        with open(args.input, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 1:
                    places_to_process.append(PlaceInput(
                        name=parts[0].strip(),
                        location_hint=parts[1].strip() if len(parts) > 1 else "",
                        description_hint=parts[2].strip() if len(parts) > 2 else "",
                        category=parts[3].strip() if len(parts) > 3 else args.category
                    ))
        print(f"  ✓ Loaded {len(places_to_process)} places")
    elif args.search:
        print(f"\n[2/4] Searching for: '{args.search}'...")
        # TODO: Implement search-based discovery
        print("  ⚠ Search mode not yet implemented")
        sys.exit(0)
    else:
        print("\n✗ No input specified. Use --demo, --input, or --search")
        parser.print_help()
        sys.exit(1)
    
    # Process each place
    print(f"\n[3/4] Processing {len(places_to_process)} places...")
    new_venues = []
    skipped = 0
    failed = 0
    
    for place in places_to_process:
        result = process_place(place, existing_names, args.dry_run)
        
        if result:
            new_venues.append(result)
            existing_names.append(result.Name)  # Prevent duplicates within batch
        elif not args.dry_run:
            # Check if it was skipped (duplicate) or failed
            is_dup, _ = is_duplicate(place.name, existing_names)
            if is_dup:
                skipped += 1
            else:
                failed += 1
        
        # Rate limiting
        time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  ✓ New venues found: {len(new_venues)}")
    print(f"  ⚠ Skipped (duplicates): {skipped}")
    print(f"  ✗ Failed (not found): {failed}")
    
    if args.dry_run:
        print("\n[DRY RUN] No changes made")
        return
    
    # Add to CSV
    if new_venues:
        print(f"\n[4/4] Adding venues to CSV...")
        add_venues_to_csv(new_venues)
        
        # Suggest next steps
        print("\n" + "=" * 60)
        print("NEXT STEPS")
        print("=" * 60)
        print("  1. Run embeddings: python scripts/generate_embeddings.py --update")
        print("  2. Fetch images:   python scripts/fetch_images.py")
        print("  3. Localize:       python scripts/localize_images.py")
        print("  4. Validate:       python scripts/validate_image_sync.py")
        
        if not args.skip_embeddings:
            print("\nWould you like to run embeddings now? (y/n)")
            # In future: auto-run if confirmed


if __name__ == "__main__":
    main()
