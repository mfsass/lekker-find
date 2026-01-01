#!/usr/bin/env python3
"""
Lekker Find - Embedding Generation Script
==========================================

Generates semantic embeddings for 261 Cape Town venues using OpenAI's
text-embedding-3-small model with 256 dimensions.

Usage:
    1. Set environment variable: $env:OPENAI_API_KEY = "your-key"
    2. Run: python scripts/generate_embeddings.py

Budget: ~$0.01 one-time cost
Output: public/lekker-find-data.json (~450KB)
Runtime: ~60 seconds
"""

import pandas as pd
import json
import sys
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from venue_id_utils import generate_stable_venue_id

# Load .env file
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_CSV = 'data-262-2025-12-26.csv'
OUTPUT_JSON = 'public/lekker-find-data.json'

# Model configuration - BENCHMARK WINNER
# small @ 256d: 100% accuracy, 37% separation, 898KB, $0.0001
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSIONS = 256  # Winner: best separation, under 1MB target

# Cost tracking
COST_PER_1K_TOKENS = 0.00002

# ============================================================================
# UI TAGS WITH ENRICHED DESCRIPTIONS
# Key optimization: Embed descriptive phrases, not just single words
# This dramatically improves semantic similarity accuracy
# ============================================================================

TAG_DESCRIPTIONS = {
    # Atmosphere - describe the feeling/energy
    'Chill': 'A chill, relaxed, laid-back atmosphere where you can unwind and decompress',
    'Lively': 'A lively, energetic, vibrant atmosphere with excitement, buzz, and fun',
    'Peaceful': 'A peaceful, calm, tranquil, serene setting for quiet relaxation',
    'Fun': 'A fun, playful, entertaining, enjoyable experience with laughter and good times',
    'Romantic': 'A romantic, intimate, cozy atmosphere perfect for couples and date nights',
    'Cozy': 'A cozy, warm, intimate, homey space that feels comfortable and welcoming',
    'Happy': 'A happy, cheerful, joyful atmosphere that lifts your spirits',
    'Relaxed': 'A relaxed, easy-going, stress-free environment to decompress',
    'Buzzy': 'A buzzy, happening, popular spot with social energy and excitement',
    'Quiet': 'A quiet, peaceful, calm place away from noise and crowds',
    'Warm': 'A warm, welcoming, friendly atmosphere that feels like home',
    'Festive': 'A festive, celebratory, party atmosphere with joy and entertainment',
    'Moody': 'A moody, atmospheric, dimly-lit space with ambiance and character',
    
    # Style - describe the aesthetic/vibe
    'Trendy': 'A trendy, fashionable, hip, Instagram-worthy spot that is currently popular',
    'Cool': 'A cool, stylish, edgy place with a modern, alternative vibe',
    'Funky': 'A funky, quirky, eclectic, unique space with personality and character',
    'Old-school': 'An old-school, classic, nostalgic, retro establishment with vintage charm',
    'Modern': 'A modern, contemporary, minimalist, sleek design aesthetic',
    'Rustic': 'A rustic, farmhouse, natural, earthy aesthetic with raw materials',
    'Boho': 'A bohemian, artsy, free-spirited, eclectic style with creative flair',
    'Classy': 'A classy, elegant, sophisticated, upscale, refined atmosphere',
    'Handmade': 'Handmade, artisanal, craft, small-batch products with care and quality',
    'Simple': 'A simple, unpretentious, no-frills, straightforward experience',
    'Mixed': 'A mixed, diverse, eclectic blend of styles and influences',
    'Retro': 'A retro, vintage, nostalgic, throwback style from past decades',
    'Stylish': 'A stylish, fashionable, well-designed, aesthetically pleasing space',
    
    # Experience - describe what you get
    'Adventure': 'An adventurous, thrilling, exciting experience with adrenaline and discovery',
    'Exciting': 'An exciting, thrilling, exhilarating experience that gets your heart pumping',
    'Secret': 'A secret, hidden, underground, exclusive spot that few people know about',
    'Hidden': 'A hidden gem, off-the-beaten-path, tucked away, hard to find location',
    'Famous': 'A famous, well-known, iconic, popular tourist destination',
    'Real': 'An authentic, genuine, real, honest experience without pretense',
    'Local': 'A local favorite, neighborhood spot, authentic to the community',
    'Unique': 'A unique, one-of-a-kind, special, unlike anywhere else experience',
    'VIP': 'A VIP, exclusive, premium, luxury experience for special occasions',
    'Deep': 'A deep, meaningful, profound, thought-provoking experience',
    'Interactive': 'An interactive, hands-on, participatory, engaging experience',
    'Inspiring': 'An inspiring, motivating, uplifting, creative experience',
    'Soulful': 'A soulful, heartfelt, emotional, moving, spiritual experience',
    'Genuine': 'A genuine, authentic, sincere, honest atmosphere',
    
    # Setting - describe the environment
    'Scenic': 'A scenic location with beautiful views, panoramic vistas, and stunning scenery',
    'Big-views': 'Big views, panoramic vistas, stunning scenery, breathtaking landscapes',
    'Coastal': 'A coastal, oceanside, beachfront, seaside location by the water',
    'City': 'An urban, city center, downtown, metropolitan location',
    'Nature': 'A nature setting, outdoors, natural environment, green spaces',
    'Forest': 'A forest, woodland, tree-covered, shady natural setting',
    'Sunset': 'A sunset spot, golden hour views, evening ambiance, dusk',
    'Vineyard': 'A vineyard, wine estate, winelands, grape-growing region',
    'Waterfront': 'A waterfront location, harbor, marina, water views',
    'Mountain': 'A mountain setting, highland, elevated, scenic peaks',
    'Garden': 'A garden setting, outdoor greenery, plants, natural beauty',
    'Rooftop': 'A rooftop venue, elevated, city views from above, open air',
    'Beach': 'A beach location, sandy shores, ocean waves, coastal',
    'Country': 'A countryside, rural, farm, pastoral, away from the city',
    
    # Social - describe the crowd/vibe
    'Social': 'A social, communal, gathering spot good for meeting people',
    'Family': 'A family-friendly, kid-safe, all-ages, wholesome environment',
    'Casual': 'A casual, informal, relaxed, no-dress-code atmosphere',
    'Friendly': 'A friendly, welcoming, warm, hospitable environment',
    'Welcoming': 'A welcoming, inclusive, open, accepting atmosphere',
    'Community': 'A community hub, neighborhood gathering, local meeting spot',
    
    # Food & Drink - describe the culinary experience
    'Tasty': 'Tasty, delicious, flavorful, yummy food that satisfies',
    'Healthy': 'Healthy, nutritious, wholesome, fresh, good-for-you options',
    'Treat': 'A treat, indulgence, guilty pleasure, special occasion food',
    'Craft-Beer': 'Craft beer, microbrewery, artisanal brews, beer tasting',
    'Wine': 'Wine, wine tasting, vineyards, sommelier, grape varietals',
    'Foodie': 'A foodie destination, gourmet, culinary excellence, gastronomic',
    'Street-food': 'Street food, casual eats, quick bites, local flavors',
    'Fresh': 'Fresh ingredients, farm-to-table, seasonal, just-made',
    
    # Cultural - describe the cultural experience
    'Artsy': 'An artsy, artistic, creative, gallery, design-focused space',
    'Music': 'A music venue, live performances, concerts, musical atmosphere',
    'History': 'A historical site, heritage, past stories, cultural significance',
    'Culture': 'A cultural experience, traditions, heritage, local customs',
    'Learning': 'An educational, learning, informative, knowledge experience',
    'Heritage': 'A heritage site, historical significance, preserved traditions',
    
    # Activity - describe the physical experience
    'Active': 'An active, physical, sporty, energetic, exercise experience',
    'Playful': 'A playful, fun, games, entertainment, light-hearted experience',
    'Creative': 'A creative, artistic, DIY, hands-on, making experience',
    'Wellness': 'A wellness, health, spa, relaxation, self-care experience',
    'Extreme': 'An extreme, adrenaline, thrill-seeking, intense, adventure sport',
    
    # Specifics
    'Comfort': 'Comfort food, home-style cooking, satisfying, hearty meals',
    'Tasting': 'A tasting experience, sampling, flights, variety to try',
    'Dive-bar': 'A dive bar, grungy, no-frills, authentic, unpretentious bar',
    'Sea-life': 'Sea life, marine animals, ocean creatures, underwater world',
    'Picnic': 'A picnic spot, outdoor dining, blanket and basket, al fresco',
    'Must-see': 'A must-see, essential, bucket-list, cannot-miss attraction',
    'Landmark': 'A landmark, iconic, famous, recognizable, tourist attraction',
    'Photo-ready': 'Photo-ready, Instagrammable, picture-perfect, photogenic',
    'Minimal': 'A minimal, simple, clean, uncluttered, Zen aesthetic',
    'Good-value': 'Good value, affordable, budget-friendly, worth the money',
    'Private': 'A private, exclusive, intimate, secluded setting',
    'Boutique': 'A boutique, small-scale, curated, specialty experience',
    'Neighborhood': 'A neighborhood spot, local haunt, community favorite',
    'Kasi-vibe': 'Kasi vibe, township energy, authentic South African culture',
    'Roots': 'Roots, traditional, heritage, authentic cultural origins',
    'Home-grown': 'Home-grown, local, made here, community-supported',
    'Secret-spot': 'A secret spot, hidden gem, only locals know, tucked away',
    'No-signage': 'No signage, unmarked, speakeasy-style, hard to find entrance',
    'Locals-only': 'Locals only, off-tourist-trail, authentic, neighborhood secret',
}

# Simple list for iteration
ALL_UI_TAGS = list(TAG_DESCRIPTIONS.keys())

# ============================================================================
# OPENAI CLIENT
# ============================================================================

def get_client():
    """Initialize OpenAI client."""
    try:
        from openai import OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("✗ OPENAI_API_KEY not found in environment")
            print("\nSet it with:")
            print('  $env:OPENAI_API_KEY = "your-key-here"  # PowerShell')
            print('  export OPENAI_API_KEY="your-key-here"  # Bash')
            sys.exit(1)
        return OpenAI(api_key=api_key)
    except ImportError:
        print("✗ openai package not installed")
        print("  pip install openai python-dotenv pandas")
        sys.exit(1)


def get_embedding(text: str, client) -> List[float]:
    """Generate embedding for text."""
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS
    )
    return response.data[0].embedding


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    print("=" * 60)
    print("LEKKER FIND - EMBEDDING GENERATION")
    print("=" * 60)
    print(f"\nModel: {EMBEDDING_MODEL}")
    print(f"Dimensions: {EMBEDDING_DIMENSIONS}")
    
    # Initialize client
    print("\n[1/5] Initializing OpenAI client...")
    client = get_client()
    print("✓ Client initialized")
    
    # Load existing data to preserve images, place_id, etc.
    print("\n[2/5] Loading existing data to preserve images...")
    existing_venues = {}
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        for v in existing_data.get('venues', []):
            existing_venues[v['name']] = v
        print(f"✓ Loaded {len(existing_venues)} existing venues with images")
    else:
        print("⚠ No existing data found, will generate fresh")
    
    # Load CSV
    print("\n[3/5] Loading venue data...")
    if not os.path.exists(INPUT_CSV):
        print(f"✗ {INPUT_CSV} not found")
        sys.exit(1)
    
    df = pd.read_csv(INPUT_CSV)
    print(f"✓ Loaded {len(df)} venues")
    
    # Generate venue embeddings
    print("\n[4/5] Generating venue embeddings...")
    venues = []
    total_tokens = 0
    
    for idx, row in df.iterrows():
        # Use VibeDescription (AI-enriched) if available, otherwise fall back to Vibe
        vibe_desc = str(row.get('VibeDescription', '')) if pd.notna(row.get('VibeDescription')) else ''
        vibe_str = str(row['Vibe']) if pd.notna(row['Vibe']) else ''
        desc_str = str(row['Description']) if pd.notna(row['Description']) else ''
        
        # Prefer enriched VibeDescription for better semantic matching
        embedding_text = vibe_desc if vibe_desc else vibe_str
        
        try:
            embedding = get_embedding(embedding_text, client)
            total_tokens += len(embedding_text.split()) * 1.3  # Rough token estimate
            
            # Get rating if available
            rating = row.get('Rating')
            rating_val = float(rating) if pd.notna(rating) else None
            
            # Generate stable ID from venue name
            venue_id = generate_stable_venue_id(row['Name'])
            
            # Start with base venue data
            venue_data = {
                'id': venue_id,
                'name': row['Name'],
                'category': row['Category'],
                'tourist_level': int(row['Tourist_Level']),
                'price_tier': row['Price_Range'],
                'numerical_price': row['Numerical_Price'],
                'best_season': row['Best_Season'],
                'vibes': [v.strip() for v in vibe_str.split(',') if v.strip()],
                'description': desc_str,
                'rating': rating_val,
                'embedding': embedding
            }
            
            # Merge with existing data to preserve images, place_id, etc.
            existing = existing_venues.get(row['Name'], {})
            for key in ['place_id', 'maps_url', 'image_url', 'image_width', 'image_height', 'image_attribution']:
                if key in existing and existing[key]:
                    venue_data[key] = existing[key]
            
            venues.append(venue_data)
            
            if (idx + 1) % 50 == 0:
                print(f"  Progress: {idx + 1}/{len(df)}...")
                
        except Exception as e:
            print(f"  ✗ Failed on {row['Name']}: {e}")
    
    print(f"✓ Generated {len(venues)} venue embeddings")
    
    # Generate tag embeddings using enriched descriptions
    print("\n[5/5] Generating tag embeddings with enriched descriptions...")
    tag_embeddings = {}
    
    for tag in ALL_UI_TAGS:
        try:
            # Use the enriched description for better semantic embedding
            description = TAG_DESCRIPTIONS.get(tag, tag)
            tag_embeddings[tag] = get_embedding(description, client)
            total_tokens += 15  # ~15 tokens per enriched description
        except Exception as e:
            print(f"  ✗ Failed on tag '{tag}': {e}")
    
    print(f"✓ Generated {len(tag_embeddings)} tag embeddings")
    
    # Compile output
    output = {
        'version': '1.0',
        'model': EMBEDDING_MODEL,
        'dimensions': EMBEDDING_DIMENSIONS,
        'venues': venues,
        'tag_embeddings': tag_embeddings,
        'metadata': {
            'total_venues': len(venues),
            'total_tags': len(tag_embeddings),
            'generated_at': pd.Timestamp.now().isoformat()
        }
    }
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f)
    
    size_kb = os.path.getsize(OUTPUT_JSON) / 1024
    cost = (total_tokens / 1000) * COST_PER_1K_TOKENS
    
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"\n✓ Saved to {OUTPUT_JSON}")
    print(f"  File size: {size_kb:.1f} KB {'✓' if size_kb < 1000 else '⚠ >1MB'}")
    print(f"  Estimated cost: ${cost:.4f}")
    print(f"\nNext: Run the app and test matching!")


def incremental_update():
    """
    Incremental update mode - only processes new venues from CSV.
    Preserves existing embeddings and image data.
    """
    print("=" * 60)
    print("LEKKER FIND - INCREMENTAL EMBEDDING UPDATE")
    print("=" * 60)
    
    # Load existing data
    print("\n[1/5] Loading existing data...")
    
    if not os.path.exists(OUTPUT_JSON):
        print(f"  ✗ {OUTPUT_JSON} not found. Run without --update first.")
        return
    
    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    
    existing_venues = {v['name']: v for v in existing_data.get('venues', [])}
    print(f"  ✓ Loaded {len(existing_venues)} existing venues")
    
    # Load CSV
    print("\n[2/5] Loading CSV...")
    df = pd.read_csv(INPUT_CSV)
    csv_names = set(df['Name'].values)
    print(f"  ✓ CSV has {len(csv_names)} venues")
    
    # Find new venues
    new_names = csv_names - set(existing_venues.keys())
    print(f"  → {len(new_names)} new venues to process")
    
    if len(new_names) == 0:
        print("\n✓ No new venues to process!")
        return
    
    print(f"\nNew venues:")
    for name in sorted(new_names)[:10]:
        print(f"  + {name}")
    if len(new_names) > 10:
        print(f"  ... and {len(new_names) - 10} more")
    
    # Initialize client
    print("\n[3/5] Initializing OpenAI client...")
    client = get_client()
    print("✓ Client initialized")
    
    # Generate embeddings for new venues only
    print("\n[4/5] Generating embeddings for new venues...")
    
    new_df = df[df['Name'].isin(new_names)]
    new_venues = []
    
    for idx, row in new_df.iterrows():
        name = row['Name']
        vibe_desc = str(row.get('VibeDescription', '')) if pd.notna(row.get('VibeDescription')) else ''
        vibe_str = str(row['Vibe']) if pd.notna(row['Vibe']) else ''
        desc_str = str(row['Description']) if pd.notna(row['Description']) else ''
        
        # Prefer enriched VibeDescription for better semantic matching
        embedding_text = vibe_desc if vibe_desc else vibe_str
        
        try:
            embedding = get_embedding(embedding_text, client)
            
            new_venues.append({
                'id': f"v{len(existing_venues) + len(new_venues)}",
                'name': name,
                'category': row['Category'],
                'tourist_level': int(row['Tourist_Level']),
                'price_tier': row['Price_Range'],
                'numerical_price': row['Numerical_Price'],
                'best_season': row['Best_Season'],
                'vibes': [v.strip() for v in vibe_str.split(',') if v.strip()],
                'description': desc_str,
                'embedding': embedding
            })
            
            print(f"  ✓ {name}")
            
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    
    # Merge with existing
    print("\n[5/5] Merging and saving...")
    
    all_venues = list(existing_venues.values()) + new_venues
    existing_data['venues'] = all_venues
    existing_data['metadata']['total_venues'] = len(all_venues)
    existing_data['metadata']['updated_at'] = pd.Timestamp.now().isoformat()
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f)
    
    size_kb = os.path.getsize(OUTPUT_JSON) / 1024
    
    print("\n" + "=" * 60)
    print("INCREMENTAL UPDATE COMPLETE")
    print("=" * 60)
    print(f"\n✓ Added {len(new_venues)} new venues")
    print(f"✓ Total venues: {len(all_venues)}")
    print(f"✓ File size: {size_kb:.1f} KB")
    print("\nNext: Run fetch_images.py to get photos for new venues")


if __name__ == "__main__":
    import sys
    
    if '--update' in sys.argv:
        incremental_update()
    elif '--help' in sys.argv:
        print(__doc__)
    else:
        main()

