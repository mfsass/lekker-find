import json
from collections import Counter, defaultdict

def analyze_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return

    venues = data.get('venues', [])
    print(f"Total venues: {len(venues)}")

    # Check duplicates
    names = [v['name'] for v in venues]
    ids = [v['id'] for v in venues]
    
    dup_names = [item for item, count in Counter(names).items() if count > 1]
    dup_ids = [item for item, count in Counter(ids).items() if count > 1]

    print(f"\nDuplicate Names ({len(dup_names)}): {dup_names}")
    print(f"Duplicate IDs: {dup_ids}")

    # Check suburbs
    suburbs = [v.get('suburb', 'Unknown') for v in venues]
    suburb_counts = Counter(suburbs)
    print(f"\nTop 20 Suburbs:\n{suburb_counts.most_common(20)}")
    print(f"Total Unique Suburbs: {len(suburb_counts)}")

    # Check for empty/missing fields
    missing_images = [v['name'] for v in venues if not v.get('image_url')]
    missing_ratings = [v['name'] for v in venues if not v.get('rating')]
    
    print(f"\nVenues missing images ({len(missing_images)}): {missing_images[:5]}...")
    print(f"Venues missing ratings ({len(missing_ratings)}): {missing_ratings[:5]}...")

    # Pricing check (basic format check)
    prices = [v.get('numerical_price', '') for v in venues]
    print(f"\nSample Pricing formats: {prices[:10]}")

if __name__ == "__main__":
    analyze_data('public/lekker-find-data.json')
