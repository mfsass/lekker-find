#!/usr/bin/env python3
"""
Generate Vibe Embeddings for New Curated Vibes
===============================================

Uses gpt-5-nano to generate rich vibe descriptions for each curated vibe word,
then generates embeddings from these descriptions for optimal semantic matching.

The key insight: Venue embeddings come from rich VibeDescriptions (2-3 sentences),
so our vibe selections should also have rich descriptions that map well to those.

Usage:
    python scripts/generate_vibe_embeddings.py           # Generate all
    python scripts/generate_vibe_embeddings.py --test    # Test with 5 vibes
    python scripts/generate_vibe_embeddings.py --list    # List all curated vibes
"""

import os
import sys
import json
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = 'gpt-5-nano'
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSIONS = 256

# ============================================================================
# CURATED VIBES (from implementation plan)
# ============================================================================

# Universal vibes (shown for ALL intents)
UNIVERSAL_VIBES = [
    "Hidden",       # Secret spots, tucked away
    "Famous",       # Must-see, iconic, landmark
    "Romantic",     # Date night, intimate
    "Family",       # Kid-friendly, safe
    "Views",        # Scenic, panoramic
    "Chill",        # Relaxed, peaceful
    "Lively",       # Buzzy, energetic
    "Local",        # Neighborhood, authentic
    "Unique",       # Quirky, one-of-a-kind
    "Cozy",         # Warm, inviting
]

# Food & Drink vibes
FOOD_VIBES = [
    "Brunch",        # breakfast, morning, eggs
    "Fine Dining",   # refined, tasting menu
    "Street Food",   # casual, quick, no-frills
    "International", # Italian, Japanese, fusion
    "Traditional",   # heritage, Cape Malay, home-style
    "Wine",          # vineyard, cellar, tasting
    "Craft Beer",    # brewery, local brews
    "Coffee",        # roastery, espresso, cafe
    "Sweet Tooth",   # desserts, chocolate, bakery
    "Evening",       # after dark dining
    "Halaal",        # halal certified
    "Outdoor Dining", # terrace, garden, sidewalk
]

# Activity vibes
ACTIVITY_VIBES = [
    "Beach",        # coastal, seaside, surf, tidal pool
    "Mountain",     # hiking, climbing, peak, altitude
    "Water",        # swimming, diving, kayak, marine
    "Forest",       # trees, shady, woodland
    "Outdoor",      # nature, open air, fresh
    "Urban",        # city, indoor, arcade
    "Sport",        # active, cycling, padel
    "Wellness",     # spa, yoga, restorative
    "Adventure",    # adrenaline, extreme, zipline
    "Wildlife",     # animals, penguins, safari
    "Learning",     # educational, tour, workshop
    "Sunset",       # golden hour, evening views
]

# Attraction vibes
ATTRACTION_VIBES = [
    "History",      # historic, heritage, old
    "Art",          # gallery, exhibition, creative
    "Music",        # live music, jazz, concert
    "Theatre",      # show, performance, stage
    "Museum",       # displays, collection
    "Interactive",  # hands-on, immersive
    "Heritage",     # cultural, indigenous, Cape Malay
    "Photo-Ready",  # colorful, instagrammable
    "Markets",      # stalls, vendors, shopping
    "Architecture", # buildings, design
]

# NOTE: Avoid vibes don't need separate embeddings!
# The avoid selection will dynamically show OTHER vibes from the same pool
# to help refine preferences. E.g., if user picks "Water" + "Adventure",
# avoid options could be "Beach", "Indoor", "Urban" - using their SAME embeddings.
#
# This ensures:
# 1. Consistent embeddings (same generation style as positive vibes)
# 2. Logical refinement (avoid Beach when you want Mountain hiking)
# 3. Smart separation based on what they already selected


# ============================================================================
# VIBE DESCRIPTION GENERATOR
# ============================================================================

def generate_vibe_description(vibe: str, category: str) -> str:
    """
    Generate a rich 2-3 sentence description for a vibe word.
    This description will be embedded and used for semantic matching.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        print("✗ openai package not installed. Run: pip install openai")
        return ""
    
    prompt = f"""You are a Cape Town travel expert. Generate a rich 2-3 sentence description for this vibe/mood that a traveler might want from an experience.

Vibe word: "{vibe}"
Category context: {category}

The description should:
1. Capture the FEELING and ATMOSPHERE this vibe represents
2. Include related words and concepts that venues with this vibe would have
3. Use warm, evocative language a traveler would resonate with
4. Be specific to Cape Town context where relevant

Write ONLY the description (2-3 sentences). No intro or labels."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ✗ OpenAI error for '{vibe}': {e}")
        return ""


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a text using OpenAI embedding model."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            dimensions=EMBEDDING_DIMENSIONS
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  ✗ Embedding error: {e}")
        return []


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_vibes(test_mode: bool = False):
    """Generate descriptions and embeddings for all curated vibes."""
    
    print("=" * 60)
    print("GENERATE VIBE EMBEDDINGS")
    print("=" * 60)
    
    all_vibes = {
        "Universal": UNIVERSAL_VIBES,
        "Food & Drink": FOOD_VIBES,
        "Activity": ACTIVITY_VIBES,
        "Attraction": ATTRACTION_VIBES,
    }
    
    total = sum(len(v) for v in all_vibes.values())
    print(f"\nTotal vibes to process: {total}")
    
    if test_mode:
        # Just process 5 vibes for testing
        all_vibes = {"Universal": UNIVERSAL_VIBES[:3], "Activity": ACTIVITY_VIBES[:2]}
        total = 5
        print(f"[TEST MODE] Processing 5 vibes only")
    
    results = {}
    count = 0
    
    for category, vibes in all_vibes.items():
        print(f"\n[{category}]")
        
        for vibe in vibes:
            count += 1
            print(f"  [{count}/{total}] {vibe}...", end=" ")
            
            # Generate description
            description = generate_vibe_description(vibe, category)
            
            if not description:
                print("✗ No description")
                continue
            
            # Generate embedding from description
            embedding = generate_embedding(description)
            
            if not embedding:
                print("✗ No embedding")
                continue
            
            results[vibe] = {
                "category": category,
                "description": description,
                "embedding": embedding
            }
            
            print(f"✓")
            if test_mode:
                print(f"      → {description[:100]}...")
    
    # Save results
    output_file = "scripts/curated_vibe_embeddings.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"✓ Generated {len(results)}/{total} vibe embeddings")
    print(f"✓ Saved to {output_file}")
    
    # Show sample
    print("\nSample descriptions:")
    for vibe in list(results.keys())[:3]:
        print(f"\n  {vibe}: {results[vibe]['description'][:150]}...")


def list_vibes():
    """List all curated vibes."""
    print("\n=== CURATED VIBES ===\n")
    
    all_vibes = {
        "Universal (10)": UNIVERSAL_VIBES,
        "Food & Drink (12)": FOOD_VIBES,
        "Activity (12)": ACTIVITY_VIBES,
        "Attraction (10)": ATTRACTION_VIBES,
    }
    
    print("NOTE: Avoid options use SAME vibes dynamically (no separate embeddings needed)")
    print("      e.g., picking 'Water' + 'Adventure' → avoid could show 'Beach', 'Indoor', 'Urban'\n")
    
    for category, vibes in all_vibes.items():
        print(f"{category}:")
        for vibe in vibes:
            print(f"  - {vibe}")
        print()
    
    print(f"Total: {sum(len(v) for v in all_vibes.values())} vibes")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("✗ OPENAI_API_KEY not found in .env")
        sys.exit(1)
    
    if '--help' in sys.argv:
        print(__doc__)
    elif '--list' in sys.argv:
        list_vibes()
    elif '--test' in sys.argv:
        process_vibes(test_mode=True)
    else:
        process_vibes()
