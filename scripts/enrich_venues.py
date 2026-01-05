#!/usr/bin/env python3
"""
Lekker Find - Venue Enrichment Script
======================================

Enriches venue data with:
1. Google Maps ratings
2. AI-generated vibe descriptions (using gpt-5-nano)

Usage:
    python scripts/enrich_venues.py              # Process NEW venues only (no VibeDescription)
    python scripts/enrich_venues.py --all        # Reprocess ALL venues (regenerate descriptions)
    python scripts/enrich_venues.py --fix-malformed  # Fix venues with raw API data in descriptions
    python scripts/enrich_venues.py --test       # Test with 5 venues
    python scripts/enrich_venues.py --dry-run    # Preview what would be processed
    python scripts/enrich_venues.py --batch      # Use Batch API for faster processing (async)

Cost estimate:
    - Google Places: ~$0.00 (using existing API)
    - OpenAI gpt-5-nano (sync): ~$0.02 for 262 venues
    - OpenAI Batch API: 50% cheaper, completes within 24 hours

FUTURE OPTIMIZATION - OpenAI Batch API:
---------------------------------------
For large-scale enrichment (100+ venues), use the Batch API for:
- 50% cost reduction
- Higher rate limits (up to 50,000 requests per batch)
- Processing within 24 hours

Batch API workflow:
1. Create a .jsonl file with one request per line:
   {"custom_id": "venue_0", "method": "POST", "url": "/v1/chat/completions", 
    "body": {"model": "gpt-5-nano", "messages": [...]}}
2. Upload: client.files.create(file=open("batch_input.jsonl"), purpose="batch")
3. Create batch: client.batches.create(input_file_id=file_id, endpoint="/v1/chat/completions")
4. Poll status: client.batches.retrieve(batch_id)
5. Download results when complete

See: https://platform.openai.com/docs/guides/batch
"""

import os
import sys
import time
import pandas as pd
from dotenv import load_dotenv
from typing import Optional, Dict

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_CSV = 'data-262-2025-12-26.csv'
MAPS_API_KEY = os.getenv('MAPS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Google Places API
TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'
CAPE_TOWN_LOCATION_BIAS = {
    "circle": {
        "center": {"latitude": -33.9249, "longitude": 18.4241},
        "radius": 50000.0
    }
}

# OpenAI Model - latest cheap model (Dec 2025)
OPENAI_MODEL = 'gpt-5-nano'

# ============================================================================
# GOOGLE PLACES API
# ============================================================================

def get_place_details(venue_name: str, category: str) -> Optional[Dict]:
    """
    Fetch place details from Google Places API.
    Returns rating, types, and editorial summary.
    """
    import requests
    
    if not MAPS_API_KEY:
        print("✗ MAPS_API_KEY not found in .env")
        return None
    
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': MAPS_API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.rating,places.types,places.editorialSummary,places.reviews'
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
            place = data['places'][0]
            return {
                'rating': place.get('rating'),
                'types': place.get('types', []),
                'editorial_summary': place.get('editorialSummary', {}).get('text', ''),
                'reviews': [r.get('text', {}).get('text', '') for r in place.get('reviews', [])[:3]]
            }
        return None
        
    except Exception as e:
        print(f"  ✗ Places API error: {e}")
        return None


# ============================================================================
# OPENAI VIBE DESCRIPTION
# ============================================================================

def generate_vibe_description(
    name: str,
    category: str,
    original_vibes: str,
    description: str,
    rating: Optional[float],
    types: list,
    editorial_summary: str,
    reviews: list
) -> Optional[str]:
    """
    Generate a 2-3 sentence vibe description using gpt-5-nano.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        print("✗ openai package not installed. Run: pip install openai")
        return None
    
    if not OPENAI_API_KEY:
        print("✗ OPENAI_API_KEY not found in .env")
        return None
    
    # Build context from available data
    context_parts = []
    
    if editorial_summary:
        context_parts.append(f"Google says: \"{editorial_summary}\"")
    
    if reviews:
        review_text = " | ".join(reviews[:2])
        context_parts.append(f"Reviews mention: \"{review_text[:300]}\"")
    
    if types:
        context_parts.append(f"Place types: {', '.join(types[:5])}")
    
    context = "\n".join(context_parts) if context_parts else "No additional context available."
    
    prompt = f"""You are a Cape Town travel expert. Write EXACTLY ONE SHORT, ATMOSPHERIC SENTENCE for this venue.
    
    CRITICAL RULES:
    1. EXTREMELY CONCISE: Maximum 120 characters. 
    2. ATMOSPHERE ONLY: Focus ONLY on the feeling, energy, or "vibe".
    3. NO FACTS: Do NOT mention the name, location, category, or specific activities.
    4. EVOCATIVE: Use warm, punchy, inviting language.
    5. NO INTRO: Do not start with "This place..." or "A...". Just the vibe.
    6. DISTINCT: Do not repeat phrases from the 'Our description' section below. Provide a fresh emotional angle.

    Venue: {name}
    Category: {category}
    Original vibes: {original_vibes}
    Our description: {description}
    Rating: {rating}/5 stars

    Context:
    {context}

    Example of what I want: "Sun-dappled tables and a gentle salt breeze invite long, lazy afternoons by the water."
    Example of what I DON'T want: "This is a seafood restaurant in Kalk Bay with great views."

    Write ONLY the vibe sentence."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=10000
        )
        content = response.choices[0].message.content.strip().strip('"')
        
        # Cleanup: Remove common AI prefixes despite instructions
        if content.lower().startswith("the vibe is "):
            content = content[12:]
        if content.lower().startswith("vibe: "):
            content = content[6:]
            
        # Validation: Reject if empty or looks like raw API data
        if not content:
            print(f"  ⚠ AI returned empty content for '{name}'")
            print(f"DEBUG: Prompt length: {len(prompt)}")
            print(f"DEBUG: Full Response: {response}")
            return None
            
        if "stars" in content and "reviews" in content and len(content) < 50:
            print(f"  ⚠ AI returned raw data format: '{content}' - discarding")
            return None
            
        return content
    except Exception as e:
        print(f"  ✗ OpenAI error: {e}")
        return None


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_venues(test_mode: bool = False, dry_run: bool = False, process_all: bool = False, fix_malformed: bool = False, reprocess_long: bool = False):
    """
    Process venues and add Rating + VibeDescription columns.
    By default, only processes venues without VibeDescription.
    Use process_all=True to regenerate all descriptions.
    Use fix_malformed=True to regenerate descriptions containing raw API data.
    Use reprocess_long=True to regenerate descriptions longer than 150 characters.
    """
    import re
    
    print("=" * 60)
    print("LEKKER FIND - VENUE ENRICHMENT")
    print("=" * 60)
    
    if not os.path.exists(INPUT_CSV):
        print(f"\n✗ {INPUT_CSV} not found")
        return
    
    # Load CSV
    print(f"\n[1/3] Loading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    print(f"  ✓ Loaded {len(df)} venues")
    
    # Add columns if missing
    if 'Rating' not in df.columns:
        df['Rating'] = None
    if 'VibeDescription' not in df.columns:
        df['VibeDescription'] = None
    
    # Pattern to detect malformed descriptions (raw API data)
    malformed_pattern = r'\(\d+\.?\d*\s*stars?,\s*\d+\s*reviews?\)'
    
    # Find venues needing enrichment
    if process_all:
        needs_enrichment = df.copy()
        print(f"  → [--all] Processing ALL {len(needs_enrichment)} venues")
    elif fix_malformed:
        # Find venues with malformed descriptions
        def has_malformed_desc(row):
            desc = str(row.get('Description', ''))
            vibe_desc = str(row.get('VibeDescription', ''))
            return bool(re.search(malformed_pattern, desc)) or bool(re.search(malformed_pattern, vibe_desc))
        
        needs_enrichment = df[df.apply(has_malformed_desc, axis=1)]
        print(f"  → [--fix-malformed] Found {len(needs_enrichment)} venues with raw API data in descriptions")
    elif reprocess_long:
        # Find venues with descriptions > 150 chars
        def is_long_desc(row):
            vibe_desc = str(row.get('VibeDescription', ''))
            return len(vibe_desc) > 150
        
        needs_enrichment = df[df.apply(is_long_desc, axis=1)]
        print(f"  → [--reprocess-long] Found {len(needs_enrichment)} venues with long descriptions (> 150 chars)")
    else:
        needs_enrichment = df[df['VibeDescription'].isna() | (df['VibeDescription'] == '')]
        print(f"  → {len(needs_enrichment)} NEW venues need enrichment")
    
    if test_mode:
        needs_enrichment = needs_enrichment.head(5)
        print(f"  → [TEST MODE] Processing first 5 venues")
    
    if dry_run:
        print("\n[DRY RUN] Would process:")
        for _, row in needs_enrichment.iterrows():
            print(f"  - {row['Name']} ({row['Category']})")
        return
    
    if len(needs_enrichment) == 0:
        print("\n✓ All venues already enriched!")
        return
    
    # Process venues
    print(f"\n[2/3] Enriching venues...")
    
    success = 0
    failed = 0
    
    for idx, row in needs_enrichment.iterrows():
        name = row['Name']
        print(f"  [{success + failed + 1}/{len(needs_enrichment)}] {name}...", end=' ')
        
        # Get Google Places data
        place_data = get_place_details(name, row['Category'])
        
        if place_data:
            # Update rating
            if place_data['rating']:
                df.at[idx, 'Rating'] = place_data['rating']
            
            # Generate vibe description
            vibe_desc = generate_vibe_description(
                name=name,
                category=row['Category'],
                original_vibes=str(row.get('Vibe', '')),
                description=str(row.get('Description', '')),
                rating=place_data['rating'],
                types=place_data['types'],
                editorial_summary=place_data['editorial_summary'],
                reviews=place_data['reviews']
            )
            
            if vibe_desc:
                df.at[idx, 'VibeDescription'] = vibe_desc
                print(f"✓ ({place_data['rating']}/5)")
                success += 1
            else:
                print("⚠ No vibe generated")
                failed += 1
        else:
            print("✗ Not found on Maps")
            failed += 1
        
        # Rate limiting
        time.sleep(0.5)
        
        # Incremental Save every 5 venues
        if (success + failed) % 5 == 0:
            print(f"    (Saving progress...)")
            df.to_csv(INPUT_CSV, index=False)
    
    # Save updated CSV
    print(f"\n[3/3] Saving updated CSV...")
    df.to_csv(INPUT_CSV, index=False)
    print(f"  ✓ Saved to {INPUT_CSV}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  ✓ Successfully enriched: {success}")
    print(f"  ✗ Failed: {failed}")
    print(f"\nTotal with VibeDescription: {df['VibeDescription'].notna().sum()}/{len(df)}")
    
    if test_mode:
        print("\n[TEST MODE] Sample vibe descriptions:")
        for _, row in df[df['VibeDescription'].notna()].head(3).iterrows():
            print(f"\n  {row['Name']}:")
            print(f"    {row['VibeDescription'][:150]}...")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process venues and add Rating + VibeDescription columns.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--test', action='store_true', help='Run in test mode (process first 5 venues)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without making changes')
    parser.add_argument('--all', action='store_true', help='Regenerate descriptions for ALL venues')
    parser.add_argument('--fix-malformed', action='store_true', help='Regenerate descriptions containing raw API data')
    parser.add_argument('--reprocess-long', action='store_true', help='Regenerate descriptions that are too long (>150 chars)')
    
    args = parser.parse_args()
    
    process_venues(
        test_mode=args.test,
        dry_run=args.dry_run,
        process_all=args.all,
        fix_malformed=args.fix_malformed,
        reprocess_long=args.reprocess_long
    )

