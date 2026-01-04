import json
import pandas as pd

CSV_FILE = 'data-262-2025-12-26.csv'
JSON_FILE = 'public/lekker-find-data.json'

def sync_json_to_csv():
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    valid_names = set(df['Name'].tolist())
    
    print(f"Reading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    venues = data['venues']
    initial_count = len(venues)
    
    print(f"Checking {initial_count} venues in JSON...")
    
    # Filter venues that are in valid_names
    valid_venues = [v for v in venues if v['name'] in valid_names]
    
    removed_count = initial_count - len(valid_venues)
    
    if removed_count > 0:
        print(f"Removing {removed_count} venues from JSON that are not in CSV:")
        for v in venues:
            if v['name'] not in valid_names:
                print(f" - {v['name']}")
                
        data['venues'] = valid_venues
        data['metadata']['total_venues'] = len(valid_venues)
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print(f"✓ Synced JSON. Saved to {JSON_FILE}")
    else:
        print("✓ JSON is already in sync with CSV (no extra venues).")

if __name__ == "__main__":
    sync_json_to_csv()
