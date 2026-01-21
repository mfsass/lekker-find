import json
import shutil
from pathlib import Path

# Configuration
INPUT_FILE = Path(__file__).parent.parent / 'public' / 'lekker-find-data.json'
BACKUP_FILE = Path(__file__).parent.parent / 'public' / 'lekker-find-data.backup.json'

# The Lekker 15 Pillars Mapping
# Keys are the source tags (normalized to lowercase for matching), Values are the Target Pillar
# If a tag maps to multiple, we can just pick the primary one or handle logic.
# For now, 1-to-1 mapping is safest to ensure distinct pillars.

PILLAR_MAP = {
    # Self-Mappings (Identity)
    'scenic': 'Scenic', 'social': 'Social', 'intimate': 'Intimate', 'active': 'Active', 
    'chill': 'Chill', 'elegant': 'Elegant', 'authentic': 'Authentic', 'artsy': 'Artsy', 
    'industrial': 'Industrial', 'family': 'Family', 'foodie': 'Foodie', 'wine': 'Wine', 
    'beach': 'Beach', 'coffee': 'Coffee', 'nightlife': 'Nightlife',
    'healthy': 'Healthy', 'music': 'Music',

    # 1. Scenic
    'nature': 'Scenic', 'views': 'Scenic', 'panoramic': 'Scenic', 'sunset': 'Scenic', 
    'waterfall': 'Scenic', 'big-views': 'Scenic', 'view': 'Scenic', 'airy': 'Scenic', 
    'mountain': 'Scenic', 'forest': 'Scenic', 'lush': 'Scenic', 'natural': 'Scenic', 
    'aerial': 'Scenic', 'pristine': 'Scenic',
    
    # 2. Social
    'lively': 'Social', 'bustling': 'Social', 'vibrant': 'Social', 'community': 'Social',
    'energetic': 'Social', 'buzzy': 'Social', 'happy': 'Social', 'fun': 'Social',
    'friendly': 'Social', 'welcoming': 'Social', 'communal': 'Social', 'interactive': 'Social',
    
    # 3. Intimate
    'romantic': 'Intimate', 'cozy': 'Intimate', 'hidden': 'Intimate', 'secret': 'Intimate',
    'quiet': 'Intimate', 'calm': 'Intimate', 'private': 'Intimate', 'moody': 'Intimate',
    'warm': 'Intimate', 'soulful': 'Intimate', 'deep': 'Intimate', 'secret-spot': 'Intimate',
    'no-signage': 'Intimate',
    
    # 4. Active
    'hiking': 'Active', 'adventure': 'Active', 'thrilling': 'Active', 'extreme': 'Active',
    'wild': 'Active', 'adrenaline': 'Active', 'outdoor': 'Active', 'wellness': 'Active',
    'wildlife': 'Active',
    
    # 5. Chill
    'relaxed': 'Chill', 'laid-back': 'Chill', 'casual': 'Chill', 'peaceful': 'Chill',
    'serene': 'Chill', 'tranquil': 'Chill', 'chilled': 'Chill', 'breezy': 'Chill',
    'slow': 'Chill', 'simple': 'Chill', 'no-frills': 'Chill',
    
    # 6. Elegant
    'fine dining': 'Elegant', 'fine-dining': 'Elegant', 'sophisticated': 'Elegant',
    'classy': 'Elegant', 'chic': 'Elegant', 'stylish': 'Elegant', 'exclusive': 'Elegant',
    'posh': 'Elegant', 'luxury': 'Elegant', 'refined': 'Elegant', 'glamorous': 'Elegant',
    'vip': 'Elegant', 'masterful': 'Elegant', 'good-value': 'Elegant', # Maybe not good-value, but keeping structure
    
    # 7. Authentic
    'local': 'Authentic', 'cultural': 'Authentic', 'historic': 'Authentic', 'nostalgic': 'Authentic',
    'retro': 'Authentic', 'vintage': 'Authentic', 'roots': 'Authentic', 'heritage': 'Authentic',
    'traditional': 'Authentic', 'old-school': 'Authentic', 'kasi-vibe': 'Authentic',
    'history': 'Authentic', 'ancient': 'Authentic', 'genuine': 'Authentic', 'real': 'Authentic',
    'locals-only': 'Authentic', 'neighborhood': 'Authentic', 'home-grown': 'Authentic',
    
    # 8. Artsy
    'creative': 'Artsy', 'unique': 'Artsy', 'quirky': 'Artsy', 'colorful': 'Artsy',
    'musical': 'Music', 'boheme': 'Artsy', 'funky': 'Artsy', 'boho': 'Artsy',
    'eclectic': 'Artsy', 'artistic': 'Artsy', 'inspiring': 'Artsy', 'educational': 'Artsy',
    'learning': 'Artsy', 'music': 'Music', 'jazz': 'Music', 'live music': 'Music',
    'theatre': 'Artsy', 'gallery': 'Artsy', 'comedy': 'Music', # Comedy fits well with entertainment/music vibe
    
    # 9. Industrial
    'grungy': 'Industrial', 'urban': 'Industrial', 'modern': 'Industrial', 
    'warehouse': 'Industrial', 'minimalist': 'Industrial', 'minimal': 'Industrial',
    'cool': 'Industrial', 'trendy': 'Industrial', 'hipster': 'Industrial',
    
    # 10. Family
    'kids': 'Family', 'playful': 'Family', 'spacious': 'Family', 'garden': 'Family',
    'family': 'Family', 'family-friendly': 'Family', 'picnic': 'Family', 'safe': 'Family',
    
    # 11. Foodie
    'tasty': 'Foodie', 'artisanal': 'Foodie', 'craft': 'Foodie', 'fusion': 'Foodie',
    'seasonal': 'Foodie', 'gourmet': 'Foodie', 'seafood': 'Foodie', 'spicy': 'Foodie',
    'healthy': 'Healthy', 'fresh': 'Healthy', 'comfort': 'Foodie', 'handmade': 'Foodie',
    'quality': 'Foodie', 'street-food': 'Foodie', 'fast': 'Foodie', 'sweet': 'Foodie',
    'italian': 'Foodie', 'mexican': 'Foodie', 'neapolitan': 'Foodie', 'treat': 'Foodie',
    'generous': 'Foodie', 'halaal': 'Foodie', 'bistro': 'Foodie',
    'vegan': 'Healthy', 'vegetarian': 'Healthy', 'plant-based': 'Healthy', 'market': 'Healthy',
    
    # 12. Wine
    'vineyard': 'Wine', 'estate': 'Wine', 'tasting': 'Wine', 'wine': 'Wine',
    
    # 13. Beach
    'beach': 'Beach', 'ocean': 'Beach', 'coastal': 'Beach', 'marine': 'Beach',
    'sea-life': 'Beach', 'sheltered': 'Beach',
    
    # 14. Coffee
    'cafe': 'Coffee', 'breakfast': 'Coffee', 'brunch': 'Coffee', 'bakery': 'Coffee',
    'lunch': 'Coffee', # Often conflated
    'wifi': 'Coffee', 'work-friendly': 'Coffee', 'laptop': 'Coffee',
    
    # 15. Nightlife
    'festive': 'Nightlife', 'party': 'Nightlife', 'cocktails': 'Nightlife',
    'dive-bar': 'Nightlife', 'theatrical': 'Nightlife', 'craft-beer': 'Nightlife',
    'tapas': 'Nightlife', 'dinner': 'Nightlife', 'sombre': 'Nightlife',
    'bar': 'Nightlife', 'pub': 'Nightlife', 'club': 'Nightlife'
}

UNMAPPED_FALLBACK = 'Authentic' # If we really can't place it

def migrate_data():
    if not INPUT_FILE.exists():
        print("Error: Input file not found.")
        return

    print(f"Backing up data to {BACKUP_FILE}...")
    shutil.copy(INPUT_FILE, BACKUP_FILE)
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    venues = data.get('venues', [])
    print(f"Processing {len(venues)} venues...")
    
    mapped_count = 0
    
    for venue in venues:
        original_vibes = venue.get('vibes', [])
        
        # If we have already migrated, 'flavors' holds the truth. Use that.
        if venue.get('flavors') and len(venue['flavors']) > 0:
             source_vibes = venue['flavors']
        else:
             source_vibes = original_vibes
        
        # 1. Ensure flavors preserves everything
        # If we are using flavors as source, just keep it. If coming from vibes, copy to flavors.
        if source_vibes != venue.get('flavors'):
            venue['flavors'] = list(set(source_vibes + venue.get('flavors', [])))
        
        # 2. Map to Pillars (From Tags)
        new_pillars = set()
        for vibe in source_vibes:
            key = vibe.lower().strip()
            if key in PILLAR_MAP:
                new_pillars.add(PILLAR_MAP[key])
            else:
                pass
                
        # 3. Smart Enrichment (From Description)
        # Many venues have "jazz" in description but not in tags. Catch them here.
        description = venue.get('description', '').lower()
        if description:
            # We check specific high-value keywords to fill gaps
            # We don't check ALL map keys to avoid noise (e.g. "and" -> ?)
            # Just the ones we identified as weak in the report.
            
            enrichment_keywords = {
                'jazz': 'Music',
                'vegan': 'Healthy',
                'vegetarian': 'Healthy',
                'secluded': 'Intimate',
                'hiking': 'Active',
                'waterfall': 'Scenic',
                'live music': 'Music',
                'market': 'Healthy',
                'work': 'Coffee'
            }
            
            for keyword, result_pillar in enrichment_keywords.items():
                if keyword in description:
                    new_pillars.add(result_pillar)
                    # Also consider adding to flavors? 
                    # For now, just fix the pillar assignment.

            
        # If no pillars found, try to assign based on category or fallback?
        if not new_pillars:
            # Fallback logic based on category could go here
            cat = venue.get('category', '').lower()
            if 'nature' in cat: new_pillars.add('Scenic')
            elif 'food' in cat: new_pillars.add('Foodie')
            elif 'drink' in cat: new_pillars.add('Nightlife')
            elif 'culture' in cat: new_pillars.add('Authentic')
            else: new_pillars.add(UNMAPPED_FALLBACK)
            
        venue['vibes'] = list(new_pillars)
        mapped_count += 1
        
    # Verify
    print("Verifying transformation...")
    example = venues[0]
    print(f"Example Venue ({example['name']}):")
    print(f"  Old Vibes (Flavors): {example['flavors']}")
    print(f"  New Vibes (Pillars): {example['vibes']}")
    
    # Save
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    print(f"Migration complete. {mapped_count} venues updated.")

if __name__ == "__main__":
    migrate_data()
