
import json
import pandas as pd
import sys
from pathlib import Path

# Config
CSV_FILE = 'data-262-2025-12-26.csv'
JSON_FILE = 'public/lekker-find-data.json'

def sync_metadata():
    print("=" * 60)
    print("LEKKER FIND - METADATA SYNC (ROBUST)")
    print("=" * 60)

    if not Path(CSV_FILE).exists() or not Path(JSON_FILE).exists():
        print(f"✗ Error: Missing {CSV_FILE} or {JSON_FILE}")
        sys.exit(1)

    print(f"Loading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    # Check for duplicates in CSV
    duplicates = df[df.duplicated('Name', keep=False)]
    if not duplicates.empty:
        print(f"⚠ Warning: Found {len(duplicates)} duplicate names in CSV. Using last occurrence.")
        # Drop duplicates, keeping last (assuming newest/updated is at bottom)
        df = df.drop_duplicates(subset='Name', keep='last')

    csv_map = df.set_index('Name').to_dict('index')

    print(f"Loading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues = data.get('venues', [])
    updated_count = 0
    
    print("\nSyncing metadata...")
    for venue in venues:
        name = venue.get('name')
        if name in csv_map:
            row = csv_map[name]
            
            # Fields to sync
            
            # 1. Price
            if row['Price_Range'] != venue.get('price_tier'):
                print(f"  UPDATE {name}: Price {venue.get('price_tier')} -> {row['Price_Range']}")
                venue['price_tier'] = row['Price_Range']
                venue['numerical_price'] = row['Numerical_Price']
                updated_count += 1
            
            # 2. Suburb
            if str(row['Suburb']) != str(venue.get('suburb')):
                print(f"  UPDATE {name}: Suburb {venue.get('suburb')} -> {row['Suburb']}")
                venue['suburb'] = str(row['Suburb'])
                updated_count += 1
                
            # 3. Rating
            if float(row['Rating']) != float(venue.get('rating') or 0):
                # print(f"  UPDATE {name}: Rating {venue.get('rating')} -> {row['Rating']}") # Less noisy
                venue['rating'] = float(row['Rating'])
                updated_count += 1
                
            # 4. Tourist Level - Force sync from CSV if we start managing it manually there
            if int(row['Tourist_Level']) != int(venue.get('tourist_level') or 0):
                # print(f"  UPDATE {name}: Level {venue.get('tourist_level')} -> {row['Tourist_Level']}")
                venue['tourist_level'] = int(row['Tourist_Level'])
                updated_count += 1

            # 5. Vibes
            csv_vibes = [v.strip() for v in str(row['Vibe']).split(',') if v.strip()]
            if csv_vibes != venue.get('vibes'):
                 print(f"  UPDATE {name}: Vibes -> {csv_vibes}")
                 venue['vibes'] = csv_vibes
                 updated_count += 1
            
            # 6. Name (Reverse Sync to rename JSON entries if needed? No, too risky for ID mismatch)

    if updated_count > 0:
        data['metadata']['updated_at'] = pd.Timestamp.now().isoformat()
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f) 
        print(f"\n✓ Synced metadata for {len(venues)} venues.")
        print(f"✓ Saved to {JSON_FILE}")
    else:
        print("\n✓ No metadata differences found.")

if __name__ == "__main__":
    sync_metadata()
